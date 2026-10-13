from pathlib import Path

import ifcopenshell


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IFC_PATH = PROJECT_ROOT / "data" / "営繕BIMモデル_EM.ifc"


def load_model():
    assert IFC_PATH.exists(), f"IFC test file not found: {IFC_PATH}"
    return ifcopenshell.open(str(IFC_PATH))


def test_ifcopenshell_version():
    """Record the IfcOpenShell version used for the baseline."""
    assert ifcopenshell.version == "0.8.5"


def test_ifc_file_can_be_opened():
    """The reference IFC model must be readable."""
    model = load_model()
    assert model is not None


def test_pipe_inventory():
    """Known pipe element counts must remain unchanged."""
    model = load_model()

    assert len(model.by_type("IfcPipeSegment")) == 252
    assert len(model.by_type("IfcPipeFitting")) == 81


def test_duct_inventory():
    """Known duct element counts must remain unchanged."""
    model = load_model()

    assert len(model.by_type("IfcDuctSegment")) == 1077
    assert len(model.by_type("IfcDuctFitting")) == 217
    assert len(model.by_type("IfcAirTerminal")) == 272
    assert len(model.by_type("IfcFan")) == 40
    assert len(model.by_type("IfcDamper")) == 5


def test_connectivity_inventory():
    """Known IFC connectivity relationship count must remain unchanged."""
    model = load_model()

    assert len(model.by_type("IfcRelConnectsPorts")) == 1144
