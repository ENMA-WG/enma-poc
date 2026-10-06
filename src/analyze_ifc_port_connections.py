from collections import Counter, defaultdict
from pathlib import Path
import csv

import ifcopenshell


IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")
OUTPUT_FILE = Path("output/ifc_port_connections.csv")
SYSTEM_OUTPUT_FILE = Path("output/duct_system_connection_summary.csv")


DUCT_SYSTEM_OBJECT_TYPES = {
    "101_SA給気",
    "102_RA還気",
    "103_OA外気",
    "105_EA排気",
}


DUCT_RELATED_CLASSES = {
    "IfcDuctSegment",
    "IfcDuctFitting",
    "IfcAirTerminal",
    "IfcAirTerminalBox",
    "IfcFan",
    "IfcDamper",
    "IfcAirToAirHeatRecovery",
    "IfcUnitaryEquipment",
}


def safe_value(obj, attr):
    """Return IFC attribute as printable text."""
    if obj is None:
        return ""

    value = getattr(obj, attr, None)

    if value is None:
        return ""

    return str(value)


def get_port_owner_map(model):
    """
    Build:
        port STEP id -> owning IFC element

    IFC4 normally represents ownership through IfcRelNests.
    """
    owners = {}

    for rel in model.by_type("IfcRelNests"):

        owner = getattr(
            rel,
            "RelatingObject",
            None,
        )

        if owner is None:
            continue

        for obj in getattr(
            rel,
            "RelatedObjects",
            [],
        ) or []:

            if obj.is_a("IfcDistributionPort"):
                owners[obj.id()] = owner

    return owners


def get_duct_system_memberships(model):
    """
    Build mappings for SA / RA / OA / EA systems.

        object STEP id -> systems
        system STEP id -> system members
    """
    object_systems = defaultdict(list)
    system_members = defaultdict(list)
    systems = []

    for system in model.by_type(
        "IfcDistributionSystem"
    ):

        object_type = safe_value(
            system,
            "ObjectType",
        )

        if object_type not in DUCT_SYSTEM_OBJECT_TYPES:
            continue

        systems.append(system)

        for rel in getattr(
            system,
            "IsGroupedBy",
            [],
        ) or []:

            for obj in getattr(
                rel,
                "RelatedObjects",
                [],
            ) or []:

                object_systems[obj.id()].append(
                    system
                )

                system_members[system.id()].append(
                    obj
                )

    return (
        systems,
        object_systems,
        system_members,
    )


def get_system_keys_for_connection(
    port1,
    port2,
    owner1,
    owner2,
    object_systems,
):
    """
    Determine systems associated with either side
    of a connection.

    We check both the ports themselves and their
    owning elements because IFC exports may assign
    either representation to a system.
    """
    systems = {}

    objects = [
        port1,
        port2,
        owner1,
        owner2,
    ]

    for obj in objects:

        if obj is None:
            continue

        for system in object_systems.get(
            obj.id(),
            [],
        ):

            systems[system.id()] = system

    return list(systems.values())


def class_pair(owner1, owner2):
    """
    Return normalized class pair so:
        A <-> B
    and:
        B <-> A
    are counted together.
    """
    class1 = (
        owner1.is_a()
        if owner1 is not None
        else "(No Owner)"
    )

    class2 = (
        owner2.is_a()
        if owner2 is not None
        else "(No Owner)"
    )

    return tuple(
        sorted(
            [
                class1,
                class2,
            ]
        )
    )


def main():
    print("=== IFC PORT CONNECTION ANALYSIS ===")
    print()
    print(f"IFC           : {IFC_FILE}")
    print(f"Connections   : {OUTPUT_FILE}")
    print(f"System summary: {SYSTEM_OUTPUT_FILE}")
    print()

    model = ifcopenshell.open(
        str(IFC_FILE)
    )

    port_owners = get_port_owner_map(
        model
    )

    (
        duct_systems,
        object_systems,
        system_members,
    ) = get_duct_system_memberships(
        model
    )

    connections = model.by_type(
        "IfcRelConnectsPorts"
    )

    print("=== BASIC COUNTS ===")
    print()
    print(
        f"IfcDistributionPort : "
        f"{len(model.by_type('IfcDistributionPort'))}"
    )
    print(
        f"IfcRelConnectsPorts : "
        f"{len(connections)}"
    )
    print(
        f"Ports with owner    : "
        f"{len(port_owners)}"
    )
    print(
        f"Duct air systems    : "
        f"{len(duct_systems)}"
    )
    print()

    pair_counter = Counter()
    duct_pair_counter = Counter()

    ownerless_side_count = 0
    duct_connection_count = 0
    air_system_connection_count = 0

    connection_rows = []

    #
    # Per-system relationship IDs.
    # Sets are used to avoid counting the same
    # IfcRelConnectsPorts more than once.
    #
    system_connection_ids = defaultdict(set)

    for rel in connections:

        port1 = getattr(
            rel,
            "RelatingPort",
            None,
        )

        port2 = getattr(
            rel,
            "RelatedPort",
            None,
        )

        if port1 is None or port2 is None:
            continue

        owner1 = port_owners.get(
            port1.id()
        )

        owner2 = port_owners.get(
            port2.id()
        )

        if owner1 is None or owner2 is None:
            ownerless_side_count += 1

        pair = class_pair(
            owner1,
            owner2,
        )

        pair_counter[pair] += 1

        class1 = (
            owner1.is_a()
            if owner1 is not None
            else ""
        )

        class2 = (
            owner2.is_a()
            if owner2 is not None
            else ""
        )

        is_duct_related = (
            class1 in DUCT_RELATED_CLASSES
            or
            class2 in DUCT_RELATED_CLASSES
        )

        if is_duct_related:
            duct_connection_count += 1
            duct_pair_counter[pair] += 1

        systems = get_system_keys_for_connection(
            port1,
            port2,
            owner1,
            owner2,
            object_systems,
        )

        if systems:
            air_system_connection_count += 1

        system_names = []
        system_object_types = []

        for system in systems:

            system_connection_ids[
                system.id()
            ].add(
                rel.id()
            )

            system_names.append(
                safe_value(
                    system,
                    "Name",
                )
            )

            system_object_types.append(
                safe_value(
                    system,
                    "ObjectType",
                )
            )

        connection_rows.append(
            {
                "relationship_step_id": rel.id(),
                "relationship_global_id": safe_value(
                    rel,
                    "GlobalId",
                ),
                "port1_step_id": port1.id(),
                "port1_global_id": safe_value(
                    port1,
                    "GlobalId",
                ),
                "port1_name": safe_value(
                    port1,
                    "Name",
                ),
                "port1_flow_direction": safe_value(
                    port1,
                    "FlowDirection",
                ),
                "owner1_step_id": (
                    ""
                    if owner1 is None
                    else owner1.id()
                ),
                "owner1_global_id": (
                    ""
                    if owner1 is None
                    else safe_value(
                        owner1,
                        "GlobalId",
                    )
                ),
                "owner1_class": class1,
                "owner1_name": (
                    ""
                    if owner1 is None
                    else safe_value(
                        owner1,
                        "Name",
                    )
                ),
                "port2_step_id": port2.id(),
                "port2_global_id": safe_value(
                    port2,
                    "GlobalId",
                ),
                "port2_name": safe_value(
                    port2,
                    "Name",
                ),
                "port2_flow_direction": safe_value(
                    port2,
                    "FlowDirection",
                ),
                "owner2_step_id": (
                    ""
                    if owner2 is None
                    else owner2.id()
                ),
                "owner2_global_id": (
                    ""
                    if owner2 is None
                    else safe_value(
                        owner2,
                        "GlobalId",
                    )
                ),
                "owner2_class": class2,
                "owner2_name": (
                    ""
                    if owner2 is None
                    else safe_value(
                        owner2,
                        "Name",
                    )
                ),
                "class_pair": (
                    f"{pair[0]} <-> {pair[1]}"
                ),
                "duct_related": (
                    "TRUE"
                    if is_duct_related
                    else "FALSE"
                ),
                "air_system_names": " | ".join(
                    sorted(
                        set(system_names)
                    )
                ),
                "air_system_object_types": (
                    " | ".join(
                        sorted(
                            set(
                                system_object_types
                            )
                        )
                    )
                ),
            }
        )

    #
    # Whole IFC class-pair summary
    #
    print("=== ALL CONNECTION CLASS PAIRS ===")
    print()

    for pair, count in pair_counter.most_common():

        print(
            f"{count:5d}  "
            f"{pair[0]} <-> {pair[1]}"
        )

    print()

    #
    # Duct-related connections
    #
    print("=== DUCT-RELATED CONNECTION CLASS PAIRS ===")
    print()

    if duct_pair_counter:

        for pair, count in (
            duct_pair_counter.most_common()
        ):

            print(
                f"{count:5d}  "
                f"{pair[0]} <-> {pair[1]}"
            )

    else:
        print(
            "(no duct-related explicit "
            "port connections found)"
        )

    print()

    #
    # Per-system summary
    #
    system_rows = []

    systems_with_connections = 0
    systems_without_connections = 0

    print("=== AIR SYSTEM CONNECTION SUMMARY ===")
    print()

    print(
        "System       | Type         | "
        "Members | Ports | Connections"
    )

    print(
        "-" * 68
    )

    for system in sorted(
        duct_systems,
        key=lambda x: (
            safe_value(
                x,
                "ObjectType",
            ),
            safe_value(
                x,
                "Name",
            ),
        ),
    ):

        members = system_members.get(
            system.id(),
            [],
        )

        port_count = sum(
            1
            for obj in members
            if obj.is_a(
                "IfcDistributionPort"
            )
        )

        element_count = (
            len(members) - port_count
        )

        connection_count = len(
            system_connection_ids.get(
                system.id(),
                set(),
            )
        )

        if connection_count > 0:
            systems_with_connections += 1
        else:
            systems_without_connections += 1

        print(
            f"{safe_value(system, 'Name'):12s} | "
            f"{safe_value(system, 'ObjectType'):12s} | "
            f"{element_count:7d} | "
            f"{port_count:5d} | "
            f"{connection_count:11d}"
        )

        system_rows.append(
            {
                "system_global_id": safe_value(
                    system,
                    "GlobalId",
                ),
                "system_name": safe_value(
                    system,
                    "Name",
                ),
                "system_object_type": safe_value(
                    system,
                    "ObjectType",
                ),
                "system_predefined_type": safe_value(
                    system,
                    "PredefinedType",
                ),
                "element_count": element_count,
                "formal_system_port_count": port_count,
                "explicit_port_connection_count": (
                    connection_count
                ),
                "has_explicit_connections": (
                    "TRUE"
                    if connection_count > 0
                    else "FALSE"
                ),
            }
        )

    print()

    #
    # Summary by air-system type
    #
    type_summary = defaultdict(
        lambda: {
            "systems": 0,
            "with_connections": 0,
            "without_connections": 0,
            "connections": 0,
        }
    )

    for row in system_rows:

        system_type = row[
            "system_object_type"
        ]

        data = type_summary[
            system_type
        ]

        data["systems"] += 1

        connection_count = int(
            row[
                "explicit_port_connection_count"
            ]
        )

        data["connections"] += (
            connection_count
        )

        if connection_count > 0:
            data[
                "with_connections"
            ] += 1
        else:
            data[
                "without_connections"
            ] += 1

    print("=== SUMMARY BY AIR SYSTEM TYPE ===")
    print()

    for system_type in sorted(
        type_summary
    ):

        data = type_summary[
            system_type
        ]

        print(
            f"{system_type:12s} | "
            f"systems={data['systems']:4d} | "
            f"with={data['with_connections']:4d} | "
            f"without={data['without_connections']:4d} | "
            f"connections={data['connections']:5d}"
        )

    print()

    #
    # Interesting equipment-boundary connections
    #
    print("=== EQUIPMENT BOUNDARY CONNECTIONS ===")
    print()

    equipment_classes = {
        "IfcFan",
        "IfcAirTerminal",
        "IfcAirTerminalBox",
        "IfcDamper",
        "IfcAirToAirHeatRecovery",
        "IfcUnitaryEquipment",
    }

    equipment_pair_counter = Counter()

    for pair, count in duct_pair_counter.items():

        if (
            pair[0] in equipment_classes
            or
            pair[1] in equipment_classes
        ):
            equipment_pair_counter[
                pair
            ] += count

    if equipment_pair_counter:

        for pair, count in (
            equipment_pair_counter.most_common()
        ):

            print(
                f"{count:5d}  "
                f"{pair[0]} <-> {pair[1]}"
            )

    else:
        print(
            "(no explicit equipment-boundary "
            "connections found)"
        )

    #
    # CSV outputs
    #
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection_fields = [
        "relationship_step_id",
        "relationship_global_id",
        "port1_step_id",
        "port1_global_id",
        "port1_name",
        "port1_flow_direction",
        "owner1_step_id",
        "owner1_global_id",
        "owner1_class",
        "owner1_name",
        "port2_step_id",
        "port2_global_id",
        "port2_name",
        "port2_flow_direction",
        "owner2_step_id",
        "owner2_global_id",
        "owner2_class",
        "owner2_name",
        "class_pair",
        "duct_related",
        "air_system_names",
        "air_system_object_types",
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=connection_fields,
        )

        writer.writeheader()
        writer.writerows(
            connection_rows
        )

    system_fields = [
        "system_global_id",
        "system_name",
        "system_object_type",
        "system_predefined_type",
        "element_count",
        "formal_system_port_count",
        "explicit_port_connection_count",
        "has_explicit_connections",
    ]

    with SYSTEM_OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=system_fields,
        )

        writer.writeheader()
        writer.writerows(
            system_rows
        )

    print()
    print("=== RESULT ===")
    print()

    print(
        f"Total explicit port connections : "
        f"{len(connections)}"
    )

    print(
        f"Connections with owner missing  : "
        f"{ownerless_side_count}"
    )

    print(
        f"Duct-related connections        : "
        f"{duct_connection_count}"
    )

    print(
        f"Connections mapped to air system: "
        f"{air_system_connection_count}"
    )

    print(
        f"Air systems total               : "
        f"{len(duct_systems)}"
    )

    print(
        f"Systems with connections        : "
        f"{systems_with_connections}"
    )

    print(
        f"Systems without connections     : "
        f"{systems_without_connections}"
    )

    print()
    print(
        f"Connection CSV: "
        f"{OUTPUT_FILE}"
    )

    print(
        f"System CSV    : "
        f"{SYSTEM_OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()