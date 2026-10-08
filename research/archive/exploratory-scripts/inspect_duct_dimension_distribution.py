import math
from collections import Counter

import ifcopenshell
import ifcopenshell.util.element as element


IFC_FILE = r"data/営繕BIMモデル_EM.ifc"


def main():
    model = ifcopenshell.open(IFC_FILE)
    ducts = model.by_type("IfcDuctSegment")

    round_sizes = Counter()
    rect_sizes = Counter()

    round_count = 0
    rect_count = 0
    errors = 0

    for duct in ducts:
        psets = element.get_psets(duct)
        qto = psets.get("Qto_DuctSegmentBaseQuantities", {})

        length_mm = qto.get("Length", 0)
        area = qto.get("GrossCrossSectionArea", 0)
        surface_area = qto.get("OuterSurfaceArea", 0)

        length_m = length_mm / 1000.0

        text = (duct.ObjectType or "") + (duct.Name or "")

        # --------------------------------------------------
        # ROUND
        # --------------------------------------------------
        if "丸" in text:
            round_count += 1

            if area <= 0:
                errors += 1
                continue

            diameter_mm = math.sqrt(
                4.0 * area / math.pi
            ) * 1000.0

            diameter_mm = round(diameter_mm, 2)

            round_sizes[diameter_mm] += 1

        # --------------------------------------------------
        # RECTANGULAR
        # --------------------------------------------------
        elif "角" in text:
            rect_count += 1

            if length_m <= 0 or area <= 0:
                errors += 1
                continue

            wh_sum = surface_area / (2.0 * length_m)
            discriminant = wh_sum**2 - 4.0 * area

            if discriminant < 0:
                errors += 1
                continue

            width_m = (
                wh_sum + math.sqrt(discriminant)
            ) / 2.0

            height_m = (
                wh_sum - math.sqrt(discriminant)
            ) / 2.0

            width_mm = round(width_m * 1000.0, 2)
            height_mm = round(height_m * 1000.0, 2)

            # Always store larger dimension first
            if height_mm > width_mm:
                width_mm, height_mm = height_mm, width_mm

            rect_sizes[(width_mm, height_mm)] += 1

        else:
            errors += 1

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    print("=== DUCT DIMENSION DISTRIBUTION ===")
    print()
    print(f"Total IfcDuctSegment : {len(ducts)}")
    print(f"ROUND                : {round_count}")
    print(f"RECTANGULAR          : {rect_count}")
    print(f"Errors / Unknown     : {errors}")

    # --------------------------------------------------
    # ROUND
    # --------------------------------------------------

    print()
    print("=== ROUND DUCT ===")
    print(f"Unique diameters : {len(round_sizes)}")
    print()

    for diameter, count in sorted(round_sizes.items()):
        print(
            f"D={diameter:8.2f} mm : "
            f"{count:4d}"
        )

    # --------------------------------------------------
    # RECTANGULAR
    # --------------------------------------------------

    print()
    print("=== RECTANGULAR DUCT ===")
    print(f"Unique dimensions : {len(rect_sizes)}")
    print()

    for (width, height), count in sorted(
        rect_sizes.items(),
        key=lambda x: (x[0][0], x[0][1])
    ):
        print(
            f"{width:8.2f} x "
            f"{height:8.2f} mm : "
            f"{count:4d}"
        )


if __name__ == "__main__":
    main()