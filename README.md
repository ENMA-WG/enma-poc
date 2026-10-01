# ENMA-WG PoC

**openBIM | MEP | Quantity Takeoff**

## Revisiting the Promise of Automated MEP Quantity Takeoff

Proof of Concept presented at the  
**buildingSMART International Summit Tokyo 2026**

> **IFC Data → Engineering Meaning → Engineering Quantity**

MEP quantity takeoff is not simply a matter of extracting geometry from a BIM model.

An IFC model may tell us that a pipe exists, where it is located, and how long it is.  
But engineering quantity takeoff requires more:

- What system does the element belong to?
- What does its size mean in engineering terms?
- Where is it installed?
- Which specification applies?
- How should fittings, insulation, painting, and labor be considered?
- What information is missing and requires engineering judgment?

The ENMA-WG PoC explores how we can bridge the gap between **IFC data** and **engineering quantities** using openBIM technologies and explicit engineering rules.

---

## From IFC Data to Engineering Quantity

```text
IFC Data
   │
   │  Geometry / Properties / Relationships
   ▼
Engineering Meaning
   │
   │  Classification / System / Size / Location
   │  IDS / bSDD / Specifications / Engineering Rules
   ▼
Engineering Quantity
      Length / Count / Surface / Insulation / Painting / Labor ...
```

The goal is not merely to **count BIM objects**.

The goal is to make the reasoning between the BIM model and the resulting quantity **explicit, reviewable, and reproducible**.

---

## What You Can Explore Here

This repository accompanies our Tokyo Summit presentation and allows you to:

- **Explore the PoC** — see how real IFC building-services data is processed.
- **Review the approach** — follow the transformation from IFC elements to engineering quantities.
- **Reproduce the results** — run the scripts and compare the generated CSV outputs.
- **Inspect the data model** — see how IFC data, specifications, inference, human review, and quantity results are separated.
- **Share your feedback** — discuss assumptions, missing information, and practical quantity-takeoff requirements through GitHub Issues.

---

## Proof of Concept

The current PoC focuses first on **MEP piping** using a real Japanese government BIM model.

For the sample model, the pipeline identifies:

- **252 `IfcPipeSegment` elements**
- **81 `IfcPipeFitting` elements**
- Pipe system, size, floor, direction, and length information
- Horizontal and vertical pipe quantities
- Cases where IFC information alone is insufficient for engineering quantity takeoff

### Pipe Quantity Results

The reproducible pipe-length result used in the Tokyo Summit presentation is:

| Quantity | Result |
|---|---:|
| Total pipe length | **649.090 m** |
| Horizontal | **375.963 m** |
| Vertical | **273.127 m** |
| Summary rows | **138** |
| Skipped pipe elements | **0** |

These results form the starting point—not the end point—of the ENMA approach.

The next question is:

> **How do we transform geometrically correct IFC quantities into quantities that an MEP engineer can actually use?**

Detailed step-by-step reproduction instructions are available here:

- [Reproducing the Pipe Quantity Results](docs/REPRODUCE_PIPE_RESULTS.md)
- [日本語版 / Japanese version](docs/REPRODUCE_PIPE_RESULTS_ja.md)

---

## Objectives

This PoC explores how IFC, IDS, bSDD, engineering specifications, and lightweight software tools can support practical MEP quantity takeoff workflows.

The project focuses on:

- IFC geometry and property extraction
- MEP equipment, duct, and pipe identification
- Quantity takeoff
- IFC data quality checking
- IDS-based information requirements
- bSDD-based semantic enrichment
- Explicit engineering rules
- Human review of uncertain or inferred information
- Reproducible openBIM workflows

The project also investigates a fundamental question:

> **What information must exist in an IFC model, and what information must be supplied by engineering knowledge, specifications, or human judgment?**

---

## ENMA Approach

ENMA treats quantity takeoff as a process rather than a single calculation.

```text
IFC Model
    │
    ▼
Element Extraction
    │
    ▼
Engineering Interpretation
    │
    ├── IFC properties and relationships
    ├── IDS information requirements
    ├── bSDD semantic definitions
    ├── Engineering specifications
    └── Engineering rules
    │
    ▼
Inference / Missing Information Detection
    │
    ▼
Human Review
    │
    ▼
Quantity Calculation
    │
    ▼
Traceable Engineering Quantity
```

This separation is important because engineering quantity takeoff often requires information that cannot be derived from geometry alone.

The longer-term ENMA data model therefore separates:

- source IFC elements
- project specifications
- reference/master data
- inference results
- human reviews
- rule evaluations
- final quantity results

This architecture is intended to keep the reasoning behind each quantity **traceable**.

More detailed documentation of the data model will be added under `docs/`.

---

## Repository Structure

```text
enma-poc/
├── data/           Sample data information and data source notes
├── docs/           Architecture and methodology
├── output/         Generated CSV and PoC output examples
├── presentation/   Tokyo Summit presentation materials
├── src/            PoC source code
├── tests/          Tests
├── LICENSE
└── README.md
```

### `src/`

Python scripts for IFC inspection, extraction, and quantity processing.

The piping PoC includes scripts for tasks such as:

- extracting pipe information
- summarizing pipe quantities
- inspecting pipe systems
- inspecting fitting sizes and connections

### `output/`

Generated CSV files and representative PoC results.

These files allow the processing results to be inspected without running the entire workflow.

### `docs/`

Documentation of the ENMA methodology, architecture, data model, and engineering assumptions.

### `presentation/`

Materials related to:

**Revisiting the Promise of Automated MEP Quantity Takeoff**  
buildingSMART International Summit Tokyo 2026

---

## Sample BIM Data

The PoC uses the **Government Building BIM Model (Revit version)** published by the Ministry of Land, Infrastructure, Transport and Tourism (**MLIT**), Japan.

The original Autodesk Revit 2022 model is converted to IFC and processed by ENMA-WG for research and demonstration purposes.

The original BIM data is **not distributed in this repository**.

Users wishing to reproduce the workflow should obtain the source BIM data from the original provider and prepare the corresponding IFC file.

Additional information about the sample data and conversion assumptions will be documented under `data/`.

---

## Environment

The current PoC has been developed and tested primarily with:

- Windows 11
- Python 3.11
- IfcOpenShell
- Git

A reproducible environment setup procedure, including Python virtual environment creation and required packages, will be documented in this repository.

---

## Reproducing the Pipe Quantity Results

The basic processing flow is:

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

The target result is:

```text
IfcPipeSegment : 252
Total Length   : 649.090 m
Horizontal     : 375.963 m
Vertical       : 273.127 m
Summary Rows   : 138
Skipped        : 0
```

For detailed commands, input-file preparation, assumptions, and validation steps, see:

- [Reproducing the Pipe Quantity Results](docs/REPRODUCE_PIPE_RESULTS.md)
- [日本語版 / Japanese version](docs/REPRODUCE_PIPE_RESULTS_ja.md)

---

## Why Engineering Meaning Matters

A pipe length extracted from IFC is not automatically a construction quantity.

For example, practical MEP quantity takeoff may also require:

- nominal pipe size and actual outside diameter
- pipe material
- system and fluid
- construction location
- exposed or concealed installation
- insulation specification
- painting specification
- fitting treatment
- applicable design or construction specification
- labor productivity
- engineer review when information is missing or ambiguous

ENMA therefore treats IFC as an important **source of engineering information**, but not as the complete engineering knowledge base.

The aim is to connect openBIM data with the engineering knowledge required for real quantity takeoff.

---

## Current Status

This repository is a **Proof of Concept** and is under active development.

Current work includes:

- piping quantity extraction
- pipe fitting inspection
- construction-location interpretation
- duct quantity takeoff
- engineering specification mapping
- inference and human-review workflows
- quantity and labor data models

The implementation should therefore be understood as an experimental research workflow rather than a production quantity-estimating system.

---

## Feedback

We welcome feedback from:

- MEP engineers
- quantity surveyors and estimators
- BIM practitioners
- IFC software developers
- openBIM researchers
- buildingSMART community members

In particular, we are interested in practical questions such as:

- Which IFC information is reliable enough for quantity takeoff?
- Which engineering information is usually missing?
- Which decisions still require human judgment?
- How should quantity-calculation assumptions be recorded?
- How can IDS and bSDD support practical MEP workflows?
- How should openBIM quantity results be validated?

Please use **GitHub Issues** to share comments, questions, and suggestions.

---

## ENMA-WG

ENMA-WG explores practical uses of openBIM for MEP engineering.

Our goal is not simply to automate existing work.

We aim to make the engineering knowledge behind quantity takeoff **explicit, structured, reusable, and open to review**.

---

## License

Source code developed by ENMA-WG in this repository is provided under the **MIT License**.

Third-party BIM data, documents, and other materials are subject to their respective licenses and terms of use.

The Government Building BIM Model used for the PoC is not redistributed as part of this repository.
