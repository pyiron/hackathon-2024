from pyiron_workflow import as_function_node
from typing import Optional

@as_function_node("cylinder")
def cut_cylinder(
    structure,
    xcenter: Optional[float|int],
    ycenter: Optional[float|int],
    radius: Optional[float|int],
):
    '''
    Returns a cylindrical structure for k-controlled fracure simulations.
    Assumed that crack front is along z-direction (make sure input structure is appropriate)
    xcenter, ycenter: Desired mathenatical center of crack tip from input structure
    radius: cylinder radius

    '''

    import numpy as np
    
    box = (2*radius) + (radius/4)
    shift_x = box/2 - xcenter
    shift_y = box/2 - ycenter
    unit_vector = [1.0, 1.0, 0.0]
    translation_vector = np.array(unit_vector) * [shift_x, shift_y, 0.0]
    box_z = structure.cell[2][2]

    del structure[[atom.index for atom in structure if (atom.position[0]-xcenter)*(atom.position[0]-xcenter)+(atom.position[1]-ycenter)*(atom.position[1]-ycenter) > 90000]]
    structure.translate(translation_vector)
    structure.set_cell([box, box, box_z])

    return structure