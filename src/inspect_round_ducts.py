from pathlib import Path
from collections import Counter, defaultdict
import csv
import json

import ifcopenshell
import ifcopenshell.util.element


IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")
DUCT_CSV = Path("output/ducts_detail.csv")
OUTPUT_FILE = Path("output/round_duct_inspection.csv")


def text(value):
    if value is None:
        return ""
    return str(value).strip()


def get_type_info(element):
    type_obj = ifcopenshell.util.element.get_type(element)

    if not type_obj:
        return "", "", "", ""

    return (
        type_obj.is_a(),
        text(getattr(type_obj, "Name", None)),
        text(getattr(type_obj, "ElementType", None)),
        text(getattr(type_obj, "PredefinedType", None)),
    )


def material_to_text(material):
    if material is None:
        return ""

    kind = material.is_a()

    if kind == "IfcMaterial":
        return text(getattr(material, "Name", None))

    if kind == "IfcMaterialLayerSetUsage":
        material = material.ForLayerSet
        kind = material.is_a()

    if kind == "IfcMaterialProfileSetUsage":
        material = material.ForProfileSet
        kind = material.is_a()

    if kind == "IfcMaterialConstituentSet":
        values = []
        for item in material.MaterialConstituents or []:
            mat = getattr(item, "Material", None)
            if mat:
                values.append(text(getattr(mat, "Name", None)))
        return " | ".join(v for v in values if v)

    if kind == "IfcMaterialLayerSet":
        values = []
        for layer in material.MaterialLayers or []:
            mat = getattr(layer, "Material", None)
            if mat:
                values.append(text(getattr(mat, "Name", None)))
        return " | ".join(v for v in values if v)

    if kind == "IfcMaterialProfileSet":
        values = []
        for profile in material.MaterialProfiles or []:
            mat = getattr(profile, "Material", None)
            if mat:
                values.append(text(getattr(mat, "Name", None)))
        return " | ".join(v for v in values if v)

    return text(getattr(material, "Name", None)) or kind


def flatten_properties(element):
    """
    Get occurrence + inherited type properties.

    Returns a compact JSON string so we can later search for terms such as:
    スパイラル / spiral / galvanized / 亜鉛 / material / duct type
    """
    psets = ifcopenshell.util.element.get_psets(
        element,
        psets_only=True,
        should_inherit=True,
    )

    cleaned = {}

    for pset_name, properties in psets.items():
        values = {}

        for key, value in properties.items():
            if key == "id":
                continue

            if value is None:
                continue

            if isinstance(value, (str, int, float, bool)):
                values[key] = value
            else:
                values[key] = str(value)

        if values:
            cleaned[pset_name] = values

    return json.dumps(
        cleaned,
        ensure_ascii=False,
        sort_keys=True,
    )


def main():
    print("=== ROUND DUCT INSPECTION ===")
    print()
    print(f"IFC    : {IFC_FILE}")
    print(f"Duct CSV: {DUCT_CSV}")
    print(f"Output : {OUTPUT_FILE}")
    print()

    model = ifcopenshell.open(str(IFC_FILE))

    # Use the geometry classification already established by extract_ducts.py.
    round_ids = set()

    with DUCT_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        reader = csv.DictReader(f)

        for row in reader:
            if text(row.get("Shape")).upper() == "ROUND":
                round_ids.add(text(row.get("GlobalId")))

    print(f"ROUND GlobalIds      : {len(round_ids)}")

    rows = []

    name_counter = Counter()
    object_type_counter = Counter()
    type_name_counter = Counter()
    element_type_counter = Counter()
    material_counter = Counter()
    predefined_counter = Counter()

    keyword_hits = defaultdict(int)

    keywords = [
        "スパイラル",
        "spiral",
        "亜鉛",
        "galvan",
        "ダクト",
        "duct",
    ]

    for duct in model.by_type("IfcDuctSegment"):
        if duct.GlobalId not in round_ids:
            continue

        (
            type_class,
            type_name,
            element_type,
            type_predefined,
        ) = get_type_info(duct)

        material = ifcopenshell.util.element.get_material(
            duct,
            should_inherit=True,
        )

        material_class = material.is_a() if material else ""
        material_name = material_to_text(material)

        properties = flatten_properties(duct)

        name = text(getattr(duct, "Name", None))
        object_type = text(getattr(duct, "ObjectType", None))
        predefined = text(
            ifcopenshell.util.element.get_predefined_type(duct)
        )

        searchable = " ".join(
            [
                name,
                object_type,
                type_name,
                element_type,
                predefined,
                type_predefined,
                material_name,
                properties,
            ]
        ).lower()

        hits = []

        for keyword in keywords:
            if keyword.lower() in searchable:
                hits.append(keyword)
                keyword_hits[keyword] += 1

        rows.append(
            {
                "GlobalId": duct.GlobalId,
                "Name": name,
                "ObjectType": object_type,
                "PredefinedType": predefined,
                "TypeClass": type_class,
                "TypeName": type_name,
                "ElementType": element_type,
                "TypePredefinedType": type_predefined,
                "MaterialClass": material_class,
                "Material": material_name,
                "KeywordHits": " | ".join(hits),
                "Properties": properties,
            }
        )

        name_counter[name or "(blank)"] += 1
        object_type_counter[object_type or "(blank)"] += 1
        type_name_counter[type_name or "(blank)"] += 1
        element_type_counter[element_type or "(blank)"] += 1
        material_counter[material_name or "(blank)"] += 1
        predefined_counter[predefined or "(blank)"] += 1

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "GlobalId",
        "Name",
        "ObjectType",
        "PredefinedType",
        "TypeClass",
        "TypeName",
        "ElementType",
        "TypePredefinedType",
        "MaterialClass",
        "Material",
        "KeywordHits",
        "Properties",
    ]

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    def show(title, counter, limit=20):
        print()
        print(f"--- {title} ---")
        for value, count in counter.most_common(limit):
            print(f"{count:4d}  {value}")

    print()
    print("=== RESULT ===")
    print(f"ROUND inspected      : {len(rows)}")

    show("ObjectType", object_type_counter)
    show("TypeName", type_name_counter)
    show("ElementType", element_type_counter)
    show("PredefinedType", predefined_counter)
    show("Material", material_counter)

    print()
    print("--- Keyword hits ---")
    for keyword in keywords:
        print(f"{keyword:<12}: {keyword_hits[keyword]}")

    print()
    print(f"CSV written          : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()