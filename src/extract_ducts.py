"""
ENMA-WG PoC - Duct Geometry Extraction

Extract duct dimensions, quantities, and air-system information from
IfcDuctSegment elements, and cross-check geometry-derived values against
IFC QTO values.

System extraction:
    IfcDuctSegment
      -> IfcRelAssignsToGroup
      -> IfcDistributionSystem

    The raw IFC system Name and ObjectType are preserved. For the current
    MLIT test IFC, ObjectType is also mapped to an ENMA air type:
        101_SA給気 -> SA
        102_RA還気 -> RA
        103_OA外気 -> OA
        105_EA排気 -> EA

    This keeps the IFC source value separate from the engineering
    interpretation. No inference from duct Name or ObjectType is required
    when an IfcDistributionSystem assignment is available.

Current target dataset:
    MLIT BIM model (Japan)
    data/営繕BIMモデル_EM.ifc

Geometry extraction:
    IfcDuctSegment
      -> IfcExtrudedAreaSolid
      -> IfcArbitraryClosedProfileDef
      -> IfcIndexedPolyCurve

Extracted geometry:
    - Shape (ROUND / RECTANGULAR)
    - Diameter or Width / Height
    - Extrusion length
    - Cross-sectional area

Validation:
    Geometry-derived length and area are compared with
    Qto_DuctSegmentBaseQuantities.

Important:
    Geometry dimensions are preserved as raw IFC geometry values.
    They are NOT converted to nominal duct sizes.

    A strict area tolerance of 0.01% is intentionally used.
    In the current MLIT test IFC, round ducts show a consistent
    difference of approximately 0.015038% between geometry-derived
    circular area and QTO GrossCrossSectionArea. This difference is
    retained as a validation result rather than hidden by relaxing
    the tolerance.

Current validation result for the target IFC:
    - IfcDuctSegment: 1077
    - ROUND: 792
    - RECTANGULAR: 285
    - System assignment: 1077 / 1077
    - SA: 512
    - RA: 4
    - OA: 112
    - EA: 449

Output:
    output/ducts_detail.csv

CSV encoding:
    UTF-8 with BOM (utf-8-sig) for compatibility with common
    spreadsheet applications.

Project:
    ENMA-WG
    Automated MEP Quantity Takeoff PoC
"""

import csv
import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element as element


IFC_FILE = Path(r"data/営繕BIMモデル_EM.ifc")
OUTPUT_FILE = Path(r"output/ducts_detail.csv")

# Validation tolerances.
#
# The area tolerance is intentionally strict.
# In the current MLIT test IFC, round ducts show a consistent
# difference of approximately 0.015038% between geometry-derived
# circular area and QTO GrossCrossSectionArea.
#
# The tolerance is NOT relaxed to hide this difference.
TOLERANCE_LENGTH_MM = 0.01
TOLERANCE_AREA_PERCENT = 0.01


def get_qto(duct):
    """Get Qto_DuctSegmentBaseQuantities."""
    psets = element.get_psets(duct)
    return psets.get("Qto_DuctSegmentBaseQuantities", {})


def get_extruded_solid(duct):
    """
    Return the first IfcExtrudedAreaSolid found in the element
    representation.

    Current MLIT test IFC has exactly one extrusion per
    IfcDuctSegment, but this function deliberately does not assume
    that all future IFC files will have the same structure.
    """
    representation = getattr(duct, "Representation", None)

    if not representation:
        return None

    for rep in representation.Representations:
        for item in rep.Items:
            if item.is_a("IfcExtrudedAreaSolid"):
                return item

    return None


def get_profile_coordinates(solid):
    """
    Extract 2D coordinates from:

        IfcExtrudedAreaSolid
          -> IfcArbitraryClosedProfileDef
          -> IfcIndexedPolyCurve
          -> IfcCartesianPointList2D

    Returns:
        coordinates, profile_type, curve_type
    """
    if solid is None:
        return None, None, None

    profile = getattr(solid, "SweptArea", None)

    if profile is None:
        return None, None, None

    profile_type = profile.is_a()

    if not profile.is_a("IfcArbitraryClosedProfileDef"):
        return None, profile_type, None

    curve = getattr(profile, "OuterCurve", None)

    if curve is None:
        return None, profile_type, None

    curve_type = curve.is_a()

    if not curve.is_a("IfcIndexedPolyCurve"):
        return None, profile_type, curve_type

    points = getattr(curve, "Points", None)

    if points is None:
        return None, profile_type, curve_type

    if not points.is_a("IfcCartesianPointList2D"):
        return None, profile_type, curve_type

    coordinates = [
        (float(p[0]), float(p[1]))
        for p in points.CoordList
    ]

    return coordinates, profile_type, curve_type


def classify_shape(duct, curve):
    """
    Classify duct shape.

    Primary method:
        Arc segments -> ROUND
        No arc segments -> RECTANGULAR

    Fallback:
        Japanese ObjectType / Name
    """
    if curve is not None and curve.is_a("IfcIndexedPolyCurve"):
        segments = getattr(curve, "Segments", None)

        if segments:
            if any(
                segment.is_a("IfcArcIndex")
                for segment in segments
            ):
                return "ROUND"

            return "RECTANGULAR"

        # In the current MLIT IFC, rectangular profiles have
        # Segments = None.
        return "RECTANGULAR"

    text = (
        (getattr(duct, "ObjectType", None) or "")
        + " "
        + (getattr(duct, "Name", None) or "")
    )

    if "丸" in text:
        return "ROUND"

    if "角" in text:
        return "RECTANGULAR"

    return "UNKNOWN"


def get_curve_from_solid(solid):
    """Return the profile OuterCurve from an extrusion solid."""
    if solid is None:
        return None

    profile = getattr(solid, "SweptArea", None)

    if profile is None:
        return None

    return getattr(profile, "OuterCurve", None)


def calculate_round_dimension(coordinates):
    """
    Determine diameter from radial distances of profile points.

    The current IFC represents a circular duct profile using
    four IfcArcIndex arcs.
    """
    if not coordinates:
        return None

    radii = [
        math.hypot(x, y)
        for x, y in coordinates
    ]

    if not radii:
        return None

    radius = sum(radii) / len(radii)

    return radius * 2.0


def calculate_rect_dimensions(coordinates):
    """
    Determine rectangular dimensions from local 2D profile coordinates.

    This uses the local profile coordinate system, not the world-space
    bounding box.

    The larger dimension is stored as Width and the smaller dimension
    as Height. Values are preserved from the IFC geometry and are not
    converted to nominal duct sizes.
    """
    if not coordinates:
        return None, None

    xs = [p[0] for p in coordinates]
    ys = [p[1] for p in coordinates]

    x_dim = max(xs) - min(xs)
    y_dim = max(ys) - min(ys)

    width = max(x_dim, y_dim)
    height = min(x_dim, y_dim)

    return width, height


def calculate_geometry_area(
    shape,
    diameter_mm,
    width_mm,
    height_mm,
):
    """
    Calculate cross-sectional area from extracted geometry.

    ROUND:
        pi * D^2 / 4

    RECTANGULAR:
        Width * Height
    """
    if shape == "ROUND" and diameter_mm is not None:
        diameter_m = diameter_mm / 1000.0
        return math.pi * diameter_m**2 / 4.0

    if (
        shape == "RECTANGULAR"
        and width_mm is not None
        and height_mm is not None
    ):
        return (
            (width_mm / 1000.0)
            * (height_mm / 1000.0)
        )

    return None


def percent_difference(value_a, value_b):
    """
    Calculate absolute percentage difference relative to value_b.
    """
    if value_a is None or value_b is None:
        return None

    if abs(value_b) < 1e-15:
        return None

    return abs(value_a - value_b) / abs(value_b) * 100.0


def get_storey_name(duct):
    """
    Try to obtain the containing IfcBuildingStorey.
    """
    try:
        container = element.get_container(duct)

        while container is not None:
            if container.is_a("IfcBuildingStorey"):
                return container.Name or ""

            container = element.get_container(container)

    except Exception:
        pass

    return ""



# ENMA interpretation of the raw IfcDistributionSystem.ObjectType.
#
# The raw IFC value is also written to the CSV, so source information
# remains separate from ENMA's engineering interpretation.
AIR_TYPE_MAP = {
    "101_SA給気": "SA",
    "102_RA還気": "RA",
    "103_OA外気": "OA",
    "105_EA排気": "EA",
}


def get_distribution_systems(duct):
    """
    Return IfcDistributionSystem objects directly assigned to a duct via:

        IfcDuctSegment
          -> IfcRelAssignsToGroup
          -> IfcDistributionSystem

    No inference from element names or connectivity is performed here.
    """
    systems = []

    for assignment in getattr(duct, "HasAssignments", []) or []:
        if not assignment.is_a("IfcRelAssignsToGroup"):
            continue

        group = getattr(assignment, "RelatingGroup", None)

        if (
            group is not None
            and group.is_a("IfcDistributionSystem")
        ):
            systems.append(group)

    return systems


def interpret_air_type(system_object_type):
    """
    Map the raw IFC system ObjectType to an ENMA air type.

    An unmapped value is returned as UNKNOWN rather than guessed from
    names. This preserves the distinction between IFC source information
    and engineering interpretation.
    """
    if not system_object_type:
        return "UNKNOWN"

    return AIR_TYPE_MAP.get(system_object_type, "UNKNOWN")


def main():
    print("=== ENMA DUCT EXTRACTION ===")
    print()

    print(f"IFC    : {IFC_FILE}")
    print(f"Output : {OUTPUT_FILE}")
    print()

    model = ifcopenshell.open(str(IFC_FILE))
    ducts = model.by_type("IfcDuctSegment")

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows = []

    shape_counts = {
        "ROUND": 0,
        "RECTANGULAR": 0,
        "UNKNOWN": 0,
    }

    geometry_ok = 0
    geometry_error = 0

    length_match_count = 0
    area_match_count = 0

    area_checked_by_shape = {
        "ROUND": 0,
        "RECTANGULAR": 0,
    }

    area_match_by_shape = {
        "ROUND": 0,
        "RECTANGULAR": 0,
    }

    air_type_counts = {
        "SA": 0,
        "RA": 0,
        "OA": 0,
        "EA": 0,
        "UNKNOWN": 0,
    }

    system_single_count = 0
    system_missing_count = 0
    system_multiple_count = 0

    for duct in ducts:

        # --------------------------------------------------
        # IFC / QTO
        # --------------------------------------------------

        qto = get_qto(duct)

        qto_length_mm = qto.get("Length")
        qto_area_m2 = qto.get(
            "GrossCrossSectionArea"
        )
        qto_net_area_m2 = qto.get(
            "NetCrossSectionArea"
        )
        qto_outer_surface_m2 = qto.get(
            "OuterSurfaceArea"
        )

        # --------------------------------------------------
        # Distribution system / air type
        # --------------------------------------------------

        systems = get_distribution_systems(duct)

        system_name = ""
        system_object_type = ""
        air_type = "UNKNOWN"
        system_source = ""

        if len(systems) == 1:
            system = systems[0]
            system_name = system.Name or ""
            system_object_type = system.ObjectType or ""
            air_type = interpret_air_type(system_object_type)
            system_source = "IFC_DISTRIBUTION_SYSTEM"
            system_single_count += 1

        elif len(systems) == 0:
            system_source = "NOT_ASSIGNED"
            system_missing_count += 1

        else:
            system_name = " | ".join(
                (system.Name or "")
                for system in systems
            )
            system_object_type = " | ".join(
                (system.ObjectType or "")
                for system in systems
            )
            system_source = "MULTIPLE_IFC_DISTRIBUTION_SYSTEMS"
            system_multiple_count += 1

        if air_type not in air_type_counts:
            air_type_counts[air_type] = 0

        air_type_counts[air_type] += 1

        # --------------------------------------------------
        # Geometry
        # --------------------------------------------------

        solid = get_extruded_solid(duct)

        profile_type = ""
        curve_type = ""

        if solid is not None:
            geometry_length_mm = float(solid.Depth)
        else:
            geometry_length_mm = None

        coordinates, profile_type, curve_type = (
            get_profile_coordinates(solid)
        )

        curve = get_curve_from_solid(solid)

        shape = classify_shape(duct, curve)

        if shape not in shape_counts:
            shape_counts[shape] = 0

        shape_counts[shape] += 1

        diameter_mm = None
        width_mm = None
        height_mm = None

        if shape == "ROUND":
            diameter_mm = calculate_round_dimension(
                coordinates
            )

        elif shape == "RECTANGULAR":
            width_mm, height_mm = (
                calculate_rect_dimensions(
                    coordinates
                )
            )

        # --------------------------------------------------
        # Geometry area
        # --------------------------------------------------

        geometry_area_m2 = calculate_geometry_area(
            shape,
            diameter_mm,
            width_mm,
            height_mm,
        )

        # --------------------------------------------------
        # Validation
        # --------------------------------------------------

        length_difference_mm = None
        area_difference_pct = None

        length_match = ""
        area_match = ""

        if (
            geometry_length_mm is not None
            and qto_length_mm is not None
        ):
            length_difference_mm = abs(
                geometry_length_mm
                - float(qto_length_mm)
            )

            length_match = (
                length_difference_mm
                <= TOLERANCE_LENGTH_MM
            )

            if length_match:
                length_match_count += 1

        if (
            geometry_area_m2 is not None
            and qto_area_m2 is not None
        ):
            area_difference_pct = percent_difference(
                geometry_area_m2,
                float(qto_area_m2),
            )

            if area_difference_pct is not None:
                area_match = (
                    area_difference_pct
                    <= TOLERANCE_AREA_PERCENT
                )

                if shape in area_checked_by_shape:
                    area_checked_by_shape[shape] += 1

                if area_match:
                    area_match_count += 1

                    if shape in area_match_by_shape:
                        area_match_by_shape[shape] += 1

        # --------------------------------------------------
        # Extraction status
        # --------------------------------------------------

        if (
            shape != "UNKNOWN"
            and geometry_length_mm is not None
            and geometry_area_m2 is not None
        ):
            geometry_status = "OK"
            geometry_ok += 1

        else:
            geometry_status = "REVIEW"
            geometry_error += 1

        # --------------------------------------------------
        # Row
        # --------------------------------------------------

        rows.append(
            {
                "GlobalId": duct.GlobalId,
                "Name": duct.Name or "",
                "ObjectType": duct.ObjectType or "",
                "Storey": get_storey_name(duct),

                "SystemName": system_name,
                "SystemObjectType": system_object_type,
                "AirType": air_type,
                "SystemSource": system_source,

                "Shape": shape,

                "Diameter_mm": (
                    round(diameter_mm, 3)
                    if diameter_mm is not None
                    else ""
                ),

                "Width_mm": (
                    round(width_mm, 3)
                    if width_mm is not None
                    else ""
                ),

                "Height_mm": (
                    round(height_mm, 3)
                    if height_mm is not None
                    else ""
                ),

                "Geometry_Length_mm": (
                    round(geometry_length_mm, 3)
                    if geometry_length_mm is not None
                    else ""
                ),

                "QTO_Length_mm": (
                    round(float(qto_length_mm), 3)
                    if qto_length_mm is not None
                    else ""
                ),

                "Geometry_Area_m2": (
                    round(geometry_area_m2, 9)
                    if geometry_area_m2 is not None
                    else ""
                ),

                "QTO_GrossArea_m2": (
                    round(float(qto_area_m2), 9)
                    if qto_area_m2 is not None
                    else ""
                ),

                "QTO_NetArea_m2": (
                    round(float(qto_net_area_m2), 9)
                    if qto_net_area_m2 is not None
                    else ""
                ),

                "QTO_OuterSurfaceArea_m2": (
                    round(
                        float(qto_outer_surface_m2),
                        9,
                    )
                    if qto_outer_surface_m2 is not None
                    else ""
                ),

                "Length_Difference_mm": (
                    round(length_difference_mm, 6)
                    if length_difference_mm is not None
                    else ""
                ),

                "Length_Match": length_match,

                "Area_Difference_pct": (
                    round(area_difference_pct, 6)
                    if area_difference_pct is not None
                    else ""
                ),

                "Area_Match": area_match,

                "ProfileType": profile_type or "",
                "CurveType": curve_type or "",

                "DimensionSource": "IFC_GEOMETRY",

                "GeometryStatus": geometry_status,
            }
        )

    # --------------------------------------------------
    # CSV
    # --------------------------------------------------

    fieldnames = [
        "GlobalId",
        "Name",
        "ObjectType",
        "Storey",
        "SystemName",
        "SystemObjectType",
        "AirType",
        "SystemSource",
        "Shape",
        "Diameter_mm",
        "Width_mm",
        "Height_mm",
        "Geometry_Length_mm",
        "QTO_Length_mm",
        "Geometry_Area_m2",
        "QTO_GrossArea_m2",
        "QTO_NetArea_m2",
        "QTO_OuterSurfaceArea_m2",
        "Length_Difference_mm",
        "Length_Match",
        "Area_Difference_pct",
        "Area_Match",
        "ProfileType",
        "CurveType",
        "DimensionSource",
        "GeometryStatus",
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

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    print("=== RESULT ===")

    print(
        f"IfcDuctSegment       : {len(ducts)}"
    )

    print(
        f"ROUND                : "
        f"{shape_counts.get('ROUND', 0)}"
    )

    print(
        f"RECTANGULAR          : "
        f"{shape_counts.get('RECTANGULAR', 0)}"
    )

    print(
        f"UNKNOWN              : "
        f"{shape_counts.get('UNKNOWN', 0)}"
    )

    print()

    print("Air system")
    print(f"  SA                  : {air_type_counts.get('SA', 0)}")
    print(f"  RA                  : {air_type_counts.get('RA', 0)}")
    print(f"  OA                  : {air_type_counts.get('OA', 0)}")
    print(f"  EA                  : {air_type_counts.get('EA', 0)}")
    print(f"  UNKNOWN             : {air_type_counts.get('UNKNOWN', 0)}")

    print()

    print("System assignment")
    print(f"  Single system       : {system_single_count}")
    print(f"  No system           : {system_missing_count}")
    print(f"  Multiple systems    : {system_multiple_count}")

    print()

    print(
        f"Geometry OK          : {geometry_ok}"
    )

    print(
        f"Geometry REVIEW      : {geometry_error}"
    )

    print()

    print(
        f"Length match         : "
        f"{length_match_count}/{len(ducts)}"
    )

    print(
        f"Area match (all)     : "
        f"{area_match_count}/{len(ducts)}"
    )

    print(
        f"  ROUND              : "
        f"{area_match_by_shape['ROUND']}/"
        f"{area_checked_by_shape['ROUND']}"
    )

    print(
        f"  RECTANGULAR        : "
        f"{area_match_by_shape['RECTANGULAR']}/"
        f"{area_checked_by_shape['RECTANGULAR']}"
    )

    print()

    print(
        f"CSV written          : {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()