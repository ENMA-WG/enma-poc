from collections import Counter, defaultdict

import ifcopenshell


IFC_FILE = r"data/営繕BIMモデル_EM.ifc"


def iter_representation_items(element):
    """
    Yield representation items from an IFC element.
    Also follows IfcMappedItem -> IfcRepresentationMap.
    """
    representation = getattr(element, "Representation", None)

    if not representation:
        return

    for rep in representation.Representations:
        for item in rep.Items:
            yield from walk_item(item)


def walk_item(item):
    """
    Recursively inspect representation items.
    """
    yield item

    # Mapped geometry
    if item.is_a("IfcMappedItem"):
        source = item.MappingSource

        if source and source.MappedRepresentation:
            for mapped_item in source.MappedRepresentation.Items:
                yield from walk_item(mapped_item)

    # Boolean geometry
    elif item.is_a("IfcBooleanResult"):
        if item.FirstOperand:
            yield from walk_item(item.FirstOperand)

        if item.SecondOperand:
            yield from walk_item(item.SecondOperand)


def main():
    model = ifcopenshell.open(IFC_FILE)
    ducts = model.by_type("IfcDuctSegment")

    item_types = Counter()
    swept_area_types = Counter()

    extrusion_count = 0
    ducts_with_extrusion = 0
    ducts_without_extrusion = 0

    profile_examples = defaultdict(list)

    print("=== DUCT REPRESENTATION / PROFILE INVENTORY ===")
    print()
    print(f"IfcDuctSegment = {len(ducts)}")
    print()

    for duct in ducts:
        found_extrusion = False

        for item in iter_representation_items(duct):
            item_type = item.is_a()
            item_types[item_type] += 1

            if item.is_a("IfcExtrudedAreaSolid"):
                found_extrusion = True
                extrusion_count += 1

                profile = item.SweptArea

                if profile:
                    profile_type = profile.is_a()
                    swept_area_types[profile_type] += 1

                    if len(profile_examples[profile_type]) < 5:
                        profile_examples[profile_type].append(
                            (
                                duct.GlobalId,
                                duct.Name,
                                profile,
                                item,
                            )
                        )

        if found_extrusion:
            ducts_with_extrusion += 1
        else:
            ducts_without_extrusion += 1

    # --------------------------------------------------
    # Representation item types
    # --------------------------------------------------

    print("=== REPRESENTATION ITEM TYPES ===")

    for name, count in item_types.most_common():
        print(f"{name:40s} {count:5d}")

    # --------------------------------------------------
    # ExtrudedAreaSolid
    # --------------------------------------------------

    print()
    print("=== IfcExtrudedAreaSolid ===")
    print(f"Total extrusion solids      : {extrusion_count}")
    print(f"Ducts with extrusion        : {ducts_with_extrusion}")
    print(f"Ducts without extrusion     : {ducts_without_extrusion}")

    # --------------------------------------------------
    # SweptArea profile types
    # --------------------------------------------------

    print()
    print("=== SWEPT AREA PROFILE TYPES ===")

    if swept_area_types:
        for name, count in swept_area_types.most_common():
            print(f"{name:40s} {count:5d}")
    else:
        print("No IfcExtrudedAreaSolid profiles found.")

    # --------------------------------------------------
    # Examples
    # --------------------------------------------------

    print()
    print("=== PROFILE EXAMPLES ===")

    for profile_type, examples in profile_examples.items():
        print()
        print("-" * 70)
        print(profile_type)
        print("-" * 70)

        for global_id, name, profile, solid in examples:
            print()
            print("GlobalId :", global_id)
            print("Name     :", name)

            # Rectangle
            if profile.is_a("IfcRectangleProfileDef"):
                print("XDim     :", profile.XDim)
                print("YDim     :", profile.YDim)

            # Circle
            elif profile.is_a("IfcCircleProfileDef"):
                print("Radius   :", profile.Radius)
                print(
                    "Diameter :",
                    profile.Radius * 2.0
                )

            # Hollow rectangle
            elif profile.is_a("IfcRectangleHollowProfileDef"):
                print("XDim     :", profile.XDim)
                print("YDim     :", profile.YDim)
                print(
                    "WallThickness :",
                    profile.WallThickness
                )

            # Hollow circle
            elif profile.is_a("IfcCircleHollowProfileDef"):
                print("Radius   :", profile.Radius)
                print(
                    "Diameter :",
                    profile.Radius * 2.0
                )
                print(
                    "WallThickness :",
                    profile.WallThickness
                )

            else:
                print("Profile  :", profile)

            print("Depth    :", solid.Depth)
            print(
                "Direction:",
                solid.ExtrudedDirection.DirectionRatios
            )


if __name__ == "__main__":
    main()