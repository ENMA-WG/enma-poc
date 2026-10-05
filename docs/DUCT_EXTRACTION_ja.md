# ダクト形状抽出とQTO検証

## 概要

このドキュメントでは、ENMA-WG Automated MEP Quantity Takeoff
PoCで実施したダクト抽出実験について説明します。

この実験では、IFCのダクト形状から寸法を直接取得し、形状から算出した値とIFC
Quantity Takeoff（QTO）の値をクロスチェックします。

目的は単にダクト数量を取得することだけではありません。IFCモデル内部に存在する複数の情報源が、相互に整合しているかを検証することも目的としています。

現在の実験対象は次のとおりです。

-   `IfcDuctSegment`
-   ダクト形状の分類
-   丸ダクトの直径
-   角ダクトの幅・高さ
-   ダクト長
-   断面積
-   IFC GeometryとQTO値の比較

> **重要**
>
> 本実装は研究PoCです。寸法は元のIFC
> Geometryに存在する値を保持しており、呼称寸法や標準寸法へ自動変換していません。

## 対象IFC

現在の検証では、ENMA-WG
PoCで使用している日本の国土交通省（MLIT）のBIMサンプルモデルを使用しています。

想定するローカルパス：

``` text
data/営繕BIMモデル_EM.ifc
```

IFCファイル自体は、このリポジトリには含めていません。

## 実行環境

現在のENMA-WG PoC環境：

-   Windows 11
-   Python 3.11.9
-   IfcOpenShell 0.8.5

リポジトリのルートで依存パッケージをインストールします。

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 実行方法

リポジトリのルートから実行します。

``` powershell
python .\src\extract_ducts.py
```

出力：

``` text
output/ducts_detail.csv
```

CSVは一般的な表計算ソフトとの互換性を考慮し、UTF-8
BOM付き（`utf-8-sig`）で出力します。

## Geometryの抽出経路

現在のMLIT検証IFCでは、このPoCで調査した1,077個すべての`IfcDuctSegment`が次の形状構造を使用しています。

``` text
IfcDuctSegment
  └─ IfcExtrudedAreaSolid
       └─ IfcArbitraryClosedProfileDef
            └─ IfcIndexedPolyCurve
                 └─ IfcCartesianPointList2D
```

押出し深さ（Depth）をGeometry由来のダクト長として使用します。

ローカル2Dプロファイルの座標から、ダクト断面寸法を算出します。

ここでローカル座標を使用することが重要です。ワールド座標系の軸平行Bounding
Boxは、部材の回転や向きによって大きくなるため、必ずしも実際のダクト幅・高さ・長さを表すとは限りません。

## 形状分類

現在のスクリプトでは、ダクトを次の3種類に分類します。

-   `ROUND`
-   `RECTANGULAR`
-   `UNKNOWN`

基本となる分類にはGeometryを使用します。

現在のIFCでは、

-   `IfcArcIndex`を含むプロファイル → `ROUND`
-   Arcを含まないプロファイル → `RECTANGULAR`

として分類しています。

日本語の`ObjectType`および`Name`は、Geometryから分類できない場合のフォールバックとしてのみ使用します。

### 現在の結果

``` text
IfcDuctSegment       : 1077
ROUND                : 792
RECTANGULAR          : 285
UNKNOWN              : 0
```

## 寸法抽出

### 丸ダクト

丸ダクトの直径は、ローカルプロファイル座標から算出します。

現在のIFCでは、丸型プロファイルがArcによって表現されています。ローカルプロファイル原点からの半径を使用して直径を求めます。

792本の丸ダクトについて、Geometryから取得された直径は次のとおりです。

        直径      本数
  ---------- ---------
      100 mm         8
      150 mm       121
      200 mm       362
      250 mm       264
      300 mm        30
      350 mm         7
    **合計**   **792**

これらは、現在の元IFC Geometryに存在する寸法を示しています。

### 角ダクト

角ダクトの幅と高さは、ローカル2Dプロファイル座標の範囲から算出します。

現在のスクリプトでは、大きい側を`Width_mm`、小さい側を`Height_mm`として保存します。

プロファイルの中には、設備技術者が一般的に使用する呼称寸法として見ると、端数や非常に大きな値など、通常とは異なって見える寸法も存在します。

これらの値は意図的にそのまま保持します。

ENMAでは、例えばGeometryに、

``` text
750 x 637.626 mm
```

と存在する値を、自動的に、

``` text
750 x 650 mm
```

のような呼称寸法へ変換しません。

その変換は元Geometryに明示されていない「技術的解釈」を加えることになるためです。

呼称寸法への解釈は、IFCからの生データ抽出とは別の処理として扱うべきだと考えています。

## GeometryとQTOのクロスチェック

Geometryから算出した値を、

``` text
Qto_DuctSegmentBaseQuantities
```

と比較します。

現在使用しているQTO：

-   `Length`
-   `GrossCrossSectionArea`
-   `NetCrossSectionArea`
-   `OuterSurfaceArea`

現在の許容値：

``` text
長さ : 0.01 mm
面積 : 0.01 %
```

面積については、意図的に厳しい許容値を設定しています。

## 検証結果

現在の検証結果：

``` text
IfcDuctSegment       : 1077
ROUND                : 792
RECTANGULAR          : 285
UNKNOWN              : 0

Geometry OK          : 1077
Geometry REVIEW      : 0

Length match         : 1077/1077
Area match (all)     : 285/1077
  ROUND              : 0/792
  RECTANGULAR        : 285/285
```

### 長さ

Geometryの押出し長さとQTO
`Length`は、`1077 / 1077`ですべて現在の許容値内で一致しました。

### 角ダクト断面積

角ダクト285本すべてについて、ローカルGeometryから算出した断面積とQTO
`GrossCrossSectionArea`が現在の許容値内で一致しました。

``` text
RECTANGULAR: 285 / 285
```

### 丸ダクト断面積

丸ダクトでは異なる結果となりました。

Geometry由来の円断面積は、Pythonの`math.pi`を使用して算出しています。

0.01%という厳しい許容値では、792本すべてがQTO
`GrossCrossSectionArea`と不一致になりました。

しかし、詳しく調査すると、これはランダムな誤差ではありませんでした。

100 mmから350
mmまでの全6径、792本すべてについて、CSVに保存された精度ではGeometryとQTOの面積差が一貫して、

``` text
0.015038 %
```

となりました。

        直径      本数      最小差      最大差
  ---------- --------- ----------- -----------
      100 mm         8   0.015038%   0.015038%
      150 mm       121   0.015038%   0.015038%
      200 mm       362   0.015038%   0.015038%
      250 mm       264   0.015038%   0.015038%
      300 mm        30   0.015038%   0.015038%
      350 mm         7   0.015038%   0.015038%
    **合計**   **792**             

このPoCでは、すべてを「一致」と表示するためだけに許容値を緩和することはしていません。差異そのものを検証結果として残しています。

現時点で確認できているのは、現在の元IFCにおいて、Geometryから算出した円断面積とQTO値の間に一貫した差が存在するという事実です。

この差が発生する原因については、まだ確定していません。

したがって、この結果から特定のBIMオーサリングソフトが特定の円周率や特定の計算方法を使用している、と判断することはしていません。

## なぜ差異を残すのか

この実験で重視している考え方の一つは、

**IFC数量取得において、一つの情報源を無条件に正しいと仮定しない**

ということです。

``` text
IFC Geometry
     │
     ├── 寸法
     ├── 押出し長さ
     └── 算出断面積
             │
             ▼
        Cross-check
             ▲
             │
IFC QTO
     ├── Length
     ├── GrossCrossSectionArea
     ├── NetCrossSectionArea
     └── OuterSurfaceArea
```

一致すれば、取得した数量に対する信頼度を高める材料になります。

一致しない場合は、その差異自体が技術者による確認対象となり得ます。

単一のIFCプロパティをそのまま数量表へ転記するだけでは得られない情報です。

## 出力項目

`output/ducts_detail.csv`には次の項目を出力します。

  項目                        内容
  --------------------------- ------------------------------------
  `GlobalId`                  IFC GlobalId
  `Name`                      IFC要素名
  `ObjectType`                IFC ObjectType
  `Storey`                    所属階
  `Shape`                     ROUND / RECTANGULAR / UNKNOWN
  `Diameter_mm`               Geometryから取得した丸ダクト直径
  `Width_mm`                  Geometryから取得した角ダクト幅
  `Height_mm`                 Geometryから取得した角ダクト高さ
  `Geometry_Length_mm`        IFC Geometryの押出し長さ
  `QTO_Length_mm`             QTO Length
  `Geometry_Area_m2`          Geometryから算出した断面積
  `QTO_GrossArea_m2`          QTO GrossCrossSectionArea
  `QTO_NetArea_m2`            QTO NetCrossSectionArea
  `QTO_OuterSurfaceArea_m2`   QTO OuterSurfaceArea
  `Length_Difference_mm`      Geometry/QTO長さの絶対差
  `Length_Match`              長さ検証結果
  `Area_Difference_pct`       Geometry/QTO面積差率
  `Area_Match`                面積検証結果
  `ProfileType`               IFCプロファイル型
  `CurveType`                 IFC曲線型
  `DimensionSource`           寸法取得元（現在は`IFC_GEOMETRY`）
  `GeometryStatus`            Geometry抽出結果

## 通常とは異なるGeometry寸法について

現在の元IFCには、一般的な呼称寸法とは異なって見える角ダクト寸法も存在します。

抽出スクリプトは、それらを意図的にそのまま保持します。

``` text
Raw IFC Geometry
        ↓
Geometry抽出
        ↓
技術的解釈
        ↓
呼称寸法・標準寸法
        ↓
数量・仕様・労務・工程
```

現在のスクリプトが実装しているのは、最初の2段階です。

呼称寸法への解釈は別のエンジニアリング処理であり、ルール、仕様書、参照マスタ、あるいは技術者による確認が必要になる可能性があります。

## 表計算ソフトでCSVを開く際の注意

CSVは「書式付きの表」ではなく、データファイルです。

このPoCのCSVは一般的な表計算ソフトとの互換性を考慮し、UTF-8
BOM付きで出力しています。

Microsoft
Excelなどの表計算ソフトでCSVを直接開くと、数値の表示桁数、日付、識別子などが表計算ソフト側の判断で自動的に解釈・整形される場合があります。

これは必ずしも元のCSVデータが変更されていることを意味しません。

再現性を重視する場合は、表計算ソフト上の表示書式ではなく、CSVを機械可読なデータファイルとして扱うことを推奨します。

## 現在の対象範囲と制約

現在のPoCは、検証対象IFCで確認されたGeometry構造を前提としています。

具体的には、

-   検証対象ダクトは`IfcExtrudedAreaSolid`を使用
-   プロファイルは`IfcArbitraryClosedProfileDef`
-   外周曲線は`IfcIndexedPolyCurve`
-   丸型・角型を対象
-   Geometry寸法から呼称寸法への変換は未実装
-   今回のダクト数量実験では継手を未算入
-   施工箇所や仕様の解釈は未実装
-   通常とは異なる寸法も自動補正せず保持

としています。

別のIFCモデルでは異なるGeometry表現が使用される可能性があり、追加の抽出ロジックが必要になる場合があります。

## ENMAの技術的解釈へ

現在のダクト実験では、生データ抽出と技術的解釈を分離しています。

将来のENMAでは、

``` text
IFC
  ↓
Geometry / Properties / Systems
  ↓
Information Validation
  ↓
Quantity
  ↓
Specifications
  ↓
Labor
  ↓
Schedule
```

という流れを検討しています。

情報要件の検証にはIDS、共通用語・分類・意味の対応にはbSDDを利用する方向を検討しています。

これらはENMA-WGの今後の研究方向であり、現在のPoCですべて実装済みであることを意味するものではありません。

## 関連ファイル

``` text
src/extract_ducts.py
output/ducts_detail.csv
```

既存の配管数量PoCについては、

``` text
docs/REPRODUCE_PIPE_RESULTS_ja.md
```

を参照してください。

## Project

ENMA-WG\
Automated MEP Quantity Takeoff PoC

本実験は、openBIMを利用した再現可能な設備数量算出と、その先のエンジニアリングワークフローを検討するENMA-WGの研究活動の一部です。
