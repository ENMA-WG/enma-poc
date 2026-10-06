# ダクト・トポロジー検証

## 1. 目的

本書では、実際のIFCモデルを使用して行ったダクト系統のトポロジー検証について整理します。

目的は、空調ネットワーク全体を自動的に復元することではありません。

まず、より基本的な問いを確認します。

> IFCモデルから、系統所属、Port所有関係、明示的な接続関係、幾何的な近接性について、実際に何が読み取れるのか。

この区別はENMA 3.0にとって重要です。

数量拾いでは、計測可能なGeometryだけで処理できる場合があります。しかしEngineering Informationを扱う場合には、IFCから直接観測できた情報と、推論によって補った情報を区別する必要があります。

今回の検証では、次のEvidence Chainを意識しています。

```text
System Membership
        ↓
Port Ownership
        ↓
Explicit Connectivity
        ↓
Port Geometry
        ↓
Inference
        ↓
Human Review
```

検証環境：

- IFC：`data/営繕BIMモデル_EM.ifc`
- IfcOpenShell：0.8.5
- Python：3.11.9

対象とした空調系統：

- `101_SA給気`
- `102_RA還気`
- `103_OA外気`
- `105_EA排気`

---

## 2. 区別すべき3つの概念

今回の検証で重要だったのは、次の3つを同じものとして扱ってはいけないという点です。

### 2.1 System Membership ― 系統所属

`IfcDistributionSystem` と `IfcRelAssignsToGroup` により、同じ系統に所属するオブジェクトを確認できます。

これは、

> これらのオブジェクトは同じDistribution Systemに所属している。

ことを示します。

しかし、各オブジェクトが物理的にどのような順序で接続されているかまで保証するものではありません。

### 2.2 Port Ownership ― Port所有関係

`IfcRelNests` により、`IfcDistributionPort` と、そのPortを所有するElementとの関係を確認できます。

これは、

> このPortは、このElementに属している。

ことを示します。

Port所有関係と、Element間の接続関係は別の情報です。

### 2.3 Explicit Connectivity ― 明示的接続

`IfcRelConnectsPorts` は、2つのPortの接続を明示的に表現します。

これはより強いEvidenceです。

> この2つのPortは、IFCモデル上で明示的に接続されている。

したがってENMAでは、

```text
System Membership ≠ Port Ownership ≠ Explicit Connectivity
```

として、それぞれを別の情報として保持する必要があります。

---

## 3. IFC全体の接続関係

対象IFCには次の情報が含まれていました。

| 項目 | 件数 |
|---|---:|
| IfcDistributionPort | 5,007 |
| IfcRelConnectsPorts | 1,144 |
| Ownerを特定できたPort | 5,007 |
| 検証対象空調System | 454 |

5,007個すべてのDistribution Portについて、`IfcRelNests` からOwner Elementを特定できました。

1,144件の明示接続について、両PortのOwner ElementのIFC Classを集計すると次のようになりました。

| 接続Element | 接続数 |
|---|---:|
| IfcDuctSegment ↔ IfcDuctSegment | 428 |
| IfcDuctFitting ↔ IfcDuctSegment | 419 |
| IfcPipeFitting ↔ IfcPipeSegment | 129 |
| IfcPipeSegment ↔ IfcPipeSegment | 77 |
| IfcCableCarrierFitting ↔ IfcCableCarrierSegment | 64 |
| IfcPipeSegment ↔ IfcValve | 12 |
| IfcDamper ↔ IfcDuctSegment | 5 |
| IfcPipeFitting ↔ IfcPipeFitting | 3 |
| IfcPipeSegment ↔ IfcWasteTerminal | 3 |
| IfcCableCarrierFitting ↔ IfcCableCarrierFitting | 2 |
| IfcPipeSegment ↔ IfcPump | 2 |

このうちダクト関係の明示接続は852件です。

```text
428  IfcDuctSegment ↔ IfcDuctSegment
419  IfcDuctFitting ↔ IfcDuctSegment
  5  IfcDamper ↔ IfcDuctSegment
-----------------------------------
852  ダクト関係の明示接続
```

一方、今回の集計では、次の機器とダクトとの `IfcRelConnectsPorts` による明示接続は確認できませんでした。

- `IfcFan`
- `IfcAirTerminal`
- `IfcAirTerminalBox`
- `IfcAirToAirHeatRecovery`

これは、IFCではこれらの接続を表現できない、という意味ではありません。

あくまで、

> 今回使用したIFCモデルと検証方法では確認できなかった。

という観測結果です。

---

## 4. 空調System別の接続状況

454の空調Systemについて、明示的なPort接続がSystemに対応付けられるかを集計しました。

| 系統 | System数 | 接続あり | 接続なし | 明示接続数 |
|---|---:|---:|---:|---:|
| SA | 199 | 110 | 89 | 419 |
| RA | 4 | 1 | 3 | 2 |
| OA | 53 | 24 | 29 | 93 |
| EA | 198 | 94 | 104 | 338 |
| **合計** | **454** | **229** | **225** | **852** |

ほぼ半数のSystemには、対応付けられる明示的なPort接続がありません。

ただし、この数字の解釈には注意が必要です。

例えばダクトSegmentが1本しか存在しないSystemでは、System内部のSegment間接続が存在しないこと自体は不自然ではありません。

したがって、

> 明示接続がない = Systemデータが不正

とは判断できません。

Systemを構成するElement数や種類も合わせて評価する必要があります。

---

## 5. EA 18のケーススタディ

詳細検証には、小規模な排気Systemである `EA 18` を使用しました。

```text
System Name    : EA 18
ObjectType     : 105_EA排気
PredefinedType : EXHAUST
```

System Memberには次のElementが含まれています。

- `IfcDuctSegment` × 1
- `IfcAirTerminal` × 1
- `IfcFan` × 1
- 正式な `IfcDistributionPort` × 5

一方、Element側から `IfcRelNests` を調べると、合計6 Port存在します。

これはFanに、Systemの正式MemberになっていないPortが1つ存在するためです。

### Element

```text
IfcDuctSegment
  丸型ダクト:00_丸タップ:40699213

IfcAirTerminal
  041_ユニバーサル形吸込口:HS:40845462

IfcFan
  11030_FAN_消音ボックス付送風機:#1_150m3/h:40873974
```

### FanのPort

```text
Port_40873974_8       SOURCEANDSINK
OutPort_40873974_9    SOURCE
InPort_40873974_10    SINK
```

このうち後者2つだけが `EA 18` の正式なSystem Portです。

この差異は自動的に補正せず、IFCから観測されたEvidenceとしてそのまま保持します。

---

## 6. EA 18の明示接続

IFC全体には1,144件の `IfcRelConnectsPorts` が存在します。

しかし `EA 18` に所属するPortおよびElementについては、明示的な接続Relationshipを確認できませんでした。

| Relationship | 件数 |
|---|---:|
| IfcRelConnectsPorts | 0 |
| IfcRelConnectsPortToElement | 0 |
| IfcRelConnectsElements | 0 |
| IfcRelConnectsPathElements | 0 |
| IfcRelNests | 3 |
| IfcRelAssignsToGroup | 1 |

したがって `EA 18` では、

```text
System membership : あり
Port ownership     : あり
Port direction     : あり
Port-to-port link  : なし
```

という状態です。

ここで、

> 同じSystemに所属しているから、Fan・Duct・AirTerminalは物理的に直結している。

と自動的に判断することはできません。

---

## 7. EA 18のPort Geometry

次に、6個すべてのNested PortについてWorld座標を取得しました。

対象IFCの長さ単位はmmです。

Duct Segment自身の2つのPort間距離は、ちょうど3,800 mmでした。

さらに異なるElement間のPort距離を総当たりで計算しました。

代表的な最短距離は次の通りです。

| Port Owner | 最短距離 |
|---|---:|
| AirTerminal ↔ Fan | 636.416 mm |
| DuctSegment ↔ Fan | 957.164 mm |
| DuctSegment ↔ AirTerminal | 1,696.478 mm |

最も近い異なるElement間のPortでも600 mm以上離れています。

したがって `EA 18` については、

> Relationshipは欠落しているが、実際には対応するPort座標が一致している。

という単純な仮説は支持されませんでした。

考えられる可能性としては、

- 中間部材がモデル化されていない
- 物理ネットワークが完全には表現されていない
- System groupingとPhysical topologyの粒度が異なる
- オーサリングソフトからのIFC出力上の特性
- その他のモデリング上の表現方法

などがあります。

現時点のEvidenceだけでは、どれが正しいかを確定できません。

---

## 8. 明示接続とPort距離の比較

Geometry proximityが接続判断の補助Evidenceとして利用できるか確認するため、IFC全体の1,144件の `IfcRelConnectsPorts` についてPort原点間の3次元距離を計算しました。

### 距離分布

| Port間距離 | 接続数 |
|---|---:|
| 実質0 mm | 1,114 |
| 0超～1 mm | 1 |
| 1超～10 mm | 0 |
| 10超～50 mm | 0 |
| 50超～100 mm | 22 |
| 100超～500 mm | 6 |
| 500 mm超 | 1 |
| **合計** | **1,144** |

統計値：

```text
Minimum :    0.000 mm
Median  :    0.000 mm
Average :    3.663 mm
Maximum : 1140.000 mm
```

1,144件中1,114件、約97.4%の明示接続でPort原点が実質的に一致しています。

したがって、このIFCでは、

> Portの幾何的な一致は、明示接続に非常によく見られる特徴である。

ことが確認できました。

しかし、これは例外のないルールではありません。

---

## 9. Port位置が一致しない明示接続

明示的に接続されているにもかかわらず、Port原点間に距離があるダクトも存在します。

確認された例：

```text
100 mm
125 mm
150 mm
200 mm
1140 mm
```

最大値は、

```text
IfcDuctSegment ↔ IfcDuctSegment
Port distance = 1140 mm
```

でした。

Port原点が1.14 m離れていても、IFC上では `IfcRelConnectsPorts` により明示的に接続されています。

したがって、

> Geometryの距離によって、明示的なIFC接続を否定してはいけない。

ことが分かります。

同様に、

> Port座標が一致しない = 非接続

とも判断できません。

これらの外れ値が発生する理由については、現時点では未検証です。

Element Geometry、Port Placementの定義、モデリング方法、IFC出力方法などが関係している可能性があります。

---

## 10. Evidenceの優先順位

今回の検証結果から、ENMAではEvidenceの強さを区別して扱う必要があります。

### Level 1 — IFCによる明示接続

```text
IfcRelConnectsPorts
```

これはIFCに直接記録された接続情報です。

ENMAでは、

```text
IFC_OBSERVED
```

として保持します。

### Level 2 — SystemおよびPort関係

```text
IfcDistributionSystem
IfcRelAssignsToGroup
IfcRelNests
IfcDistributionPort.FlowDirection
```

これらも重要なIFC情報ですが、それだけでは物理的な隣接関係を証明しません。

これらも、

```text
IFC_OBSERVED
```

として保持します。

### Level 3 — Geometry Proximity

Portの座標および距離はGeometryから得られる観測情報です。

例えば、

```text
distance(port_A, port_B) ≈ 0
```

という結果は、

```text
GEOMETRY_OBSERVED
```

です。

これは接続推論を支えるEvidenceにはなりますが、明示的なIFC接続そのものではありません。

### Level 4 — Connectivity Inference

明示接続がない場合、将来的にENMAが、

```text
CONNECTION_CANDIDATE
```

を生成することは考えられます。

その際には複数のEvidenceを組み合わせます。

例えば、

- 同一Distribution System
- PortのFlowDirection
- Element Classの互換性
- 寸法の互換性
- Geometry上の近接性
- Portの方向
- Networkの連続性

などです。

これは、

```text
INFERENCE
```

であり、`IFC_OBSERVED` ではありません。

### Level 5 — Human Review

曖昧な接続推論については、設備技術者が確認します。

```text
INFERENCE
        ↓
HUMAN REVIEW
        ↓
ACCEPT / REJECT / MODIFY
```

これにより、機械が読み取ったEvidenceと技術者のEngineering Judgementを区別できます。

---

## 11. ENMAにおける接続判定の考え方

将来的には、次のような保守的な処理が考えられます。

```text
IfcRelConnectsPorts が存在するか？
        |
        +-- YES
        |     |
        |     +--> CONNECTED
        |          Evidence = IFC_OBSERVED
        |
        +-- NO
              |
              +--> System Membershipを確認
              |
              +--> Port Ownershipを確認
              |
              +--> FlowDirectionを確認
              |
              +--> Geometryを確認
              |
              +--> Size / Orientationを確認
              |
              +--> 接続候補を生成
                        |
                        v
                    INFERENCE
                        |
                        v
                   HUMAN REVIEW
```

重要なのは、Geometry proximityだけを自動接続ルールにしないことです。

今回のIFCでは、

1. 明示接続が存在してもPort原点が一致しない場合がある
2. 同一Systemへの所属だけではPhysical adjacencyを証明できない

という両方のケースが確認されました。

---

## 12. Engineering Informationへの意味

今回の検証は、ENMAの基本的な考え方を改めて示しています。

> Measurement、Semantics、Topology、Engineering Decisionは、それぞれ異なる情報レイヤーである。

数量拾いであれば、Geometryからダクト長を測るだけで十分な場合があります。

しかしEngineering Informationとして扱うには、

- どのSystemに所属しているか
- どのPortがElementに属しているか
- どの接続がIFCに明示されているか
- どの関係をENMAが推論したのか
- 推論のEvidenceは何か
- 技術者が確認したか

まで区別する必要があります。

そのEvidence Chainは、例えば次のようになります。

```text
IFC
 ↓
Observed Geometry
 ↓
Observed Semantics
 ↓
Observed Topology
 ↓
Engineering Inference
 ↓
Human Review
 ↓
Rule Evaluation
 ↓
Traceable Result
```

---

## 13. 今回の検証で証明していないこと

今回の検証結果を一般化しすぎないことも重要です。

本検証は、次のことを証明するものではありません。

- すべてのIFCモデルが同じ構造になる
- すべてのRevit IFC出力が同じ構造になる
- Port座標一致が普遍的な接続ルールである
- `IfcRelConnectsPorts` がないElementは非接続である
- Port間距離が0でなければ非接続である
- HVAC Network全体をすでに自動復元できる

今回得られた結果は、

> 使用したIFCモデルと、現在の抽出方法で観測された結果

です。

今後、異なるモデルやオーサリング環境でも検証する必要があります。

---

## 14. 再現性

本書で説明したTopology検証を再現するため、次のスクリプトをリポジトリに収録しています。

```text
src/analyze_ifc_port_connections.py
src/inspect_ifc_connectivity_relationships.py
src/trace_duct_system_topology.py
src/inspect_duct_port_geometry.py
src/analyze_connected_port_distances.py
```

これらのスクリプトを実行すると、代表的な出力として次のCSVが生成されます。

```text
output/ifc_port_connections.csv
output/duct_system_connection_summary.csv
output/duct_port_geometry_EA18.csv
output/duct_port_distances_EA18.csv
output/connected_port_distances.csv
```

これらはProduction-readyなNetwork Reconstruction Algorithmではなく、検証過程を確認可能にするためのExploratory Validation Artifactです。

---

## 15. Key Finding

今回のTopology検証で最も重要な結果は、

```text
System Membership
        ≠
Physical Topology
        ≠
Geometric Proximity
```

という点です。

一方で、それぞれの情報についてProvenanceを保持すれば、互いを補完するEvidenceとして利用できます。

ENMA 3.0が目指すのは、不完全なIFC情報を暗黙の仮定によってEngineering Truthへ変換することではありません。

目指すのは、判断過程を追跡可能にすることです。

```text
OBSERVE
   ↓
INTERPRET
   ↓
INFER
   ↓
REVIEW
   ↓
DECIDE
```

この区別が、Automated Quantity MeasurementからEngineering Informationへ進むための重要なステップになります。