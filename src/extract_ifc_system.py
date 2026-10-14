from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element


# ============================================================
# Settings
# ============================================================

INPUT_IFC = Path("data/営繕BIMモデル_EM.ifc")
OUTPUT_IFC = Path("output/4FL_SA7.ifc")

TARGET_STOREY = "4FL"
TARGET_SYSTEM = "SA 7"


def get_storey(element):
    """
    Return the IfcBuildingStorey containing element.
    Uses IfcRelContainedInSpatialStructure / decomposition relations
    through IfcOpenShell utility functions.
    """
    container = ifcopenshell.util.element.get_container(element)

    while container is not None:
        if container.is_a("IfcBuildingStorey"):
            return container

        container = ifcopenshell.util.element.get_aggregate(container)

    return None


def get_systems(element):
    """
    Return distribution systems/groups assigned to element.
    """
    systems = []

    for rel in getattr(element, "HasAssignments", []) or []:
        if not rel.is_a("IfcRelAssignsToGroup"):
            continue

        group = rel.RelatingGroup

        if group and (
            group.is_a("IfcDistributionSystem")
            or group.is_a("IfcSystem")
        ):
            systems.append(group)

    return systems


def belongs_to_target_system(element):
    for system in get_systems(element):
        if (system.Name or "").strip() == TARGET_SYSTEM:
            return True

    return False


def belongs_to_target_storey(element):
    storey = get_storey(element)

    if storey is None:
        return False

    return (storey.Name or "").strip() == TARGET_STOREY


def main():
    print(f"Input : {INPUT_IFC}")
    print(f"Target: {TARGET_STOREY} / {TARGET_SYSTEM}")

    model = ifcopenshell.open(str(INPUT_IFC))

    # --------------------------------------------------------
    # 1. Find MEP elements belonging to SA 7 and 4FL
    # --------------------------------------------------------

    selected = []

    for element in model.by_type("IfcDistributionElement"):

        if not belongs_to_target_system(element):
            continue

        if not belongs_to_target_storey(element):
            continue

        selected.append(element)

    print()
    print(f"Selected elements: {len(selected)}")

    for element in selected:
        print(
            f"#{element.id():<8} "
            f"{element.is_a():<28} "
            f"GUID={element.GlobalId} "
            f"Name={element.Name}"
        )

    if not selected:
        print("No matching elements found.")
        return

    # --------------------------------------------------------
    # 2. Create a copy of the original model
    #
    # Important:
    # Instead of rebuilding geometry/property relationships
    # from scratch, copy the original IFC and remove unwanted
    # distribution elements.
    # --------------------------------------------------------

    output = ifcopenshell.open(str(INPUT_IFC))

    selected_guids = {
        e.GlobalId
        for e in selected
        if getattr(e, "GlobalId", None)
    }

    remove_elements = []

    for element in output.by_type("IfcDistributionElement"):

        guid = getattr(element, "GlobalId", None)

        if guid not in selected_guids:
            remove_elements.append(element)

    print()
    print(f"Distribution elements to remove: {len(remove_elements)}")

    # Deep removal removes relationships owned by the removed element.
    for element in remove_elements:
        try:
            ifcopenshell.util.element.remove_deep2(output, element)
        except Exception as exc:
            print(
                f"WARNING: could not deep-remove "
                f"#{element.id()} {element.is_a()}: {exc}"
            )

    # --------------------------------------------------------
    # 3. Write IFC
    # --------------------------------------------------------

    OUTPUT_IFC.parent.mkdir(parents=True, exist_ok=True)

    output.write(str(OUTPUT_IFC))

    print()
    print("Done.")
    print(f"Output: {OUTPUT_IFC}")


if __name__ == "__main__":
    main()