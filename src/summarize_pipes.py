"""
summarize_pipes.py

ENMA-WG Tokyo Summit 2026 PoC
MEP Quantity Takeoff - Step 1

Input:
    output/pipes_detail.csv

Output:
    output/pipes_summary.csv

Purpose:
    Aggregate IfcPipeSegment quantities by:

        Storey
        Distribution System
        Pipe Diameter
        Direction

    This script intentionally separates:

        IFC extraction
            ↓
        pipes_detail.csv
            ↓
        Quantity Takeoff
            ↓
        pipes_summary.csv

Usage:
    python src/summarize_pipes.py
"""

from pathlib import Path
import csv
from collections import defaultdict


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

INPUT_FILE = Path("output/pipes_detail.csv")
OUTPUT_FILE = Path("output/pipes_summary.csv")


# ------------------------------------------------------------
# Utility
# ------------------------------------------------------------

def to_float(value):
    """
    Convert CSV value to float.

    Blank / invalid values return None.
    """

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    try:
        return float(value)

    except ValueError:
        return None


def format_number(value, digits=3):
    """
    Format numeric output.
    """

    if value is None:
        return ""

    return round(value, digits)


# ------------------------------------------------------------
# Load detail CSV
# ------------------------------------------------------------

def load_pipe_details():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input CSV not found: {INPUT_FILE}"
        )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as f:

        reader = csv.DictReader(f)

        rows = list(reader)

    return rows


# ------------------------------------------------------------
# Aggregate
# ------------------------------------------------------------

def aggregate_pipes(rows):

    """
    Aggregate by:

        階
        系統コード
        系統名称
        IFC系統分類
        外径
        方向区分

    Length in pipes_detail.csv is currently treated
    as millimetres and converted to metres here.
    """

    groups = defaultdict(
        lambda: {
            "本数": 0,
            "長さ_mm": 0.0,
        }
    )

    skipped = 0

    for row in rows:

        storey = (
            row.get("階", "")
            or "(階不明)"
        ).strip()

        system_code = (
            row.get("系統コード", "")
            or "(系統コード不明)"
        ).strip()

        system_name = (
            row.get("系統名称", "")
            or "(系統不明)"
        ).strip()

        ifc_system_type = (
            row.get("IFC系統分類", "")
            or "(分類不明)"
        ).strip()

        outside_diameter = to_float(
            row.get("外径")
        )

        length_mm = to_float(
            row.get("長さ")
        )

        direction = (
            row.get("方向区分", "")
            or "(方向不明)"
        ).strip()

        # Quantity Takeoff requires length.
        if length_mm is None:
            skipped += 1
            continue

        # Diameter is kept as a numeric grouping key.
        diameter_key = (
            round(outside_diameter, 3)
            if outside_diameter is not None
            else None
        )

        key = (
            storey,
            system_code,
            system_name,
            ifc_system_type,
            diameter_key,
            direction,
        )

        groups[key]["本数"] += 1
        groups[key]["長さ_mm"] += length_mm

    return groups, skipped


# ------------------------------------------------------------
# Convert aggregation to CSV rows
# ------------------------------------------------------------

def make_summary_rows(groups):

    summary = []

    for key, values in groups.items():

        (
            storey,
            system_code,
            system_name,
            ifc_system_type,
            outside_diameter,
            direction,
        ) = key

        length_mm = values["長さ_mm"]

        summary.append(
            {
                "階": storey,
                "系統コード": system_code,
                "系統名称": system_name,
                "IFC系統分類": ifc_system_type,
                "外径_mm": format_number(
                    outside_diameter,
                    3,
                ),
                "方向区分": direction,
                "本数": values["本数"],
                "長さ_m": format_number(
                    length_mm / 1000.0,
                    3,
                ),
            }
        )

    # --------------------------------------------------------
    # Sort
    #
    # Human-readable ordering:
    #   Storey
    #   System
    #   Diameter
    #   Direction
    # --------------------------------------------------------

    def sort_key(row):

        diameter = to_float(
            row["外径_mm"]
        )

        if diameter is None:
            diameter = 999999

        return (
            row["階"],
            row["系統名称"],
            row["系統コード"],
            diameter,
            row["方向区分"],
        )

    summary.sort(
        key=sort_key
    )

    return summary


# ------------------------------------------------------------
# Write CSV
# ------------------------------------------------------------

def write_summary(rows):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "階",
        "系統コード",
        "系統名称",
        "IFC系統分類",
        "外径_mm",
        "方向区分",
        "本数",
        "長さ_m",
    ]

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(rows)


# ------------------------------------------------------------
# Console summary
# ------------------------------------------------------------

def print_summary(
    detail_rows,
    summary_rows,
    skipped,
):

    total_length_m = sum(
        to_float(row["長さ_m"]) or 0.0
        for row in summary_rows
    )

    horizontal_length_m = sum(
        to_float(row["長さ_m"]) or 0.0
        for row in summary_rows
        if row["方向区分"] == "水平管"
    )

    vertical_length_m = sum(
        to_float(row["長さ_m"]) or 0.0
        for row in summary_rows
        if row["方向区分"] == "立管"
    )

    sloped_length_m = sum(
        to_float(row["長さ_m"]) or 0.0
        for row in summary_rows
        if row["方向区分"] == "斜め管"
    )

    print()
    print("=" * 60)
    print("ENMA-WG MEP Quantity Takeoff")
    print("Tokyo Summit 2026 PoC - Step 1")
    print("=" * 60)

    print(
        f"Pipe segments : {len(detail_rows)}"
    )

    print(
        f"Summary rows  : {len(summary_rows)}"
    )

    print(
        f"Skipped       : {skipped}"
    )

    print()

    print(
        f"Total length      : "
        f"{total_length_m:.3f} m"
    )

    print(
        f"Horizontal length : "
        f"{horizontal_length_m:.3f} m"
    )

    print(
        f"Vertical length   : "
        f"{vertical_length_m:.3f} m"
    )

    print(
        f"Sloped length     : "
        f"{sloped_length_m:.3f} m"
    )

    print()

    print(
        f"CSV : {OUTPUT_FILE}"
    )

    print("=" * 60)


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    print(
        f"Input : {INPUT_FILE}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    detail_rows = load_pipe_details()

    groups, skipped = aggregate_pipes(
        detail_rows
    )

    summary_rows = make_summary_rows(
        groups
    )

    write_summary(
        summary_rows
    )

    print_summary(
        detail_rows,
        summary_rows,
        skipped,
    )


if __name__ == "__main__":
    main()