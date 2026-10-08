from collections import Counter, defaultdict

import ifcopenshell


IFC_FILE = r"data/営繕BIMモデル_EM.ifc"


def main():
    model = ifcopenshell.open(IFC_FILE)
    ducts = model.by_type("IfcDuctSegment")

    curve_types = Counter()
    curve_examples = defaultdict(list)

    total_profiles = 0
    missing_curve = 0

    print("=== DUCT OUTER CURVE INVENTORY ===")
    print()
    print(f"IfcDuctSegment = {len(ducts)}")
    print()

    for duct in ducts:
        representation = getattr(duct, "Representation", None)

        if not representation:
            continue

        for rep in representation.Representations:
            for item in rep.Items:

                if not item.is_a("IfcExtrudedAreaSolid"):
                    continue

                profile = item.SweptArea

                if not profile:
                    continue

                if not profile.is_a(
                    "IfcArbitraryClosedProfileDef"
                ):
                    continue

                total_profiles += 1

                curve = profile.OuterCurve

                if not curve:
                    missing_curve += 1
                    continue

                curve_type = curve.is_a()
                curve_types[curve_type] += 1

                if len(curve_examples[curve_type]) < 10:
                    curve_examples[curve_type].append(
                        (
                            duct,
                            profile,
                            curve,
                            item,
                        )
                    )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    print("=== OUTER CURVE TYPES ===")

    for curve_type, count in curve_types.most_common():
        print(
            f"{curve_type:40s} "
            f"{count:5d}"
        )

    print()
    print(f"Profiles inspected : {total_profiles}")
    print(f"Missing OuterCurve : {missing_curve}")

    # --------------------------------------------------
    # Examples
    # --------------------------------------------------

    print()
    print("=== OUTER CURVE EXAMPLES ===")

    for curve_type, examples in curve_examples.items():

        print()
        print("=" * 70)
        print(curve_type)
        print("=" * 70)

        for duct, profile, curve, solid in examples:

            print()
            print("GlobalId   :", duct.GlobalId)
            print("Name       :", duct.Name)
            print("ObjectType :", duct.ObjectType)
            print("Profile    :", profile)
            print("OuterCurve :", curve)
            print("Depth      :", solid.Depth)

            # ------------------------------------------
            # IfcPolyline
            # ------------------------------------------

            if curve.is_a("IfcPolyline"):

                print("Points:")

                for point in curve.Points:
                    print(
                        "   ",
                        tuple(point.Coordinates)
                    )

            # ------------------------------------------
            # IfcIndexedPolyCurve
            # ------------------------------------------

            elif curve.is_a("IfcIndexedPolyCurve"):

                points = curve.Points

                print(
                    "PointList type:",
                    points.is_a()
                )

                if hasattr(points, "CoordList"):
                    print("Coordinates:")

                    for coords in points.CoordList:
                        print(
                            "   ",
                            tuple(coords)
                        )

                if curve.Segments:
                    print("Segments:")

                    for segment in curve.Segments:
                        print(
                            "   ",
                            segment
                        )

            # ------------------------------------------
            # IfcCompositeCurve
            # ------------------------------------------

            elif curve.is_a("IfcCompositeCurve"):

                print(
                    "Segments:",
                    len(curve.Segments)
                )

                for segment in curve.Segments:
                    parent = segment.ParentCurve

                    print(
                        "   ",
                        parent.is_a(),
                        ":",
                        parent
                    )

            # ------------------------------------------
            # Other
            # ------------------------------------------

            else:
                print(
                    "Curve data:",
                    curve
                )


if __name__ == "__main__":
    main()