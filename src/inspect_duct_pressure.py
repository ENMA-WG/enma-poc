from pathlib import Path
from collections import Counter
import csv
import json

import ifcopenshell
import ifcopenshell.util.element


IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")
DUCT_CSV = Path("output/ducts_detail.csv")
OUTPUT_FILE = Path("output/duct_pressure_inspection.csv")


PRESSURE_KEYWORDS = (
    "pressure",
    "workingpressure",
    "pressurerange",
    "staticpressure",
    "圧力",
    "静圧",
    "低圧",
    "高圧",
)


def clean(value):
    if value is None:
        return ""

    if isinstance(value, (str, int, float, bool)):
        return str(value)

    return str(value)


def find_pressure_properties(element):
    """
    Search occurrence + inherited type properties
    for pressure-related properties.
    """
    psets = ifcopenshell.util.element.get_psets(
        element,
        psets_only=True,
        should_inherit=True,
    )

    hits = []

    for pset_name, properties in psets.items():

        for prop_name, value in properties.items():

            if prop_name == "id":
                continue

            searchable = (
                f"{pset_name} {prop_name} {clean(value)}"
            ).lower()

            if any(
                keyword.lower() in searchable
                for keyword in PRESSURE_KEYWORDS
            ):
                hits.append(
                    {
                        "Pset": pset_name,
                        "Property": prop_name,
                        "Value": clean(value),
                    }
                )

    return hits


def get_common_pressure_values(element):
    """
    Explicitly inspect Pset_DuctSegmentTypeCommon.
    """
    psets = ifcopenshell.util.element.get_psets(
        element,
        psets_only=True,
        should_inherit=True,
    )

    common = psets.get(
        "Pset_DuctSegmentTypeCommon",
        {}
    )

    return (
        clean(common.get("WorkingPressure")),
        clean(common.get("PressureRange")),
    )


def main():

    print("=== DUCT PRESSURE INSPECTION ===")
    print()
    print(f"IFC    : {IFC_FILE}")
    print(f"Duct CSV: {DUCT_CSV}")
    print(f"Output : {OUTPUT_FILE}")
    print()

    model = ifcopenshell.open(str(IFC_FILE))

    # Read already established ENMA classifications.
    duct_info = {}

    with DUCT_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:
            duct_info[row["GlobalId"]] = {
                "AirType": row.get("AirType", ""),
                "Shape": row.get("Shape", ""),
                "SystemName": row.get("SystemName", ""),
                "SystemObjectType": row.get(
                    "SystemObjectType",
                    ""
                ),
            }

    rows = []

    working_pressure_counter = Counter()
    pressure_range_counter = Counter()
    pset_property_counter = Counter()

    working_pressure_present = 0
    pressure_range_present = 0
    any_pressure_property = 0

    for duct in model.by_type("IfcDuctSegment"):

        info = duct_info.get(
            duct.GlobalId,
            {}
        )

        working_pressure, pressure_range = (
            get_common_pressure_values(duct)
        )

        hits = find_pressure_properties(duct)

        if working_pressure:
            working_pressure_present += 1
            working_pressure_counter[
                working_pressure
            ] += 1

        if pressure_range:
            pressure_range_present += 1
            pressure_range_counter[
                pressure_range
            ] += 1

        if hits:
            any_pressure_property += 1

        for hit in hits:
            pset_property_counter[
                (
                    hit["Pset"],
                    hit["Property"],
                    hit["Value"],
                )
            ] += 1

        rows.append(
            {
                "GlobalId": duct.GlobalId,
                "Name": clean(
                    getattr(duct, "Name", None)
                ),
                "ObjectType": clean(
                    getattr(duct, "ObjectType", None)
                ),
                "AirType": info.get(
                    "AirType",
                    ""
                ),
                "Shape": info.get(
                    "Shape",
                    ""
                ),
                "SystemName": info.get(
                    "SystemName",
                    ""
                ),
                "SystemObjectType": info.get(
                    "SystemObjectType",
                    ""
                ),
                "WorkingPressure": working_pressure,
                "PressureRange": pressure_range,
                "PressurePropertyHits": json.dumps(
                    hits,
                    ensure_ascii=False,
                ),
            }
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fieldnames = [
        "GlobalId",
        "Name",
        "ObjectType",
        "AirType",
        "Shape",
        "SystemName",
        "SystemObjectType",
        "WorkingPressure",
        "PressureRange",
        "PressurePropertyHits",
    ]

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    print("=== RESULT ===")
    print(
        f"IfcDuctSegment        : {len(rows)}"
    )
    print(
        f"WorkingPressure       : "
        f"{working_pressure_present}/{len(rows)}"
    )
    print(
        f"PressureRange         : "
        f"{pressure_range_present}/{len(rows)}"
    )
    print(
        f"Any pressure property : "
        f"{any_pressure_property}/{len(rows)}"
    )

    print()
    print("--- WorkingPressure values ---")

    if working_pressure_counter:
        for value, count in (
            working_pressure_counter.most_common()
        ):
            print(
                f"{count:4d}  {value}"
            )
    else:
        print("(none)")

    print()
    print("--- PressureRange values ---")

    if pressure_range_counter:
        for value, count in (
            pressure_range_counter.most_common()
        ):
            print(
                f"{count:4d}  {value}"
            )
    else:
        print("(none)")

    print()
    print("--- All pressure-related properties ---")

    if pset_property_counter:

        for (
            pset,
            prop,
            value,
        ), count in (
            pset_property_counter.most_common()
        ):

            print(
                f"{count:4d}  "
                f"{pset}.{prop} = {value}"
            )

    else:
        print("(none)")

    print()
    print(
        f"CSV written           : {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()