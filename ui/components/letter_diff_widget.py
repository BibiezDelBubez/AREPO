"""
Letter Difference Assistant Component for PySide6.
Displays missing and surplus letter counts between keys and solution phrases.
"""

from typing import Dict
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QFrame
from PySide6.QtCore import Qt


class LetterDiffWidget(QFrame):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setObjectName("OdooCard")

        main_layout = QVBoxLayout(self)

        header = QLabel("📊 Assistente Lettere (Confronto Anarebus)")
        header.setStyleSheet("font-weight: bold; font-size: 13px; color: #2C3E50;")
        main_layout.addWidget(header)

        boxes_layout = QHBoxLayout()

        # Missing Letters Box (Red)
        self.missing_frame = QFrame()
        self.missing_frame.setStyleSheet("background-color: #FDE8E8; border-radius: 6px; padding: 8px;")
        missing_vbox = QVBoxLayout(self.missing_frame)
        self.lbl_missing_title = QLabel("❌ Lettere Mancanti nelle Chiavi:")
        self.lbl_missing_title.setStyleSheet("color: #9B1C1C; font-weight: bold; font-size: 12px;")
        self.lbl_missing_val = QLabel("Nessuna")
        self.lbl_missing_val.setStyleSheet("color: #9B1C1C; font-size: 13px;")
        missing_vbox.addWidget(self.lbl_missing_title)
        missing_vbox.addWidget(self.lbl_missing_val)

        # Surplus Letters Box (Blue)
        self.surplus_frame = QFrame()
        self.surplus_frame.setStyleSheet("background-color: #E1EFFE; border-radius: 6px; padding: 8px;")
        surplus_vbox = QVBoxLayout(self.surplus_frame)
        self.lbl_surplus_title = QLabel("ℹ️ Lettere in Più nelle Chiavi:")
        self.lbl_surplus_title.setStyleSheet("color: #1E40AF; font-weight: bold; font-size: 12px;")
        self.lbl_surplus_val = QLabel("Nessuna")
        self.lbl_surplus_val.setStyleSheet("color: #1E40AF; font-size: 13px;")
        surplus_vbox.addWidget(self.lbl_surplus_title)
        surplus_vbox.addWidget(self.lbl_surplus_val)

        boxes_layout.addWidget(self.missing_frame)
        boxes_layout.addWidget(self.surplus_frame)
        main_layout.addLayout(boxes_layout)

    def update_diff(self, missing: Dict[str, int], surplus: Dict[str, int], is_perfect: bool) -> None:
        if is_perfect:
            self.lbl_missing_val.setText("✅ Anagramma Perfetto (0 Mancanti)")
            self.lbl_surplus_val.setText("✅ Anagramma Perfetto (0 Eccedenti)")
            return

        if missing:
            m_str = ", ".join(f"{k}: {v}" for k, v in sorted(missing.items()))
            self.lbl_missing_val.setText(m_str)
        else:
            self.lbl_missing_val.setText("Nessuna")

        if surplus:
            s_str = ", ".join(f"{k}: {v}" for k, v in sorted(surplus.items()))
            self.lbl_surplus_val.setText(s_str)
        else:
            self.lbl_surplus_val.setText("Nessuna")
