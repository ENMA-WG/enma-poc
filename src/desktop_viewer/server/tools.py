from __future__ import annotations

from typing import Any

from ..ai.chat_provider import ToolDefinition
from ..viewer.viewer_widget import IfcViewerWidget

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
    def __init__(self, viewer: IfcViewerWidget):
        self._viewer = viewer

    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "select_by_ifc_class":
            raise NotImplementedError
        if name == "highlight_element":
            self._viewer.highlight(arguments["global_id"])
            return {"status": "ok"}

        raise ValueError(f"Unknown tool: {name}")
