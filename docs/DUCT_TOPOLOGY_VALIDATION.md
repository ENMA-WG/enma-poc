# Duct Topology Validation

## 1. Purpose

This document describes an exploratory validation of duct-system topology using a real IFC model.

The objective is not to reconstruct a complete HVAC network automatically. Instead, the investigation asks a more fundamental question:

> What does the IFC model actually tell us about system membership, port ownership, explicit connectivity, and geometric proximity?

This distinction is important for ENMA 3.0.

A quantity takeoff workflow may only require measurable geometry. Engineering interpretation, however, requires us to distinguish observed IFC information from inferred relationships.

The validation therefore follows an evidence-oriented approach:

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

The current study uses:

- IFC: `data/営繕BIMモデル_EM.ifc`
- IfcOpenShell: 0.8.5
- Python: 3.11.9

The investigated air-system categories are:

- `101_SA給気`
- `102_RA還気`
- `103_OA外気`
- `105_EA排気`

---

## 2. Three Different Concepts

One of the main findings is that the following concepts must not be treated as equivalent.

### 2.1 System Membership

`IfcDistributionSystem` and `IfcRelAssignsToGroup` identify objects belonging to the same system.

This tells us:

> These objects are members of the same distribution system.

It does **not** necessarily tell us how those objects are physically connected.

### 2.2 Port Ownership

`IfcRelNests` associates an `IfcDistributionPort` with its owning element.

This tells us:

> This port belongs to this element.

Port ownership is different from connectivity between two elements.

### 2.3 Explicit Connectivity

`IfcRelConnectsPorts` explicitly connects two ports.

This is much stronger evidence:

> These two ports are explicitly represented as connected in the IFC model.

For ENMA, these three types of information must therefore be preserved separately.

```text
System Membership ≠ Port Ownership ≠ Explicit Connectivity
```

---

## 3. Whole-Model Connectivity Inventory

The model contains:

| Item | Count |
|---|---:|
| IfcDistributionPort | 5,007 |
| IfcRelConnectsPorts | 1,144 |
| Ports with identified owner | 5,007 |
| Air distribution systems investigated | 454 |

All 5,007 distribution ports could be associated with an owning element through `IfcRelNests`.

The 1,144 explicit port connections were classified by the IFC classes of their owning elements.

| Connected element classes | Connections |
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

There are 852 duct-related explicit connections:

```text
428  IfcDuctSegment ↔ IfcDuctSegment
419  IfcDuctFitting ↔ IfcDuctSegment
  5  IfcDamper ↔ IfcDuctSegment
-----------------------------------
852  duct-related explicit connections
```

A notable observation is that explicit connections to several types of HVAC equipment were not found in this inventory.

For example, no explicit `IfcRelConnectsPorts` connection was observed between ducts and:

- `IfcFan`
- `IfcAirTerminal`
- `IfcAirTerminalBox`
- `IfcAirToAirHeatRecovery`

This does not mean that IFC cannot represent such connections.

It only means that they were not observed in the tested model through this workflow.

---

## 4. Connectivity by Air-System Type

The 454 investigated air systems were classified according to whether at least one explicit port connection could be mapped to the system.

| System Type | Systems | With Connections | Without Connections | Explicit Connections |
|---|---:|---:|---:|---:|
| SA | 199 | 110 | 89 | 419 |
| RA | 4 | 1 | 3 | 2 |
| OA | 53 | 24 | 29 | 93 |
| EA | 198 | 94 | 104 | 338 |
| **Total** | **454** | **229** | **225** | **852** |

Almost half of the air systems have no explicit port-to-port connection mapped to them.

This must be interpreted carefully.

A system containing only one duct segment, for example, does not necessarily require an internal `IfcRelConnectsPorts` relationship.

Therefore:

> No explicit connection does not automatically mean invalid system data.

The number and type of system members must also be considered.

---

## 5. EA 18 Case Study

A small exhaust-air system was selected for detailed investigation:

```text
System Name : EA 18
ObjectType  : 105_EA排気
PredefinedType : EXHAUST
```

Its system members include:

- 1 `IfcDuctSegment`
- 1 `IfcAirTerminal`
- 1 `IfcFan`
- 5 formal `IfcDistributionPort`

The elements themselves contain six nested ports because the fan has one additional nested port that is not a formal member of the system.

### Elements

```text
IfcDuctSegment
  丸型ダクト:00_丸タップ:40699213

IfcAirTerminal
  041_ユニバーサル形吸込口:HS:40845462

IfcFan
  11030_FAN_消音ボックス付送風機:#1_150m3/h:40873974
```

### Formal System Ports

The system contains five formal ports.

The fan contains three nested ports:

```text
Port_40873974_8       SOURCEANDSINK
OutPort_40873974_9    SOURCE
InPort_40873974_10    SINK
```

Only the latter two are formal members of `EA 18`.

This difference is retained as observed IFC evidence rather than being silently corrected.

---

## 6. Explicit Connectivity of EA 18

The complete IFC model contains 1,144 `IfcRelConnectsPorts` relationships.

However, no explicit connectivity relationship was found for the ports or elements belonging to `EA 18`.

For `EA 18`:

| Relationship | Count |
|---|---:|
| IfcRelConnectsPorts | 0 |
| IfcRelConnectsPortToElement | 0 |
| IfcRelConnectsElements | 0 |
| IfcRelConnectsPathElements | 0 |
| IfcRelNests | 3 |
| IfcRelAssignsToGroup | 1 |

Therefore the tested IFC explicitly provides:

```text
System membership : YES
Port ownership     : YES
Port direction     : YES
Port-to-port link  : NO
```

At this point, it would be incorrect to automatically infer that the fan, duct, and air terminal are physically connected simply because they belong to the same system.

---

## 7. Port Geometry of EA 18

The next test examined the world coordinates of all six nested ports.

The IFC project length unit is millimetres.

The two ports of the duct segment are located 3,800 mm apart, consistent with the geometric extent represented by the duct segment.

More importantly, cross-element port distances were calculated.

Selected nearest distances were:

| Port Owners | Minimum Observed Distance |
|---|---:|
| AirTerminal ↔ Fan | 636.416 mm |
| DuctSegment ↔ Fan | 957.164 mm |
| DuctSegment ↔ AirTerminal | 1,696.478 mm |

The nearest cross-element port pair is therefore still more than 600 mm apart.

This result does **not** support the simple hypothesis:

> The explicit relationship is missing, but the corresponding ports occupy the same geometric position.

For `EA 18`, they do not.

Possible explanations include:

- unmodelled intermediate components,
- incomplete physical network representation,
- differences between system grouping and physical topology,
- export characteristics of the authoring application,
- other modelling conventions not yet investigated.

The current evidence does not determine which explanation is correct.

---

## 8. Validation Against Explicit Connections

To understand whether geometric proximity could be useful as supporting evidence, all 1,144 explicit `IfcRelConnectsPorts` relationships were examined.

For each explicitly connected port pair, the 3D distance between the port placement origins was calculated.

### Distance Distribution

| Port Distance | Connections |
|---|---:|
| Virtually zero | 1,114 |
| >0 to 1 mm | 1 |
| >1 to 10 mm | 0 |
| >10 to 50 mm | 0 |
| >50 to 100 mm | 22 |
| >100 to 500 mm | 6 |
| >500 mm | 1 |
| **Total** | **1,144** |

Statistics:

```text
Minimum :    0.000 mm
Median  :    0.000 mm
Average :    3.663 mm
Maximum : 1140.000 mm
```

1,114 of the 1,144 explicit connections — approximately 97.4% — have virtually coincident port origins.

This is strong evidence that geometric coincidence is a common characteristic of explicit connectivity in this model.

However, it is not universal.

---

## 9. Explicit Connections with Non-Zero Distances

Several explicitly connected duct ports have non-zero geometric distances.

Examples include:

```text
100 mm
125 mm
150 mm
200 mm
1140 mm
```

The largest observed value was:

```text
IfcDuctSegment ↔ IfcDuctSegment
Port distance = 1140 mm
```

Despite this distance, the IFC explicitly states the connectivity through `IfcRelConnectsPorts`.

Therefore:

> Geometric distance must not override explicit IFC connectivity.

Likewise:

> Non-coincident port origins do not prove that two elements are disconnected.

The reason for these outliers has not yet been investigated.

They may reflect modelling or export conventions, element geometry, port placement definitions, or other factors.

---

## 10. Evidence Priority

Based on the current experiment, ENMA should distinguish evidence strength.

### Level 1 — Explicit IFC Connectivity

```text
IfcRelConnectsPorts
```

This is direct IFC evidence.

ENMA should preserve it as:

```text
IFC_OBSERVED
```

### Level 2 — System and Port Relationships

```text
IfcDistributionSystem
IfcRelAssignsToGroup
IfcRelNests
IfcDistributionPort.FlowDirection
```

These provide valuable semantic and ownership information but do not independently prove physical adjacency.

They should also be preserved as:

```text
IFC_OBSERVED
```

### Level 3 — Geometric Proximity

Port coordinates and distances are geometric observations.

For example:

```text
distance(port_A, port_B) ≈ 0
```

is:

```text
GEOMETRY_OBSERVED
```

It may support a connectivity hypothesis, but it is not itself an explicit IFC connection.

### Level 4 — Connectivity Inference

Where explicit connectivity is absent, ENMA may eventually generate a candidate such as:

```text
CONNECTION_CANDIDATE
```

based on multiple pieces of evidence.

Possible evidence could include:

- same distribution system,
- compatible port direction,
- compatible element classes,
- compatible dimensions,
- geometric proximity,
- orientation,
- continuity of the network.

This belongs to:

```text
INFERENCE
```

not `IFC_OBSERVED`.

### Level 5 — Human Review

Ambiguous inferred connectivity should be presented for engineering review.

```text
INFERENCE
        ↓
HUMAN REVIEW
        ↓
ACCEPT / REJECT / MODIFY
```

This preserves the distinction between machine-readable evidence and engineering judgement.

---

## 11. Proposed ENMA Connectivity Logic

A conservative future workflow could be:

```text
Is IfcRelConnectsPorts present?
        |
        +-- YES
        |     |
        |     +--> CONNECTED
        |          Evidence = IFC_OBSERVED
        |
        +-- NO
              |
              +--> Examine system membership
              |
              +--> Examine port ownership
              |
              +--> Examine FlowDirection
              |
              +--> Examine geometry
              |
              +--> Examine size / orientation
              |
              +--> Generate candidate
                        |
                        v
                    INFERENCE
                        |
                        v
                   HUMAN REVIEW
```

Importantly, geometric proximity should not be used as a single automatic rule.

The current model demonstrates both directions of the problem:

1. ports can be explicitly connected even when their placement origins are not coincident;
2. membership in the same system does not prove physical adjacency.

---

## 12. Implications for Engineering Information

The experiment reinforces a broader ENMA principle:

> Measurement, semantics, topology, and engineering decisions are different layers of information.

For quantity takeoff, geometry may be sufficient to measure a duct.

For engineering interpretation, ENMA must also ask:

- What system does it belong to?
- Which ports belong to the element?
- Which connections are explicitly represented?
- Which relationships are only inferred?
- What evidence supports the inference?
- Has an engineer reviewed the result?

This leads to an evidence chain such as:

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

## 13. What This Validation Does Not Prove

This experiment is intentionally limited.

It does not prove that:

- all IFC models behave in the same way;
- all Revit IFC exports behave in the same way;
- port coincidence is a universal connectivity rule;
- missing `IfcRelConnectsPorts` means disconnected;
- non-zero port distance means disconnected;
- the complete HVAC network can already be reconstructed automatically.

The results describe the tested IFC model and the current extraction workflow.

Further validation with additional models and authoring/export environments is required.

---

## 14. Reproducibility

The following scripts are included in this repository for reproducing the topology validation described in this document:

```text
src/analyze_ifc_port_connections.py
src/inspect_ifc_connectivity_relationships.py
src/trace_duct_system_topology.py
src/inspect_duct_port_geometry.py
src/analyze_connected_port_distances.py
```

Representative outputs generated by these scripts include:

```text
output/ifc_port_connections.csv
output/duct_system_connection_summary.csv
output/duct_port_geometry_EA18.csv
output/duct_port_distances_EA18.csv
output/connected_port_distances.csv
```

These files are exploratory validation artifacts. Their purpose is to make the reasoning process inspectable rather than to present a production-ready network reconstruction algorithm.

---

## 15. Key Finding

The central result of this validation is:

```text
System Membership
        ≠
Physical Topology
        ≠
Geometric Proximity
```

At the same time, these information layers can complement one another when their provenance is preserved.

For ENMA 3.0, the goal is therefore not to silently convert incomplete IFC information into assumed engineering truth.

The goal is to build a traceable process:

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

That distinction is essential when moving from automated quantity measurement toward engineering information.