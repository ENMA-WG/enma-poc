'''
inspect_pipe_systems.py
IFCを変更せず、配管について「属性 → Pset → Type → Group/System relationship」を調べる診断用
'''
from pathlib import Path
from collections import Counter
import csv

import ifcopenshell
import ifcopenshell.util.element


IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")
OUTPUT_FILE = Path("output/pipe_system_inspection.csv")


def value_to_text(value):
    """IFC valueを表示可能な文字列にする。"""
    if value is None:
        return ""

    if hasattr(value, "wrappedValue"):
        value = value.wrappedValue

    if isinstance(value, (list, tuple)):
        return " | ".join(value_to_text(v) for v in value)

    return str(value)


def flatten_psets(element):
    """
    Pset/Qtoを
    PsetName.PropertyName = Value
    の形式で一覧化する。
    """
    result = []

    try:
        psets = ifcopenshell.util.element.get_psets(
            element,
            psets_only=False,
            qtos_only=False,
        )
    except Exception:
        return result

    for pset_name, props in psets.items():

        if not isinstance(props, dict):
            continue

        for prop_name, value in props.items():

            # get_psets() が返す内部idは除外
            if prop_name == "id":
                continue

            result.append(
                (
                    str(pset_name),
                    str(prop_name),
                    value_to_text(value),
                )
            )

    return result


def get_type_info(pipe):
    """IfcTypeObject側の情報を取得。"""
    type_obj = ifcopenshell.util.element.get_type(pipe)

    if type_obj is None:
        return "", "", "", []

    return (
        type_obj.is_a(),
        value_to_text(getattr(type_obj, "Name", None)),
        value_to_text(getattr(type_obj, "PredefinedType", None)),
        flatten_psets(type_obj),
    )


def get_group_relationships(pipe):
    """
    IfcRelAssignsToGroup を調べる。

    IfcSystem / IfcDistributionSystem への所属があれば、
    ここで見つける。
    """
    groups = []

    for rel in getattr(pipe, "HasAssignments", []) or []:

        if not rel.is_a("IfcRelAssignsToGroup"):
            continue

        group = rel.RelatingGroup

        if group is None:
            continue

        groups.append(
            {
                "class": group.is_a(),
                "name": value_to_text(
                    getattr(group, "Name", None)
                ),
                "description": value_to_text(
                    getattr(group, "Description", None)
                ),
                "object_type": value_to_text(
                    getattr(group, "ObjectType", None)
                ),
                "predefined_type": value_to_text(
                    getattr(group, "PredefinedType", None)
                ),
                "long_name": value_to_text(
                    getattr(group, "LongName", None)
                ),
            }
        )

    return groups


def find_keywords(text):
    """
    今回探したい語を検出。
    診断用なので分類にはまだ使用しない。
    """
    keywords = [
        "供給",
        "排水",
        "給水",
        "給湯",
        "還り",
        "往り",
        "冷水",
        "温水",
        "冷温水",
        "ドレン",
        "汚水",
        "雑排水",
        "通気",
        "消火",
        "ガス",
        "System",
        "system",
    ]

    found = []

    for keyword in keywords:
        if keyword in text:
            found.append(keyword)

    return " | ".join(found)


def main():

    print(f"IFC : {IFC_FILE}")
    print(f"CSV : {OUTPUT_FILE}")

    if not IFC_FILE.exists():
        raise FileNotFoundError(IFC_FILE)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    model = ifcopenshell.open(str(IFC_FILE))

    pipes = model.by_type("IfcPipeSegment")

    print(f"IfcPipeSegment count: {len(pipes)}")
    print()

    rows = []

    group_counter = Counter()
    pset_counter = Counter()
    property_counter = Counter()
    type_counter = Counter()

    # --------------------------------------------------------
    # Pipe inspection
    # --------------------------------------------------------

    for index, pipe in enumerate(pipes, start=1):

        name = value_to_text(
            getattr(pipe, "Name", None)
        )

        object_type = value_to_text(
            getattr(pipe, "ObjectType", None)
        )

        predefined_type = value_to_text(
            getattr(pipe, "PredefinedType", None)
        )

        # Instance Psets
        instance_psets = flatten_psets(pipe)

        for pset_name, prop_name, _ in instance_psets:
            pset_counter[pset_name] += 1
            property_counter[
                f"{pset_name}.{prop_name}"
            ] += 1

        # Type
        (
            type_class,
            type_name,
            type_predefined,
            type_psets,
        ) = get_type_info(pipe)

        if type_name:
            type_counter[type_name] += 1

        # Groups / Systems
        groups = get_group_relationships(pipe)

        for group in groups:
            key = (
                f"{group['class']} : "
                f"{group['name']}"
            )
            group_counter[key] += 1

        # 全情報を検索対象文字列にまとめる
        search_parts = [
            name,
            object_type,
            predefined_type,
            type_class,
            type_name,
            type_predefined,
        ]

        for pset_name, prop_name, value in instance_psets:
            search_parts.append(
                f"{pset_name}.{prop_name}={value}"
            )

        for pset_name, prop_name, value in type_psets:
            search_parts.append(
                f"TYPE:{pset_name}.{prop_name}={value}"
            )

        for group in groups:
            search_parts.extend(
                [
                    group["class"],
                    group["name"],
                    group["description"],
                    group["object_type"],
                    group["predefined_type"],
                    group["long_name"],
                ]
            )

        search_text = "\n".join(search_parts)

        keywords = find_keywords(search_text)

        # CSVにはPset/Groupをまとめて格納
        pset_text = " || ".join(
            f"{pset}.{prop}={value}"
            for pset, prop, value
            in instance_psets
        )

        type_pset_text = " || ".join(
            f"{pset}.{prop}={value}"
            for pset, prop, value
            in type_psets
        )

        group_text = " || ".join(
            (
                f"{g['class']}"
                f"[Name={g['name']};"
                f"ObjectType={g['object_type']};"
                f"PredefinedType={g['predefined_type']};"
                f"LongName={g['long_name']}]"
            )
            for g in groups
        )

        rows.append(
            {
                "GlobalId": pipe.GlobalId,
                "Name": name,
                "ObjectType": object_type,
                "PredefinedType": predefined_type,
                "TypeClass": type_class,
                "TypeName": type_name,
                "TypePredefinedType": type_predefined,
                "KeywordsFound": keywords,
                "InstancePsets": pset_text,
                "TypePsets": type_pset_text,
                "GroupsSystems": group_text,
            }
        )

        print(
            f"[{index:03d}/{len(pipes):03d}] "
            f"{pipe.GlobalId} "
            f"Name={name!r} "
            f"Keyword={keywords!r} "
            f"Groups={len(groups)}"
        )

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    fieldnames = [
        "GlobalId",
        "Name",
        "ObjectType",
        "PredefinedType",
        "TypeClass",
        "TypeName",
        "TypePredefinedType",
        "KeywordsFound",
        "InstancePsets",
        "TypePsets",
        "GroupsSystems",
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig",
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
    print("GROUP / SYSTEM RELATIONSHIPS")
    print("=" * 70)

    if group_counter:
        for key, count in group_counter.most_common():
            print(f"{count:4d}  {key}")
    else:
        print("No IfcRelAssignsToGroup relationships found.")

    print()
    print("=" * 70)
    print("TYPE NAMES")
    print("=" * 70)

    for key, count in type_counter.most_common():
        print(f"{count:4d}  {key}")

    print()
    print("=" * 70)
    print("PROPERTY NAMES")
    print("=" * 70)

    for key, count in property_counter.most_common():
        print(f"{count:4d}  {key}")

    print()
    print("=" * 70)
    print("KEYWORD MATCHES")
    print("=" * 70)

    keyword_rows = [
        row
        for row in rows
        if row["KeywordsFound"]
    ]

    print(
        f"Rows containing system-related keywords: "
        f"{len(keyword_rows)} / {len(rows)}"
    )

    print()
    print("=" * 70)
    print("Completed")
    print("=" * 70)
    print(f"CSV : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
