"""
inspect_port_topology.py

ENMA-WG
IFC Distribution Port Topology Inspector

目的
----
営繕BIMモデル_EM.ifc に含まれる IfcDistributionPort と
IfcRelConnectsPorts の構造を棚卸しする。

特に以下を確認する。

1. IfcDistributionPort は何個あるか
2. Port はどの方法で親Elementに所属しているか
   - IfcRelNests
   - IfcRelAggregates
   - IfcRelConnectsPortToElement
3. 1,144件の IfcRelConnectsPorts の両端Portの親は何者か
4. 親Element同士の IFC Class の組合せ
5. PipeSegment が Port 経由で何につながっているか

出力
----
コンソール:
    全体Summary
    親Element Class集計
    接続Classペア集計
    代表例

CSV:
    output/port_parent_inventory.csv
    output/port_connection_inventory.csv
"""

from pathlib import Path
from collections import Counter, defaultdict
import csv

import ifcopenshell


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

IFC_PATH = (
    PROJECT_ROOT
    / "data"
    / "営繕BIMモデル_EM.ifc"
)

OUTPUT_DIR = PROJECT_ROOT / "output"

PORT_PARENT_CSV = (
    OUTPUT_DIR
    / "port_parent_inventory.csv"
)

PORT_CONNECTION_CSV = (
    OUTPUT_DIR
    / "port_connection_inventory.csv"
)


# ============================================================
# Settings
# ============================================================

EXAMPLE_LIMIT = 20


# ============================================================
# Utility
# ============================================================

def safe_text(value):
    if value is None:
        return ""

    if hasattr(value, "wrappedValue"):
        value = value.wrappedValue

    return str(value)


def entity_class(entity):
    if entity is None:
        return ""

    return entity.is_a()


def entity_name(entity):
    if entity is None:
        return ""

    return safe_text(
        getattr(entity, "Name", None)
    )


def entity_object_type(entity):
    if entity is None:
        return ""

    return safe_text(
        getattr(entity, "ObjectType", None)
    )


def entity_global_id(entity):
    if entity is None:
        return ""

    return safe_text(
        getattr(entity, "GlobalId", None)
    )


def entity_predefined_type(entity):
    if entity is None:
        return ""

    return safe_text(
        getattr(entity, "PredefinedType", None)
    )


# ============================================================
# Parent indexes
# ============================================================

def build_parent_indexes(model):
    """
    Port -> parent Element の索引を構築する。

    IFC Exporter によってPortの所属表現が異なる可能性が
    あるため、複数Relationを調査する。
    """

    port_parents = defaultdict(list)

    relation_counts = Counter()

    # --------------------------------------------------------
    # IfcRelNests
    # --------------------------------------------------------

    for rel in model.by_type("IfcRelNests"):

        parent = getattr(
            rel,
            "RelatingObject",
            None,
        )

        children = getattr(
            rel,
            "RelatedObjects",
            None,
        ) or []

        for child in children:

            if child.is_a(
                "IfcDistributionPort"
            ):
                port_parents[
                    child.id()
                ].append(
                    (
                        parent,
                        "IfcRelNests",
                        rel,
                    )
                )

                relation_counts[
                    "IfcRelNests"
                ] += 1

    # --------------------------------------------------------
    # IfcRelAggregates
    # --------------------------------------------------------

    for rel in model.by_type(
        "IfcRelAggregates"
    ):

        parent = getattr(
            rel,
            "RelatingObject",
            None,
        )

        children = getattr(
            rel,
            "RelatedObjects",
            None,
        ) or []

        for child in children:

            if child.is_a(
                "IfcDistributionPort"
            ):
                port_parents[
                    child.id()
                ].append(
                    (
                        parent,
                        "IfcRelAggregates",
                        rel,
                    )
                )

                relation_counts[
                    "IfcRelAggregates"
                ] += 1

    # --------------------------------------------------------
    # IfcRelConnectsPortToElement
    # --------------------------------------------------------

    for rel in model.by_type(
        "IfcRelConnectsPortToElement"
    ):

        port = getattr(
            rel,
            "RelatingPort",
            None,
        )

        parent = getattr(
            rel,
            "RelatedElement",
            None,
        )

        if (
            port is not None
            and parent is not None
        ):
            port_parents[
                port.id()
            ].append(
                (
                    parent,
                    "IfcRelConnectsPortToElement",
                    rel,
                )
            )

            relation_counts[
                "IfcRelConnectsPortToElement"
            ] += 1

    return (
        port_parents,
        relation_counts,
    )


# ============================================================
# Resolve parents
# ============================================================

def get_port_parents(
    port,
    port_parents,
):
    """
    同じ親が複数Relationから得られた場合に重複除去。
    """

    result = []

    seen = set()

    for (
        parent,
        method,
        rel,
    ) in port_parents.get(
        port.id(),
        [],
    ):

        if parent is None:
            continue

        key = (
            parent.id(),
            method,
        )

        if key in seen:
            continue

        seen.add(key)

        result.append(
            (
                parent,
                method,
                rel,
            )
        )

    return result


def first_parent(
    port,
    port_parents,
):
    parents = get_port_parents(
        port,
        port_parents,
    )

    if not parents:
        return (
            None,
            "",
            None,
        )

    return parents[0]


# ============================================================
# Port inventory
# ============================================================

def build_port_inventory(
    ports,
    port_parents,
):
    rows = []

    parent_class_counter = Counter()

    parent_method_counter = Counter()

    no_parent_count = 0

    multiple_parent_count = 0

    for port in ports:

        parents = get_port_parents(
            port,
            port_parents,
        )

        if not parents:
            no_parent_count += 1

            rows.append(
                {
                    "PortStepId":
                        port.id(),

                    "PortGlobalId":
                        entity_global_id(port),

                    "PortName":
                        entity_name(port),

                    "FlowDirection":
                        safe_text(
                            getattr(
                                port,
                                "FlowDirection",
                                None,
                            )
                        ),

                    "SystemType":
                        safe_text(
                            getattr(
                                port,
                                "SystemType",
                                None,
                            )
                        ),

                    "ParentCount":
                        0,

                    "ParentMethod":
                        "",

                    "ParentStepId":
                        "",

                    "ParentGlobalId":
                        "",

                    "ParentClass":
                        "",

                    "ParentName":
                        "",

                    "ParentObjectType":
                        "",

                    "ParentPredefinedType":
                        "",
                }
            )

            continue

        if len(parents) > 1:
            multiple_parent_count += 1

        for (
            parent,
            method,
            rel,
        ) in parents:

            parent_class_counter[
                entity_class(parent)
            ] += 1

            parent_method_counter[
                method
            ] += 1

            rows.append(
                {
                    "PortStepId":
                        port.id(),

                    "PortGlobalId":
                        entity_global_id(port),

                    "PortName":
                        entity_name(port),

                    "FlowDirection":
                        safe_text(
                            getattr(
                                port,
                                "FlowDirection",
                                None,
                            )
                        ),

                    "SystemType":
                        safe_text(
                            getattr(
                                port,
                                "SystemType",
                                None,
                            )
                        ),

                    "ParentCount":
                        len(parents),

                    "ParentMethod":
                        method,

                    "ParentStepId":
                        parent.id(),

                    "ParentGlobalId":
                        entity_global_id(parent),

                    "ParentClass":
                        entity_class(parent),

                    "ParentName":
                        entity_name(parent),

                    "ParentObjectType":
                        entity_object_type(parent),

                    "ParentPredefinedType":
                        entity_predefined_type(parent),
                }
            )

    return {
        "rows":
            rows,

        "parent_class_counter":
            parent_class_counter,

        "parent_method_counter":
            parent_method_counter,

        "no_parent_count":
            no_parent_count,

        "multiple_parent_count":
            multiple_parent_count,
    }


# ============================================================
# Connection inventory
# ============================================================

def build_connection_inventory(
    model,
    port_parents,
):
    rows = []

    pair_counter = Counter()

    unresolved_a = 0
    unresolved_b = 0
    unresolved_both = 0

    same_parent_count = 0

    pipe_related_count = 0

    relations = model.by_type(
        "IfcRelConnectsPorts"
    )

    for no, rel in enumerate(
        relations,
        start=1,
    ):

        port_a = getattr(
            rel,
            "RelatingPort",
            None,
        )

        port_b = getattr(
            rel,
            "RelatedPort",
            None,
        )

        parent_a, method_a, _ = (
            first_parent(
                port_a,
                port_parents,
            )
            if port_a is not None
            else (None, "", None)
        )

        parent_b, method_b, _ = (
            first_parent(
                port_b,
                port_parents,
            )
            if port_b is not None
            else (None, "", None)
        )

        if parent_a is None:
            unresolved_a += 1

        if parent_b is None:
            unresolved_b += 1

        if (
            parent_a is None
            and parent_b is None
        ):
            unresolved_both += 1

        class_a = (
            entity_class(parent_a)
            if parent_a is not None
            else "UNRESOLVED"
        )

        class_b = (
            entity_class(parent_b)
            if parent_b is not None
            else "UNRESOLVED"
        )

        # Class pairは順序を正規化
        pair = tuple(
            sorted(
                (
                    class_a,
                    class_b,
                )
            )
        )

        pair_counter[pair] += 1

        if (
            parent_a is not None
            and parent_b is not None
            and parent_a.id()
            == parent_b.id()
        ):
            same_parent_count += 1

        if (
            class_a == "IfcPipeSegment"
            or class_b == "IfcPipeSegment"
        ):
            pipe_related_count += 1

        rows.append(
            {
                "No":
                    no,

                "RelationStepId":
                    rel.id(),

                # Port A
                "PortA_StepId":
                    port_a.id()
                    if port_a is not None
                    else "",

                "PortA_GlobalId":
                    entity_global_id(port_a),

                "PortA_Name":
                    entity_name(port_a),

                "PortA_FlowDirection":
                    safe_text(
                        getattr(
                            port_a,
                            "FlowDirection",
                            None,
                        )
                    )
                    if port_a is not None
                    else "",

                "PortA_SystemType":
                    safe_text(
                        getattr(
                            port_a,
                            "SystemType",
                            None,
                        )
                    )
                    if port_a is not None
                    else "",

                # Parent A
                "ParentA_Method":
                    method_a,

                "ParentA_StepId":
                    parent_a.id()
                    if parent_a is not None
                    else "",

                "ParentA_GlobalId":
                    entity_global_id(parent_a),

                "ParentA_Class":
                    class_a,

                "ParentA_Name":
                    entity_name(parent_a),

                "ParentA_ObjectType":
                    entity_object_type(parent_a),

                "ParentA_PredefinedType":
                    entity_predefined_type(parent_a),

                # Port B
                "PortB_StepId":
                    port_b.id()
                    if port_b is not None
                    else "",

                "PortB_GlobalId":
                    entity_global_id(port_b),

                "PortB_Name":
                    entity_name(port_b),

                "PortB_FlowDirection":
                    safe_text(
                        getattr(
                            port_b,
                            "FlowDirection",
                            None,
                        )
                    )
                    if port_b is not None
                    else "",

                "PortB_SystemType":
                    safe_text(
                        getattr(
                            port_b,
                            "SystemType",
                            None,
                        )
                    )
                    if port_b is not None
                    else "",

                # Parent B
                "ParentB_Method":
                    method_b,

                "ParentB_StepId":
                    parent_b.id()
                    if parent_b is not None
                    else "",

                "ParentB_GlobalId":
                    entity_global_id(parent_b),

                "ParentB_Class":
                    class_b,

                "ParentB_Name":
                    entity_name(parent_b),

                "ParentB_ObjectType":
                    entity_object_type(parent_b),

                "ParentB_PredefinedType":
                    entity_predefined_type(parent_b),

                "SameParent":
                    (
                        "YES"
                        if (
                            parent_a is not None
                            and parent_b is not None
                            and parent_a.id()
                            == parent_b.id()
                        )
                        else "NO"
                    ),
            }
        )

    return {
        "rows":
            rows,

        "pair_counter":
            pair_counter,

        "unresolved_a":
            unresolved_a,

        "unresolved_b":
            unresolved_b,

        "unresolved_both":
            unresolved_both,

        "same_parent_count":
            same_parent_count,

        "pipe_related_count":
            pipe_related_count,
    }


# ============================================================
# CSV
# ============================================================

def write_csv(
    path,
    rows,
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not rows:
        print(
            f"[WARN] No rows for {path}"
        )
        return

    with path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=list(
                rows[0].keys()
            ),
        )

        writer.writeheader()

        writer.writerows(rows)


# ============================================================
# Console output
# ============================================================

def print_counter(
    title,
    counter,
    limit=None,
):
    print()
    print(title)
    print("-" * 78)

    items = counter.most_common(
        limit
    )

    if not items:
        print("  (none)")
        return

    for key, count in items:

        if isinstance(key, tuple):
            label = " <-> ".join(key)
        else:
            label = str(key)

        print(
            f"  {count:6d}  {label}"
        )


def print_pipe_examples(
    connection_rows,
):
    print()
    print(
        "Representative Pipe-related connections"
    )
    print("-" * 78)

    shown = 0

    for row in connection_rows:

        if (
            row["ParentA_Class"]
            != "IfcPipeSegment"
            and row["ParentB_Class"]
            != "IfcPipeSegment"
        ):
            continue

        print()

        print(
            f"  Connection #{row['No']} "
            f"(IfcRelConnectsPorts "
            f"#{row['RelationStepId']})"
        )

        print(
            "    A : "
            f"{row['ParentA_Class']} "
            f"#{row['ParentA_StepId']} "
            f"'{row['ParentA_Name']}'"
        )

        print(
            "        "
            f"ObjectType="
            f"'{row['ParentA_ObjectType']}'"
        )

        print(
            "    B : "
            f"{row['ParentB_Class']} "
            f"#{row['ParentB_StepId']} "
            f"'{row['ParentB_Name']}'"
        )

        print(
            "        "
            f"ObjectType="
            f"'{row['ParentB_ObjectType']}'"
        )

        shown += 1

        if shown >= EXAMPLE_LIMIT:
            break

    if shown == 0:
        print(
            "  No resolved Pipe-related "
            "connections found."
        )


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 78)
    print(
        "ENMA-WG IFC Distribution Port "
        "Topology Inspector"
    )
    print("=" * 78)

    print(
        f"IFC : {IFC_PATH}"
    )

    if not IFC_PATH.exists():
        print()
        print(
            "[ERROR] IFC file not found."
        )
        return 1

    # --------------------------------------------------------
    # 1. Open IFC
    # --------------------------------------------------------

    print()
    print(
        "[1/6] Opening IFC..."
    )

    model = ifcopenshell.open(
        str(IFC_PATH)
    )

    print(
        f"      Schema : {model.schema}"
    )

    # --------------------------------------------------------
    # 2. Basic counts
    # --------------------------------------------------------

    print(
        "[2/6] Reading topology entities..."
    )

    ports = model.by_type(
        "IfcDistributionPort"
    )

    rel_ports = model.by_type(
        "IfcRelConnectsPorts"
    )

    rel_nests = model.by_type(
        "IfcRelNests"
    )

    rel_aggregates = model.by_type(
        "IfcRelAggregates"
    )

    rel_port_element = model.by_type(
        "IfcRelConnectsPortToElement"
    )

    print(
        f"      IfcDistributionPort          : "
        f"{len(ports)}"
    )

    print(
        f"      IfcRelConnectsPorts          : "
        f"{len(rel_ports)}"
    )

    print(
        f"      IfcRelNests                  : "
        f"{len(rel_nests)}"
    )

    print(
        f"      IfcRelAggregates             : "
        f"{len(rel_aggregates)}"
    )

    print(
        f"      IfcRelConnectsPortToElement  : "
        f"{len(rel_port_element)}"
    )

    # --------------------------------------------------------
    # 3. Parent mapping
    # --------------------------------------------------------

    print(
        "[3/6] Resolving Port -> Parent Element..."
    )

    (
        port_parents,
        relation_counts,
    ) = build_parent_indexes(
        model
    )

    port_inventory = (
        build_port_inventory(
            ports,
            port_parents,
        )
    )

    print(
        f"      Ports resolved               : "
        f"{len(ports) - port_inventory['no_parent_count']}"
    )

    print(
        f"      Ports unresolved             : "
        f"{port_inventory['no_parent_count']}"
    )

    print(
        f"      Ports with multiple parents  : "
        f"{port_inventory['multiple_parent_count']}"
    )

    # --------------------------------------------------------
    # 4. Connection mapping
    # --------------------------------------------------------

    print(
        "[4/6] Resolving Port <-> Port connections..."
    )

    connection_inventory = (
        build_connection_inventory(
            model,
            port_parents,
        )
    )

    print(
        f"      Connections                  : "
        f"{len(connection_inventory['rows'])}"
    )

    print(
        f"      Pipe-related connections     : "
        f"{connection_inventory['pipe_related_count']}"
    )

    print(
        f"      Both parents unresolved      : "
        f"{connection_inventory['unresolved_both']}"
    )

    print(
        f"      Same-parent connections      : "
        f"{connection_inventory['same_parent_count']}"
    )

    # --------------------------------------------------------
    # 5. CSV
    # --------------------------------------------------------

    print(
        "[5/6] Writing CSV..."
    )

    write_csv(
        PORT_PARENT_CSV,
        port_inventory["rows"],
    )

    write_csv(
        PORT_CONNECTION_CSV,
        connection_inventory["rows"],
    )

    # --------------------------------------------------------
    # 6. Summary
    # --------------------------------------------------------

    print(
        "[6/6] Summary..."
    )

    print_counter(
        "Port parent resolution methods",
        port_inventory[
            "parent_method_counter"
        ],
    )

    print_counter(
        "Port parent IFC Classes",
        port_inventory[
            "parent_class_counter"
        ],
    )

    print_counter(
        "Connected parent Class pairs",
        connection_inventory[
            "pair_counter"
        ],
    )

    print_pipe_examples(
        connection_inventory[
            "rows"
        ]
    )

    print()
    print("=" * 78)
    print("Output")
    print("=" * 78)

    print(
        f"Port parents : "
        f"{PORT_PARENT_CSV}"
    )

    print(
        f"Connections  : "
        f"{PORT_CONNECTION_CSV}"
    )

    print()
    print("Done.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())