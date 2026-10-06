# ENMA-WG FAQ — Automated MEP Quantity Takeoff

> Originally prepared for the buildingSMART International Summit Tokyo 2026 Q&A and updated as the ENMA-WG PoC progressed.

## このFAQについて

このFAQは、buildingSMART International Summit Tokyo 2026「Revisiting the Promise of Automated MEP Quantity Takeoff」の想定問答集を基に、公開GitHub向けに再構成したものです。発表時点の説明を基礎としつつ、その後のPoC進捗を反映しています。

**Key message:** *Measurement is not the same as estimation.* IFCで測れる数量に、IDS・bSDD・Engineering Knowledge・Human Reviewをつなぎ、追跡可能なEngineering Quantityへ進めることを目指します。AIは判断を置き換えず、解釈や候補提示を補助します。

## Q1. 今回のPoCでは、実際にどこまでできていますか？

**30秒回答**

配管については実際の国土交通省BIMモデルをIfcOpenShellで解析し、252本の`IfcPipeSegment`、81個のPipe Fittingを識別し、中心線ベースの配管長649.090 mを取得しました。ダクトについては1,077本の`IfcDuctSegment`を抽出し、ROUND 792本、RECTANGULAR 285本、Geometry/QTO総延長1,088.945 mを確認しています。さらに正式な`IfcDistributionSystem`割当とEngineering Informationの検証まで進めています。機器は今後の対象です。

**補足**

重要なのは、これは概念図だけではなく実IFCから得た結果だという点です。一方、649.090mは最終的な積算数量ではありません。現PoCではcenterline-based lengthで、継手長はまだ控除していません。今回の発表では、実測できた数量と積算に使う数量を区別しています。

## Q2. 649.090mは、そのまま積算に使える配管数量ですか？

**30秒回答**

いいえ。現在値は中心線ベースの測定値です。継手長をまだ控除していないため、最終的な積算数量とは呼んでいません。

**補足**

Property Length、Geometry Length、Centerline Length、Net Pipe Length、Quantity for Estimationは同じとは限りません。どの数量を積算に採用するかはEngineering RulesやHuman Reviewを含めて決める必要があります。今回のPoCの大きな発見の一つが、measurable quantityとestimable quantityを区別すべきだという点です。

## Q3. BIMから数量が取れれば、自動積算は完成ではないのですか？

**30秒回答**

数量取得は入口です。積算には、その部材が何であるか、材質・規格・施工条件は何か、どのルールを適用するかというEngineering Meaningが必要です。

**補足**

例えば配管長が取れても、保温数量を決めるには施工箇所や用途、仕様、適用ルールが必要になります。今回の発表ではこの違いを “Measurement is not the same as estimation.” と表現しています。

## Q4. IFCに必要な属性がない場合はどうしますか？

**30秒回答**

まずIDSで必要情報が存在するかを確認し、不足を明示します。不足情報をAIが勝手に確定するのではなく、既存データやEngineering Knowledgeから候補を提示し、人が確認する考えです。

**補足**

そのためデータモデルにはInference ResultsとHuman Reviewsを分けて設けています。推論結果をそのまま数量にせず、人による確認、Engineering Rulesの評価、Calculation Evidenceまで追跡できる構造を目指しています。

## Q5. IDSとbSDDはどう使い分けるのですか？

**30秒回答**

今回の整理では、IDSは必要な情報が揃っているかを検証する役割、bSDDは情報の共通の意味をつなぐ役割です。

**補足**

IDSはValidation、bSDDはSemanticsという役割分担です。ただしbSDDだけで積算ルールや単価が決まるわけではありません。そこにEngineering Knowledgeやローカルなマスタ、ルールを組み合わせます。

## Q6. bSDDを使えば、日本の材料や積算コードと自動的につながりますか？

**30秒回答**

自動的につながるわけではありません。bSDDは共有された意味を表す層として使い、日本固有の材料・規格・積算体系とはマッピングが必要だと考えています。

**補足**

国際標準と日本固有体系を無理に一つにするのではなく、IFC/bSDD側の意味と、日本側の材料・規格・単価・歩掛などを対応付ける構造が現実的です。版管理や人によるレビューも必要になります。

## Q7. Engineering Knowledgeとは具体的に何ですか？

**30秒回答**

設備技術者が日常的に使っているものの、IFCのGeometryやPropertyだけでは表現しきれない判断ルールや経験知です。

**補足**

今回のPoCでは、施工箇所、流体、管材、規格、保温、塗装、歩掛などをEngineering MastersやEngineering Rulesとして扱う構造を設計しています。将来は機器選定、法令チェック、LCAなどにも同じ知識基盤を再利用する構想です。

## Q8. AIはどこで使うのですか？ AIが積算を決めるのですか？

**30秒回答**

AIは最終判断をする位置づけではありません。不完全・曖昧な情報の解釈や候補提示を支援します。Engineering Knowledgeと人間の判断が中心です。

**補足**

発表でも “AI alone is not enough.” としています。AIの出力を確定値と混同せず、IFC由来、ルール由来、推論由来などの根拠を追跡できるようにすることが重要です。

## Q9. Human Reviewを入れると、自動化の意味がなくなりませんか？

**30秒回答**

むしろ実務で使うために必要だと考えています。すべてを人が確認するのではなく、不足や曖昧さがある部分を人に戻し、確認結果を次のルール評価につなげます。

**補足**

現在のデータモデルは IFC Elements → Inference Results → Human Reviews → Rule Evaluations → Quantity Results という流れです。自動化と人の判断を対立させず、判断根拠を追跡可能にする設計です。

## Q10. なぜRDBだけでなくKnowledge Graphも考えているのですか？

**30秒回答**

RDBを置き換えるためではありません。数量、単価、マスタ、計算結果のような表形式データはRDBが得意です。Knowledge Graphは、系統・接続・空間・仕様・ルールなどの関係をたどる用途に向いています。

**補足**

今回のPoCではまず追跡可能なRDB構造を具体化しています。Knowledge GraphはENMA 3.0のKnowledge Layerを拡張する将来方向で、現在の配管数量PoCで完成済みという意味ではありません。

## Q11. IfcDistributionPortや接続情報は今回使っていますか？

**30秒回答**

今回の実IFCではPortsや接続情報も分析対象にしています。ただし、現在の649.090mという配管長そのものは中心線ベースの数量です。

**補足**

Port/Connectivityは今後、継手、系統追跡、機器との接続、上流・下流関係などを扱う重要な情報になります。今回のPoCでは、まず実モデルにどの程度情報が存在するかを確認しながら次段階へ進めています。

## Q12. 継手81個はどのように扱っていますか？

**30秒回答**

今回のモデルでは81個のPipe Fittingを識別していますが、現時点の649.090mでは継手長をまだ控除していません。

**補足**

したがって継手を認識できたことと、継手寸法を考慮したNet Pipe Lengthを完成したことは分けて説明します。次の段階では接続径や継手種別、標準寸法などをEngineering Knowledgeと結び、積算数量へ近づけます。

## Q13. 保温の例は今回のPoCで実装済みですか？

**30秒回答**

いいえ。Slide 6の保温例は、IFC DataからEngineering Meaningを経てEngineering Quantityへ進む考え方を示すillustrative exampleです。

**補足**

現在実装しているのは配管数量抽出です。保温、塗装、歩掛などはデータモデルとルール体系を整備しながら今後検証する対象です。発表スライドにも “not implemented in the current PoC” と明記しています。

## Q14. ダクトや機器はどこまでできていますか？

**30秒回答**

Pipesは数量抽出を実装済みです。Ductsは、1,077本の抽出、形状・寸法、Geometry/QTO総延長1,088.945 m、SA/RA/OA/EAのSystem分類まで確認し、現在は板厚選定などに必要なEngineering Informationの検証へ進んでいます。EquipmentはFutureです。

**補足**

ダクトや機器まで実装済みと受け取られないように区別しています。将来は同じEngineering Knowledgeの考え方を、ダクト数量や機器選定などへ拡張したいと考えています。

## Q15. Quantity Setの値とGeometryから計算した値のどちらを信用しますか？

**30秒回答**

どちらかを無条件に正とするのではなく、出所を区別して比較・検証する考えです。

**補足**

Property/Quantityとして格納された値、Geometryから求めた値、中心線ベースの値には、それぞれ由来と前提があります。重要なのは数値だけを残すのではなく、Calculation Evidenceとして入力・判断・ルール結果を追跡できるようにすることです。

## Q16. ENMAのデータモデルで一番重要な点は何ですか？

**30秒回答**

数量結果だけではなく、その数量がどのIFCデータ、推論、人の確認、ルールから作られたかを追跡できることです。

**補足**

中心の流れは IFC Elements → Inference Results → Human Reviews → Rule Evaluations → Quantity Results → Quantity Summaries です。周囲にSpecifications/IDS、Engineering Masters/bSDD、Engineering Rules、Calculation Evidenceを置いています。

## Q17. ENMAは既存のBIMソフトや積算ソフトを置き換えるのですか？

**30秒回答**

置き換えることを目的としていません。既存のBIM・設計・解析・施工・FMのツールはそのまま使い、その周囲にopenBIMベースのEngineering Knowledge Layerを加える構想です。

**補足**

Slide 11でも “Existing tools remain in place.” としています。ENMAはIFC、IDS、bSDD、Engineering Knowledge、Knowledge Graph、AI-assisted Reasoningをつなぎ、既存ワークフローを補強する位置づけです。

## Q18. Quantity Takeoffの次に何を目指しますか？

**30秒回答**

Quantity Takeoffは最終ゴールではなく、再利用可能なEngineering Informationの出発点です。

**補足**

数量にClassification、Material/Property、Costなどを結びつければ、Cost Estimation、Construction Progress、Procurement、Equipment Selectionなどへ展開できます。ただし、これらのdownstream applicationsは現在のPoCでは未実装で、Future Directionです。

## Q19. なぜ今、25年前からある『BIMで自動積算』をもう一度扱うのですか？

**30秒回答**

Geometryから数量を取る技術だけでは、設備積算の実務には届かなかったからです。現在はIFCに加え、IDS、bSDD、IfcOpenShell、オープンソース、AIなどを組み合わせ、意味と知識まで扱える環境が整ってきました。

**補足**

今回“Revisiting the Promise”としたのは、昔の約束が単純に失敗したという意味ではありません。MeasurementからEngineering Meaning、さらにEngineering Decisionへ進むために何が不足していたかを、現在のopenBIM技術で再検討するという意味です。

## Q20. ENMA 3.0の最終的なビジョンは何ですか？

**30秒回答**

openBIMを単なるデータ交換ではなく、Engineering Knowledgeを共有・再利用する基盤へ広げることです。

**補足**

IFCでInteroperable Dataを扱い、IDSでrequirementsを検証し、bSDDでsemanticsを共有し、Engineering Knowledgeを再利用可能なrules and intentとして扱います。その基盤をQuantity Takeoffだけでなく、Equipment Selection、Code Compliance、Carbon/LCA、Lifecycle Cost、Facility Knowledgeなどへ広げる構想です。

## Q21. このPoCやコードは公開されていますか？

**30秒回答**

はい。ENMA-WGのGitHubでQuantity Takeoff PoCを公開しています。発表最後のQRコードからアクセスできます。

**補足**

今回の発表では、完成製品としてではなく、openでcollaborativeな研究活動として公開し、国際的なopenBIMコミュニティからフィードバックを得たいと考えています。

## Q22. この研究で一番伝えたいことは何ですか？

**30秒回答**

“openBIM connects data. Engineering Knowledge connects decisions.” です。

**補足**

IFCで測れるようにするだけでなく、Engineering Knowledgeで意味を理解し、open standardsによって再利用できるようにする。発表の最後ではこれを Measure → Understand → Reuse の3語でまとめています。

## 質疑応答で迷ったときの共通回答軸

| 軸 | 確認すること |
|---|---|
| Data | IFCに何が事実として存在しているか |
| Validation | IDS等で必要情報が揃っているか |
| Meaning | bSDD等で、その情報が何を意味するか |
| Knowledge | 技術者のルール・経験知をどう適用するか |
| Inference | 推論値と確定値を区別し、根拠を残す |
| Human Review | 曖昧な部分を技術者が確認する |
| Rules | Engineering Rulesを適用し、数量へ変換する |
| Evidence | Calculation Evidenceとして由来を追跡する |
| Decision | 最終的なEngineering Decisionは人間が行う |

回答の基本形は、**結論 → 実データ／具体例 → 現在地 → 今後**です。

## Related documents

- [Duct Engineering Information Validation](DUCT_ENGINEERING_INFORMATION.md)
- [ダクトEngineering Information検証](DUCT_ENGINEERING_INFORMATION_ja.md)
- [Reproduce Pipe Results](REPRODUCE_PIPE_RESULTS.md)
- [配管結果の再現](REPRODUCE_PIPE_RESULTS_ja.md)
