"""
inspect_pipe_fittings.py

ENMA-WG Tokyo Summit 2026 PoC
Diagnostic tool for IfcPipeFitting inventory.

Purpose:
    Inspect how pipe fittings are represented in the MLIT IFC model.

    This is NOT the production quantity takeoff logic.
    It is an investigation tool used before implementing fitting takeoff.

Output:
    output/pipe_fitting_inventory.csv

Checks:
    - IfcPipeFitting count
    - Name / ObjectType / PredefinedType
    - Related IfcPipeFittingType
    - Storey
    - IfcDistributionSystem membership
    - Property sets / quantities
    - Material
    - Ports
"""

from pathlib import Path
from collections import Counter
import csv

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.system


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")
OUTPUT_FILE = Path("output/pipe_fitting_inventory.csv")


# ------------------------------------------------------------
# Utility
# ------------------------------------------------------------

def safe_text(value):
    """Convert IFC value to a safe string."""
    if value is None:
        return ""
    return str(value).strip()


def join_unique(values):
    """Join unique non-empty values while preserving order."""
    result = []

    for value in values:
        value = safe_text(value)

        if value and value not in result:
            result.append(value)

    return " | ".join(result)


def flatten_value(value):
    """
    Convert property values to CSV-friendly text.

    Diagnostic script only:
    nested structures are represented as strings.
    """
    if value is None:
        return ""

    if isinstance(value, (str, int, float, bool)):
        return str(value)

    if isinstance(value, (list, tuple)):
        return " | ".join(
            flatten_value(v)
            for v in value
            if v is not None
        )

    if isinstance(value, dict):
        parts = []

        for key, val in value.items():
            if key == "id":
                continue

            parts.append(
                f"{key}={flatten_value(val)}"
            )

        return "; ".join(parts)

    return str(value)


# ------------------------------------------------------------
# Storey
# ------------------------------------------------------------

def get_storey(element):
    """
    Find containing IfcBuildingStorey.
    """

    container = ifcopenshell.util.element.get_container(
        element
    )

    current = container

    while current is not None:

        if current.is_a("IfcBuildingStorey"):
            return safe_text(current.Name)

        current = ifcopenshell.util.element.get_container(
            current
        )

    return ""


# ------------------------------------------------------------
# Type information
# ------------------------------------------------------------

def get_type_info(element):
    """
    Return:
        Type IFC class
        Type Name
        Type ElementType
        Type PredefinedType
    """

    element_type = ifcopenshell.util.element.get_type(
        element
    )

    if element_type is None:
        return "", "", "", ""

    type_class = element_type.is_a()

    type_name = safe_text(
        getattr(element_type, "Name", None)
    )

    type_element_type = safe_text(
        getattr(element_type, "ElementType", None)
    )

    type_predefined = safe_text(
        getattr(element_type, "PredefinedType", None)
    )

    return (
        type_class,
        type_name,
        type_element_type,
        type_predefined,
    )


# ------------------------------------------------------------
# Distribution systems
# ------------------------------------------------------------

def get_system_info(element):
    """
    Get all distribution systems assigned to the fitting.

    Multiple systems are preserved.
    """

    try:
        systems = ifcopenshell.util.system.get_element_systems(
            element
        )
    except Exception:
        systems = []

    system_names = []
    system_object_types = []
    system_predefined_types = []

    for system in systems:

        system_names.append(
            getattr(system, "Name", None)
        )

        system_object_types.append(
            getattr(system, "ObjectType", None)
        )

        system_predefined_types.append(
            getattr(system, "PredefinedType", None)
        )

    return {
        "count": len(systems),
        "names": join_unique(system_names),
        "object_types": join_unique(
            system_object_types
        ),
        "predefined_types": join_unique(
            system_predefined_types
        ),
    }


# ------------------------------------------------------------
# Material
# ------------------------------------------------------------

def get_material_info(element):
    """
    Get material assigned to the fitting.

    Because IFC material relationships can have several forms,
    preserve the raw IFC class and readable names.
    """

    try:
        material = ifcopenshell.util.element.get_material(
            element,
            should_skip_usage=False,
        )
    except Exception:
        material = None

    if material is None:
        return "", ""

    material_class = material.is_a()

    names = []

    # Direct IfcMaterial
    if material.is_a("IfcMaterial"):
        names.append(
            getattr(material, "Name", None)
        )

    # IfcMaterialLayerSetUsage etc.
    elif material.is_a("IfcMaterialLayerSetUsage"):

        layer_set = getattr(
            material,
            "ForLayerSet",
            None,
        )

        if layer_set:

            for layer in getattr(
                layer_set,
                "MaterialLayers",
                [],
            ):

                mat = getattr(
                    layer,
                    "Material",
                    None,
                )

                if mat:
                    names.append(
                        getattr(mat, "Name", None)
                    )

    # IfcMaterialProfileSetUsage
    elif material.is_a("IfcMaterialProfileSetUsage"):

        profile_set = getattr(
            material,
            "ForProfileSet",
            None,
        )

        if profile_set:

            for profile in getattr(
                profile_set,
                "MaterialProfiles",
                [],
            ):

                mat = getattr(
                    profile,
                    "Material",
                    None,
                )

                if mat:
                    names.append(
                        getattr(mat, "Name", None)
                    )

    # IfcMaterialConstituentSet
    elif material.is_a("IfcMaterialConstituentSet"):

        for constituent in getattr(
            material,
            "MaterialConstituents",
            [],
        ):

            mat = getattr(
                constituent,
                "Material",
                None,
            )

            if mat:
                names.append(
                    getattr(mat, "Name", None)
                )

    # IfcMaterialList
    elif material.is_a("IfcMaterialList"):

        for mat in getattr(
            material,
            "Materials",
            [],
        ):
            names.append(
                getattr(mat, "Name", None)
            )

    # Generic fallback
    else:

        name = getattr(
            material,
            "Name",
            None,
        )

        if name:
            names.append(name)

    return (
        material_class,
        join_unique(names),
    )


# ------------------------------------------------------------
# Ports
# ------------------------------------------------------------

def get_ports(element):
    """
    Count ports assigned to the fitting.

    Handles IFC4-style IfcRelNests and also checks
    HasPorts where available.
    """

    ports = []

    # IFC4 / IFC4x3
    for rel in getattr(element, "IsNestedBy", []):

        for obj in getattr(
            rel,
            "RelatedObjects",
            [],
        ):

            if obj.is_a("IfcDistributionPort"):
                ports.append(obj)

    # IFC2x3-style relationship if present
    for rel in getattr(element, "HasPorts", []):

        port = getattr(
            rel,
            "RelatingPort",
            None,
        )

        if (
            port is not None
            and port.is_a("IfcDistributionPort")
        ):
            ports.append(port)

    # Deduplicate by IFC id
    unique = {}

    for port in ports:
        unique[port.id()] = port

    return list(unique.values())


# ------------------------------------------------------------
# Property inventory
# ------------------------------------------------------------

def get_property_inventory(element):
    """
    Flatten all Psets / Qtos into one diagnostic string.

    Example:
        Pset_X.PropA=value;
        Qto_X.Length=value
    """

    try:
        psets = ifcopenshell.util.element.get_psets(
            element
        )
    except Exception:
        return ""

    items = []

    for pset_name in sorted(psets.keys()):

        properties = psets[pset_name]

        if not isinstance(properties, dict):
            continue

        for prop_name in sorted(properties.keys()):

            if prop_name == "id":
                continue

            value = properties[prop_name]

            items.append(
                f"{pset_name}.{prop_name}"
                f"={flatten_value(value)}"
            )

    return "; ".join(items)


# ------------------------------------------------------------
# Property names only
# ------------------------------------------------------------

def get_property_names(element):
    """
    Return Pset.Property names without values.

    Useful for comparing what information exists
    across all fittings.
    """

    try:
        psets = ifcopenshell.util.element.get_psets(
            element
        )
    except Exception:
        return []

    names = []

    for pset_name, properties in psets.items():

        if not isinstance(properties, dict):
            continue

        for prop_name in properties.keys():

            if prop_name == "id":
                continue

            names.append(
                f"{pset_name}.{prop_name}"
            )

    return sorted(names)


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    print()
    print("=" * 70)
    print("ENMA-WG Pipe Fitting Inspection")
    print("Tokyo Summit 2026 PoC")
    print("=" * 70)

    print(f"IFC : {IFC_FILE}")

    if not IFC_FILE.exists():
        raise FileNotFoundError(
            f"IFC file not found: {IFC_FILE}"
        )

    model = ifcopenshell.open(
        str(IFC_FILE)
    )

    fittings = model.by_type(
        "IfcPipeFitting"
    )

    print()
    print(
        f"IfcPipeFitting count: {len(fittings)}"
    )

    rows = []

    predefined_counter = Counter()
    type_counter = Counter()
    system_counter = Counter()
    storey_counter = Counter()
    material_counter = Counter()
    port_counter = Counter()
    property_counter = Counter()

    for index, fitting in enumerate(
        fittings,
        start=1,
    ):

        # ----------------------------------------------------
        # Basic information
        # ----------------------------------------------------

        global_id = safe_text(
            getattr(
                fitting,
                "GlobalId",
                None,
            )
        )

        name = safe_text(
            getattr(
                fitting,
                "Name",
                None,
            )
        )

        object_type = safe_text(
            getattr(
                fitting,
                "ObjectType",
                None,
            )
        )

        # Use utility so type inheritance / USERDEFINED
        # is handled more robustly.
        try:
            predefined_type = safe_text(
                ifcopenshell.util.element.get_predefined_type(
                    fitting
                )
            )
        except Exception:
            predefined_type = safe_text(
                getattr(
                    fitting,
                    "PredefinedType",
                    None,
                )
            )

        # ----------------------------------------------------
        # Type
        # ----------------------------------------------------

        (
            type_class,
            type_name,
            type_element_type,
            type_predefined_type,
        ) = get_type_info(fitting)

        # ----------------------------------------------------
        # Storey
        # ----------------------------------------------------

        storey = get_storey(
            fitting
        )

        # ----------------------------------------------------
        # System
        # ----------------------------------------------------

        system = get_system_info(
            fitting
        )

        # ----------------------------------------------------
        # Material
        # ----------------------------------------------------

        (
            material_class,
            material_name,
        ) = get_material_info(
            fitting
        )

        # ----------------------------------------------------
        # Ports
        # ----------------------------------------------------

        ports = get_ports(
            fitting
        )

        port_count = len(ports)

        # ----------------------------------------------------
        # Properties
        # ----------------------------------------------------

        property_inventory = (
            get_property_inventory(
                fitting
            )
        )

        property_names = (
            get_property_names(
                fitting
            )
        )

        # ----------------------------------------------------
        # Counters
        # ----------------------------------------------------

        predefined_counter[
            predefined_type or "(blank)"
        ] += 1

        type_counter[
            type_name or "(blank)"
        ] += 1

        storey_counter[
            storey or "(blank)"
        ] += 1

        material_counter[
            material_name
            or material_class
            or "(blank)"
        ] += 1

        port_counter[
            port_count
        ] += 1

        if system["object_types"]:

            for value in system[
                "object_types"
            ].split(" | "):

                system_counter[
                    value
                ] += 1

        else:
            system_counter[
                "(blank)"
            ] += 1

        for prop_name in property_names:
            property_counter[
                prop_name
            ] += 1

        # ----------------------------------------------------
        # CSV row
        # ----------------------------------------------------

        row = {
            "GlobalId": global_id,
            "Name": name,
            "ObjectType": object_type,
            "PredefinedType": predefined_type,

            "TypeClass": type_class,
            "TypeName": type_name,
            "TypeElementType": type_element_type,
            "TypePredefinedType": type_predefined_type,

            "階": storey,

            "系統コード": system["names"],
            "系統名称": system["object_types"],
            "IFC系統分類": system[
                "predefined_types"
            ],
            "系統所属数": system["count"],

            "MaterialClass": material_class,
            "MaterialName": material_name,

            "PortCount": port_count,

            "Properties": property_inventory,
        }

        rows.append(row)

        # ----------------------------------------------------
        # Console progress
        # ----------------------------------------------------

        print(
            f"[{index:>3}/{len(fittings)}] "
            f"{predefined_type or '(blank)':<15} "
            f"{type_name or name or '(unnamed)'}"
        )

    # --------------------------------------------------------
    # Write CSV
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "GlobalId",
        "Name",
        "ObjectType",
        "PredefinedType",

        "TypeClass",
        "TypeName",
        "TypeElementType",
        "TypePredefinedType",

        "階",

        "系統コード",
        "系統名称",
        "IFC系統分類",
        "系統所属数",

        "MaterialClass",
        "MaterialName",

        "PortCount",

        "Properties",
    ]

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print()
    print(
        f"IfcPipeFitting : {len(fittings)}"
    )

    # --------------------------------------------------------
    # PredefinedType
    # --------------------------------------------------------

    print()
    print("--- PredefinedType ---")

    for key, count in (
        predefined_counter.most_common()
    ):
        print(
            f"{count:>5}  {key}"
        )

    # --------------------------------------------------------
    # TypeName
    # --------------------------------------------------------

    print()
    print("--- TypeName ---")

    for key, count in (
        type_counter.most_common()
    ):
        print(
            f"{count:>5}  {key}"
        )

    # --------------------------------------------------------
    # Storey
    # --------------------------------------------------------

    print()
    print("--- Storey ---")

    for key, count in (
        storey_counter.most_common()
    ):
        print(
            f"{count:>5}  {key}"
        )

    # --------------------------------------------------------
    # Systems
    # --------------------------------------------------------

    print()
    print("--- Distribution System ---")

    for key, count in (
        system_counter.most_common()
    ):
        print(
            f"{count:>5}  {key}"
        )

    # --------------------------------------------------------
    # Materials
    # --------------------------------------------------------

    print()
    print("--- Material ---")

    for key, count in (
        material_counter.most_common()
    ):
        print(
            f"{count:>5}  {key}"
        )

    # --------------------------------------------------------
    # Ports
    # --------------------------------------------------------

    print()
    print("--- Port Count ---")

    for key in sorted(
        port_counter.keys()
    ):
        print(
            f"{port_counter[key]:>5}  "
            f"{key} ports"
        )

    # --------------------------------------------------------
    # Properties
    # --------------------------------------------------------

    print()
    print("--- Property occurrence ---")

    for key, count in (
        property_counter.most_common()
    ):
        print(
            f"{count:>5}  {key}"
        )

    # --------------------------------------------------------
    # End
    # --------------------------------------------------------

    print()
    print(
        f"CSV : {OUTPUT_FILE}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()
