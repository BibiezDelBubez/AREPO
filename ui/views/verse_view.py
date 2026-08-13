"""
Verse Games View for AREPO (Giochi in Versi).
Includes Meter Editor, Rhyme Finder, Anagrams, Zeppe, Cambi, and Bisenzi tools.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QTabWidget, QMessageBox
)
from PySide6.QtCore import Qt
from ui.components.odoo_card import OdooCard
from ui.components.meter_editor import MeterEditorWidget
from core.modules.verse_logic import VerseLogic


class VerseView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.verse_logic = VerseLogic()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Tab Widget for Verse Sub-tools
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self._build_meter_tab()
        self._build_transformations_tab()

    # --- Sub-tab 1: Meter IDE ---
    def _build_meter_tab(self) -> None:
        meter_widget = QWidget()
        layout = QVBoxLayout(meter_widget)

        card = OdooCard(
            title="📜 Assistente Metrico & Prosodia",
            subtitle="Scrivi e analizza la struttura metrica delle righe di poesia. Riconosce la Sinalefe ed il conteggio delle sillabe."
        )
        layout.addWidget(card)

        self.meter_editor = MeterEditorWidget()
        layout.addWidget(self.meter_editor)

        self.tabs.addTab(meter_widget, "📜 IDE Metrico")

    # --- Sub-tab 2: Transformations ---
    def _build_transformations_tab(self) -> None:
        trans_widget = QWidget()
        layout = QVBoxLayout(trans_widget)

        card = OdooCard(
            title="🔤 Combinatorio Enigmistico",
            subtitle="Ricerca Rime, Anagrammi, Zeppe, Cambi di lettera e Bisenzi per una parola base."
        )

        h_search = QHBoxLayout()
        h_search.addWidget(QLabel("Parola Base:"))
        self.txt_word = QLineEdit()
        self.txt_word.setPlaceholderText("Es: PARCO")
        h_search.addWidget(self.txt_word)

        btn_find = QPushButton("Cerca Combinazioni")
        btn_find.setProperty("class", "PrimaryAction")
        btn_find.clicked.connect(self._run_transformations)
        h_search.addWidget(btn_find)
        card.add_layout(h_search)
        layout.addWidget(card)

        # Results Notebook
        res_tabs = QTabWidget()
        
        self.list_rhymes = QListWidget()
        self.list_anagrams = QListWidget()
        self.list_zeppe = QListWidget()
        self.list_cambi = QListWidget()
        self.list_bisenzi = QListWidget()

        res_tabs.addTab(self.list_rhymes, "Rime")
        res_tabs.addTab(self.list_anagrams, "Anagrammi")
        res_tabs.addTab(self.list_zeppe, "Zeppe (+1 Lettera)")
        res_tabs.addTab(self.list_cambi, "Cambi di Lettera")
        res_tabs.addTab(self.list_bisenzi, "Bisenzi (Omografi)")

        layout.addWidget(res_tabs)
        self.tabs.addTab(trans_widget, "🔤 Rime & Combinazioni")

    def _run_transformations(self) -> None:
        w = self.txt_word.text().strip().upper()
        if not w:
            QMessageBox.warning(self, "Attenzione", "Inserisci una parola base!")
            return

        # 1. Rhymes
        rhymes = self.verse_logic.find_rhymes(w)
        self.list_rhymes.clear()
        for r in rhymes:
            self.list_rhymes.addItem(r)

        # 2. Anagrams
        anagrams = self.verse_logic.find_anagrams(w)
        self.list_anagrams.clear()
        for a in anagrams:
            self.list_anagrams.addItem(a)

        # 3. Zeppe
        zeppe = self.verse_logic.find_zeppe(w)
        self.list_zeppe.clear()
        for z_word, char, pos in zeppe:
            self.list_zeppe.addItem(f"{z_word} (Lettera '{char}' in pos {pos+1})")

        # 4. Cambi
        cambi = self.verse_logic.find_cambi(w)
        self.list_cambi.clear()
        for c_word, old_c, new_c, pos in cambi:
            self.list_cambi.addItem(f"{c_word} ('{old_c}' -> '{new_c}' in pos {pos+1})")

        # 5. Bisenzi
        bisenzi = self.verse_logic.find_bisenzi(w)
        self.list_bisenzi.clear()
        for b in bisenzi:
            self.list_bisenzi.addItem(b)
