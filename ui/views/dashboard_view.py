"""
Dashboard View for AREPO (Enigmistica Suite).
Provides welcome overview cards with quick navigation shortcuts.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout
from PySide6.QtCore import Qt, Signal
from ui.components.odoo_card import OdooCard


class DashboardView(QWidget):
    navigate_requested = Signal(str)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header Card
        header_card = OdooCard(
            title="🎯 AREPO - Suite Professionale per L'Enigmistica",
            subtitle="Piattaforma avanzata per la creazione di Rebus, Anarebus, Giochi in Versi e Cruciverba."
        )
        main_layout.addWidget(header_card)

        # Shortcuts Grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(16)

        # Card 1: Rebus & Anarebus
        card_rebus = OdooCard(
            title="🧩 Rebus, Anarebus & NLP",
            subtitle="Estrattore sintagmi da testi, valutatore Regole d'Oro, assistente lettere e stereoscopici."
        )
        btn_rebus = QPushButton("Apri Modulo Rebus")
        btn_rebus.setProperty("class", "PrimaryAction")
        btn_rebus.clicked.connect(lambda: self.navigate_requested.emit("rebus"))
        card_rebus.add_widget(btn_rebus)
        grid_layout.addWidget(card_rebus, 0, 0)

        # Card 2: Giochi in Versi
        card_verse = OdooCard(
            title="📜 Giochi in Versi (IDE Metrico)",
            subtitle="Sillabatore prosodico con sinalefe, contatore di metrica, rime, bisenzi, zeppe e cambi."
        )
        btn_verse = QPushButton("Apri IDE Metrico")
        btn_verse.setProperty("class", "PrimaryAction")
        btn_verse.clicked.connect(lambda: self.navigate_requested.emit("verse"))
        card_verse.add_widget(btn_verse)
        grid_layout.addWidget(card_verse, 0, 1)

        # Card 3: Cruciverba
        card_cross = OdooCard(
            title="✏️ Cruciverba & Derivati",
            subtitle="Editor griglia con simmetria automatica, numerazione e motore di backtracking DFS su DAWG."
        )
        btn_cross = QPushButton("Apri Editor Cruciverba")
        btn_cross.setProperty("class", "PrimaryAction")
        btn_cross.clicked.connect(lambda: self.navigate_requested.emit("crossword"))
        card_cross.add_widget(btn_cross)
        grid_layout.addWidget(card_cross, 1, 0)

        # Card 4: Dizionario & Ricerca
        card_dict = OdooCard(
            title="🔤 Dizionario Duale & Ricerca",
            subtitle="Ricerca posizionale e grammaticale su 280k parole, esclusioni blacklist e note utente."
        )
        btn_dict = QPushButton("Apri Dizionario")
        btn_dict.setProperty("class", "PrimaryAction")
        btn_dict.clicked.connect(lambda: self.navigate_requested.emit("dictionary"))
        card_dict.add_widget(btn_dict)
        grid_layout.addWidget(card_dict, 1, 1)

        # Card 5: Dipendenze & Sistema
        card_system = OdooCard(
            title="⚙️ Dipendenze & Sistema",
            subtitle="Gestisci le librerie Python installate (PySide6, SQLAlchemy, spaCy, ReportLab) ed aggiornale via pip."
        )
        btn_system = QPushButton("Gestisci Dipendenze")
        btn_system.setProperty("class", "SecondaryAction")
        btn_system.clicked.connect(lambda: self.navigate_requested.emit("system"))
        card_system.add_widget(btn_system)
        grid_layout.addWidget(card_system, 2, 0, 1, 2)

        main_layout.addLayout(grid_layout)
        main_layout.addStretch()
