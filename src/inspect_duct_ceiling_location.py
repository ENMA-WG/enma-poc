"""
inspect_duct_ceiling_location.py

ENMA-WG PoC
Inspect spatial relationships between IfcDuctSegment,
IfcSpace and ceiling-like IfcCovering elements.

V3 policy:
- Preserve observed / geometrically derived evidence.
- Prefer same-storey ceiling candidates.
- Do not use XY fallback as construction-location evidence.
- Output preliminary construction-location candidates.
- Do NOT decide final "concealed" / "exposed" yet.
- Keep ambiguous and unresolved cases visible.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom


# ----------------------------------------------------------------------
# Utility
# ----------------------------------------------------------------------

def safe_text(value) -> str:
    if value is None:
        return ""
    return str(value)


def entity_label(entity) -> str:
    name = safe_text(getattr(entity, "Name", None))
    objtype = safe_text(getattr(entity, "ObjectType", None))

    if name and objtype:
        return f"{name} / {objtype}"
    return name or objtype


def get_storey(element):
    """
    Find containing IfcBuildingStorey through spatial containment.
    """
    try:
        for rel in getattr(element, "ContainedInStructure", []) or []:
            structure = getattr(rel, "RelatingStructure", None)
            if structure and structure.is_a("IfcBuildingStorey"):
                return structure
    except Exception:
        pass

    return None


def get_storey_name(element) -> str:
    storey = get_storey(element)
    if storey is None:
        return ""
    return safe_text(getattr(storey, "Name", None))


# ----------------------------------------------------------------------
# Geometry
# ----------------------------------------------------------------------

def make_geom_settings():
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    return settings


def get_vertices(entity, settings):
    """
    Return [(x,y,z), ...] in model length coordinates converted by
    IfcOpenShell geometry engine (normally SI metres with world coords).
    """
    try:
        shape = ifcopenshell.geom.create_shape(settings, entity)
        verts = shape.geometry.verts

        return [
            (float(verts[i]), float(verts[i + 1]), float(verts[i + 2]))
            for i in range(0, len(verts), 3)
        ]

    except Exception:
        return []


def bbox_from_vertices(vertices):
    if not vertices:
        return None

    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    zs = [v[2] for v in vertices]

    return {
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
        "min_z": min(zs),
        "max_z": max(zs),
    }


def bbox_center(bbox):
    return (
        (bbox["min_x"] + bbox["max_x"]) / 2.0,
        (bbox["min_y"] + bbox["max_y"]) / 2.0,
        (bbox["min_z"] + bbox["max_z"]) / 2.0,
    )


def xy_contains(bbox, x, y, tolerance=0.01):
    return (
        bbox["min_x"] - tolerance <= x <= bbox["max_x"] + tolerance
        and bbox["min_y"] - tolerance <= y <= bbox["max_y"] + tolerance
    )


def z_contains(bbox, z, tolerance=0.01):
    return bbox["min_z"] - tolerance <= z <= bbox["max_z"] + tolerance


def xy_bbox_overlap(a, b, tolerance=0.01):
    return not (
        a["max_x"] < b["min_x"] - tolerance
        or a["min_x"] > b["max_x"] + tolerance
        or a["max_y"] < b["min_y"] - tolerance
        or a["min_y"] > b["max_y"] + tolerance
    )


def xy_overlap_area(a, b):
    dx = max(
        0.0,
        min(a["max_x"], b["max_x"]) - max(a["min_x"], b["min_x"]),
    )
    dy = max(
        0.0,
        min(a["max_y"], b["max_y"]) - max(a["min_y"], b["min_y"]),
    )
    return dx * dy


# ----------------------------------------------------------------------
# Ceiling identification
# ----------------------------------------------------------------------

def is_ceiling_covering(entity) -> bool:
    """
    Conservative V1 ceiling identification.

    IFC4 IfcCovering may have PredefinedType=CEILING.
    Also inspect Name/ObjectType as fallback.
    """
    predefined = safe_text(getattr(entity, "PredefinedType", None)).upper()

    if predefined == "CEILING":
        return True

    text = " ".join(
        [
            safe_text(getattr(entity, "Name", None)),
            safe_text(getattr(entity, "ObjectType", None)),
            safe_text(getattr(entity, "Description", None)),
        ]
    ).lower()

    keywords = [
        "ceiling",
        "decke",
        "天井",
    ]

    return any(keyword in text for keyword in keywords)


# ----------------------------------------------------------------------
# Inventory builders
# ----------------------------------------------------------------------

def build_space_inventory(model, settings):
    inventory = []

    for space in model.by_type("IfcSpace"):
        vertices = get_vertices(space, settings)
        bbox = bbox_from_vertices(vertices)

        if bbox is None:
            continue

        inventory.append(
            {
                "entity": space,
                "step_id": space.id(),
                "global_id": safe_text(getattr(space, "GlobalId", None)),
                "name": safe_text(getattr(space, "Name", None)),
                "long_name": safe_text(getattr(space, "LongName", None)),
                "storey": get_storey_name(space),
                "bbox": bbox,
            }
        )

    return inventory


def build_ceiling_inventory(model, settings):
    inventory = []

    for covering in model.by_type("IfcCovering"):
        if not is_ceiling_covering(covering):
            continue

        vertices = get_vertices(covering, settings)
        bbox = bbox_from_vertices(vertices)

        if bbox is None:
            continue

        inventory.append(
            {
                "entity": covering,
                "step_id": covering.id(),
                "global_id": safe_text(
                    getattr(covering, "GlobalId", None)
                ),
                "name": safe_text(getattr(covering, "Name", None)),
                "object_type": safe_text(
                    getattr(covering, "ObjectType", None)
                ),
                "storey": get_storey_name(covering),
                "bbox": bbox,
            }
        )

    return inventory


# ----------------------------------------------------------------------
# Candidate search
# ----------------------------------------------------------------------

def find_space_candidates(duct_bbox, spaces):
    cx, cy, cz = bbox_center(duct_bbox)

    candidates = []

    for item in spaces:
        bbox = item["bbox"]

        if not xy_contains(bbox, cx, cy):
            continue

        relation = ""

        if z_contains(bbox, cz):
            relation = "CENTER_INSIDE_AABB"

        elif cz > bbox["max_z"]:
            relation = "CENTER_ABOVE_SPACE_AABB"

        elif cz < bbox["min_z"]:
            relation = "CENTER_BELOW_SPACE_AABB"

        candidates.append(
            {
                **item,
                "relation": relation,
                "z_delta_to_space_top": cz - bbox["max_z"],
            }
        )

    return candidates


def choose_space_candidate(candidates):
    """
    V1 heuristic only.

    Preference:
      1. Center Z inside Space AABB
      2. If above spaces, nearest Space top below duct center

    Candidate count is always exported so ambiguity is not hidden.
    """
    if not candidates:
        return None

    inside = [
        c for c in candidates
        if c["relation"] == "CENTER_INSIDE_AABB"
    ]

    if inside:
        return min(
            inside,
            key=lambda c: abs(c["z_delta_to_space_top"]),
        )

    above = [
        c for c in candidates
        if c["relation"] == "CENTER_ABOVE_SPACE_AABB"
        and c["z_delta_to_space_top"] >= 0
    ]

    if above:
        return min(
            above,
            key=lambda c: c["z_delta_to_space_top"],
        )

    return candidates[0]


def find_ceiling_candidates(duct_bbox, duct_storey, ceilings):
    """
    V2:
    Find ceiling AABBs overlapping duct in XY.

    Priority / filtering:
    - If duct Storey is known, use ceilings on the SAME Storey.
    - If duct Storey is unknown, retain all XY-overlapping ceilings.
    - Do NOT infer CEILING_VOID yet.
    """
    cx, cy, cz = bbox_center(duct_bbox)

    xy_candidates = []

    for item in ceilings:
        bbox = item["bbox"]

        if not xy_bbox_overlap(duct_bbox, bbox):
            continue

        overlap_area = xy_overlap_area(
            duct_bbox,
            bbox,
        )

        ceiling_mid_z = (
            bbox["min_z"] + bbox["max_z"]
        ) / 2.0

        xy_candidates.append(
            {
                **item,
                "overlap_area": overlap_area,
                "ceiling_mid_z": ceiling_mid_z,
                "duct_center_to_ceiling_z": (
                    cz - ceiling_mid_z
                ),
            }
        )

    # --------------------------------------------------------------
    # V2: Prefer same-storey ceilings.
    # --------------------------------------------------------------

    if duct_storey:
        same_storey = [
            c for c in xy_candidates
            if c["storey"] == duct_storey
        ]

        if same_storey:
            return same_storey, "SAME_STOREY"

    # No same-storey ceiling candidate found.
    # Keep XY candidates for diagnostic purposes.
    return xy_candidates, "XY_FALLBACK"


def choose_ceiling_candidate(duct_bbox, candidates):
    """
    Prefer:
      - XY overlapping ceiling
      - nearest ceiling below duct center

    Still only a geometric candidate, not a semantic conclusion.
    """
    if not candidates:
        return None

    _, _, cz = bbox_center(duct_bbox)

    below = [
        c for c in candidates
        if c["ceiling_mid_z"] <= cz
    ]

    if below:
        return min(
            below,
            key=lambda c: (
                cz - c["ceiling_mid_z"],
                -c["overlap_area"],
            ),
        )

    return min(
        candidates,
        key=lambda c: abs(cz - c["ceiling_mid_z"]),
    )


def classify_ceiling_location(
    *,
    chosen_ceiling,
    ceiling_candidate_source,
    ceiling_relation,
):
    """
    V3 preliminary inference.

    Important:
    This is NOT the final construction-location decision.

    OBSERVED / DERIVED evidence:
      - Ceiling candidate exists
      - Ceiling candidate source
      - Duct / ceiling Z relationship

    INFERRED result:
      - CEILING_VOID_CANDIDATE
      - BELOW_CEILING_CANDIDATE
      - UNRESOLVED_CEILING
      - NO_CEILING_EVIDENCE
    """

    # --------------------------------------------------------------
    # No ceiling geometry was found at all.
    # --------------------------------------------------------------
    if chosen_ceiling is None:
        return (
            "NO_CEILING_EVIDENCE",
            "UNRESOLVED",
            "No ceiling candidate found",
        )

    # --------------------------------------------------------------
    # XY fallback means that no same-storey ceiling was found.
    #
    # Keep this as diagnostic evidence only.
    # Do NOT use another storey's ceiling for construction-location
    # inference.
    # --------------------------------------------------------------
    if ceiling_candidate_source != "SAME_STOREY":
        return (
            "UNRESOLVED_CEILING",
            "UNRESOLVED",
            "No same-storey ceiling candidate",
        )

    # --------------------------------------------------------------
    # Same-storey ceiling + duct center above ceiling
    #
    # Strong candidate for ceiling void, but V3 still does not call
    # this final "concealed".
    # --------------------------------------------------------------
    if ceiling_relation == "DUCT_CENTER_ABOVE_CEILING":
        return (
            "CEILING_VOID_CANDIDATE",
            "INFERRED_CANDIDATE",
            "Same-storey ceiling; duct center is above ceiling",
        )

    # --------------------------------------------------------------
    # Same-storey ceiling + duct center below ceiling
    #
    # Possible exposed duct, but we intentionally do not infer
    # EXPOSED yet.
    # --------------------------------------------------------------
    if ceiling_relation == "DUCT_CENTER_BELOW_CEILING":
        return (
            "BELOW_CEILING_CANDIDATE",
            "INFERRED_CANDIDATE",
            "Same-storey ceiling; duct center is below ceiling",
        )

    if ceiling_relation == "DUCT_CENTER_AT_CEILING":
        return (
            "AT_CEILING_CANDIDATE",
            "INFERRED_CANDIDATE",
            "Same-storey ceiling; duct center is at ceiling elevation",
        )

    return (
        "UNRESOLVED",
        "UNRESOLVED",
        "Ceiling relationship could not be classified",
    )

# ----------------------------------------------------------------------
# Main inspection
# ----------------------------------------------------------------------

def inspect(ifc_path: Path, output_path: Path):
    print("=" * 78)
    print("ENMA-WG Duct / Space / Ceiling Location Inspector V3")
    print("=" * 78)
    print(f"IFC    : {ifc_path}")
    print(f"Output : {output_path}")
    print()

    print("Opening IFC...")
    model = ifcopenshell.open(str(ifc_path))

    print(f"Schema : {model.schema}")
    print()

    settings = make_geom_settings()

    print("Building Space inventory...")
    spaces = build_space_inventory(model, settings)

    print("Building Ceiling inventory...")
    ceilings = build_ceiling_inventory(model, settings)

    ducts = model.by_type("IfcDuctSegment")

    print(f"IfcSpace       : {len(spaces)} geometry OK")
    print(f"Ceiling        : {len(ceilings)} geometry OK")
    print(f"IfcDuctSegment : {len(ducts)}")
    print()

    rows = []

    geometry_failed = 0
    space_match_counter = Counter()
    ceiling_match_counter = Counter()
    inference_counter = Counter()

    for index, duct in enumerate(ducts, start=1):
        if index % 100 == 0:
            print(f"Processing ducts : {index}/{len(ducts)}")

        vertices = get_vertices(duct, settings)
        duct_bbox = bbox_from_vertices(vertices)

        if duct_bbox is None:
            geometry_failed += 1
            continue

        cx, cy, cz = bbox_center(duct_bbox)

        space_candidates = find_space_candidates(
            duct_bbox,
            spaces,
        )
        chosen_space = choose_space_candidate(
            space_candidates
        )

        duct_storey = get_storey_name(duct)
        
        ceiling_candidates, ceiling_candidate_source = (
            find_ceiling_candidates(
                duct_bbox,
                duct_storey,
                ceilings,
            )
        )
        
        chosen_ceiling = choose_ceiling_candidate(
            duct_bbox,
            ceiling_candidates,
        )


        if chosen_space:
            space_match_counter[
                chosen_space["relation"]
            ] += 1
        else:
            space_match_counter["NO_SPACE_CANDIDATE"] += 1

        if chosen_ceiling:
            if (
                chosen_ceiling["duct_center_to_ceiling_z"]
                > 0
            ):
                ceiling_relation = "DUCT_CENTER_ABOVE_CEILING"
            elif (
                chosen_ceiling["duct_center_to_ceiling_z"]
                < 0
            ):
                ceiling_relation = "DUCT_CENTER_BELOW_CEILING"
            else:
                ceiling_relation = "DUCT_CENTER_AT_CEILING"

            ceiling_match_counter[ceiling_relation] += 1
        else:
            ceiling_relation = "NO_CEILING_CANDIDATE"
            ceiling_match_counter[ceiling_relation] += 1

        (
            construction_location_candidate,
            inference_level,
            inference_reason,
        ) = classify_ceiling_location(
            chosen_ceiling=chosen_ceiling,
            ceiling_candidate_source=ceiling_candidate_source,
            ceiling_relation=ceiling_relation,
        )

        inference_counter[
            construction_location_candidate
        ] += 1


        row = {
            "DuctStepId": duct.id(),
            "DuctGlobalId": safe_text(
                getattr(duct, "GlobalId", None)
            ),
            "DuctName": safe_text(
                getattr(duct, "Name", None)
            ),
            "DuctObjectType": safe_text(
                getattr(duct, "ObjectType", None)
            ),
            "DuctStorey": duct_storey,

            "DuctMinX": duct_bbox["min_x"],
            "DuctMaxX": duct_bbox["max_x"],
            "DuctMinY": duct_bbox["min_y"],
            "DuctMaxY": duct_bbox["max_y"],
            "DuctMinZ": duct_bbox["min_z"],
            "DuctMaxZ": duct_bbox["max_z"],

            "DuctCenterX": cx,
            "DuctCenterY": cy,
            "DuctCenterZ": cz,

            "SpaceCandidateCount": len(
                space_candidates
            ),

            "SpaceStepId": (
                chosen_space["step_id"]
                if chosen_space else ""
            ),
            "SpaceName": (
                chosen_space["name"]
                if chosen_space else ""
            ),
            "SpaceLongName": (
                chosen_space["long_name"]
                if chosen_space else ""
            ),
            "SpaceStorey": (
                chosen_space["storey"]
                if chosen_space else ""
            ),
            "SpaceMinZ": (
                chosen_space["bbox"]["min_z"]
                if chosen_space else ""
            ),
            "SpaceMaxZ": (
                chosen_space["bbox"]["max_z"]
                if chosen_space else ""
            ),
            "SpaceRelation": (
                chosen_space["relation"]
                if chosen_space
                else "NO_SPACE_CANDIDATE"
            ),
            "DuctCenterToSpaceTopZ": (
                chosen_space[
                    "z_delta_to_space_top"
                ]
                if chosen_space else ""
            ),

            "CeilingCandidateCount": len(
                ceiling_candidates
            ),

            "CeilingCandidateSource": ceiling_candidate_source,
            
            "CeilingSameStorey": (
                (
                    chosen_ceiling["storey"]
                    == duct_storey
                )
                if chosen_ceiling
                and duct_storey
                and chosen_ceiling["storey"]
                else ""
            ),


            "CeilingStepId": (
                chosen_ceiling["step_id"]
                if chosen_ceiling else ""
            ),
            "CeilingName": (
                chosen_ceiling["name"]
                if chosen_ceiling else ""
            ),
            "CeilingObjectType": (
                chosen_ceiling["object_type"]
                if chosen_ceiling else ""
            ),
            "CeilingStorey": (
                chosen_ceiling["storey"]
                if chosen_ceiling else ""
            ),
            "CeilingMinZ": (
                chosen_ceiling["bbox"]["min_z"]
                if chosen_ceiling else ""
            ),
            "CeilingMaxZ": (
                chosen_ceiling["bbox"]["max_z"]
                if chosen_ceiling else ""
            ),
            "CeilingMidZ": (
                chosen_ceiling["ceiling_mid_z"]
                if chosen_ceiling else ""
            ),
            "DuctCenterToCeilingZ": (
                chosen_ceiling[
                    "duct_center_to_ceiling_z"
                ]
                if chosen_ceiling else ""
            ),
            "CeilingXYOverlapArea": (
                chosen_ceiling["overlap_area"]
                if chosen_ceiling else ""
            ),
            "CeilingRelation": ceiling_relation,

            # ------------------------------------------------------
            # V3 preliminary inference.
            #
            # This is intentionally a CANDIDATE.
            # Final construction location will require stronger
            # spatial evidence in a later version.
            # ------------------------------------------------------

            "ConstructionLocationCandidate": (
                construction_location_candidate
            ),

            "InferenceLevel": inference_level,

            "InferenceReason": inference_reason,

            "InferenceStatus": "PRELIMINARY_V3",
        }


        rows.append(row)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = list(rows[0].keys()) if rows else []

    with output_path.open(
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
    print("=" * 78)
    print("Result")
    print("=" * 78)
    print(f"Ducts total       : {len(ducts)}")
    print(f"Rows written      : {len(rows)}")
    print(f"Geometry failed   : {geometry_failed}")
    print()

    print("Space relations")
    print("-" * 78)
    for key, value in space_match_counter.most_common():
        print(f"{value:6d}  {key}")

    print()
    print("Preliminary construction-location inference")
    print("-" * 78)
    for key, value in inference_counter.most_common():
        print(f"{value:6d}  {key}")

    print()
    print(f"CSV : {output_path}")
    print("=" * 78)


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Inspect IfcDuctSegment spatial relationships "
            "with IfcSpace and ceiling IfcCovering."
        )
    )

    parser.add_argument(
        "ifc",
        help="Input IFC file",
    )

    parser.add_argument(
        "--output",
        default="output/duct_ceiling_location.csv",
        help=(
            "Output CSV "
            "(default: output/duct_ceiling_location.csv)"
        ),
    )

    args = parser.parse_args()

    ifc_path = Path(args.ifc)
    output_path = Path(args.output)

    if not ifc_path.exists():
        raise FileNotFoundError(
            f"IFC file not found: {ifc_path}"
        )

    inspect(
        ifc_path=ifc_path,
        output_path=output_path,
    )


if __name__ == "__main__":
    main()