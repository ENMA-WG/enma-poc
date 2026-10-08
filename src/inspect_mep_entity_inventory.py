"""
inspect_mep_entity_inventory.py

ENMA-WG MEP Entity Inventory Inspector

目的:
    IFCファイルに実際に格納されている IfcElement 系クラス、
    DistributionPort の親要素、PropertySet / Property を棚卸しする。

特に IFC2X3 + Japan-Domestic な設備利用標準について、
IFC4の設備Entity名を前提にせず、実データから構造を観察する。

Geometryは生成しない。

Usage:

    python .\src\inspect_mep_entity_inventory.py `
        ".\data\BLCJ_SampleModel_2022_MEP_Variation_01_Revit.ifc"

    python .\src\inspect_mep_entity_inventory.py `
        ".\data\BLCJ_SampleModel_2022_MEP_Variation_01_Revit.ifc" `
        --output-dir ".\output"
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import ifcopenshell


# ----------------------------------------------------------------------
# Utility
# ----------------------------------------------------------------------

def safe_text(value: Any) -> str:
    if value is None:
        return ""

    try:
        if hasattr(value, "wrappedValue"):
            value = value.wrappedValue
    except Exception:
        pass

    text = str(value)

    # CSVやコンソールが壊れにくいよう改行を除去
    text = text.replace("\r", " ").replace("\n", " ")

    return text.strip()


def truncate(text: str, length: int = 120) -> str:
    if len(text) <= length:
        return text
    return text[: length - 3] + "..."


def safe_attr(obj, name: str):
    try:
        return getattr(obj, name, None)
    except Exception:
        return None


def safe_by_type(model, entity_name: str):
    try:
        return model.by_type(entity_name)
    except Exception:
        return []


# ----------------------------------------------------------------------
# Property extraction
# ----------------------------------------------------------------------

def extract_nominal_value(prop) -> str:
    """
    IfcPropertySingleValue等から代表値を取得する。
    複雑なPropertyは型名を返す。
    """

    try:
        prop_type = prop.is_a()
    except Exception:
        return ""

    try:
        if prop_type == "IfcPropertySingleValue":
            return safe_text(prop.NominalValue)

        if prop_type == "IfcPropertyEnumeratedValue":
            values = getattr(prop, "EnumerationValues", None) or []
            return " | ".join(safe_text(v) for v in values)

        if prop_type == "IfcPropertyListValue":
            values = getattr(prop, "ListValues", None) or []
            return " | ".join(safe_text(v) for v in values)

        if prop_type == "IfcPropertyBoundedValue":
            lower = safe_text(
                getattr(prop, "LowerBoundValue", None)
            )
            upper = safe_text(
                getattr(prop, "UpperBoundValue", None)
            )
            return f"{lower} .. {upper}"

        if prop_type == "IfcPropertyReferenceValue":
            value = getattr(prop, "PropertyReference", None)

            if value is not None:
                try:
                    return f"{value.is_a()} #{value.id()}"
                except Exception:
                    return safe_text(value)

        if prop_type == "IfcPropertyTableValue":
            return "[TABLE]"

    except Exception:
        pass

    return f"[{prop_type}]"


def iter_pset_properties(pset):
    """
    IfcPropertySet の HasProperties を返す。
    """

    try:
        properties = pset.HasProperties or []
    except Exception:
        return

    for prop in properties:
        yield prop


# ----------------------------------------------------------------------
# Instance PropertySet relations
# ----------------------------------------------------------------------

def build_instance_pset_index(model):
    """
    IfcRelDefinesByProperties を利用して、
    Element STEP id -> [(pset, source)] を構築。

    source は INSTANCE。
    """

    index = defaultdict(list)

    relations = safe_by_type(
        model,
        "IfcRelDefinesByProperties",
    )

    for rel in relations:

        try:
            pdef = rel.RelatingPropertyDefinition
        except Exception:
            continue

        if pdef is None:
            continue

        try:
            pdef_type = pdef.is_a()
        except Exception:
            continue

        if pdef_type != "IfcPropertySet":
            continue

        try:
            related = rel.RelatedObjects or []
        except Exception:
            continue

        for obj in related:
            try:
                index[obj.id()].append(
                    (pdef, "INSTANCE")
                )
            except Exception:
                continue

    return index


# ----------------------------------------------------------------------
# Type PropertySet relations
# ----------------------------------------------------------------------

def build_type_index(model):
    """
    Element STEP id -> TypeObject

    IFC2X3 / IFC4 共通で IfcRelDefinesByType を利用する。
    """

    result = {}

    relations = safe_by_type(
        model,
        "IfcRelDefinesByType",
    )

    for rel in relations:

        try:
            type_object = rel.RelatingType
            related = rel.RelatedObjects or []
        except Exception:
            continue

        for obj in related:
            try:
                result[obj.id()] = type_object
            except Exception:
                continue

    return result


def get_type_psets(type_object):
    """
    TypeObject側のPropertySetを取得。
    IFC2X3 / IFC4 の HasPropertySets を利用。
    """

    if type_object is None:
        return []

    try:
        psets = type_object.HasPropertySets or []
    except Exception:
        return []

    result = []

    for pset in psets:
        try:
            if pset.is_a() == "IfcPropertySet":
                result.append((pset, "TYPE"))
        except Exception:
            continue

    return result


# ----------------------------------------------------------------------
# Port ownership
# ----------------------------------------------------------------------

def build_port_parent_index(model):
    """
    Port -> parent element をSchema非依存にできるだけ解決する。

    IFC2X3:
        IfcRelConnectsPortToElement

    IFC4:
        IfcRelNests

    さらに IfcRelAggregates も補助的に見る。
    """

    parents = defaultdict(list)

    # IFC2X3 style
    for rel in safe_by_type(
        model,
        "IfcRelConnectsPortToElement",
    ):
        try:
            port = rel.RelatingPort
            element = rel.RelatedElement

            parents[port.id()].append(
                (
                    element,
                    "IfcRelConnectsPortToElement",
                )
            )
        except Exception:
            continue

    # IFC4 style
    for rel in safe_by_type(
        model,
        "IfcRelNests",
    ):
        try:
            parent = rel.RelatingObject
            children = rel.RelatedObjects or []
        except Exception:
            continue

        for child in children:
            try:
                if child.is_a("IfcDistributionPort"):
                    parents[child.id()].append(
                        (
                            parent,
                            "IfcRelNests",
                        )
                    )
            except Exception:
                continue

    # Fallback / supplementary
    for rel in safe_by_type(
        model,
        "IfcRelAggregates",
    ):
        try:
            parent = rel.RelatingObject
            children = rel.RelatedObjects or []
        except Exception:
            continue

        for child in children:
            try:
                if child.is_a("IfcDistributionPort"):
                    parents[child.id()].append(
                        (
                            parent,
                            "IfcRelAggregates",
                        )
                    )
            except Exception:
                continue

    return parents


# ----------------------------------------------------------------------
# Element inventory
# ----------------------------------------------------------------------

def inspect_elements(model):
    """
    全 IfcElement を実クラス別に集計。
    """

    elements = safe_by_type(
        model,
        "IfcElement",
    )

    class_counter = Counter()
    object_type_counter = Counter()

    detail_rows = []

    for element in elements:

        try:
            entity_class = element.is_a()
        except Exception:
            entity_class = "UNKNOWN"

        class_counter[entity_class] += 1

        name = safe_text(
            safe_attr(element, "Name")
        )

        object_type = safe_text(
            safe_attr(element, "ObjectType")
        )

        tag = safe_text(
            safe_attr(element, "Tag")
        )

        if object_type:
            object_type_counter[
                (entity_class, object_type)
            ] += 1

        detail_rows.append({
            "StepId": element.id(),
            "GlobalId": safe_text(
                safe_attr(element, "GlobalId")
            ),
            "IfcClass": entity_class,
            "Name": name,
            "ObjectType": object_type,
            "Tag": tag,
        })

    return (
        elements,
        class_counter,
        object_type_counter,
        detail_rows,
    )


# ----------------------------------------------------------------------
# Property inventory
# ----------------------------------------------------------------------

def inspect_properties(
    elements,
    instance_psets,
    type_index,
):
    """
    PropertySet / Property の出現頻度と代表値を集計。

    INSTANCE と TYPE を区別する。
    """

    property_counter = Counter()
    pset_counter = Counter()

    samples = defaultdict(list)

    element_property_rows = []

    for element in elements:

        element_id = element.id()
        entity_class = element.is_a()

        sources = []

        # Instance Psets
        sources.extend(
            instance_psets.get(
                element_id,
                []
            )
        )

        # Type Psets
        type_object = type_index.get(
            element_id
        )

        sources.extend(
            get_type_psets(type_object)
        )

        seen_on_element = set()

        for pset, source in sources:

            pset_name = safe_text(
                safe_attr(pset, "Name")
            )

            pset_key = (
                entity_class,
                source,
                pset_name,
            )

            # 同じ要素で重複カウントしない
            if pset_key not in seen_on_element:
                pset_counter[pset_key] += 1
                seen_on_element.add(pset_key)

            for prop in iter_pset_properties(pset):

                prop_name = safe_text(
                    safe_attr(prop, "Name")
                )

                try:
                    prop_type = prop.is_a()
                except Exception:
                    prop_type = ""

                value = extract_nominal_value(
                    prop
                )

                key = (
                    entity_class,
                    source,
                    pset_name,
                    prop_name,
                    prop_type,
                )

                property_counter[key] += 1

                if value:
                    sample_list = samples[key]

                    if (
                        value not in sample_list
                        and len(sample_list) < 5
                    ):
                        sample_list.append(value)

                element_property_rows.append({
                    "StepId": element_id,
                    "GlobalId": safe_text(
                        safe_attr(
                            element,
                            "GlobalId",
                        )
                    ),
                    "IfcClass": entity_class,
                    "Name": safe_text(
                        safe_attr(
                            element,
                            "Name",
                        )
                    ),
                    "ObjectType": safe_text(
                        safe_attr(
                            element,
                            "ObjectType",
                        )
                    ),
                    "Source": source,
                    "PsetName": pset_name,
                    "PropertyName": prop_name,
                    "PropertyType": prop_type,
                    "Value": value,
                })

    return (
        pset_counter,
        property_counter,
        samples,
        element_property_rows,
    )


# ----------------------------------------------------------------------
# Port inventory
# ----------------------------------------------------------------------

def inspect_ports(model, port_parents):

    ports = safe_by_type(
        model,
        "IfcDistributionPort",
    )

    parent_class_counter = Counter()
    relation_counter = Counter()

    rows = []

    unresolved = 0
    multiple = 0

    for port in ports:

        parent_entries = port_parents.get(
            port.id(),
            [],
        )

        if not parent_entries:
            unresolved += 1

            rows.append({
                "PortStepId": port.id(),
                "PortGlobalId": safe_text(
                    safe_attr(
                        port,
                        "GlobalId",
                    )
                ),
                "PortName": safe_text(
                    safe_attr(
                        port,
                        "Name",
                    )
                ),
                "ParentStepId": "",
                "ParentGlobalId": "",
                "ParentIfcClass": "",
                "ParentName": "",
                "ParentObjectType": "",
                "Relation": "",
                "Status": "UNRESOLVED",
            })

            continue

        if len(parent_entries) > 1:
            multiple += 1

        for parent, relation_name in parent_entries:

            try:
                parent_class = parent.is_a()
            except Exception:
                parent_class = "UNKNOWN"

            parent_class_counter[
                parent_class
            ] += 1

            relation_counter[
                relation_name
            ] += 1

            rows.append({
                "PortStepId": port.id(),
                "PortGlobalId": safe_text(
                    safe_attr(
                        port,
                        "GlobalId",
                    )
                ),
                "PortName": safe_text(
                    safe_attr(
                        port,
                        "Name",
                    )
                ),
                "ParentStepId": parent.id(),
                "ParentGlobalId": safe_text(
                    safe_attr(
                        parent,
                        "GlobalId",
                    )
                ),
                "ParentIfcClass": parent_class,
                "ParentName": safe_text(
                    safe_attr(
                        parent,
                        "Name",
                    )
                ),
                "ParentObjectType": safe_text(
                    safe_attr(
                        parent,
                        "ObjectType",
                    )
                ),
                "Relation": relation_name,
                "Status":
                    "MULTIPLE"
                    if len(parent_entries) > 1
                    else "OK",
            })

    return {
        "ports": ports,
        "parent_class_counter":
            parent_class_counter,
        "relation_counter":
            relation_counter,
        "unresolved": unresolved,
        "multiple": multiple,
        "rows": rows,
    }


# ----------------------------------------------------------------------
# CSV writers
# ----------------------------------------------------------------------

def write_csv(
    path: Path,
    fieldnames,
    rows,
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
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


# ----------------------------------------------------------------------
# Main inspection
# ----------------------------------------------------------------------

def inspect_ifc(
    ifc_path: Path,
    output_dir: Path,
):

    print("=" * 78)
    print(
        "ENMA-WG MEP Entity Inventory Inspector"
    )
    print("=" * 78)

    print(f"IFC       : {ifc_path.resolve()}")

    size_mb = (
        ifc_path.stat().st_size
        / 1024
        / 1024
    )

    print(f"File size : {size_mb:.2f} MB")
    print()
    print("Opening IFC...")

    model = ifcopenshell.open(
        str(ifc_path)
    )

    print(f"Schema    : {model.schema}")
    print()

    # --------------------------------------------------------------
    # Elements
    # --------------------------------------------------------------

    (
        elements,
        class_counter,
        object_type_counter,
        element_rows,
    ) = inspect_elements(model)

    print("=" * 78)
    print(
        f"IfcElement inventory : {len(elements)}"
    )
    print("=" * 78)

    for name, count in (
        class_counter.most_common()
    ):
        print(
            f"{count:>8}  {name}"
        )

    # --------------------------------------------------------------
    # ObjectType
    # --------------------------------------------------------------

    print()
    print("=" * 78)
    print("Representative ObjectType")
    print("=" * 78)

    for (
        entity_class,
        object_type,
    ), count in object_type_counter.most_common(80):

        print(
            f"{count:>8}  "
            f"{entity_class:<30} "
            f"{truncate(object_type, 70)}"
        )

    # --------------------------------------------------------------
    # Ports
    # --------------------------------------------------------------

    port_parent_index = (
        build_port_parent_index(model)
    )

    port_info = inspect_ports(
        model,
        port_parent_index,
    )

    print()
    print("=" * 78)
    print("DistributionPort ownership")
    print("=" * 78)

    print(
        f"Ports             : "
        f"{len(port_info['ports'])}"
    )

    print(
        f"Unresolved        : "
        f"{port_info['unresolved']}"
    )

    print(
        f"Multiple parents  : "
        f"{port_info['multiple']}"
    )

    print()
    print("Parent IFC Classes")
    print("-" * 78)

    for parent_class, count in (
        port_info[
            "parent_class_counter"
        ].most_common()
    ):
        print(
            f"{count:>8}  {parent_class}"
        )

    print()
    print("Ownership Relations")
    print("-" * 78)

    for relation, count in (
        port_info[
            "relation_counter"
        ].most_common()
    ):
        print(
            f"{count:>8}  {relation}"
        )

    # --------------------------------------------------------------
    # Properties
    # --------------------------------------------------------------

    print()
    print("Building Property indexes...")

    instance_psets = (
        build_instance_pset_index(model)
    )

    type_index = build_type_index(model)

    (
        pset_counter,
        property_counter,
        samples,
        element_property_rows,
    ) = inspect_properties(
        elements,
        instance_psets,
        type_index,
    )

    print()
    print("=" * 78)
    print("PropertySet inventory")
    print("=" * 78)

    for (
        entity_class,
        source,
        pset_name,
    ), count in pset_counter.most_common(120):

        print(
            f"{count:>8}  "
            f"{entity_class:<28} "
            f"{source:<8} "
            f"{truncate(pset_name, 60)}"
        )

    # --------------------------------------------------------------
    # Output paths
    # --------------------------------------------------------------

    stem = ifc_path.stem

    entity_csv = (
        output_dir
        / f"{stem}_element_inventory.csv"
    )

    pset_csv = (
        output_dir
        / f"{stem}_pset_inventory.csv"
    )

    property_csv = (
        output_dir
        / f"{stem}_property_inventory.csv"
    )

    element_property_csv = (
        output_dir
        / f"{stem}_element_properties.csv"
    )

    port_csv = (
        output_dir
        / f"{stem}_port_parent_inventory.csv"
    )

    # --------------------------------------------------------------
    # Entity CSV
    # --------------------------------------------------------------

    write_csv(
        entity_csv,
        [
            "StepId",
            "GlobalId",
            "IfcClass",
            "Name",
            "ObjectType",
            "Tag",
        ],
        element_rows,
    )

    # --------------------------------------------------------------
    # Pset summary CSV
    # --------------------------------------------------------------

    pset_rows = []

    for (
        entity_class,
        source,
        pset_name,
    ), count in sorted(
        pset_counter.items()
    ):

        pset_rows.append({
            "IfcClass": entity_class,
            "Source": source,
            "PsetName": pset_name,
            "ElementCount": count,
        })

    write_csv(
        pset_csv,
        [
            "IfcClass",
            "Source",
            "PsetName",
            "ElementCount",
        ],
        pset_rows,
    )

    # --------------------------------------------------------------
    # Property summary CSV
    # --------------------------------------------------------------

    property_rows = []

    for key, count in sorted(
        property_counter.items()
    ):

        (
            entity_class,
            source,
            pset_name,
            prop_name,
            prop_type,
        ) = key

        sample_values = samples.get(
            key,
            [],
        )

        property_rows.append({
            "IfcClass": entity_class,
            "Source": source,
            "PsetName": pset_name,
            "PropertyName": prop_name,
            "PropertyType": prop_type,
            "OccurrenceCount": count,
            "SampleValues":
                " || ".join(sample_values),
        })

    write_csv(
        property_csv,
        [
            "IfcClass",
            "Source",
            "PsetName",
            "PropertyName",
            "PropertyType",
            "OccurrenceCount",
            "SampleValues",
        ],
        property_rows,
    )

    # --------------------------------------------------------------
    # Element-property detail CSV
    # --------------------------------------------------------------

    write_csv(
        element_property_csv,
        [
            "StepId",
            "GlobalId",
            "IfcClass",
            "Name",
            "ObjectType",
            "Source",
            "PsetName",
            "PropertyName",
            "PropertyType",
            "Value",
        ],
        element_property_rows,
    )

    # --------------------------------------------------------------
    # Port parent CSV
    # --------------------------------------------------------------

    write_csv(
        port_csv,
        [
            "PortStepId",
            "PortGlobalId",
            "PortName",
            "ParentStepId",
            "ParentGlobalId",
            "ParentIfcClass",
            "ParentName",
            "ParentObjectType",
            "Relation",
            "Status",
        ],
        port_info["rows"],
    )

    # --------------------------------------------------------------
    # Result
    # --------------------------------------------------------------

    print()
    print("=" * 78)
    print("Output")
    print("=" * 78)

    print(f"Elements    : {entity_csv}")
    print(f"Psets       : {pset_csv}")
    print(f"Properties  : {property_csv}")
    print(
        f"ElementProps: "
        f"{element_property_csv}"
    )
    print(f"Port parents: {port_csv}")

    print()
    print("=" * 78)
    print("Done.")
    print("=" * 78)


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Inventory actual IFC element classes, "
            "MEP port ownership and properties."
        )
    )

    parser.add_argument(
        "ifc",
        type=Path,
        help="Input IFC file",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Output directory",
    )

    return parser.parse_args()


def main():

    args = parse_args()

    ifc_path = args.ifc

    if not ifc_path.exists():
        raise SystemExit(
            f"IFC file not found: {ifc_path}"
        )

    inspect_ifc(
        ifc_path,
        args.output_dir,
    )


if __name__ == "__main__":
    main()