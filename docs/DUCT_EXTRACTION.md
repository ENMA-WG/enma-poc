# Duct Geometry, QTO Validation, and System Extraction

## Overview

This document describes the duct extraction experiment implemented in
the ENMA-WG Automated MEP Quantity Takeoff PoC.

The experiment extracts dimensions directly from IFC duct geometry,
cross-checks the geometry-derived values against IFC Quantity Takeoff
(QTO) properties, and extracts air-system information through formal IFC
relationships.

The purpose is not only to obtain duct quantities, but also to examine
whether geometry, QTO, and relationship-based system information inside
the IFC model can be kept explicit and mutually reviewable.

The current experiment focuses on:

-   `IfcDuctSegment`
-   duct shape classification
-   round duct diameter
-   rectangular duct width and height
-   duct length
-   cross-sectional area
-   comparison between IFC geometry and QTO values
-   `IfcDistributionSystem` assignment
-   preservation of raw system `Name` and `ObjectType`
-   explicit mapping to ENMA air type (SA / RA / OA / EA)

> **Important**
>
> This is a research PoC. Geometry dimensions are preserved as they
> exist in the source IFC model. They are not automatically converted to
> nominal or standard duct sizes.

## Target IFC

The current test uses the Japanese MLIT BIM sample model used by the
ENMA-WG PoC.

Expected local path:

``` text
data/営繕BIMモデル_EM.ifc
```

The IFC file itself is not included in this repository.

## Requirements

The current ENMA-WG PoC environment uses:

-   Windows 11
-   Python 3.11.9
-   IfcOpenShell 0.8.5

Install the project dependencies from the repository root:

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Running the Extraction

From the repository root:

``` powershell
python .\src\extract_ducts.py
```

Output:

``` text
output/ducts_detail.csv
```

The CSV is written as UTF-8 with BOM (`utf-8-sig`) for compatibility
with common spreadsheet applications.

## System Extraction Path

The current script also follows the formal IFC group assignment from each
`IfcDuctSegment` to `IfcDistributionSystem`:

``` text
IfcDuctSegment
  └─ IfcRelAssignsToGroup
       └─ IfcDistributionSystem
```

For each duct segment, the script preserves the raw IFC system `Name` and
`ObjectType` as `SystemName` and `SystemObjectType`.

For the current MLIT test IFC, all 1,077 duct segments have exactly one
`IfcDistributionSystem` assignment:

``` text
Single system       : 1077
No system           : 0
Multiple systems    : 0
```

The current source values are explicitly mapped as follows:

| `IfcDistributionSystem.ObjectType` | ENMA `AirType` |
|---|---|
| `101_SA給気` | `SA` |
| `102_RA還気` | `RA` |
| `103_OA外気` | `OA` |
| `105_EA排気` | `EA` |

This produces:

| AirType | Count |
|---|---:|
| SA | **512** |
| RA | **4** |
| OA | **112** |
| EA | **449** |
| UNKNOWN | **0** |
| **Total** | **1,077** |

This mapping is deliberately separated from raw IFC extraction. The script
does **not** infer SA/RA/OA/EA from the duct element `Name` or `ObjectType`
when an `IfcDistributionSystem` assignment is available.

`SystemSource` records how the system information was obtained. In the
current test result, all 1,077 rows use `IFC_DISTRIBUTION_SYSTEM`.

## Geometry Extraction Path

In the current MLIT test IFC, all 1,077 `IfcDuctSegment` elements
examined by this PoC use the following geometry structure:

``` text
IfcDuctSegment
  └─ IfcExtrudedAreaSolid
       └─ IfcArbitraryClosedProfileDef
            └─ IfcIndexedPolyCurve
                 └─ IfcCartesianPointList2D
```

The extrusion depth is used as the geometry-derived duct length.

The local 2D profile coordinates are used to derive the duct
cross-sectional dimensions.

Using local profile coordinates is important. A world-space axis-aligned
bounding box may be enlarged by rotation or orientation and therefore
does not necessarily represent the actual duct width, height, or length.

## Shape Classification

The current script classifies duct segments as:

-   `ROUND`
-   `RECTANGULAR`
-   `UNKNOWN`

The primary classification uses the profile geometry.

For the current IFC:

-   profiles containing `IfcArcIndex` segments are classified as `ROUND`
-   profiles without arc segments are classified as `RECTANGULAR`

Japanese `ObjectType` and `Name` values are used only as a fallback.

### Current result

``` text
IfcDuctSegment       : 1077
ROUND                : 792
RECTANGULAR          : 285
UNKNOWN              : 0
```

## Dimension Extraction

### Round ducts

Round duct diameter is derived from the local profile coordinates.

The current IFC represents round profiles using arc segments. Radial
distances from the local profile origin are used to determine the
diameter.

The 792 round ducts contain the following geometry-derived diameters:

     Diameter     Count
  ----------- ---------
       100 mm         8
       150 mm       121
       200 mm       362
       250 mm       264
       300 mm        30
       350 mm         7
    **Total**   **792**

These values describe the geometry found in the current source IFC.

### Rectangular ducts

Rectangular width and height are calculated from the extents of the
local 2D profile coordinates.

The larger dimension is currently stored as `Width_mm` and the smaller
dimension as `Height_mm`.

Some profiles contain dimensions that may look unusual from an
engineering or nominal-size perspective, for example fractional or very
large values.

These values are intentionally preserved.

ENMA does **not** silently convert geometry such as:

``` text
750 x 637.626 mm
```

into a nominal size such as:

``` text
750 x 650 mm
```

because doing so would introduce an engineering interpretation that is
not explicitly present in the source geometry.

Such interpretation should be handled separately from raw IFC
extraction.

## Geometry and QTO Cross-Check

The geometry-derived values are compared with:

``` text
Qto_DuctSegmentBaseQuantities
```

The current comparison uses:

-   `Length`
-   `GrossCrossSectionArea`
-   `NetCrossSectionArea`
-   `OuterSurfaceArea`

The current validation tolerances are:

``` text
Length tolerance : 0.01 mm
Area tolerance   : 0.01 %
```

The area tolerance is intentionally strict.

## Validation Results

The current test produced:

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

Air system
  SA                  : 512
  RA                  : 4
  OA                  : 112
  EA                  : 449
  UNKNOWN             : 0

System assignment
  Single system       : 1077
  No system           : 0
  Multiple systems    : 0
```

### Length

Geometry-derived extrusion length matched QTO `Length` for `1077 / 1077`
duct segments under the current tolerance.

### Rectangular cross-sectional area

For all 285 rectangular duct segments, the cross-sectional area
calculated from the local geometry matched QTO `GrossCrossSectionArea`
under the current tolerance.

``` text
RECTANGULAR: 285 / 285
```

### Round cross-sectional area

Round ducts produced a different result.

The geometry-derived circular area is calculated using Python's
`math.pi`.

Under the strict 0.01% tolerance, none of the 792 round ducts matched
the QTO `GrossCrossSectionArea`.

However, further inspection showed that this is not a random error.

Across all 792 round ducts and all six observed diameters from 100 mm
through 350 mm, the CSV-level percentage difference was consistently:

``` text
0.015038 %
```

     Diameter     Count   Min Difference   Max Difference
  ----------- --------- ---------------- ----------------
       100 mm         8        0.015038%        0.015038%
       150 mm       121        0.015038%        0.015038%
       200 mm       362        0.015038%        0.015038%
       250 mm       264        0.015038%        0.015038%
       300 mm        30        0.015038%        0.015038%
       350 mm         7        0.015038%        0.015038%
    **Total**   **792**                  

This PoC deliberately does **not** relax the tolerance simply to make
all records report a match.

Instead, the difference is retained as a validation result.

At this stage, the experiment confirms a consistent difference between
the geometry-derived circular area and the QTO value in the current
source IFC. The cause of that difference has not yet been established.

Therefore, this result should **not** be interpreted as evidence that a
particular authoring application uses a specific value of pi or a
specific calculation method.

## Why Preserve the Difference?

A central idea of this experiment is that IFC quantity extraction should
not automatically assume that one information source is correct.

``` text
IFC Geometry
     │
     ├── dimensions
     ├── extrusion length
     └── calculated area
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

If the values agree, confidence in the extracted quantity increases.

If they do not agree, the difference itself becomes useful engineering
information that may require review.

This is more useful for the ENMA PoC than simply copying a single IFC
property into a quantity table.

## Output Columns

`output/ducts_detail.csv` contains:

  Column                      Description
  --------------------------- -----------------------------------------------
  `GlobalId`                  IFC GlobalId
  `Name`                      IFC element name
  `ObjectType`                IFC ObjectType
  `Storey`                    Containing building storey
  `SystemName`                Raw `IfcDistributionSystem.Name`
  `SystemObjectType`          Raw `IfcDistributionSystem.ObjectType`
  `AirType`                   ENMA mapping: SA / RA / OA / EA / UNKNOWN
  `SystemSource`               Source/status of system assignment
  `Shape`                     ROUND / RECTANGULAR / UNKNOWN
  `Diameter_mm`               Geometry-derived round duct diameter
  `Width_mm`                  Geometry-derived rectangular width
  `Height_mm`                 Geometry-derived rectangular height
  `Geometry_Length_mm`        Extrusion depth from IFC geometry
  `QTO_Length_mm`             QTO Length
  `Geometry_Area_m2`          Cross-sectional area calculated from geometry
  `QTO_GrossArea_m2`          QTO GrossCrossSectionArea
  `QTO_NetArea_m2`            QTO NetCrossSectionArea
  `QTO_OuterSurfaceArea_m2`   QTO OuterSurfaceArea
  `Length_Difference_mm`      Absolute geometry/QTO length difference
  `Length_Match`              Length validation result
  `Area_Difference_pct`       Geometry/QTO area percentage difference
  `Area_Match`                Area validation result
  `ProfileType`               IFC profile type
  `CurveType`                 IFC curve type
  `DimensionSource`           Current dimension source (`IFC_GEOMETRY`)
  `GeometryStatus`            Geometry extraction status

## About Unusual Geometry Dimensions

The current source IFC contains some rectangular profiles with
dimensions that may not resemble typical nominal duct sizes.

The extraction script intentionally preserves those values.

``` text
Raw IFC geometry
        ↓
Geometry extraction
        ↓
Engineering interpretation
        ↓
Nominal / standard size
        ↓
Quantity / specification / labor / schedule
```

The current script now implements raw geometry extraction, QTO cross-validation, and relationship-based system extraction. Nominal-size, specification, labor, and schedule interpretation remain separate engineering stages.

Nominal-size interpretation is a separate engineering task and may
require rules, specifications, reference data, or human review.

## Spreadsheet Note

CSV files are data files, not formatted spreadsheets.

The files in this PoC are exported as UTF-8 with BOM for compatibility
with common spreadsheet applications.

When a CSV file is opened directly in spreadsheet software such as
Microsoft Excel, numeric values, dates, identifiers, or display
precision may be automatically interpreted or reformatted by the
spreadsheet application.

This does not necessarily mean that the original CSV data has changed.

For reproducible analysis, we recommend treating the CSV output as
machine-readable data rather than relying on spreadsheet display
formatting.

## Current Scope and Limitations

This PoC currently assumes the geometry structures observed in the test
IFC.

In particular:

-   the tested duct segments use `IfcExtrudedAreaSolid`
-   profiles use `IfcArbitraryClosedProfileDef`
-   outer curves use `IfcIndexedPolyCurve`
-   round and rectangular profiles are handled
-   geometry dimensions are not converted to nominal sizes
-   fittings are not yet included in this duct quantity experiment
-   air-system information is extracted from `IfcDistributionSystem` in the current test IFC
-   construction location and specification interpretation are not yet
    included
-   unusual dimensions are preserved rather than automatically corrected

Future IFC models may use different representation structures and will
require additional extraction logic.

## Toward ENMA Engineering Interpretation

The current duct experiment separates raw extraction from engineering
interpretation.

A possible future ENMA workflow is:

``` text
IFC
  ↓
Geometry / properties / systems
  ↓
Information validation
  ↓
Quantity
  ↓
Specifications
  ↓
Labor
  ↓
Schedule
```

Information requirements may be validated using IDS, while shared
terminology, classification, and semantic mapping may be supported by
bSDD.

These are future directions of the ENMA-WG research and should not be
interpreted as fully implemented functions of the current PoC.

## Related Files

``` text
src/extract_ducts.py
output/ducts_detail.csv
```

For the existing pipe quantity experiment, see:

``` text
docs/REPRODUCE_PIPE_RESULTS.md
```

## Project

ENMA-WG\
Automated MEP Quantity Takeoff PoC

This experiment is part of the ENMA-WG investigation into reproducible,
openBIM-based MEP quantity takeoff and engineering workflows.

## Duct Quantity Summary

After extracting duct geometry and system information, the results can be summarized by air system, shape, and geometry-derived size.

```powershell
python src/summarize_ducts.py
```

Input:

- `output/ducts_detail.csv`

Output:

- `output/ducts_summary.csv`

Current MLIT test IFC results:

- Input duct segments: 1,077
- Summary rows: 234
- Skipped rows: 0
- Total geometry length: 1,088.945 m
- Total QTO length: 1,088.945 m
- SA: 512 segments / 490.481 m
- RA: 4 segments / 1.400 m
- OA: 112 segments / 148.086 m
- EA: 449 segments / 448.978 m

The summary key is:

`AirType × Shape × Size`

`Size` preserves geometry-derived dimensions. It does not convert them to nominal engineering sizes.

Examples:

- ROUND: `D200`
- RECTANGULAR: `750x637.626`

This distinction is important for subsequent engineering-rule evaluation. A geometry-derived diameter must not automatically be treated as a nominal diameter.

