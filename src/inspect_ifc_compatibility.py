"""
inspect_ifc_compatibility.py

ENMA-WG IFC Compatibility Inspector

Purpose:
    Inspect IFC files without generating geometry and compare
    their basic architectural / MEP / connectivity structures.

Usage examples:

    # Single IFC file
    python .\src\inspect_ifc_compatibility.py `
        ".\data\Ifc4_Revit_MEP.ifc"

    # All IFC files in a directory
    python .\src\inspect_ifc_compatibility.py `
        ".\data" `
        --all

    # Specify output CSV
    python .\src\inspect_ifc_compatibility.py `
        ".\data" `
        --all `
        --output ".\output\ifc_compatibility_inventory.csv"
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Optional

import ifcopenshell


# ----------------------------------------------------------------------
# Entities inspected by ENMA pre-flight
# ----------------------------------------------------------------------

ENTITY_GROUPS = {
    "Spatial": [
        "IfcProject",
        "IfcSite",
        "IfcBuilding",
        "IfcBuildingStorey",
        "IfcSpace",
    ],

    "Architecture": [
        "IfcWall",
        "IfcWallStandardCase",
        "IfcSlab",
        "IfcRoof",
        "IfcDoor",
        "IfcWindow",
        "IfcCovering",
        "IfcOpeningElement",
    ],

    "Pipe": [
        "IfcPipeSegment",
        "IfcPipeFitting",
        "IfcValve",
        "IfcPump",
        "IfcTank",
        "IfcWasteTerminal",
        "IfcFireSuppressionTerminal",
    ],

    "Duct": [
        "IfcDuctSegment",
        "IfcDuctFitting",
        "IfcDamper",
        "IfcFan",
        "IfcAirTerminal",
        "IfcAirTerminalBox",
        "IfcUnitaryEquipment",
        "IfcAirToAirHeatRecovery",
        "IfcChiller",
    ],

    "Electrical": [
        "IfcCableCarrierSegment",
        "IfcCableCarrierFitting",
        "IfcLightFixture",
        "IfcElectricDistributionBoard",
    ],

    "Connectivity": [
        "IfcDistributionPort",
        "IfcRelConnectsPorts",
        "IfcRelConnectsPortToElement",
        "IfcRelConnectsElements",
        "IfcRelNests",
        "IfcRelAggregates",
    ],

    "Properties": [
        "IfcPropertySet",
        "IfcElementQuantity",
        "IfcRelDefinesByProperties",
    ],

    "ClassificationMaterial": [
        "IfcClassification",
        "IfcClassificationReference",
        "IfcRelAssociatesClassification",
        "IfcMaterial",
        "IfcRelAssociatesMaterial",
    ],
}


# ----------------------------------------------------------------------
# Safe IFC access
# ----------------------------------------------------------------------

def safe_by_type(model, entity_name: str):
    """
    Safely call model.by_type().

    Returns:
        (entities, status)

    status:
        OK
        NOT_IN_SCHEMA
        ERROR
    """

    try:
        entities = model.by_type(entity_name)
        return entities, "OK"

    except RuntimeError:
        # Typical IfcOpenShell behaviour when an entity
        # does not exist in the current IFC schema.
        return None, "NOT_IN_SCHEMA"

    except Exception:
        return None, "ERROR"


def safe_count(model, entity_name: str):
    entities, status = safe_by_type(model, entity_name)

    if entities is None:
        return None, status

    return len(entities), status


# ----------------------------------------------------------------------
# Header / application
# ----------------------------------------------------------------------

def get_application_info(model):
    apps, status = safe_by_type(model, "IfcApplication")

    if status != "OK" or not apps:
        return "", "", ""

    app = apps[0]

    name = getattr(app, "ApplicationFullName", None) or ""
    identifier = getattr(app, "ApplicationIdentifier", None) or ""
    version = getattr(app, "Version", None) or ""

    return str(name), str(identifier), str(version)


def get_header_description(model):
    try:
        desc = model.header.file_description.description
        return " | ".join(str(x) for x in desc)
    except Exception:
        try:
            return str(model.header.file_description)
        except Exception:
            return ""


def get_preprocessor_version(model):
    try:
        value = model.header.file_name.preprocessor_version
        return str(value or "")
    except Exception:
        return ""


def get_originating_system(model):
    try:
        value = model.header.file_name.originating_system
        return str(value or "")
    except Exception:
        return ""


# ----------------------------------------------------------------------
# Model classification
# ----------------------------------------------------------------------

def count_value(counts, entity_name):
    value = counts.get(entity_name)

    if value is None:
        return 0

    return value


def classify_model(counts):
    """
    Very conservative preliminary classification.

    This is NOT an engineering conclusion.
    It only classifies the IFC according to entity presence.
    """

    architecture_count = sum(
        count_value(counts, name)
        for name in [
            "IfcWall",
            "IfcWallStandardCase",
            "IfcSlab",
            "IfcRoof",
            "IfcDoor",
            "IfcWindow",
            "IfcCovering",
        ]
    )

    mep_count = sum(
        count_value(counts, name)
        for name in [
            "IfcPipeSegment",
            "IfcPipeFitting",
            "IfcValve",
            "IfcPump",
            "IfcTank",
            "IfcWasteTerminal",
            "IfcFireSuppressionTerminal",
            "IfcDuctSegment",
            "IfcDuctFitting",
            "IfcDamper",
            "IfcFan",
            "IfcAirTerminal",
            "IfcAirTerminalBox",
            "IfcUnitaryEquipment",
            "IfcAirToAirHeatRecovery",
            "IfcChiller",
            "IfcCableCarrierSegment",
            "IfcCableCarrierFitting",
            "IfcLightFixture",
            "IfcElectricDistributionBoard",
        ]
    )

    if architecture_count > 0 and mep_count > 0:
        return "MIXED"

    if mep_count > 0:
        return "MEP"

    if architecture_count > 0:
        return "ARCHITECTURE"

    return "UNKNOWN"


# ----------------------------------------------------------------------
# IFC inspection
# ----------------------------------------------------------------------

def inspect_ifc(ifc_path: Path):

    print()
    print("=" * 78)
    print(f"Inspecting : {ifc_path.name}")
    print("=" * 78)

    file_size_mb = ifc_path.stat().st_size / (1024 * 1024)

    try:
        model = ifcopenshell.open(str(ifc_path))

    except Exception as e:
        print(f"[ERROR] Cannot open IFC: {e}")

        return {
            "file": ifc_path,
            "file_size_mb": file_size_mb,
            "schema": "",
            "application": "",
            "application_identifier": "",
            "application_version": "",
            "header_description": "",
            "preprocessor_version": "",
            "originating_system": "",
            "model_type": "OPEN_ERROR",
            "counts": {},
            "statuses": {},
        }

    schema = model.schema

    application, app_id, app_version = get_application_info(model)

    header_description = get_header_description(model)
    preprocessor_version = get_preprocessor_version(model)
    originating_system = get_originating_system(model)

    counts = {}
    statuses = {}

    for group_name, entity_names in ENTITY_GROUPS.items():

        for entity_name in entity_names:

            count, status = safe_count(model, entity_name)

            counts[entity_name] = count
            statuses[entity_name] = status

    model_type = classify_model(counts)

    print(f"Schema      : {schema}")
    print(f"Application : {application}")
    print(f"Version     : {app_version}")
    print(f"Model type  : {model_type}")
    print(f"File size   : {file_size_mb:.2f} MB")

    print()

    for group_name, entity_names in ENTITY_GROUPS.items():

        print(f"[{group_name}]")

        for entity_name in entity_names:

            count = counts[entity_name]
            status = statuses[entity_name]

            if status == "OK":
                print(f"  {entity_name:<35} {count:>8}")

            else:
                print(
                    f"  {entity_name:<35} "
                    f"{'-':>8}  {status}"
                )

        print()

    return {
        "file": ifc_path,
        "file_size_mb": file_size_mb,
        "schema": schema,
        "application": application,
        "application_identifier": app_id,
        "application_version": app_version,
        "header_description": header_description,
        "preprocessor_version": preprocessor_version,
        "originating_system": originating_system,
        "model_type": model_type,
        "counts": counts,
        "statuses": statuses,
    }


# ----------------------------------------------------------------------
# CSV output
# ----------------------------------------------------------------------

def write_csv(results, output_path: Path):

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "FileName",
        "FileSizeMB",
        "Schema",
        "Application",
        "ApplicationIdentifier",
        "ApplicationVersion",
        "ModelType",
        "HeaderDescription",
        "PreprocessorVersion",
        "OriginatingSystem",
        "Group",
        "Entity",
        "Count",
        "Status",
    ]

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for result in results:

            for group_name, entity_names in ENTITY_GROUPS.items():

                for entity_name in entity_names:

                    count = result["counts"].get(entity_name)
                    status = result["statuses"].get(
                        entity_name,
                        "ERROR",
                    )

                    writer.writerow({
                        "FileName":
                            result["file"].name,

                        "FileSizeMB":
                            f"{result['file_size_mb']:.2f}",

                        "Schema":
                            result["schema"],

                        "Application":
                            result["application"],

                        "ApplicationIdentifier":
                            result["application_identifier"],

                        "ApplicationVersion":
                            result["application_version"],

                        "ModelType":
                            result["model_type"],

                        "HeaderDescription":
                            result["header_description"],

                        "PreprocessorVersion":
                            result["preprocessor_version"],

                        "OriginatingSystem":
                            result["originating_system"],

                        "Group":
                            group_name,

                        "Entity":
                            entity_name,

                        "Count":
                            "" if count is None else count,

                        "Status":
                            status,
                    })

    print()
    print(f"CSV written : {output_path}")


# ----------------------------------------------------------------------
# Input handling
# ----------------------------------------------------------------------

def collect_ifc_files(
    input_path: Path,
    all_files: bool,
):

    if input_path.is_file():

        if input_path.suffix.lower() != ".ifc":
            raise ValueError(
                f"Not an IFC file: {input_path}"
            )

        return [input_path]

    if input_path.is_dir():

        if not all_files:
            raise ValueError(
                "Directory specified. "
                "Use --all to inspect all IFC files."
            )

        files = sorted(
            input_path.glob("*.ifc"),
            key=lambda p: p.name.lower(),
        )

        if not files:
            raise FileNotFoundError(
                f"No IFC files found: {input_path}"
            )

        return files

    raise FileNotFoundError(
        f"Input path not found: {input_path}"
    )


# ----------------------------------------------------------------------
# Command line
# ----------------------------------------------------------------------

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Inspect IFC schema compatibility and "
            "basic architecture / MEP structure."
        )
    )

    parser.add_argument(
        "input",
        type=Path,
        help="IFC file or directory",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Inspect all *.ifc files in directory",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "output/ifc_compatibility_inventory.csv"
        ),
        help="Output CSV path",
    )

    return parser.parse_args()


def main():

    args = parse_args()

    try:
        ifc_files = collect_ifc_files(
            args.input,
            args.all,
        )

    except Exception as e:
        print(
            f"[ERROR] {type(e).__name__}: {e}"
        )
        raise SystemExit(1)

    print("=" * 78)
    print("ENMA-WG IFC Compatibility Inspector")
    print("=" * 78)

    print(f"IFC files : {len(ifc_files)}")

    results = []

    for ifc_path in ifc_files:

        result = inspect_ifc(ifc_path)
        results.append(result)

    write_csv(
        results,
        args.output,
    )

    print()
    print("=" * 78)
    print("Completed")
    print("=" * 78)


if __name__ == "__main__":
    main()