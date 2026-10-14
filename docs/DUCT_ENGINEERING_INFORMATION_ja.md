# ダクトEngineering Information検証

## 概要

このドキュメントでは、ENMA-WG Automated MEP Quantity Takeoff PoCにおいて、再現可能なIFCダクト数量算出から仕様選定へ進むために必要となるEngineering Informationを調査した結果をまとめます。

現在の実験では、ENMA-WG PoCで使用している日本の国土交通省（MLIT）のBIMサンプルモデルを使用しています。

```text
data/営繕BIMモデル_EM.ifc
```

目的は、IFC一般の限界を主張することではありません。現在の検証IFCから何が確認でき、何が確認できなかったかを記録し、IFCから観測した情報と技術的解釈を明示的に分離することです。

## 出発点：再現可能なダクト数量

これまでのダクトPoCでは、現在の検証IFCについて次の結果を確認しています。

- `IfcDuctSegment`: 1,077本
- ROUND: 792本
- RECTANGULAR: 285本
- UNKNOWN: 0本
- Geometry総延長: 1,088.945 m
- QTO総延長: 1,088.945 m
- 1,077本すべてに正式な `IfcDistributionSystem` がちょうど1系統ずつ割り当てられている
- ENMA AirType: SA 512 / RA 4 / OA 112 / EA 449

数量集計では、1,077本を `AirType × Shape × Size` の234行へ集約し、Geometry由来寸法をそのまま保持しています。

ここまでで数量算出の再現可能な基盤ができました。次の問いは、板厚などの仕様を選定するために必要なEngineering Informationまで、同じIFCから取得できるかということです。

## なぜ板厚を対象にしたのか

ダクト板厚は、長さだけでは決定できないため、「数量の先」を検証する題材として適しています。Engineering Ruleでは、例えば次の情報が必要になる可能性があります。

- ダクト形状
- ダクト構造種別
- 材料仕様
- 圧力区分
- 角ダクトの長辺寸法
- 丸ダクトの呼称直径
- 適用する標準仕様・案件仕様

このうち一部はIFC Geometryから直接観測できますが、別の情報は案件仕様、標準仕様、推論、あるいは技術者確認が必要になります。

## 1. 形状とGeometry寸法

現在のPoCでは、IFC Geometryからダクト形状と寸法を取得できます。

```text
IfcDuctSegment 1077
├─ ROUND        792
└─ RECTANGULAR  285
```

角ダクトではローカル2Dプロファイルから幅・高さを取得し、丸ダクトではローカルプロファイルGeometryから直径を取得します。

これらはIFCから観測した値として扱います。

## 2. Geometry DiameterとNominal Diameterを分離する

ROUNDダクトではGeometry由来の直径を取得できます。しかし現在のワークフローでは、その値を追加確認なしにEngineering上の呼称直径とは扱いません。

```text
IFC観測値
  Geometry Diameter
        ↓
技術的解釈・確認
        ↓
  Nominal Diameter
```

例えばGeometry直径200 mmが、最終的に呼称直径200 mmと確認されることはあり得ます。しかしENMAのデータモデルでは、この二つを別概念として保持します。

標準仕様のルールが「呼称直径」を基準としている場合、Geometry直径を無条件に代用しないためです。

## 3. ROUNDだけではSPIRALと確定できない

`src/inspect_round_ducts.py` では、GeometryからすでにROUNDと分類された792本を対象に、Type、PredefinedType、Material、Propertyを調査しました。

結果：

```text
ROUND inspected      : 792

ObjectType
 789  丸型ダクト:00_丸タップ
   3  丸型ダクト:00_丸ティー

TypeName
 789  丸型ダクト:00_丸タップ
   3  丸型ダクト:00_丸ティー

ElementType
 792  (blank)

PredefinedType
 792  NOTDEFINED

Material
 792  ダクト－排気

Keyword hits
スパイラル       : 0
spiral          : 0
亜鉛             : 0
galvan          : 0
ダクト           : 792
duct            : 792
```

Occurrence/Type PropertyおよびMaterial情報から、構造種別・材料仕様の根拠になり得る語を調査しています。

今回のIFCから、Geometry上ROUNDであることは確認できますが、それをSPIRALダクト、あるいは亜鉛鉄板製ダクトと確定するための十分な根拠は確認できませんでした。

`Material = ダクト－排気` というIFC値は保持しますが、現在のPoCではこれをそのまま信頼できるEngineering Material Specificationとは解釈しません。

## 4. Duct Segment側の圧力情報

`src/inspect_duct_pressure.py` では、`Pset_DuctSegmentTypeCommon` を明示的に確認するとともに、Occurrenceおよび継承Type Propertyから圧力関連情報を検索しました。

修正版では、無関係な単語まで誤検出する可能性がある裸の `pa` 部分一致を使用していません。

結果：

```text
IfcDuctSegment        : 1077
WorkingPressure       : 0/1077
PressureRange         : 0/1077
Any pressure property : 0/1077

WorkingPressure values
(none)

PressureRange values
(none)

All pressure-related properties
(none)
```

これは「IFCでは圧力情報を表現できない」という意味ではありません。今回の検証IFCのダクト要素から、現在の板厚検討に必要な圧力情報を確認できなかったという結果です。

## 5. Distribution System側の圧力情報

調査対象を個々のダクト要素だけで終わらせず、正式に割り当てられている `IfcDistributionSystem` 側まで広げました。

関係経路：

```text
IfcDuctSegment
  └─ IfcRelAssignsToGroup
       └─ IfcDistributionSystem
```

`src/inspect_duct_system_properties.py` の結果：

```text
IfcDuctSegment             : 1077
Used IfcDistributionSystem : 404
Duct without system        : 0
Duct with multiple systems : 0
Output rows                : 404
```

Systemの `ObjectType` は空調系統分類に有効です。

| System ObjectType | ダクト本数 |
|---|---:|
| `101_SA給気` | 512 |
| `105_EA排気` | 449 |
| `103_OA外気` | 112 |
| `102_RA還気` | 4 |

System `PredefinedType` をダクト本数で集計すると次のとおりです。

| PredefinedType | ダクト本数 |
|---|---:|
| `VENTILATION` | 628 |
| `EXHAUST` | 449 |

404個の使用Systemで確認されたPropertyは、系統分類に対応する `Pset_DistributionSystemCommon.Reference` でした。圧力関連Propertyは確認できませんでした。

```text
Pressure-like properties
(none)
```

したがって現在の検証IFCでは、正式なSystem所属とSA/RA/OA/EA分類には有用な情報が存在しますが、1,077本のダクト要素側にも、割り当てられた404個のDistribution System側にも、板厚選定に必要な圧力区分情報を確認できませんでした。

## Engineering Information Gap

今回の結果を整理すると次のようになります。

| Engineering Information | 現在のMLIT検証IFC | ENMAでの扱い |
|---|---|---|
| Shape | 取得可能 | IFC観測値 |
| 角ダクト Width / Height | 取得可能 | IFC観測値 |
| Geometry Diameter | 取得可能 | IFC観測値 |
| Air System SA/RA/OA/EA | 正式なSystem割当から取得可能 | IFC観測値 + 明示的ENMAマッピング |
| Nominal Diameter | 独立したEngineering値として未確定 | 解釈・確認が必要 |
| Duct Construction Type（例：SPIRAL） | 未確認 | 解釈・確認が必要 |
| Material Specification（例：亜鉛鉄板） | Engineering用途として未確認 | 仕様・確認が必要 |
| Pressure Class | 確認できず | 案件仕様・推論・確認が必要 |
| Duct Thickness | このワークフローではIFC生データではない | 必要入力確定後にEngineering Ruleで導出 |

重要なのは、単に「情報がない」ということではありません。

**IFCから観測できる情報と、Engineering Decisionを行うために必要な情報の境界が見えた**ことが今回の検証結果です。

## ENMAの情報レイヤー

PoCでは、情報の出所を次のように明示的に分離する方向で進めています。

```text
1. IFC_OBSERVED
   Shape
   Width / Height
   Geometry Diameter
   Length
   Distribution System

2. PROJECT_SPECIFICATION / ENGINEERING ATTRIBUTE
   Nominal Diameter
   Duct Construction Type
   Pressure Class
   Material Specification

3. STANDARD_SPECIFICATION
   適用条項
   寸法範囲
   圧力区分ルール
   板厚ルール

4. DERIVED
   Long Side
   Duct Thickness
   後続する材料・労務数量
```

推定・仮定したEngineering値を、IFCに直接格納されていた値のように扱わないことが目的です。

## Human ReviewとEngineering Rule

ENMAのデータモデルでは、不足情報を暗黙に埋めるのではなく、確認可能なワークフローとして扱います。

```text
IFC observation
      ↓
inference_results
      ↓
human_reviews
      ↓
rule_evaluations
      ↓
element_quantity_results
```

ダクト板厚については、現在のデータモデルに `R40-01 duct_thickness_rules` を追加しています。

ルール入力として、例えば次の項目を扱います。

- `duct_shape`
- `duct_construction_type`
- `material`
- `pressure_class`
- `size_basis`
- `size_min_mm`
- `size_max_mm`
- `thickness_mm`
- `standard_provision_id`

特に `size_basis` の区別が重要です。

```text
LONG_SIDE
NOMINAL_DIAMETER
GEOMETRY_DIAMETER
```

標準仕様が呼称直径を基準としているルールに、Geometry直径を暗黙に代用しないためです。

## Quantity TakeoffからEngineering Specificationへ

今回の実験から、次のようなワークフローが見えてきました。

```text
IFC
 ↓
Geometry / QTO / Systems
 ↓
Reproducible Quantity
 ↓
Engineering Information Validation
 ↓
Inference / Project Specification / Human Review
 ↓
Engineering Rule Evaluation
 ↓
Specification Result
 ↓
Material / Labor / Schedule
```

これが現在のENMA-WGで検討している「数量の先へ」の具体的な意味です。

数量算出そのものを再現可能にできても、仕様選定へ進むためには追加のEngineering Informationが必要になる場合があります。その境界を明示し、不足情報を暗黙の仮定で置き換えないことを重視しています。

## 現在の対象範囲と注意

ここで示した結果は、現在のMLIT検証IFCと現在のPoC実装に対するものです。

次のような一般論を意味するものではありません。

- IFCでは圧力情報を表現できない
- すべてのROUNDダクトがSPIRALである、またはSPIRALではない
- すべてのIFCモデルに呼称寸法情報が存在しない
- 今回確認したMaterial値が常に信頼できない
- すべての案件で同じ情報補完ワークフローが必要になる

別のIFC出力、BIMオーサリングツール、案件要件、IDS定義、モデリングルールでは追加情報が取得できる可能性があります。

このPoCの目的は、観測データ・技術的解釈・導出結果を分離し、それぞれの処理を確認可能かつ再現可能にすることです。

## 関連ファイル

```text
src/extract_ducts.py
src/summarize_ducts.py
src/inspect_round_ducts.py
src/inspect_duct_pressure.py
src/inspect_duct_system_properties.py

output/ducts_detail.csv
output/ducts_summary.csv
output/round_duct_inspection.csv
output/duct_pressure_inspection.csv
output/duct_system_properties.csv

docs/DUCT_EXTRACTION_ja.md
```

## Project

ENMA-WG  
Automated MEP Quantity Takeoff PoC

本検証は、openBIMを利用した再現可能な設備数量算出と、その先のEngineering Workflowを検討するENMA-WGの研究活動の一部です。
