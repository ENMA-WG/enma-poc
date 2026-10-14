from collections import defaultdict
from pathlib import Path
import csv
import math

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit


IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")
OUTPUT_FILE = Path("output/nonzero_port_connections.csv")

# Existing explicit connections farther apart than this
# are investigated.  This is an analysis threshold,
# NOT a connectivity rule.
MIN_DISTANCE_MM = 10.0


def safe_value(obj, attr):
    if obj is None:
        return ""

    value = getattr(obj, attr, None)

    if value is None:
        return ""

    return str(value)


def get_port_owner_map(model):
    """
    Map:
        IfcDistributionPort STEP id -> owning IFC element
    """
    owners = {}

    for rel in model.by_type("IfcRelNests"):
        owner = getattr(rel, "RelatingObject", None)

        if owner is None:
            continue

        for obj in getattr(rel, "RelatedObjects", []) or []:
            if obj.is_a("IfcDistributionPort"):
                owners[obj.id()] = owner

    return owners


def get_object_system_map(model):
    """
    Map an IFC object STEP id to its IfcDistributionSystem(s).

    Both elements and ports may be assigned to systems,
    depending on the exporter.
    """
    object_systems = defaultdict(list)

    for system in model.by_type("IfcDistributionSystem"):
        for rel in getattr(system, "IsGroupedBy", []) or []:
            for obj in getattr(rel, "RelatedObjects", []) or []:
                object_systems[obj.id()].append(system)

    return object_systems


def get_connection_systems(
    port1,
    port2,
    owner1,
    owner2,
    object_systems,
):
    systems = {}

    for obj in (port1, port2, owner1, owner2):
        if obj is None:
            continue

        for system in object_systems.get(obj.id(), []):
            systems[system.id()] = system

    return list(systems.values())


def get_port_xyz(port):
    """
    Return port placement origin in project coordinates.

    Values are returned in project length units.
    """
    placement = getattr(port, "ObjectPlacement", None)

    if placement is None:
        return None

    matrix = ifcopenshell.util.placement.get_local_placement(
        placement
    )

    return (
        float(matrix[0][3]),
        float(matrix[1][3]),
        float(matrix[2][3]),
    )


def distance_3d(point1, point2):
    return math.sqrt(
        (point1[0] - point2[0]) ** 2
        + (point1[1] - point2[1]) ** 2
        + (point1[2] - point2[2]) ** 2
    )


def get_world_bbox(element, geom_settings):
    """
    Return world-coordinate geometry bounding box:

        xmin, ymin, zmin,
        xmax, ymax, zmax
    """
    if element is None:
        return None

    try:
        shape = ifcopenshell.geom.create_shape(
            geom_settings,
            element,
        )
    except Exception:
        return None

    verts = shape.geometry.verts

    if not verts:
        return None

    xs = verts[0::3]
    ys = verts[1::3]
    zs = verts[2::3]

    return (
        min(xs),
        min(ys),
        min(zs),
        max(xs),
        max(ys),
        max(zs),
    )


def bbox_dimensions(bbox):
    if bbox is None:
        return None

    return (
        bbox[3] - bbox[0],
        bbox[4] - bbox[1],
        bbox[5] - bbox[2],
    )


def axis_gap(min1, max1, min2, max2):
    """
    Distance between two 1D intervals.

    0 means the intervals overlap or touch.
    """
    if max1 < min2:
        return min2 - max1

    if max2 < min1:
        return min1 - max2

    return 0.0


def bbox_gaps(bbox1, bbox2):
    """
    Return X/Y/Z gaps between two bounding boxes.
    """
    if bbox1 is None or bbox2 is None:
        return None

    gap_x = axis_gap(
        bbox1[0], bbox1[3],
        bbox2[0], bbox2[3],
    )

    gap_y = axis_gap(
        bbox1[1], bbox1[4],
        bbox2[1], bbox2[4],
    )

    gap_z = axis_gap(
        bbox1[2], bbox1[5],
        bbox2[2], bbox2[5],
    )

    return gap_x, gap_y, gap_z


def bbox_distance(gaps):
    """
    Euclidean distance between two AABBs.

    0 means the bounding boxes overlap or touch.
    """
    if gaps is None:
        return None

    return math.sqrt(
        gaps[0] ** 2
        + gaps[1] ** 2
        + gaps[2] ** 2
    )


def mm(value_m):
    if value_m is None:
        return ""

    return value_m * 1000.0


def rounded(value, digits=3):
    if value == "":
        return ""

    if value is None:
        return ""

    return round(value, digits)


def main():
    print("=== NONZERO PORT CONNECTION ANALYSIS ===")
    print()
    print(f"IFC    : {IFC_FILE}")
    print(f"Output : {OUTPUT_FILE}")
    print(
        f"Filter : explicit port distance "
        f"> {MIN_DISTANCE_MM:.1f} mm"
    )
    print()

    model = ifcopenshell.open(str(IFC_FILE))

    unit_scale = ifcopenshell.util.unit.calculate_unit_scale(
        model
    )

    port_owners = get_port_owner_map(model)
    object_systems = get_object_system_map(model)

    geom_settings = ifcopenshell.geom.settings()
    geom_settings.set(
        geom_settings.USE_WORLD_COORDS,
        True,
    )

    rows = []

    bbox_cache = {}

    connections = model.by_type(
        "IfcRelConnectsPorts"
    )

    for rel in connections:
        port1 = getattr(rel, "RelatingPort", None)
        port2 = getattr(rel, "RelatedPort", None)

        if port1 is None or port2 is None:
            continue

        xyz1 = get_port_xyz(port1)
        xyz2 = get_port_xyz(port2)

        if xyz1 is None or xyz2 is None:
            continue

        distance_project = distance_3d(
            xyz1,
            xyz2,
        )

        distance_m = distance_project * unit_scale
        distance_mm = distance_m * 1000.0

        if distance_mm <= MIN_DISTANCE_MM:
            continue

        owner1 = port_owners.get(port1.id())
        owner2 = port_owners.get(port2.id())

        if owner1 is None or owner2 is None:
            continue

        for owner in (owner1, owner2):
            if owner.id() not in bbox_cache:
                bbox_cache[owner.id()] = get_world_bbox(
                    owner,
                    geom_settings,
                )

        bbox1 = bbox_cache[owner1.id()]
        bbox2 = bbox_cache[owner2.id()]

        dims1 = bbox_dimensions(bbox1)
        dims2 = bbox_dimensions(bbox2)

        gaps = bbox_gaps(bbox1, bbox2)
        geom_distance = bbox_distance(gaps)

        systems = get_connection_systems(
            port1,
            port2,
            owner1,
            owner2,
            object_systems,
        )

        system_names = sorted(
            {
                safe_value(system, "Name")
                for system in systems
                if safe_value(system, "Name")
            }
        )

        system_types = sorted(
            {
                safe_value(system, "ObjectType")
                for system in systems
                if safe_value(system, "ObjectType")
            }
        )

        bbox_overlap = (
            gaps is not None
            and gaps[0] == 0.0
            and gaps[1] == 0.0
            and gaps[2] == 0.0
        )

        row = {
            "relationship_step_id": rel.id(),
            "relationship_global_id":
                safe_value(rel, "GlobalId"),

            "port1_step_id": port1.id(),
            "port1_global_id":
                safe_value(port1, "GlobalId"),
            "port1_name":
                safe_value(port1, "Name"),
            "port1_flow_direction":
                safe_value(port1, "FlowDirection"),

            "owner1_step_id": owner1.id(),
            "owner1_global_id":
                safe_value(owner1, "GlobalId"),
            "owner1_class": owner1.is_a(),
            "owner1_name":
                safe_value(owner1, "Name"),

            "port2_step_id": port2.id(),
            "port2_global_id":
                safe_value(port2, "GlobalId"),
            "port2_name":
                safe_value(port2, "Name"),
            "port2_flow_direction":
                safe_value(port2, "FlowDirection"),

            "owner2_step_id": owner2.id(),
            "owner2_global_id":
                safe_value(owner2, "GlobalId"),
            "owner2_class": owner2.is_a(),
            "owner2_name":
                safe_value(owner2, "Name"),

            "system_names":
                " | ".join(system_names),
            "system_object_types":
                " | ".join(system_types),

            "port_distance_mm":
                rounded(distance_mm, 6),

            "port1_x_m":
                rounded(xyz1[0] * unit_scale, 6),
            "port1_y_m":
                rounded(xyz1[1] * unit_scale, 6),
            "port1_z_m":
                rounded(xyz1[2] * unit_scale, 6),

            "port2_x_m":
                rounded(xyz2[0] * unit_scale, 6),
            "port2_y_m":
                rounded(xyz2[1] * unit_scale, 6),
            "port2_z_m":
                rounded(xyz2[2] * unit_scale, 6),

            "owner1_bbox_x_mm":
                rounded(mm(dims1[0]), 3)
                if dims1 else "",
            "owner1_bbox_y_mm":
                rounded(mm(dims1[1]), 3)
                if dims1 else "",
            "owner1_bbox_z_mm":
                rounded(mm(dims1[2]), 3)
                if dims1 else "",

            "owner2_bbox_x_mm":
                rounded(mm(dims2[0]), 3)
                if dims2 else "",
            "owner2_bbox_y_mm":
                rounded(mm(dims2[1]), 3)
                if dims2 else "",
            "owner2_bbox_z_mm":
                rounded(mm(dims2[2]), 3)
                if dims2 else "",

            "bbox_gap_x_mm":
                rounded(mm(gaps[0]), 3)
                if gaps else "",
            "bbox_gap_y_mm":
                rounded(mm(gaps[1]), 3)
                if gaps else "",
            "bbox_gap_z_mm":
                rounded(mm(gaps[2]), 3)
                if gaps else "",

            "bbox_distance_mm":
                rounded(mm(geom_distance), 3)
                if geom_distance is not None
                else "",

            "bbox_overlap":
                "TRUE" if bbox_overlap else "FALSE",
        }

        rows.append(row)

    rows.sort(
        key=lambda row: float(
            row["port_distance_mm"]
        )
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if rows:
        with OUTPUT_FILE.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=list(rows[0].keys()),
            )

            writer.writeheader()
            writer.writerows(rows)

    print("=== RESULT ===")
    print()
    print(
        f"Explicit connections total : "
        f"{len(connections)}"
    )
    print(
        f"Connections > 10 mm        : "
        f"{len(rows)}"
    )

    overlap_count = sum(
        1
        for row in rows
        if row["bbox_overlap"] == "TRUE"
    )

    separated_count = sum(
        1
        for row in rows
        if row["bbox_overlap"] == "FALSE"
    )

    print(
        f"BBOX overlap/touch         : "
        f"{overlap_count}"
    )
    print(
        f"BBOX separated             : "
        f"{separated_count}"
    )
    print()

    print("=== CONNECTIONS ===")
    print()

    for row in rows:
        print(
            f"Rel #{row['relationship_step_id']:>6} | "
            f"Port={row['port_distance_mm']:>10} mm | "
            f"BBOX={row['bbox_distance_mm']:>8} mm | "
            f"Overlap={row['bbox_overlap']:5s} | "
            f"{row['owner1_class']} <-> "
            f"{row['owner2_class']} | "
            f"{row['system_names']}"
        )

    print()
    print(f"CSV written: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
