from __future__ import annotations

from typing import Any

from ..ai.chat_provider import ToolDefinition
from .viewer_bridge import ViewerBridge

SELECT_BY_CLASS = ToolDefinition(
    name="select_by_ifc_class",
    description="Select and highlight every element of a given IFC class, e.g. IfcPipeSegment.",
    parameters={
        "type": "object",
        "properties": {"ifc_class": {"type": "string"}},
        "required": ["ifc_class"],
    },
)

HIGHLIGHT_ELEMENT = ToolDefinition(
    name="highlight_element",
    description="Highlight a single element by its IFC GlobalId.",
    parameters={
        "type": "object",
        "properties": {"global_id": {"type": "string"}},
        "required": ["global_id"],
    },
)

TOOL_DEFINITIONS = [SELECT_BY_CLASS, HIGHLIGHT_ELEMENT]


class ViewerToolExecutor:
    """Runs chat-requested tools against the viewer via ``ViewerBridge``.

    This executor is called from the FastAPI request thread; it never
    touches ``IfcViewerWidget`` directly, only the bridge's signals, which
    Qt delivers to the GUI thread. See ``ViewerBridge`` for why.
    """

    def __init__(self, bridge: ViewerBridge):
        self._bridge = bridge

    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "select_by_ifc_class":
            ifc_class = arguments["ifc_class"]
            self._bridge.select_by_class_requested.emit(ifc_class)
            return {"status": "ok", "ifc_class": ifc_class}
        if name == "highlight_element":
            global_id = arguments["global_id"]
            self._bridge.highlight_requested.emit(global_id)
            return {"status": "ok", "global_id": global_id}

        raise ValueError(f"Unknown tool: {name}")
