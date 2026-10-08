from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class ViewerBridge(QObject):
    """Marshals tool-call requests from the FastAPI thread onto the GUI thread.

    ``start_local_server`` runs uvicorn on a background thread, but
    ``IfcViewerWidget`` is a Qt widget that may only be touched from the
    thread it lives on. This QObject lives on the GUI thread; emitting one
    of its signals from any other thread is automatically queued by Qt and
    delivered there, which is the standard cross-thread signal/slot pattern.
    """

    highlight_requested = Signal(str)
    select_by_class_requested = Signal(str)
