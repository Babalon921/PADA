import sys

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QTextBlockFormat, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileSystemModel,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from agent import stream_response

ACCENT = "#FF0000"

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
QTextEdit {{
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


class AgentWorker(QThread):
    token_received = Signal(str)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self._message = message

    def run(self) -> None:
        try:
            for token in stream_response(self._message):
                self.token_received.emit(token)
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished_ok.emit()


class AgentWindow(QMainWindow):
    def __init__(self, workspace_path: str = "."):
        super().__init__()
        self.setWindowTitle("Agent")
        self.resize(1000, 650)

        self._build_terminal_panel()
        self._build_file_explorer_dock(workspace_path)

    def _build_terminal_panel(self) -> None:
        self.output = QTextEdit(self)
        self.output.setReadOnly(True)
        self.append_agent("$ agent ready")

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

    def _build_file_explorer_dock(self, workspace_path: str) -> None:
        model = QFileSystemModel(self)
        model.setRootPath(workspace_path)

        tree = QTreeView(self)
        tree.setModel(model)
        tree.setRootIndex(model.index(workspace_path))

        dock = QDockWidget("Workspace", self)
        dock.setWidget(tree)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def handle_input(self) -> None:
        text = self.input.text().strip()
        if not text:
            return
        self.append_user(text)
        self.input.clear()
        self.input.setEnabled(False)

        self._begin_agent_message()
        self._worker = AgentWorker(text, self)
        self._worker.token_received.connect(self._append_agent_token)
        self._worker.failed.connect(self._on_agent_failed)
        self._worker.finished_ok.connect(self._on_agent_finished)
        self._worker.start()

    def _on_agent_failed(self, error: str) -> None:
        self._append_agent_token(f"[error] {error}")

    def _on_agent_finished(self) -> None:
        self.input.setEnabled(True)
        self.input.setFocus()

    def append_user(self, text: str) -> None:
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.End)
        if not self.output.document().isEmpty():
            cursor.insertBlock()

        block_format = QTextBlockFormat()
        block_format.setAlignment(Qt.AlignLeft)
        cursor.setBlockFormat(block_format)

        char_format = QTextCharFormat()
        char_format.setForeground(QColor("#e6e6e6"))
        cursor.insertText(text, char_format)

        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def append_agent(self, text: str) -> None:
        self._begin_agent_message()
        self._append_agent_token(text)

    def _begin_agent_message(self) -> None:
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.End)
        if not self.output.document().isEmpty():
            cursor.insertBlock()

        block_format = QTextBlockFormat()
        block_format.setAlignment(Qt.AlignRight)
        block_format.setLeftMargin(self.output.viewport().width() / 2)
        cursor.setBlockFormat(block_format)
        self.output.setTextCursor(cursor)

        self._agent_char_format = QTextCharFormat()
        self._agent_char_format.setForeground(QColor(ACCENT))

    def _append_agent_token(self, token: str) -> None:
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(token, self._agent_char_format)
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    win = AgentWindow(".")
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()