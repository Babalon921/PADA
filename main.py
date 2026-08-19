import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileSystemModel,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)


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
        self.setWindowTitle("PADA - Python based-Agentic Data Analyst")
        self.resize(1000, 400)

        self._build_term_panel()
        self._build_file_explorer_()

    def _build_term_panel(self) -> None:
        self.output = QPlainTextEdit(self)
        self.output.setReadOnly(True)
        self.output.appendPlainText("$ agent ready")

        self.input = QLineEdit(self)
        self.input.setPlaceholderText("Type a message...")
        self.input.returnPressed.connect(self.handle_input)

        send_btn = QPushButton("Send", self)
        send_btn.clicked.connect(self.handle_input)

        input_row = QHBoxLayout()
        input_row.addWidget(self.input)
        input_row.addWidget(send_btn)

        layout = QVBoxLayout()
        layout.addWidget(self.output)
        layout.addLayout(input_row)

        central = QWidget(self)
        central.setLayout(layout)
        self.setCentralWidget(central)

    def _build_file_explorer_(self,workspace_path: str = ".") -> None:
        model = QFileSystemModel(self)
        model.setRootPath(workspace_path)

        #self._model = QFileSystemModel(self)
        #self._model.setRootPath(workspace_path)

        tree = QTreeView(self)
        tree.setModel(model)
        tree.setRootIndex(model.index(workspace_path))

        dock = QDockWidget("Workspace", self)
        dock.setWidget(tree)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def artifact_view(self) -> None:
        return

    def handle_input(self) -> None:
        text = self.input.text().strip()
        if not text:
            return "-_-"
        self.output.appendPlainText(f">>> {text}")
        self.input.clear()

        ## agentic code here

def main():
    #print("Enter Path:  ")
    #user_input = input()
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    win = AgentWindow(".")
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()