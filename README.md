# ENMA-WG PoC

**openBIM | MEP | Quantity Takeoff**

[🇯🇵 日本語版 / Japanese README](README_ja.md)

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

### Key Documentation

- [ENMA 3.0 FAQ](docs/FAQ.md) — start here for an overview of the ENMA approach, engineering knowledge, human review, and future direction.
- [Sample Outputs](docs/SAMPLE_OUTPUTS.md) — inspect representative pipe and fitting outputs and how engineering meaning is derived.
- [ENMA Quantity Takeoff Data Model](docs/DATA_MODEL.md) — explore the data architecture behind specifications, inference, human review, rules, and quantity results.
- [Reproducing the Pipe Quantity Results](docs/REPRODUCE_PIPE_RESULTS.md) — reproduce the pipe quantities presented at the Tokyo Summit.
- [Duct Geometry, QTO Validation, and System Extraction](docs/DUCT_EXTRACTION.md) — inspect how 1,077 `IfcDuctSegment` elements are extracted from IFC geometry, cross-checked against IFC QTO, and associated with `IfcDistributionSystem`.
- [Duct Engineering Information Validation](docs/DUCT_ENGINEERING_INFORMATION.md) — examine what engineering information is available or missing when moving from reproducible duct quantities toward specification selection.
- [Duct Topology Validation](docs/DUCT_TOPOLOGY_VALIDATION.md) — Validation of system membership, port ownership, explicit connectivity, and geometric proximity using real IFC data

Japanese versions are also available:

- [ENMA 3.0 FAQ — 日本語](docs/FAQ_ja.md)
- [Sample Outputs — 日本語](docs/SAMPLE_OUTPUTS_ja.md)
- [Data Model — 日本語](docs/DATA_MODEL_ja.md)
- [Pipe Result Reproduction — 日本語](docs/REPRODUCE_PIPE_RESULTS_ja.md)
- [Duct Geometry, QTO Validation, and System Extraction — 日本語](docs/DUCT_EXTRACTION_ja.md)
- [Duct Engineering Information Validation — 日本語](docs/DUCT_ENGINEERING_INFORMATION_ja.md)
- [Duct Topology Validation — 日本語](docs/DUCT_TOPOLOGY_VALIDATION_ja.md)
- [Python Tools Guide — 日本語](docs/PYTHON_TOOLS_ja.md)

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

### Duct Geometry, QTO Validation, and System Extraction

The PoC has also been extended to `IfcDuctSegment` geometry extraction, QTO cross-validation, and air-system extraction through formal IFC relationships.

For the current MLIT test IFC:

| Validation | Result |
|---|---:|
| IfcDuctSegment | **1,077** |
| Round ducts | **792** |
| Rectangular ducts | **285** |
| Unknown shape | **0** |
| Geometry extraction | **1,077 / 1,077** |
| Geometry/QTO length match | **1,077 / 1,077** |
| Rectangular area match | **285 / 285** |
| Exactly one `IfcDistributionSystem` assignment | **1,077 / 1,077** |
| No system assignment | **0** |
| Multiple system assignments | **0** |

The system assignments in the current test IFC are mapped from `IfcDistributionSystem.ObjectType` to the following ENMA air types:

| Air type | Duct segments |
|---|---:|
| SA | **512** |
| RA | **4** |
| OA | **112** |
| EA | **449** |
| UNKNOWN | **0** |

The raw IFC system `Name` and `ObjectType` are preserved in the CSV. The SA/RA/OA/EA classification is an explicit ENMA mapping from `IfcDistributionSystem.ObjectType`; it is **not inferred from the duct element name**.

Round ducts showed a consistent **0.015038%** difference between the geometry-derived circular area and QTO `GrossCrossSectionArea`. Rather than hiding this difference by relaxing the tolerance, the PoC preserves it as a validation result.

Raw IFC geometry dimensions are also preserved without silently converting them to nominal duct sizes.

- [Duct Geometry, QTO Validation, and System Extraction](docs/DUCT_EXTRACTION.md)
- [日本語版 / Japanese version](docs/DUCT_EXTRACTION_ja.md)

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

See the [ENMA Quantity Takeoff Data Model](docs/DATA_MODEL.md) for the detailed architecture and table hierarchy.

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

See [Sample Outputs](docs/SAMPLE_OUTPUTS.md) for an explanation of how the pipe and fitting CSV outputs relate to engineering quantity takeoff.

### `docs/`

Documentation of the ENMA methodology, architecture, data model, and engineering assumptions.

### `presentation/`

Materials related to:

**Revisiting the Promise of Automated MEP Quantity Takeoff**  
buildingSMART International Summit Tokyo 2026
October 7, 2026

Tokyo Summit 2026 presentation archive:

- [Presentation Slides (PDF)](presentation/tokyo-summit-2026/Automated_MEP_Quantity_Takeoff_final.pdf)
- [Submitted Abstract](presentation/tokyo-summit-2026/TOKYO_SUMMIT_2026_ABSTRACT.md)
- [Speaker Notes](presentation/tokyo-summit-2026/TOKYO_SUMMIT_2026_SPEAKER_NOTES.md)

The presentation materials document the research baseline presented at the
Tokyo Summit. Development after the Summit continues through GitHub Issues
and subsequent research activities.

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
- Python 3.11.9
- IfcOpenShell 0.8.5
- Git

The repository includes:

- `requirements.txt` — Python package dependencies
- `scripts/check_environment.ps1` — Windows development environment checker

### Prerequisites

Before starting, make sure the following tools are available:

- Windows 11
- PowerShell
- Git
- Python 3.11

You can check them with:

```powershell
git --version
py -3.11 --version
```

### Quick Start

The following example shows the basic setup on Windows PowerShell.

#### 1. Clone the repository

```powershell
git clone https://github.com/ENMA-WG/enma-poc.git
cd enma-poc
```

#### 2. Create a Python virtual environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### 3. Install the required packages

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Check the environment

```powershell
.\scripts\check_environment.ps1
```

The reference environment currently uses Python 3.11.9 and IfcOpenShell 0.8.5.

The environment checker accepts Python 3.11.9 as the reference version and reports other Python 3.11 patch versions as warnings.

#### 5. Prepare the IFC file

Place the IFC model used for the pipe PoC at:

```text
data/営繕BIMモデル_EM.ifc
```

The source BIM/IFC model is not redistributed in this repository. Obtain the source BIM data from the original provider and prepare the corresponding IFC file.

For detailed input-file preparation and assumptions, see:

- [Reproducing the Pipe Quantity Results](docs/REPRODUCE_PIPE_RESULTS.md)
- [日本語版 / Japanese version](docs/REPRODUCE_PIPE_RESULTS_ja.md)

#### 6. Run the pipe quantity PoC

```powershell
python .\src\extract_pipes.py
python .\src\summarize_pipes.py
```

The expected result is:

```text
Pipe segments : 252
Summary rows  : 138
Skipped       : 0

Total length      : 649.090 m
Horizontal length : 375.963 m
Vertical length   : 273.127 m
Sloped length     : 0.000 m
```

#### 7. Run the duct extraction and system-validation PoC

```powershell
python .\src\extract_ducts.py
```

The expected validation summary includes **1,077 `IfcDuctSegment` elements**, with **792 round** and **285 rectangular** ducts. Geometry extraction succeeds for all 1,077 elements, geometry-derived lengths match the IFC QTO lengths for all 1,077 elements, and all 1,077 duct segments have exactly one `IfcDistributionSystem` assignment. The current system mapping produces **SA 512 / RA 4 / OA 112 / EA 449 / UNKNOWN 0**.

For detailed geometry assumptions, system extraction, validation tolerances, output columns, and observed Geometry/QTO differences, see [Duct Geometry, QTO Validation, and System Extraction](docs/DUCT_EXTRACTION.md).

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
- duct geometry extraction, QTO cross-validation, and `IfcDistributionSystem` extraction
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
