# 配管数量算出結果の再現

## 概要

本ドキュメントでは、以下の発表で提示した配管数量算出結果を再現する方法について説明します。

**Revisiting the Promise of Automated MEP Quantity Takeoff**  
buildingSMART International Summit Tokyo 2026

このPoC（概念実証）の目的は、IFCジオメトリから数量を算出することだけではありません。計算プロセスを**明確化し、検証可能かつ再現可能なものにすること**も目的としています。

基本的なワークフローは以下のとおりです。

```text
IFC Model
   ↓
IfcPipeSegment extraction
   ↓
Engineering interpretation
   ↓
pipes_detail.csv
   ↓
Quantity aggregation
   ↓
pipes_summary.csv
   ↓
Engineering Quantity
```

Tokyo Summit 2026のPoCでは、日本の国土交通省が公開しているBIMサンプルデータから作成したMEP IFCモデルを使用して、このワークフローを検証しました。

---

## 期待される結果

Tokyo Summit 2026で発表した配管数量算出結果は以下のとおりです。

| 項目 | 結果 |
|---|---:|
| IfcPipeSegment | 252 |
| 集計行数 | 138 |
| スキップされた要素 | 0 |
| 配管総延長 | 649.090 m |
| 水平配管延長 | 375.963 m |
| 垂直配管延長 | 273.127 m |
| 傾斜配管延長 | 0.000 m |

これらの値は、Tokyo Summit 2026での発表に先立ち、**2026年10月1日**に現在のPoCコードから再度再現されたものです。

---

## 前提条件

このPoCは、主に以下の環境で開発およびテストしています。

- Windows 11
- Python 3.11
- IfcOpenShell
- Git

以下のコマンドは、リポジトリのルートディレクトリから実行してください。

例：

```text
G:\enma-wg\enma-poc
```

Pythonの仮想環境の使用を推奨します。

Windows PowerShellでの例：

```powershell
.venv\Scripts\Activate.ps1
```

> PoCリポジトリの改良に伴い、具体的な環境設定や依存関係のインストール手順は今後更新される可能性があります。

---

## IFCファイルの準備

現在、抽出スクリプトでは以下のIFCファイルを想定しています。

```text
data/営繕BIMモデル_EM.ifc
```

このPoCで使用しているサンプルは、日本の国土交通省（MLIT）が公開している**営繕BIMモデル**に基づいています。

元のモデルはAutodesk Revit 2022形式で提供されており、このPoCのためにIFC形式へ変換しました。

元となるBIM/IFCデータは、**このリポジトリでは再配布していません**。

ワークフロー全体を再現する場合は、元の提供元からBIMデータを入手し、対応するIFCファイルを用意してください。

現在の抽出スクリプトでは、以下の固定パスを使用しています。

```python
IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")
```

したがって、スクリプトを実行する前にIFCファイルをこの場所へ配置する必要があります。

---

## ステップ1 — 配管セグメントの抽出

以下を実行します。

```powershell
python .\src\extract_pipes.py
```

スクリプトはIFCモデルを開き、以下の要素を抽出します。

```text
IfcPipeSegment
```

Tokyo Summit 2026のサンプルモデルで想定される要素数は以下のとおりです。

```text
IfcPipeSegment count: 252
```

スクリプトは各配管セグメントを解析し、詳細な抽出結果を以下に出力します。

```text
output/pipes_detail.csv
```

抽出処理では、IFCジオメトリから配管の方向も解釈します。

例えば：

```text
axis=(1.0000, 0.0000, 0.0000)  → horizontal
axis=(0.0000, 1.0000, 0.0000)  → horizontal
axis=(0.0000, 0.0000, 1.0000)  → vertical
```

直交方向以外の水平ジオメトリが存在する場合もあります。

例えば：

```text
axis=(0.7071, -0.7071, 0.0000)
```

この場合も水平として分類されます。

想定される抽出結果の概要は以下のとおりです。

```text
========================================
Completed
========================================
Pipes : 252
CSV   : output\pipes_detail.csv

Direction summary
  水平管: 189
  立管: 63
```

この抽出処理では、配管セグメントの取りこぼしはありませんでした。

---

## ステップ2 — 配管数量の集計

`pipes_detail.csv` が生成されたら、以下を実行します。

```powershell
python .\src\summarize_pipes.py
```

集計のワークフローは以下のとおりです。

```text
output/pipes_detail.csv
        ↓
src/summarize_pipes.py
        ↓
output/pipes_summary.csv
```

想定されるコンソール出力は以下のとおりです。

```text
============================================================
ENMA-WG MEP Quantity Takeoff
Tokyo Summit 2026 PoC - Step 1
============================================================
Pipe segments : 252
Summary rows  : 138
Skipped       : 0

Total length      : 649.090 m
Horizontal length : 375.963 m
Vertical length   : 273.127 m
Sloped length     : 0.000 m

CSV : output\pipes_summary.csv
============================================================
```

これらの値は、Tokyo Summit 2026で発表した配管数量算出結果と一致しています。

---

## 出力ファイル

このワークフローでは、主に2つのCSVファイルを使用します。

### `output/pipes_detail.csv`

これは要素レベルの抽出結果です。

各IFC配管セグメントを個別のレコードとして保持するため、数量計算の結果を元のIFC要素まで遡って追跡できます。

抽出される情報には、以下のようなデータが含まれます。

- IFC要素の識別情報
- 階／Storey
- 系統情報
- 配管種別
- サイズ情報
- 長さ
- 方向分類
- ジオメトリ情報

このファイルは、

```text
IFC Data
```

から、

```text
Engineering Meaning
```

への移行を表しています。

### `output/pipes_summary.csv`

これは `pipes_detail.csv` から生成される集計数量結果です。

詳細レコードを、数量算出に使用するエンジニアリング上の数量カテゴリごとにグループ化し、数量集計結果を作成します。

これは次の移行を表しています。

```text
Engineering Meaning
        ↓
Engineering Quantity
```

元のIFCモデルがなくても抽出結果および集計結果を確認できるよう、両方のCSVファイルをこのリポジトリに含めています。

---

## 再現性の確認

2026年10月1日、Tokyo Summit 2026での発表に先立ち、配管の抽出および集計ワークフロー全体を再度実行しました。

実行した手順は以下のとおりです。

```powershell
python .\src\extract_pipes.py
python .\src\summarize_pipes.py
git status --short
```

再生成した以下のファイル：

```text
output/pipes_detail.csv
output/pipes_summary.csv
```

には、リポジトリに保存されている既存ファイルとの差分がGit上で検出されませんでした。

したがって、現在のPoCコードによって、合計数量だけでなく、保存済みの詳細CSVおよび集計CSVについても同一の結果が再現されることを確認しました。

---

## トレーサビリティ

ENMA-WGの重要な目的は、単に最終的な数量を算出することではありません。

計算結果は追跡可能であるべきだと考えています。

概念的には以下のようになります。

```text
IFC Element
    │
    │ GlobalId / IFC properties / geometry
    ↓
pipes_detail.csv
    │
    │ engineering interpretation
    ↓
