import sys

from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileSystemModel,
    QMainWindow,
    QTreeView,
    QWidget,
)
from PySide6.QtCore import Qt

ACCENT = "#f00000"

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: #1a1a1a;
    color: #e6e6e6;
}}
QTreeView {{
    background-color: #242424;
    border: 1px solid #3a3a3a;
}}
QTreeView::item:selected {{
    background-color: {ACCENT};
}}
QDockWidget::title {{
    background-color: #212121;
    padding: 6px;
    border-left: 2px solid {ACCENT};
}}
QPlainTextEdit {{
    background-color: #111111;
    color: #e6e6e6;
    border: 1px solid #3a3a3a;
    font-family: "Consolas", "Menlo", monospace;
}}
QLineEdit {{
    background-color: #242424;
    color: #e6e6e6;
    border: 1px solid #3a3a3a;
    padding: 6px;
    font-family: "Consolas", "Menlo", monospace;
}}
QLineEdit:focus {{
    border: 1px solid {ACCENT};
}}
QPushButton {{
    background-color: {ACCENT};
    color: #ffffff;
    border: none;
    padding: 6px 16px;
}}
QPushButton:hover {{
    background-color: #ff6369;
}}
"""


class AgentWindow(QMainWindow):
    def __init__(self, workspace_path: str = "."):
        super().__init__()
        self.setWindowTitle("Agent")
        self.resize(1000, 650)

        #agent panel
        self.setCentralWidget(QWidget(self))

        self._model = QFileSystemModel(self)
        self._model.setRootPath(workspace_path)

        tree = QTreeView(self)
        tree.setModel(self._model)
        tree.setRootIndex(self._model.index(workspace_path))

        dock = QDockWidget("Workspace", self)
        dock.setWidget(tree)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)


def main():
    

    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    win = AgentWindow(".")
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()