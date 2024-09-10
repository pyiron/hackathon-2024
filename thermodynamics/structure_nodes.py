from typing import Optional
import numpy as np
from pyiron_workflow import Workflow

@Workflow.wrap.as_function_node()
def get_structure(species: str, 
                  a0: Optional[float]= None, 
                  lattice_type: Optional[str]= None, 
                  cubic: Optional[bool]= True,
                  repeat: Optional[tuple]= (1,1,1), 
                  a2: Optional[float]= None):
    
    from pyiron_atomistics import Project
    pr = Project('structure')
    structure = pr.create.structure.bulk(a=a0,
                                         c=a2,
                                         name=species,
                                         crystalstructure=lattice_type,
                                         cubic=cubic).repeat(repeat)
    return structure

if __name__=='__main__':
    wf = Workflow('atomistic_structure')
    wf.step1 = get_structure()
    wf.draw(size=(5,5))
    wf.run(step1__a0=3.52,step1__species='Ni', step1__a2=None,
       step1__lattice_type='fcc',step1__cubic=True, step1__repeat=np.array([2,2,2]))