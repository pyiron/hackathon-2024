from pyiron_workflow import Workflow
import numpy as np

def CreateInputDict():
    return {
        "mode": None,
        "pressure": 0,
        "temperature": 0,
        "reference_phase": None,
        "npt": True,
        "n_equilibration_steps": 15000,
        "n_switching_steps": 25000,
        "n_print_steps": 1000,
        "n_iterations": 1,
        "spring_constants": None,
        "equilibration_control": "nose-hoover",
        "melting_cycle": True,
        "md": {
            "timestep": 0.001,
            "n_small_steps": 10000,
            "n_every_steps": 10,
            "n_repeat_steps": 10,
            "n_cycles": 100,
            "thermostat_damping": 0.5,
            "barostat_damping": 0.1,
        },
        "tolerance": {
            "lattice_constant": 0.0002,
            "spring_constant": 0.01,
            "solid_fraction": 0.7,
            "liquid_fraction": 0.05,
            "pressure": 0.5,
        },
        "nose_hoover": {
            "thermostat_damping": 0.1,
            "barostat_damping": 0.1,
        },
        "berendsen": {
            "thermostat_damping": 100.0,
            "barostat_damping": 100.0,
        },
        "queue": {
            "cores": 1,
        }

    }

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
    return job.report