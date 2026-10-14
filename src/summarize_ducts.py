"""
ENMA-WG PoC
Duct Quantity Summary

Input:
    output/ducts_detail.csv

Output:
    output/ducts_summary.csv

Summary key:
    AirType
    Shape
    Size

The script preserves geometry-derived duct dimensions.
It does not convert raw geometry dimensions to nominal sizes.
"""

from pathlib import Path
import csv
from collections import defaultdict


INPUT_FILE = Path("output/ducts_detail.csv")
OUTPUT_FILE = Path("output/ducts_summary.csv")


def parse_float(value):
    """Convert CSV value to float. Return None for blank/invalid values."""
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    try:
        return float(value)
    except ValueError:
        return None


def format_number(value):
    """
    Format a dimension without unnecessary trailing zeros.

    Examples:
        200.000 -> 200
        637.626 -> 637.626
        3.760 -> 3.76
    """
    if value is None:
        return ""

    return f"{value:.3f}".rstrip("0").rstrip(".")


def make_size_key(row):
    """
    Create an engineering-neutral size key from geometry-derived dimensions.

    ROUND:
        D200

    RECTANGULAR:
        750x637.626

    No nominal-size conversion is performed.
    """
    shape = (row.get("Shape") or "").strip().upper()

    if shape == "ROUND":
        diameter = parse_float(row.get("Diameter_mm"))

        if diameter is None:
            return "UNKNOWN"

        return f"D{format_number(diameter)}"

    if shape == "RECTANGULAR":
        width = parse_float(row.get("Width_mm"))
        height = parse_float(row.get("Height_mm"))

        if width is None or height is None:
            return "UNKNOWN"

        return f"{format_number(width)}x{format_number(height)}"

    return "UNKNOWN"


def main():
    print("=== ENMA DUCT SUMMARY ===")
    print()
    print(f"Input  : {INPUT_FILE}")
    print(f"Output : {OUTPUT_FILE}")
    print()

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input CSV not found: {INPUT_FILE}\n"
            "Run src/extract_ducts.py first."
        )

    summary = defaultdict(
        lambda: {
            "Count": 0,
            "Geometry_Length_mm": 0.0,
            "QTO_Length_mm": 0.0,
        }
    )

    total_rows = 0
    skipped_rows = 0

    with INPUT_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        required_columns = {
            "AirType",
            "Shape",
            "Diameter_mm",
            "Width_mm",
            "Height_mm",
            "Geometry_Length_mm",
            "QTO_Length_mm",
        }

        missing_columns = required_columns - set(reader.fieldnames or [])

        if missing_columns:
            raise ValueError(
                "Required columns are missing from ducts_detail.csv: "
                + ", ".join(sorted(missing_columns))
            )

        for row in reader:
            total_rows += 1

            air_type = (row.get("AirType") or "UNKNOWN").strip() or "UNKNOWN"
            shape = (row.get("Shape") or "UNKNOWN").strip() or "UNKNOWN"

            size = make_size_key(row)

            geometry_length = parse_float(row.get("Geometry_Length_mm"))
            qto_length = parse_float(row.get("QTO_Length_mm"))

            if geometry_length is None:
                skipped_rows += 1
                continue

            key = (
                air_type,
                shape,
                size,
            )

            summary[key]["Count"] += 1
            summary[key]["Geometry_Length_mm"] += geometry_length

            if qto_length is not None:
                summary[key]["QTO_Length_mm"] += qto_length

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "AirType",
        "Shape",
        "Size",
        "Count",
        "Geometry_Length_m",
        "QTO_Length_m",
        "Length_Difference_m",
    ]

    sorted_items = sorted(
        summary.items(),
        key=lambda item: (
            item[0][0],  # AirType
            item[0][1],  # Shape
            item[0][2],  # Size
        ),
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for (air_type, shape, size), values in sorted_items:

            geometry_length_m = (
                values["Geometry_Length_mm"] / 1000.0
            )

            qto_length_m = (
                values["QTO_Length_mm"] / 1000.0
            )

            difference_m = (
                geometry_length_m - qto_length_m
            )

            writer.writerow(
                {
                    "AirType": air_type,
                    "Shape": shape,
                    "Size": size,
                    "Count": values["Count"],
                    "Geometry_Length_m": f"{geometry_length_m:.3f}",
                    "QTO_Length_m": f"{qto_length_m:.3f}",
                    "Length_Difference_m": f"{difference_m:.6f}",
                }
            )

    total_geometry_length_m = sum(
        values["Geometry_Length_mm"]
        for values in summary.values()
    ) / 1000.0

    total_qto_length_m = sum(
        values["QTO_Length_mm"]
        for values in summary.values()
    ) / 1000.0

    print("=== RESULT ===")
    print(f"Input rows           : {total_rows}")
    print(f"Summary rows         : {len(summary)}")
    print(f"Skipped rows         : {skipped_rows}")
    print()
    print(f"Geometry total length: {total_geometry_length_m:.3f} m")
    print(f"QTO total length     : {total_qto_length_m:.3f} m")
    print()

    print("Air system")

    air_summary = defaultdict(
        lambda: {
            "Count": 0,
            "Length_mm": 0.0,
        }
    )

    for (air_type, shape, size), values in summary.items():
        air_summary[air_type]["Count"] += values["Count"]
        air_summary[air_type]["Length_mm"] += values["Geometry_Length_mm"]

    preferred_order = ["SA", "RA", "OA", "EA", "UNKNOWN"]

    for air_type in preferred_order:
        if air_type not in air_summary:
            continue

        count = air_summary[air_type]["Count"]
        length_m = air_summary[air_type]["Length_mm"] / 1000.0

        print(
            f"  {air_type:<7}"
            f": {count:4d} segments"
            f" / {length_m:10.3f} m"
        )

    # Print any unexpected AirType values as well.
    for air_type in sorted(
        set(air_summary.keys()) - set(preferred_order)
    ):
        count = air_summary[air_type]["Count"]
        length_m = air_summary[air_type]["Length_mm"] / 1000.0

        print(
            f"  {air_type:<7}"
            f": {count:4d} segments"
            f" / {length_m:10.3f} m"
        )

    print()
    print(f"CSV written          : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()