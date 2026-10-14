from pathlib import Path
from collections import Counter, defaultdict
import csv

import ifcopenshell
import ifcopenshell.util.element


IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")
DUCT_CSV = Path("output/ducts_detail.csv")
OUTPUT_FILE = Path("output/duct_system_properties.csv")


def clean(value):
    if value is None:
        return ""

    if isinstance(value, (str, int, float, bool)):
        return str(value).strip()

    return str(value).strip()


def get_systems_from_duct(duct):
    """
    Get IfcDistributionSystem objects formally assigned to an
    IfcDuctSegment through IfcRelAssignsToGroup.

    No inference from duct Name/ObjectType is performed.
    """
    systems = []

    for rel in getattr(duct, "HasAssignments", []) or []:

        if not rel.is_a("IfcRelAssignsToGroup"):
            continue

        group = getattr(rel, "RelatingGroup", None)

        if group and group.is_a("IfcDistributionSystem"):
            systems.append(group)

    return systems


def get_system_properties(system):
    """
    Flatten property sets attached to IfcDistributionSystem.

    Returns:
        list of tuples:
        (pset_name, property_name, property_value)
    """
    result = []

    psets = ifcopenshell.util.element.get_psets(
        system,
        psets_only=True,
        should_inherit=False,
    )

    for pset_name, properties in sorted(psets.items()):

        for property_name, value in sorted(properties.items()):

            if property_name == "id":
                continue

            result.append(
                (
                    clean(pset_name),
                    clean(property_name),
                    clean(value),
                )
            )

    return result


def main():

    print("=== DUCT SYSTEM PROPERTY INSPECTION ===")
    print()
    print(f"IFC     : {IFC_FILE}")
    print(f"Duct CSV: {DUCT_CSV}")
    print(f"Output  : {OUTPUT_FILE}")
    print()

    model = ifcopenshell.open(str(IFC_FILE))

    # ---------------------------------------------------------
    # Read the ENMA duct result.
    # This lets us compare the already extracted AirType/System
    # information with the actual IFC relationships.
    # ---------------------------------------------------------

    duct_csv_info = {}

    with DUCT_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            global_id = clean(row.get("GlobalId"))

            duct_csv_info[global_id] = {
                "AirType": clean(row.get("AirType")),
                "Shape": clean(row.get("Shape")),
                "SystemName": clean(row.get("SystemName")),
                "SystemObjectType": clean(
                    row.get("SystemObjectType")
                ),
            }

    # ---------------------------------------------------------
    # Find actual IfcDistributionSystem assignments.
    # ---------------------------------------------------------

    system_ducts = defaultdict(list)

    duct_count = 0
    duct_without_system = 0
    duct_with_multiple_systems = 0

    for duct in model.by_type("IfcDuctSegment"):

        duct_count += 1

        systems = get_systems_from_duct(duct)

        if not systems:
            duct_without_system += 1
            continue

        if len(systems) > 1:
            duct_with_multiple_systems += 1

        for system in systems:
            system_ducts[system.id()].append(duct)

    # ---------------------------------------------------------
    # Inventory all used systems.
    # ---------------------------------------------------------

    rows = []

    system_name_counter = Counter()
    system_object_type_counter = Counter()
    system_predefined_counter = Counter()
    property_counter = Counter()

    pressure_like_counter = Counter()

    # More careful than the previous "pa" substring search.
    pressure_terms = (
        "pressure",
        "workingpressure",
        "pressurerange",
        "staticpressure",
        "圧力",
        "静圧",
        "低圧",
        "高圧",
    )

    for system_id, ducts in sorted(system_ducts.items()):

        system = model.by_id(system_id)

        system_name = clean(
            getattr(system, "Name", None)
        )

        system_object_type = clean(
            getattr(system, "ObjectType", None)
        )

        system_predefined = clean(
            getattr(system, "PredefinedType", None)
        )

        system_long_name = clean(
            getattr(system, "LongName", None)
        )

        system_description = clean(
            getattr(system, "Description", None)
        )

        duct_global_ids = [
            duct.GlobalId
            for duct in ducts
        ]

        # AirType values already established by extract_ducts.py
        air_types = sorted(
            {
                duct_csv_info.get(
                    gid,
                    {}
                ).get("AirType", "")
                for gid in duct_global_ids
                if duct_csv_info.get(
                    gid,
                    {}
                ).get("AirType", "")
            }
        )

        shapes = sorted(
            {
                duct_csv_info.get(
                    gid,
                    {}
                ).get("Shape", "")
                for gid in duct_global_ids
                if duct_csv_info.get(
                    gid,
                    {}
                ).get("Shape", "")
            }
        )

        properties = get_system_properties(system)

        system_name_counter[
            system_name or "(blank)"
        ] += len(ducts)

        system_object_type_counter[
            system_object_type or "(blank)"
        ] += len(ducts)

        system_predefined_counter[
            system_predefined or "(blank)"
        ] += len(ducts)

        # -----------------------------------------------------
        # Always output at least one row per system.
        # This is important when the system has no properties.
        # -----------------------------------------------------

        if not properties:

            rows.append(
                {
                    "SystemGlobalId": clean(
                        getattr(
                            system,
                            "GlobalId",
                            None,
                        )
                    ),
                    "SystemName": system_name,
                    "SystemObjectType": (
                        system_object_type
                    ),
                    "SystemPredefinedType": (
                        system_predefined
                    ),
                    "SystemLongName": (
                        system_long_name
                    ),
                    "SystemDescription": (
                        system_description
                    ),
                    "AirType": " | ".join(
                        air_types
                    ),
                    "Shape": " | ".join(
                        shapes
                    ),
                    "DuctCount": len(ducts),
                    "PropertySet": "",
                    "PropertyName": "",
                    "PropertyValue": "",
                    "PressureLike": "",
                }
            )

            continue

        # -----------------------------------------------------
        # One CSV row per property.
        # -----------------------------------------------------

        for (
            pset_name,
            property_name,
            property_value,
        ) in properties:

            property_counter[
                (
                    pset_name,
                    property_name,
                    property_value,
                )
            ] += 1

            searchable = (
                f"{pset_name} "
                f"{property_name} "
                f"{property_value}"
            ).lower()

            pressure_like = any(
                term.lower() in searchable
                for term in pressure_terms
            )

            if pressure_like:
                pressure_like_counter[
                    (
                        system_name,
                        pset_name,
                        property_name,
                        property_value,
                    )
                ] += 1

            rows.append(
                {
                    "SystemGlobalId": clean(
                        getattr(
                            system,
                            "GlobalId",
                            None,
                        )
                    ),
                    "SystemName": system_name,
                    "SystemObjectType": (
                        system_object_type
                    ),
                    "SystemPredefinedType": (
                        system_predefined
                    ),
                    "SystemLongName": (
                        system_long_name
                    ),
                    "SystemDescription": (
                        system_description
                    ),
                    "AirType": " | ".join(
                        air_types
                    ),
                    "Shape": " | ".join(
                        shapes
                    ),
                    "DuctCount": len(ducts),
                    "PropertySet": pset_name,
                    "PropertyName": (
                        property_name
                    ),
                    "PropertyValue": (
                        property_value
                    ),
                    "PressureLike": (
                        "YES"
                        if pressure_like
                        else ""
                    ),
                }
            )

    # ---------------------------------------------------------
    # Write CSV
    # ---------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "SystemGlobalId",
        "SystemName",
        "SystemObjectType",
        "SystemPredefinedType",
        "SystemLongName",
        "SystemDescription",
        "AirType",
        "Shape",
        "DuctCount",
        "PropertySet",
        "PropertyName",
        "PropertyValue",
        "PressureLike",
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

    # ---------------------------------------------------------
    # Console report
    # ---------------------------------------------------------

    print("=== RESULT ===")
    print(
        f"IfcDuctSegment             : {duct_count}"
    )
    print(
        f"Used IfcDistributionSystem : {len(system_ducts)}"
    )
    print(
        f"Duct without system        : {duct_without_system}"
    )
    print(
        f"Duct with multiple systems : "
        f"{duct_with_multiple_systems}"
    )
    print(
        f"Output rows                : {len(rows)}"
    )

    print()
    print("--- System Name (duct count) ---")

    for value, count in (
        system_name_counter.most_common()
    ):
        print(
            f"{count:4d}  {value}"
        )

    print()
    print("--- System ObjectType (duct count) ---")

    for value, count in (
        system_object_type_counter.most_common()
    ):
        print(
            f"{count:4d}  {value}"
        )

    print()
    print("--- System PredefinedType (duct count) ---")

    for value, count in (
        system_predefined_counter.most_common()
    ):
        print(
            f"{count:4d}  {value}"
        )

    print()
    print("--- System properties ---")

    if property_counter:

        for (
            pset_name,
            property_name,
            property_value,
        ), count in (
            property_counter.most_common()
        ):

            print(
                f"{count:4d}  "
                f"{pset_name}."
                f"{property_name}"
                f" = {property_value}"
            )

    else:
        print("(none)")

    print()
    print("--- Pressure-like properties ---")

    if pressure_like_counter:

        for (
            system_name,
            pset_name,
            property_name,
            property_value,
        ), count in (
            pressure_like_counter.most_common()
        ):

            print(
                f"{count:4d}  "
                f"{system_name} : "
                f"{pset_name}."
                f"{property_name}"
                f" = {property_value}"
            )

    else:
        print("(none)")

    print()
    print(
        f"CSV written                : {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()