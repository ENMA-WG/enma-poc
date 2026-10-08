import math

import ifcopenshell
import ifcopenshell.util.element as element


IFC_FILE = r"data/営繕BIMモデル_EM.ifc"


def main():
    model = ifcopenshell.open(IFC_FILE)
    ducts = model.by_type("IfcDuctSegment")

    errors = []

    for duct in ducts:
        qto = element.get_psets(duct).get(
            "Qto_DuctSegmentBaseQuantities", {}
        )

        length_mm = qto.get("Length", 0)
        area = qto.get("GrossCrossSectionArea", 0)
        surface_area = qto.get("OuterSurfaceArea", 0)

        length_m = length_mm / 1000.0

        text = (duct.ObjectType or "") + (duct.Name or "")

        reason = None

        if "丸" in text:
            if area <= 0:
                reason = "ROUND: area <= 0"

        elif "角" in text:
            if length_m <= 0:
                reason = "RECT: length <= 0"

            elif area <= 0:
                reason = "RECT: area <= 0"

            else:
                wh_sum = surface_area / (2.0 * length_m)
                discriminant = wh_sum**2 - 4.0 * area

                if discriminant < 0:
                    reason = (
                        "RECT: negative discriminant "
                        f"({discriminant:.9f})"
                    )

        else:
            reason = "UNKNOWN SHAPE"

        if reason:
            errors.append(
                (
                    duct,
                    reason,
                    length_mm,
                    area,
                    surface_area,
                )
            )

    print("=== DUCT DIMENSION ERRORS ===")
    print(f"Errors = {len(errors)}")
    print()

    for duct, reason, length, area, surface in errors:
        print("=" * 70)
        print("GlobalId          :", duct.GlobalId)
        print("Name              :", duct.Name)
        print("ObjectType        :", duct.ObjectType)
        print("Reason            :", reason)
        print("Length            :", length)
        print("CrossSectionArea  :", area)
        print("OuterSurfaceArea  :", surface)


if __name__ == "__main__":
    main()