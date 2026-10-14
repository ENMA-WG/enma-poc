from collections import defaultdict, deque, Counter
from pathlib import Path
import csv

import ifcopenshell


IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")
OUTPUT_FILE = Path("output/duct_system_topology_EA18.csv")

TARGET_SYSTEM_NAME = "EA 18"
TARGET_SYSTEM_OBJECT_TYPE = "105_EA排気"


def safe_value(obj, attr):
    """Return an IFC attribute as printable text."""
    value = getattr(obj, attr, None)

    if value is None:
        return ""

    return str(value)


def get_target_system(model):
    """Find the target IfcDistributionSystem."""
    matches = []

    for system in model.by_type("IfcDistributionSystem"):

        if (
            safe_value(system, "Name") == TARGET_SYSTEM_NAME
            and safe_value(system, "ObjectType")
            == TARGET_SYSTEM_OBJECT_TYPE
        ):
            matches.append(system)

    if not matches:
        return None

    if len(matches) > 1:
        print(
            f"WARNING: {len(matches)} matching systems found. "
            "Using the first one."
        )

    return matches[0]


def get_system_members(system):
    """
    Return all objects formally assigned to the system
    through IfcRelAssignsToGroup / IsGroupedBy.
    """
    members = []

    for rel in getattr(system, "IsGroupedBy", []) or []:
        for obj in getattr(rel, "RelatedObjects", []) or []:
            members.append(obj)

    return members


def get_port_owner(model):
    """
    Build:

        port STEP id -> owning element

    IFC ports may be related to their owner using
    IfcRelNests or IfcRelConnectsPortToElement.
    """
    owners = {}

    # IFC4-style nesting
    for rel in model.by_type("IfcRelNests"):

        relating_object = getattr(
            rel,
            "RelatingObject",
            None,
        )

        for obj in getattr(rel, "RelatedObjects", []) or []:

            if obj.is_a("IfcDistributionPort"):
                owners[obj.id()] = relating_object

    # Older / alternative representation
    for rel in model.by_type("IfcRelConnectsPortToElement"):

        port = getattr(
            rel,
            "RelatingPort",
            None,
        )

        element = getattr(
            rel,
            "RelatedElement",
            None,
        )

        if port is not None and element is not None:
            owners[port.id()] = element

    return owners


def build_port_connections(model):
    """
    Build an undirected graph between ports using
    IfcRelConnectsPorts.

        port STEP id -> list of connected ports
    """
    graph = defaultdict(list)

    for rel in model.by_type("IfcRelConnectsPorts"):

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

        graph[port1.id()].append(
            {
                "port": port2,
                "relationship": rel,
            }
        )

        graph[port2.id()].append(
            {
                "port": port1,
                "relationship": rel,
            }
        )

    return graph


def get_element_ports(element):
    """
    Return IfcDistributionPorts belonging to an element.
    """
    ports = []

    # IFC4 nesting
    for rel in getattr(element, "IsNestedBy", []) or []:

        for obj in getattr(rel, "RelatedObjects", []) or []:

            if obj.is_a("IfcDistributionPort"):
                ports.append(obj)

    # IfcRelConnectsPortToElement representation
    for rel in getattr(element, "HasPorts", []) or []:

        port = getattr(
            rel,
            "RelatingPort",
            None,
        )

        if (
            port is not None
            and port.is_a("IfcDistributionPort")
            and port not in ports
        ):
            ports.append(port)

    return ports


def describe_element(element):
    """Return a compact printable element description."""
    if element is None:
        return "(No Owner)"

    return (
        f"{element.is_a()} | "
        f"{safe_value(element, 'Name')}"
    )


def main():
    print("=== DUCT SYSTEM TOPOLOGY TRACE ===")
    print()
    print(f"IFC        : {IFC_FILE}")
    print(
        f"Target     : "
        f"{TARGET_SYSTEM_NAME} | "
        f"{TARGET_SYSTEM_OBJECT_TYPE}"
    )
    print(f"Output     : {OUTPUT_FILE}")
    print()

    model = ifcopenshell.open(str(IFC_FILE))

    system = get_target_system(model)

    if system is None:
        print("ERROR: Target system was not found.")
        return

    print("=== TARGET SYSTEM ===")
    print()
    print(
        f"GlobalId       : "
        f"{safe_value(system, 'GlobalId')}"
    )
    print(
        f"Name           : "
        f"{safe_value(system, 'Name')}"
    )
    print(
        f"ObjectType     : "
        f"{safe_value(system, 'ObjectType')}"
    )
    print(
        f"PredefinedType : "
        f"{safe_value(system, 'PredefinedType')}"
    )
    print()

    members = get_system_members(system)

    member_ids = {
        member.id()
        for member in members
    }

    member_counter = Counter(
        member.is_a()
        for member in members
    )

    print("=== SYSTEM MEMBERS ===")
    print()

    for ifc_class, count in member_counter.most_common():
        print(f"{count:5d}  {ifc_class}")

    print()

    port_owner = get_port_owner(model)
    port_graph = build_port_connections(model)

    system_ports = [
        member
        for member in members
        if member.is_a("IfcDistributionPort")
    ]

    system_elements = [
        member
        for member in members
        if not member.is_a("IfcDistributionPort")
    ]

    print(
        f"System ports    : {len(system_ports)}"
    )
    print(
        f"System elements : {len(system_elements)}"
    )
    print()

    print("=== SYSTEM ELEMENTS ===")
    print()

    for element in sorted(
        system_elements,
        key=lambda x: (
            x.is_a(),
            safe_value(x, "Name"),
        ),
    ):

        ports = get_element_ports(element)

        print(
            f"{element.is_a():24s} | "
            f"ports={len(ports):2d} | "
            f"{safe_value(element, 'Name')}"
        )

    print()

    print("=== PORT OWNERS ===")
    print()

    for port in sorted(
        system_ports,
        key=lambda x: x.id(),
    ):

        owner = port_owner.get(port.id())

        print(
            f"Port #{port.id():6d} | "
            f"FlowDirection="
            f"{safe_value(port, 'FlowDirection'):8s} | "
            f"{describe_element(owner)}"
        )

    print()

    print("=== PORT CONNECTIONS ===")
    print()

    rows = []

    connection_count = 0
    internal_connection_count = 0
    external_connection_count = 0

    processed_pairs = set()

    for port in system_ports:

        owner1 = port_owner.get(port.id())

        connections = port_graph.get(
            port.id(),
            [],
        )

        for connection in connections:

            other_port = connection["port"]
            rel = connection["relationship"]

            pair = tuple(
                sorted(
                    (
                        port.id(),
                        other_port.id(),
                    )
                )
            )

            if pair in processed_pairs:
                continue

            processed_pairs.add(pair)

            owner2 = port_owner.get(
                other_port.id()
            )

            connection_count += 1

            if other_port.id() in member_ids:
                scope = "INTERNAL"
                internal_connection_count += 1
            else:
                scope = "EXTERNAL"
                external_connection_count += 1

            print(
                f"{scope:8s} | "
                f"Port #{port.id():6d} "
                f"({safe_value(port, 'FlowDirection')}) "
                f"[{describe_element(owner1)}]"
            )

            print(
                f"         -> "
                f"Port #{other_port.id():6d} "
                f"({safe_value(other_port, 'FlowDirection')}) "
                f"[{describe_element(owner2)}]"
            )

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
                    "system_object_type": safe_value(
                        system,
                        "ObjectType",
                    ),
                    "connection_scope": scope,
                    "relationship_global_id": safe_value(
                        rel,
                        "GlobalId",
                    ),
                    "from_port_step_id": port.id(),
                    "from_port_global_id": safe_value(
                        port,
                        "GlobalId",
                    ),
                    "from_port_name": safe_value(
                        port,
                        "Name",
                    ),
                    "from_flow_direction": safe_value(
                        port,
                        "FlowDirection",
                    ),
                    "from_owner_step_id": (
                        ""
                        if owner1 is None
                        else owner1.id()
                    ),
                    "from_owner_global_id": (
                        ""
                        if owner1 is None
                        else safe_value(
                            owner1,
                            "GlobalId",
                        )
                    ),
                    "from_owner_class": (
                        ""
                        if owner1 is None
                        else owner1.is_a()
                    ),
                    "from_owner_name": (
                        ""
                        if owner1 is None
                        else safe_value(
                            owner1,
                            "Name",
                        )
                    ),
                    "to_port_step_id": other_port.id(),
                    "to_port_global_id": safe_value(
                        other_port,
                        "GlobalId",
                    ),
                    "to_port_name": safe_value(
                        other_port,
                        "Name",
                    ),
                    "to_flow_direction": safe_value(
                        other_port,
                        "FlowDirection",
                    ),
                    "to_owner_step_id": (
                        ""
                        if owner2 is None
                        else owner2.id()
                    ),
                    "to_owner_global_id": (
                        ""
                        if owner2 is None
                        else safe_value(
                            owner2,
                            "GlobalId",
                        )
                    ),
                    "to_owner_class": (
                        ""
                        if owner2 is None
                        else owner2.is_a()
                    ),
                    "to_owner_name": (
                        ""
                        if owner2 is None
                        else safe_value(
                            owner2,
                            "Name",
                        )
                    ),
                }
            )

    print()
    print("=== CONNECTION SUMMARY ===")
    print()

    print(
        f"Connections found : {connection_count}"
    )
    print(
        f"Internal           : "
        f"{internal_connection_count}"
    )
    print(
        f"External           : "
        f"{external_connection_count}"
    )

    print()

    #
    # Fan-centered traversal
    #
    fans = [
        element
        for element in system_elements
        if element.is_a("IfcFan")
    ]

    print("=== FAN-CENTERED TRACE ===")
    print()

    if not fans:
        print("No IfcFan found in target system.")

    for fan in fans:

        print(
            f"START FAN: "
            f"{safe_value(fan, 'Name')}"
        )

        fan_ports = get_element_ports(fan)

        print(
            f"Fan ports : {len(fan_ports)}"
        )

        visited_ports = set()
        visited_elements = set()

        queue = deque()

        for port in fan_ports:
            queue.append(
                (
                    port,
                    0,
                )
            )

        while queue:

            port, depth = queue.popleft()

            if port.id() in visited_ports:
                continue

            visited_ports.add(port.id())

            owner = port_owner.get(
                port.id()
            )

            indent = "  " * depth

            print(
                f"{indent}"
                f"Port #{port.id()} "
                f"[{safe_value(port, 'FlowDirection')}] "
                f"Owner={describe_element(owner)}"
            )

            if owner is not None:
                visited_elements.add(
                    owner.id()
                )

            for connection in port_graph.get(
                port.id(),
                [],
            ):

                other_port = connection["port"]

                other_owner = port_owner.get(
                    other_port.id()
                )

                print(
                    f"{indent}  -> "
                    f"Port #{other_port.id()} "
                    f"[{safe_value(other_port, 'FlowDirection')}] "
                    f"Owner={describe_element(other_owner)}"
                )

                #
                # Continue only through the target system.
                #
                if other_port.id() not in member_ids:
                    continue

                if (
                    other_port.id()
                    not in visited_ports
                ):
                    queue.append(
                        (
                            other_port,
                            depth + 1,
                        )
                    )

                #
                # Once we arrive at another element,
                # add all of that element's ports.
                #
                if other_owner is not None:

                    if other_owner.id() in member_ids:

                        for owner_port in get_element_ports(
                            other_owner
                        ):
                            if (
                                owner_port.id()
                                not in visited_ports
                            ):
                                queue.append(
                                    (
                                        owner_port,
                                        depth + 1,
                                    )
                                )

        print()
        print(
            f"Visited ports    : "
            f"{len(visited_ports)}"
        )
        print(
            f"Visited elements : "
            f"{len(visited_elements)}"
        )

        print()

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "system_global_id",
        "system_name",
        "system_object_type",
        "connection_scope",
        "relationship_global_id",
        "from_port_step_id",
        "from_port_global_id",
        "from_port_name",
        "from_flow_direction",
        "from_owner_step_id",
        "from_owner_global_id",
        "from_owner_class",
        "from_owner_name",
        "to_port_step_id",
        "to_port_global_id",
        "to_port_name",
        "to_flow_direction",
        "to_owner_step_id",
        "to_owner_global_id",
        "to_owner_class",
        "to_owner_name",
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
        f"System members       : "
        f"{len(members)}"
    )
    print(
        f"System ports         : "
        f"{len(system_ports)}"
    )
    print(
        f"Port connections     : "
        f"{connection_count}"
    )
    print(
        f"CSV rows             : "
        f"{len(rows)}"
    )
    print()
    print(f"CSV written: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()