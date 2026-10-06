from pathlib import Path
from math import sqrt
import csv

import ifcopenshell
import ifcopenshell.util.placement


IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")
OUTPUT_FILE = Path("output/duct_port_geometry_EA18.csv")
DISTANCE_OUTPUT_FILE = Path(
    "output/duct_port_distances_EA18.csv"
)

TARGET_SYSTEM_NAME = "EA 18"
TARGET_SYSTEM_OBJECT_TYPE = "105_EA排気"


def safe_value(obj, attr):
    """Return IFC attribute as printable text."""
    if obj is None:
        return ""

    value = getattr(obj, attr, None)

    if value is None:
        return ""

    return str(value)


def get_target_system(model):
    """Find the target IfcDistributionSystem."""
    for system in model.by_type(
        "IfcDistributionSystem"
    ):
        if (
            safe_value(system, "Name")
            == TARGET_SYSTEM_NAME
            and
            safe_value(system, "ObjectType")
            == TARGET_SYSTEM_OBJECT_TYPE
        ):
            return system

    return None


def get_system_members(system):
    """Return formal system members."""
    members = []

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

            members.append(obj)

    return members


def get_nested_ports(element):
    """Return ports nested under an element."""
    ports = []

    for rel in getattr(
        element,
        "IsNestedBy",
        [],
    ) or []:

        for obj in getattr(
            rel,
            "RelatedObjects",
            [],
        ) or []:

            if obj.is_a(
                "IfcDistributionPort"
            ):
                ports.append(obj)

    return ports


def get_port_owner_map(model):
    """
    Build:
        port STEP id -> owner element
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
    Return world X/Y/Z from ObjectPlacement.

    IfcOpenShell placement matrix:
        matrix[0][3] = X
        matrix[1][3] = Y
        matrix[2][3] = Z

    Values are returned in IFC project length units.
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
    """Euclidean distance."""
    return sqrt(
        (point1[0] - point2[0]) ** 2
        + (point1[1] - point2[1]) ** 2
        + (point1[2] - point2[2]) ** 2
    )


def get_length_unit_scale(model):
    """
    Return conversion factor from IFC project
    length unit to metres.

    Example:
        millimetres -> 0.001
        metres      -> 1.0
    """
    try:
        import ifcopenshell.util.unit

        return (
            ifcopenshell.util.unit
            .calculate_unit_scale(model)
        )

    except Exception as exc:
        print(
            "WARNING: Could not determine "
            f"unit scale: {exc}"
        )

        return 1.0


def main():
    print(
        "=== DUCT PORT GEOMETRY INSPECTION ==="
    )
    print()

    print(
        f"IFC       : {IFC_FILE}"
    )

    print(
        f"Target    : "
        f"{TARGET_SYSTEM_NAME} | "
        f"{TARGET_SYSTEM_OBJECT_TYPE}"
    )

    print(
        f"Port CSV  : {OUTPUT_FILE}"
    )

    print(
        f"Distance  : "
        f"{DISTANCE_OUTPUT_FILE}"
    )

    print()

    model = ifcopenshell.open(
        str(IFC_FILE)
    )

    unit_scale = get_length_unit_scale(
        model
    )

    print("=== IFC LENGTH UNIT ===")
    print()

    print(
        f"Unit scale to metre : "
        f"{unit_scale}"
    )

    print()

    system = get_target_system(
        model
    )

    if system is None:
        print(
            "ERROR: Target system "
            "was not found."
        )
        return

    members = get_system_members(
        system
    )

    formal_system_port_ids = {
        obj.id()
        for obj in members
        if obj.is_a(
            "IfcDistributionPort"
        )
    }

    system_elements = [
        obj
        for obj in members
        if not obj.is_a(
            "IfcDistributionPort"
        )
    ]

    owner_map = get_port_owner_map(
        model
    )

    #
    # Get every nested port belonging
    # to the system elements.
    #
    ports = {}

    for element in system_elements:

        for port in get_nested_ports(
            element
        ):

            ports[port.id()] = port

    print("=== TARGET ELEMENTS ===")
    print()

    for element in sorted(
        system_elements,
        key=lambda x: x.id(),
    ):

        nested = get_nested_ports(
            element
        )

        print(
            f"#{element.id():6d} | "
            f"{element.is_a():20s} | "
            f"ports={len(nested):2d} | "
            f"{safe_value(element, 'Name')}"
        )

    print()

    print(
        f"Nested ports found : "
        f"{len(ports)}"
    )

    print()

    #
    # Port coordinates
    #
    port_rows = []
    port_points = {}

    print("=== PORT WORLD COORDINATES ===")
    print()

    for port_id in sorted(ports):

        port = ports[
            port_id
        ]

        owner = owner_map.get(
            port.id()
        )

        point = get_world_coordinates(
            port
        )

        if point is None:

            x_raw = ""
            y_raw = ""
            z_raw = ""

            x_m = ""
            y_m = ""
            z_m = ""

        else:

            port_points[
                port.id()
            ] = point

            x_raw, y_raw, z_raw = point

            x_m = (
                x_raw * unit_scale
            )

            y_m = (
                y_raw * unit_scale
            )

            z_m = (
                z_raw * unit_scale
            )

        formal_member = (
            port.id()
            in formal_system_port_ids
        )

        owner_class = (
            owner.is_a()
            if owner is not None
            else ""
        )

        owner_name = (
            safe_value(
                owner,
                "Name",
            )
            if owner is not None
            else ""
        )

        if point is None:

            coordinate_text = (
                "(no placement)"
            )

        else:

            coordinate_text = (
                f"X={x_m:10.4f} m | "
                f"Y={y_m:10.4f} m | "
                f"Z={z_m:8.4f} m"
            )

        print(
            f"Port #{port.id():6d} | "
            f"{safe_value(port, 'FlowDirection'):13s} | "
            f"System={'YES' if formal_member else 'NO ':3s} | "
            f"{coordinate_text}"
        )

        print(
            f"               "
            f"Owner={owner_class} | "
            f"{owner_name}"
        )

        port_rows.append(
            {
                "port_step_id": port.id(),
                "port_global_id": safe_value(
                    port,
                    "GlobalId",
                ),
                "port_name": safe_value(
                    port,
                    "Name",
                ),
                "flow_direction": safe_value(
                    port,
                    "FlowDirection",
                ),
                "formal_system_member": (
                    "TRUE"
                    if formal_member
                    else "FALSE"
                ),
                "owner_step_id": (
                    ""
                    if owner is None
                    else owner.id()
                ),
                "owner_global_id": (
                    ""
                    if owner is None
                    else safe_value(
                        owner,
                        "GlobalId",
                    )
                ),
                "owner_class": owner_class,
                "owner_name": owner_name,
                "x_project_unit": x_raw,
                "y_project_unit": y_raw,
                "z_project_unit": z_raw,
                "x_m": x_m,
                "y_m": y_m,
                "z_m": z_m,
            }
        )

    print()

    #
    # Pairwise distances.
    #
    print("=== PORT-TO-PORT DISTANCES ===")
    print()

    distance_rows = []

    sorted_ids = sorted(
        port_points
    )

    for i in range(
        len(sorted_ids)
    ):

        id1 = sorted_ids[i]

        port1 = ports[id1]
        owner1 = owner_map.get(id1)
        point1 = port_points[id1]

        for j in range(
            i + 1,
            len(sorted_ids),
        ):

            id2 = sorted_ids[j]

            port2 = ports[id2]
            owner2 = owner_map.get(id2)
            point2 = port_points[id2]

            distance_raw = distance_3d(
                point1,
                point2,
            )

            distance_m = (
                distance_raw
                * unit_scale
            )

            distance_mm = (
                distance_m
                * 1000.0
            )

            same_owner = (
                owner1 is not None
                and
                owner2 is not None
                and
                owner1.id()
                == owner2.id()
            )

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

            #
            # Simple descriptive distance band.
            # This is NOT a connectivity decision.
            #
            if distance_mm <= 1.0:
                distance_band = "<=1mm"

            elif distance_mm <= 10.0:
                distance_band = "<=10mm"

            elif distance_mm <= 50.0:
                distance_band = "<=50mm"

            elif distance_mm <= 100.0:
                distance_band = "<=100mm"

            elif distance_mm <= 500.0:
                distance_band = "<=500mm"

            else:
                distance_band = ">500mm"

            distance_rows.append(
                {
                    "port1_step_id": id1,
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
                    "owner1_class": owner1_class,
                    "owner1_name": owner1_name,
                    "port2_step_id": id2,
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
                    "owner2_class": owner2_class,
                    "owner2_name": owner2_name,
                    "same_owner": (
                        "TRUE"
                        if same_owner
                        else "FALSE"
                    ),
                    "distance_project_unit": (
                        distance_raw
                    ),
                    "distance_m": distance_m,
                    "distance_mm": distance_mm,
                    "distance_band": distance_band,
                }
            )

    #
    # Sort by distance so nearest candidates
    # appear first.
    #
    distance_rows.sort(
        key=lambda row: row[
            "distance_mm"
        ]
    )

    for row in distance_rows:

        same_owner_mark = (
            "SAME"
            if row["same_owner"]
            == "TRUE"
            else "    "
        )

        print(
            f"{row['distance_mm']:12.3f} mm | "
            f"{row['distance_band']:7s} | "
            f"{same_owner_mark:4s} | "
            f"#{row['port1_step_id']} "
            f"{row['owner1_class']} "
            f"<-> "
            f"#{row['port2_step_id']} "
            f"{row['owner2_class']}"
        )

    print()

    #
    # Cross-owner candidates only.
    #
    cross_owner_rows = [
        row
        for row in distance_rows
        if row["same_owner"]
        == "FALSE"
    ]

    print(
        "=== NEAREST CROSS-OWNER PORT PAIRS ==="
    )
    print()

    for row in cross_owner_rows[:20]:

        print(
            f"{row['distance_mm']:12.3f} mm | "
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
    # CSV output
    #
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    port_fields = [
        "port_step_id",
        "port_global_id",
        "port_name",
        "flow_direction",
        "formal_system_member",
        "owner_step_id",
        "owner_global_id",
        "owner_class",
        "owner_name",
        "x_project_unit",
        "y_project_unit",
        "z_project_unit",
        "x_m",
        "y_m",
        "z_m",
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=port_fields,
        )

        writer.writeheader()
        writer.writerows(
            port_rows
        )

    distance_fields = [
        "port1_step_id",
        "port1_name",
        "port1_flow_direction",
        "owner1_step_id",
        "owner1_class",
        "owner1_name",
        "port2_step_id",
        "port2_name",
        "port2_flow_direction",
        "owner2_step_id",
        "owner2_class",
        "owner2_name",
        "same_owner",
        "distance_project_unit",
        "distance_m",
        "distance_mm",
        "distance_band",
    ]

    with DISTANCE_OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=distance_fields,
        )

        writer.writeheader()
        writer.writerows(
            distance_rows
        )

    print()
    print("=== RESULT ===")
    print()

    print(
        f"System elements     : "
        f"{len(system_elements)}"
    )

    print(
        f"Formal system ports : "
        f"{len(formal_system_port_ids)}"
    )

    print(
        f"Nested ports        : "
        f"{len(ports)}"
    )

    print(
        f"Ports with placement: "
        f"{len(port_points)}"
    )

    print(
        f"Port pairs          : "
        f"{len(distance_rows)}"
    )

    print(
        f"Cross-owner pairs   : "
        f"{len(cross_owner_rows)}"
    )

    if cross_owner_rows:

        nearest = cross_owner_rows[0]

        print()

        print(
            "Nearest cross-owner : "
            f"{nearest['distance_mm']:.3f} mm"
        )

        print(
            f"  #{nearest['port1_step_id']} "
            f"{nearest['owner1_class']}"
        )

        print(
            f"  #{nearest['port2_step_id']} "
            f"{nearest['owner2_class']}"
        )

    print()
    print(
        f"Port CSV     : "
        f"{OUTPUT_FILE}"
    )

    print(
        f"Distance CSV : "
        f"{DISTANCE_OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()