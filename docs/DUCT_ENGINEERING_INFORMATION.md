# Duct Engineering Information Validation

## Overview

This document summarizes the ENMA-WG PoC investigation into the engineering information required to move from reproducible IFC duct quantity takeoff toward specification selection.

The current experiment uses the Japanese MLIT BIM sample model used by the ENMA-WG PoC:

```text
data/営繕BIMモデル_EM.ifc
```

The purpose is not to claim a general limitation of IFC. It is to document what was and was not confirmed in the current test IFC, and to keep IFC-observed information separate from engineering interpretation.

## Starting Point: Reproducible Duct Quantity

The preceding duct PoC established the following results for the current test IFC:

- `IfcDuctSegment`: 1,077
- ROUND: 792
- RECTANGULAR: 285
- UNKNOWN: 0
- Geometry total length: 1,088.945 m
- QTO total length: 1,088.945 m
- all 1,077 duct segments have exactly one formal `IfcDistributionSystem` assignment
- ENMA AirType mapping: SA 512 / RA 4 / OA 112 / EA 449

The quantity summary groups the 1,077 duct segments into 234 `AirType × Shape × Size` rows while preserving geometry-derived dimensions.

This establishes a reproducible quantity baseline. The next question is whether the same IFC contains enough engineering information to select duct specifications such as sheet thickness.

## Why Sheet Thickness Was Chosen

Duct sheet thickness is a useful next-step test because it cannot be selected from length alone. Engineering rules may depend on information such as:

- duct shape
- duct construction type
- material specification
- pressure class
- rectangular long-side dimension
- round nominal diameter
- applicable standard or project specification

Some of these values can be observed directly from IFC geometry. Others may require project specifications, reference standards, inference, or human review.

## 1. Shape and Geometry Dimensions

The current PoC can obtain duct shape and dimensions from IFC geometry.

```text
IfcDuctSegment 1077
├─ ROUND        792
└─ RECTANGULAR  285
```

For rectangular ducts, width and height are derived from the local 2D profile. For round ducts, diameter is derived from the local profile geometry.

These values are treated as IFC observations.

## 2. Geometry Diameter Is Not Automatically Nominal Diameter

For ROUND ducts, the PoC obtains a geometry-derived diameter. However, the current workflow deliberately does not treat that value as an engineering nominal diameter without additional confirmation.

```text
IFC observation
    Geometry Diameter
          ↓
Engineering interpretation / confirmation
          ↓
    Nominal Diameter
```

For example, a geometry diameter of 200 mm may eventually be confirmed as nominal diameter 200 mm, but those two concepts remain separate in the ENMA data model.

This distinction becomes important when a standard specification defines a rule using nominal diameter rather than raw geometry diameter.

## 3. ROUND Does Not Establish SPIRAL Construction

`src/inspect_round_ducts.py` inspected all 792 duct segments already classified as ROUND from geometry.

Observed results:

```text
ROUND inspected      : 792

ObjectType
 789  丸型ダクト:00_丸タップ
   3  丸型ダクト:00_丸ティー

TypeName
 789  丸型ダクト:00_丸タップ
   3  丸型ダクト:00_丸ティー

ElementType
 792  (blank)

PredefinedType
 792  NOTDEFINED

Material
 792  ダクト－排気

Keyword hits
スパイラル       : 0
spiral          : 0
亜鉛             : 0
galvan          : 0
ダクト           : 792
duct            : 792
```

The inspection searches occurrence/type properties and material information for terms that could support a construction-type or material interpretation.

The current IFC therefore supports the observation that these profiles are ROUND, but the investigation did not find evidence sufficient to confirm that they are SPIRAL ducts or galvanized-steel ducts.

`Material = ダクト－排気` is preserved as an IFC value, but it is not interpreted by this PoC as a reliable engineering material specification.

## 4. Pressure Information on Duct Segments

`src/inspect_duct_pressure.py` explicitly checks `Pset_DuctSegmentTypeCommon` and searches occurrence/inherited type properties for pressure-related information.

The corrected inspection deliberately avoids a bare `pa` substring search because that can create false positives in unrelated words.

Result:

```text
IfcDuctSegment        : 1077
WorkingPressure       : 0/1077
PressureRange         : 0/1077
Any pressure property : 0/1077

WorkingPressure values
(none)

PressureRange values
(none)

All pressure-related properties
(none)
```

This does **not** mean that IFC cannot represent pressure information. It means that the pressure information required for the current duct-thickness investigation was not found on the duct segments in this test IFC.

## 5. Pressure Information on Distribution Systems

The investigation was extended beyond individual duct segments to the formally assigned `IfcDistributionSystem` objects.

The relationship path is:

```text
IfcDuctSegment
  └─ IfcRelAssignsToGroup
       └─ IfcDistributionSystem
```

`src/inspect_duct_system_properties.py` produced:

```text
IfcDuctSegment             : 1077
Used IfcDistributionSystem : 404
Duct without system        : 0
Duct with multiple systems : 0
Output rows                : 404
```

The system `ObjectType` values remain useful for air-system classification:

| System ObjectType | Duct count |
|---|---:|
| `101_SA給気` | 512 |
| `105_EA排気` | 449 |
| `103_OA外気` | 112 |
| `102_RA還気` | 4 |

System `PredefinedType` by duct count:

| PredefinedType | Duct count |
|---|---:|
| `VENTILATION` | 628 |
| `EXHAUST` | 449 |

The properties found on the 404 used systems were `Pset_DistributionSystemCommon.Reference` values corresponding to the system classification. No pressure-like property was found.

```text
Pressure-like properties
(none)
```

Therefore, the current test IFC provides useful formal system membership and SA/RA/OA/EA classification, but the investigation did not find pressure-class information on either the 1,077 duct segments or their 404 assigned distribution systems.

## Engineering Information Gap

The current findings can be summarized as follows.

| Engineering information | Current MLIT test IFC | ENMA treatment |
|---|---|---|
| Shape | Available | IFC observation |
| Rectangular width / height | Available | IFC observation |
| Geometry diameter | Available | IFC observation |
| Air system SA/RA/OA/EA | Available through formal system assignment | IFC observation + explicit ENMA mapping |
| Nominal diameter | Not confirmed as a separate engineering value | Interpretation / review required |
| Duct construction type (e.g. SPIRAL) | Not confirmed | Interpretation / review required |
| Material specification (e.g. galvanized steel) | Not confirmed for engineering use | Specification / review required |
| Pressure class | Not found | Project specification / inference / review required |
| Duct thickness | Not a raw IFC observation in this workflow | Derived by Engineering Rule after required inputs are established |

The central finding is therefore not simply that information is “missing.” The important boundary is between information observed in IFC and information required to make an engineering decision.

## ENMA Information Layers

The PoC is moving toward an explicit separation of information provenance:

```text
1. IFC_OBSERVED
   Shape
   Width / Height
   Geometry Diameter
   Length
   Distribution System

2. PROJECT_SPECIFICATION / ENGINEERING ATTRIBUTE
   Nominal Diameter
   Duct Construction Type
   Pressure Class
   Material Specification

3. STANDARD_SPECIFICATION
   Applicable source provision
   Size range
   Pressure-class rule
   Thickness rule

4. DERIVED
   Long Side
   Selected Duct Thickness
   Subsequent material / labor quantities
```

This separation is intended to prevent an inferred or assumed engineering value from being presented as if it had been directly stored in the IFC.

## Human Review and Engineering Rules

The ENMA data model supports a reviewable workflow rather than silently filling information gaps.

```text
IFC observation
      ↓
inference_results
      ↓
human_reviews
      ↓
rule_evaluations
      ↓
element_quantity_results
```

For duct thickness, the current data model includes `R40-01 duct_thickness_rules`.

A rule can use inputs such as:

- `duct_shape`
- `duct_construction_type`
- `material`
- `pressure_class`
- `size_basis`
- `size_min_mm`
- `size_max_mm`
- `thickness_mm`
- `standard_provision_id`

The `size_basis` distinction is especially important:

```text
LONG_SIDE
NOMINAL_DIAMETER
GEOMETRY_DIAMETER
```

A rule defined by a standard using nominal diameter should not silently use geometry diameter instead.

## From Quantity Takeoff to Engineering Specification

The experiment currently suggests the following workflow:

```text
IFC
 ↓
Geometry / QTO / Systems
 ↓
Reproducible Quantity
 ↓
Engineering Information Validation
 ↓
Inference / Project Specification / Human Review
 ↓
Engineering Rule Evaluation
 ↓
Specification Result
 ↓
Material / Labor / Schedule
```

This is the practical meaning of moving “beyond quantity takeoff” in the current ENMA-WG investigation.

The quantity calculation can be reproducible while still requiring additional engineering information before a specification can be selected. Making that boundary explicit is preferable to silently substituting assumptions for missing information.

## Current Scope and Caution

These findings apply to the current MLIT test IFC and the current PoC implementation.

They should **not** be interpreted as claims that:

- IFC cannot represent pressure information
- every ROUND duct is or is not SPIRAL
- every IFC model lacks nominal-size information
- the inspected material value is universally unreliable
- all projects require the same information-completion workflow

Different IFC exports, authoring tools, project requirements, IDS definitions, or modeling practices may provide additional information.

The purpose of this PoC is to preserve the distinction between observed data, engineering interpretation, and derived results so that each step remains reviewable and reproducible.

## Related Files

```text
src/extract_ducts.py
src/summarize_ducts.py
src/inspect_round_ducts.py
src/inspect_duct_pressure.py
src/inspect_duct_system_properties.py

output/ducts_detail.csv
output/ducts_summary.csv
output/round_duct_inspection.csv
output/duct_pressure_inspection.csv
output/duct_system_properties.csv

docs/DUCT_EXTRACTION.md
```

## Project

ENMA-WG  
Automated MEP Quantity Takeoff PoC

This investigation is part of the ENMA-WG research into reproducible openBIM-based MEP quantity takeoff and the engineering workflows that follow it.
