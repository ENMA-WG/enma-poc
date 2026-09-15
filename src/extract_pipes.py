from pathlib import Path
import csv
import math

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement


# ============================================================
# Settings
# ============================================================

IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")
OUTPUT_FILE = Path("output/pipes_detail.csv")

# 方向判定許容値
ANGLE_TOLERANCE_DEG = 1.0


# ============================================================
# Utility
# ============================================================

def safe_float(value):
    if value is None:
        return None

    try:
        if hasattr(value, "wrappedValue"):
            value = value.wrappedValue
        return float(value)
    except (TypeError, ValueError):
        return None


def find_property(psets, candidate_names):
    candidates = {name.lower() for name in candidate_names}

    for _, properties in psets.items():
        if not isinstance(properties, dict):
            continue

        for prop_name, value in properties.items():
            if prop_name.lower() in candidates:
                return value

    return None


def get_storey(element):
    container = ifcopenshell.util.element.get_container(element)

    while container:
        if container.is_a("IfcBuildingStorey"):
            return container.Name or ""

        container = ifcopenshell.util.element.get_container(container)

    return ""


# ============================================================
# Properties
# ============================================================

def get_pipe_properties(pipe):
    psets = ifcopenshell.util.element.get_psets(pipe)

    system_name = find_property(
        psets,
        [
            "SystemName",
            "System Name",
            "System",
            "系統",
            "系統名",
        ],
    )

    outside_diameter = find_property(
        psets,
        [
            "OuterDiameter",
            "OutsideDiameter",
            "NominalDiameter",
            "呼び径",
            "外径",
        ],
    )

    inside_diameter = find_property(
        psets,
        [
            "InnerDiameter",
            "InsideDiameter",
            "内径",
        ],
    )

    length = find_property(
        psets,
        [
            "Length",
            "NetLength",
            "NominalLength",
            "長さ",
        ],
    )

    return {
        "system": system_name or "",
        "outside_diameter": safe_float(outside_diameter),
        "inside_diameter": safe_float(inside_diameter),
        "length": safe_float(length),
    }

def get_distribution_system(pipe):
    """
    IfcPipeSegment が所属する IfcDistributionSystem を取得する。

    Returns:
        {
            "name": "CH 3",
            "object_type": "M031_CH冷温水(往)",
            "predefined_type": "HEATING",
            "count": 1,
        }

    複数Systemに所属している場合は " | " で連結する。
    """

    systems = []

    for rel in getattr(pipe, "HasAssignments", []) or []:

        if not rel.is_a("IfcRelAssignsToGroup"):
            continue

        group = rel.RelatingGroup

        if group is None:
            continue

        if not group.is_a("IfcDistributionSystem"):
            continue

        systems.append(group)

    if not systems:
        return {
            "name": "",
            "object_type": "",
            "predefined_type": "",
            "count": 0,
        }

    names = []
    object_types = []
    predefined_types = []

    for system in systems:

        name = getattr(system, "Name", None)
        object_type = getattr(system, "ObjectType", None)
        predefined_type = getattr(
            system,
            "PredefinedType",
            None,
        )

        if name:
            names.append(str(name))

        if object_type:
            object_types.append(str(object_type))

        if predefined_type:
            predefined_types.append(str(predefined_type))

    return {
        "name": " | ".join(dict.fromkeys(names)),
        "object_type": " | ".join(
            dict.fromkeys(object_types)
        ),
        "predefined_type": " | ".join(
            dict.fromkeys(predefined_types)
        ),
        "count": len(systems),
    }


def get_pipe_type_name(pipe):
    """
    IfcPipeSegment の IfcTypeObject.Name を取得する。
    例:
        配管タイプ:00_供給
        配管タイプ:00_排水
        配管タイプ:00_冷媒
    """

    type_obj = ifcopenshell.util.element.get_type(pipe)

    if type_obj is None:
        return ""

    return str(type_obj.Name or "")

# ============================================================
# Representation / pipe axis
# ============================================================

def iter_representation_items(item):
    """
    Representationを再帰的にたどる。
    IfcMappedItemにも対応する。
    """

    if item is None:
        return

    yield item

    if item.is_a("IfcMappedItem"):
        source = item.MappingSource

        if source and source.MappedRepresentation:
            for sub_item in source.MappedRepresentation.Items:
                yield from iter_representation_items(sub_item)

    elif item.is_a("IfcBooleanResult"):
        if item.FirstOperand:
            yield from iter_representation_items(item.FirstOperand)

        if item.SecondOperand:
            yield from iter_representation_items(item.SecondOperand)


def find_extruded_solid(pipe):
    """
    IfcPipeSegmentのRepresentationから
    IfcExtrudedAreaSolidを探す。
    """

    representation = pipe.Representation

    if not representation:
        return None

    for shape_rep in representation.Representations:

        for item in shape_rep.Items:

            for sub_item in iter_representation_items(item):

                if sub_item.is_a("IfcExtrudedAreaSolid"):
                    return sub_item

    return None


def normalize_vector(x, y, z):
    length = math.sqrt(x * x + y * y + z * z)

    if length == 0:
        return None

    return (
        x / length,
        y / length,
        z / length,
    )


def get_pipe_axis(pipe):
    """
    配管のIfcExtrudedAreaSolid.ExtrudedDirectionを取得し、
    PipeのObjectPlacementを使ってWorld方向へ変換する。

    Returns:
        (dx, dy, dz) normalized world vector
    """

    solid = find_extruded_solid(pipe)

    if solid is None:
        return None

    direction = solid.ExtrudedDirection

    if direction is None:
        return None

    ratios = list(direction.DirectionRatios)

    if len(ratios) == 2:
        local_dir = (
            float(ratios[0]),
            float(ratios[1]),
            0.0,
        )
    else:
        local_dir = (
            float(ratios[0]),
            float(ratios[1]),
            float(ratios[2]),
        )

    # ExtrudedAreaSolid自身のPositionも考慮
    if solid.Position:
        solid_matrix = ifcopenshell.util.placement.get_axis2placement(
            solid.Position
        )

        sx = (
            solid_matrix[0][0] * local_dir[0]
            + solid_matrix[0][1] * local_dir[1]
            + solid_matrix[0][2] * local_dir[2]
        )

        sy = (
            solid_matrix[1][0] * local_dir[0]
            + solid_matrix[1][1] * local_dir[1]
            + solid_matrix[1][2] * local_dir[2]
        )

        sz = (
            solid_matrix[2][0] * local_dir[0]
            + solid_matrix[2][1] * local_dir[1]
            + solid_matrix[2][2] * local_dir[2]
        )

        local_dir = (sx, sy, sz)

    # Pipe ObjectPlacement → World
    if pipe.ObjectPlacement:

        matrix = ifcopenshell.util.placement.get_local_placement(
            pipe.ObjectPlacement
        )

        wx = (
            matrix[0][0] * local_dir[0]
            + matrix[0][1] * local_dir[1]
            + matrix[0][2] * local_dir[2]
        )

        wy = (
            matrix[1][0] * local_dir[0]
            + matrix[1][1] * local_dir[1]
            + matrix[1][2] * local_dir[2]
        )

        wz = (
            matrix[2][0] * local_dir[0]
            + matrix[2][1] * local_dir[1]
            + matrix[2][2] * local_dir[2]
        )

    else:
        wx, wy, wz = local_dir

    return normalize_vector(wx, wy, wz)


# ============================================================
# Direction classification
# ============================================================

def classify_direction(axis):
    """
    World座標の配管軸から
    水平管 / 立管 / 斜め管 を判定。
    """

    if axis is None:
        return "不明"

    dx, dy, dz = axis

    abs_dz = abs(dz)

    horizontal_limit = math.sin(
        math.radians(ANGLE_TOLERANCE_DEG)
    )

    vertical_limit = math.cos(
        math.radians(ANGLE_TOLERANCE_DEG)
    )

    if abs_dz <= horizontal_limit:
        return "水平管"

    if abs_dz >= vertical_limit:
        return "立管"

    return "斜め管"


def calculate_angle(axis):
    """
    水平面からの角度。
    0° = 水平
    90° = 垂直
    """

    if axis is None:
        return None

    _, _, dz = axis

    dz = max(-1.0, min(1.0, dz))

    return math.degrees(
        math.asin(abs(dz))
    )


def calculate_slope(axis):
    """
    水平距離に対する高低差。
    例:
        0.01 -> 1/100
        0.02 -> 1/50
    """

    if axis is None:
        return None

    dx, dy, dz = axis

    horizontal = math.sqrt(
        dx * dx + dy * dy
    )

    if horizontal < 1e-9:
        return None

    return abs(dz) / horizontal


# ============================================================
# Geometry Z range
# ============================================================

def get_z_range(pipe, settings):

    try:
        shape = ifcopenshell.geom.create_shape(
            settings,
            pipe,
        )
    except Exception:
        return None, None

    verts = shape.geometry.verts

    if not verts:
        return None, None

    zs = [
        float(verts[i + 2])
        for i in range(0, len(verts), 3)
    ]

    return min(zs), max(zs)


# ============================================================
# Main
# ============================================================

def main():

    print(f"IFC : {IFC_FILE}")
    print(f"CSV : {OUTPUT_FILE}")

    if not IFC_FILE.exists():
        raise FileNotFoundError(IFC_FILE)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    model = ifcopenshell.open(
        str(IFC_FILE)
    )

    pipes = model.by_type(
        "IfcPipeSegment"
    )

    print(
        f"IfcPipeSegment count: {len(pipes)}"
    )

    settings = ifcopenshell.geom.settings()

    settings.set(
        settings.USE_WORLD_COORDS,
        True,
    )

    rows = []

    for index, pipe in enumerate(
        pipes,
        start=1,
    ):

        props = get_pipe_properties(pipe)

        pipe_type_name = get_pipe_type_name(pipe)

        system = get_distribution_system(pipe)
                        
        axis = get_pipe_axis(pipe)

        axis = get_pipe_axis(pipe)

        direction = classify_direction(axis)

        angle = calculate_angle(axis)

        slope = calculate_slope(axis)

        z_min, z_max = get_z_range(
            pipe,
            settings,
        )

        if axis:
            axis_x, axis_y, axis_z = axis
        else:
            axis_x = None
            axis_y = None
            axis_z = None

        if z_min is not None and z_max is not None:
            delta_z = z_max - z_min
        else:
            delta_z = None

        row = {
            "GlobalId": pipe.GlobalId,
            "Name": pipe.Name or "",
            "階": get_storey(pipe),
        
            # 配管Type
            "配管種別": pipe_type_name,
        
            # IfcDistributionSystem
            "系統コード": system["name"],
            "系統名称": system["object_type"],
            "IFC系統分類": system["predefined_type"],
            "系統所属数": system["count"],
        
            # Property / Quantity
            "外径": props["outside_diameter"],
            "内径": props["inside_diameter"],
            "長さ": props["length"],
        
            # Geometry
            "方向区分": direction,
            "軸DX": axis_x,
            "軸DY": axis_y,
            "軸DZ": axis_z,
            "水平面角度_deg": angle,
            "勾配": slope,
            "Z最低": z_min,
            "Z最高": z_max,
            "高低差": delta_z,
        }

        rows.append(row)

        axis_text = ""

        if axis:
            axis_text = (
                f"axis=("
                f"{axis_x:.4f}, "
                f"{axis_y:.4f}, "
                f"{axis_z:.4f})"
            )
        else:
            axis_text = "axis=(not found)"

        print(
            f"[{index:03d}/{len(pipes):03d}] "
            f"{pipe.GlobalId} "
            f"{row['階']} "
            f"{direction} "
            f"{axis_text}"
        )

    fieldnames = [
        "GlobalId",
        "Name",
        "階",
        "配管種別",
        "系統コード",
        "系統名称",
        "IFC系統分類",
        "系統所属数",
        "外径",
        "内径",
        "長さ",
        "方向区分",
        "軸DX",
        "軸DY",
        "軸DZ",
        "水平面角度_deg",
        "勾配",
        "Z最低",
        "Z最高",
        "高低差",
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)

    print()
    print(
        "========================================"
    )
    print("Completed")
    print(
        "========================================"
    )

    print(f"Pipes : {len(rows)}")
    print(f"CSV   : {OUTPUT_FILE}")

    summary = {}

    for row in rows:
        key = row["方向区分"]
        summary[key] = summary.get(key, 0) + 1

    print()
    print("Direction summary")

    for key, value in sorted(summary.items()):
        print(
            f"  {key}: {value}"
        )


if __name__ == "__main__":
    main()