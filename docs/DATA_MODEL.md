# ENMA Quantity Takeoff Data Model

The **ENMA Quantity Takeoff Data Model** describes how IFC data can be transformed into engineering quantities through explicit, traceable engineering interpretation.

It is the conceptual data model behind the ENMA-WG approach presented at the **buildingSMART International Summit Tokyo 2026**.

The central idea is:

```text
IFC Data
    ↓
Engineering Meaning
    ↓
Engineering Quantity
```

A construction quantity is not simply read from IFC.

IFC provides geometry, properties, classifications, systems, ports, connections, and other relationships. Engineering quantity takeoff requires these data to be interpreted together with project specifications, engineering master data, calculation rules, and—in some cases—human judgment.

The ENMA data model is intended to make this interpretation process explicit and traceable.

---

## 1. Why a Data Model Is Needed

For a simple quantity calculation, it may appear sufficient to extract a length, area, or count directly from an IFC model.

Real MEP quantity takeoff is more complex.

For example, a pipe quantity may depend not only on its geometric length, but also on:

- system
- floor or space
- pipe size
- pipe material
- construction location
- insulation requirements
- painting requirements
- applicable project specifications
- engineering rules
- missing or ambiguous information

Some of these values can be read directly from IFC.

Others must be derived from relationships between IFC elements, interpreted using engineering knowledge, or confirmed by an engineer.

The ENMA Quantity Takeoff Data Model separates these different responsibilities instead of treating quantity takeoff as a single IFC extraction operation.

---

## 2. How to Read the ENMA Classification Codes

The ENMA data model organizes tables and engineering information into six major categories.

| Code | Category | Purpose |
|---|---|---|
| **P** | Project / Transaction | Project-specific data, IFC elements, properties, ports, connections, and calculation transactions |
| **S** | Specification | Source specifications, specification sets, and project-applied specifications |
| **M** | Master | Reusable engineering master data such as fluids, work locations, materials, and sizes |
| **R** | Rule | Engineering rules used to interpret specifications and determine quantities |
| **I** | Inference / Evaluation | ENMA inference, rule evaluation, and engineering review |
| **O** | Output / Result | Element-level results, quantity summaries, and calculation evidence |

Codes such as `M10`, `I20`, and `O30` are classification identifiers used to organize the ENMA data model.

More detailed codes identify individual groups and tables.

For example:

```text
M
└─ M10
   ├─ M10-01
   └─ M10-02
```

The code therefore provides a simple way to understand where each table belongs in the overall engineering information model.

---

## 3. Example: How to Read M10

`M` represents **Master Data**.

Within the Master Data category, `M10` represents **Common / Classification** master data.

For example:

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

This hierarchy separates reusable engineering knowledge from individual IFC projects.

For example, an IFC model may contain a pipe diameter or system name, while engineering master data can provide the corresponding pipe standard, nominal size, material information, or other information required for quantity takeoff.

The same master data can then be reused across multiple projects.

---

## 4. From IFC Data to Engineering Quantity

The overall ENMA concept can be viewed as the following information flow:

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

Each category has a different role.

**Project / Transaction (P)** stores information specific to the project and IFC model.

**Specification (S)** represents the specifications and requirements applicable to the project.

**Master (M)** provides reusable engineering knowledge.

**Rule (R)** represents the engineering logic used to interpret the available information.

**Inference / Evaluation (I)** records the results of automated interpretation, rule evaluation, and engineering review.

**Output / Result (O)** stores the resulting quantities and the evidence used to produce them.

This separation is important because the same IFC geometry can produce different engineering quantities depending on the applicable specifications, materials, construction conditions, and engineering rules.

---

## 5. Human-in-the-Loop Engineering

ENMA does not assume that every engineering decision can or should be automated.

MEP models may contain:

- missing properties
- ambiguous classifications
- incomplete relationships
- project-specific conventions
- information that requires engineering judgment

For this reason, the data model includes a human-review process.

A simplified flow is:

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

`inference_results` can record what ENMA inferred from IFC data and engineering knowledge.

When the result is uncertain or requires confirmation, `human_reviews` provides a place for an engineer to review the inference.

The reviewed information can then be used in subsequent rule evaluation and quantity calculation.

Finally, `calculation_evidence` is intended to preserve the basis of the calculated result.

The objective is therefore not simply:

```text
IFC → Quantity
```

but rather:

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

This makes the quantity takeoff process more transparent and auditable.

---

## 6. Example: Pipe Quantity Takeoff

The current ENMA PoC provides a simple example of this approach using real IFC pipe data.

At the IFC level, an `IfcPipeSegment` contains or relates to information such as:

- GlobalId
- geometry
- length
- system
- properties
- placement
- connections

ENMA transforms this IFC information into engineering-oriented attributes.

For the current pipe PoC, these include:

- floor
- system code
- system name
- IFC system classification
- outside diameter
- inside diameter
- pipe length
- direction classification
- axis direction
- elevation range

The simplified interpretation flow is:

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

Using the current sample IFC model, the PoC extracts:

```text
IfcPipeSegment      : 252
Summary rows        : 138
Total length        : 649.090 m
Horizontal length   : 375.963 m
Vertical length     : 273.127 m
Sloped length       :   0.000 m
```

These results can be reproduced using:

- `src/extract_pipes.py`
- `src/summarize_pipes.py`

and inspected in:

- `output/pipes_detail.csv`
- `output/pipes_summary.csv`

See:

- [`REPRODUCE_PIPE_RESULTS.md`](REPRODUCE_PIPE_RESULTS.md)
- [`REPRODUCE_PIPE_RESULTS_ja.md`](REPRODUCE_PIPE_RESULTS_ja.md)

for the reproduction procedure.

---

## 7. Relationships Can Also Provide Engineering Meaning

Engineering information does not always exist as a property on the element being quantified.

For example, in the current fitting PoC, information about a pipe fitting can be derived from its relationship with connected pipe segments.

A simplified example is:

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

This illustrates an important ENMA principle:

> Engineering meaning may come not only from an IFC element itself, but also from its relationships and context.

This becomes increasingly important when quantity takeoff requires information about systems, spaces, construction locations, fittings, insulation, or other engineering conditions.

---

## 8. Current PoC Scope

The data model represents a broader engineering framework than the functionality currently implemented in the public PoC.

### Demonstrated in the current PoC

The current repository demonstrates, among other things:

- IFC pipe element extraction
- system identification
- pipe diameter extraction
- pipe length extraction
- horizontal / vertical direction classification
- pipe quantity aggregation
- pipe fitting extraction
- fitting classification
- use of connected pipe information for fitting connection diameters

### Designed or under development

The broader ENMA data model also addresses areas such as:

- construction-location interpretation
- project specifications
- pipe material and standard mapping
- insulation requirements
- painting requirements
- labor productivity
- rule-based engineering interpretation
- human review of inferred information
- calculation evidence
- duct quantity workflows
- equipment-related workflows

The presence of a category or table in the data model does **not** mean that all corresponding functions are already implemented in the current PoC.

The data model is intended to provide a framework for progressively extending the quantity takeoff process.

---

## 9. Traceability

A major objective of the ENMA approach is traceability.

For a calculated engineering quantity, it should eventually be possible to answer questions such as:

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

This is why ENMA separates project data, engineering knowledge, inference, human review, quantity results, and calculation evidence.

The goal is not only to calculate a number, but also to preserve the engineering reasoning behind that number.

---

## 10. Detailed Table Definitions

This document provides a conceptual guide to the ENMA Quantity Takeoff Data Model.

Detailed table and field definitions are maintained in:

**[`ENMA_Data_Model.xlsx`](ENMA_Data_Model.xlsx)**

The spreadsheet contains the detailed table structure used in the ongoing ENMA-WG design work.

The data model continues to evolve as the PoC expands from basic IFC quantity extraction toward broader MEP engineering quantity takeoff.

---

## Related Documents

- [`REPRODUCE_PIPE_RESULTS.md`](REPRODUCE_PIPE_RESULTS.md) — Reproduce the pipe quantity results presented at the Tokyo Summit
- [`REPRODUCE_PIPE_RESULTS_ja.md`](REPRODUCE_PIPE_RESULTS_ja.md) — Japanese reproduction guide
- [`ENMA_Data_Model.xlsx`](ENMA_Data_Model.xlsx) — Detailed ENMA table definitions

---

## ENMA-WG

ENMA-WG explores practical methods for connecting openBIM / IFC data with MEP engineering knowledge and quantity takeoff.

The objective is not merely to extract data from IFC, but to make the engineering interpretation between model data and construction quantities explicit, reusable, and traceable.
