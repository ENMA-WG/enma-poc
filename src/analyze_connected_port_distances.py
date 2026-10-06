from collections import Counter
from pathlib import Path
from math import sqrt
import csv

import ifcopenshell
import ifcopenshell.util.placement
import ifcopenshell.util.unit


IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")

OUTPUT_FILE = Path(
    "output/connected_port_distances.csv"
)


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
        port STEP id -> owner element

    Port ownership is obtained from IfcRelNests.
    """
    owners = {}

    for rel in model.by_type(
        "IfcRelNests"
    ):

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

            if obj.is_a(
                "IfcDistributionPort"
            ):
                owners[obj.id()] = owner

    return owners


def get_world_coordinates(obj):
    """
    Return world X/Y/Z coordinates
    from ObjectPlacement.

    Coordinates are returned in the
    IFC project's native length unit.
    """
    placement = getattr(
        obj,
        "ObjectPlacement",
        None,
    )

    if placement is None:
        return None

    try:
        matrix = (
            ifcopenshell.util.placement
            .get_local_placement(
                placement
            )
        )

        return (
            float(matrix[0][3]),
            float(matrix[1][3]),
            float(matrix[2][3]),
        )

    except Exception as exc:
        print(
            f"WARNING: placement failed "
            f"for #{obj.id()}: {exc}"
        )

        return None


def distance_3d(point1, point2):
    """Return Euclidean 3D distance."""
    return sqrt(
        (point1[0] - point2[0]) ** 2
        + (point1[1] - point2[1]) ** 2
        + (point1[2] - point2[2]) ** 2
    )


def get_distance_band(distance_mm):
    """
    Descriptive distance band only.

    This is NOT a connectivity rule.
    Connectivity is already explicitly
    stated by IfcRelConnectsPorts.
    """
    if distance_mm <= 0.001:
        return "ZERO"

    if distance_mm <= 1.0:
        return "<=1mm"

    if distance_mm <= 10.0:
        return "<=10mm"

    if distance_mm <= 50.0:
        return "<=50mm"

    if distance_mm <= 100.0:
        return "<=100mm"

    if distance_mm <= 500.0:
        return "<=500mm"

    return ">500mm"


def normalized_class_pair(owner1, owner2):
    """
    Normalize owner class pair so:
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
    print(
        "=== CONNECTED PORT DISTANCE ANALYSIS ==="
    )
    print()

    print(
        f"IFC    : {IFC_FILE}"
    )

    print(
        f"Output : {OUTPUT_FILE}"
    )

    print()

    model = ifcopenshell.open(
        str(IFC_FILE)
    )

    unit_scale = (
        ifcopenshell.util.unit
        .calculate_unit_scale(model)
    )

    connections = model.by_type(
        "IfcRelConnectsPorts"
    )

    owner_map = get_port_owner_map(
        model
    )

    print("=== BASIC COUNTS ===")
    print()

    print(
        f"Unit scale to metre   : "
        f"{unit_scale}"
    )

    print(
        f"IfcDistributionPort   : "
        f"{len(model.by_type('IfcDistributionPort'))}"
    )

    print(
        f"IfcRelConnectsPorts   : "
        f"{len(connections)}"
    )

    print(
        f"Ports with owner      : "
        f"{len(owner_map)}"
    )

    print()

    rows = []

    distance_band_counter = Counter()
    class_pair_counter = Counter()

    missing_port_count = 0
    missing_placement_count = 0
    missing_owner_count = 0

    #
    # Cache port coordinates because the
    # same port may appear in more than one
    # relationship.
    #
    coordinate_cache = {}

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
            missing_port_count += 1
            continue

        owner1 = owner_map.get(
            port1.id()
        )

        owner2 = owner_map.get(
            port2.id()
        )

        if owner1 is None or owner2 is None:
            missing_owner_count += 1

        if port1.id() not in coordinate_cache:
            coordinate_cache[
                port1.id()
            ] = get_world_coordinates(
                port1
            )

        if port2.id() not in coordinate_cache:
            coordinate_cache[
                port2.id()
            ] = get_world_coordinates(
                port2
            )

        point1 = coordinate_cache[
            port1.id()
        ]

        point2 = coordinate_cache[
            port2.id()
        ]

        if point1 is None or point2 is None:
            missing_placement_count += 1
            continue

        distance_project_unit = (
            distance_3d(
                point1,
                point2,
            )
        )

        distance_m = (
            distance_project_unit
            * unit_scale
        )

        distance_mm = (
            distance_m
            * 1000.0
        )

        distance_band = (
            get_distance_band(
                distance_mm
            )
        )

        distance_band_counter[
            distance_band
        ] += 1

        pair = normalized_class_pair(
            owner1,
            owner2,
        )

        class_pair_counter[
            pair
        ] += 1

        owner1_class = (
            owner1.is_a()
            if owner1 is not None
            else ""
        )

        owner2_class = (
            owner2.is_a()
            if owner2 is not None
            else ""
        )

        owner1_name = (
            safe_value(
                owner1,
                "Name",
            )
            if owner1 is not None
            else ""
        )

        owner2_name = (
            safe_value(
                owner2,
                "Name",
            )
            if owner2 is not None
            else ""
        )

        rows.append(
            {
                "relationship_step_id": (
                    rel.id()
                ),
                "relationship_global_id": (
                    safe_value(
                        rel,
                        "GlobalId",
                    )
                ),

                "port1_step_id": (
                    port1.id()
                ),
                "port1_global_id": (
                    safe_value(
                        port1,
                        "GlobalId",
                    )
                ),
                "port1_name": (
                    safe_value(
                        port1,
                        "Name",
                    )
                ),
                "port1_flow_direction": (
                    safe_value(
                        port1,
                        "FlowDirection",
                    )
                ),

                "owner1_step_id": (
                    ""
                    if owner1 is None
                    else owner1.id()
                ),
                "owner1_class": (
                    owner1_class
                ),
                "owner1_name": (
                    owner1_name
                ),

                "port2_step_id": (
                    port2.id()
                ),
                "port2_global_id": (
                    safe_value(
                        port2,
                        "GlobalId",
                    )
                ),
                "port2_name": (
                    safe_value(
                        port2,
                        "Name",
                    )
                ),
                "port2_flow_direction": (
                    safe_value(
                        port2,
                        "FlowDirection",
                    )
                ),

                "owner2_step_id": (
                    ""
                    if owner2 is None
                    else owner2.id()
                ),
                "owner2_class": (
                    owner2_class
                ),
                "owner2_name": (
                    owner2_name
                ),

                "class_pair": (
                    f"{pair[0]} <-> "
                    f"{pair[1]}"
                ),

                "port1_x_project_unit": (
                    point1[0]
                ),
                "port1_y_project_unit": (
                    point1[1]
                ),
                "port1_z_project_unit": (
                    point1[2]
                ),

                "port2_x_project_unit": (
                    point2[0]
                ),
                "port2_y_project_unit": (
                    point2[1]
                ),
                "port2_z_project_unit": (
                    point2[2]
                ),

                "distance_project_unit": (
                    distance_project_unit
                ),
                "distance_m": (
                    distance_m
                ),
                "distance_mm": (
                    distance_mm
                ),
                "distance_band": (
                    distance_band
                ),
            }
        )

    #
    # Sort from nearest to farthest.
    #
    rows.sort(
        key=lambda row: row[
            "distance_mm"
        ]
    )

    print(
        "=== DISTANCE DISTRIBUTION ==="
    )
    print()

    band_order = [
        "ZERO",
        "<=1mm",
        "<=10mm",
        "<=50mm",
        "<=100mm",
        "<=500mm",
        ">500mm",
    ]

    for band in band_order:

        count = distance_band_counter[
            band
        ]

        print(
            f"{band:8s} : "
            f"{count:5d}"
        )

    print()

    #
    # Basic statistics.
    #
    distances = [
        row["distance_mm"]
        for row in rows
    ]

    if distances:

        sorted_distances = sorted(
            distances
        )

        count = len(
            sorted_distances
        )

        minimum = (
            sorted_distances[0]
        )

        maximum = (
            sorted_distances[-1]
        )

        average = (
            sum(sorted_distances)
            / count
        )

        if count % 2 == 1:

            median = (
                sorted_distances[
                    count // 2
                ]
            )

        else:

            median = (
                sorted_distances[
                    count // 2 - 1
                ]
                +
                sorted_distances[
                    count // 2
                ]
            ) / 2.0

        print(
            "=== DISTANCE STATISTICS ==="
        )
        print()

        print(
            f"Count   : {count}"
        )

        print(
            f"Minimum : "
            f"{minimum:.6f} mm"
        )

        print(
            f"Median  : "
            f"{median:.6f} mm"
        )

        print(
            f"Average : "
            f"{average:.6f} mm"
        )

        print(
            f"Maximum : "
            f"{maximum:.6f} mm"
        )

        print()

    #
    # Class pair summary.
    #
    print(
        "=== CONNECTION CLASS PAIRS ==="
    )
    print()

    for pair, count in (
        class_pair_counter.most_common()
    ):

        print(
            f"{count:5d}  "
            f"{pair[0]} <-> "
            f"{pair[1]}"
        )

    print()

    #
    # Nearest examples.
    #
    print(
        "=== NEAREST EXPLICIT CONNECTIONS ==="
    )
    print()

    for row in rows[:20]:

        print(
            f"{row['distance_mm']:12.6f} mm | "
            f"#{row['port1_step_id']} "
            f"{row['owner1_class']} "
            f"<-> "
            f"#{row['port2_step_id']} "
            f"{row['owner2_class']}"
        )

    print()

    #
    # Farthest examples are particularly
    # useful for detecting whether placement
    # distance is a reliable connectivity
    # indicator in this IFC.
    #
    print(
        "=== FARTHEST EXPLICIT CONNECTIONS ==="
    )
    print()

    for row in reversed(
        rows[-20:]
    ):

        print(
            f"{row['distance_mm']:12.6f} mm | "
            f"#{row['port1_step_id']} "
            f"{row['owner1_class']} "
            f"<-> "
            f"#{row['port2_step_id']} "
            f"{row['owner2_class']}"
        )

        print(
            f"               "
            f"{row['owner1_name']}"
        )

        print(
            f"               "
            f"{row['owner2_name']}"
        )

    #
    # CSV
    #
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fields = [
        "relationship_step_id",
        "relationship_global_id",

        "port1_step_id",
        "port1_global_id",
        "port1_name",
        "port1_flow_direction",

        "owner1_step_id",
        "owner1_class",
        "owner1_name",

        "port2_step_id",
        "port2_global_id",
        "port2_name",
        "port2_flow_direction",

        "owner2_step_id",
        "owner2_class",
        "owner2_name",

        "class_pair",

        "port1_x_project_unit",
        "port1_y_project_unit",
        "port1_z_project_unit",

        "port2_x_project_unit",
        "port2_y_project_unit",
        "port2_z_project_unit",

        "distance_project_unit",
        "distance_m",
        "distance_mm",
        "distance_band",
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fields,
        )

        writer.writeheader()
        writer.writerows(
            rows
        )

    print()
    print("=== RESULT ===")
    print()

    print(
        f"Explicit connections       : "
        f"{len(connections)}"
    )

    print(
        f"Connections measured       : "
        f"{len(rows)}"
    )

    print(
        f"Missing port relationship  : "
        f"{missing_port_count}"
    )

    print(
        f"Missing owner              : "
        f"{missing_owner_count}"
    )

    print(
        f"Missing placement          : "
        f"{missing_placement_count}"
    )

    if distances:

        zero_count = (
            distance_band_counter[
                "ZERO"
            ]
        )

        within_1mm = sum(
            1
            for value in distances
            if value <= 1.0
        )

        within_10mm = sum(
            1
            for value in distances
            if value <= 10.0
        )

        print()

        print(
            f"Exactly / virtually zero   : "
            f"{zero_count}"
        )

        print(
            f"Within 1 mm                : "
            f"{within_1mm}"
        )

        print(
            f"Within 10 mm               : "
            f"{within_10mm}"
        )

    print()

    print(
        f"CSV written: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()