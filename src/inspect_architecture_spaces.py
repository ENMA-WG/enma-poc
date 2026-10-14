"""
inspect_architecture_spaces.py

営繕BIMモデル_A.ifc に含まれる IfcSpace を棚卸しする。

Version 2
---------
1. IfcSpace の所属階取得を改善
2. IfcSpace Geometry の Bounding Box を取得
3. PropertySet を CSV に展開

目的:
    建築IFCから設備積算に必要な「施工場所」を推定できるか検討するため、
    IfcSpace の基本属性、所属階、PropertySet、空間座標範囲を CSV に出力する。

Input:
    data/営繕BIMモデル_A.ifc

Output:
    output/architecture_spaces.csv
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element


# ------------------------------------------------------------
# Path settings
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

IFC_PATH = PROJECT_ROOT / "data" / "営繕BIMモデル_A.ifc"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_CSV = OUTPUT_DIR / "architecture_spaces.csv"


# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------

def safe_text(value: Any) -> str:
    """None や IFC 値を CSV に安全に出力できる文字列へ変換する。"""
    if value is None:
        return ""

    if hasattr(value, "wrappedValue"):
        value = value.wrappedValue

    return str(value)


def safe_float(value: Any, digits: int = 3) -> str:
    """数値を CSV 出力用文字列へ変換する。"""
    if value is None:
        return ""

    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return ""


# ------------------------------------------------------------
# Storey detection
# ------------------------------------------------------------

def get_storey_from_container(space):
    """
    IfcOpenShell utility を使って直接 container を取得する。
    """
    try:
        container = ifcopenshell.util.element.get_container(space)

        if container and container.is_a("IfcBuildingStorey"):
            return container

    except Exception:
        pass

    return None


def get_storey_from_decomposition(space):
    """
    IfcRelAggregates / Decomposes をたどって IfcBuildingStorey を探す。

    Revit等では IfcSpace が IfcBuildingStorey に直接 contained されず、
    decomposition 関係になっている場合があるため、そのケースを補完する。
    """
    current = space
    visited = set()

    for _ in range(20):

        current_id = current.id()

        if current_id in visited:
            break

        visited.add(current_id)

        # ----------------------------------------------------
        # Decomposes:
        # child -> parent
        # ----------------------------------------------------

        decomposes = getattr(current, "Decomposes", None) or []

        for rel in decomposes:

            parent = getattr(rel, "RelatingObject", None)

            if parent is None:
                continue

            if parent.is_a("IfcBuildingStorey"):
                return parent

            current = parent
            break

        else:
            break

    return None


def get_storey_from_containment(space):
    """
    IfcRelContainedInSpatialStructure を直接確認する。
    """
    contained_in = getattr(space, "ContainedInStructure", None) or []

    for rel in contained_in:

        structure = getattr(rel, "RelatingStructure", None)

        if structure is None:
            continue

        if structure.is_a("IfcBuildingStorey"):
            return structure

    return None


def get_storey(space):
    """
    複数の方法で IfcSpace の所属 IfcBuildingStorey を取得する。

    Returns:
        (
            storey_name,
            storey_long_name,
            storey_elevation,
            detection_method
        )
    """

    # Method 1
    storey = get_storey_from_container(space)

    if storey:
        return (
            safe_text(getattr(storey, "Name", None)),
            safe_text(getattr(storey, "LongName", None)),
            safe_text(getattr(storey, "Elevation", None)),
            "get_container",
        )

    # Method 2
    storey = get_storey_from_containment(space)

    if storey:
        return (
            safe_text(getattr(storey, "Name", None)),
            safe_text(getattr(storey, "LongName", None)),
            safe_text(getattr(storey, "Elevation", None)),
            "ContainedInStructure",
        )

    # Method 3
    storey = get_storey_from_decomposition(space)

    if storey:
        return (
            safe_text(getattr(storey, "Name", None)),
            safe_text(getattr(storey, "LongName", None)),
            safe_text(getattr(storey, "Elevation", None)),
            "Decomposes",
        )

    return "", "", "", "unknown"


# ------------------------------------------------------------
# PropertySet
# ------------------------------------------------------------

def flatten_properties(space) -> dict[str, str]:
    """
    IfcSpace の PropertySet を

        Pset名.Property名 = 値

    の形式で1階層の辞書へ展開する。
    """

    result: dict[str, str] = {}

    try:
        psets = ifcopenshell.util.element.get_psets(
            space,
            psets_only=True,
        )
    except Exception:
        return result

    for pset_name, properties in psets.items():

        for property_name, value in properties.items():

            # get_psets() が付加する内部IDは今回不要
            if property_name == "id":
                continue

            column_name = f"{pset_name}.{property_name}"

            result[column_name] = safe_text(value)

    return result


# ------------------------------------------------------------
# Geometry
# ------------------------------------------------------------

def create_geometry_settings():
    """
    IfcOpenShell Geometry Engine の設定を作成する。

    USE_WORLD_COORDS=True とし、
    Spaceごとのローカル座標ではなく建物全体の座標で取得する。
    """

    settings = ifcopenshell.geom.settings()

    settings.set(
        settings.USE_WORLD_COORDS,
        True,
    )

    return settings


def get_space_bbox(space, settings):
    """
    IfcSpace の Geometry から Bounding Box を取得する。

    Returns:
        {
            min_x,
            min_y,
            min_z,
            max_x,
            max_y,
            max_z,
            size_x,
            size_y,
            size_z
        }

    Geometry を生成できない場合は None。
    """

    try:
        shape = ifcopenshell.geom.create_shape(
            settings,
            space,
        )

        verts = shape.geometry.verts

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
            "size_x": max_x - min_x,
            "size_y": max_y - min_y,
            "size_z": max_z - min_z,
        }

    except Exception:
        return None


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main() -> int:

    print("=" * 70)
    print("ENMA-WG Architecture Space Inspector")
    print("Version 2 - Storey + Geometry")
    print("=" * 70)

    print(f"IFC    : {IFC_PATH}")
    print(f"Output : {OUTPUT_CSV}")
    print()

    # --------------------------------------------------------
    # Check input file
    # --------------------------------------------------------

    if not IFC_PATH.exists():

        print("[ERROR] IFC file not found.")
        print(f"        {IFC_PATH}")

        return 1

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Open IFC
    # --------------------------------------------------------

    print("[1/5] Opening IFC file...")

    try:
        model = ifcopenshell.open(
            str(IFC_PATH)
        )

    except Exception as exc:

        print(
            f"[ERROR] Failed to open IFC: {exc}"
        )

        return 1

    print(f"      Schema : {model.schema}")

    # --------------------------------------------------------
    # Get spaces
    # --------------------------------------------------------

    print("[2/5] Reading IfcSpace...")

    spaces = model.by_type("IfcSpace")

    print(
        f"      IfcSpace count : {len(spaces)}"
    )

    if not spaces:

        print("[WARN] No IfcSpace found.")

        return 0

    # --------------------------------------------------------
    # Geometry settings
    # --------------------------------------------------------

    print("[3/5] Preparing geometry engine...")

    geom_settings = create_geometry_settings()

    # --------------------------------------------------------
    # Collect data
    # --------------------------------------------------------

    print(
        "[4/5] Collecting storey, geometry and PropertySets..."
    )

    rows: list[dict[str, str]] = []

    property_columns: set[str] = set()

    geometry_success = 0
    geometry_failed = 0

    storey_method_counts: dict[str, int] = {}

    for index, space in enumerate(
        spaces,
        start=1,
    ):

        (
            storey_name,
            storey_long_name,
            storey_elevation,
            storey_method,
        ) = get_storey(space)

        storey_method_counts[storey_method] = (
            storey_method_counts.get(
                storey_method,
                0,
            )
            + 1
        )

        # ----------------------------------------------------
        # Geometry
        # ----------------------------------------------------

        bbox = get_space_bbox(
            space,
            geom_settings,
        )

        if bbox:
            geometry_success += 1
        else:
            geometry_failed += 1

        # ----------------------------------------------------
        # PropertySet
        # ----------------------------------------------------

        properties = flatten_properties(space)

        property_columns.update(
            properties.keys()
        )

        # ----------------------------------------------------
        # Base data
        # ----------------------------------------------------

        row = {
            "No": str(index),
            "IfcClass": space.is_a(),
            "GlobalId": safe_text(
                getattr(space, "GlobalId", None)
            ),
            "Name": safe_text(
                getattr(space, "Name", None)
            ),
            "LongName": safe_text(
                getattr(space, "LongName", None)
            ),
            "ObjectType": safe_text(
                getattr(space, "ObjectType", None)
            ),
            "PredefinedType": safe_text(
                getattr(space, "PredefinedType", None)
            ),
            "StoreyName": storey_name,
            "StoreyLongName": storey_long_name,
            "StoreyElevation": storey_elevation,
            "StoreyDetectionMethod": storey_method,
        }

        # ----------------------------------------------------
        # Bounding Box
        # ----------------------------------------------------

        if bbox:

            row.update(
                {
                    "MinX": safe_float(
                        bbox["min_x"]
                    ),
                    "MinY": safe_float(
                        bbox["min_y"]
                    ),
                    "MinZ": safe_float(
                        bbox["min_z"]
                    ),
                    "MaxX": safe_float(
                        bbox["max_x"]
                    ),
                    "MaxY": safe_float(
                        bbox["max_y"]
                    ),
                    "MaxZ": safe_float(
                        bbox["max_z"]
                    ),
                    "SizeX": safe_float(
                        bbox["size_x"]
                    ),
                    "SizeY": safe_float(
                        bbox["size_y"]
                    ),
                    "SizeZ": safe_float(
                        bbox["size_z"]
                    ),
                    "GeometryStatus": "OK",
                }
            )

        else:

            row.update(
                {
                    "MinX": "",
                    "MinY": "",
                    "MinZ": "",
                    "MaxX": "",
                    "MaxY": "",
                    "MaxZ": "",
                    "SizeX": "",
                    "SizeY": "",
                    "SizeZ": "",
                    "GeometryStatus": "FAILED",
                }
            )

        row.update(properties)

        rows.append(row)

        # Progress
        if (
            index % 20 == 0
            or index == len(spaces)
        ):

            print(
                f"      {index:>3}/{len(spaces)} spaces processed"
            )

    # --------------------------------------------------------
    # Write CSV
    # --------------------------------------------------------

    print("[5/5] Writing CSV...")

    base_columns = [
        "No",
        "IfcClass",
        "GlobalId",
        "Name",
        "LongName",
        "ObjectType",
        "PredefinedType",
        "StoreyName",
        "StoreyLongName",
        "StoreyElevation",
        "StoreyDetectionMethod",
        "MinX",
        "MinY",
        "MinZ",
        "MaxX",
        "MaxY",
        "MaxZ",
        "SizeX",
        "SizeY",
        "SizeZ",
        "GeometryStatus",
    ]

    sorted_property_columns = sorted(
        property_columns
    )

    fieldnames = (
        base_columns
        + sorted_property_columns
    )

    with OUTPUT_CSV.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as csvfile:

        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(row)

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print("Summary")
    print("-" * 70)

    print(
        f"IfcSpace             : {len(spaces)}"
    )

    print(
        f"Property columns     : "
        f"{len(sorted_property_columns)}"
    )

    print(
        f"Geometry OK          : "
        f"{geometry_success}"
    )

    print(
        f"Geometry FAILED      : "
        f"{geometry_failed}"
    )

    print(
        f"CSV rows             : {len(rows)}"
    )

    print(
        f"CSV                  : {OUTPUT_CSV}"
    )

    # --------------------------------------------------------
    # Storey detection summary
    # --------------------------------------------------------

    print()
    print("Storey detection:")

    for method, count in sorted(
        storey_method_counts.items()
    ):

        print(
            f"  {method:<30} {count:>4}"
        )

    # --------------------------------------------------------
    # Storey summary
    # --------------------------------------------------------

    print()
    print("Storeys:")

    storey_counts: dict[str, int] = {}

    for row in rows:

        name = (
            row["StoreyName"]
            or "(unknown)"
        )

        storey_counts[name] = (
            storey_counts.get(
                name,
                0,
            )
            + 1
        )

    for name, count in sorted(
        storey_counts.items()
    ):

        print(
            f"  {name:<30} {count:>4}"
        )

    print()
    print("Done.")

    return 0


if __name__ == "__main__":
    sys.exit(main())