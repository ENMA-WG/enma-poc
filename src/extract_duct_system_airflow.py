from collections import Counter, defaultdict
from pathlib import Path
import csv

import ifcopenshell
import ifcopenshell.util.element


IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")
OUTPUT_FILE = Path("output/duct_system_airflow.csv")


# 今回対象とする空調系統
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


def get_system_memberships(model):
    """
    Build mapping:

        element STEP id -> list of IfcDistributionSystem

    Only SA / RA / OA / EA systems are included.
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


def get_nominal_airflow(fan):
    """
    Extract NominalAirFlowRate from the fan property sets.

    Returns:
        (pset_name, raw_value)

    No inference is performed.
    """
    try:
        psets = ifcopenshell.util.element.get_psets(
            fan,
            psets_only=False,
            qtos_only=False,
            should_inherit=True,
        )
    except Exception:
        return "", None

    for pset_name, properties in psets.items():

        if not isinstance(properties, dict):
            continue

        if "NominalAirFlowRate" not in properties:
            continue

        value = properties.get("NominalAirFlowRate")

        if value is None:
            continue

        return pset_name, value

    return "", None


def convert_to_float(value):
    """Convert a property value to float where possible."""
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main():
    print("=== DUCT SYSTEM AIRFLOW EXTRACTION ===")
    print()
    print(f"IFC   : {IFC_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print()

    model = ifcopenshell.open(str(IFC_FILE))

    memberships = get_system_memberships(model)

    fans = model.by_type("IfcFan")

    rows = []

    system_type_counter = Counter()

    fans_in_duct_system = set()
    fans_with_airflow = set()
    fans_without_airflow = set()

    for fan in fans:

        systems = memberships.get(fan.id(), [])

        # FanがSA/RA/OA/EA系統に所属していなければ対象外
        if not systems:
            continue

        fans_in_duct_system.add(fan.id())

        pset_name, raw_airflow = get_nominal_airflow(fan)

        airflow_m3_s = convert_to_float(raw_airflow)

        if airflow_m3_s is not None:
            airflow_m3_h = airflow_m3_s * 3600.0
            fans_with_airflow.add(fan.id())
        else:
            airflow_m3_h = None
            fans_without_airflow.add(fan.id())

        for system in systems:

            system_object_type = safe_value(
                system,
                "ObjectType",
            )

            system_type_counter[system_object_type] += 1

            rows.append(
                {
                    "system_global_id": safe_value(
                        system,
                        "GlobalId",
                    ),
                    "system_name": safe_value(
                        system,
                        "Name",
                    ),
                    "system_object_type": system_object_type,
                    "system_predefined_type": safe_value(
                        system,
                        "PredefinedType",
                    ),
                    "fan_global_id": safe_value(
                        fan,
                        "GlobalId",
                    ),
                    "fan_name": safe_value(
                        fan,
                        "Name",
                    ),
                    "fan_object_type": safe_value(
                        fan,
                        "ObjectType",
                    ),
                    "fan_predefined_type": safe_value(
                        fan,
                        "PredefinedType",
                    ),
                    "airflow_pset_name": pset_name,
                    "nominal_airflow_raw": (
                        ""
                        if raw_airflow is None
                        else str(raw_airflow)
                    ),
                    "nominal_airflow_m3_s": (
                        ""
                        if airflow_m3_s is None
                        else f"{airflow_m3_s:.9f}"
                    ),
                    "nominal_airflow_m3_h": (
                        ""
                        if airflow_m3_h is None
                        else f"{airflow_m3_h:.3f}"
                    ),
                    "airflow_source": (
                        f"{pset_name}.NominalAirFlowRate"
                        if pset_name
                        else ""
                    ),
                }
            )

    rows.sort(
        key=lambda row: (
            row["system_object_type"],
            row["system_name"],
            row["fan_name"],
        )
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "system_global_id",
        "system_name",
        "system_object_type",
        "system_predefined_type",
        "fan_global_id",
        "fan_name",
        "fan_object_type",
        "fan_predefined_type",
        "airflow_pset_name",
        "nominal_airflow_raw",
        "nominal_airflow_m3_s",
        "nominal_airflow_m3_h",
        "airflow_source",
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

    print("=== RESULT ===")
    print()

    print(
        f"IfcFan total             : "
        f"{len(fans)}"
    )

    print(
        f"Fans in duct systems     : "
        f"{len(fans_in_duct_system)}"
    )

    print(
        f"Fans with airflow        : "
        f"{len(fans_with_airflow)}"
    )

    print(
        f"Fans without airflow     : "
        f"{len(fans_without_airflow)}"
    )

    print(
        f"Output rows              : "
        f"{len(rows)}"
    )

    print()

    print("--- System Type / Fan Count ---")

    for system_type, count in sorted(
        system_type_counter.items()
    ):
        print(
            f"{count:5d}  "
            f"{system_type}"
        )

    print()
    print("--- System / Fan / Nominal Air Flow ---")

    for row in rows:

        airflow = row["nominal_airflow_m3_h"]

        if airflow:
            airflow_text = f"{airflow} m3/h"
        else:
            airflow_text = "(not available)"

        print(
            f"{row['system_name']:12s} | "
            f"{row['system_object_type']:12s} | "
            f"{airflow_text:18s} | "
            f"{row['fan_name']}"
        )

    print()
    print("--- Engineering Information Status ---")
    print()

    if fans_with_airflow:
        print(
            "OBSERVED: NominalAirFlowRate is available "
            "from IFC fan properties."
        )

    if fans_without_airflow:
        print(
            "MISSING : Some fans do not have "
            "NominalAirFlowRate."
        )

    print()
    print(
        "NOTE: Fan NominalAirFlowRate is an IFC-observed "
        "equipment property."
    )

    print(
        "      It is NOT automatically assigned to every "
        "duct segment in the system."
    )

    print()
    print(f"CSV written: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()