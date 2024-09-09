from pyiron_workflow import Workflow

@Workflow.wrap.as_function_node()
def obtain_potential(pot_str:str):
    from pyiron_atomistics.lammps.potential import LammpsPotentialFile,LammpsPotential

    # Potential file details
    potential = LammpsPotentialFile().find_by_name(pot_str)
    config = potential['Config'].iloc[0]
    files = potential['Filename'].iloc[0]

    # Element list of the potential
    element_list = LammpsPotential()
    element_list.df = potential
    elements = element_list.get_element_lst()
    return config, files, elements, element_list  