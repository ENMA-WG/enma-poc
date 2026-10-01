# 出力例

このドキュメントでは、ENMA-WG MEP数量算出PoCによって生成される出力ファイルの例について説明します。

これらの出力の目的は、単にIFCデータをCSVへエクスポートすることではありません。

IFCデータをどのように解釈し、数量算出に利用できるエンジニアリング情報へ変換できるかを示すものです。

基本的なコンセプトは以下のとおりです。

```text
IFC Data
   ↓
Relationships / Context
   ↓
Engineering Meaning
   ↓
Engineering Quantity
```

現在のPoCでは、主に配管セグメントと配管継手を対象としています。

---

## 1. 概要

以下の4つの出力ファイルは、現在のPoCにおける主要なサンプル結果です。

| 出力ファイル | 説明 | データ行数 |
|---|---|---:|
| `output/pipes_detail.csv` | 個々の配管セグメントについて抽出・解釈されたエンジニアリング属性 | 252 |
| `output/pipes_summary.csv` | 集計された配管数量 | 138 |
| `output/pipe_fittings_detail.csv` | 個々の配管継手に関するエンジニアリング属性および接続情報 | 81 |
| `output/pipe_fittings_summary.csv` | 集計された配管継手数量 | 48 |

これらのファイルを通して、個々のIFC要素からエンジニアリング数量情報へ至る変換過程を確認できます。

---

# 2. 配管要素

## `output/pipes_detail.csv`

このファイルには、PoCで処理した各 `IfcPipeSegment` が1行ずつ記録されています。

現在のソースモデルには、以下の配管セグメントが含まれています。

```text
IfcPipeSegment : 252
```

代表的な列は以下のとおりです。

| 列 | 意味 |
|---|---|
| `GlobalId` | IFC GlobalId |
| `Name` | IFC要素名 |
| `階` | 建物階 |
| `配管種別` | 配管種別 |
| `系統コード` | 系統コード |
| `系統名称` | 系統名称 |
| `IFC系統分類` | IFC系統分類 |
| `外径` | 外径 |
| `内径` | 内径 |
| `長さ` | 配管長 |
| `方向区分` | 方向区分 |
| `軸DX`, `軸DY`, `軸DZ` | 配管軸ベクトル |
| `水平面角度_deg` | 水平面上の角度 |
| `勾配` | 勾配 |
| `Z最低`, `Z最高` | 最低・最高Z座標 |
| `高低差` | 高低差 |

重要な点は、このファイルにはIFCプロパティを直接エクスポートしただけではない情報が含まれていることです。

幾何情報を解釈することによって、配管の方向などのエンジニアリング属性を判定しています。

例えば：

```text
IFC geometry
     ↓
Pipe axis vector
     ↓
Direction interpretation
     ↓
Horizontal / Vertical / Sloped
```

この解釈によって、IFC要素を数量算出にとって意味のある単位でグループ化できるようになります。

---

# 3. 配管数量集計

## `output/pipes_summary.csv`

このファイルは、`pipes_detail.csv` に含まれる252個の個別配管要素を集計したものです。

現在の集計軸には以下が含まれます。

- 建物階
- 系統
- IFC系統分類
- 外径
- 方向区分

代表的な列は以下のとおりです。

| 列 | 意味 |
|---|---|
| `階` | 建物階 |
| `系統コード` | 系統コード |
| `系統名称` | 系統名称 |
| `IFC系統分類` | IFC系統分類 |
| `外径_mm` | 外径（mm） |
| `方向区分` | 方向区分 |
| `本数` | 配管セグメント数 |
| `長さ_m` | 配管総延長（m） |

現在のPoCでは、以下の結果が生成されます。

```text
Pipe segments : 252
Summary rows  : 138
Skipped       : 0

Total length      : 649.090 m
Horizontal length : 375.963 m
Vertical length   : 273.127 m
Sloped length     : 0.000 m
```

これは、以下の変換として捉えることができます。

```text
252 IFC pipe elements
        ↓
Engineering attributes
        ↓
Grouping / Aggregation
        ↓
138 quantity summary rows
```

この結果は、集計に使用したエンジニアリング属性を保持しながら、IFC要素を構造化された数量情報へ変換できることを示しています。

`649.090 m` は、このPoCで採用している現在のIFCベースの配管長解釈による値です。完全な施工数量や工事見積数量を意味するものではありません。

詳細な再現手順および現在の制限事項については、[REPRODUCE_PIPE_RESULTS.md](REPRODUCE_PIPE_RESULTS.md) を参照してください。

---

# 4. 配管継手

## `output/pipe_fittings_detail.csv`

このファイルには、現在のPoCで処理した各 `IfcPipeFitting` が1行ずつ記録されています。

ソースモデルには以下が含まれています。

```text
IfcPipeFitting : 81
```

代表的な列は以下のとおりです。

| 列 | 意味 |
|---|---|
| `GlobalId` | IFC GlobalId |
| `Name` | IFC要素名 |
| `ObjectType` | IFC ObjectType |
| `PredefinedType` | IFC PredefinedType |
| `TypeName` | IFCタイプ名 |
| `継手種類` | 解釈された継手種類 |
| `階` | 建物階 |
| `系統コード` | 系統コード |
| `系統名称` | 系統名称 |
| `IFC系統分類` | IFC系統分類 |
| `Material` | 材料情報 |
| `PortCount` | ポート数 |
| `接続径1_mm` | 接続径1 |
| `接続径2_mm` | 接続径2 |
| `接続径3_mm` | 接続径3 |
| `径情報完全性` | 径情報の完全性 |
| `径取得元` | 径を判定するために使用した情報源 |
| `数量_個` | 数量 |
| `Warning` | 注意が必要な欠落情報または曖昧な情報 |

この出力は、ENMAの重要な考え方の一つを示しています。

> エンジニアリング上の意味が、必ずしもIFC要素自体の単一のプロパティとして存在するとは限りません。

一部の継手では、接続された配管セグメントまでIFCの関係をたどることで、接続径の情報を取得しています。

例えば：

```text
IfcPipeFitting
       ↓
IfcDistributionPort / Connections
       ↓
Connected IfcPipeSegment
       ↓
Pset_PipeSegmentTypeCommon.OuterDiameter
       ↓
Fitting connection diameter
```

現在の出力では、`径取得元` に以下のように記録される場合があります。

```text
Connected IfcPipeSegment.Pset_PipeSegmentTypeCommon.OuterDiameter
```

これは、単に継手自体からプロパティを読み取ることとは異なります。

エンジニアリング情報を、IFC要素間の **関係（Relationship）と文脈（Context）** から導き出しています。

これは、ENMAアプローチの中心的な考え方の一つです。

---

# 5. 継手数量集計

## `output/pipe_fittings_summary.csv`

このファイルは、`pipe_fittings_detail.csv` の個々の継手レコードを集計したものです。

代表的な列は以下のとおりです。

| 列 | 意味 |
|---|---|
| `階` | 建物階 |
| `系統コード` | 系統コード |
| `系統名称` | 系統名称 |
| `IFC系統分類` | IFC系統分類 |
| `継手種類` | 継手種類 |
| `TypeName` | IFCタイプ名 |
| `PortCount` | ポート数 |
| `数量_個` | 数量 |

現在のPoCでは、以下の変換が行われます。

```text
81 pipe fittings
       ↓
Engineering interpretation
       ↓
48 quantity summary rows
```

詳細ファイルと集計ファイルは、意図的に分けて保持しています。

詳細ファイルでは、各IFC要素のトレーサビリティと、その要素を解釈するために使用した情報を保持します。一方、集計ファイルでは、後続の積算処理に必要となる集計済み数量情報を提供します。

---

# 6. これらの出力が示すもの

サンプル出力は、ENMA-WGのアプローチにおけるいくつかの原則を示しています。

## 6.1 IFCは出発点であり、最終的な数量ではない

IFCは、形状、プロパティ、分類、空間的関係、系統、ポート、接続関係などの情報を提供します。

しかし、工事数量を算出するためには、これらのデータをエンジニアリングの観点から解釈する必要があります。

```text
IFC Data
   ↓
Engineering Interpretation
   ↓
Quantity Information
```

---

## 6.2 関係性からエンジニアリング上の意味を得ることができる

エンジニアリング情報は、単一のプロパティだけでなく、IFC要素間の関係から得られる場合があります。

配管継手の例は、このことを明確に示しています。

```text
Fitting
   ↓
Port / Connection
   ↓
Connected Pipe
   ↓
Pipe Diameter
   ↓
Fitting Connection Diameter
```

実際のIFCモデルを扱う場合、このような関係性に基づく解釈はますます重要になります。

---

## 6.3 詳細と集計は追跡可能であるべき

数量の集計結果は、その元となったIFC要素から切り離されるべきではありません。

そのため、このPoCでは以下を分離しています。

```text
Element-level interpretation
        ↓
Quantity aggregation
```

一方で、詳細出力には `GlobalId` やその他のエンジニアリング属性を保持しています。

これにより、数量結果を元のIFCモデルまで遡って確認するための基盤を提供します。

---

## 6.4 欠落している情報は可視化されたままであるべき

実際のIFCモデルには、数量算出に必要な情報がすべて含まれているとは限りません。

このPoCでは、欠落している値をすべて安全に推論できるとは想定していません。

例えば、以下のようなフィールドを保持しています。

```text
径情報完全性
径取得元
Warning
```

これにより、欠落している情報、推論された情報、曖昧な情報を可視化した状態に保つことができます。

この考え方は、ENMAデータモデルにおけるHuman-in-the-Loopのアプローチと直接つながっています。

```text
Machine interpretation
        ↓
Uncertain / missing information
        ↓
Engineer review
        ↓
Confirmed engineering meaning
        ↓
Quantity result
```

より広範なENMA数量算出データモデルについては、[DATA_MODEL.md](DATA_MODEL.md) を参照してください。

---

# 7. 現在の制限事項

現在のサンプル出力はPoCを示すものであり、完全な工事見積として解釈されるべきではありません。

現在実証している範囲外、またはさらなる開発が必要なエンジニアリング上の課題には、以下が含まれます。

- 継手長および配管数量計算におけるその扱い
- 施工箇所
- 露出・隠蔽条件
- 管材の解釈
- 保温仕様
- 塗装仕様
- 案件固有の仕様
- 労務歩掛
- 不完全なIFC情報の扱い
- 正式な技術者確認ワークフロー
- ダクト数量算出の拡張
- 機器数量および仕様の解釈

これらは、単にCSVの列を追加すれば解決する問題ではありません。

エンジニアリングルール、参照データ、案件仕様、推論、そして場合によっては技術者による判断が必要になります。

このためENMAアプローチでは、IFCデータと、エンジニアリングマスタ、仕様、ルール、推論、レビュー、最終的な数量結果を分離しています。

---

# 8. サンプル出力からENMAデータモデルへ

現在のPoC出力ファイルは、より広範なENMAコンセプトの初期実装として捉えることができます。

```text
IFC Data
   │
   ▼
Element-level information
   │
   ▼
Relationships / Context
   │
   ▼
Engineering Meaning
   │
   ▼
Quantity Results
```

ENMAデータモデルでは、この考え方を拡張し、以下を明示的に分離しています。

```text
P  Project / Transaction
S  Specification
M  Master
R  Rule
I  Inference / Evaluation
O  Output / Result
```

これにより、単に、

> 数量はいくつか？

という問いだけではなく、

> その数量はどのように算出されたのか？

という問いにも答えられるようにすることを目指しています。

この違いは、エンジニアリング数量算出において重要です。

数量は、単にIFCから読み取られるものではありません。

**数量は、明示的で追跡可能な解釈プロセスを経て生成されます。**

---

# 9. 関連ドキュメント

詳細については、以下を参照してください。

- [README](../README.md) — プロジェクト概要およびQuick Start
- [REPRODUCE_PIPE_RESULTS.md](REPRODUCE_PIPE_RESULTS.md) — 配管数量結果の再現手順
- [REPRODUCE_PIPE_RESULTS_ja.md](REPRODUCE_PIPE_RESULTS_ja.md) — 配管数量結果の日本語版再現手順
- [DATA_MODEL.md](DATA_MODEL.md) — ENMA Quantity Takeoff Data Model
- [DATA_MODEL_ja.md](DATA_MODEL_ja.md) — ENMA数量算出データモデル日本語版
- [ENMA_Data_Model.xlsx](ENMA_Data_Model.xlsx) — ENMAテーブル定義詳細

---

# ENMA-WG

ENMA-WG PoCでは、openBIMデータを、明示的で再利用可能かつ追跡可能なエンジニアリング上の解釈を通じて、エンジニアリング数量へ変換する方法を検討しています。

```text
IFC Data
   ↓
Engineering Meaning
   ↓
Engineering Quantity
```