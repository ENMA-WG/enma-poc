from pathlib import Path

import ifcopenshell
import ifcopenshell.geom


IFC_FILE = Path("data/Ifc4_Revit_MEP.ifc")
TARGET_GID = "20CwKgKhbCIP4TTJ5euRpM"


def get_bbox(element):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)

    shape = ifcopenshell.geom.create_shape(settings, element)
    verts = shape.geometry.verts

    xs = verts[0::3]
    ys = verts[1::3]
    zs = verts[2::3]

    return {
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
        "min_z": min(zs),
        "max_z": max(zs),
    }


def get_storey(element):
    """
    Return the IfcBuildingStorey associated with an element.

    Priority:
      1. ContainedInStructure
      2. Decomposes / IfcRelAggregates

    IfcSpace is commonly related to IfcBuildingStorey through
    IfcRelAggregates rather than IfcRelContainedInSpatialStructure.
    """

    # 1. Normal spatial containment
    for rel in getattr(element, "ContainedInStructure", []):
        structure = getattr(rel, "RelatingStructure", None)

        if structure and structure.is_a("IfcBuildingStorey"):
            return structure.Name or ""

    # 2. Spatial decomposition, typically used by IfcSpace
    for rel in getattr(element, "Decomposes", []):
        relating_object = getattr(rel, "RelatingObject", None)

        if relating_object and relating_object.is_a("IfcBuildingStorey"):
            return relating_object.Name or ""

    return ""

model = ifcopenshell.open(str(IFC_FILE))

duct = model.by_guid(TARGET_GID)
duct_bbox = get_bbox(duct)

cx = (duct_bbox["min_x"] + duct_bbox["max_x"]) / 2
cy = (duct_bbox["min_y"] + duct_bbox["max_y"]) / 2
cz = (duct_bbox["min_z"] + duct_bbox["max_z"]) / 2

print()
print("TARGET DUCT")
print("-----------")
print("GlobalId :", duct.GlobalId)
print("Storey   :", get_storey(duct))
print(f"Center   : X={cx:.3f}, Y={cy:.3f}, Z={cz:.3f}")

print()
print("LEVEL 3 SPACES")
print("--------------")

for space in model.by_type("IfcSpace"):

    if get_storey(space) != "Level 3":
        continue

    try:
        bbox = get_bbox(space)
    except Exception:
        continue

    xy_inside = (
        bbox["min_x"] <= cx <= bbox["max_x"]
        and bbox["min_y"] <= cy <= bbox["max_y"]
    )

    z_inside = bbox["min_z"] <= cz <= bbox["max_z"]

    print(
        f"{space.id():6d} | "
        f"{space.Name or '':10s} | "
        f"{space.LongName or '':25s} | "
        f"X={bbox['min_x']:.2f}..{bbox['max_x']:.2f} | "
        f"Y={bbox['min_y']:.2f}..{bbox['max_y']:.2f} | "
        f"Z={bbox['min_z']:.2f}..{bbox['max_z']:.2f} | "
        f"XY={xy_inside} | Z={z_inside}"
    )