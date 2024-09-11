from pyiron_workflow import as_function_node
import ase as _ase
import numpy as _numpy
import ipywidgets as _ipywidgets
from typing import Optional


@as_function_node('plot')
def ase2ovito_viz(ase_atoms: _ase.Atoms):
    """Visualize ase.Atoms with ovito widget"""
    from ovito.pipeline import StaticSource, Pipeline
    from ovito.io.ase import ase_to_ovito
    data = ase_to_ovito(ase_atoms)
    pipeline = Pipeline(source = StaticSource(data = data))
    pipeline.add_to_scene()
    from ovito.vis import Viewport
    from ipywidgets import Layout
    vp = Viewport()
    return vp.create_jupyter_widget(layout=Layout(width='100%'))

@as_function_node('plot')
def viz_ovito(pipeline, 
              layout: Optional[_ipywidgets.Layout] =None
             ):
    """Visualize ovito pipeline with a ovito widget"""
    from ovito.vis import Viewport
    from ipywidgets import Layout
    layout = layout or Layout(width='100%')
    pipeline.add_to_scene()
    vp = Viewport()
    return vp.create_jupyter_widget(layout=layout)

@as_function_node('plot')
def ase_view(atoms: _ase.Atoms):
    """Visualize ase.Atoms """
    from ase.visualize import view
    return view(atoms, viewer='ngl')

@as_function_node('plot')
def plot3d(structure: _ase.Atoms,
           particle_size: Optional[int|float] = 1,
           #show_cell: bool = True,
           #show_axes: bool = True,
           camera: str = 'orthographic',
           #spacefill: Optional[bool] = True,
           select_atoms: Optional[_numpy.ndarray] = None,
          ):
    """Visualize ase.Atoms using nglview"""
    from structuretoolkit import plot3d
    return plot3d(structure=structure, 
                  particle_size=particle_size, 
                  #show_cell=show_cell,
                  #show_axes=show_axes,
                  camera=camera,
                  #spacefill=spacefill,
                  select_atoms=select_atoms
                 )

