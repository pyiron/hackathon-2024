from pyiron_workflow import as_function_node
import ase as _ase
import numpy as _numpy
import ipywidgets as _ipywidgets
from typing import Optional

@as_function_node()
def ase_read(fp: str,
             format=None):
    """Read structure from file using ase"""
    from ase.io import read
    structure = read(fp, format=format)
    return structure

@as_function_node()
def swap_atom_types(structure: _ase.Atoms, 
                    old_atom_number: int, 
                    new_atom_number: int):
    """Swap atom type number to another atom type number""" 
    structure = structure.copy()
    structure.numbers[structure.numbers == old_atom_number] = new_atom_number
    return structure
    
    