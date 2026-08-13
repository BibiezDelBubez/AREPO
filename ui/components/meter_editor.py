"""
Meter Editor Component for PySide6 (Giochi in Versi).
Provides live poetic line syllable counting and metric badge indicators.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, QLabel, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, Signal
from core.engine.syllabifier import Syllabifier


class MeterEditorWidget(QWidget):
    lines_changed = Signal(list)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Left: Text Editor for Poetry
        self.text_editor = QTextEdit()
        self.text_editor.setPlaceholderText("Scrivi qui i tuoi versi...\nEs: Nel mezzo del cammin di nostra vita")
        self.text_editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.text_editor, stretch=3)

        # Right: Metric Syllable Counter List
        self.meter_list = QListWidget()
        self.meter_list.setFixedWidth(200)
        layout.addWidget(self.meter_list, stretch=1)

    def _on_text_changed(self) -> None:
        text = self.text_editor.toPlainText()
        lines = text.split('\n')
        
        self.meter_list.clear()
        for idx, line in enumerate(lines, 1):
            if not line.strip():
                item = QListWidgetItem(f"Riga {idx}: -")
                self.meter_list.addItem(item)
                continue

            count, syls, details = Syllabifier.count_line_metric_syllables(line)
            meter_name = Syllabifier.get_meter_name(count)
            
            item = QListWidgetItem(f"[{count}] {meter_name}")
            if count == 11:
                item.setForeground(Qt.darkGreen)
            elif count in (7, 8, 9, 10):
                item.setForeground(Qt.blue)
            else:
                item.setForeground(Qt.darkRed)
                
            self.meter_list.addItem(item)

        self.lines_changed.emit(lines)
