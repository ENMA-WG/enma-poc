"""
inspect_ifc_application.py

ENMA-WG IFC Application Inspector

Usage:
    python .\src\inspect_ifc_application.py ".\data\sample.ifc"

Purpose:
    Inspect the basic provenance of an IFC file:
    - IFC schema
    - IfcApplication
    - IfcOrganization
    - IFC header
    - OwnerHistory application usage

This script does NOT generate geometry.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from collections import Counter

import ifcopenshell


def safe_value(obj, attr, default=""):
    try:
        value = getattr(obj, attr, None)
        if value is None:
            return default
        return str(value)
    except Exception:
        return default


def application_name(app):
    if app is None:
        return "(None)"

    full_name = safe_value(app, "ApplicationFullName")
    identifier = safe_value(app, "ApplicationIdentifier")
    version = safe_value(app, "Version")

    parts = []

    if full_name:
        parts.append(full_name)

    if version:
        parts.append(f"Version={version}")

    if identifier:
        parts.append(f"ID={identifier}")

    return " / ".join(parts) if parts else f"#{app.id()}"


def print_header(model):
    print()
    print("=" * 78)
    print("IFC Header")
    print("=" * 78)

    try:
        print()
        print("FILE_DESCRIPTION")
        print(model.header.file_description)
    except Exception as e:
        print(f"[WARN] FILE_DESCRIPTION : {e}")

    try:
        print()
        print("FILE_NAME")
        print(model.header.file_name)
    except Exception as e:
        print(f"[WARN] FILE_NAME : {e}")

    try:
        print()
        print("FILE_SCHEMA")
        print(model.header.file_schema)
    except Exception as e:
        print(f"[WARN] FILE_SCHEMA : {e}")


def inspect_applications(model):
    applications = model.by_type("IfcApplication")

    print()
    print("=" * 78)
    print(f"IfcApplication : {len(applications)}")
    print("=" * 78)

    if not applications:
        print("(none)")
        return

    for i, app in enumerate(applications, start=1):

        developer = getattr(app, "ApplicationDeveloper", None)

        print()
        print(f"[Application {i}]")
        print(f"STEP id               : #{app.id()}")
        print(
            f"ApplicationFullName    : "
            f"{safe_value(app, 'ApplicationFullName')}"
        )
        print(
            f"ApplicationIdentifier  : "
            f"{safe_value(app, 'ApplicationIdentifier')}"
        )
        print(
            f"Version                : "
            f"{safe_value(app, 'Version')}"
        )

        if developer is not None:
            print(
                f"Developer              : "
                f"{safe_value(developer, 'Name')}"
            )
            print(
                f"DeveloperDescription   : "
                f"{safe_value(developer, 'Description')}"
            )
        else:
            print("Developer              :")


def inspect_organizations(model):
    organizations = model.by_type("IfcOrganization")

    print()
    print("=" * 78)
    print(f"IfcOrganization : {len(organizations)}")
    print("=" * 78)

    if not organizations:
        print("(none)")
        return

    for i, org in enumerate(organizations, start=1):

        print()
        print(f"[Organization {i}]")
        print(f"STEP id        : #{org.id()}")
        print(
            f"Identification : "
            f"{safe_value(org, 'Identification')}"
        )
        print(
            f"Name           : "
            f"{safe_value(org, 'Name')}"
        )
        print(
            f"Description    : "
            f"{safe_value(org, 'Description')}"
        )


def inspect_owner_history(model):
    """
    Check which applications are actually referenced by IfcOwnerHistory.

    This is useful when multiple IfcApplication records exist.
    """

    histories = model.by_type("IfcOwnerHistory")

    owning_apps = Counter()
    modifying_apps = Counter()

    for history in histories:

        owning = getattr(history, "OwningApplication", None)

        if owning is not None:
            owning_apps[application_name(owning)] += 1

        modifying = getattr(
            history,
            "LastModifyingApplication",
            None,
        )

        if modifying is not None:
            modifying_apps[application_name(modifying)] += 1

    print()
    print("=" * 78)
    print(f"IfcOwnerHistory : {len(histories)}")
    print("=" * 78)

    print()
    print("OwningApplication")
    print("-" * 78)

    if owning_apps:
        for name, count in owning_apps.most_common():
            print(f"{count:8d}  {name}")
    else:
        print("(none)")

    print()
    print("LastModifyingApplication")
    print("-" * 78)

    if modifying_apps:
        for name, count in modifying_apps.most_common():
            print(f"{count:8d}  {name}")
    else:
        print("(none)")


def inspect_ifc(ifc_path: Path):

    if not ifc_path.exists():
        raise FileNotFoundError(
            f"IFC file not found: {ifc_path}"
        )

    file_size_mb = ifc_path.stat().st_size / (1024 * 1024)

    print("=" * 78)
    print("ENMA-WG IFC Application Inspector")
    print("=" * 78)

    print(f"IFC       : {ifc_path.resolve()}")
    print(f"File size : {file_size_mb:.2f} MB")

    print()
    print("Opening IFC...")

    model = ifcopenshell.open(str(ifc_path))

    print(f"Schema    : {model.schema}")

    inspect_applications(model)
    inspect_organizations(model)
    inspect_owner_history(model)
    print_header(model)

    print()
    print("=" * 78)
    print("Done.")
    print("=" * 78)


def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Inspect IFC schema, application, organization "
            "and provenance information."
        )
    )

    parser.add_argument(
        "ifc_file",
        type=Path,
        help="Path to IFC file",
    )

    return parser.parse_args()


def main():

    args = parse_args()

    try:
        inspect_ifc(args.ifc_file)

    except Exception as e:
        print()
        print(f"[ERROR] {type(e).__name__}: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()