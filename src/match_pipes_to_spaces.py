"""
match_pipes_to_spaces.py

ENMA-WG
Pipe / Architecture Space Matcher
Version 2 - Automatic Model Coordinate Alignment

目的
----
設備IFC (営繕BIMモデル_EM.ifc) の IfcPipeSegment と、
建築IFC (営繕BIMモデル_A.ifc) の IfcSpace を空間的に照合する。

Version 2 の主な機能
--------------------
1. 建築IFCと設備IFCの共通 IfcBuildingStorey を取得
2. 各StoreyのWorld Originを比較
3. モデル間の平行移動量を自動検出
4. 全共通Storeyで変換量が一致することを検証
5. MEP Geometryを建築座標系へ変換
6. Pipe中心点とSpace Bounding Boxを照合
7. INSIDE_SPACE / ABOVE_SPACE / NO_MATCH を分類
8. 判定根拠と座標変換情報をCSVへ保存

注意
----
Version 2ではPipe中心点による粗い空間判定を行う。
長い配管が複数Spaceを横断する場合の長さ分割は
今後のVersionで実装する。

Input
-----
data/営繕BIMモデル_A.ifc
data/営繕BIMモデル_EM.ifc

Output
------
output/pipe_space_matches.csv
"""

from __future__ import annotations

import csv
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element


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

OUTPUT_PATH = (
    PROJECT_ROOT
    / "output"
    / "pipe_space_matches.csv"
)


# ============================================================
# Parameters
# ============================================================

# XY Bounding Box tolerance [m]
XY_TOLERANCE = 0.01

# Space上端から何m上までを ABOVE_SPACE 候補とするか
ABOVE_SPACE_LIMIT = 2.0

# Storey Originの差がこの値以内なら
# 同一Translationとみなす [m]
TRANSLATION_TOLERANCE = 0.001

# 今回のIfcOpenShell GeometryはSI単位(m)で取得される。
# Placement座標はIFC project length unit。
# IFCの単位を自動取得してmへ変換する。
DEFAULT_LENGTH_SCALE_TO_METERS = 0.001


# ============================================================
# Basic utility
# ============================================================

def safe_text(value: Any) -> str:
    if value is None:
        return ""

    if hasattr(value, "wrappedValue"):
        value = value.wrappedValue

    return str(value)


def safe_float(value: Any, digits: int = 6) -> str:
    if value is None:
        return ""

    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return safe_text(value)


def unwrap_value(value: Any) -> Any:
    if value is None:
        return None

    if hasattr(value, "wrappedValue"):
        return value.wrappedValue

    return value


# ============================================================
# IFC unit handling
# ============================================================

def get_length_scale_to_meters(model) -> float:
    """
    IFC project length unit → meter の倍率を返す。

    例:
        millimetre -> 0.001
        metre      -> 1.0
    """

    try:
        projects = model.by_type("IfcProject")

        if not projects:
            return DEFAULT_LENGTH_SCALE_TO_METERS

        project = projects[0]
        units_context = getattr(
            project,
            "UnitsInContext",
            None,
        )

        if units_context is None:
            return DEFAULT_LENGTH_SCALE_TO_METERS

        for unit in units_context.Units:

            if not unit.is_a("IfcSIUnit"):
                continue

            if getattr(
                unit,
                "UnitType",
                None,
            ) != "LENGTHUNIT":
                continue

            name = safe_text(
                getattr(
                    unit,
                    "Name",
                    None,
                )
            ).upper()

            prefix = safe_text(
                getattr(
                    unit,
                    "Prefix",
                    None,
                )
            ).upper()

            if name == "METRE":

                factors = {
                    "": 1.0,
                    "MILLI": 0.001,
                    "CENTI": 0.01,
                    "DECI": 0.1,
                    "KILO": 1000.0,
                }

                return factors.get(
                    prefix,
                    1.0,
                )

    except Exception:
        pass

    return DEFAULT_LENGTH_SCALE_TO_METERS


# ============================================================
# Matrix functions for IFC placement
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
        a[1] * b[2]
        - a[2] * b[1],

        a[2] * b[0]
        - a[0] * b[2],

        a[0] * b[1]
        - a[1] * b[0],
    )


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


def get_direction(
    direction,
    default,
):
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
    if relative_placement is None:
        return identity_matrix()

    location = get_coordinates(
        getattr(
            relative_placement,
            "Location",
            None,
        )
    )

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
    累積Placement Matrixを返す。

    注意:
        Translation値はIFC project length unit。
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


def get_world_origin_m(
    entity,
    length_scale,
):
    placement = getattr(
        entity,
        "ObjectPlacement",
        None,
    )

    matrix = get_local_placement_matrix(
        placement
    )

    return (
        matrix[0][3] * length_scale,
        matrix[1][3] * length_scale,
        matrix[2][3] * length_scale,
    )


# ============================================================
# Model alignment
# ============================================================

def collect_storey_origins(
    model,
    length_scale,
):
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
        ).strip()

        if not name:
            continue

        result[name] = {
            "entity": storey,
            "origin":
                get_world_origin_m(
                    storey,
                    length_scale,
                ),
            "elevation":
                getattr(
                    storey,
                    "Elevation",
                    None,
                ),
        }

    return result


def calculate_model_translation(
    arch_model,
    mep_model,
    arch_scale,
    mep_scale,
):
    """
    MEP Geometry座標をArchitecture Geometry座標へ
    変換するTranslationを共通Storeyから算出する。

    transform:
        architecture = mep + translation
    """

    arch_storeys = (
        collect_storey_origins(
            arch_model,
            arch_scale,
        )
    )

    mep_storeys = (
        collect_storey_origins(
            mep_model,
            mep_scale,
        )
    )

    common_names = sorted(
        set(arch_storeys)
        & set(mep_storeys)
    )

    if not common_names:
        raise RuntimeError(
            "Architecture / MEP間に"
            "共通Storeyがありません。"
        )

    translations = []

    for name in common_names:

        arch_origin = (
            arch_storeys[name][
                "origin"
            ]
        )

        mep_origin = (
            mep_storeys[name][
                "origin"
            ]
        )

        translation = (
            arch_origin[0]
            - mep_origin[0],

            arch_origin[1]
            - mep_origin[1],

            arch_origin[2]
            - mep_origin[2],
        )

        translations.append(
            {
                "name": name,
                "arch_origin":
                    arch_origin,
                "mep_origin":
                    mep_origin,
                "translation":
                    translation,
            }
        )

    # ----------------------------------------
    # 平均Translation
    # ----------------------------------------

    tx = sum(
        item["translation"][0]
        for item in translations
    ) / len(translations)

    ty = sum(
        item["translation"][1]
        for item in translations
    ) / len(translations)

    tz = sum(
        item["translation"][2]
        for item in translations
    ) / len(translations)

    mean_translation = (
        tx,
        ty,
        tz,
    )

    # ----------------------------------------
    # 各Storeyとの差を検証
    # ----------------------------------------

    max_deviation = 0.0

    for item in translations:

        t = item["translation"]

        deviation = math.sqrt(
            (t[0] - tx) ** 2
            + (t[1] - ty) ** 2
            + (t[2] - tz) ** 2
        )

        item["deviation"] = (
            deviation
        )

        max_deviation = max(
            max_deviation,
            deviation,
        )

    consistent = (
        max_deviation
        <= TRANSLATION_TOLERANCE
    )

    return {
        "translation":
            mean_translation,

        "common_storeys":
            common_names,

        "details":
            translations,

        "max_deviation":
            max_deviation,

        "consistent":
            consistent,
    }


# ============================================================
# Geometry
# ============================================================

def create_geom_settings():
    settings = (
        ifcopenshell.geom.settings()
    )

    settings.set(
        settings.USE_WORLD_COORDS,
        True,
    )

    return settings


def get_bbox(
    element,
    settings,
):
    """
    IfcOpenShell GeometryからAABBを取得。
    座標単位は通常SI(m)。
    """

    try:

        shape = (
            ifcopenshell.geom.create_shape(
                settings,
                element,
            )
        )

        verts = list(
            shape.geometry.verts
        )

        if not verts:
            return None

        xs = verts[0::3]
        ys = verts[1::3]
        zs = verts[2::3]

        min_x = min(xs)
        min_y = min(ys)
        min_z = min(zs)

        max_x = max(xs)
        max_y = max(ys)
        max_z = max(zs)

        return {
            "min_x": min_x,
            "min_y": min_y,
            "min_z": min_z,

            "max_x": max_x,
            "max_y": max_y,
            "max_z": max_z,

            "center_x":
                (min_x + max_x) / 2.0,

            "center_y":
                (min_y + max_y) / 2.0,

            "center_z":
                (min_z + max_z) / 2.0,
        }

    except Exception:
        return None


def translate_bbox(
    bbox,
    translation,
):
    tx, ty, tz = translation

    return {
        "min_x":
            bbox["min_x"] + tx,

        "min_y":
            bbox["min_y"] + ty,

        "min_z":
            bbox["min_z"] + tz,

        "max_x":
            bbox["max_x"] + tx,

        "max_y":
            bbox["max_y"] + ty,

        "max_z":
            bbox["max_z"] + tz,

        "center_x":
            bbox["center_x"] + tx,

        "center_y":
            bbox["center_y"] + ty,

        "center_z":
            bbox["center_z"] + tz,
    }


# ============================================================
# Storey detection
# ============================================================

def get_storey(
    element,
):
    """
    可能な方法を順に使って
    IfcBuildingStoreyを探す。
    """

    # ----------------------------------------
    # 1. ifcopenshell.util.element
    # ----------------------------------------

    try:

        container = (
            ifcopenshell.util.element
            .get_container(
                element
            )
        )

        current = container
        visited = set()

        while current is not None:

            if current.id() in visited:
                break

            visited.add(
                current.id()
            )

            if current.is_a(
                "IfcBuildingStorey"
            ):
                return (
                    current,
                    "get_container",
                )

            decomposes = getattr(
                current,
                "Decomposes",
                [],
            )

            if not decomposes:
                break

            relation = decomposes[0]

            current = getattr(
                relation,
                "RelatingObject",
                None,
            )

    except Exception:
        pass

    # ----------------------------------------
    # 2. ContainedInStructure
    # ----------------------------------------

    try:

        for relation in getattr(
            element,
            "ContainedInStructure",
            [],
        ):

            structure = getattr(
                relation,
                "RelatingStructure",
                None,
            )

            if structure is not None:

                if structure.is_a(
                    "IfcBuildingStorey"
                ):
                    return (
                        structure,
                        "ContainedInStructure",
                    )

    except Exception:
        pass

    # ----------------------------------------
    # 3. Decomposes upward
    # ----------------------------------------

    current = element
    visited = set()

    while current is not None:

        if current.id() in visited:
            break

        visited.add(
            current.id()
        )

        if current.is_a(
            "IfcBuildingStorey"
        ):
            return (
                current,
                "Decomposes",
            )

        decomposes = getattr(
            current,
            "Decomposes",
            [],
        )

        if not decomposes:
            break

        relation = decomposes[0]

        current = getattr(
            relation,
            "RelatingObject",
            None,
        )

    return (
        None,
        "unknown",
    )


# ============================================================
# Property extraction
# ============================================================

def get_psets_flat(
    element,
):
    result = {}

    try:

        psets = (
            ifcopenshell.util.element
            .get_psets(
                element
            )
        )

    except Exception:
        return result

    for pset_name, properties in (
        psets.items()
    ):

        if not isinstance(
            properties,
            dict,
        ):
            continue

        for prop_name, value in (
            properties.items()
        ):

            if prop_name == "id":
                continue

            key = (
                f"{pset_name}."
                f"{prop_name}"
            )

            result[key] = (
                unwrap_value(value)
            )

    return result


def find_property_value(
    psets,
    keywords,
):
    """
    Pset.Property名にkeywordsのいずれかを含む
    最初の値を返す。
    """

    keywords_lower = [
        keyword.lower()
        for keyword in keywords
    ]

    for key, value in psets.items():

        key_lower = key.lower()

        if any(
            keyword in key_lower
            for keyword
            in keywords_lower
        ):

            if value not in (
                None,
                "",
            ):
                return value

    return None


# ============================================================
# Space index
# ============================================================

def build_space_index(
    arch_model,
    settings,
):
    spaces = []

    geometry_failed = 0

    for space in arch_model.by_type(
        "IfcSpace"
    ):

        bbox = get_bbox(
            space,
            settings,
        )

        if bbox is None:

            geometry_failed += 1
            continue

        storey, storey_method = (
            get_storey(space)
        )

        psets = get_psets_flat(
            space
        )

        spaces.append(
            {
                "entity":
                    space,

                "bbox":
                    bbox,

                "name":
                    safe_text(
                        getattr(
                            space,
                            "Name",
                            None,
                        )
                    ),

                "long_name":
                    safe_text(
                        getattr(
                            space,
                            "LongName",
                            None,
                        )
                    ),

                "storey":
                    safe_text(
                        getattr(
                            storey,
                            "Name",
                            None,
                        )
                    )
                    if storey
                    else "",

                "storey_method":
                    storey_method,

                "is_external":
                    find_property_value(
                        psets,
                        [
                            "IsExternal",
                        ],
                    ),

                "ceiling_covering":
                    find_property_value(
                        psets,
                        [
                            "CeilingCovering",
                        ],
                    ),
            }
        )

    return (
        spaces,
        geometry_failed,
    )


# ============================================================
# Space matching
# ============================================================

def match_point_to_spaces(
    point,
    spaces,
):
    x, y, z = point

    candidates = []

    for space in spaces:

        bbox = space["bbox"]

        # ------------------------------------
        # XY containment
        # ------------------------------------

        if not (
            bbox["min_x"]
            - XY_TOLERANCE
            <= x
            <= bbox["max_x"]
            + XY_TOLERANCE
        ):
            continue

        if not (
            bbox["min_y"]
            - XY_TOLERANCE
            <= y
            <= bbox["max_y"]
            + XY_TOLERANCE
        ):
            continue

        # ------------------------------------
        # Z relation
        # ------------------------------------

        if (
            bbox["min_z"]
            - XY_TOLERANCE
            <= z
            <= bbox["max_z"]
            + XY_TOLERANCE
        ):

            relation = (
                "INSIDE_SPACE"
            )

            z_distance = 0.0

            priority = 0

        elif (
            z > bbox["max_z"]
            and
            z <= (
                bbox["max_z"]
                + ABOVE_SPACE_LIMIT
            )
        ):

            relation = (
                "ABOVE_SPACE"
            )

            z_distance = (
                z
                - bbox["max_z"]
            )

            priority = 1

        else:
            continue

        candidates.append(
            {
                "space":
                    space,

                "relation":
                    relation,

                "z_distance":
                    z_distance,

                "priority":
                    priority,
            }
        )

    candidates.sort(
        key=lambda item: (
            item["priority"],
            item["z_distance"],
        )
    )

    if not candidates:
        return (
            None,
            [],
        )

    return (
        candidates[0],
        candidates,
    )


# ============================================================
# Coordinate range
# ============================================================

def print_bbox_range(
    label,
    bboxes,
):
    if not bboxes:
        print(
            f"      {label}: "
            "(no geometry)"
        )
        return

    print(
        f"      {label}:"
    )

    print(
        "        X : "
        f"{min(b['min_x'] for b in bboxes):.3f}"
        " .. "
        f"{max(b['max_x'] for b in bboxes):.3f}"
    )

    print(
        "        Y : "
        f"{min(b['min_y'] for b in bboxes):.3f}"
        " .. "
        f"{max(b['max_y'] for b in bboxes):.3f}"
    )

    print(
        "        Z : "
        f"{min(b['min_z'] for b in bboxes):.3f}"
        " .. "
        f"{max(b['max_z'] for b in bboxes):.3f}"
    )


# ============================================================
# Main
# ============================================================

def main() -> int:

    print("=" * 76)

    print(
        "ENMA-WG Pipe / Architecture Space Matcher"
    )

    print(
        "Version 2 - Automatic Model Coordinate Alignment"
    )

    print("=" * 76)

    print(
        f"Architecture : "
        f"{ARCH_IFC_PATH}"
    )

    print(
        f"MEP          : "
        f"{MEP_IFC_PATH}"
    )

    print(
        f"Output       : "
        f"{OUTPUT_PATH}"
    )

    print()

    # --------------------------------------------------------
    # File check
    # --------------------------------------------------------

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

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # 1. Open IFC
    # --------------------------------------------------------

    print(
        "[1/7] Opening IFC files..."
    )

    arch_model = ifcopenshell.open(
        str(ARCH_IFC_PATH)
    )

    mep_model = ifcopenshell.open(
        str(MEP_IFC_PATH)
    )

    print(
        "      Architecture schema : "
        f"{arch_model.schema}"
    )

    print(
        "      MEP schema          : "
        f"{mep_model.schema}"
    )

    # --------------------------------------------------------
    # 2. Units
    # --------------------------------------------------------

    print(
        "[2/7] Reading IFC units..."
    )

    arch_scale = (
        get_length_scale_to_meters(
            arch_model
        )
    )

    mep_scale = (
        get_length_scale_to_meters(
            mep_model
        )
    )

    print(
        "      Architecture "
        "length scale -> m : "
        f"{arch_scale}"
    )

    print(
        "      MEP "
        "length scale -> m          : "
        f"{mep_scale}"
    )

    # --------------------------------------------------------
    # 3. Coordinate alignment
    # --------------------------------------------------------

    print(
        "[3/7] Detecting model coordinate alignment..."
    )

    alignment = (
        calculate_model_translation(
            arch_model,
            mep_model,
            arch_scale,
            mep_scale,
        )
    )

    translation = (
        alignment["translation"]
    )

    print(
        "      Common storeys : "
        f"{len(alignment['common_storeys'])}"
    )

    print(
        "      "
        + ", ".join(
            alignment[
                "common_storeys"
            ]
        )
    )

    print()

    print(
        "      Storey translation checks:"
    )

    for item in alignment["details"]:

        tx, ty, tz = (
            item["translation"]
        )

        print(
            f"        "
            f"{item['name']:<12} "
            f"({tx:+.3f}, "
            f"{ty:+.3f}, "
            f"{tz:+.3f}) m"
        )

    print()

    print(
        "      Translation "
        "(MEP -> ARCH) : "
        f"({translation[0]:+.3f}, "
        f"{translation[1]:+.3f}, "
        f"{translation[2]:+.3f}) m"
    )

    print(
        "      Max deviation             : "
        f"{alignment['max_deviation']:.6f} m"
    )

    print(
        "      Consistency               : "
        f"{'OK' if alignment['consistent'] else 'FAILED'}"
    )

    if not alignment["consistent"]:

        print()
        print(
            "[ERROR] Storey間で"
            "Translationが一致しません。"
        )

        print(
            "        Version 2では"
            "平行移動だけを扱うため停止します。"
        )

        return 1

    # --------------------------------------------------------
    # 4. Geometry engine + Space index
    # --------------------------------------------------------

    print(
        "[4/7] Building architecture space index..."
    )

    settings = create_geom_settings()

    (
        spaces,
        space_geometry_failed,
    ) = build_space_index(
        arch_model,
        settings,
    )

    print(
        "      Space count : "
        f"{len(spaces)}"
    )

    print(
        "      Space geometry failed : "
        f"{space_geometry_failed}"
    )

    space_bboxes = [
        space["bbox"]
        for space in spaces
    ]

    print_bbox_range(
        "Architecture Space coordinate range",
        space_bboxes,
    )

    # --------------------------------------------------------
    # 5. Pipes
    # --------------------------------------------------------

    print(
        "[5/7] Reading IfcPipeSegment..."
    )

    pipes = mep_model.by_type(
        "IfcPipeSegment"
    )

    print(
        "      Pipe count : "
        f"{len(pipes)}"
    )

    pipe_geometry = {}

    pipe_geometry_failed = 0

    original_pipe_bboxes = []
    aligned_pipe_bboxes = []

    for pipe in pipes:

        bbox = get_bbox(
            pipe,
            settings,
        )

        if bbox is None:

            pipe_geometry_failed += 1
            continue

        aligned_bbox = translate_bbox(
            bbox,
            translation,
        )

        pipe_geometry[
            pipe.id()
        ] = {
            "original":
                bbox,
            "aligned":
                aligned_bbox,
        }

        original_pipe_bboxes.append(
            bbox
        )

        aligned_pipe_bboxes.append(
            aligned_bbox
        )

    print_bbox_range(
        "MEP Pipe coordinate range BEFORE alignment",
        original_pipe_bboxes,
    )

    print_bbox_range(
        "MEP Pipe coordinate range AFTER alignment",
        aligned_pipe_bboxes,
    )

    # --------------------------------------------------------
    # 6. Match
    # --------------------------------------------------------

    print(
        "[6/7] Matching pipes to spaces..."
    )

    rows = []

    relation_counter = Counter()

    matched_count = 0
    no_match_count = 0

    for index, pipe in enumerate(
        pipes,
        start=1,
    ):

        geom = pipe_geometry.get(
            pipe.id()
        )

        # ------------------------------------
        # Geometry failure
        # ------------------------------------

        if geom is None:

            relation_counter[
                "GEOMETRY_FAILED"
            ] += 1

            continue

        original_bbox = (
            geom["original"]
        )

        aligned_bbox = (
            geom["aligned"]
        )

        point = (
            aligned_bbox[
                "center_x"
            ],
            aligned_bbox[
                "center_y"
            ],
            aligned_bbox[
                "center_z"
            ],
        )

        (
            best,
            candidates,
        ) = match_point_to_spaces(
            point,
            spaces,
        )

        storey, storey_method = (
            get_storey(pipe)
        )

        pipe_storey = safe_text(
            getattr(
                storey,
                "Name",
                None,
            )
        ) if storey else ""

        psets = get_psets_flat(
            pipe
        )

        system_value = (
            find_property_value(
                psets,
                [
                    "System",
                    "系統",
                    "用途",
                ],
            )
        )

        diameter_value = (
            find_property_value(
                psets,
                [
                    "NominalDiameter",
                    "呼び径",
                    "口径",
                ],
            )
        )

        # ------------------------------------
        # No match
        # ------------------------------------

        if best is None:

            relation = (
                "NO_MATCH"
            )

            relation_counter[
                relation
            ] += 1

            no_match_count += 1

            rows.append(
                {
                    "No":
                        index,

                    "PipeGlobalId":
                        safe_text(
                            getattr(
                                pipe,
                                "GlobalId",
                                None,
                            )
                        ),

                    "PipeName":
                        safe_text(
                            getattr(
                                pipe,
                                "Name",
                                None,
                            )
                        ),

                    "PipeObjectType":
                        safe_text(
                            getattr(
                                pipe,
                                "ObjectType",
                                None,
                            )
                        ),

                    "PipeStorey":
                        pipe_storey,

                    "PipeStoreyMethod":
                        storey_method,

                    "System":
                        safe_text(
                            system_value
                        ),

                    "NominalDiameter":
                        safe_text(
                            diameter_value
                        ),

                    "OriginalCenterX":
                        safe_float(
                            original_bbox[
                                "center_x"
                            ]
                        ),

                    "OriginalCenterY":
                        safe_float(
                            original_bbox[
                                "center_y"
                            ]
                        ),

                    "OriginalCenterZ":
                        safe_float(
                            original_bbox[
                                "center_z"
                            ]
                        ),

                    "TranslationX":
                        safe_float(
                            translation[0]
                        ),

                    "TranslationY":
                        safe_float(
                            translation[1]
                        ),

                    "TranslationZ":
                        safe_float(
                            translation[2]
                        ),

                    "AlignedCenterX":
                        safe_float(
                            aligned_bbox[
                                "center_x"
                            ]
                        ),

                    "AlignedCenterY":
                        safe_float(
                            aligned_bbox[
                                "center_y"
                            ]
                        ),

                    "AlignedCenterZ":
                        safe_float(
                            aligned_bbox[
                                "center_z"
                            ]
                        ),

                    "MatchRelation":
                        relation,

                    "CandidateCount":
                        0,

                    "SpaceGlobalId":
                        "",

                    "SpaceName":
                        "",

                    "SpaceLongName":
                        "",

                    "SpaceStorey":
                        "",

                    "SpaceIsExternal":
                        "",

                    "CeilingCovering":
                        "",

                    "SpaceMinZ":
                        "",

                    "SpaceMaxZ":
                        "",

                    "PipeToSpaceTop":
                        "",

                    "MatchSource":
                        "ARCH_SPACE_GEOMETRY",

                    "MatchMethod":
                        "ALIGNED_AABB_CENTER",
                }
            )

        # ------------------------------------
        # Match
        # ------------------------------------

        else:

            relation = (
                best["relation"]
            )

            relation_counter[
                relation
            ] += 1

            matched_count += 1

            space = best["space"]
            space_entity = (
                space["entity"]
            )

            space_bbox = (
                space["bbox"]
            )

            pipe_to_space_top = (
                aligned_bbox[
                    "center_z"
                ]
                - space_bbox[
                    "max_z"
                ]
            )

            rows.append(
                {
                    "No":
                        index,

                    "PipeGlobalId":
                        safe_text(
                            getattr(
                                pipe,
                                "GlobalId",
                                None,
                            )
                        ),

                    "PipeName":
                        safe_text(
                            getattr(
                                pipe,
                                "Name",
                                None,
                            )
                        ),

                    "PipeObjectType":
                        safe_text(
                            getattr(
                                pipe,
                                "ObjectType",
                                None,
                            )
                        ),

                    "PipeStorey":
                        pipe_storey,

                    "PipeStoreyMethod":
                        storey_method,

                    "System":
                        safe_text(
                            system_value
                        ),

                    "NominalDiameter":
                        safe_text(
                            diameter_value
                        ),

                    "OriginalCenterX":
                        safe_float(
                            original_bbox[
                                "center_x"
                            ]
                        ),

                    "OriginalCenterY":
                        safe_float(
                            original_bbox[
                                "center_y"
                            ]
                        ),

                    "OriginalCenterZ":
                        safe_float(
                            original_bbox[
                                "center_z"
                            ]
                        ),

                    "TranslationX":
                        safe_float(
                            translation[0]
                        ),

                    "TranslationY":
                        safe_float(
                            translation[1]
                        ),

                    "TranslationZ":
                        safe_float(
                            translation[2]
                        ),

                    "AlignedCenterX":
                        safe_float(
                            aligned_bbox[
                                "center_x"
                            ]
                        ),

                    "AlignedCenterY":
                        safe_float(
                            aligned_bbox[
                                "center_y"
                            ]
                        ),

                    "AlignedCenterZ":
                        safe_float(
                            aligned_bbox[
                                "center_z"
                            ]
                        ),

                    "MatchRelation":
                        relation,

                    "CandidateCount":
                        len(candidates),

                    "SpaceGlobalId":
                        safe_text(
                            getattr(
                                space_entity,
                                "GlobalId",
                                None,
                            )
                        ),

                    "SpaceName":
                        space[
                            "name"
                        ],

                    "SpaceLongName":
                        space[
                            "long_name"
                        ],

                    "SpaceStorey":
                        space[
                            "storey"
                        ],

                    "SpaceIsExternal":
                        safe_text(
                            space[
                                "is_external"
                            ]
                        ),

                    "CeilingCovering":
                        safe_text(
                            space[
                                "ceiling_covering"
                            ]
                        ),

                    "SpaceMinZ":
                        safe_float(
                            space_bbox[
                                "min_z"
                            ]
                        ),

                    "SpaceMaxZ":
                        safe_float(
                            space_bbox[
                                "max_z"
                            ]
                        ),

                    "PipeToSpaceTop":
                        safe_float(
                            pipe_to_space_top
                        ),

                    "MatchSource":
                        "ARCH_SPACE_GEOMETRY",

                    "MatchMethod":
                        "ALIGNED_AABB_CENTER",
                }
            )

        if (
            index % 25 == 0
            or index == len(pipes)
        ):

            print(
                f"      "
                f"{index:>3}/"
                f"{len(pipes)} "
                "pipes processed"
            )

    # --------------------------------------------------------
    # 7. CSV
    # --------------------------------------------------------

    print(
        "[7/7] Writing CSV..."
    )

    fieldnames = [
        "No",

        "PipeGlobalId",
        "PipeName",
        "PipeObjectType",

        "PipeStorey",
        "PipeStoreyMethod",

        "System",
        "NominalDiameter",

        "OriginalCenterX",
        "OriginalCenterY",
        "OriginalCenterZ",

        "TranslationX",
        "TranslationY",
        "TranslationZ",

        "AlignedCenterX",
        "AlignedCenterY",
        "AlignedCenterZ",

        "MatchRelation",
        "CandidateCount",

        "SpaceGlobalId",
        "SpaceName",
        "SpaceLongName",
        "SpaceStorey",

        "SpaceIsExternal",
        "CeilingCovering",

        "SpaceMinZ",
        "SpaceMaxZ",

        "PipeToSpaceTop",

        "MatchSource",
        "MatchMethod",
    ]

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(
            rows
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("-" * 76)
    print("Summary")
    print("-" * 76)

    print(
        f"IfcSpace             : "
        f"{len(spaces)}"
    )

    print(
        f"IfcPipeSegment       : "
        f"{len(pipes)}"
    )

    print(
        f"Space geometry failed: "
        f"{space_geometry_failed}"
    )

    print(
        f"Pipe geometry failed : "
        f"{pipe_geometry_failed}"
    )

    print()

    print(
        "Coordinate alignment:"
    )

    print(
        f"  Common storeys      : "
        f"{len(alignment['common_storeys'])}"
    )

    print(
        "  Translation         : "
        f"({translation[0]:+.3f}, "
        f"{translation[1]:+.3f}, "
        f"{translation[2]:+.3f}) m"
    )

    print(
        f"  Consistency         : "
        f"{'OK' if alignment['consistent'] else 'FAILED'}"
    )

    print(
        f"  Max deviation       : "
        f"{alignment['max_deviation']:.6f} m"
    )

    print()

    print(
        f"Matched              : "
        f"{matched_count}"
    )

    print(
        f"No match             : "
        f"{no_match_count}"
    )

    print()
    print("Relations:")

    for relation, count in (
        relation_counter.most_common()
    ):

        print(
            f"  {relation:<22}"
            f"{count:>6}"
        )

    # ----------------------------------------
    # Candidate ambiguity
    # ----------------------------------------

    ambiguous_count = sum(
        1
        for row in rows
        if int(
            row[
                "CandidateCount"
            ]
        ) > 1
    )

    print()

    print(
        "Multiple candidates  : "
        f"{ambiguous_count}"
    )

    print()

    print(
        f"CSV : {OUTPUT_PATH}"
    )

    print()
    print("Done.")

    return 0


if __name__ == "__main__":
    sys.exit(main())