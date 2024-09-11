from pyiron_workflow import as_function_node
import ase as _ase
import numpy as _numpy
import ipywidgets as _ipywidgets
from typing import Optional

@as_function_node()
def ase2ovito_data(atoms: _ase.Atoms):
    """Convert ase.Atoms object to ovidto data object"""
    import ovito
    ovito_data = ovito.io.ase.ase_to_ovito(atoms)
    return ovito_data

@as_function_node()
def ovito_data2ovito_pipeline(ovito_data):
    """Convert convert ovito data to ovito pipeline"""
    from ovito import pipeline
    static= pipeline.StaticSource()
    static.data = ovito_data
    pipeline = pipeline.Pipeline(source=static)
    return pipeline

@as_function_node()
def ovito2ase(pipeline):
    """Convert ovito pipeline to ase.Atoms object"""
    import ovito
    ase_atoms = ovito.io.ase.ovito_to_ase(pipeline.compute())
    return ase_atoms

