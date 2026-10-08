# src/inspect_target_pipe.py
#
# ENMA PoC
# 指定した IfcPipeSegment 1本について、
# IFCから取得できる事実を可能な限り棚卸しする。
#
# 対象:
#   IFC STEP ID = #511
#
# 出力:
#   output/target_pipe_511_inventory.csv
#
# 方針:
#   - IFCに明示されている情報だけを IFC_FACT とする
#   - IFCから取得できない情報は NOT_IN_IFC とする
#   - ENMA側での推定・マスタ補完・Engineering Rule適用は行わない

from pathlib import Path
import csv
import json

import ifcopenshell
import ifcopenshell.util.element


# ============================================================
# 設定
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

IFC_FILE = PROJECT_ROOT / "data" / "営繕BIMモデル_EM.ifc"
OUTPUT_FILE = PROJECT_ROOT / "output" / "target_pipe_511_inventory.csv"

TARGET_STEP_ID = 511


# ============================================================
# 共通関数
# ============================================================

def safe_value(value):
    """CSVに書き込みやすい文字列へ変換する。"""
    if value is None:
        return ""

    if isinstance(value, (list, tuple, set)):
        return " | ".join(str(v) for v in value)

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, default=str)

    return str(value)


def add_row(
    rows,
    category,
    item,
    value,
    source_type="IFC_FACT",
    ifc_source="",
    note="",
):
    """
    棚卸し結果を1行追加する。

    source_type:
        IFC_FACT   : IFCから直接取得
        NOT_IN_IFC : IFCから取得できなかった
    """

    if value is None or value == "" or value == []:
        source_type = "NOT_IN_IFC"

    rows.append(
        {
            "category": category,
            "item": item,
            "value": safe_value(value),
            "source_type": source_type,
            "ifc_source": ifc_source,
            "note": note,
        }
    )


def entity_label(entity):
    """IFC Entityを人が確認しやすい文字列にする。"""
    if entity is None:
        return ""

    parts = [
        f"#{entity.id()}",
        entity.is_a(),
    ]

    name = getattr(entity, "Name", None)
    if name:
        parts.append(str(name))

    global_id = getattr(entity, "GlobalId", None)
    if global_id:
        parts.append(f"GlobalId={global_id}")

    return " / ".join(parts)


# ============================================================
# 基本情報
# ============================================================

def inspect_basic(pipe, rows):

    add_row(
        rows,
        "Basic",
        "STEP_ID",
        pipe.id(),
        ifc_source="IfcPipeSegment",
    )

    add_row(
        rows,
        "Basic",
        "EntityType",
        pipe.is_a(),
        ifc_source="IfcPipeSegment",
    )

    add_row(
        rows,
        "Basic",
        "GlobalId",
        getattr(pipe, "GlobalId", None),
        ifc_source="IfcPipeSegment.GlobalId",
    )

    add_row(
        rows,
        "Basic",
        "Name",
        getattr(pipe, "Name", None),
        ifc_source="IfcPipeSegment.Name",
    )

    add_row(
        rows,
        "Basic",
        "Description",
        getattr(pipe, "Description", None),
        ifc_source="IfcPipeSegment.Description",
    )

    add_row(
        rows,
        "Basic",
        "ObjectType",
        getattr(pipe, "ObjectType", None),
        ifc_source="IfcPipeSegment.ObjectType",
    )

    add_row(
        rows,
        "Basic",
        "PredefinedType",
        getattr(pipe, "PredefinedType", None),
        ifc_source="IfcPipeSegment.PredefinedType",
    )


# ============================================================
# 階
# ============================================================

def inspect_storey(pipe, rows):

    container = ifcopenshell.util.element.get_container(pipe)

    storey = None
    current = container

    while current:
        if current.is_a("IfcBuildingStorey"):
            storey = current
            break

        current = ifcopenshell.util.element.get_aggregate(current)

    if storey:
        add_row(
            rows,
            "Spatial",
            "Storey",
            getattr(storey, "Name", None),
            ifc_source=f"IfcBuildingStorey #{storey.id()}",
        )

        add_row(
            rows,
            "Spatial",
            "StoreyElevation",
            getattr(storey, "Elevation", None),
            ifc_source=f"IfcBuildingStorey #{storey.id()}.Elevation",
        )

    else:
        add_row(
            rows,
            "Spatial",
            "Storey",
            None,
            note="IfcBuildingStoreyとの包含関係を取得できなかった",
        )


# ============================================================
# Space
# ============================================================

def inspect_space(pipe, rows):

    found = []

    # IfcRelContainedInSpatialStructure 等
    for rel in getattr(pipe, "ContainedInStructure", []) or []:

        structure = getattr(rel, "RelatingStructure", None)

        if structure and structure.is_a("IfcSpace"):
            found.append(structure)

    # 逆参照を念のため確認
    for rel in getattr(pipe, "ReferencedInStructures", []) or []:

        structure = getattr(rel, "RelatingStructure", None)

        if structure and structure.is_a("IfcSpace"):
            found.append(structure)

    # 重複除去
    unique = {x.id(): x for x in found}

    if unique:
        for space in unique.values():

            add_row(
                rows,
                "Spatial",
                "Space",
                entity_label(space),
                ifc_source="IfcSpace relation",
            )

    else:
        add_row(
            rows,
            "Spatial",
            "Space",
            None,
            note=(
                "IfcPipeSegmentから直接たどれる"
                "IfcSpace関係を取得できなかった"
            ),
        )


# ============================================================
# 系統
# ============================================================

def inspect_system(pipe, rows):

    systems = []

    for rel in getattr(pipe, "HasAssignments", []) or []:

        if not rel.is_a("IfcRelAssignsToGroup"):
            continue

        group = getattr(rel, "RelatingGroup", None)

        if group is None:
            continue

        if group.is_a("IfcDistributionSystem") or group.is_a("IfcSystem"):
            systems.append(group)

    if systems:
        for system in systems:

            add_row(
                rows,
                "System",
                "SystemName",
                getattr(system, "Name", None),
                ifc_source=(
                    f"{system.is_a()} #{system.id()} "
                    "via IfcRelAssignsToGroup"
                ),
            )

            add_row(
                rows,
                "System",
                "SystemLongName",
                getattr(system, "LongName", None),
                ifc_source=f"{system.is_a()} #{system.id()}",
            )

            add_row(
                rows,
                "System",
                "SystemPredefinedType",
                getattr(system, "PredefinedType", None),
                ifc_source=f"{system.is_a()} #{system.id()}",
            )

    else:
        add_row(
            rows,
            "System",
            "SystemName",
            None,
            note="IfcDistributionSystem / IfcSystem を取得できなかった",
        )


# ============================================================
# Property Set
# ============================================================

def inspect_psets(pipe, rows):

    psets = ifcopenshell.util.element.get_psets(
        pipe,
        psets_only=False,
        qtos_only=False,
    )

    if not psets:
        add_row(
            rows,
            "Pset",
            "PropertySets",
            None,
            note="Property Set / Quantity Setを取得できなかった",
        )
        return

    for pset_name, properties in sorted(psets.items()):

        if not isinstance(properties, dict):
            continue

        for property_name, value in properties.items():

            # util.element.get_psets が付加する内部ID
            if property_name == "id":
                continue

            add_row(
                rows,
                "Pset",
                f"{pset_name}.{property_name}",
                value,
                ifc_source=f"{pset_name}.{property_name}",
            )


# ============================================================
# 呼び径・長さ候補
# ============================================================

def inspect_key_properties(pipe, rows):

    psets = ifcopenshell.util.element.get_psets(
        pipe,
        psets_only=False,
        qtos_only=False,
    )

    diameter_candidates = []
    length_candidates = []

    for pset_name, properties in psets.items():

        if not isinstance(properties, dict):
            continue

        for property_name, value in properties.items():

            lower = property_name.lower()

            if any(
                keyword in lower
                for keyword in [
                    "nominaldiameter",
                    "diameter",
                    "nominal diameter",
                    "呼び径",
                    "管径",
                ]
            ):
                diameter_candidates.append(
                    f"{pset_name}.{property_name}={value}"
                )

            if any(
                keyword in lower
                for keyword in [
                    "length",
                    "長さ",
                ]
            ):
                length_candidates.append(
                    f"{pset_name}.{property_name}={value}"
                )

    add_row(
        rows,
        "KeyFact",
        "NominalDiameterCandidates",
        diameter_candidates,
        ifc_source="Property/Qto search",
        note="径を意味しそうなIFC Propertyを列挙。値の採用判断はまだ行わない。",
    )

    add_row(
        rows,
        "KeyFact",
        "LengthCandidates",
        length_candidates,
        ifc_source="Property/Qto search",
        note="長さを意味しそうなIFC Property/Qtoを列挙。採用判断はまだ行わない。",
    )


# ============================================================
# Material
# ============================================================

def inspect_material(pipe, rows):

    material = ifcopenshell.util.element.get_material(
        pipe,
        should_skip_usage=False,
    )

    if material is None:

        add_row(
            rows,
            "Material",
            "Material",
            None,
            note="IfcMaterial関連を取得できなかった",
        )
        return

    add_row(
        rows,
        "Material",
        "MaterialEntity",
        entity_label(material),
        ifc_source=material.is_a(),
    )

    # 単純 IfcMaterial
    if material.is_a("IfcMaterial"):

        add_row(
            rows,
            "Material",
            "MaterialName",
            getattr(material, "Name", None),
            ifc_source=f"IfcMaterial #{material.id()}",
        )

    # LayerSet
    elif material.is_a("IfcMaterialLayerSetUsage"):

        layer_set = material.ForLayerSet

        for i, layer in enumerate(layer_set.MaterialLayers, start=1):

            mat = getattr(layer, "Material", None)

            add_row(
                rows,
                "Material",
                f"Layer{i}.Material",
                getattr(mat, "Name", None) if mat else None,
                ifc_source="IfcMaterialLayerSetUsage",
            )

            add_row(
                rows,
                "Material",
                f"Layer{i}.Thickness",
                getattr(layer, "LayerThickness", None),
                ifc_source="IfcMaterialLayer",
            )

    # ProfileSet
    elif material.is_a("IfcMaterialProfileSetUsage"):

        profile_set = material.ForProfileSet

        for i, profile in enumerate(
            profile_set.MaterialProfiles,
            start=1,
        ):

            mat = getattr(profile, "Material", None)

            add_row(
                rows,
                "Material",
                f"Profile{i}.Material",
                getattr(mat, "Name", None) if mat else None,
                ifc_source="IfcMaterialProfileSetUsage",
            )


# ============================================================
# Port
# ============================================================

def get_ports(model, pipe):

    ports = []

    # IFC4系: IfcRelNests
    for rel in getattr(pipe, "IsNestedBy", []) or []:

        for obj in getattr(rel, "RelatedObjects", []) or []:

            if obj.is_a("IfcDistributionPort"):
                ports.append(obj)

    # 念のためモデル全体から IfcRelConnectsPortToElement も確認
    for rel in model.by_type("IfcRelConnectsPortToElement"):

        if rel.RelatedElement == pipe:
            ports.append(rel.RelatingPort)

    # 重複除去
    return list({p.id(): p for p in ports}.values())


def inspect_ports(model, pipe, rows):

    ports = get_ports(model, pipe)

    if not ports:

        add_row(
            rows,
            "Port",
            "Ports",
            None,
            note="IfcDistributionPortを取得できなかった",
        )
        return

    add_row(
        rows,
        "Port",
        "PortCount",
        len(ports),
        ifc_source="IfcDistributionPort",
    )

    for index, port in enumerate(
        sorted(ports, key=lambda x: x.id()),
        start=1,
    ):

        prefix = f"Port{index}"

        add_row(
            rows,
            "Port",
            f"{prefix}.STEP_ID",
            port.id(),
            ifc_source="IfcDistributionPort",
        )

        add_row(
            rows,
            "Port",
            f"{prefix}.Name",
            getattr(port, "Name", None),
            ifc_source=f"IfcDistributionPort #{port.id()}",
        )

        add_row(
            rows,
            "Port",
            f"{prefix}.FlowDirection",
            getattr(port, "FlowDirection", None),
            ifc_source=f"IfcDistributionPort #{port.id()}",
        )

        add_row(
            rows,
            "Port",
            f"{prefix}.PredefinedType",
            getattr(port, "PredefinedType", None),
            ifc_source=f"IfcDistributionPort #{port.id()}",
        )

        # PortのPropertyも全部確認
        port_psets = ifcopenshell.util.element.get_psets(port)

        for pset_name, properties in port_psets.items():

            if not isinstance(properties, dict):
                continue

            for prop_name, value in properties.items():

                if prop_name == "id":
                    continue

                add_row(
                    rows,
                    "Port",
                    f"{prefix}.{pset_name}.{prop_name}",
                    value,
                    ifc_source=(
                        f"IfcDistributionPort #{port.id()} "
                        f"{pset_name}.{prop_name}"
                    ),
                )


# ============================================================
# 接続先
# ============================================================

def inspect_connections(model, pipe, rows):

    ports = get_ports(model, pipe)

    connections_found = 0

    for port in ports:

        # ConnectedTo
        for rel in getattr(port, "ConnectedTo", []) or []:

            other_port = getattr(rel, "RelatedPort", None)

            if other_port is None:
                continue

            connections_found += 1

            add_row(
                rows,
                "Connection",
                f"Port#{port.id()} ConnectedTo",
                entity_label(other_port),
                ifc_source="IfcRelConnectsPorts",
            )

            # 接続先Portの親要素を探索
            parent = find_port_parent(model, other_port)

            add_row(
                rows,
                "Connection",
                f"Port#{port.id()} ConnectedElement",
                entity_label(parent) if parent else None,
                ifc_source="IfcDistributionPort parent relation",
            )

        # ConnectedFrom
        for rel in getattr(port, "ConnectedFrom", []) or []:

            other_port = getattr(rel, "RelatingPort", None)

            if other_port is None:
                continue

            connections_found += 1

            add_row(
                rows,
                "Connection",
                f"Port#{port.id()} ConnectedFrom",
                entity_label(other_port),
                ifc_source="IfcRelConnectsPorts",
            )

            parent = find_port_parent(model, other_port)

            add_row(
                rows,
                "Connection",
                f"Port#{port.id()} ConnectedElement",
                entity_label(parent) if parent else None,
                ifc_source="IfcDistributionPort parent relation",
            )

    if connections_found == 0:

        add_row(
            rows,
            "Connection",
            "ConnectedElements",
            None,
            note="Port経由の接続先を取得できなかった",
        )


def find_port_parent(model, port):

    # IfcRelNests
    for rel in getattr(port, "Nests", []) or []:

        parent = getattr(rel, "RelatingObject", None)

        if parent:
            return parent

    # IfcRelConnectsPortToElement
    for rel in model.by_type("IfcRelConnectsPortToElement"):

        if rel.RelatingPort == port:
            return rel.RelatedElement

    return None


# ============================================================
# IFCでは決めない項目
# ============================================================

def add_enma_missing_candidates(rows):

    """
    今後 S/M/R から補う可能性が高い項目。
    IFCに値が存在するか否かとは別に、
    この段階ではENMA側で決定しない。
    """

    candidates = [
        (
            "ENMA_GAP",
            "ApplicableSpecification",
            "S",
            "案件に適用する仕様",
        ),
        (
            "ENMA_GAP",
            "InsulationRequired",
            "S/R",
            "保温が必要かどうか",
        ),
        (
            "ENMA_GAP",
            "InsulationSpecification",
            "S/M/R",
            "保温材・保温厚・仕上げ等",
        ),
        (
            "ENMA_GAP",
            "StandardOutsideDiameter",
            "M",
            "JIS等による標準外径",
        ),
        (
            "ENMA_GAP",
            "PaintingSpecification",
            "S/M/R",
            "塗装要否・塗装仕様",
        ),
        (
            "ENMA_GAP",
            "LaborProductivity",
            "M/R",
            "歩掛",
        ),
        (
            "ENMA_GAP",
            "QuantityCalculationRule",
            "R",
            "数量計算方法",
        ),
    ]

    for category, item, layer, note in candidates:

        rows.append(
            {
                "category": category,
                "item": item,
                "value": "",
                "source_type": "TO_BE_SUPPLIED",
                "ifc_source": "",
                "note": f"補完候補層={layer}; {note}",
            }
        )


# ============================================================
# main
# ============================================================

def main():

    print("=" * 70)
    print("ENMA target pipe inventory")
    print("=" * 70)

    print(f"IFC file : {IFC_FILE}")
    print(f"Target   : #{TARGET_STEP_ID}")
    print(f"Output   : {OUTPUT_FILE}")
    print()

    if not IFC_FILE.exists():
        raise FileNotFoundError(
            f"IFCファイルが見つかりません: {IFC_FILE}"
        )

    model = ifcopenshell.open(str(IFC_FILE))

    pipe = model.by_id(TARGET_STEP_ID)

    if pipe is None:
        raise ValueError(
            f"STEP ID #{TARGET_STEP_ID} が見つかりません"
        )

    if not pipe.is_a("IfcPipeSegment"):
        raise TypeError(
            f"#{TARGET_STEP_ID} は IfcPipeSegment ではありません: "
            f"{pipe.is_a()}"
        )

    rows = []

    inspect_basic(pipe, rows)
    inspect_system(pipe, rows)
    inspect_storey(pipe, rows)
    inspect_space(pipe, rows)
    inspect_psets(pipe, rows)
    inspect_key_properties(pipe, rows)
    inspect_material(pipe, rows)
    inspect_ports(model, pipe, rows)
    inspect_connections(model, pipe, rows)

    # S/M/Rから補完する候補
    add_enma_missing_candidates(rows)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "category",
        "item",
        "value",
        "source_type",
        "ifc_source",
        "note",
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

    print(f"Entity   : {pipe.is_a()}")
    print(f"GlobalId : {getattr(pipe, 'GlobalId', '')}")
    print(f"Name     : {getattr(pipe, 'Name', '')}")
    print()
    print(f"Rows     : {len(rows)}")
    print(f"Saved    : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
