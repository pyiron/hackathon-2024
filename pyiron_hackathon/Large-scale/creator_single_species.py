from pyiron_workflow import as_function_node
from typing import Optional

@as_function_node("structure")
def create_box_single_species(
    crystal: Optional[str],
    lattice_constant_a: Optional[float|int],
    x_indices: Optional[str|list[int]] = '1 0 0',
    y_indices: Optional[str|list[int]] = '0 1 0',
    z_indices: Optional[str|list[int]] = '0 0 1',
    x_repetition: Optional[int] = 1,
    y_repetition: Optional[int] = 1,
    z_repetition: Optional[int] = 1,
    species: Optional[str] = 'W',
    x_pbc: Optional[bool] = False,
    y_pbc: Optional[bool] = False,
    z_pbc: Optional[bool] = False
):
    '''
    Returns an ase atom object in the form of a simple box


        Parameters:
            crystal: bcc or fcc or hcp or dc (diamond cubic)
            lattice_constant_a: desired lattice constant
            x_indices, y_indices, z_indices: the desired miller indices for the three coordinate axes
            x_repetition, y_repetition, z_repetition: Supercell repetitions along the three coordinate axes
            species: desired element
            x_pbc, y_pbc, z_pbc: periodic boundaries, true or false along the three coordinate axes
    '''
    
    from ase.lattice.cubic import BodyCenteredCubic

    if isinstance(x_indices, str):
        x_indices = [int(i) for i in x_indices.split()]
    if isinstance(y_indices, str):
        y_indices = [int(i) for i in y_indices.split()]
    if isinstance(z_indices, str):
        z_indices = [int(i) for i in z_indices.split()]

    if x_pbc == True:
        x_pbc_int = 1
    else:
        x_pbc_int = 0

    if y_pbc == True:
        y_pbc_int = 1
    else:
        y_pbc_int = 0

    if z_pbc == True:
        z_pbc_int = 1
    else:
        z_pbc_int = 0

    orient_dict = {'[0, 0, 0, 1]': [0, 0, 1], '[1, -1, 0, 0]': [0, 1, 0], '[-1, 1, 0, 0]': [0, -1, 0], '[1, 0, -1, 0]': [1, 0, 0],
                   '[-1, 0, 1, 0]': [-1, 0, 0],'[2, -1, -1, 0]': [1, 0, 0],'[-2, 1, 1, 0]': [-1, 0, 0], '[1, -2, 1, 0]': [0, -1, 0],
                   '[-1, 2, -1, 0]': [0, 1, 0]}
    if crystal=='c14' or crystal=='hcp':
        m1 = orient_dict[str(x_indices)]
        m2 = orient_dict[str(y_indices)]
        m3 = orient_dict[str(z_indices)]
    else:
        m1 = x_indices
        m2 = y_indices
        m3 = z_indices
        
    ase_atoms = BodyCenteredCubic(directions = [m1, m2, m3], 
                                  size=(x_repetition, y_repetition, z_repetition), 
                                  symbol=species,
                                  pbc=(x_pbc,y_pbc,z_pbc),
                                  latticeconstant = lattice_constant_a)

    return ase_atoms


    

    
