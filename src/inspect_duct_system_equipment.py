from collections import Counter, defaultdict
from pathlib import Path
import csv

import ifcopenshell


IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")
OUTPUT_FILE = Path("output/duct_system_equipment.csv")


def safe_value(obj, attr):
    """Return an IFC attribute as a printable string."""
    value = getattr(obj, attr, None)
    if value is None:
        return ""
    return str(value)


def main():
    print("=== DUCT SYSTEM EQUIPMENT INSPECTION ===")
    print()
    print(f"IFC   : {IFC_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print()

    model = ifcopenshell.open(str(IFC_FILE))

    systems = model.by_type("IfcDistributionSystem")

    rows = []
    class_counter = Counter()
    non_duct_counter = Counter()
    system_class_counter = defaultdict(Counter)

    used_systems = 0
    total_related_elements = 0

    for system in systems:
        related_elements = []

        # IfcDistributionSystem inherits from IfcGroup.
        # Group membership is represented by IfcRelAssignsToGroup.
        for rel in getattr(system, "IsGroupedBy", []) or []:
            for obj in getattr(rel, "RelatedObjects", []) or []:
                related_elements.append(obj)

        if related_elements:
            used_systems += 1

        for element in related_elements:
            ifc_class = element.is_a()

            class_counter[ifc_class] += 1
            system_class_counter[system.id()][ifc_class] += 1
            total_related_elements += 1

            if ifc_class != "IfcDuctSegment":
                non_duct_counter[ifc_class] += 1

            rows.append(
                {
                    "system_global_id": safe_value(system, "GlobalId"),
                    "system_name": safe_value(system, "Name"),
                    "system_object_type": safe_value(system, "ObjectType"),
                    "system_predefined_type": safe_value(
                        system, "PredefinedType"
                    ),
                    "element_global_id": safe_value(element, "GlobalId"),
                    "element_ifc_class": ifc_class,
                    "element_name": safe_value(element, "Name"),
                    "element_object_type": safe_value(
                        element, "ObjectType"
                    ),
                    "element_predefined_type": safe_value(
                        element, "PredefinedType"
                    ),
                }
            )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "system_global_id",
        "system_name",
        "system_object_type",
        "system_predefined_type",
        "element_global_id",
        "element_ifc_class",
        "element_name",
        "element_object_type",
        "element_predefined_type",
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("=== RESULT ===")
    print()
    print(f"IfcDistributionSystem total : {len(systems)}")
    print(f"Used systems                : {used_systems}")
    print(f"Related element rows        : {total_related_elements}")
    print()

    print("--- Element IFC Class ---")
    for ifc_class, count in class_counter.most_common():
        print(f"{count:5d}  {ifc_class}")

    print()
    print("--- Non IfcDuctSegment Classes ---")

    if non_duct_counter:
        for ifc_class, count in non_duct_counter.most_common():
            print(f"{count:5d}  {ifc_class}")
    else:
        print("(none)")

    print()
    print("--- System / IFC Class ---")

    for system in systems:
        counts = system_class_counter.get(system.id())

        if not counts:
            continue

        system_name = safe_value(system, "Name") or "(No Name)"
        object_type = safe_value(system, "ObjectType") or "(No ObjectType)"

        for ifc_class, count in counts.most_common():
            print(
                f"{count:5d}  "
                f"{system_name} | "
                f"{object_type} | "
                f"{ifc_class}"
            )

    print()
    print(f"CSV written: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()