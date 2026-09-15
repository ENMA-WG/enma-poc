"""
inspect_fitting_sizes.py

ENMA-WG Tokyo Summit 2026 PoC
Diagnostic tool for IfcPipeFitting port / size / connectivity inspection.

Purpose:
    Inspect all IfcPipeFitting elements and their IfcDistributionPorts.

    For each fitting port, inspect:
        - Fitting information
        - Storey
        - Distribution System
        - Port name / description
        - FlowDirection
        - Port PredefinedType / SystemType where available
        - NominalDiameter-like properties
        - All port properties
        - Connected port
        - Connected element
        - Connected element type
        - Connected pipe diameter information

Output:
    output/fitting_port_inventory.csv

Important:
    This is a diagnostic script.
    Do not use inferred diameter values for production quantity takeoff
    until the actual IFC representation has been verified.
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

IFC_FILE = Path(
    "data/営繕BIMモデル_EM.ifc"
)

OUTPUT_FILE = Path(
    "output/fitting_port_inventory.csv"
)


# ------------------------------------------------------------
# Utility
# ------------------------------------------------------------

def safe_text(value):
    if value is None:
        return ""

    # IFC wrapped value
    if hasattr(value, "wrappedValue"):
        return safe_text(value.wrappedValue)

    return str(value).strip()


def join_unique(values):
    result = []

    for value in values:
        text = safe_text(value)

        if text and text not in result:
            result.append(text)

    return " | ".join(result)


def flatten_value(value):
    """
    Convert IFC/Pset values into CSV-friendly text.
    """

    if value is None:
        return ""

    if hasattr(value, "wrappedValue"):
        return safe_text(value.wrappedValue)

    if isinstance(
        value,
        (str, int, float, bool),
    ):
        return str(value)

    if isinstance(
        value,
        (list, tuple),
    ):
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

    try:
        container = (
            ifcopenshell.util.element
            .get_container(element)
        )
    except Exception:
        container = None

    current = container

    while current is not None:

        if current.is_a(
            "IfcBuildingStorey"
        ):
            return safe_text(
                getattr(
                    current,
                    "Name",
                    None,
                )
            )

        try:
            current = (
                ifcopenshell.util.element
                .get_container(current)
            )
        except Exception:
            break

    return ""


# ------------------------------------------------------------
# Element type
# ------------------------------------------------------------

def get_type_name(element):

    if element is None:
        return ""

    try:
        element_type = (
            ifcopenshell.util.element
            .get_type(element)
        )
    except Exception:
        element_type = None

    if element_type is None:
        return ""

    return safe_text(
        getattr(
            element_type,
            "Name",
            None,
        )
    )


# ------------------------------------------------------------
# Distribution system
# ------------------------------------------------------------

def get_system_info(element):

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
            getattr(
                system,
                "Name",
                None,
            )
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

        "names":
            join_unique(names),

        "object_types":
            join_unique(object_types),

        "predefined_types":
            join_unique(
                predefined_types
            ),
    }


# ------------------------------------------------------------
# Ports belonging to an element
# ------------------------------------------------------------

def get_ports(element):
    """
    Return unique IfcDistributionPorts belonging
    to an element.

    Checks:
        - IfcRelNests
        - IfcRelConnectsPortToElement / HasPorts
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
# Owner element of a port
# ------------------------------------------------------------

def get_port_owner(port):
    """
    Find the element that owns / nests the port.
    """

    # IFC4: port nested under distribution element
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

    # IFC2x3 / compatibility
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


# ------------------------------------------------------------
# Connected port
# ------------------------------------------------------------

def get_connected_ports(port):
    """
    Return ports connected through IfcRelConnectsPorts.

    Both ConnectedTo and ConnectedFrom are checked.
    """

    connected = []

    # This port is RelatingPort
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

        if other is not None:
            connected.append(other)

    # This port is RelatedPort
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

        if other is not None:
            connected.append(other)

    unique = {}

    for item in connected:
        unique[item.id()] = item

    return list(unique.values())


# ------------------------------------------------------------
# Pset inventory
# ------------------------------------------------------------

def get_psets_safe(element):

    if element is None:
        return {}

    try:
        return (
            ifcopenshell.util.element
            .get_psets(element)
        )
    except Exception:
        return {}


def get_property_inventory(element):
    """
    Flatten all Pset / Qto properties.
    """

    psets = get_psets_safe(
        element
    )

    items = []

    for pset_name in sorted(
        psets.keys()
    ):

        properties = psets[
            pset_name
        ]

        if not isinstance(
            properties,
            dict,
        ):
            continue

        for prop_name in sorted(
            properties.keys()
        ):

            if prop_name == "id":
                continue

            value = properties[
                prop_name
            ]

            items.append(
                f"{pset_name}."
                f"{prop_name}="
                f"{flatten_value(value)}"
            )

    return "; ".join(items)


# ------------------------------------------------------------
# Diameter-like property search
# ------------------------------------------------------------

DIAMETER_KEYWORDS = (
    "diameter",
    "nominaldiameter",
    "nominal diameter",
    "nominal_diameter",
    "outerdiameter",
    "innerdiameter",
    "径",
    "口径",
)


def get_diameter_properties(element):
    """
    Search all Psets/Qtos for diameter-like
    property names.

    This intentionally does NOT assume where
    NominalDiameter is stored.
    """

    psets = get_psets_safe(
        element
    )

    matches = []

    for pset_name, properties in (
        psets.items()
    ):

        if not isinstance(
            properties,
            dict,
        ):
            continue

        for prop_name, value in (
            properties.items()
        ):

            if prop_name == "id":
                continue

            search_name = (
                str(prop_name).lower()
            )

            if any(
                keyword.lower()
                in search_name
                for keyword
                in DIAMETER_KEYWORDS
            ):

                matches.append(
                    (
                        pset_name,
                        prop_name,
                        flatten_value(
                            value
                        ),
                    )
                )

    return matches


def format_diameter_properties(
    matches
):
    """
    Example:
        Pset_X.NominalDiameter=50
        | Pset_Y.OuterDiameter=60.5
    """

    return " | ".join(
        f"{pset}.{prop}={value}"
        for pset, prop, value
        in matches
    )


def first_diameter_value(matches):
    """
    Diagnostic convenience column only.

    Do NOT treat this as authoritative yet.
    """

    priority = (
        "nominaldiameter",
        "nominal diameter",
        "nominal_diameter",
        "outerdiameter",
        "diameter",
        "径",
        "口径",
    )

    for keyword in priority:

        for (
            pset_name,
            prop_name,
            value,
        ) in matches:

            if (
                keyword.lower()
                in prop_name.lower()
            ):
                return value

    return ""


# ------------------------------------------------------------
# Direct port attributes
# ------------------------------------------------------------

def get_port_attribute(
    port,
    attribute_name,
):

    value = getattr(
        port,
        attribute_name,
        None,
    )

    return safe_text(value)


# ------------------------------------------------------------
# Fitting classification
# ------------------------------------------------------------

def classify_fitting(type_name):

    text = safe_text(type_name)

    if "エルボ_冷媒管" in text:
        return "冷媒管エルボ"

    if "エルボ" in text:
        return "エルボ"

    if (
        "径違い90°" in text
        and "Y" in text
    ):
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

    return text or "(継手種類不明)"


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    print()
    print("=" * 72)
    print(
        "ENMA-WG Fitting Size / Port Inspection"
    )
    print(
        "Tokyo Summit 2026 PoC"
    )
    print("=" * 72)

    print(
        f"IFC : {IFC_FILE}"
    )

    if not IFC_FILE.exists():

        raise FileNotFoundError(
            f"IFC file not found: "
            f"{IFC_FILE}"
        )

    model = ifcopenshell.open(
        str(IFC_FILE)
    )

    fittings = model.by_type(
        "IfcPipeFitting"
    )

    print()
    print(
        f"IfcPipeFitting count: "
        f"{len(fittings)}"
    )

    rows = []

    port_count_counter = Counter()

    flow_direction_counter = Counter()

    connected_class_counter = Counter()

    port_diameter_counter = Counter()

    connected_diameter_counter = Counter()

    unconnected_ports = 0

    total_ports = 0

    # --------------------------------------------------------
    # Each fitting
    # --------------------------------------------------------

    for fitting_index, fitting in enumerate(
        fittings,
        start=1,
    ):

        fitting_type_name = (
            get_type_name(fitting)
        )

        fitting_category = (
            classify_fitting(
                fitting_type_name
            )
        )

        storey = get_storey(
            fitting
        )

        system = get_system_info(
            fitting
        )

        ports = get_ports(
            fitting
        )

        port_count_counter[
            len(ports)
        ] += 1

        print(
            f"[{fitting_index:>3}/"
            f"{len(fittings)}] "
            f"{fitting_category:<18} "
            f"ports={len(ports)}"
        )

        # ----------------------------------------------------
        # Each port
        # ----------------------------------------------------

        for port_index, port in enumerate(
            ports,
            start=1,
        ):

            total_ports += 1

            flow_direction = (
                get_port_attribute(
                    port,
                    "FlowDirection",
                )
            )

            port_predefined_type = (
                get_port_attribute(
                    port,
                    "PredefinedType",
                )
            )

            port_system_type = (
                get_port_attribute(
                    port,
                    "SystemType",
                )
            )

            flow_direction_counter[
                flow_direction
                or "(blank)"
            ] += 1

            # -----------------------------------------------
            # Port properties / diameter
            # -----------------------------------------------

            port_diameter_matches = (
                get_diameter_properties(
                    port
                )
            )

            port_diameter_text = (
                format_diameter_properties(
                    port_diameter_matches
                )
            )

            port_diameter_value = (
                first_diameter_value(
                    port_diameter_matches
                )
            )

            if port_diameter_value:

                port_diameter_counter[
                    port_diameter_value
                ] += 1

            # -----------------------------------------------
            # Connectivity
            # -----------------------------------------------

            connected_ports = (
                get_connected_ports(
                    port
                )
            )

            if not connected_ports:

                unconnected_ports += 1

                # Still output one row for the port
                connected_ports_for_output = [
                    None
                ]

            else:

                connected_ports_for_output = (
                    connected_ports
                )

            # -----------------------------------------------
            # One row per port x connection
            # -----------------------------------------------

            for connected_port in (
                connected_ports_for_output
            ):

                if connected_port is None:

                    connected_port_guid = ""
                    connected_port_name = ""
                    connected_flow_direction = ""
                    connected_element = None

                    connected_port_diameter_text = ""
                    connected_port_diameter_value = ""

                else:

                    connected_port_guid = (
                        safe_text(
                            getattr(
                                connected_port,
                                "GlobalId",
                                None,
                            )
                        )
                    )

                    connected_port_name = (
                        safe_text(
                            getattr(
                                connected_port,
                                "Name",
                                None,
                            )
                        )
                    )

                    connected_flow_direction = (
                        get_port_attribute(
                            connected_port,
                            "FlowDirection",
                        )
                    )

                    connected_element = (
                        get_port_owner(
                            connected_port
                        )
                    )

                    connected_port_matches = (
                        get_diameter_properties(
                            connected_port
                        )
                    )

                    connected_port_diameter_text = (
                        format_diameter_properties(
                            connected_port_matches
                        )
                    )

                    connected_port_diameter_value = (
                        first_diameter_value(
                            connected_port_matches
                        )
                    )

                # -------------------------------------------
                # Connected element
                # -------------------------------------------

                if connected_element is None:

                    connected_class = ""
                    connected_guid = ""
                    connected_name = ""
                    connected_type_name = ""

                    connected_element_diameter_text = ""
                    connected_element_diameter_value = ""

                else:

                    connected_class = (
                        connected_element.is_a()
                    )

                    connected_guid = (
                        safe_text(
                            getattr(
                                connected_element,
                                "GlobalId",
                                None,
                            )
                        )
                    )

                    connected_name = (
                        safe_text(
                            getattr(
                                connected_element,
                                "Name",
                                None,
                            )
                        )
                    )

                    connected_type_name = (
                        get_type_name(
                            connected_element
                        )
                    )

                    connected_element_matches = (
                        get_diameter_properties(
                            connected_element
                        )
                    )

                    connected_element_diameter_text = (
                        format_diameter_properties(
                            connected_element_matches
                        )
                    )

                    connected_element_diameter_value = (
                        first_diameter_value(
                            connected_element_matches
                        )
                    )

                    connected_class_counter[
                        connected_class
                    ] += 1

                    if (
                        connected_element_diameter_value
                    ):

                        connected_diameter_counter[
                            connected_element_diameter_value
                        ] += 1

                # -------------------------------------------
                # Diagnostic diameter candidate
                # -------------------------------------------

                diameter_candidate = ""

                diameter_source = ""

                if port_diameter_value:

                    diameter_candidate = (
                        port_diameter_value
                    )

                    diameter_source = (
                        "FittingPort"
                    )

                elif connected_port_diameter_value:

                    diameter_candidate = (
                        connected_port_diameter_value
                    )

                    diameter_source = (
                        "ConnectedPort"
                    )

                elif connected_element_diameter_value:

                    diameter_candidate = (
                        connected_element_diameter_value
                    )

                    diameter_source = (
                        "ConnectedElement"
                    )

                # -------------------------------------------
                # Warnings
                # -------------------------------------------

                warnings = []

                if connected_port is None:

                    warnings.append(
                        "接続先Portなし"
                    )

                if not diameter_candidate:

                    warnings.append(
                        "径候補なし"
                    )

                # -------------------------------------------
                # Row
                # -------------------------------------------

                rows.append(
                    {
                        "FittingGlobalId":
                            safe_text(
                                getattr(
                                    fitting,
                                    "GlobalId",
                                    None,
                                )
                            ),

                        "FittingName":
                            safe_text(
                                getattr(
                                    fitting,
                                    "Name",
                                    None,
                                )
                            ),

                        "FittingTypeName":
                            fitting_type_name,

                        "継手種類":
                            fitting_category,

                        "階":
                            storey,

                        "系統コード":
                            system["names"],

                        "系統名称":
                            system[
                                "object_types"
                            ],

                        "IFC系統分類":
                            system[
                                "predefined_types"
                            ],

                        "FittingPortCount":
                            len(ports),

                        "PortIndex":
                            port_index,

                        "PortGlobalId":
                            safe_text(
                                getattr(
                                    port,
                                    "GlobalId",
                                    None,
                                )
                            ),

                        "PortName":
                            safe_text(
                                getattr(
                                    port,
                                    "Name",
                                    None,
                                )
                            ),

                        "PortDescription":
                            safe_text(
                                getattr(
                                    port,
                                    "Description",
                                    None,
                                )
                            ),

                        "FlowDirection":
                            flow_direction,

                        "PortPredefinedType":
                            port_predefined_type,

                        "PortSystemType":
                            port_system_type,

                        "PortDiameterProperties":
                            port_diameter_text,

                        "PortDiameterCandidate":
                            port_diameter_value,

                        "PortProperties":
                            get_property_inventory(
                                port
                            ),

                        "ConnectedPortGlobalId":
                            connected_port_guid,

                        "ConnectedPortName":
                            connected_port_name,

                        "ConnectedPortFlowDirection":
                            connected_flow_direction,

                        "ConnectedPortDiameterProperties":
                            connected_port_diameter_text,

                        "ConnectedPortDiameterCandidate":
                            connected_port_diameter_value,

                        "ConnectedElementClass":
                            connected_class,

                        "ConnectedElementGlobalId":
                            connected_guid,

                        "ConnectedElementName":
                            connected_name,

                        "ConnectedElementTypeName":
                            connected_type_name,

                        "ConnectedElementDiameterProperties":
                            connected_element_diameter_text,

                        "ConnectedElementDiameterCandidate":
                            connected_element_diameter_value,

                        "DiameterCandidate":
                            diameter_candidate,

                        "DiameterSource":
                            diameter_source,

                        "Warning":
                            " | ".join(
                                warnings
                            ),
                    }
                )

    # --------------------------------------------------------
    # Write CSV
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "FittingGlobalId",
        "FittingName",
        "FittingTypeName",
        "継手種類",
        "階",
        "系統コード",
        "系統名称",
        "IFC系統分類",

        "FittingPortCount",
        "PortIndex",
        "PortGlobalId",
        "PortName",
        "PortDescription",
        "FlowDirection",
        "PortPredefinedType",
        "PortSystemType",

        "PortDiameterProperties",
        "PortDiameterCandidate",
        "PortProperties",

        "ConnectedPortGlobalId",
        "ConnectedPortName",
        "ConnectedPortFlowDirection",
        "ConnectedPortDiameterProperties",
        "ConnectedPortDiameterCandidate",

        "ConnectedElementClass",
        "ConnectedElementGlobalId",
        "ConnectedElementName",
        "ConnectedElementTypeName",
        "ConnectedElementDiameterProperties",
        "ConnectedElementDiameterCandidate",

        "DiameterCandidate",
        "DiameterSource",

        "Warning",
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
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)

    print()
    print(
        f"IfcPipeFitting : "
        f"{len(fittings)}"
    )

    print(
        f"Total ports    : "
        f"{total_ports}"
    )

    print(
        f"CSV rows       : "
        f"{len(rows)}"
    )

    print(
        f"Unconnected    : "
        f"{unconnected_ports}"
    )

    print()

    print(
        "--- Fitting Port Count ---"
    )

    for port_count in sorted(
        port_count_counter
    ):

        print(
            f"{port_count_counter[port_count]:>5}  "
            f"{port_count} ports"
        )

    print()

    print(
        "--- FlowDirection ---"
    )

    for value, count in (
        flow_direction_counter
        .most_common()
    ):

        print(
            f"{count:>5}  {value}"
        )

    print()

    print(
        "--- Connected Element Class ---"
    )

    if connected_class_counter:

        for value, count in (
            connected_class_counter
            .most_common()
        ):

            print(
                f"{count:>5}  {value}"
            )

    else:

        print(
            "    0  No connected elements"
        )

    print()

    print(
        "--- Fitting Port Diameter Candidate ---"
    )

    if port_diameter_counter:

        for value, count in (
            port_diameter_counter
            .most_common()
        ):

            print(
                f"{count:>5}  {value}"
            )

    else:

        print(
            "    0  No diameter properties "
            "found on fitting ports"
        )

    print()

    print(
        "--- Connected Element Diameter Candidate ---"
    )

    if connected_diameter_counter:

        for value, count in (
            connected_diameter_counter
            .most_common()
        ):

            print(
                f"{count:>5}  {value}"
            )

    else:

        print(
            "    0  No diameter properties "
            "found on connected elements"
        )

    print()

    diameter_source_counter = Counter(
        row["DiameterSource"]
        or "(none)"
        for row in rows
    )

    print(
        "--- Diameter Source ---"
    )

    for value, count in (
        diameter_source_counter
        .most_common()
    ):

        print(
            f"{count:>5}  {value}"
        )

    print()

    warning_counter = Counter()

    for row in rows:

        if not row["Warning"]:
            continue

        for warning in (
            row["Warning"]
            .split(" | ")
        ):

            warning_counter[
                warning
            ] += 1

    print(
        "--- Warnings ---"
    )

    if warning_counter:

        for value, count in (
            warning_counter
            .most_common()
        ):

            print(
                f"{count:>5}  {value}"
            )

    else:

        print(
            "    0  None"
        )

    print()

    print(
        f"CSV : {OUTPUT_FILE}"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()