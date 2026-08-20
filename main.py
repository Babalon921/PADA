import os
import sys
import librosa
import numpy as np
import pickle
import sqlite3

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
    QListWidget,
    QAbstractItemView,
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
QPushButton:disabled {{
    background-color: #3a3a3a;
    color: #7a7a7a;
}}
"""
def audio_analyst(path):

      #y = samples sr = hz
      y, sr = librosa.load(path, sr=None)
      sample_ref = ["Samples", y,"Sample Rate",sr]

      tempo, bf = librosa.beat.beat_track(y=y, sr=sr)
      bt = librosa.frames_to_time(bf, sr=sr)
      bpm_ref = ["BPM",tempo,"Beat Time",bt]

      mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
      mfccs = ["Mfccs",mfccs]

      S_db = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
      S_db = ["STFT", S_db]

      S_C = librosa.feature.spectral_centroid(y=y, sr=sr)
      S_C = ["Spectral Centroid", S_C]

      ZCR = librosa.feature.zero_crossing_rate(y) 
      ZCR = ["Zero Cross Rate", ZCR]

      return sample_ref + bpm_ref + mfccs + S_db + S_C + ZCR

class AnalysisWorker(QThread):
    result_ready = Signal(str, object)
    finished_ok = Signal()

    def __init__(self, paths: list[str], parent=None):
        super().__init__(parent)
        self._paths = paths

    def run(self) -> None:
        for path in self._paths:
            result = audio_analyst(path)
            self.result_ready.emit(path, result)
        self.finished_ok.emit()

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
        self.setWindowTitle("PADA - Python based-Agentic Data Analyst")
        self.resize(1000, 600)

        self._init_analysis_db()
        self._build_terminal_panel()
        self._build_file_explorer_dock(workspace_path)
        self._build_artifacts_dock()

    def _build_terminal_panel(self) -> None:
        self.output = QTextEdit(self)
        self.output.setReadOnly(True)
        self.append_user("$ agent ready")

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
        self.explorer_model = QFileSystemModel(self)
        self.explorer_model.setRootPath(workspace_path)
        self.explorer_model.setNameFilters(["*.wav", "*.mp3", "*.flac"])
        self.explorer_tree = QTreeView(self)
        self.explorer_tree.setModel(self.explorer_model)
        self.explorer_tree.setRootIndex(self.explorer_model.index(workspace_path))
        self.explorer_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)


        self.analyse_btn = QPushButton("Analyse", self)
        self.analyse_btn.clicked.connect(self._on_analyse_clicked)

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.addWidget(self.explorer_tree)
        layout.addWidget(self.analyse_btn)

        dock = QDockWidget("Workspace", self)
        dock.setWidget(container)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self._explorer_dock = dock
        
    def _init_analysis_db(self) -> None:
        self._analysis_db = sqlite3.connect("analysis_results.db")
        self._analysis_db.execute(
            """
            CREATE TABLE IF NOT EXISTS audio_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                result BLOB NOT NULL
            )
            """
        )
        self._analysis_db.commit()

    def _save_analysis_result(self, path: str, result) -> None:
        self._analysis_db.execute(
            "INSERT INTO audio_analysis (path, result) VALUES (?, ?)",
            (path, pickle.dumps(result)),
        )
        self._analysis_db.commit()
        
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

        width = self.output.viewport().width()
        block_format = QTextBlockFormat()
        block_format.setAlignment(Qt.AlignLeft)
        block_format.setLeftMargin(width / 2)
        block_format.setRightMargin(width * 0.08)
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

    def _build_artifacts_dock(self) -> None:
        self.artifacts = QListWidget(self)
        self._load_artifacts()

        dock = QDockWidget("Data View", self)
        dock.setWidget(self.artifacts)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self.splitDockWidget(self._explorer_dock, dock, Qt.Vertical)

    def _load_artifacts(self) -> None:
        self.artifacts.clear()
        rows = self._analysis_db.execute(
            "SELECT path FROM audio_analysis ORDER BY id"
        ).fetchall()
        for (path,) in rows:
            self.artifacts.addItem(os.path.basename(path))

    def _on_analyse_clicked(self) -> None:
        paths = [
            self.explorer_model.filePath(index)
            for index in self.explorer_tree.selectionModel().selectedRows()
        ]
        self.analyse_btn.setEnabled(False)
        self.analyse_files(paths)

    def analyse_files(self, paths: list[str]) -> None:
        self._analysis_worker = AnalysisWorker(paths, self)
        self._analysis_worker.result_ready.connect(self._on_analysis_result)
        self._analysis_worker.finished_ok.connect(self._on_analysis_finished)
        self._analysis_worker.start()

    def _on_analysis_result(self, path: str, result) -> None:
        self._save_analysis_result(path, result)
        self.artifacts.addItem(os.path.basename(path))

    def _on_analysis_finished(self) -> None:
        self.analyse_btn.setEnabled(True)
            


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    win = AgentWindow(".")
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()