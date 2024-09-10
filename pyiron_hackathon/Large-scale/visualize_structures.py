from pyiron_workflow import Workflow
import ase as _ase

@Workflow.wrap.as_function_node()
def ase_read(fp: str,
             format=None):
    from ase.io import read
    atoms = read(fp, format=format)
    return atoms

@Workflow.wrap.as_function_node()
def ase2ovito(atoms: _ase.Atoms):
    import ovito
    ovito_data = ovito.io.ase.ovito_to_ase(ovito_file.compute())
    return ovito_data

@Workflow.wrap.as_function_node('plot')
def ase_view(atoms: _ase.Atoms):
    from ase.visualize import view
    return view(atoms, viewer='ngl')
                
