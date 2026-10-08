from collections import Counter, defaultdict
from pathlib import Path
import csv

import ifcopenshell
import ifcopenshell.util.element


IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")
OUTPUT_FILE = Path("output/duct_system_equipment_properties.csv")


# 今回調査する空調機器クラス
TARGET_CLASSES = {
    "IfcFan",
    "IfcAirToAirHeatRecovery",
    "IfcAirTerminalBox",
    "IfcDamper",
}


# 空調系統として扱う ObjectType
DUCT_SYSTEM_OBJECT_TYPES = {
    "101_SA給気",
    "102_RA還気",
    "103_OA外気",
    "105_EA排気",
}


def safe_value(obj, attr):
    """Return an IFC attribute as a printable string."""
    value = getattr(obj, attr, None)
    if value is None:
        return ""
    return str(value)


def value_to_string(value):
    """Convert IFC/property values to a readable string."""
    if value is None:
        return ""

    if isinstance(value, (list, tuple)):
        return " | ".join(value_to_string(v) for v in value)

    if isinstance(value, dict):
        return str(value)

    return str(value)


def get_system_memberships(model):
    """
    Build a mapping:
        element STEP id -> list of IfcDistributionSystem

    Only duct/air systems are included.
    """
    memberships = defaultdict(list)

    for system in model.by_type("IfcDistributionSystem"):
        object_type = safe_value(system, "ObjectType")

        if object_type not in DUCT_SYSTEM_OBJECT_TYPES:
            continue

        for rel in getattr(system, "IsGroupedBy", []) or []:
            for obj in getattr(rel, "RelatedObjects", []) or []:
                memberships[obj.id()].append(system)

    return memberships


def flatten_psets(element):
    """
    Return property rows from psets/qto sets.

    ifcopenshell.util.element.get_psets() returns both
    property sets and quantity sets in a convenient dictionary form.

    Metadata keys such as 'id' are skipped.
    """
    rows = []

    try:
        psets = ifcopenshell.util.element.get_psets(
            element,
            psets_only=False,
            qtos_only=False,
            should_inherit=True,
        )
    except Exception as exc:
        return [
            {
                "pset_name": "__ERROR__",
                "property_name": "__ERROR__",
                "property_value": str(exc),
            }
        ]

    for pset_name, properties in sorted(psets.items()):
        if not isinstance(properties, dict):
            continue

        for property_name, property_value in sorted(properties.items()):
            # get_psets() adds internal metadata such as STEP id.
            if property_name == "id":
                continue

            rows.append(
                {
                    "pset_name": str(pset_name),
                    "property_name": str(property_name),
                    "property_value": value_to_string(property_value),
                }
            )

    return rows


def main():
    print("=== DUCT SYSTEM EQUIPMENT PROPERTY INSPECTION ===")
    print()
    print(f"IFC   : {IFC_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print()

    model = ifcopenshell.open(str(IFC_FILE))

    memberships = get_system_memberships(model)

    output_rows = []

    equipment_counter = Counter()
    property_counter = Counter()
    pset_counter = Counter()
    system_equipment_counter = Counter()

    equipment_seen = set()
    equipment_with_properties = set()

    for ifc_class in sorted(TARGET_CLASSES):
        elements = model.by_type(ifc_class)

        for element in elements:
            systems = memberships.get(element.id(), [])

            # 今回は空調系統に正式所属する機器だけを対象とする
            if not systems:
                continue

            equipment_seen.add(element.id())
            equipment_counter[ifc_class] += 1

            property_rows = flatten_psets(element)

            if property_rows:
                equipment_with_properties.add(element.id())

            for system in systems:
                system_name = safe_value(system, "Name")
                system_object_type = safe_value(system, "ObjectType")
                system_predefined_type = safe_value(
                    system,
                    "PredefinedType",
                )

                system_equipment_counter[
                    (
                        system_object_type,
                        ifc_class,
                    )
                ] += 1

                # Propertyが0件でも機器そのものはCSVに残す
                if not property_rows:
                    output_rows.append(
                        {
                            "system_global_id": safe_value(
                                system,
                                "GlobalId",
                            ),
                            "system_name": system_name,
                            "system_object_type": system_object_type,
                            "system_predefined_type": system_predefined_type,
                            "equipment_global_id": safe_value(
                                element,
                                "GlobalId",
                            ),
                            "equipment_ifc_class": ifc_class,
                            "equipment_name": safe_value(
                                element,
                                "Name",
                            ),
                            "equipment_object_type": safe_value(
                                element,
                                "ObjectType",
                            ),
                            "equipment_predefined_type": safe_value(
                                element,
                                "PredefinedType",
                            ),
                            "pset_name": "",
                            "property_name": "",
                            "property_value": "",
                        }
                    )
                    continue

                for prop in property_rows:
                    pset_name = prop["pset_name"]
                    property_name = prop["property_name"]

                    pset_counter[
                        (
                            ifc_class,
                            pset_name,
                        )
                    ] += 1

                    property_counter[
                        (
                            ifc_class,
                            property_name,
                        )
                    ] += 1

                    output_rows.append(
                        {
                            "system_global_id": safe_value(
                                system,
                                "GlobalId",
                            ),
                            "system_name": system_name,
                            "system_object_type": system_object_type,
                            "system_predefined_type": system_predefined_type,
                            "equipment_global_id": safe_value(
                                element,
                                "GlobalId",
                            ),
                            "equipment_ifc_class": ifc_class,
                            "equipment_name": safe_value(
                                element,
                                "Name",
                            ),
                            "equipment_object_type": safe_value(
                                element,
                                "ObjectType",
                            ),
                            "equipment_predefined_type": safe_value(
                                element,
                                "PredefinedType",
                            ),
                            "pset_name": pset_name,
                            "property_name": property_name,
                            "property_value": prop[
                                "property_value"
                            ],
                        }
                    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "system_global_id",
        "system_name",
        "system_object_type",
        "system_predefined_type",
        "equipment_global_id",
        "equipment_ifc_class",
        "equipment_name",
        "equipment_object_type",
        "equipment_predefined_type",
        "pset_name",
        "property_name",
        "property_value",
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
        writer.writerows(output_rows)

    print("=== RESULT ===")
    print()
    print(
        f"Target equipment          : "
        f"{len(equipment_seen)}"
    )
    print(
        f"Equipment with properties : "
        f"{len(equipment_with_properties)}"
    )
    print(
        f"Output property rows       : "
        f"{len(output_rows)}"
    )
    print()

    print("--- Equipment IFC Class ---")
    for ifc_class, count in equipment_counter.most_common():
        print(f"{count:5d}  {ifc_class}")

    print()
    print("--- System Type / Equipment Class ---")
    for (
        system_object_type,
        ifc_class,
    ), count in sorted(system_equipment_counter.items()):
        print(
            f"{count:5d}  "
            f"{system_object_type} | "
            f"{ifc_class}"
        )

    print()
    print("--- Property Names by IFC Class ---")

    for ifc_class in sorted(TARGET_CLASSES):
        print()
        print(f"[{ifc_class}]")

        found = False

        class_properties = [
            (property_name, count)
            for (
                cls,
                property_name,
            ), count in property_counter.items()
            if cls == ifc_class
        ]

        for property_name, count in sorted(
            class_properties,
            key=lambda x: (-x[1], x[0]),
        ):
            found = True
            print(f"{count:5d}  {property_name}")

        if not found:
            print("(no properties)")

    print()
    print("--- Potential Engineering Information ---")

    keywords = [
        "pressure",
        "static",
        "風量",
        "静圧",
        "圧力",
        "airflow",
        "air flow",
        "flow",
        "capacity",
        "能力",
        "power",
        "出力",
        "motor",
        "電動機",
        "rpm",
        "回転",
    ]

    candidates = []

    for (
        ifc_class,
        property_name,
    ), count in property_counter.items():

        lower_name = property_name.lower()

        if any(
            keyword.lower() in lower_name
            for keyword in keywords
        ):
            candidates.append(
                (
                    ifc_class,
                    property_name,
                    count,
                )
            )

    if candidates:
        for ifc_class, property_name, count in sorted(
            candidates
        ):
            print(
                f"{count:5d}  "
                f"{ifc_class} | "
                f"{property_name}"
            )
    else:
        print("(no keyword candidates found)")

    print()
    print(f"CSV written: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()