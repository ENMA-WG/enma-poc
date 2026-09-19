from __future__ import annotations

import logging
import sys
from pathlib import Path

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
from .server.api_server import start_local_server
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
        self._build_menu_bar()

        self.statusBar().showMessage("Ready")

    # ---- menu bar -----------------------------------------------------------
    def _build_menu_bar(self) -> None:
        file_menu = self.menuBar().addMenu("ファイル(&F)")

        open_action = QAction("IFC ファイルを開く...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_ifc_dialog)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        quit_action = QAction("終了", self)
        # StandardKey.Quit resolves to nothing on Windows, so set it explicitly.
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        view_menu = self.menuBar().addMenu("表示(&V)")
        # The groups are kept on self: a QActionGroup that goes out of scope
        # takes the exclusivity of its actions with it.
        self._viewer_theme_group = self._add_theme_menu(
            view_menu, "3D ビューの背景(&B)", self.viewer.set_theme, self.viewer.theme_name
        )
        self._chat_theme_group = self._add_theme_menu(
            view_menu, "AI チャットパネル(&C)", self.chat_panel.set_theme, self.chat_panel.theme_name
        )

    def _add_theme_menu(self, parent_menu: QMenu, title, apply_theme, current: str) -> QActionGroup:
        menu = parent_menu.addMenu(title)
        group = QActionGroup(self)
        group.setExclusive(True)

        for name, label in (("light", "ライト"), ("dark", "ダーク")):
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(name == current)
            action.triggered.connect(lambda _checked=False, n=name: apply_theme(n))
            group.addAction(action)
            menu.addAction(action)

        return group

    # ---- file loading -------------------------------------------------------
    def open_ifc_dialog(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "IFC ファイルを開く",
            str(self._last_ifc_dir),
            "IFC ファイル (*.ifc);;すべてのファイル (*)",
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
            self.statusBar().showMessage(f"読み込みに失敗しました: {ifc_path.name}", 8000)
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Critical)
            box.setWindowTitle("読み込みエラー")
            box.setText(f"{ifc_path.name} を読み込めませんでした。")
            box.setInformativeText("詳細は下部のログを確認してください。")
            box.exec()
            return False

    def load_chat_ui(self, url: QUrl) -> None:
        self.chat_panel.load_chat_ui(url)

    def load_ifc_file(self, ifc_path: Path) -> None:
        logger.info("Opening IFC file: %s", ifc_path)
        self.statusBar().showMessage(f"Loading {ifc_path.name} ...")
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
                    f"Loading {ifc_path.name} ... {mesh_count} elements"
                )
                QApplication.processEvents()

        self.viewer.reset_camera()
        logger.info("Done: %d elements loaded.", mesh_count)
        self.statusBar().showMessage(f"Loaded {ifc_path.name}: {mesh_count} elements", 5000)


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

    if len(sys.argv) > 1:
        window.try_load_ifc_file(Path(sys.argv[1]))

    logger.info("Window shown.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
