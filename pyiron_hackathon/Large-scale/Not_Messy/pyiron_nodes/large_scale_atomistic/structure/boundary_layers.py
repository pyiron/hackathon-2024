from pyiron_workflow import as_function_node
from typing import Optional

@as_function_node("cylinder_with_boundary")
def outer_cylinder(
    structure,
    radius: Optional[float|int],
):
    '''
    Takes in a cylindrical structure and changes atom type in a cylindrical outer boundary region.
    The changed atoms can then be fixed or given a different interaction.
    Assumed that crack front is along z-direction (make sure input structure is appropriate)
    radius: cylinder radius outside which atom types are changed

    '''
    
    xcenter = structure.cell[0][0]/2
    ycenter = structure.cell[1][1]/2

    is_outside = ((structure.positions[:][:,0]-xcenter)*(structure.positions[:][:,0]-xcenter))+((structure.positions[:][:,1]-ycenter)*(structure.positions[:][:,1]-ycenter)) >= radius*radius
    is_inside = ((structure.positions[:][:,0]-xcenter)*(structure.positions[:][:,0]-xcenter))+((structure.positions[:][:,1]-ycenter)*(structure.positions[:][:,1]-ycenter)) < radius*radius

    structure.numbers[is_outside] = 3
    structure.numbers[is_inside] = 4

    return structure
