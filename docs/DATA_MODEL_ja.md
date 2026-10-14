# ENMA 数量算出データモデル

**ENMA 数量算出データモデル（ENMA Quantity Takeoff Data Model）**は、IFCデータを、明示的かつ追跡可能な工学的解釈を通じて、エンジニアリング数量へ変換する方法を示すものです。

これは、**buildingSMART International Summit Tokyo 2026** で発表するENMA-WGのアプローチを支える概念データモデルです。

中心となる考え方は、次のとおりです。

```text
IFC Data
    ↓
Engineering Meaning
    ↓
Engineering Quantity
```

施工数量は、単にIFCから読み取るだけで得られるものではありません。

IFCは、形状、プロパティ、分類、システム、ポート、接続、その他の関係性を提供します。MEPの数量算出では、これらのデータを、プロジェクト仕様、エンジニアリングマスターデータ、計算ルール、そして場合によっては人間の判断と組み合わせて解釈する必要があります。

ENMAデータモデルは、この解釈プロセスを明示的かつ追跡可能にすることを目的としています。

---

## 1. データモデルが必要な理由

単純な数量計算であれば、IFCモデルから長さ、面積、個数などを直接抽出するだけで十分に見えるかもしれません。

しかし、実際のMEP数量算出は、より複雑です。

たとえば配管数量は、幾何学的な長さだけでなく、次のような情報にも依存する場合があります。

- 系統
- 階またはスペース
- 配管サイズ
- 配管材質
- 施工場所
- 保温要件
- 塗装要件
- 適用されるプロジェクト仕様
- エンジニアリングルール
- 欠落または曖昧な情報

これらの値の一部は、IFCから直接読み取ることができます。

一方、それ以外の値については、IFC要素間の関係から導き出したり、エンジニアリング知識を用いて解釈したり、技術者による確認が必要になる場合があります。

ENMA数量算出データモデルでは、数量算出を単一のIFC抽出処理として扱うのではなく、これらの異なる役割を分離して扱います。

---

## 2. ENMA分類コードの読み方

ENMAデータモデルでは、テーブルとエンジニアリング情報を6つの主要カテゴリに分類しています。

| コード | カテゴリ | 目的 |
|---|---|---|
| **P** | Project / Transaction | プロジェクト固有のデータ、IFC要素、プロパティ、ポート、接続、計算トランザクション |
| **S** | Specification | 原典仕様、仕様セット、プロジェクトに適用される仕様 |
| **M** | Master | 流体、施工場所、材料、サイズなど、再利用可能なエンジニアリングマスターデータ |
| **R** | Rule | 仕様を解釈し、数量を決定するためのエンジニアリングルール |
| **I** | Inference / Evaluation | ENMAによる推論、ルール評価、技術者によるレビュー |
| **O** | Output / Result | 要素単位の結果、数量集計、計算根拠 |

`M10`、`I20`、`O30` などのコードは、ENMAデータモデルを整理するために使用する分類識別子です。

さらに詳細なコードによって、個々のグループやテーブルを識別します。

たとえば、次のようになります。

```text
M
└─ M10
   ├─ M10-01
   └─ M10-02
```

このコード体系によって、それぞれのテーブルがエンジニアリング情報モデル全体のどこに位置するのかを把握しやすくしています。

---

## 3. 例：M10の読み方

`M` は **Master Data（マスターデータ）** を表します。

Master Dataカテゴリの中で、`M10` は **Common / Classification（共通／分類）** のマスターデータを表します。

たとえば、次のような階層になります。

```text
M  Master
│
├─ M10  Common / Classification
│   ├─ M10-01  fluids
│   └─ M10-02  work_locations
│
├─ M20  Material / Product
│   └─ M21  Pipe
│       ├─ M21-01  pipe_materials
│       ├─ M21-02  pipe_standards
│       └─ M21-03  pipe_sizes
│
└─ ...
```

この階層構造によって、再利用可能なエンジニアリング知識と、個々のIFCプロジェクトに固有の情報を分離します。

たとえば、IFCモデルには配管径や系統名が含まれている場合があります。一方、エンジニアリングマスターデータでは、それに対応する配管規格、呼び径、材料情報など、数量算出に必要となる追加情報を提供できます。

同じマスターデータを複数のプロジェクトで再利用することも可能になります。

---

## 4. IFCデータからエンジニアリング数量へ

ENMA全体の考え方は、次のような情報フローとして捉えることができます。

```text
Project / IFC Data (P)
          │
          ▼
   ┌───────────────┐
   │ Specification │  (S)
   ├───────────────┤
   │ Master Data   │  (M)
   ├───────────────┤
   │ Rules         │  (R)
   └───────────────┘
          │
          ▼
Inference / Evaluation (I)
          │
          ▼
   Output / Result (O)
```

それぞれのカテゴリには異なる役割があります。

**Project / Transaction（P）** は、プロジェクトおよびIFCモデルに固有の情報を格納します。

**Specification（S）** は、プロジェクトに適用される仕様や要件を表します。

**Master（M）** は、再利用可能なエンジニアリング知識を提供します。

**Rule（R）** は、利用可能な情報を解釈するために使用するエンジニアリングロジックを表します。

**Inference / Evaluation（I）** は、自動的な解釈、ルール評価、技術者によるレビューの結果を記録します。

**Output / Result（O）** は、算出された数量と、その算出に使用した根拠を格納します。

この分離が重要なのは、同じIFCジオメトリであっても、適用される仕様、材料、施工条件、エンジニアリングルールによって、異なるエンジニアリング数量が生じる可能性があるためです。

---

## 5. Human-in-the-Loop Engineering

ENMAでは、すべてのエンジニアリング上の判断を自動化できる、あるいは自動化すべきであるとは考えていません。

MEPモデルには、次のような状況が存在する場合があります。

- プロパティの欠落
- 曖昧な分類
- 不完全な関係性
- プロジェクト固有の規約
- 技術者による判断を必要とする情報

このため、データモデルには人間によるレビュープロセスを組み込んでいます。

簡略化したフローは次のとおりです。

```text
I10-01  inference_results
            │
            ▼
I20-01  human_reviews
            │
            ▼
I10-02  rule_evaluations
            │
            ▼
O10-01  element_quantity_results
            │
            ▼
O20-01  quantity_summaries
            │
            ▼
O30-01  calculation_evidence
```

`inference_results` には、ENMAがIFCデータとエンジニアリング知識から推論した内容を記録できます。

推論結果が不確実である場合や確認を必要とする場合、`human_reviews` によって技術者がその推論をレビューできます。

レビューされた情報は、その後のルール評価や数量計算に使用できます。

最後に、`calculation_evidence` は、計算結果の根拠を保存することを目的としています。

したがって、目標は単純な、

```text
IFC → Quantity
```

ではなく、

```text
IFC
 ↓
Interpretation
 ↓
Engineering Review where necessary
 ↓
Rule Evaluation
 ↓
Quantity
 ↓
Evidence
```

というプロセスです。

これによって、数量算出プロセスの透明性と監査可能性を高めます。

---

## 6. 例：配管数量算出

現在のENMA PoCでは、実際のIFC配管データを使用して、このアプローチの簡単な例を示しています。

IFCレベルでは、`IfcPipeSegment` に次のような情報が含まれている、または関連付けられています。

- GlobalId
- ジオメトリ
- 長さ
- 系統
- プロパティ
- 配置
- 接続

ENMAは、これらのIFC情報をエンジニアリング向けの属性へ変換します。

現在の配管PoCでは、次のような属性を扱っています。

- 階
- 系統コード
- 系統名称
- IFC系統分類
- 外径
- 内径
- 配管長
- 方向区分
- 軸方向
- 高さ範囲

簡略化した解釈フローは次のとおりです。

```text
IfcPipeSegment
       │
       ▼
IFC properties and relationships
       │
       ▼
Engineering attributes
       │
       ▼
Floor × System × Diameter × Direction
       │
       ▼
Quantity summary
```

現在のIFCサンプルモデルを使用すると、PoCでは次の結果が得られます。

```text
IfcPipeSegment      : 252
Summary rows        : 138
Total length        : 649.090 m
Horizontal length   : 375.963 m
Vertical length     : 273.127 m
Sloped length       :   0.000 m
```

これらの結果は、次のスクリプトを使用して再現できます。

- `src/extract_pipes.py`
- `src/summarize_pipes.py`

結果は、次のファイルで確認できます。

- `output/pipes_detail.csv`
- `output/pipes_summary.csv`

再現手順については、次のドキュメントを参照してください。

- [`REPRODUCE_PIPE_RESULTS.md`](REPRODUCE_PIPE_RESULTS.md)
- [`REPRODUCE_PIPE_RESULTS_ja.md`](REPRODUCE_PIPE_RESULTS_ja.md)

---

## 7. 関係性からもエンジニアリング上の意味を得る

エンジニアリングに必要な情報が、必ずしも数量算出対象となる要素そのもののプロパティとして存在するとは限りません。

たとえば、現在の継手PoCでは、配管継手に関する情報を、接続された配管セグメントとの関係から導き出すことができます。

簡略化すると、次のようになります。

```text
IfcPipeFitting
       │
       ▼
IfcDistributionPort / Connections
       │
       ▼
Connected IfcPipeSegment
       │
       ▼
Pipe outside diameter
       │
       ▼
Fitting connection diameter
```

これは、ENMAの重要な原則の一つを示しています。

> エンジニアリング上の意味は、IFC要素そのものだけでなく、その関係性やコンテキストからも得られる場合があります。

数量算出に、系統、スペース、施工場所、継手、保温、その他のエンジニアリング条件に関する情報が必要になるほど、この考え方は重要になります。

---

## 8. 現在のPoCの範囲

このデータモデルは、現在公開しているPoCで実装済みの機能よりも、広いエンジニアリングの枠組みを表しています。

### 現在のPoCで実証しているもの

現在のリポジトリでは、特に次の内容を実証しています。

- IFC配管要素の抽出
- 系統の識別
- 配管径の抽出
- 配管長の抽出
- 水平／垂直方向の分類
- 配管数量の集計
- 配管継手の抽出
- 継手の分類
- 継手接続径を求めるための接続配管情報の利用

### 設計済み、または開発中のもの

より広範なENMAデータモデルでは、次のような領域も扱います。

- 施工場所の解釈
- プロジェクト仕様
- 配管材質・規格のマッピング
- 保温要件
- 塗装要件
- 労務歩掛
- ルールベースのエンジニアリング解釈
- 推論結果に対する人間のレビュー
- 計算根拠
- ダクト数量算出ワークフロー
- 機器関連ワークフロー

データモデルにカテゴリやテーブルが存在することは、**対応するすべての機能が現在のPoCですでに実装されていることを意味するものではありません。**

このデータモデルは、数量算出プロセスを段階的に拡張していくためのフレームワークを提供することを目的としています。

---

## 9. トレーサビリティ

ENMAアプローチの主要な目的の一つは、トレーサビリティです。

算出されたエンジニアリング数量について、最終的には次のような問いに答えられることを目指しています。

```text
Which IFC element produced this quantity?

Which IFC properties or relationships were used?

Which engineering master data were applied?

Which project specification was applied?

Which rule produced the interpretation?

Was any information inferred?

Was the inference reviewed by an engineer?

What calculation produced the final quantity?
```

ENMAが、プロジェクトデータ、エンジニアリング知識、推論、人間によるレビュー、数量結果、計算根拠を分離しているのは、このためです。

目標は単に数値を算出することではなく、その数値の背後にあるエンジニアリング上の判断・推論を保存することにもあります。

---

## 10. 詳細なテーブル定義

このドキュメントは、ENMA数量算出データモデルを理解するための概念的なガイドです。

詳細なテーブルおよびフィールド定義は、次のファイルで管理しています。

**[`ENMA_Data_Model.xlsx`](ENMA_Data_Model.xlsx)**

このスプレッドシートには、現在進行中のENMA-WGの設計作業で使用している詳細なテーブル構造が含まれています。

PoCが基本的なIFC数量抽出から、より広範なMEPエンジニアリング数量算出へ拡張されるにつれて、データモデルも継続的に発展していきます。

---

## 関連ドキュメント

- [`REPRODUCE_PIPE_RESULTS.md`](REPRODUCE_PIPE_RESULTS.md) — Tokyo Summitで示した配管数量結果の再現手順
- [`REPRODUCE_PIPE_RESULTS_ja.md`](REPRODUCE_PIPE_RESULTS_ja.md) — 配管数量結果の日本語版再現手順
- [`ENMA_Data_Model.xlsx`](ENMA_Data_Model.xlsx) — ENMAの詳細テーブル定義

---

## ENMA-WG

ENMA-WGは、openBIM / IFCデータと、MEPのエンジニアリング知識および数量算出を結び付けるための実践的な方法を検討しています。

目的は、単にIFCからデータを抽出することではありません。

モデルデータから施工数量に至るまでの**エンジニアリング上の解釈を、明示的で、再利用可能かつ追跡可能なものにすること**を目指しています。