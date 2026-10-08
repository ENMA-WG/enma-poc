"""
inspect_supply_pipe_connections.py

ENMA-WG
Diagnostic script for tracing connections from "00_供給" pipe segments.

目的
----
営繕BIMモデル_EM.ifc から、
Name に "00_供給" を含む IfcPipeSegment を抽出し、
その配管に関連する IfcDistributionPort と接続先要素を追跡する。

調査対象
--------
- IfcRelConnectsPortToElement
- IfcRelConnectsPorts
- IfcRelConnectsElements
- IfcDistributionPort
- 接続先要素の Name / ObjectType / PredefinedType / Property

このスクリプトは診断用。
IFCモデルによってConnectivityの表現方法が異なるため、
複数の経路を確認する。
"""

from pathlib import Path
from collections import defaultdict

import ifcopenshell
import ifcopenshell.util.element


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

IFC_PATH = (
    PROJECT_ROOT
    / "data"
    / "営繕BIMモデル_EM.ifc"
)


# ============================================================
# Settings
# ============================================================

TARGET_KEYWORD = "00_供給"

MAX_PROPERTY_LINES = 30


# ============================================================
# Utility
# ============================================================

def safe_text(value):
    if value is None:
        return ""

    if hasattr(value, "wrappedValue"):
        value = value.wrappedValue

    return str(value)


def entity_label(entity):
    if entity is None:
        return "(none)"

    name = safe_text(
        getattr(
            entity,
            "Name",
            None,
        )
    )

    return (
        f"{entity.is_a()} "
        f"#{entity.id()} "
        f"Name='{name}'"
    )


def get_predefined_type(entity):
    value = getattr(
        entity,
        "PredefinedType",
        None,
    )

    return safe_text(value)


# ============================================================
# Property output
# ============================================================

def print_properties(
    entity,
    indent="      ",
):
    try:
        psets = (
            ifcopenshell.util.element
            .get_psets(entity)
        )
    except Exception as exc:
        print(
            f"{indent}[Property read failed] "
            f"{exc}"
        )
        return

    property_lines = []

    for pset_name, properties in psets.items():

        if not isinstance(
            properties,
            dict,
        ):
            continue

        for prop_name, value in properties.items():

            if prop_name == "id":
                continue

            if isinstance(
                value,
                dict,
            ):
                continue

            text = safe_text(value)

            if not text:
                continue

            property_lines.append(
                (
                    pset_name,
                    prop_name,
                    text,
                )
            )

    if not property_lines:
        print(
            f"{indent}(no properties)"
        )
        return

    for (
        pset_name,
        prop_name,
        value,
    ) in property_lines[
        :MAX_PROPERTY_LINES
    ]:

        print(
            f"{indent}"
            f"{pset_name}."
            f"{prop_name}"
            f" = {value}"
        )

    if (
        len(property_lines)
        > MAX_PROPERTY_LINES
    ):
        print(
            f"{indent}"
            f"... "
            f"{len(property_lines) - MAX_PROPERTY_LINES} "
            f"more properties"
        )


# ============================================================
# Build connectivity indexes
# ============================================================

def build_connectivity_indexes(model):

    # Port -> Element
    port_to_elements = defaultdict(list)

    # Element -> Port
    element_to_ports = defaultdict(list)

    # Port -> connected Port
    port_to_ports = defaultdict(list)

    # Element -> connected Element
    element_to_elements = defaultdict(list)

    # --------------------------------------------------------
    # IfcRelConnectsPortToElement
    # --------------------------------------------------------

    for rel in model.by_type(
        "IfcRelConnectsPortToElement"
    ):

        port = getattr(
            rel,
            "RelatingPort",
            None,
        )

        element = getattr(
            rel,
            "RelatedElement",
            None,
        )

        if (
            port is not None
            and element is not None
        ):

            port_to_elements[
                port.id()
            ].append(
                element
            )

            element_to_ports[
                element.id()
            ].append(
                port
            )

    # --------------------------------------------------------
    # IfcRelConnectsPorts
    # --------------------------------------------------------

    for rel in model.by_type(
        "IfcRelConnectsPorts"
    ):

        relating_port = getattr(
            rel,
            "RelatingPort",
            None,
        )

        related_port = getattr(
            rel,
            "RelatedPort",
            None,
        )

        if (
            relating_port is None
            or related_port is None
        ):
            continue

        port_to_ports[
            relating_port.id()
        ].append(
            related_port
        )

        port_to_ports[
            related_port.id()
        ].append(
            relating_port
        )

    # --------------------------------------------------------
    # IfcRelConnectsElements
    # --------------------------------------------------------

    for rel in model.by_type(
        "IfcRelConnectsElements"
    ):

        relating_element = getattr(
            rel,
            "RelatingElement",
            None,
        )

        related_element = getattr(
            rel,
            "RelatedElement",
            None,
        )

        if (
            relating_element is None
            or related_element is None
        ):
            continue

        element_to_elements[
            relating_element.id()
        ].append(
            related_element
        )

        element_to_elements[
            related_element.id()
        ].append(
            relating_element
        )

    return {
        "port_to_elements":
            port_to_elements,

        "element_to_ports":
            element_to_ports,

        "port_to_ports":
            port_to_ports,

        "element_to_elements":
            element_to_elements,
    }


# ============================================================
# Resolve owning element of a port
# ============================================================

def get_port_elements(
    port,
    indexes,
):
    result = []

    seen = set()

    # --------------------------------------------------------
    # Index created from IfcRelConnectsPortToElement
    # --------------------------------------------------------

    for element in indexes[
        "port_to_elements"
    ].get(
        port.id(),
        [],
    ):

        if element.id() not in seen:

            seen.add(
                element.id()
            )

            result.append(
                element
            )

    # --------------------------------------------------------
    # IFC inverse relation fallback
    # --------------------------------------------------------

    try:

        for rel in getattr(
            port,
            "ContainedIn",
            [],
        ):

            element = getattr(
                rel,
                "RelatedElement",
                None,
            )

            if (
                element is not None
                and element.id()
                not in seen
            ):

                seen.add(
                    element.id()
                )

                result.append(
                    element
                )

    except Exception:
        pass

    return result


# ============================================================
# Print element
# ============================================================

def print_element_detail(
    element,
    indent="      ",
):
    print(
        f"{indent}Class          : "
        f"{element.is_a()}"
    )

    print(
        f"{indent}STEP id        : "
        f"#{element.id()}"
    )

    print(
        f"{indent}GlobalId       : "
        f"{safe_text(getattr(element, 'GlobalId', None))}"
    )

    print(
        f"{indent}Name           : "
        f"{safe_text(getattr(element, 'Name', None))}"
    )

    print(
        f"{indent}ObjectType     : "
        f"{safe_text(getattr(element, 'ObjectType', None))}"
    )

    print(
        f"{indent}PredefinedType : "
        f"{get_predefined_type(element)}"
    )

    print(
        f"{indent}Properties:"
    )

    print_properties(
        element,
        indent=indent + "  ",
    )


# ============================================================
# Trace one pipe
# ============================================================

def trace_pipe(
    pipe,
    indexes,
):
    print()
    print("=" * 78)

    print(
        f"TARGET PIPE #{pipe.id()}"
    )

    print("=" * 78)

    print_element_detail(
        pipe,
        indent="  ",
    )

    # --------------------------------------------------------
    # Ports belonging to Pipe
    # --------------------------------------------------------

    ports = indexes[
        "element_to_ports"
    ].get(
        pipe.id(),
        [],
    )

    print()
    print(
        f"  Ports attached to pipe : "
        f"{len(ports)}"
    )

    if not ports:

        print(
            "    No IfcDistributionPort "
            "found through "
            "IfcRelConnectsPortToElement."
        )

    # --------------------------------------------------------
    # Trace each port
    # --------------------------------------------------------

    for port_index, port in enumerate(
        ports,
        start=1,
    ):

        print()
        print(
            f"  ------------------------------------------------------------"
        )

        print(
            f"  PIPE PORT {port_index}"
        )

        print(
            f"  ------------------------------------------------------------"
        )

        print(
            f"    {entity_label(port)}"
        )

        print(
            "    FlowDirection   : "
            f"{safe_text(getattr(port, 'FlowDirection', None))}"
        )

        print(
            "    PredefinedType  : "
            f"{safe_text(getattr(port, 'PredefinedType', None))}"
        )

        print(
            "    SystemType      : "
            f"{safe_text(getattr(port, 'SystemType', None))}"
        )

        connected_ports = indexes[
            "port_to_ports"
        ].get(
            port.id(),
            [],
        )

        print(
            f"    Connected ports : "
            f"{len(connected_ports)}"
        )

        # ----------------------------------------------------
        # Connected ports
        # ----------------------------------------------------

        for connected_index, connected_port in enumerate(
            connected_ports,
            start=1,
        ):

            print()
            print(
                f"    Connected Port "
                f"{connected_index}:"
            )

            print(
                f"      "
                f"{entity_label(connected_port)}"
            )

            print(
                "      FlowDirection : "
                f"{safe_text(getattr(connected_port, 'FlowDirection', None))}"
            )

            print(
                "      SystemType    : "
                f"{safe_text(getattr(connected_port, 'SystemType', None))}"
            )

            connected_elements = (
                get_port_elements(
                    connected_port,
                    indexes,
                )
            )

            print(
                f"      Owning elements : "
                f"{len(connected_elements)}"
            )

            for element_index, element in enumerate(
                connected_elements,
                start=1,
            ):

                print()
                print(
                    f"      CONNECTED ELEMENT "
                    f"{element_index}"
                )

                print_element_detail(
                    element,
                    indent="        ",
                )

    # --------------------------------------------------------
    # Direct element-to-element connection
    # --------------------------------------------------------

    direct_elements = indexes[
        "element_to_elements"
    ].get(
        pipe.id(),
        [],
    )

    print()
    print(
        "  Direct IfcRelConnectsElements "
        f"connections : {len(direct_elements)}"
    )

    for element_index, element in enumerate(
        direct_elements,
        start=1,
    ):

        print()
        print(
            f"  DIRECT CONNECTED ELEMENT "
            f"{element_index}"
        )

        print_element_detail(
            element,
            indent="    ",
        )


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 78)

    print(
        "ENMA-WG Supply Pipe Connection Inspector"
    )

    print(
        f"Target keyword : {TARGET_KEYWORD}"
    )

    print("=" * 78)

    print(
        f"IFC : {IFC_PATH}"
    )

    if not IFC_PATH.exists():

        print()
        print(
            "[ERROR] IFC file not found."
        )

        return 1

    # --------------------------------------------------------
    # Open IFC
    # --------------------------------------------------------

    print()
    print(
        "[1/4] Opening IFC..."
    )

    model = ifcopenshell.open(
        str(IFC_PATH)
    )

    print(
        f"      Schema : "
        f"{model.schema}"
    )

    # --------------------------------------------------------
    # Connectivity indexes
    # --------------------------------------------------------

    print(
        "[2/4] Building connectivity indexes..."
    )

    indexes = (
        build_connectivity_indexes(
            model
        )
    )

    print(
        "      IfcRelConnectsPortToElement : "
        f"{len(model.by_type('IfcRelConnectsPortToElement'))}"
    )

    print(
        "      IfcRelConnectsPorts         : "
        f"{len(model.by_type('IfcRelConnectsPorts'))}"
    )

    print(
        "      IfcRelConnectsElements      : "
        f"{len(model.by_type('IfcRelConnectsElements'))}"
    )

    # --------------------------------------------------------
    # Find target pipes
    # --------------------------------------------------------

    print(
        "[3/4] Searching target pipes..."
    )

    pipes = model.by_type(
        "IfcPipeSegment"
    )

    targets = []

    for pipe in pipes:

        name = safe_text(
            getattr(
                pipe,
                "Name",
                None,
            )
        )

        object_type = safe_text(
            getattr(
                pipe,
                "ObjectType",
                None,
            )
        )

        if (
            TARGET_KEYWORD in name
            or TARGET_KEYWORD
            in object_type
        ):

            targets.append(
                pipe
            )

    print(
        f"      IfcPipeSegment total : "
        f"{len(pipes)}"
    )

    print(
        f"      Target pipes         : "
        f"{len(targets)}"
    )

    if not targets:

        print()
        print(
            "[WARN] No target pipe found."
        )

        print(
            "       Name/ObjectTypeに "
            f"'{TARGET_KEYWORD}' "
            "が存在するか確認してください。"
        )

        return 0

    # --------------------------------------------------------
    # Trace
    # --------------------------------------------------------

    print(
        "[4/4] Tracing connections..."
    )

    for pipe in targets:

        trace_pipe(
            pipe,
            indexes,
        )

    print()
    print("=" * 78)

    print(
        f"Done. "
        f"{len(targets)} target pipe(s) inspected."
    )

    print("=" * 78)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())