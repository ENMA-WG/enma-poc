# ENMA-WG PoC

**openBIM | MEP | Quantity Takeoff**

🌐 **English:** [README.md](README.md)

## Revisiting the Promise of Automated MEP Quantity Takeoff

**buildingSMART International Summit Tokyo 2026** で発表した Proof of Concept（PoC）です。

> **IFC Data → Engineering Meaning → Engineering Quantity**  
> **IFCデータ → エンジニアリング上の意味 → エンジニアリング数量**

設備（MEP）の数量算出は、BIMモデルから形状情報を取り出すだけでは実現できません。

IFCモデルから、配管が存在すること、その位置、長さを取得することはできます。  
しかし、設備技術者が実際に利用できる数量を算出するためには、さらに次のような情報が必要です。

- その要素は、どの系統に属しているのか？
- そのサイズは、設備上どのような意味を持つのか？
- どこに施工されているのか？
- どの仕様が適用されるのか？
- 継手、保温、塗装、労務をどのように考慮するのか？
- どの情報が不足しており、技術者の判断が必要なのか？

ENMA-WG PoCでは、openBIM技術と明示的なエンジニアリングルールを用いて、**IFCデータ**と、実務で利用できる**エンジニアリング数量**との間をどのようにつなぐことができるかを検証しています。

---

## IFCデータからエンジニアリング数量へ

```text
IFC Data（IFCデータ）
   │
   │  Geometry / Properties / Relationships
   │  形状 / プロパティ / 関係
   ▼
Engineering Meaning（エンジニアリング上の意味）
   │
   │  Classification / System / Size / Location
   │  分類 / 系統 / サイズ / 施工箇所
   │  IDS / bSDD / Specifications / Engineering Rules
   │  IDS / bSDD / 仕様 / エンジニアリングルール
   ▼
Engineering Quantity（エンジニアリング数量）
      Length / Count / Surface / Insulation / Painting / Labor ...
      長さ / 個数 / 表面積 / 保温 / 塗装 / 労務 ...
```

目的は、単に**BIMオブジェクトを数えること**ではありません。

BIMモデルから最終的な数量に至るまでの判断過程を、**明示し、確認でき、再現できるようにすること**が目標です。

---

## このリポジトリで確認できること

### 主なドキュメント

- [ENMA 3.0 FAQ](docs/FAQ_ja.md) — ENMAの考え方、Engineering Knowledge、Human Review、今後の方向をQ&A形式で確認できます。
- [Sample Outputs — 日本語](docs/SAMPLE_OUTPUTS_ja.md) — 配管・継手の代表的な出力例と、そこからエンジニアリング上の意味をどのように導くかを確認できます。
- [Data Model — 日本語](docs/DATA_MODEL_ja.md) — 仕様、推論、技術者による確認、ルール、数量結果を扱うENMAのデータ構造を確認できます。
- [Pipe Result Reproduction — 日本語](docs/REPRODUCE_PIPE_RESULTS_ja.md) — Tokyo Summitで示した配管数量の再現手順を確認できます。
- [ダクト形状・QTO検証・系統情報抽出](docs/DUCT_EXTRACTION_ja.md) — 1,077個の `IfcDuctSegment` をIFC Geometryから抽出し、IFC QTOとのクロスチェックおよび `IfcDistributionSystem` からの系統情報取得を確認できます。
- [ダクト Engineering Information 検証](docs/DUCT_ENGINEERING_INFORMATION_ja.md) — 再現可能なダクト数量から仕様選定へ進む際に、どのEngineering Informationが取得でき、何が不足するかを確認できます。

英語版も用意しています。

- [ENMA 3.0 FAQ](docs/FAQ.md)
- [Sample Outputs](docs/SAMPLE_OUTPUTS.md)
- [ENMA Quantity Takeoff Data Model](docs/DATA_MODEL.md)
- [Reproducing the Pipe Quantity Results](docs/REPRODUCE_PIPE_RESULTS.md)
- [Duct Geometry, QTO Validation, and System Extraction](docs/DUCT_EXTRACTION.md)
- [Duct Engineering Information Validation](docs/DUCT_ENGINEERING_INFORMATION.md)

このリポジトリはTokyo Summitでの発表内容に対応しており、次のことができます。

- **PoCを確認する** — 実際の設備IFCデータがどのように処理されるかを確認できます。
- **アプローチを確認する** — IFC要素からエンジニアリング数量へ変換していく過程を追うことができます。
- **結果を再現する** — スクリプトを実行し、生成されたCSV出力と結果を比較できます。
- **データモデルを確認する** — IFCデータ、仕様、推論、技術者による確認、数量結果がどのように分離されているかを確認できます。
- **フィードバックを共有する** — 前提条件、不足情報、実務上の数量算出要件についてGitHub Issuesで議論できます。

---

## Proof of Concept

現在のPoCでは、まず日本の実在する公共建築BIMモデルを用いた**設備配管**を対象としています。

サンプルモデルから、処理パイプラインによって次の情報を抽出・確認しています。

- **252個の `IfcPipeSegment` 要素**
- **81個の `IfcPipeFitting` 要素**
- 配管の系統、サイズ、階、方向、長さ
- 水平配管・垂直配管の数量
- IFC情報だけでは設備数量を確定できないケース

### 配管数量の結果

Tokyo Summitの発表で使用した、再現可能な配管長の結果は次のとおりです。

| 数量 | 結果 |
|---|---:|
| 配管総延長 | **649.090 m** |
| 水平 | **375.963 m** |
| 垂直 | **273.127 m** |
| 集計行数 | **138** |
| スキップされた配管要素 | **0** |

これらの結果はENMAのアプローチにとって**出発点であり、ゴールではありません**。

次の問いは、

> **幾何学的には正しいIFC数量を、設備技術者が実際に使える数量へ、どのように変換するか？**

です。

詳細な再現手順はこちらです。

- [配管数量結果の再現手順](docs/REPRODUCE_PIPE_RESULTS_ja.md)
- [English version](docs/REPRODUCE_PIPE_RESULTS.md)

### ダクト形状・QTO検証・系統情報抽出

PoCでは、`IfcDuctSegment` のGeometry抽出、QTOクロスチェックに加え、正式なIFC関係をたどった空調系統情報の取得にも対象を拡張しています。

現在のMLIT検証IFCでの結果：

| 検証項目 | 結果 |
|---|---:|
| IfcDuctSegment | **1,077** |
| 丸ダクト | **792** |
| 角ダクト | **285** |
| UNKNOWN | **0** |
| Geometry抽出 | **1,077 / 1,077** |
| Geometry/QTO長さ一致 | **1,077 / 1,077** |
| 角ダクト断面積一致 | **285 / 285** |
| `IfcDistributionSystem` が1系統 | **1,077 / 1,077** |
| 系統割当なし | **0** |
| 複数系統割当 | **0** |

現在の検証IFCでは、`IfcDistributionSystem.ObjectType` をENMAのAirTypeへ次のように明示的に対応付けています。

| AirType | ダクト本数 |
|---|---:|
| SA | **512** |
| RA | **4** |
| OA | **112** |
| EA | **449** |
| UNKNOWN | **0** |

CSVにはIFC由来の系統 `Name` と `ObjectType` をそのまま保持します。SA/RA/OA/EAは `IfcDistributionSystem.ObjectType` からの明示的なENMAマッピングであり、**ダクト要素のNameから推定したものではありません**。

丸ダクトでは、Geometryから算出した円断面積とQTO `GrossCrossSectionArea`との間に、一貫して **0.015038%** の差が確認されました。このPoCでは、許容値を緩和して差を隠すのではなく、差異そのものを検証結果として保持しています。

また、IFC Geometryの寸法を呼称寸法へ自動的に丸めることはせず、元のGeometry値を保持しています。

- [ダクト形状・QTO検証・系統情報抽出](docs/DUCT_EXTRACTION_ja.md)
- [English version](docs/DUCT_EXTRACTION.md)

---

## 目的

このPoCでは、IFC、IDS、bSDD、設備仕様、軽量なソフトウェアツールを組み合わせることで、実務的な設備数量算出ワークフローをどのように支援できるかを検証します。

主な対象は次のとおりです。

- IFCの形状・プロパティ抽出
- 設備機器、ダクト、配管の識別
- 数量算出
- IFCデータ品質の確認
- IDSによる情報要件
- bSDDによる意味情報の補強
- 明示的なエンジニアリングルール
- 不確実な情報や推論結果に対する技術者の確認
- 再現可能なopenBIMワークフロー

また、本プロジェクトでは次の根本的な問いについても検討しています。

> **どの情報をIFCモデル内に持たせるべきか。そして、どの情報をエンジニアリング知識、仕様、あるいは技術者の判断によって補う必要があるのか？**

---

## ENMAのアプローチ

ENMAでは、数量算出を単一の計算ではなく、ひとつの**プロセス**として捉えます。

```text
IFC Model
    │
    ▼
Element Extraction
要素抽出
    │
    ▼
Engineering Interpretation
エンジニアリング上の解釈
    │
    ├── IFC properties and relationships
    │   IFCプロパティ・関係
    ├── IDS information requirements
    │   IDS情報要件
    ├── bSDD semantic definitions
    │   bSDD意味定義
    ├── Engineering specifications
    │   設備仕様
    └── Engineering rules
        エンジニアリングルール
    │
    ▼
Inference / Missing Information Detection
推論 / 不足情報の検出
    │
    ▼
Human Review
技術者による確認
    │
    ▼
Quantity Calculation
数量計算
    │
    ▼
Traceable Engineering Quantity
根拠を追跡可能なエンジニアリング数量
```

このように処理を分離することが重要なのは、設備数量の算出では、形状情報だけからは得られない情報がしばしば必要になるためです。

そのため、ENMAの長期的なデータモデルでは次の情報を分離して管理します。

- 元となるIFC要素
- 案件適用仕様
- 参照データ／マスタデータ
- 推論結果
- 技術者による確認
- ルール評価結果
- 最終的な数量結果

このアーキテクチャは、各数量が**どのような根拠と判断から算出されたかを追跡できること**を目的としています。

詳細なアーキテクチャとテーブル体系については、[ENMA数量算出データモデル](docs/DATA_MODEL_ja.md)を参照してください。

---

## リポジトリ構成

```text
enma-poc/
├── data/           サンプルデータ情報・データ出典に関する注記
├── docs/           アーキテクチャ・方法論
├── output/         生成CSV・PoC出力例
├── presentation/   Tokyo Summit発表資料
├── src/            PoCソースコード
├── tests/          テスト
├── LICENSE
├── README.md
└── README_ja.md
```

### `src/`

IFCの調査、抽出、数量処理を行うPythonスクリプトです。

配管PoCには、次のような処理を行うスクリプトが含まれています。

- 配管情報の抽出
- 配管数量の集計
- 配管系統の調査
- 継手サイズ・接続情報の調査

### `output/`

生成されたCSVファイルと、代表的なPoC結果を格納します。

配管・継手CSV出力と設備数量算出との関係については、[Sample Outputs — 日本語](docs/SAMPLE_OUTPUTS_ja.md)を参照してください。

### `docs/`

ENMAの方法論、アーキテクチャ、データモデル、設備上の前提条件に関するドキュメントを格納します。

### `presentation/`

次の発表に関連する資料を格納します。

**Revisiting the Promise of Automated MEP Quantity Takeoff**  
buildingSMART International Summit Tokyo 2026

---

## サンプルBIMデータ

PoCでは、日本の国土交通省（**MLIT: Ministry of Land, Infrastructure, Transport and Tourism**）が公開している**官庁営繕BIMモデル（Revit版）**を使用しています。

元のAutodesk Revit 2022モデルをIFCへ変換し、ENMA-WGにおける研究・実証のために処理しています。

元のBIMデータは、**このリポジトリでは配布していません**。

ワークフローを再現する場合は、元データの提供元からBIMデータを入手し、対応するIFCファイルを準備してください。

サンプルデータおよび変換時の前提条件に関する追加情報は、`data/` 以下に記載します。

---

## 開発環境

現在のPoCは、主に次の環境で開発・テストしています。

- Windows 11
- Python 3.11.9
- IfcOpenShell 0.8.5
- Git

リポジトリには次のファイルが含まれています。

- `requirements.txt` — Pythonパッケージ依存関係
- `scripts/check_environment.ps1` — Windows開発環境チェック用スクリプト

### クイックスタート

以下はWindows PowerShellでの基本的なセットアップ例です。

#### 1. リポジトリをクローン

```powershell
git clone https://github.com/ENMA-WG/enma-poc.git
cd enma-poc
```

#### 2. Python仮想環境を作成

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### 3. 必要なパッケージをインストール

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. 開発環境を確認

```powershell
.\scripts\check_environment.ps1
```

基準環境では、現在Python 3.11.9およびIfcOpenShell 0.8.5を使用しています。

環境チェッカーではPython 3.11.9を基準バージョンとして扱い、それ以外のPython 3.11系パッチバージョンについては警告として表示します。

#### 5. IFCファイルを準備

配管PoCで使用するIFCモデルを次の場所に配置します。

```text
data/営繕BIMモデル_EM.ifc
```

元となるBIM/IFCモデルは、このリポジトリでは再配布していません。元データの提供元からBIMデータを入手し、対応するIFCファイルを準備してください。

入力ファイルの準備方法と前提条件の詳細については、次を参照してください。

- [配管数量結果の再現手順](docs/REPRODUCE_PIPE_RESULTS_ja.md)
- [English version](docs/REPRODUCE_PIPE_RESULTS.md)

#### 6. 配管数量PoCを実行

```powershell
python .\src\extract_pipes.py
python .\src\summarize_pipes.py
```

期待される結果は次のとおりです。

```text
Pipe segments : 252
Summary rows  : 138
Skipped       : 0

Total length      : 649.090 m
Horizontal length : 375.963 m
Vertical length   : 273.127 m
Sloped length     : 0.000 m
```

#### 7. ダクト抽出・系統検証PoCを実行

```powershell
python .\src\extract_ducts.py
```

期待される検証結果には、**1,077個の `IfcDuctSegment`**（**丸ダクト792個、角ダクト285個**）が含まれます。1,077要素すべてでGeometry抽出に成功し、Geometryから得た長さとIFC QTOの長さが1,077要素すべてで一致します。また、1,077要素すべてに `IfcDistributionSystem` が1系統ずつ割り当てられており、現在のマッピング結果は **SA 512 / RA 4 / OA 112 / EA 449 / UNKNOWN 0** です。

Geometryの前提条件、系統情報の抽出、検証許容値、出力列、Geometry/QTO間で確認された差異の詳細は、[ダクト形状・QTO検証・系統情報抽出](docs/DUCT_EXTRACTION_ja.md)を参照してください。

---

## 配管数量結果の再現

基本的な処理フローは次のとおりです。

```text
IFC model
    │
    ▼
src/extract_pipes.py
    │
    ▼
output/pipes_detail.csv
    │
    ▼
src/summarize_pipes.py
    │
    ▼
output/pipes_summary.csv
    │
    ▼
Tokyo Summit PoC Results
```

目標となる結果は次のとおりです。

```text
IfcPipeSegment : 252
Total Length   : 649.090 m
Horizontal     : 375.963 m
Vertical       : 273.127 m
Summary Rows   : 138
Skipped        : 0
```

詳細なコマンド、入力ファイルの準備、前提条件、検証手順については次を参照してください。

- [配管数量結果の再現手順](docs/REPRODUCE_PIPE_RESULTS_ja.md)
- [English version](docs/REPRODUCE_PIPE_RESULTS.md)

---

## なぜ「エンジニアリング上の意味」が重要なのか

IFCから取得した配管長が、そのまま施工数量になるわけではありません。

例えば、実務的な設備数量算出には次のような情報も必要になります。

- 配管の呼び径と実外径
- 管材
- 系統・流体
- 施工箇所
- 露出・隠蔽
- 保温仕様
- 塗装仕様
- 継手の扱い
- 適用される設計仕様・施工仕様
- 労務歩掛
- 情報が不足・曖昧な場合の技術者による確認

そのためENMAでは、IFCを重要な**エンジニアリング情報の情報源**として扱いますが、IFCだけですべてのエンジニアリング知識を表現できるとは考えていません。

openBIMデータと、実際の数量算出に必要なエンジニアリング知識をつなぐことを目指しています。

---

## 現在の状況

このリポジトリは**Proof of Concept（PoC）**であり、現在も開発を進めています。

現在取り組んでいる内容には、次のものがあります。

- 配管数量の抽出
- 配管継手の調査
- 施工箇所の解釈
- ダクトGeometry抽出、QTOクロスチェック、`IfcDistributionSystem`系統情報抽出
- 設備仕様とのマッピング
- 推論と技術者確認のワークフロー
- 数量・労務データモデル

したがって、現在の実装は本番用の積算システムではなく、**研究・検証段階の実験的なワークフロー**としてご理解ください。

---

## フィードバック

次のような方々からのフィードバックを歓迎します。

- 設備技術者
- 積算担当者
- BIM実務者
- IFCソフトウェア開発者
- openBIM研究者
- buildingSMARTコミュニティの皆様

特に、次のような実務上の問いについて意見交換できればと考えています。

- IFCのどの情報が数量算出に十分な信頼性を持つのか？
- 通常、どのようなエンジニアリング情報が不足するのか？
- どの判断には、依然として技術者の確認が必要なのか？
- 数量計算の前提条件をどのように記録すべきか？
- IDSやbSDDを実務的な設備ワークフローにどう活用できるか？
- openBIMによる数量結果をどのように検証すべきか？

コメント、質問、ご提案は **GitHub Issues** へお寄せください。

---

## ENMA-WG

ENMA-WGでは、設備エンジニアリングにおけるopenBIMの実践的な活用を検討しています。

私たちの目的は、既存業務を単に自動化することではありません。

数量算出の背景にあるエンジニアリング知識を、**明示し、構造化し、再利用可能にし、誰もが検証できる形にすること**を目指しています。

---

## ライセンス

このリポジトリでENMA-WGが開発したソースコードは、**MIT License**のもとで提供しています。

第三者が提供するBIMデータ、文書、その他の資料については、それぞれのライセンスおよび利用条件に従います。

PoCで使用している官庁営繕BIMモデルは、このリポジトリの一部として再配布していません。
