# EA18 Duct Connectivity Evidence

This directory preserves evidence used to investigate duct connectivity for the EA18 system.

The purpose of this dataset is to distinguish between:

1. explicit connectivity represented in IFC;
2. connectivity that may be inferred from port geometry;
3. engineering inference that requires additional rules or domain knowledge;
4. cases that should remain subject to human review.

This evidence supports the research issue:

**Investigate inferred duct connectivity when IfcRelConnectsPorts is missing**

## Files

### `duct_port_geometry_EA18.csv`

Inventory of distribution ports associated with the EA18 investigation.

It includes information such as:

- port STEP ID and GlobalId;
- port name;
- FlowDirection;
- formal system membership;
- parent MEP element information;
- port geometry and coordinates where available.

### `duct_port_distances_EA18.csv`

Candidate geometric relationships between ports.

This file is used to investigate whether spatial proximity and port direction can provide evidence for connectivity when an explicit IFC connection is unavailable.

A short distance alone must not be treated as proof of engineering connectivity.

### `ifc_connectivity_relationships_EA18.csv`

IFC relationships discovered around the EA18 elements and ports.

The file records explicit IFC relationships such as nesting and system/group assignment and helps distinguish IFC facts from later ENMA inference.

### `duct_system_topology_EA18.csv`

Result of extracting explicit duct-system topology for EA18.

At the time of this investigation, the file contains the CSV header but **zero topology rows**.

This is intentional research evidence, not a broken or incomplete CSV file.

It records that the investigated IFC relationships did not produce an explicit EA18 topology through the current extraction method, even though relevant ports, parent elements, and system information were present.

## Interpretation

These files should be considered evidence rather than a final engineering conclusion.

ENMA should keep the following stages separate:

**IFC fact → geometric evidence → engineering inference → human review**

The absence of an explicit IFC connection must not automatically be interpreted as either a confirmed connection or a confirmed disconnection.

## Status

Research evidence captured during the ENMA-WG PoC.

Further investigation should determine when geometric and engineering evidence is sufficient to propose an inferred connection and when the case should be escalated for human review.
