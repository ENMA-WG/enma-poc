# Reproducing the Pipe Quantity Results

## Overview

This document explains how to reproduce the pipe quantity results presented in:

**Revisiting the Promise of Automated MEP Quantity Takeoff**  
buildingSMART International Summit Tokyo 2026

The purpose of this PoC is not only to calculate quantities from IFC geometry, but also to make the calculation process **explicit, reviewable, and reproducible**.

The basic workflow is:

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

For the Tokyo Summit PoC, the workflow was tested using an MEP IFC model derived from the Japanese government BIM sample data.

---

## Expected Results

The pipe quantity results presented at the Tokyo Summit are:

| Item | Result |
|---|---:|
| IfcPipeSegment | 252 |
| Summary rows | 138 |
| Skipped elements | 0 |
| Total pipe length | 649.090 m |
| Horizontal pipe length | 375.963 m |
| Vertical pipe length | 273.127 m |
| Sloped pipe length | 0.000 m |

These values were reproduced again from the current PoC code on **October 1, 2026**, before the Tokyo Summit presentation.

---

## Prerequisites

The PoC has been developed and tested primarily with:

- Windows 11
- Python 3.11
- IfcOpenShell
- Git

Run the commands below from the repository root.

For example:

```text
G:\enma-wg\enma-poc
```

A Python virtual environment is recommended.

Example on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

> The exact environment setup and dependency installation procedure may be updated as the PoC repository is refined.

---

## Preparing the IFC File

The extraction script currently expects the following IFC file:

```text
data/営繕BIMモデル_EM.ifc
```

The sample used for this PoC is based on the **Government Building BIM Model** published by Japan's Ministry of Land, Infrastructure, Transport and Tourism (MLIT).

The original model was provided as an Autodesk Revit 2022 model and was converted to IFC for this PoC.

The source BIM/IFC data is **not redistributed in this repository**.

Users wishing to reproduce the complete workflow should obtain the source BIM data from the original provider and prepare the corresponding IFC file.

The current extraction script uses the fixed path:

```python
IFC_FILE = Path("data/営繕BIMモデル_EM.ifc")
```

Therefore, the IFC file should be placed at that location before running the script.

---

## Step 1 — Extract Pipe Segments

Run:

```powershell
python .\src\extract_pipes.py
```

The script opens the IFC model and extracts:

```text
IfcPipeSegment
```

For the Tokyo Summit sample model, the expected number of elements is:

```text
IfcPipeSegment count: 252
```

The script analyzes each pipe segment and writes the detailed extraction result to:

```text
output/pipes_detail.csv
```

During the extraction, the script also interprets the pipe direction from IFC geometry.

For example:

```text
axis=(1.0000, 0.0000, 0.0000)  → horizontal
axis=(0.0000, 1.0000, 0.0000)  → horizontal
axis=(0.0000, 0.0000, 1.0000)  → vertical
```

Non-orthogonal horizontal geometry can also occur. For example:

```text
axis=(0.7071, -0.7071, 0.0000)
```

is classified as horizontal.

The expected extraction summary is:

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

No pipe segments were lost during this extraction.

---

## Step 2 — Aggregate Pipe Quantities

After `pipes_detail.csv` has been generated, run:

```powershell
python .\src\summarize_pipes.py
```

The aggregation workflow is:

```text
output/pipes_detail.csv
        ↓
src/summarize_pipes.py
        ↓
output/pipes_summary.csv
```

The expected console output is:

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

These values correspond to the pipe quantity results presented at the Tokyo Summit.

---

## Output Files

Two main CSV files are used for this workflow.

### `output/pipes_detail.csv`

This is the element-level extraction result.

Each IFC pipe segment is represented individually so that the quantity calculation can be traced back toward the source IFC element.

The extracted information includes data such as:

- IFC element identity
- floor/storey
- system information
- pipe type
- size information
- length
- direction classification
- geometric information

This file represents the transition from:

```text
IFC Data
```

toward:

```text
Engineering Meaning
```

### `output/pipes_summary.csv`

This is the aggregated quantity result generated from `pipes_detail.csv`.

The detail records are grouped into engineering-oriented quantity categories to produce the summary used for quantity takeoff.

This represents the next transition:

```text
Engineering Meaning
        ↓
Engineering Quantity
```

Both CSV files are included in this repository so that the extracted and aggregated results can be reviewed even without the original IFC model.

---

## Reproducibility Check

On October 1, 2026, immediately before the Tokyo Summit, the complete pipe extraction and aggregation workflow was executed again.

The following sequence was used:

```powershell
python .\src\extract_pipes.py
python .\src\summarize_pipes.py
git status --short
```

The regenerated:

```text
output/pipes_detail.csv
output/pipes_summary.csv
```

showed **no Git differences** from the versions already stored in this repository.

Therefore, the current PoC code reproduced not only the same total quantities, but also the same stored detail and summary CSV results.

---

## Traceability

A key objective of ENMA-WG is not merely to produce a final quantity.

The calculation should remain traceable.

Conceptually:

```text
IFC Element
    │
    │ GlobalId / IFC properties / geometry
    ↓
pipes_detail.csv
    │
    │ engineering interpretation
    ↓
pipes_summary.csv
    │
    │ aggregation
    ↓
Engineering Quantity
```

This allows an engineer to investigate where a quantity came from instead of treating the final number as a black-box result.

The longer-term ENMA concept extends this traceability to:

```text
IFC Data
   ↓
Engineering Interpretation
   ↓
Inference / Missing Information Detection
   ↓
Human Review
   ↓
Rule Evaluation
   ↓
Engineering Quantity
```

---

## What the Current Pipe PoC Demonstrates

The current Step 1 PoC demonstrates that IFC pipe geometry and associated information can be transformed into a reproducible engineering-oriented quantity dataset.

In particular, it demonstrates:

- extraction of all 252 `IfcPipeSegment` elements in the test model
- identification of floor/storey
- extraction and interpretation of pipe properties
- interpretation of pipe orientation
- separation of horizontal and vertical pipe quantities
- element-level CSV output
- engineering-oriented quantity aggregation
- traceability from IFC elements to aggregated quantities
- reproducibility of the published Tokyo Summit results

---

## Current Limitations

The current result should **not** be interpreted as a complete construction estimate.

At this stage, the pipe length represents the current IFC-based quantity interpretation used by the PoC.

Several engineering considerations still need to be incorporated or refined, including:

- treatment of fitting lengths
- construction location
- exposed / concealed conditions
- pipe material interpretation
- insulation requirements
- painting requirements
- applicable project specifications
- labor productivity
- missing-information handling
- human engineering review

These are important because geometrically correct quantities are not necessarily sufficient for real MEP estimation.

For example:

```text
649.090 m of pipe
```

is useful geometric information.

But an estimator may also need to know:

```text
What system?
What nominal size?
What material?
Where is it installed?
Is it exposed or concealed?
Does it require insulation?
Does it require painting?
How are fittings treated?
Which specification applies?
What labor productivity applies?
```

This distinction is central to the ENMA-WG approach:

> **IFC Data → Engineering Meaning → Engineering Quantity**

---

## Next Steps

The PoC is being extended toward:

- fitting interpretation
- construction-location inference
- architectural space relationships
- insulation and painting requirements
- duct quantity takeoff
- project specification mapping
- inference and missing-information detection
- human review
- rule evaluation
- labor and productivity models

The goal is not simply to extract more IFC properties.

The goal is to determine how IFC information can become **usable, explainable, and reviewable engineering knowledge**.

---

## Feedback

This is an experimental PoC and is still evolving.

We welcome feedback from:

- MEP engineers
- estimators
- BIM coordinators
- IFC implementers
- software developers
- researchers
- buildingSMART community members

In particular, we are interested in questions such as:

- Which quantities are actually needed for MEP estimation?
- Which IFC properties are reliable enough to use directly?
- Which engineering meanings must be inferred?
- Which decisions require human review?
- How should missing information be represented?
- How should the results remain traceable to the original IFC model?

Please use the GitHub Issues section of this repository to share comments, questions, or suggestions.

---

## ENMA-WG

ENMA-WG explores practical openBIM workflows for building services engineering.

Our aim is to connect:

```text
IFC
+
Engineering Knowledge
+
Open Standards
+
Human Review
```

and investigate how openBIM can support practical MEP engineering workflows beyond geometry alone.

**IFC Data → Engineering Meaning → Engineering Quantity**

