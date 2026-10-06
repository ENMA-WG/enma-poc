# ENMA-WG FAQ — Automated MEP Quantity Takeoff

> Originally prepared for the buildingSMART International Summit Tokyo 2026 Q&A and updated as the ENMA-WG PoC progressed.

## About this FAQ

This FAQ is based on the anticipated Q&A prepared for the buildingSMART International Summit Tokyo 2026 presentation, “Revisiting the Promise of Automated MEP Quantity Takeoff,” and has been reorganized for the public GitHub repository. It preserves the presentation framing while reflecting subsequent PoC progress.

**Key message:** *Measurement is not the same as estimation.* ENMA-WG connects quantities measurable through IFC with IDS, bSDD, Engineering Knowledge, and Human Review to move toward traceable Engineering Quantity. AI assists interpretation and candidate suggestions rather than replacing engineering judgment.

## Q1. What exactly has been achieved in this PoC?

**30-second answer**

For piping, we analyzed an actual Japanese MLIT BIM model using IfcOpenShell, identified 252 `IfcPipeSegment` objects and 81 pipe fittings, and obtained a centerline-based piping length of 649.090 m. For ducts, we extracted 1,077 `IfcDuctSegment` objects—792 ROUND and 285 RECTANGULAR—and confirmed a Geometry/QTO total length of 1,088.945 m. We have also progressed to formal `IfcDistributionSystem` assignment and Engineering Information validation. Equipment remains a future scope.

**If asked for more detail**

It is important to note that these results were derived from actual IFC data, not just conceptual drawings. However, the 649.090 m figure is not the final quantity for quantity takeoff. In the current PoC, this is a centerline-based length, and the length of fittings has not yet been deducted. In this presentation, we distinguish between the quantities that could be measured and those used for quantity takeoff.

## Q2. Is the 649.090 m a piping quantity that can be used directly for quantity takeoff?

**30-second answer**

No. The current value is a centerline-based measurement. Since the length of the fittings has not yet been deducted, we do not refer to it as the final quantity for the estimate.

**If asked for more detail**

“Property Length,” “Geometry Length,” “Centerline Length,” “Net Pipe Length,” and “Quantity for Estimation” are not necessarily the same. The quantity to be used for estimation must be determined in accordance with Engineering Rules and subject to Human Review. One of the key findings of this PoC is that we should distinguish between “measurable quantities” and “estimable quantities.”

## Q3. If quantities can be extracted from BIM, isn’t that the end of the automated quantity takeoff process?

**30-second answer**

Quantity extraction is just the starting point. Quantity takeoff requires “Engineering Meaning”—understanding what the component is, its material, specifications, and construction conditions, as well as which rules to apply.

**If asked for more detail**

For example, even if you can determine the length of piping, you still need to know the installation location, purpose, specifications, and applicable rules to determine the quantity of insulation required. In this presentation, we express this distinction as “Measurement is not the same as estimation.”

## Q4. What should you do if the required attributes are missing from the IFC file?

**30-second answer**

First, verify whether the necessary information exists in the IDS and clearly indicate any gaps. The idea is not for AI to arbitrarily determine missing information, but rather for it to suggest candidates based on existing data and engineering knowledge, which a human then verifies.

**If asked for more detail**

For this reason, the data model distinguishes between “Inference Results” and “Human Reviews.” We aim for a structure where inference results are not automatically converted into quantities, but rather are subject to human verification, evaluation against engineering rules, and traceability all the way to the calculation evidence.

## Q5. How do you differentiate between IDS and bSDD?

**30-second answer**

In this framework, IDS verifies whether all necessary information is present, while bSDD connects the shared meanings of that information.

**If asked for more detail**

The division of roles is that IDS handles “Validation” and bSDD handles “Semantics.” However, bSDD alone does not determine cost estimation rules or unit prices. Engineering knowledge, local master data, and rules are also incorporated into the process.

## Q6. Does using bSDD automatically link to Japanese materials and quantity survey codes?

**30-second answer**

It does not connect automatically. We view bSDD as a layer representing shared semantics, and believe that mapping to Japan-specific materials, standards, and quantity surveying systems is necessary.

**If asked for more detail**

Rather than forcing international standards and Japan-specific systems into a single framework, a more practical approach is to establish a structure that maps the meanings defined by IFC/bSDD to Japan’s materials, standards, unit prices, and labor rates. Version control and manual review will also be necessary.

## Q7. What exactly is “Engineering Knowledge”?

**30-second answer**

It refers to the judgment rules and experiential knowledge that facilities engineers use on a daily basis but that cannot be fully expressed by IFC Geometry or Property alone.

**If asked for more detail**

In this PoC, we are designing a framework that treats construction locations, fluids, piping materials, standards, insulation, coatings, and labor rates as “Engineering Masters” and “Engineering Rules.” The vision is to reuse this same knowledge base in the future for equipment selection, regulatory compliance checks, and LCA.

## Q8. Where is AI used? Does AI determine the cost estimate?

**30-second answer**

AI is not positioned to make the final decision. It assists in interpreting incomplete or ambiguous information and suggesting options. Engineering knowledge and human judgment remain central.

**If asked for more detail**

As stated in the presentation, “AI alone is not enough.” It is important not to confuse AI outputs with definitive values, and to ensure that the basis for those outputs—whether derived from IFC, rules, or inference—can be traced.

## Q9. Doesn’t including human review defeat the purpose of automation?

**30-second answer**

On the contrary, I believe it is necessary for practical use. Rather than having humans verify everything, we return parts with deficiencies or ambiguities to humans for review, and then use the results of that review to inform the next rule evaluation.

**If asked for more detail**

The current data model follows this flow: IFC Elements → Inference Results → Human Reviews → Rule Evaluations → Quantity Results. The design ensures that automation and human judgment are not at odds with each other and that the basis for decisions can be traced.

## Q10. Why are you considering a Knowledge Graph in addition to an RDB?

**30-second answer**

It is not intended to replace the RDB. The RDB excels at tabular data such as quantities, unit prices, master data, and calculation results. The Knowledge Graph is well-suited for tracing relationships such as lineage, connections, spatial relationships, specifications, and rules.

**If asked for more detail**

In this PoC, we are first defining a traceable RDB structure. The Knowledge Graph represents a future direction for extending the Knowledge Layer of ENMA 3.0; it does not mean that it has already been completed in the current piping quantity PoC.

## Q11. Are IfcDistributionPort or connection information being used in this project?

**30-second answer**

In this actual IFC, we are also analyzing ports and connection information. However, the current piping length of 649.090 m is based on centerline measurements.

**If asked for more detail**

Port/Connectivity will become critical information in the future for handling fittings, system tracing, connections to equipment, and upstream/downstream relationships. In this PoC, we are proceeding to the next phase while first verifying the extent to which this information exists in the actual model.

## Q12. How are the 81 fittings being handled?

**30-second answer**

This model identifies 81 pipe fittings, but the current measurement of 649.090 m does not yet account for the length of the fittings.

**If asked for more detail**

Therefore, I will explain separately how the fittings were recognized and how the net pipe length, taking fitting dimensions into account, was calculated. In the next phase, we will link connection diameters, fitting types, standard dimensions, and other factors to engineering knowledge to bring the results closer to the actual quantity for billing.

## Q13. Has the thermal insulation example been implemented in this PoC?

**30-second answer**

No. The thermal insulation example on Slide 6 is an illustrative example demonstrating the concept of progressing from IFC data through engineering meaning to engineering quantities.

**If asked for more detail**

What is currently implemented is the extraction of piping quantities. Insulation, painting, and labor rates are subjects that will be verified in the future as we refine the data model and rule set. The presentation slides also clearly state “not implemented in the current PoC.”

## Q14. How far along is the implementation for ducts and equipment?

**30-second answer**

Pipes have implemented quantity extraction. For ducts, we have extracted 1,077 segments, confirmed shape and dimensions, a Geometry/QTO total length of 1,088.945 m, and SA/RA/OA/EA system classification. The current duct work has progressed to validating the Engineering Information required for decisions such as sheet-thickness selection. Equipment remains Future.

**If asked for more detail**

We make this distinction so that it is not interpreted as meaning that ducts and equipment have already been implemented. In the future, we plan to extend the same “Engineering Knowledge” approach to areas such as duct quantities and equipment selection.

## Q15. Which do you trust more: the values from the Quantity Set or those calculated from the geometry?

**30-second answer**

Rather than unconditionally accepting one as correct, our approach is to distinguish between sources and compare and verify them.

**If asked for more detail**

Values stored as Properties or Quantities, values derived from Geometry, and centerline-based values each have their own origins and underlying assumptions. The key is not just to retain the numerical values, but to ensure that inputs, judgments, and rule results can be traced as “Calculation Evidence.”

## Q16. What is the most important aspect of the ENMA data model?

**30-second answer**

It is the ability to track not only the quantity results but also the specific IFC data, inferences, human verifications, and rules from which those quantities were derived.

**If asked for more detail**

The central flow is IFC Elements → Inference Results → Human Reviews → Rule Evaluations → Quantity Results → Quantity Summaries. Specifications/IDS, Engineering Masters/bSDD, Engineering Rules, and Calculation Evidence are positioned around this flow.

## Q17. Does ENMA replace existing BIM or quantity takeoff software?

**30-second answer**

It is not intended to replace them. The concept is to continue using existing BIM, design, analysis, construction, and FM tools as-is, while adding an openBIM-based Engineering Knowledge Layer around them.

**If asked for more detail**

As stated on Slide 11, “Existing tools remain in place.” ENMA connects IFC, IDS, bSDD, Engineering Knowledge, Knowledge Graph, and AI-assisted Reasoning to reinforce existing workflows.

## Q18. What is your next goal after Quantity Takeoff?

**30-second answer**

Quantity Takeoff is not the ultimate goal; it is the starting point for reusable engineering information.

**If asked for more detail**

By linking quantities to classification, materials/properties, and costs, we can expand into areas such as cost estimation, construction progress tracking, procurement, and equipment selection. However, these downstream applications are not yet implemented in the current PoC and are part of our future direction.

## Q19. Why are we revisiting “automated quantity takeoff with BIM”—a concept that’s been around for 25 years—right now?

**30-second answer**

It’s because the technology for extracting quantities from geometry alone was insufficient for practical equipment quantity takeoff. Today, in addition to IFC, we have established an environment that can handle meaning and knowledge by combining IDS, bSDD, IFC OpenShell, open-source tools, and AI.

**If asked for more detail**

The reason we titled this session “Revisiting the Promise” is not to suggest that the promise made in the past simply failed. Rather, it means we are using current openBIM technology to reexamine what was missing in order to progress from “Measurement” to “Engineering Meaning” and ultimately to “Engineering Decision.”

## Q20. What is the ultimate vision for ENMA 3.0?

**30-second answer**

It is to expand openBIM beyond mere data exchange into a foundation for sharing and reusing engineering knowledge.

**If asked for more detail**

We handle interoperable data via IFC, verify requirements using IDS, share semantics through bSDD, and treat engineering knowledge as reusable rules and intent. Our vision is to expand this foundation beyond quantity takeoff to include equipment selection, code compliance, carbon/LCA, lifecycle costs, and facility knowledge.

## Q21. Are this PoC and the code publicly available?

**30-second answer**

Yes. The Quantity Takeoff PoC is available on the ENMA-WG’s GitHub. You can access it via the QR code at the end of the presentation.

**If asked for more detail**

In this presentation, we are releasing this not as a finished product, but as an open and collaborative research initiative, with the aim of gathering feedback from the international openBIM community.

## Q22. What is the main message you want to convey through this research?

**30-second answer**

“openBIM connects data. Engineering Knowledge connects decisions.”

**If asked for more detail**

It’s not just about making data measurable via IFC; it’s about understanding its meaning through engineering knowledge and ensuring it can be reused through open standards. At the end of the presentation, I summarized this with the three words: Measure → Understand → Reuse.

## A general framework for answering questions

| Framework | Point to verify |
|---|---|
| Data | What facts are actually present in the IFC? |
| Validation | Is the required information present, for example as checked through IDS? |
| Meaning | What does the information mean, for example through bSDD? |
| Knowledge | How should engineering rules and experiential knowledge be applied? |
| Inference | Distinguish inferred values from confirmed values and retain the rationale. |
| Human Review | Engineers verify ambiguous areas. |
| Rules | Apply Engineering Rules and convert information into quantities. |
| Evidence | Trace provenance as Calculation Evidence. |
| Decision | The final Engineering Decision is made by a human. |

A useful response structure is: **Conclusion → Actual data / specific example → Current status → Future direction**.

## Related documents

- [Duct Engineering Information Validation](DUCT_ENGINEERING_INFORMATION.md)
- [ダクトEngineering Information検証](DUCT_ENGINEERING_INFORMATION_ja.md)
- [Reproduce Pipe Results](REPRODUCE_PIPE_RESULTS.md)
- [配管結果の再現](REPRODUCE_PIPE_RESULTS_ja.md)
