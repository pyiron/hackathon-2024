from pyiron_workflow import as_function_node
import ase as _ase

@as_function_node()
def ase_read(fp: str,
             format=None):
    from ase.io import read
    atoms = read(fp, format=format)
    return atoms

@as_function_node()
def ase2ovito_data(atoms: _ase.Atoms):
    import ovito
    ovito_data = ovito.io.ase.ase_to_ovito(atoms)
    return ovito_data

@as_function_node()
def ovito_data2ovito_pipeline(ovito_data):
    from ovito import pipeline
    static= pipeline.StaticSource()
    static.data = ovito_data
    pipeline = pipeline.Pipeline()
    return pipeline

@as_function_node()
def ovito2ase(pipeline):
    import ovito
    ase_atoms = ovito.io.ase.ovito_to_ase(pipeline.compute())
    return ase_atoms

@as_function_node('plot')
def viz_ovito(pipeline, layout=None):
    from ovito.vis import Viewport
    from ipywidgets import Layout
    layout = layout or Layout(width='100%')
    pipeline.add_to_scene()
    vp = Viewport()
    return vp.create_jupyter_widget(layout=layout)

@as_function_node('plot')
def ase_view(atoms: _ase.Atoms):
    from ase.visualize import view
    return view(atoms, viewer='ngl')


