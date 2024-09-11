from pyiron_workflow import Workflow
import numpy as np
from structure_nodes import *
from thermo_potential import *
from dataclasses import dataclass, asdict
from typing import Optional

@Workflow.wrap.as_function_node()
def Initialize(inputdict, structure, potential_obj, files, potential_config):
    from pyiron_atomistics.lammps.structure import (
        LammpsStructure,
        UnfoldingPrism,
        structure_to_lammps,
    ) 
    import os
    from calphy.input import Calculation
    import shutil
    from dataclasses import asdict

    inputdict = asdict(inputdict)
    
    #filename of structure
    file_name = os.path.join(os.getcwd(), 'temp.struct.dat')
    lmp_structure = LammpsStructure()
    lmp_structure.potential = potential_obj
    lmp_structure.atom_type = "atomic"
    lmp_structure.el_eam_lst = potential_obj.get_element_lst()
    lmp_structure.structure = structure_to_lammps(structure)
    if not set(lmp_structure.structure.get_species_symbols()).issubset(
        set(lmp_structure.el_eam_lst)
    ):
        raise ValueError(
            "The selected potentials do not support the given combination of elements."
        )
    lmp_structure.write_file(file_name=file_name)

    #now populate the input dict
    inputdict['lattice'] = file_name
    inputdict['pair_style'] = potential_config[0].strip().split('pair_style ')[-1]
    inputdict['pair_coeff'] = potential_config[1].strip().split('pair_coeff ')[-1]
    inputdict['element'] = potential_obj.get_element_lst()

    elements_from_pot = inputdict['element']
    elements_object_lst = structure.get_species_objects()
    elements_struct_lst = structure.get_species_symbols()

    masses = []
    for element_name in elements_from_pot:
        if element_name in elements_struct_lst:
            index = list(elements_struct_lst).index(element_name)
            masses.append(elements_object_lst[index].AtomicMass)
        else:
            masses.append(1.0)
 
    inputdict['mass'] = masses
    
    #working directory
    calculation = Calculation(**inputdict)
    simfolder = calculation.create_folders()
    potential_obj.copy_pot_files(simfolder)
    #for file in files:
    #    shutil.copy(file, simfolder)
        
    return calculation, simfolder

@Workflow.wrap.as_function_node()
def RunCalculation(calculation, simfolder):
    from calphy import Liquid, Solid
    from calphy.routines import routine_alchemy, routine_fe, routine_pscale, routine_ts
    #simfolder = calc.create_folders()
    if calculation.reference_phase == "solid":
        job = Solid(calculation=calculation, simfolder=simfolder)
    elif calculation.reference_phase == "liquid":
        job = Liquid(calculation=calculation, simfolder=simfolder)
    else:
        raise ValueError("Unknown reference state")

    if calculation.mode == "fe":
        routine_fe(job)
    elif calculation.mode == "ts":
        routine_ts(job)
    elif calculation.mode == "pscale":
        routine_pscale(job)
    else:
        raise ValueError("Unknown mode")
    return job

@Workflow.wrap.as_function_node()
def GetResults(job):
    import os
    import matplotlib.pyplot as plt
    if job.calc.mode == 'fe':
        results = job.report
    elif job.calc.mode == 'ts':
        results = job.report
        resfile = os.path.join(job.simfolder, 'temperature_sweep.dat')
        temp, fe = np.loadtxt(resfile, 
                unpack=True, usecols=(0,1))
        plt.plot(temp, fe)
        plt.xlabel('Temperature (K)')
        plt.ylabel('Free energy (eV/K)')
        plt.show()
    return results

@Workflow.wrap.as_function_node("temperature", "free_energy")
def ParseTS(job):
    import os
    results = job.report
    if job.calc.mode == 'ts':
        resfile = os.path.join(job.simfolder, 'temperature_sweep.dat')
        temp, fe = np.loadtxt(resfile, 
            unpack=True, usecols=(0,1))
    elif job.calc.mode == 'fe':
        temp = job.report['input']['temperature']
        fe = job.report['results']['free_energy']
    return temp, fe

@dataclass
class MD:
    timestep: float = 0.001
    n_small_steps: int = 10000
    n_every_steps: int = 10
    n_repeat_steps: int = 10
    n_cycles: int = 100
    thermostat_damping: float = 0.5
    barostat_damping: float = 0.1

@dataclass
class Tolerance:
    lattice_constant: float = 0.0002
    spring_constant: float = 0.01
    solid_fraction: float = 0.7
    liquid_fraction: float = 0.05
    pressure: float = 0.5

@dataclass
class NoseHoover:
    thermostat_damping: float = 0.1
    barostat_damping: float = 0.1

@dataclass
class Berendsen:
    thermostat_damping: float = 100.0
    barostat_damping: float = 100.0

@dataclass
class Queue:
    cores: int = 1

@dataclass
class InputClass:
    md: Optional[MD] = None
    tolerance: Optional[Tolerance] = None
    nose_hoover: Optional[NoseHoover] = None
    berendsen: Optional[Berendsen] = None
    queue: Optional[Queue] = None
    pressure: int = 0
    temperature: int = 0
    npt: bool = True
    n_equilibration_steps: int = 15000
    n_switching_steps: int = 25000
    n_print_steps: int = 1000
    n_iterations: int = 1
    equilibration_control: str = "nose_hoover"
    melting_cycle: bool = True
    reference_phase: Optional[str] = None
    mode: Optional[str] = None
    spring_constants: Optional[float] = None
    
    def __post_init__(self):
        self.md = MD()
        self.tolerance = Tolerance()
        self.nose_hoover = NoseHoover()
        self.berendsen = Berendsen()
        self.queue = Queue()

@Workflow.wrap.as_function_node()
def UpdateTemperature(inp, temperature, make_copy=True):
    if make_copy:
        inp = InputClass(**asdict(inp))
    inp.temperature = temperature
    return inp
    
#@Workflow.wrap.as_macro_node("temperature", "free_energy")
@Workflow.wrap.as_macro_node('temperature')
def RunFreeEnergy(wf, inp, species: str, 
                  potential: str, temperature: float):

    wf.step1 = obtain_potential(potential)
    wf.step2 = get_structure(species=species, repeat=(2,2,2))
    wf.step2a = UpdateTemperature(inp, temperature)
    wf.step3 = Initialize(wf.step2a.outputs.inp, 
                          wf.step2.outputs.structure,
                     wf.step1.outputs.element_list,
                     wf.step1.outputs.files,
                     wf.step1.outputs.config)
    wf.step4 = RunCalculation(wf.step3.outputs.calculation,
                         wf.step3.outputs.simfolder)
    wf.step5 = ParseTS(wf.step4.outputs.job)
    #return wf.step5.outputs.temperature, wf.step5.outputs.free_energy
    #incremented_temp = wf.step5.outputs.temperature + 100. 
    return wf.step5.outputs.temperature
    