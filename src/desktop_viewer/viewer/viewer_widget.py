import numpy as np
import pyvista as pv
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget
from pyvistaqt import QtInteractor

from ..ui.theme import DEFAULT_THEME, get_theme
from .ifc_geometry import ElementMesh


class IfcViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.plotter = QtInteractor(self)
        # QtInteractor is a QOpenGLWidget, which Qt normally draws into the
        # top-level window's shared backing store. A QWebEngineView anywhere
        # in the same top-level window switches that backing store to the
        # D3D11 RHI path, and OpenGL widgets composited through it are never
        # initialised at all - initializeGL/paintGL simply never fire, the
        # widget has no GL context, and the viewport stays black forever.
        # Giving the interactor its own native window takes it out of that
        # shared backing store, so VTK and Chromium each render on their own
        # surface. Must be set before the widget is first shown.
        self.plotter.interactor.setAttribute(Qt.WA_NativeWindow, True)
        self._actors: dict[str, list] = {}
        self._theme_name = DEFAULT_THEME
        self.set_theme(self._theme_name)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plotter.interactor)

    @property
    def theme_name(self) -> str:
        return self._theme_name

    def set_theme(self, name: str) -> None:
        self._theme_name = name
        self.plotter.set_background(get_theme(name).viewer_background)
        self.plotter.render()

    def clear(self) -> None:
        self.plotter.clear()
        self._actors.clear()
        # ``clear`` resets renderer state, so restore the chosen background.
        self.set_theme(self._theme_name)

    def add_mesh(self, mesh: ElementMesh) -> None:
        global_id = mesh.element.GlobalId
        actors = []

        for index, styled_mesh in enumerate(mesh.styled_meshes):
            points = np.array(styled_mesh.vertices)
            faces = np.hstack([[3, *triangle] for triangle in styled_mesh.faces])
            poly = pv.PolyData(points, faces)

            actor = self.plotter.add_mesh(
                poly,
                color=styled_mesh.color,
                opacity=styled_mesh.opacity,
                name=f"{global_id}-{index}",
            )
            actors.append(actor)

        self._actors[global_id] = actors

    def highlight(self, global_id: str, color: str = "red") -> None:
        actors = self._actors.get(global_id)
        if not actors:
            raise KeyError(f"No mesh loaded for GlobalId {global_id}")

        for actor in actors:
            actor.prop.color = color

    def reset_camera(self) -> None:
        self.plotter.reset_camera()
        self.plotter.render()

    def add_debug_box(self) -> None:
        """Add a fixed 3m x 4m x 5m red box, to check the render pipeline
        works independently of any IFC content."""
        box = pv.Box(bounds=(-1.5, 1.5, -2.0, 2.0, -2.5, 2.5))
        self.plotter.add_mesh(box, color="red", name="debug-box")
        self.plotter.reset_camera()
        self.plotter.render()
