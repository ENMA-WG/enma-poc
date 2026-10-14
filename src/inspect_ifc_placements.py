"""
inspect_ifc_placements.py

建築IFCと設備IFCの空間配置（ObjectPlacement）を比較する診断ツール。

目的:
    営繕BIMモデル_A.ifc と 営繕BIMモデル_EM.ifc で
    Geometry の XY 座標が一致しない原因を調査する。

調査対象:
    IfcSite
    IfcBuilding
    IfcBuildingStorey

表示内容:
    - Name
    - GlobalId
    - ObjectPlacement
    - PlacementRelTo
    - RelativePlacement.Location
    - Axis
    - RefDirection
    - 累積 World Placement Matrix
    - World Origin
    - Storey Elevation

Input:
    data/営繕BIMモデル_A.ifc
    data/営繕BIMモデル_EM.ifc
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import ifcopenshell


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ARCH_IFC_PATH = (
    PROJECT_ROOT
    / "data"
    / "営繕BIMモデル_A.ifc"
)

MEP_IFC_PATH = (
    PROJECT_ROOT
    / "data"
    / "営繕BIMモデル_EM.ifc"
)


# ============================================================
# Utility
# ============================================================

def safe_text(value: Any) -> str:
    if value is None:
        return ""

    if hasattr(value, "wrappedValue"):
        value = value.wrappedValue

    return str(value)


def fmt_number(value: float) -> str:
    return f"{float(value):.6f}"


def fmt_vector(values) -> str:
    if values is None:
        return "(none)"

    return "(" + ", ".join(
        fmt_number(v) for v in values
    ) + ")"


# ============================================================
# Matrix functions
# ============================================================

def identity_matrix():
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def matrix_multiply(a, b):
    result = [
        [0.0] * 4
        for _ in range(4)
    ]

    for i in range(4):
        for j in range(4):
            result[i][j] = sum(
                a[i][k] * b[k][j]
                for k in range(4)
            )

    return result


def normalize(vector):
    length = math.sqrt(
        sum(v * v for v in vector)
    )

    if length == 0:
        return vector

    return tuple(
        v / length for v in vector
    )


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


# ============================================================
# IFC placement
# ============================================================

def get_coordinates(point):
    if point is None:
        return (0.0, 0.0, 0.0)

    coords = list(
        getattr(
            point,
            "Coordinates",
            (),
        )
    )

    while len(coords) < 3:
        coords.append(0.0)

    return tuple(
        float(v)
        for v in coords[:3]
    )


def get_direction(direction, default):
    if direction is None:
        return default

    ratios = list(
        getattr(
            direction,
            "DirectionRatios",
            (),
        )
    )

    while len(ratios) < 3:
        ratios.append(0.0)

    return normalize(
        tuple(
            float(v)
            for v in ratios[:3]
        )
    )


def axis2placement_matrix(
    relative_placement,
):
    """
    IfcAxis2Placement3D / IfcAxis2Placement2D
    から4x4変換行列を作る。
    """

    if relative_placement is None:
        return identity_matrix()

    location = get_coordinates(
        getattr(
            relative_placement,
            "Location",
            None,
        )
    )

    # ----------------------------------------
    # 3D placement
    # ----------------------------------------

    if relative_placement.is_a(
        "IfcAxis2Placement3D"
    ):

        z_axis = get_direction(
            getattr(
                relative_placement,
                "Axis",
                None,
            ),
            (0.0, 0.0, 1.0),
        )

        x_axis = get_direction(
            getattr(
                relative_placement,
                "RefDirection",
                None,
            ),
            (1.0, 0.0, 0.0),
        )

        y_axis = normalize(
            cross(
                z_axis,
                x_axis,
            )
        )

        # 再度Xを直交化
        x_axis = normalize(
            cross(
                y_axis,
                z_axis,
            )
        )

        return [
            [
                x_axis[0],
                y_axis[0],
                z_axis[0],
                location[0],
            ],
            [
                x_axis[1],
                y_axis[1],
                z_axis[1],
                location[1],
            ],
            [
                x_axis[2],
                y_axis[2],
                z_axis[2],
                location[2],
            ],
            [
                0.0,
                0.0,
                0.0,
                1.0,
            ],
        ]

    # ----------------------------------------
    # 2D placement
    # ----------------------------------------

    if relative_placement.is_a(
        "IfcAxis2Placement2D"
    ):

        ref = getattr(
            relative_placement,
            "RefDirection",
            None,
        )

        if ref is not None:
            ratios = list(
                ref.DirectionRatios
            )

            x = float(ratios[0])
            y = float(ratios[1])

            length = math.sqrt(
                x * x + y * y
            )

            if length != 0:
                x /= length
                y /= length
        else:
            x = 1.0
            y = 0.0

        return [
            [
                x,
                -y,
                0.0,
                location[0],
            ],
            [
                y,
                x,
                0.0,
                location[1],
            ],
            [
                0.0,
                0.0,
                1.0,
                location[2],
            ],
            [
                0.0,
                0.0,
                0.0,
                1.0,
            ],
        ]

    return identity_matrix()


def get_local_placement_matrix(
    object_placement,
):
    """
    IfcLocalPlacementを親方向へ再帰し、
    World座標系まで累積した4x4行列を返す。
    """

    if object_placement is None:
        return identity_matrix()

    if not object_placement.is_a(
        "IfcLocalPlacement"
    ):
        return identity_matrix()

    relative = getattr(
        object_placement,
        "RelativePlacement",
        None,
    )

    local_matrix = (
        axis2placement_matrix(
            relative
        )
    )

    parent = getattr(
        object_placement,
        "PlacementRelTo",
        None,
    )

    if parent is None:
        return local_matrix

    parent_matrix = (
        get_local_placement_matrix(
            parent
        )
    )

    return matrix_multiply(
        parent_matrix,
        local_matrix,
    )


# ============================================================
# Placement information
# ============================================================

def get_relative_info(
    object_placement,
):
    if object_placement is None:
        return {
            "location": None,
            "axis": None,
            "ref_direction": None,
        }

    relative = getattr(
        object_placement,
        "RelativePlacement",
        None,
    )

    if relative is None:
        return {
            "location": None,
            "axis": None,
            "ref_direction": None,
        }

    location = get_coordinates(
        getattr(
            relative,
            "Location",
            None,
        )
    )

    axis_obj = getattr(
        relative,
        "Axis",
        None,
    )

    ref_obj = getattr(
        relative,
        "RefDirection",
        None,
    )

    axis = None
    ref_direction = None

    if axis_obj is not None:
        axis = tuple(
            float(v)
            for v
            in axis_obj.DirectionRatios
        )

    if ref_obj is not None:
        ref_direction = tuple(
            float(v)
            for v
            in ref_obj.DirectionRatios
        )

    return {
        "location": location,
        "axis": axis,
        "ref_direction":
            ref_direction,
    }


def placement_depth(
    object_placement,
):
    depth = 0
    current = object_placement
    visited = set()

    while current is not None:

        if current.id() in visited:
            break

        visited.add(
            current.id()
        )

        parent = getattr(
            current,
            "PlacementRelTo",
            None,
        )

        if parent is None:
            break

        depth += 1
        current = parent

    return depth


# ============================================================
# Print entity
# ============================================================

def print_entity(entity):

    name = safe_text(
        getattr(
            entity,
            "Name",
            None,
        )
    )

    global_id = safe_text(
        getattr(
            entity,
            "GlobalId",
            None,
        )
    )

    placement = getattr(
        entity,
        "ObjectPlacement",
        None,
    )

    print()
    print(
        f"  {entity.is_a()} "
        f"#{entity.id()}"
    )

    print(
        f"    Name              : "
        f"{name}"
    )

    print(
        f"    GlobalId          : "
        f"{global_id}"
    )

    if entity.is_a(
        "IfcBuildingStorey"
    ):

        print(
            f"    Elevation         : "
            f"{safe_text(getattr(entity, 'Elevation', None))}"
        )

    if placement is None:

        print(
            "    ObjectPlacement   : "
            "(none)"
        )

        return

    print(
        f"    ObjectPlacement   : "
        f"{placement.is_a()} "
        f"#{placement.id()}"
    )

    print(
        f"    Placement depth   : "
        f"{placement_depth(placement)}"
    )

    parent = getattr(
        placement,
        "PlacementRelTo",
        None,
    )

    if parent is not None:

        print(
            f"    PlacementRelTo    : "
            f"{parent.is_a()} "
            f"#{parent.id()}"
        )

    else:

        print(
            "    PlacementRelTo    : "
            "(none)"
        )

    relative_info = (
        get_relative_info(
            placement
        )
    )

    print(
        f"    Relative Location : "
        f"{fmt_vector(relative_info['location'])}"
    )

    print(
        f"    Axis              : "
        f"{fmt_vector(relative_info['axis'])}"
    )

    print(
        f"    RefDirection      : "
        f"{fmt_vector(relative_info['ref_direction'])}"
    )

    world_matrix = (
        get_local_placement_matrix(
            placement
        )
    )

    world_origin = (
        world_matrix[0][3],
        world_matrix[1][3],
        world_matrix[2][3],
    )

    print(
        f"    World Origin      : "
        f"{fmt_vector(world_origin)}"
    )

    print("    World Matrix      :")

    for matrix_row in world_matrix:

        print(
            "      "
            + " ".join(
                f"{value:12.6f}"
                for value
                in matrix_row
            )
        )


# ============================================================
# IFC summary
# ============================================================

def inspect_model(
    label,
    path,
):

    print()
    print("=" * 78)
    print(label)
    print("=" * 78)

    print(
        f"File   : {path}"
    )

    model = ifcopenshell.open(
        str(path)
    )

    print(
        f"Schema : {model.schema}"
    )

    print()

    entity_types = [
        "IfcSite",
        "IfcBuilding",
        "IfcBuildingStorey",
    ]

    for entity_type in entity_types:

        entities = model.by_type(
            entity_type
        )

        print(
            f"{entity_type}: "
            f"{len(entities)}"
        )

        for entity in entities:
            print_entity(entity)

    return model


# ============================================================
# Storey comparison
# ============================================================

def collect_storeys(model):

    result = {}

    for storey in model.by_type(
        "IfcBuildingStorey"
    ):

        name = safe_text(
            getattr(
                storey,
                "Name",
                None,
            )
        )

        placement = getattr(
            storey,
            "ObjectPlacement",
            None,
        )

        matrix = (
            get_local_placement_matrix(
                placement
            )
        )

        origin = (
            matrix[0][3],
            matrix[1][3],
            matrix[2][3],
        )

        result[name] = {
            "entity": storey,
            "origin": origin,
            "elevation":
                getattr(
                    storey,
                    "Elevation",
                    None,
                ),
        }

    return result


def compare_storeys(
    arch_model,
    mep_model,
):

    print()
    print("=" * 78)
    print(
        "ARCHITECTURE / MEP STOREY COMPARISON"
    )
    print("=" * 78)

    arch_storeys = collect_storeys(
        arch_model
    )

    mep_storeys = collect_storeys(
        mep_model
    )

    names = sorted(
        set(arch_storeys)
        | set(mep_storeys)
    )

    for name in names:

        arch = arch_storeys.get(
            name
        )

        mep = mep_storeys.get(
            name
        )

        print()
        print(
            f"Storey : {name}"
        )

        if arch:

            print(
                "  ARCH World Origin : "
                f"{fmt_vector(arch['origin'])}"
            )

            print(
                "  ARCH Elevation    : "
                f"{safe_text(arch['elevation'])}"
            )

        else:

            print(
                "  ARCH              : "
                "(not found)"
            )

        if mep:

            print(
                "  MEP  World Origin : "
                f"{fmt_vector(mep['origin'])}"
            )

            print(
                "  MEP  Elevation    : "
                f"{safe_text(mep['elevation'])}"
            )

        else:

            print(
                "  MEP               : "
                "(not found)"
            )

        if arch and mep:

            dx = (
                mep["origin"][0]
                - arch["origin"][0]
            )

            dy = (
                mep["origin"][1]
                - arch["origin"][1]
            )

            dz = (
                mep["origin"][2]
                - arch["origin"][2]
            )

            print(
                "  MEP - ARCH        : "
                f"({dx:.6f}, "
                f"{dy:.6f}, "
                f"{dz:.6f})"
            )


# ============================================================
# Main
# ============================================================

def main() -> int:

    print("=" * 78)

    print(
        "ENMA-WG IFC Placement Inspector"
    )

    print(
        "Architecture / MEP Coordinate Diagnostics"
    )

    print("=" * 78)

    for path in [
        ARCH_IFC_PATH,
        MEP_IFC_PATH,
    ]:

        if not path.exists():

            print(
                f"[ERROR] File not found: "
                f"{path}"
            )

            return 1

    try:

        arch_model = inspect_model(
            "ARCHITECTURE IFC",
            ARCH_IFC_PATH,
        )

        mep_model = inspect_model(
            "MEP IFC",
            MEP_IFC_PATH,
        )

        compare_storeys(
            arch_model,
            mep_model,
        )

    except Exception as exc:

        print()
        print(
            f"[ERROR] {type(exc).__name__}: "
            f"{exc}"
        )

        return 1

    print()
    print("=" * 78)
    print("Done.")
    print("=" * 78)

    return 0


if __name__ == "__main__":
    sys.exit(main())