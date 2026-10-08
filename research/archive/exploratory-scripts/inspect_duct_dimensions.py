import math

import ifcopenshell
import ifcopenshell.util.element as element


IFC_FILE = r"data/営繕BIMモデル_EM.ifc"


def main():
    model = ifcopenshell.open(IFC_FILE)
    ducts = model.by_type("IfcDuctSegment")

    print(f"IfcDuctSegment = {len(ducts)}")
    print("=== INFERRED DUCT DIMENSIONS : FIRST 20 ===")

    for duct in ducts[:20]:
        psets = element.get_psets(duct)
        qto = psets.get("Qto_DuctSegmentBaseQuantities", {})

        length_mm = qto.get("Length", 0)
        area = qto.get("GrossCrossSectionArea", 0)
        surface_area = qto.get("OuterSurfaceArea", 0)

        length_m = length_mm / 1000.0

        text = (duct.ObjectType or "") + (duct.Name or "")

        if "丸" in text:
            shape = "ROUND"

            if area > 0:
                diameter_mm = math.sqrt(
                    4.0 * area / math.pi
                ) * 1000.0

                print(
                    f"{shape:5s} "
                    f"D={diameter_mm:8.2f} mm  "
                    f"L={length_m:7.3f} m  "
                    f"{duct.Name}"
                )
            else:
                print(
                    f"{shape:5s} CALC_ERROR "
                    f"L={length_m:7.3f} m "
                    f"{duct.Name}"
                )

        elif "角" in text:
            shape = "RECT"

            if length_m <= 0:
                print(
                    f"{shape:5s} CALC_ERROR "
                    f"L={length_m:7.3f} m "
                    f"{duct.Name}"
                )
                continue

            # For a rectangular duct:
            #
            # A = W * H
            # S = 2 * (W + H) * L
            #
            # Therefore:
            # W + H = S / (2 * L)

            wh_sum = surface_area / (2.0 * length_m)
            discriminant = wh_sum**2 - 4.0 * area

            if discriminant >= 0:
                width_m = (
                    wh_sum + math.sqrt(discriminant)
                ) / 2.0

                height_m = (
                    wh_sum - math.sqrt(discriminant)
                ) / 2.0

                width_mm = width_m * 1000.0
                height_mm = height_m * 1000.0

                print(
                    f"{shape:5s} "
                    f"{width_mm:8.2f} x "
                    f"{height_mm:8.2f} mm  "
                    f"L={length_m:7.3f} m  "
                    f"{duct.Name}"
                )
            else:
                print(
                    f"{shape:5s} CALC_ERROR "
                    f"L={length_m:7.3f} m "
                    f"{duct.Name}"
                )

        else:
            print(
                f"UNKNOWN "
                f"L={length_m:7.3f} m "
                f"{duct.Name}"
            )


if __name__ == "__main__":
    main()