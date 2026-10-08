from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Callable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("desktop_viewer")

logger.info("Importing Qt...")
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QAction, QActionGroup, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QSplashScreen,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

logger.info("Qt imported.")

logger.info(
    "Importing viewer/geometry modules "
    "(pyvista/pyvistaqt import can take several seconds on first run)..."
)
from .i18n import get_language, t
from .i18n import set_language as set_ui_language
from .server.api_server import set_tool_executor, start_local_server
from .server.tools import ViewerToolExecutor
from .server.viewer_bridge import ViewerBridge
from .ui.ai_settings_dialog import AiSettingsDialog
from .ui.chat_panel import ChatPanel
from .viewer.ifc_geometry import iter_all_product_meshes, load_model
from .viewer.viewer_widget import IfcViewerWidget

logger.info("Viewer modules imported.")


class QtLogHandler(logging.Handler):
    """Forwards log records to a Qt signal so they can be shown in-window."""

    def __init__(self, emitter: "_LogEmitter"):
        super().__init__()
        self._emitter = emitter

    def emit(self, record: logging.LogRecord) -> None:
        self._emitter.log_emitted.emit(self.format(record))


class _LogEmitter(QWidget):
    log_emitted = Signal(str)

    def __init__(self):
        super().__init__()
        self.hide()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ENMA IFC Desktop Viewer")

        self._log_emitter = _LogEmitter()
        self.log_panel = QPlainTextEdit(self)
        self.log_panel.setReadOnly(True)
        self.log_panel.setMaximumBlockCount(2000)
        self._log_emitter.log_emitted.connect(self.log_panel.appendPlainText)

        log_handler = QtLogHandler(self._log_emitter)
        log_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
        )
        logging.getLogger().addHandler(log_handler)

        logger.info("Creating 3D viewer widget...")
        self.viewer = IfcViewerWidget(self)
        logger.info("Adding debug box (3m x 4m x 5m, red) to confirm rendering works...")
        self.viewer.add_debug_box()

        logger.info("Creating chat panel (QWebEngineView)...")
        self.chat_panel = ChatPanel(self)

        # The chat API runs on FastAPI's own background thread and can only
        # reach the viewer through this bridge - see ViewerBridge for why.
        self._viewer_bridge = ViewerBridge()
        self._viewer_bridge.highlight_requested.connect(self.viewer.highlight)
        self._viewer_bridge.select_by_class_requested.connect(self.viewer.select_by_class)
        set_tool_executor(ViewerToolExecutor(self._viewer_bridge))

        splitter = QSplitter(self)
        splitter.addWidget(self.viewer)
        splitter.addWidget(self.chat_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        # A QWebEngineView with no page loaded reports a 0x0 size hint, and
        # QSplitter would hand it zero width - the panel disappears entirely.
        # Give the split an explicit starting ratio and forbid collapsing.
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([840, 560])

        central = QWidget(self)
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.addWidget(splitter, stretch=4)
        central_layout.addWidget(self.log_panel, stretch=1)
        self.setCentralWidget(central)

        self._last_ifc_dir = Path.home()
        self._i18n_registrations: list[tuple[Callable[[str], None], str]] = []
        self._build_menu_bar()
        self.chat_panel.set_language(get_language())

        self.statusBar().showMessage(t("status_ready"))

    # ---- menu bar -----------------------------------------------------------
    def _build_menu_bar(self) -> None:
        file_menu = self.menuBar().addMenu(t("file_menu"))
        self._register_i18n(file_menu.setTitle, "file_menu")

        open_action = QAction(t("open_ifc_action"), self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_ifc_dialog)
        self._register_i18n(open_action.setText, "open_ifc_action")
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        quit_action = QAction(t("quit_action"), self)
        # StandardKey.Quit resolves to nothing on Windows, so set it explicitly.
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        self._register_i18n(quit_action.setText, "quit_action")
        file_menu.addAction(quit_action)

        view_menu = self.menuBar().addMenu(t("view_menu"))
        self._register_i18n(view_menu.setTitle, "view_menu")

        # The groups are kept on self: a QActionGroup that goes out of scope
        # takes the exclusivity of its actions with it.
        self._viewer_theme_group = self._add_radio_menu(
            view_menu,
            "viewer_theme_menu",
            [("light", "theme_light"), ("dark", "theme_dark")],
            self.viewer.set_theme,
            self.viewer.theme_name,
        )
        self._chat_theme_group = self._add_radio_menu(
            view_menu,
            "chat_theme_menu",
            [("light", "theme_light"), ("dark", "theme_dark")],
            self.chat_panel.set_theme,
            self.chat_panel.theme_name,
        )
        # Language names are proper nouns for the language itself, written
        # the same way regardless of which UI language is active - unlike
        # the theme options above, they are never passed through t().
        self._language_group = self._add_radio_menu(
            view_menu,
            "language_menu",
            [("en", "English"), ("ja", "日本語")],
            self.set_language,
            get_language(),
            translate_labels=False,
        )

        ai_menu = self.menuBar().addMenu(t("ai_menu"))
        self._register_i18n(ai_menu.setTitle, "ai_menu")

        ai_settings_action = QAction(t("ai_settings_action"), self)
        ai_settings_action.triggered.connect(self.open_ai_settings_dialog)
        self._register_i18n(ai_settings_action.setText, "ai_settings_action")
        ai_menu.addAction(ai_settings_action)

    def _add_radio_menu(
        self,
        parent_menu: QMenu,
        title_key: str,
        options: list[tuple[str, str]],
        apply_value: Callable[[str], None],
        current: str,
        translate_labels: bool = True,
    ) -> QActionGroup:
        menu = parent_menu.addMenu(t(title_key))
        self._register_i18n(menu.setTitle, title_key)

        group = QActionGroup(self)
        group.setExclusive(True)

        for value, label in options:
            action = QAction(t(label) if translate_labels else label, self)
            action.setCheckable(True)
            action.setChecked(value == current)
            action.triggered.connect(lambda _checked=False, v=value: apply_value(v))
            if translate_labels:
                self._register_i18n(action.setText, label)
            group.addAction(action)
            menu.addAction(action)

        return group

    def _register_i18n(self, setter: Callable[[str], None], key: str) -> None:
        self._i18n_registrations.append((setter, key))
        setter(t(key))

    def set_language(self, code: str) -> None:
        set_ui_language(code)
        for setter, key in self._i18n_registrations:
            setter(t(key))
        self.statusBar().showMessage(t("status_ready"))
        self.chat_panel.set_language(code)

    # ---- AI settings ----------------------------------------------------------
    def open_ai_settings_dialog(self) -> None:
        dialog = AiSettingsDialog(self)
        if dialog.exec() == AiSettingsDialog.DialogCode.Accepted:
            dialog.save()

    # ---- file loading -------------------------------------------------------
    def open_ifc_dialog(self) -> None:
        file_filter = (
            f"{t('ifc_file_filter_label')} (*.ifc);;{t('all_files_filter_label')} (*)"
        )
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            t("open_ifc_dialog_title"),
            str(self._last_ifc_dir),
            file_filter,
        )
        if not path_str:
            return

        ifc_path = Path(path_str)
        self._last_ifc_dir = ifc_path.parent
        self.try_load_ifc_file(ifc_path)

    def try_load_ifc_file(self, ifc_path: Path) -> bool:
        """Load an IFC file, reporting failure instead of tearing down the UI."""
        try:
            self.load_ifc_file(ifc_path)
            return True
        except Exception:
            logger.exception("Failed to load IFC file: %s", ifc_path)
            self.statusBar().showMessage(t("load_failed_status", name=ifc_path.name), 8000)
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Critical)
            box.setWindowTitle(t("load_error_title"))
            box.setText(t("load_error_text", name=ifc_path.name))
            box.setInformativeText(t("load_error_informative"))
            box.exec()
            return False

    def load_chat_ui(self, url: QUrl) -> None:
        self.chat_panel.load_chat_ui(url)

    def load_ifc_file(self, ifc_path: Path) -> None:
        logger.info("Opening IFC file: %s", ifc_path)
        self.statusBar().showMessage(t("loading_status", name=ifc_path.name))
        QApplication.processEvents()

        model = load_model(ifc_path)
        logger.info("Model opened (schema=%s). Extracting geometry...", model.schema)

        self.viewer.clear()
        mesh_count = 0

        for element_mesh in iter_all_product_meshes(model):
            self.viewer.add_mesh(element_mesh)
            mesh_count += 1

            if mesh_count % 10 == 0:
                logger.info("  %d elements loaded...", mesh_count)
                self.statusBar().showMessage(
                    t("loading_status_with_count", name=ifc_path.name, count=mesh_count)
                )
                QApplication.processEvents()

        self.viewer.reset_camera()
        logger.info("Done: %d elements loaded.", mesh_count)
        self.statusBar().showMessage(
            t("loaded_status", name=ifc_path.name, count=mesh_count), 5000
        )


def main() -> None:
    # Recommended by QtWebEngine; must be set before QApplication is
    # constructed. Note this is NOT what keeps the 3D viewport from going
    # black next to the chat panel - see IfcViewerWidget.__init__ for that.
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)

    app = QApplication(sys.argv)

    splash_pixmap = QPixmap(420, 160)
    splash_pixmap.fill(Qt.white)
    splash = QSplashScreen(splash_pixmap)
    splash.showMessage(
        "Starting ENMA IFC Desktop Viewer...\nFirst launch can take a while.",
        Qt.AlignCenter,
    )
    splash.show()
    app.processEvents()

    logger.info("Starting local API server...")
    start_local_server()

    logger.info("Creating main window...")
    window = MainWindow()
    window.resize(1400, 900)

    # Shown before loading geometry so the log panel and status bar give
    # feedback while a large IFC file is being processed.
    window.show()
    splash.finish(window)
    app.processEvents()

    # Point the chat panel at the local API server, replacing the
    # placeholder. Serving over http (not file://) keeps the frontend and
    # /chat on the same origin - see api_server.py's StaticFiles mount.
    window.load_chat_ui(QUrl("http://127.0.0.1:8756/"))

    if len(sys.argv) > 1:
        window.try_load_ifc_file(Path(sys.argv[1]))

    logger.info("Window shown.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
