"""
OdooCard Component for PySide6.
Provides an elegant white card container widget with title and subtitle.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt


class OdooCard(QFrame):
    def __init__(self, title: str = "", subtitle: str = "", parent: QWidget = None):
        super().__init__(parent)
        self.setObjectName("OdooCard")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(10)

        if title:
            self.title_label = QLabel(title)
            self.title_label.setObjectName("CardTitle")
            self.title_label.setProperty("class", "CardTitle")
            self.layout.addWidget(self.title_label)

        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setObjectName("Subtitle")
            self.subtitle_label.setProperty("class", "Subtitle")
            self.layout.addWidget(self.subtitle_label)

    def add_widget(self, widget: QWidget) -> None:
        self.layout.addWidget(widget)

    def add_layout(self, layout) -> None:
        self.layout.addLayout(layout)
