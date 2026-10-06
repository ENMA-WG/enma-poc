from collections import Counter
from pathlib import Path
import csv

import ifcopenshell


IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")
OUTPUT_FILE = Path("output/ifc_connectivity_relationships_EA18.csv")

TARGET_SYSTEM_NAME = "EA 18"
TARGET_SYSTEM_OBJECT_TYPE = "105_EA排気"


RELATIONSHIP_TYPES = [
    "IfcRelConnectsPorts",
    "IfcRelConnectsPortToElement",
    "IfcRelConnectsElements",
    "IfcRelConnectsPathElements",
    "IfcRelNests",
    "IfcRelAggregates",
    "IfcRelAssignsToGroup",
]


def safe_value(obj, attr):
    """Return IFC attribute as printable text."""
    value = getattr(obj, attr, None)

    if value is None:
        return ""

    return str(value)


def describe(obj):
    """Compact IFC object description."""
    if obj is None:
        return ""

    try:
        ifc_class = obj.is_a()
    except Exception:
        return str(obj)

    step_id = ""

    try:
        step_id = obj.id()
    except Exception:
        pass

    name = safe_value(obj, "Name")

    return f"#{step_id} {ifc_class} | {name}"


def get_target_system(model):
    """Find target IfcDistributionSystem."""
    for system in model.by_type("IfcDistributionSystem"):

        if (
            safe_value(system, "Name") == TARGET_SYSTEM_NAME
            and
            safe_value(system, "ObjectType")
            == TARGET_SYSTEM_OBJECT_TYPE
        ):
            return system

    return None


def get_system_members(system):
    """Return formally assigned system members."""
    members = []

    for rel in getattr(system, "IsGroupedBy", []) or []:

        for obj in getattr(rel, "RelatedObjects", []) or []:
            members.append(obj)

    return members


def get_nested_ports(element):
    """Return ports nested under an element."""
    ports = []

    for rel in getattr(element, "IsNestedBy", []) or []:

        for obj in getattr(rel, "RelatedObjects", []) or []:

            if obj.is_a("IfcDistributionPort"):
                ports.append(obj)

    return ports


def entity_references_target(value, target_ids):
    """
    Recursively inspect an IFC relationship attribute
    and determine whether it references one of the
    target STEP ids.
    """
    if value is None:
        return False

    if isinstance(value, (list, tuple)):
        return any(
            entity_references_target(
                item,
                target_ids,
            )
            for item in value
        )

    try:
        entity_id = value.id()

        if entity_id in target_ids:
            return True

    except Exception:
        pass

    return False


def relationship_targets(rel, target_ids):
    """
    Return names of relationship attributes that
    reference a target element/port.
    """
    matches = []

    info = rel.get_info()

    for attr_name in info:

        if attr_name in {
            "id",
            "type",
            "GlobalId",
            "OwnerHistory",
            "Name",
            "Description",
        }:
            continue

        try:
            value = getattr(rel, attr_name)
        except Exception:
            continue

        if entity_references_target(
            value,
            target_ids,
        ):
            matches.append(attr_name)

    return matches


def relationship_summary(rel):
    """
    Produce human-readable details for common
    connectivity relationships.
    """
    if rel.is_a("IfcRelConnectsPorts"):

        return (
            f"RelatingPort={describe(rel.RelatingPort)} ; "
            f"RelatedPort={describe(rel.RelatedPort)}"
        )

    if rel.is_a("IfcRelConnectsPortToElement"):

        return (
            f"RelatingPort={describe(rel.RelatingPort)} ; "
            f"RelatedElement={describe(rel.RelatedElement)}"
        )

    if rel.is_a("IfcRelConnectsElements"):

        return (
            f"RelatingElement="
            f"{describe(rel.RelatingElement)} ; "
            f"RelatedElement="
            f"{describe(rel.RelatedElement)}"
        )

    if rel.is_a("IfcRelNests"):

        related = ", ".join(
            describe(obj)
            for obj in rel.RelatedObjects
        )

        return (
            f"RelatingObject="
            f"{describe(rel.RelatingObject)} ; "
            f"RelatedObjects={related}"
        )

    if rel.is_a("IfcRelAggregates"):

        related = ", ".join(
            describe(obj)
            for obj in rel.RelatedObjects
        )

        return (
            f"RelatingObject="
            f"{describe(rel.RelatingObject)} ; "
            f"RelatedObjects={related}"
        )

    if rel.is_a("IfcRelAssignsToGroup"):

        related = ", ".join(
            describe(obj)
            for obj in rel.RelatedObjects
        )

        return (
            f"RelatingGroup="
            f"{describe(rel.RelatingGroup)} ; "
            f"RelatedObjects={related}"
        )

    return ""


def main():
    print("=== IFC CONNECTIVITY RELATIONSHIP INSPECTION ===")
    print()
    print(f"IFC    : {IFC_FILE}")
    print(
        f"Target : "
        f"{TARGET_SYSTEM_NAME} | "
        f"{TARGET_SYSTEM_OBJECT_TYPE}"
    )
    print(f"Output : {OUTPUT_FILE}")
    print()

    model = ifcopenshell.open(str(IFC_FILE))

    #
    # 1. Whole-IFC relationship inventory
    #
    print("=== WHOLE IFC RELATIONSHIP COUNTS ===")
    print()

    relationship_counts = {}

    for rel_type in RELATIONSHIP_TYPES:

        try:
            relationships = model.by_type(rel_type)
            count = len(relationships)
        except Exception:
            count = 0

        relationship_counts[rel_type] = count

        print(
            f"{rel_type:30s} : "
            f"{count}"
        )

    print()

    #
    # 2. Target system
    #
    system = get_target_system(model)

    if system is None:
        print("ERROR: Target system was not found.")
        return

    members = get_system_members(system)

    system_ports = [
        obj
        for obj in members
        if obj.is_a("IfcDistributionPort")
    ]

    system_elements = [
        obj
        for obj in members
        if not obj.is_a("IfcDistributionPort")
    ]

    print("=== TARGET SYSTEM MEMBERS ===")
    print()

    counter = Counter(
        obj.is_a()
        for obj in members
    )

    for ifc_class, count in counter.most_common():
        print(
            f"{count:5d}  "
            f"{ifc_class}"
        )

    print()

    #
    # Include ports nested under system elements,
    # even when they are not formal system members.
    #
    nested_ports = []

    for element in system_elements:

        for port in get_nested_ports(element):

            if port not in nested_ports:
                nested_ports.append(port)

    all_target_objects = []

    for obj in (
        [system]
        + system_elements
        + system_ports
        + nested_ports
    ):
        if obj not in all_target_objects:
            all_target_objects.append(obj)

    target_ids = {
        obj.id()
        for obj in all_target_objects
    }

    print(
        f"Formal system ports : "
        f"{len(system_ports)}"
    )

    print(
        f"Nested element ports: "
        f"{len(nested_ports)}"
    )

    print(
        f"Target STEP ids     : "
        f"{len(target_ids)}"
    )

    print()

    print("=== TARGET OBJECTS ===")
    print()

    for obj in sorted(
        all_target_objects,
        key=lambda x: x.id(),
    ):

        membership = []

        if obj.id() == system.id():
            membership.append("SYSTEM")

        if obj in system_elements:
            membership.append("SYSTEM_ELEMENT")

        if obj in system_ports:
            membership.append("SYSTEM_PORT")

        if obj in nested_ports:
            membership.append("NESTED_PORT")

        print(
            f"#{obj.id():6d} | "
            f"{obj.is_a():24s} | "
            f"{','.join(membership):25s} | "
            f"{safe_value(obj, 'Name')}"
        )

    print()

    #
    # 3. Find relationships that reference
    #    EA 18 objects or their ports.
    #
    print("=== RELATIONSHIPS REFERENCING EA 18 ===")
    print()

    rows = []
    target_rel_counter = Counter()

    for rel_type in RELATIONSHIP_TYPES:

        try:
            relationships = model.by_type(rel_type)
        except Exception:
            continue

        for rel in relationships:

            matched_attributes = relationship_targets(
                rel,
                target_ids,
            )

            if not matched_attributes:
                continue

            target_rel_counter[rel_type] += 1

            detail = relationship_summary(rel)

            print(
                f"#{rel.id():6d} | "
                f"{rel_type:30s} | "
                f"{','.join(matched_attributes)}"
            )

            if detail:
                print(
                    f"         {detail}"
                )

            rows.append(
                {
                    "relationship_step_id": rel.id(),
                    "relationship_global_id": safe_value(
                        rel,
                        "GlobalId",
                    ),
                    "relationship_type": rel_type,
                    "matched_attributes": ",".join(
                        matched_attributes
                    ),
                    "relationship_detail": detail,
                }
            )

    if not rows:
        print(
            "(no relationships referencing "
            "target objects)"
        )

    print()

    print("=== EA 18 RELATIONSHIP SUMMARY ===")
    print()

    for rel_type in RELATIONSHIP_TYPES:

        print(
            f"{rel_type:30s} : "
            f"{target_rel_counter.get(rel_type, 0)}"
        )

    print()

    #
    # 4. Dedicated check of explicit physical
    #    connectivity relationships.
    #
    print("=== EXPLICIT CONNECTIVITY CHECK ===")
    print()

    connectivity_types = [
        "IfcRelConnectsPorts",
        "IfcRelConnectsPortToElement",
        "IfcRelConnectsElements",
        "IfcRelConnectsPathElements",
    ]

    connectivity_found = False

    for rel_type in connectivity_types:

        count = target_rel_counter.get(
            rel_type,
            0,
        )

        print(
            f"{rel_type:30s} : "
            f"{count}"
        )

        if count > 0:
            connectivity_found = True

    print()

    if connectivity_found:

        print(
            "RESULT: Explicit connectivity "
            "relationships were found."
        )

        print(
            "        Inspect the relationship "
            "details before topology inference."
        )

    else:

        print(
            "RESULT: No explicit connectivity "
            "relationship was found for EA 18."
        )

        print(
            "        System membership and port "
            "ownership may exist without"
        )

        print(
            "        explicit element-to-element "
            "network connectivity."
        )

    #
    # 5. CSV
    #
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "relationship_step_id",
        "relationship_global_id",
        "relationship_type",
        "matched_attributes",
        "relationship_detail",
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

    print()
    print("=== RESULT ===")
    print()

    print(
        f"Whole IFC IfcRelConnectsPorts        : "
        f"{relationship_counts.get('IfcRelConnectsPorts', 0)}"
    )

    print(
        f"Whole IFC IfcRelConnectsPortToElement: "
        f"{relationship_counts.get('IfcRelConnectsPortToElement', 0)}"
    )

    print(
        f"Whole IFC IfcRelConnectsElements     : "
        f"{relationship_counts.get('IfcRelConnectsElements', 0)}"
    )

    print(
        f"EA 18 related relationships          : "
        f"{len(rows)}"
    )

    print()

    print(f"CSV written: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()