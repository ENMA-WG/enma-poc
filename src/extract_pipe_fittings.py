"""
extract_pipe_fittings.py

ENMA-WG Tokyo Summit 2026 PoC
MEP Quantity Takeoff - Step 1 / Pipe Fittings

Input:
    data/営繕BIMモデル_EM.ifc

Output:
    output/pipe_fittings_detail.csv
    output/pipe_fittings_summary.csv

Purpose:
    Extract IfcPipeFitting quantities and aggregate them by:

        Storey
        Distribution System
        Fitting Type
        Port Count

Notes:
    - Pipe fittings are counted as discrete quantities.
    - Pipe fitting length is NOT added to pipe segment length.
    - PredefinedType is preserved even when NOTDEFINED.
    - TypeName is used as the practical fitting description.
    - Multiple distribution-system memberships are preserved.
"""

from pathlib import Path
from collections import Counter, defaultdict
import csv

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.system


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")

DETAIL_FILE = Path(
    "output/pipe_fittings_detail.csv"
)

SUMMARY_FILE = Path(
    "output/pipe_fittings_summary.csv"
)


# ------------------------------------------------------------
# Utility
# ------------------------------------------------------------

def safe_text(value):
    if value is None:
        return ""

    return str(value).strip()


def join_unique(values):
    result = []

    for value in values:
        value = safe_text(value)

        if value and value not in result:
            result.append(value)

    return " | ".join(result)


# ------------------------------------------------------------
# Storey
# ------------------------------------------------------------

def get_storey(element):
    """
    Return containing IfcBuildingStorey name.
    """

    try:
        container = (
            ifcopenshell.util.element.get_container(
                element
            )
        )
    except Exception:
        container = None

    current = container

    while current is not None:

        if current.is_a("IfcBuildingStorey"):
            return safe_text(
                getattr(current, "Name", None)
            )

        try:
            current = (
                ifcopenshell.util.element.get_container(
                    current
                )
            )
        except Exception:
            break

    return ""


# ------------------------------------------------------------
# Type
# ------------------------------------------------------------

def get_type_info(element):
    """
    Return fitting type information.
    """

    element_type = (
        ifcopenshell.util.element.get_type(
            element
        )
    )

    if element_type is None:
        return {
            "class": "",
            "name": "",
            "element_type": "",
            "predefined_type": "",
        }

    return {
        "class": element_type.is_a(),

        "name": safe_text(
            getattr(
                element_type,
                "Name",
                None,
            )
        ),

        "element_type": safe_text(
            getattr(
                element_type,
                "ElementType",
                None,
            )
        ),

        "predefined_type": safe_text(
            getattr(
                element_type,
                "PredefinedType",
                None,
            )
        ),
    }


# ------------------------------------------------------------
# Distribution System
# ------------------------------------------------------------

def get_system_info(element):
    """
    Return all IfcDistributionSystem memberships.

    Multiple memberships are preserved with " | ".
    """

    try:
        systems = (
            ifcopenshell.util.system
            .get_element_systems(element)
        )
    except Exception:
        systems = []

    names = []
    object_types = []
    predefined_types = []

    for system in systems:

        names.append(
            getattr(system, "Name", None)
        )

        object_types.append(
            getattr(
                system,
                "ObjectType",
                None,
            )
        )

        predefined_types.append(
            getattr(
                system,
                "PredefinedType",
                None,
            )
        )

    return {
        "count": len(systems),

        "names": join_unique(
            names
        ),

        "object_types": join_unique(
            object_types
        ),

        "predefined_types": join_unique(
            predefined_types
        ),
    }


# ------------------------------------------------------------
# Material
# ------------------------------------------------------------

def get_material_name(element):
    """
    Return readable material name(s).

    Diagnostic / provenance information.
    """

    try:
        material = (
            ifcopenshell.util.element.get_material(
                element,
                should_skip_usage=False,
            )
        )
    except Exception:
        material = None

    if material is None:
        return ""

    names = []

    if material.is_a("IfcMaterial"):

        names.append(
            getattr(material, "Name", None)
        )

    elif material.is_a(
        "IfcMaterialLayerSetUsage"
    ):

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
                        getattr(
                            mat,
                            "Name",
                            None,
                        )
                    )

    elif material.is_a(
        "IfcMaterialProfileSetUsage"
    ):

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
                        getattr(
                            mat,
                            "Name",
                            None,
                        )
                    )

    elif material.is_a(
        "IfcMaterialConstituentSet"
    ):

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
                    getattr(
                        mat,
                        "Name",
                        None,
                    )
                )

    elif material.is_a(
        "IfcMaterialList"
    ):

        for mat in getattr(
            material,
            "Materials",
            [],
        ):

            names.append(
                getattr(
                    mat,
                    "Name",
                    None,
                )
            )

    else:

        names.append(
            getattr(
                material,
                "Name",
                None,
            )
        )

    return join_unique(names)


# ------------------------------------------------------------
# Ports
# ------------------------------------------------------------

def get_ports(element):
    """
    Return unique IfcDistributionPorts.

    IFC4 normally uses IfcRelNests.
    HasPorts is also checked for compatibility.
    """

    ports = []

    # IFC4 / IFC4x3
    for rel in getattr(
        element,
        "IsNestedBy",
        [],
    ):

        for obj in getattr(
            rel,
            "RelatedObjects",
            [],
        ):

            if obj.is_a(
                "IfcDistributionPort"
            ):
                ports.append(obj)

    # Compatibility fallback
    for rel in getattr(
        element,
        "HasPorts",
        [],
    ):

        port = getattr(
            rel,
            "RelatingPort",
            None,
        )

        if (
            port is not None
            and port.is_a(
                "IfcDistributionPort"
            )
        ):
            ports.append(port)

    unique = {}

    for port in ports:
        unique[port.id()] = port

    return list(unique.values())


# ------------------------------------------------------------
# Port connectivity / fitting connection diameter
# ------------------------------------------------------------

def get_connected_ports(port):
    """
    Return IfcDistributionPorts connected to this port
    through IfcRelConnectsPorts.

    Both directions are checked:
        ConnectedTo
        ConnectedFrom
    """

    connected = []

    for rel in getattr(
        port,
        "ConnectedTo",
        [],
    ):
        other = getattr(
            rel,
            "RelatedPort",
            None,
        )

        if (
            other is not None
            and other.is_a(
                "IfcDistributionPort"
            )
        ):
            connected.append(other)

    for rel in getattr(
        port,
        "ConnectedFrom",
        [],
    ):
        other = getattr(
            rel,
            "RelatingPort",
            None,
        )

        if (
            other is not None
            and other.is_a(
                "IfcDistributionPort"
            )
        ):
            connected.append(other)

    unique = {}

    for item in connected:
        unique[item.id()] = item

    return list(unique.values())


def get_port_owner(port):
    """
    Return the element owning / nesting a port.
    """

    # IFC4 / IFC4x3
    for rel in getattr(
        port,
        "Nests",
        [],
    ):
        owner = getattr(
            rel,
            "RelatingObject",
            None,
        )

        if owner is not None:
            return owner

    # Compatibility fallback
    for rel in getattr(
        port,
        "ContainedIn",
        [],
    ):
        owner = getattr(
            rel,
            "RelatedElement",
            None,
        )

        if owner is not None:
            return owner

    return None


def unwrap_value(value):
    """
    Convert IFC wrapped values to normal Python values.
    """

    if value is None:
        return None

    if hasattr(
        value,
        "wrappedValue",
    ):
        return value.wrappedValue

    return value


def get_outer_diameter(element):
    """
    Get OuterDiameter from the connected element.

    Priority:
        Pset_PipeSegmentTypeCommon.OuterDiameter

    The function also searches element type properties
    as a fallback.

    Returns:
        float or None
    """

    if element is None:
        return None

    # --------------------------------------------------------
    # Occurrence Psets
    # --------------------------------------------------------

    try:
        psets = (
            ifcopenshell.util.element
            .get_psets(element)
        )
    except Exception:
        psets = {}

    pset = psets.get(
        "Pset_PipeSegmentTypeCommon",
        {},
    )

    value = pset.get(
        "OuterDiameter"
    )

    value = unwrap_value(value)

    if value not in (
        None,
        "",
    ):
        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            pass

    # --------------------------------------------------------
    # Type Psets fallback
    # --------------------------------------------------------

    try:
        element_type = (
            ifcopenshell.util.element
            .get_type(element)
        )
    except Exception:
        element_type = None

    if element_type is not None:

        try:
            type_psets = (
                ifcopenshell.util.element
                .get_psets(
                    element_type
                )
            )
        except Exception:
            type_psets = {}

        pset = type_psets.get(
            "Pset_PipeSegmentTypeCommon",
            {},
        )

        value = pset.get(
            "OuterDiameter"
        )

        value = unwrap_value(value)

        if value not in (
            None,
            "",
        ):
            try:
                return float(value)
            except (
                TypeError,
                ValueError,
            ):
                pass

    return None


def normalize_diameter(value):
    """
    Clean floating-point noise.

    Example:
        114.30000000000001 -> 114.3
    """

    if value is None:
        return ""

    return round(
        float(value),
        3,
    )


def get_fitting_connection_diameters(
    fitting
):
    """
    Determine fitting connection diameters from connectivity.

    Verified path:

        IfcPipeFitting
            -> IfcDistributionPort
            -> IfcRelConnectsPorts
            -> IfcDistributionPort
            -> IfcPipeSegment
            -> Pset_PipeSegmentTypeCommon.OuterDiameter

    No diameter is inferred when:
        - the fitting port is unconnected
        - the connected element is another fitting
        - OuterDiameter is unavailable

    Returns:
        {
            "diameters": [d1, d2, d3],
            "completeness": "COMPLETE" / "PARTIAL" / "NONE",
            "source": "...",
        }
    """

    ports = get_ports(
        fitting
    )

    # Make output deterministic.
    ports = sorted(
        ports,
        key=lambda p: p.id(),
    )

    diameters = []

    source_found = False

    for port in ports:

        diameter = None

        connected_ports = (
            get_connected_ports(
                port
            )
        )

        # Deterministic order
        connected_ports = sorted(
            connected_ports,
            key=lambda p: p.id(),
        )

        for connected_port in (
            connected_ports
        ):

            connected_element = (
                get_port_owner(
                    connected_port
                )
            )

            if connected_element is None:
                continue

            # Important:
            # Do NOT infer through another fitting yet.
            if not connected_element.is_a(
                "IfcPipeSegment"
            ):
                continue

            diameter = (
                get_outer_diameter(
                    connected_element
                )
            )

            if diameter is not None:
                source_found = True
                break

        diameters.append(
            normalize_diameter(
                diameter
            )
        )

    # Maximum expected for current pipe fittings = 3.
    while len(diameters) < 3:
        diameters.append("")

    known_count = sum(
        1
        for value in diameters[
            :len(ports)
        ]
        if value != ""
    )

    if not ports or known_count == 0:
        completeness = "NONE"

    elif known_count == len(ports):
        completeness = "COMPLETE"

    else:
        completeness = "PARTIAL"

    if source_found:
        source = (
            "Connected "
            "IfcPipeSegment."
            "Pset_PipeSegmentTypeCommon."
            "OuterDiameter"
        )
    else:
        source = ""

    return {
        "diameters":
            diameters[:3],

        "completeness":
            completeness,

        "source":
            source,
    }


# ------------------------------------------------------------
# Practical fitting category
# ------------------------------------------------------------

def classify_fitting(type_name):
    """
    Convert model-specific Japanese TypeName
    into a practical quantity-takeoff category.

    IMPORTANT:
        Original TypeName is always preserved separately.

    This mapping is intentionally explicit rather than
    pretending that IFC PredefinedType supplied the meaning.
    """

    text = safe_text(type_name)

    if "エルボ_冷媒管" in text:
        return "冷媒管エルボ"

    if "エルボ" in text:
        return "エルボ"

    if "径違い90°" in text and "Y" in text:
        return "径違い90°大曲がりY"

    if "径違いＴ型" in text:
        return "径違いT型"

    if "レジューサ" in text:
        return "レジューサ"

    if "ソケット" in text:
        return "ソケット"

    if "キャップ" in text:
        return "キャップ"

    if "掃除口" in text:
        return "掃除口"

    if text:
        return text

    return "(継手種類不明)"


# ------------------------------------------------------------
# Extract
# ------------------------------------------------------------

def extract_fittings(model):

    fittings = model.by_type(
        "IfcPipeFitting"
    )

    rows = []

    for fitting in fittings:

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

        # Preserve actual IFC value.
        raw_predefined_type = safe_text(
            getattr(
                fitting,
                "PredefinedType",
                None,
            )
        )

        type_info = get_type_info(
            fitting
        )

        system = get_system_info(
            fitting
        )

        ports = get_ports(
            fitting
        )

        port_count = len(ports)

        material_name = get_material_name(
            fitting
        )

        connection_size = (
            get_fitting_connection_diameters(
                fitting
            )
        )

        connection_diameters = (
            connection_size[
                "diameters"
            ]
        )


        fitting_category = classify_fitting(
            type_info["name"]
        )

        warning_parts = []

        if not type_info["name"]:
            warning_parts.append(
                "TypeNameなし"
            )

        if (
            raw_predefined_type
            in ("", "NOTDEFINED")
        ):
            warning_parts.append(
                "PredefinedType未定義"
            )

        if system["count"] == 0:
            warning_parts.append(
                "系統なし"
            )

        elif system["count"] > 1:
            warning_parts.append(
                "複数系統"
            )

        if port_count == 0:
            warning_parts.append(
                "Portなし"
            )

        if (
            connection_size[
                "completeness"
            ]
            == "PARTIAL"
        ):
            warning_parts.append(
                "径情報一部不足"
            )

        elif (
            connection_size[
                "completeness"
            ]
            == "NONE"
        ):
            warning_parts.append(
                "径情報なし"
            )

        row = {
            "GlobalId": global_id,

            "Name": name,

            "ObjectType": object_type,

            "PredefinedType":
                raw_predefined_type,

            "TypeName":
                type_info["name"],

            "継手種類":
                fitting_category,

            "階":
                get_storey(fitting),

            "系統コード":
                system["names"],

            "系統名称":
                system["object_types"],

            "IFC系統分類":
                system["predefined_types"],

            "系統所属数":
                system["count"],

            "Material":
                material_name,

            "PortCount":
                port_count,

            "接続径1_mm":
                connection_diameters[0],

            "接続径2_mm":
                connection_diameters[1],

            "接続径3_mm":
                connection_diameters[2],

            "径情報完全性":
                connection_size[
                    "completeness"
                ],

            "径取得元":
                connection_size[
                    "source"
                ],

            "数量_個":
                1,

            "Warning":
                " | ".join(
                    warning_parts
                ),



        }

        rows.append(row)

    return rows


# ------------------------------------------------------------
# Write detail CSV
# ------------------------------------------------------------

def write_detail(rows):

    DETAIL_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "GlobalId",
        "Name",
        "ObjectType",
        "PredefinedType",
        "TypeName",
        "継手種類",
        "階",
        "系統コード",
        "系統名称",
        "IFC系統分類",
        "系統所属数",
        "Material",
        "PortCount",

        "接続径1_mm",
        "接続径2_mm",
        "接続径3_mm",
        "径情報完全性",
        "径取得元",

        "数量_個",
        "Warning",
    ]

    with DETAIL_FILE.open(
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


# ------------------------------------------------------------
# Aggregate
# ------------------------------------------------------------

def aggregate_fittings(rows):
    """
    Aggregate fitting quantity by:

        Storey
        System code
        System name
        IFC system classification
        Fitting category
        Original TypeName
        Port count

    The original TypeName is retained as provenance.
    """

    groups = defaultdict(int)

    for row in rows:

        key = (
            row["階"]
            or "(階不明)",

            row["系統コード"]
            or "(系統コード不明)",

            row["系統名称"]
            or "(系統不明)",

            row["IFC系統分類"]
            or "(分類不明)",

            row["継手種類"],

            row["TypeName"],

            row["PortCount"],
        )

        groups[key] += 1

    summary = []

    for key, count in groups.items():

        (
            storey,
            system_code,
            system_name,
            ifc_system_type,
            fitting_category,
            type_name,
            port_count,
        ) = key

        summary.append(
            {
                "階": storey,

                "系統コード":
                    system_code,

                "系統名称":
                    system_name,

                "IFC系統分類":
                    ifc_system_type,

                "継手種類":
                    fitting_category,

                "TypeName":
                    type_name,

                "PortCount":
                    port_count,

                "数量_個":
                    count,
            }
        )

    summary.sort(
        key=lambda row: (
            row["階"],
            row["系統名称"],
            row["継手種類"],
            row["PortCount"],
        )
    )

    return summary


# ------------------------------------------------------------
# Write summary CSV
# ------------------------------------------------------------

def write_summary(rows):

    SUMMARY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "階",
        "系統コード",
        "系統名称",
        "IFC系統分類",
        "継手種類",
        "TypeName",
        "PortCount",
        "数量_個",
    ]

    with SUMMARY_FILE.open(
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


# ------------------------------------------------------------
# Console summary
# ------------------------------------------------------------

def print_summary(
    detail_rows,
    summary_rows,
):

    type_counter = Counter()
    port_counter = Counter()
    storey_counter = Counter()

    warning_counter = Counter()

    for row in detail_rows:

        type_counter[
            row["継手種類"]
        ] += 1

        port_counter[
            row["PortCount"]
        ] += 1

        storey_counter[
            row["階"]
            or "(階不明)"
        ] += 1

        if row["Warning"]:

            for warning in (
                row["Warning"].split(" | ")
            ):

                warning_counter[
                    warning
                ] += 1

    print()
    print("=" * 70)
    print(
        "ENMA-WG MEP Quantity Takeoff"
    )
    print(
        "Tokyo Summit 2026 PoC - "
        "Step 1 / Pipe Fittings"
    )
    print("=" * 70)

    print(
        f"Pipe fittings : "
        f"{len(detail_rows)}"
    )

    print(
        f"Summary rows  : "
        f"{len(summary_rows)}"
    )

    print()

    print("--- Fitting quantity ---")

    for name, count in (
        type_counter.most_common()
    ):

        print(
            f"{count:>5}  {name}"
        )

    print()

    print("--- Port structure ---")

    for port_count in sorted(
        port_counter
    ):

        print(
            f"{port_counter[port_count]:>5}  "
            f"{port_count} ports"
        )

    print()

    print("--- Storey ---")

    for storey, count in (
        storey_counter.most_common()
    ):

        print(
            f"{count:>5}  {storey}"
        )

    print()

    print("--- Warnings ---")

    if warning_counter:

        for warning, count in (
            warning_counter.most_common()
        ):

            print(
                f"{count:>5}  {warning}"
            )

    else:
        print("    0  None")

    print()

    print(
        f"Detail CSV  : {DETAIL_FILE}"
    )

    print(
        f"Summary CSV : {SUMMARY_FILE}"
    )

    print("=" * 70)


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    print(
        f"IFC    : {IFC_FILE}"
    )

    print(
        f"Detail : {DETAIL_FILE}"
    )

    print(
        f"Summary: {SUMMARY_FILE}"
    )

    if not IFC_FILE.exists():

        raise FileNotFoundError(
            f"IFC file not found: "
            f"{IFC_FILE}"
        )

    model = ifcopenshell.open(
        str(IFC_FILE)
    )

    detail_rows = extract_fittings(
        model
    )

    write_detail(
        detail_rows
    )

    summary_rows = aggregate_fittings(
        detail_rows
    )

    write_summary(
        summary_rows
    )

    print_summary(
        detail_rows,
        summary_rows,
    )


if __name__ == "__main__":
    main()