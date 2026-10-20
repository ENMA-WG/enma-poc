from pathlib import Path
from typing import Iterator, NamedTuple

import ifcopenshell
import ifcopenshell.geom

PIPE_CLASSES = ("IfcPipeSegment", "IfcPipeFitting")

# IFC surface colours (IfcColourRgb) are already normalised to 0.0-1.0.
DEFAULT_COLOR = (0.82, 0.82, 0.82)
# IFC transparency is 0.0 = fully opaque, 1.0 = fully transparent - the
# inverse of the opacity that pyvista/VTK expect, so callers must invert it.
DEFAULT_OPACITY = 1.0


class StyledMesh(NamedTuple):
    vertices: list[tuple[float, float, float]]
    faces: list[tuple[int, int, int]]
    color: tuple[float, float, float]
    opacity: float


class ElementMesh(NamedTuple):
    element: ifcopenshell.entity_instance
    styled_meshes: list[StyledMesh]


def load_model(ifc_path: Path) -> ifcopenshell.file:
    return ifcopenshell.open(str(ifc_path))


def _create_settings() -> ifcopenshell.geom.settings:
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    return settings


def _material_style(material) -> tuple[tuple[float, float, float], float]:
    diffuse = material.diffuse
    color = (diffuse.r(), diffuse.g(), diffuse.b())
    transparency = material.transparency if material.has_transparency() else 0.0
    opacity = 1.0 - transparency
    return color, opacity


def _shape_to_mesh(element: ifcopenshell.entity_instance, shape) -> ElementMesh:
    geometry = shape.geometry
    verts = geometry.verts
    faces = geometry.faces
    material_ids = geometry.material_ids
    styles = [_material_style(material) for material in geometry.materials]

    vertices = [
        (verts[i], verts[i + 1], verts[i + 2])
        for i in range(0, len(verts), 3)
    ]
    triangles = [
        (faces[i], faces[i + 1], faces[i + 2])
        for i in range(0, len(faces), 3)
    ]

    groups: dict[tuple[tuple[float, float, float], float], list[tuple[int, int, int]]] = {}
    for face_index, triangle in enumerate(triangles):
        material_id = material_ids[face_index] if face_index < len(material_ids) else -1
        style = styles[material_id] if 0 <= material_id < len(styles) else (DEFAULT_COLOR, DEFAULT_OPACITY)
        groups.setdefault(style, []).append(triangle)

    styled_meshes = [
        StyledMesh(vertices=vertices, faces=group_faces, color=color, opacity=opacity)
        for (color, opacity), group_faces in groups.items()
    ]

    return ElementMesh(element=element, styled_meshes=styled_meshes)


def iter_meshes_for_classes(
    model: ifcopenshell.file, ifc_classes: tuple[str, ...]
) -> Iterator[ElementMesh]:
    settings = _create_settings()

    for ifc_class in ifc_classes:
        for element in model.by_type(ifc_class):
            if element.Representation is None:
                continue
            shape = ifcopenshell.geom.create_shape(settings, element)
            yield _shape_to_mesh(element, shape)


def iter_pipe_meshes(model: ifcopenshell.file) -> Iterator[ElementMesh]:
    yield from iter_meshes_for_classes(model, PIPE_CLASSES)


def iter_all_product_meshes(model: ifcopenshell.file) -> Iterator[ElementMesh]:
    """Render every IfcProduct with geometry, regardless of class.

    Used as a first smoke test against arbitrary IFC files before real MEP
    content is available; iter_pipe_meshes stays the scoped extraction path.
    """
    settings = _create_settings()

    for element in model.by_type("IfcProduct"):
        if element.Representation is None:
            continue
        try:
            shape = ifcopenshell.geom.create_shape(settings, element)
        except RuntimeError:
            continue
        yield _shape_to_mesh(element, shape)
