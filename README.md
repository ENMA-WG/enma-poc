# ENMA-WG PoC

**openBIM | MEP | Quantity Takeoff**

ENMA-WG is exploring practical openBIM workflows for building services
engineering, with a focus on automated MEP quantity takeoff.

This repository contains the proof-of-concept implementation for:

**Revisiting the Promise of Automated MEP Quantity Takeoff**

Presented at buildingSMART International Summit Tokyo 2026.

## Objectives

This PoC explores how IFC, IDS, bSDD and lightweight software tools can
support practical MEP quantity takeoff workflows.

The project focuses on:

- IFC geometry and property extraction
- MEP equipment, duct and pipe identification
- Quantity takeoff
- IFC data quality checking
- IDS-based information requirements
- bSDD-based semantic enrichment
- Reproducible openBIM workflows

## Repository Structure

- src/ : PoC source code
- 	ests/ : tests
- data/ : sample data information and data source notes
- output/ : generated CSV and PoC output examples
- docs/ : architecture and methodology
- presentation/ : presentation materials

## Sample BIM Data

The PoC uses the Government Building BIM Model (Revit version)
published by the Ministry of Land, Infrastructure, Transport and Tourism
(MLIT), Japan.

The original Autodesk Revit 2022 model is converted to IFC and processed
by ENMA-WG for research and demonstration purposes.

The original BIM data is not distributed in this repository.

## License

Source code developed by ENMA-WG in this repository is provided under
the MIT License.

Third-party BIM data, documents and other materials are subject to their
respective licenses and terms of use.
