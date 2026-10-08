# ENMA Python Tools Guide（日本語版）

ENMA-WG PoC で使用している Python
ツールの目的、入力データ、出力データ、および研究上の位置づけを整理したガイドです。

> **対象**\
> 本書は現在 `src/`
> に置かれている実行・調査用スクリプトを中心に説明します。過去の探索的スクリプトは
> `research/archive/exploratory-scripts/`、研究上残すべき検証結果は
> `research/evidence/` に分けて保存します。

------------------------------------------------------------------------

## 1. このドキュメントについて

ENMA-WG では、IFC モデルから設備数量を取得するだけでなく、IFC
に記録された情報を調査し、設備技術者が積算・施工・維持管理に利用できる
**Engineering Information** へつなげることを目指しています。

そのため PoC では、数量抽出、IFC の構造確認、MEP Entity
の棚卸し、System・Port・Topology の調査、Space
との位置関係、施工箇所候補の検証など、多数の Python
ツールを作成しています。

本書は API
リファレンスではなく、各スクリプトの「目的」「入力」「出力」「ENMA
での位置づけ」を整理し、**ENMA PoC
を読み、再現し、次の研究へ進むための地図**とするものです。

------------------------------------------------------------------------

## 2. ENMA の Python ツール全体像

``` text
IFC Model
   │
   ├── IFC Inspection
   │      └─ IFC に何が入っているかを確認
   │
   ├── Quantity Extraction
   │      └─ 配管・ダクト・継手の数量を抽出・集計
   │
   ├── Engineering Information Inspection
   │      └─ System・圧力・寸法・機器・Property 等を調査
   │
   ├── Spatial Analysis
   │      └─ 階・Space・施工箇所候補を調査
   │
   └── Connectivity / Topology Analysis
          └─ Port・System・接続関係を調査
                 │
                 ▼
              IFC Fact
                 │
                 ▼
         Geometric Evidence
                 │
                 ▼
       Engineering Inference
                 │
                 ▼
           Human Review
                 │
                 ▼
       Engineering Information
```

ENMA では、IFC
から直接取得できる情報と、幾何情報や設備工学上の知識から推定した情報を混同しないことを重視します。

------------------------------------------------------------------------

## 3. まず何を実行すればよいか

  ---------------------------------------------------------------------------------
  やりたいこと                                主に見るスクリプト
  ------------------------------------------- -------------------------------------
  配管数量を再現したい                        `extract_pipes.py` →
                                              `summarize_pipes.py`

  ダクト数量を再現したい                      `extract_ducts.py` →
                                              `summarize_ducts.py`

  配管継手を調べたい                          `extract_pipe_fittings.py`,
                                              `inspect_pipe_fittings.py`,
                                              `inspect_fitting_sizes.py`

  IFC の                                      `inspect_ifc_application.py`
  Schema・作成アプリケーションを確認したい    

  IFC 間の互換性・内容差を確認したい          `inspect_ifc_compatibility.py`

  IFC にどの MEP Entity が存在するか調べたい  `inspect_mep_entity_inventory.py`

  ダクトの System 情報を調べたい              `inspect_duct_system_properties.py`

  ダクトの圧力・Profile・機器情報を調べたい   `inspect_duct_pressure.py`,
                                              `inspect_duct_profiles.py`,
                                              `inspect_duct_system_equipment.py`

  建築 Space を調べたい                       `inspect_architecture_spaces.py`

  配管と Space の位置関係を調べたい           `match_pipes_to_spaces.py`

  ダクトの天井内施工箇所候補を調べたい        `inspect_duct_ceiling_location.py`

  Port の接続関係を調べたい                   `inspect_port_topology.py`,
                                              `analyze_ifc_port_connections.py`

  特定配管を IFC Fact として深掘りしたい      `inspect_target_pipe.py`

  特定ダクト系統の Topology を追跡したい      `trace_duct_system_topology.py`
  ---------------------------------------------------------------------------------

------------------------------------------------------------------------

## 4. ツール一覧

### Status の意味

-   **Current / Reproducible** ---
    現在の代表ワークフローで使用し、再現対象となるもの
-   **Research** --- ENMA の研究課題を検証するためのツール
-   **Diagnostic** --- IFC の内容や品質を調査するための診断ツール

  ----------------------------------------------------------------------------------------------------------------
  Category       Script                                          主な目的                           Status
  -------------- ----------------------------------------------- ---------------------------------- --------------
  Quantity       `extract_pipes.py`                              配管情報の抽出                     Current /
                                                                                                    Reproducible

  Quantity       `summarize_pipes.py`                            配管数量の集計                     Current /
                                                                                                    Reproducible

  Quantity       `extract_pipe_fittings.py`                      配管継手情報の抽出                 Current /
                                                                                                    Reproducible

  Quantity       `inspect_pipe_fittings.py`                      配管継手の棚卸し                   Diagnostic

  Quantity       `inspect_fitting_sizes.py`                      継手寸法・Port 径の確認            Diagnostic

  Quantity       `extract_ducts.py`                              ダクト情報の抽出                   Current /
                                                                                                    Reproducible

  Quantity       `summarize_ducts.py`                            ダクト数量の集計                   Current /
                                                                                                    Reproducible

  IFC Inspection `inspect_ifc_application.py`                    Schema・作成アプリケーション確認   Diagnostic

  IFC Inspection `inspect_ifc_compatibility.py`                  IFC 互換性の事前確認               Diagnostic

  IFC Inspection `inspect_ifc_placements.py`                     Placement・座標系の調査            Research

  IFC Inspection `inspect_mep_entity_inventory.py`               MEP Entity / Property の棚卸し     Research

  Duct           `extract_duct_system_airflow.py`                System と風量情報の抽出            Research
  Engineering                                                                                       

  Duct           `inspect_duct_pressure.py`                      圧力関連 Property の調査           Research
  Engineering                                                                                       

  Duct           `inspect_duct_profiles.py`                      Profile / Representation の調査    Research
  Engineering                                                                                       

  Duct           `inspect_duct_outer_curves.py`                  OuterCurve 型の棚卸し              Diagnostic
  Engineering                                                                                       

  Duct           `inspect_duct_system_properties.py`             formal System 情報の確認           Research
  Engineering                                                                                       

  Duct           `inspect_duct_system_equipment.py`              System 別機器の棚卸し              Research
  Engineering                                                                                       

  Duct           `inspect_duct_system_equipment_properties.py`   System 機器 Property の調査        Research
  Engineering                                                                                       

  Duct           `inspect_round_ducts.py`                        丸ダクトの Type / Material / Pset  Research
  Engineering                                                    調査                               

  Spatial        `inspect_architecture_spaces.py`                建築 IFC の Space 棚卸し           Research

  Spatial        `inspect_duct_ceiling_location.py`              ダクト施工箇所候補の検証           Research

  Spatial        `match_pipes_to_spaces.py`                      配管と Space の幾何的対応付け      Research

  Connectivity   `analyze_connected_port_distances.py`           接続 Port 間距離の分析             Research

  Connectivity   `analyze_ifc_port_connections.py`               IFC Port 接続情報の分析            Research

  Connectivity   `inspect_ifc_connectivity_relationships.py`     IFC 接続 Relationship の調査       Research

  Connectivity   `inspect_duct_port_geometry.py`                 ダクト Port の位置・方向の調査     Research

  Connectivity   `trace_duct_system_topology.py`                 ダクト System Topology の追跡      Research

  Connectivity   `inspect_port_topology.py`                      Port 親要素・接続関係の総合調査    Research

  Connectivity   `inspect_pipe_systems.py`                       配管 System 情報の調査             Diagnostic

  Connectivity   `inspect_target_pipe.py`                        特定配管の IFC Fact 確認           Research

  Utility /      `extract_ifc_system.py`                         指定階・System の IFC              Research
  Research                                                       サブモデル抽出                     
  ----------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------

## 5. 数量算出ツール

### `extract_pipes.py`

設備 IFC から `IfcPipeSegment`
を抽出し、GlobalId、階、系統、径、長さ、方向、高さ、角度など、配管数量算出に必要な基本情報を
CSV に整理します。

**主な出力:** `output/pipes_detail.csv`\
**位置づけ:** `summarize_pipes.py`
の入力となる配管数量ワークフローの基本処理。\
**Status:** Current / Reproducible

### `summarize_pipes.py`

`pipes_detail.csv`
をもとに、階・系統・径などの単位で配管数量を集計します。

**主な出力:** `output/pipes_summary.csv`\
**位置づけ:** Tokyo Summit 2026 で示した配管数量 PoC
の代表的な再現ワークフロー。\
**Status:** Current / Reproducible

### `extract_pipe_fittings.py`

`IfcPipeFitting` と Port
等を調査し、継手数量・種類・接続情報を抽出します。
配管を「長さ」だけでなく継手を含む施工数量へ拡張するための数量算出ツールです。

**主な出力:** `output/pipe_fittings_detail.csv`,
`output/pipe_fittings_summary.csv`

**Status:** Current / Reproducible

### `inspect_pipe_fittings.py`

配管継手の型、Property、接続状況などを棚卸しし、IFC
にどこまで継手情報が存在するかを確認します。

**Status:** Diagnostic

### `inspect_fitting_sizes.py`

継手の Port 径や寸法情報を調査します。呼び径、実寸法、Port
情報を数量算出へどう利用するかを検討するための診断ツールです。

**Status:** Diagnostic

### `extract_ducts.py`

設備 IFC からダクトを抽出し、数量算出に必要な幾何・System 情報を CSV
化します。

**主な出力:** `output/ducts_detail.csv`\
**Status:** Current / Reproducible

### `summarize_ducts.py`

`ducts_detail.csv` をもとにダクト数量を集計します。

**主な出力:** `output/ducts_summary.csv`\
**Status:** Current / Reproducible

------------------------------------------------------------------------

## 6. IFC 調査・互換性確認ツール

### `inspect_ifc_application.py`

IFC
Schema、Header、OwnerHistory、作成アプリケーション等を確認する汎用診断ツールです。

### `inspect_ifc_compatibility.py`

複数 IFC の Entity
や構造を比較し、後続処理を実行できるかを事前確認します。

### `inspect_ifc_placements.py`

建築 IFC と設備 IFC の Placement・座標系を調査します。Space と MEP
要素を幾何的に対応付ける際の座標補正検討につながったツールです。

### `inspect_mep_entity_inventory.py`

IFC 内に実際に存在する MEP Entity、Port の親要素、Pset / Property
等を棚卸しします。「あるはずのクラス」を決め打ちせず、まず実データを観察するために使用します。

------------------------------------------------------------------------

## 7. ダクト Engineering Information 調査ツール

### `extract_duct_system_airflow.py`

formal な `IfcDistributionSystem` 等を利用し、SA / RA / OA / EA
などのダクト System と風量関連情報を抽出します。

### `inspect_duct_pressure.py`

ダクトに設定された圧力関連 Property
を調査し、数量だけでなく設備仕様・Engineering Information を IFC
から取得できるかを検証します。

### `inspect_duct_profiles.py`

Mapped representation や Boolean geometry を含む IFC Geometry
をたどり、ダクト Profile の表現方法を棚卸しします。

### `inspect_duct_outer_curves.py`

`IfcArbitraryClosedProfileDef` 等の `OuterCurve`
型を調査し、断面形状の表現方法を確認します。

### `inspect_duct_system_properties.py`

`IfcRelAssignsToGroup` 等による formal な `IfcDistributionSystem`
情報を調査します。ダクトの `Name` や `ObjectType` から System
を推定せず、IFC に明示された System 情報を確認することを重視します。

### `inspect_duct_system_equipment.py`

ダクト System に属する設備機器を棚卸しし、System と機器の関係を
Engineering Information として利用できるかを検証します。

### `inspect_duct_system_equipment_properties.py`

現在の実装では
`IfcFan`、`IfcAirToAirHeatRecovery`、`IfcAirTerminalBox`、 `IfcDamper`
の4クラスを対象に、Pset / Property と System 所属を調査します。

**主な出力:** `output/duct_system_equipment_properties.csv`

**Status:** Research

### `inspect_round_ducts.py`

丸ダクトについて Type、Material、Pset
等を棚卸しし、寸法・材料情報の取得可能性を確認します。

------------------------------------------------------------------------

## 8. 空間・施工箇所解析ツール

### `inspect_architecture_spaces.py`

建築 IFC の `IfcSpace` を棚卸しし、階、Space
名、位置・範囲等を調査します。設備要素の「天井内」「室内」「露出」等の施工箇所を建築
IFC との関係から判断できるかを検討する基礎データです。

### `match_pipes_to_spaces.py`

建築 IFC と設備 IFC の座標差を考慮し、配管中心位置と Space の Bounding
Box 等を比較します。`INSIDE_SPACE`、`ABOVE_SPACE`、`NO_MATCH`
等は最終判定ではなく、施工箇所推論のための **Geometric Evidence**
として扱います。

### `inspect_duct_ceiling_location.py`

ダクトと建築 Space / Ceiling
の位置関係から、天井内施工箇所の候補を調査します。曖昧なケースを無理に断定せず、観測された位置関係を
Evidence として保持します。

------------------------------------------------------------------------

## 9. 配管・接続・Topology 解析ツール

### `analyze_connected_port_distances.py`

接続されている Port 間の距離を分析し、IFC
で明示された接続と幾何的距離の関係を調査します。

### `analyze_ifc_port_connections.py`

IFC 全体の Port 接続情報を分析し、MEP 要素間の接続表現を確認します。
あわせて、SA / RA / OA / EA の対象ダクト System
について接続状況を集計します。

**主な出力:** `output/ifc_port_connections.csv`,
`output/duct_system_connection_summary.csv`

**Status:** Research

### `inspect_ifc_connectivity_relationships.py`

`IfcRelConnectsPorts`、`IfcRelConnectsPortToElement`、`IfcRelConnectsElements`、
Nesting、Aggregation、Grouping 等、接続や所属に関係する IFC Relationship
を調査します。

現在の実装は **EA18（EA 18 /
105_EA排気）を対象としたケーススタディ用**です。

**主な出力:** `output/ifc_connectivity_relationships_EA18.csv`

**Status:** Research

### `inspect_duct_port_geometry.py`

ダクト系統の Port
について、座標、方向、FlowDirection、親要素等を調査し、
明示的接続が不足する場合の幾何 Evidence を取得します。

現在の実装は **EA18（EA 18 /
105_EA排気）を対象としたケーススタディ用**です。

**主な出力:** `output/duct_port_geometry_EA18.csv`,
`output/duct_port_distances_EA18.csv`

**Status:** Research

### `trace_duct_system_topology.py`

指定したダクト System の Port / Connection をたどり、Topology
を抽出します。
明示的な接続が取得できないケースも研究結果として扱います。

現在の実装は **EA18（EA 18 /
105_EA排気）を対象としたケーススタディ用**です。

**主な出力:** `output/duct_system_topology_EA18.csv`

**Status:** Research

### `inspect_port_topology.py`

`IfcDistributionPort` の親要素、Nesting / Aggregation / Port-to-Element
関係、`IfcRelConnectsPorts` 等を総合的に棚卸しします。明示的な IFC
Connectivity と、後段の幾何推定・Engineering Inference
を分離するための基礎ツールです。

### `inspect_pipe_systems.py`

配管の System 情報について、Attribute、Pset、Type、Group / System
等の取得経路を、 IFC を変更せずに調査する診断ツールです。

**主な出力:** `output/pipe_system_inspection.csv`

**Status:** Diagnostic

### `inspect_target_pipe.py`

特定の配管要素を対象に IFC
に直接記録された情報を詳細確認します。直接確認できた情報を
**IFC_FACT**、IFC に存在しない情報を **NOT_IN_IFC**
として扱い、推論・Master・Rule と混ぜないことを重視します。

### `extract_ifc_system.py`

指定した階・System 等をもとに IFC サブモデルを抽出し、 対象を限定した
Topology / Geometry 調査に利用します。

現在の実装では対象条件が **`4FL / SA 7` に固定**されており、
`output/4FL_SA7.ifc` を生成します。現時点では任意の階・System を
コマンドライン引数で指定する汎用ツールではありません。

**Status:** Research

------------------------------------------------------------------------

## 10. Exploratory Scripts

現在の推奨ワークフローに含めない探索的スクリプトは
`research/archive/exploratory-scripts/` に保存します。

ここには、QTO
値からのダクト寸法推定、寸法計算誤差の調査、特定ダクト要素の Geometry
調査、ダクトと Space の初期診断、特定配管の接続追跡、System
情報を取り込む前のダクト抽出処理などが含まれます。

これらは「不要になった古いコード」ではありません。ENMA
では、**どのような仮説を立て、何を調べ、なぜ現在の方法へ至ったか**という研究過程も成果と考え、現行ツールとは分離して保存します。

------------------------------------------------------------------------

## 11. Output と Research Evidence

### `output/`

再現可能な代表結果を置きます。Git 管理している代表例は次のとおりです。

-   `pipes_detail.csv`
-   `pipes_summary.csv`
-   `ducts_detail.csv`
-   `ducts_summary.csv`
-   `pipe_fittings_detail.csv`
-   `pipe_fittings_summary.csv`
-   `fitting_port_inventory.csv`

通常の調査・診断スクリプトが生成する CSV は再生成可能なため、原則 Git
管理しません。

### `research/evidence/`

研究上、結果そのものを保存する意味がある Evidence を置きます。

例：`research/evidence/duct-connectivity/EA18/`

EA18 では Port Geometry、Port 間距離、IFC Relationship、Topology
抽出結果等を保存しています。`duct_system_topology_EA18.csv`
がヘッダーのみで 0 行であることも、**現在の明示的な IFC 接続情報から
EA18 Topology を取得できなかったという観測結果**として扱います。

### `research/archive/`

現在の推奨実装へ至るまでの探索的コードを保存します。

------------------------------------------------------------------------

## 12. ENMA の開発・研究上の考え方

### 12.1 IFC Fact と推論を混ぜない

``` text
IFC Fact
    ↓
Geometric Evidence
    ↓
Engineering Inference
    ↓
Human Review
    ↓
Engineering Information
```

-   **IFC Fact** --- IFC の Entity、Attribute、Property、Relationship
    等から直接確認できる情報
-   **Geometric Evidence** --- 座標、距離、方向、Bounding Box、Space
    との位置関係等から得られる観測情報
-   **Engineering Inference** --- IFC Fact と Geometric Evidence
    に設備工学上のルール、仕様、Master Data 等を加えて導く推論
-   **Human Review** ---
    自動推論だけでは確定できないケースを設備技術者が確認する段階

この区別は、数量算出や Engineering Information
の「根拠」を追跡可能にするために重要です。

### 12.2 「情報がない」と「存在しない」を区別する

IFC に接続 Relationship
が見つからないからといって、実際の設備として接続していないとは限りません。また、短い距離に
Port が存在するからといって、接続していると断定することもできません。

情報不足や曖昧性を隠さず Evidence として保持し、必要に応じて Engineering
Inference または Human Review へ渡します。

### 12.3 Measurement と Estimation を区別する

IFC Geometry
から測定できる数量と、施工・積算上必要となる数量は必ずしも同一ではありません。配管では、芯々長さ、実長、Property
に記録された長さ、継手長、保温・塗装、施工箇所等を区別して扱う必要があります。

------------------------------------------------------------------------

## 13. 現在の研究テーマとの関係

接続研究では、明示的な IFC Connectivity
が不足するケースについて、`IfcDistributionPort`、`IfcRelConnectsPorts`、Port
の親 MEP 要素、座標、方向、`FlowDirection`、System
membership、ダクト・継手・機器の種類、断面・寸法、Port
間距離等を組み合わせて検証します。

``` text
Explicit IFC Connectivity
        ↓
Geometric Candidate
        ↓
Engineering Candidate
        ↓
Human Review（必要な場合）
```

候補を直ちに「接続」と断定しないことを原則とします。

------------------------------------------------------------------------

## 14. 今後の拡張

-   ダクト接続 Topology の推定
-   Port Geometry を用いた接続候補抽出
-   Construction Location の判定
-   配管・ダクトの保温・塗装条件
-   継手を含む施工数量
-   Engineering Information と数量算出の統合
-   Human Review による推論結果確認
-   IDS による必要情報チェック
-   bSDD による意味・分類情報との連携
-   RDB による数量・仕様・歩掛・根拠情報の管理
-   Graph / Topology 情報の利用

------------------------------------------------------------------------

## 15. ディレクトリの役割

``` text
src/
    現在使用する数量算出・調査・研究ツール

output/
    代表的な再現結果
    通常の生成 CSV は原則 Git 管理しない

research/evidence/
    研究上保存する意味のある検証結果

research/archive/
    探索的コード・研究過程

docs/
    再現手順、FAQ、技術ガイド等
```

------------------------------------------------------------------------

## 16. このガイドの更新について

新しい Python ツールを `src/`
に追加した場合は、可能な限り本書にも次の情報を追加します。

1.  スクリプト名
2.  Category
3.  目的
4.  主な入力
5.  主な出力
6.  ENMA での位置づけ
7.  Status

研究途中で役割を終えたスクリプトは、必要に応じて `research/archive/`
へ移し、研究履歴として残すことを検討します。

------------------------------------------------------------------------

## 17. 関連ドキュメント

-   `README.md` --- ENMA PoC 全体概要
-   `docs/FAQ.md` --- ENMA 3.0 FAQ（英語）
-   `docs/FAQ_ja.md` --- ENMA 3.0 FAQ（日本語）
-   `docs/REPRODUCE_PIPE_RESULTS.md` --- 配管結果の再現手順（英語）
-   `docs/REPRODUCE_PIPE_RESULTS_ja.md` --- 配管結果の再現手順（日本語）
-   `research/archive/exploratory-scripts/README.md` ---
    探索的スクリプトの位置づけ
-   `research/evidence/duct-connectivity/EA18/README.md` --- EA18
    接続研究 Evidence

------------------------------------------------------------------------

*ENMA-WG --- Engineering Meaning Automation*\
*Engineering Knowledge for Everyone*
