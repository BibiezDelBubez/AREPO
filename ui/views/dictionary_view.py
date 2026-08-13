"""
Dictionary View for AREPO (Ricerca Parole Rebus & Gestione Dual-Layer DB).
Incorporates word positional search, grammatical noun/verb filters, clipboard copy, and User Dictionary overlay manager.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QSpinBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QApplication, QMessageBox, QTabWidget, QGroupBox, QTextEdit
)
from PySide6.QtCore import Qt
from ui.components.odoo_card import OdooCard
from core.engine.word_search_engine import WordSearchEngine
from core.database.connection import DatabaseManager
from core.database.models import UserWord, Word


class DictionaryView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.db_mgr = DatabaseManager()
        self.word_engine = WordSearchEngine(db_mgr=self.db_mgr)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Tab Widget for Dictionary Tools
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self._build_search_tab()
        self._build_user_dict_tab()

    # --- Sub-tab 1: Ricerca Parole Rebus (Full Richness from Indovinista) ---
    def _build_search_tab(self) -> None:
        search_widget = QWidget()
        layout = QVBoxLayout(search_widget)

        card = OdooCard(
            title="🔤 Ricerca Parole Rebus (Dizionario Italiano)",
            subtitle="Cerca parole nel dizionario per posizione delle lettere (prefisso/suffisso) e categoria grammaticale. Preposizioni ed articoli sono esclusi in automatico."
        )

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Testo / Gruppo di Lettere:"))
        self.txt_query = QLineEdit()
        self.txt_query.setPlaceholderText("Es: ROSA, CARO, CA")
        self.txt_query.returnPressed.connect(self._run_word_search)
        h1.addWidget(self.txt_query)

        h1.addWidget(QLabel("Posizione Match:"))
        self.combo_pos = QComboBox()
        self.combo_pos.addItems(["Inizio (Prefisso)", "Fine (Suffisso)", "In mezzo", "Contiene"])
        h1.addWidget(self.combo_pos)
        card.add_layout(h1)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Filtro Categoria:"))
        self.combo_cat = QComboBox()
        self.combo_cat.addItems(["Solo Sostantivi (Nomi)", "Altro (Verbi, Aggettivi, ecc.)", "Tutte le categorie"])
        h2.addWidget(self.combo_cat)

        h2.addWidget(QLabel("Min Lettere:"))
        self.spin_min_l = QSpinBox()
        self.spin_min_l.setRange(2, 30)
        self.spin_min_l.setValue(3)
        h2.addWidget(self.spin_min_l)

        h2.addWidget(QLabel("Max Lettere:"))
        self.spin_max_l = QSpinBox()
        self.spin_max_l.setRange(2, 30)
        self.spin_max_l.setValue(20)
        h2.addWidget(self.spin_max_l)

        h2.addWidget(QLabel("Dizionario:"))
        self.combo_dict = QComboBox()
        self.combo_dict.addItems(["Dizionario 280.000 parole", "Dizionario comune 60.000 parole"])
        h2.addWidget(self.combo_dict)

        self.btn_search = QPushButton("🚀 Cerca Parole")
        self.btn_search.setProperty("class", "PrimaryAction")
        self.btn_search.clicked.connect(self._run_word_search)
        h2.addWidget(self.btn_search)

        card.add_layout(h2)
        layout.addWidget(card)

        # Status Label
        self.lbl_status = QLabel("💡 Doppio clic su una parola trovata per copiarla negli appunti.")
        self.lbl_status.setStyleSheet("color: #7F8C8D; font-style: italic;")
        layout.addWidget(self.lbl_status)

        # Results Table
        self.table_results = QTableWidget(0, 4)
        self.table_results.setHorizontalHeaderLabels(["Parola", "Categoria Grammaticale", "N° Lettere", "Posizione Match"])
        self.table_results.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_results.cellDoubleClicked.connect(self._copy_word_to_clipboard)
        layout.addWidget(self.table_results)

        self.tabs.addTab(search_widget, "🔍 Ricerca Parole Rebus")

    # --- Sub-tab 2: Dizionario Utente & Overlay Manager ---
    def _build_user_dict_tab(self) -> None:
        user_widget = QWidget()
        layout = QVBoxLayout(user_widget)

        card = OdooCard(
            title="📂 Dizionario Personale Utente & Blacklist Overlay",
            subtitle="Aggiungi neologismi o parole personalizzate, ed inserisci termini in blacklist per escluderli dai rebus e dai cruciverba."
        )

        grp_add = QGroupBox("Aggiungi Termine Utente / Definizioni Custom")
        v_add = QVBoxLayout(grp_add)
        h_add = QHBoxLayout()

        h_add.addWidget(QLabel("Termine:"))
        self.txt_custom_term = QLineEdit()
        self.txt_custom_term.setPlaceholderText("Es: ANTIGRAVITA")
        h_add.addWidget(self.txt_custom_term)

        h_add.addWidget(QLabel("Categoria:"))
        self.combo_custom_cat = QComboBox()
        self.combo_custom_cat.addItems(["Sostantivo", "Verbo", "Aggettivo", "Altro"])
        h_add.addWidget(self.combo_custom_cat)

        btn_add_term = QPushButton("➕ Aggiungi Termine")
        btn_add_term.setProperty("class", "PrimaryAction")
        btn_add_term.clicked.connect(self._add_custom_word)
        h_add.addWidget(btn_add_term)
        v_add.addLayout(h_add)
        card.add_widget(grp_add)

        layout.addWidget(card)

        # User Words Table
        self.table_user_words = QTableWidget(0, 3)
        self.table_user_words.setHorizontalHeaderLabels(["Termine Utente", "Categoria", "Blacklist / Escluso"])
        self.table_user_words.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_user_words)

        self._load_user_words_table()

        self.tabs.addTab(user_widget, "📂 Dizionario Utente (Overlay)")

    def _run_word_search(self) -> None:
        query = self.txt_query.text().strip()
        if not query or len(query) < 2:
            QMessageBox.warning(self, "Attenzione", "Inserisci almeno 2 lettere da cercare!")
            return

        pos_map = {
            "Inizio (Prefisso)": "start",
            "Fine (Suffisso)": "end",
            "In mezzo": "middle",
            "Contiene": "contains"
        }
        pos_mode = pos_map.get(self.combo_pos.currentText(), "start")

        cat_map = {
            "Solo Sostantivi (Nomi)": "nouns",
            "Altro (Verbi, Aggettivi, ecc.)": "other",
            "Tutte le categorie": "all"
        }
        cat_filter = cat_map.get(self.combo_cat.currentText(), "all")

        dict_choice = "280k" if "280.000" in self.combo_dict.currentText() else "60k"

        results = self.word_engine.search_words(
            query=query,
            pos_mode=pos_mode,
            category_filter=cat_filter,
            min_letters=self.spin_min_l.value(),
            max_letters=self.spin_max_l.value(),
            dict_choice=dict_choice,
            max_results=100
        )

        self.lbl_status.setText(f"Trovate {len(results)} parole corrispondenti ai criteri. Doppio clic per copiare.")
        self.table_results.setRowCount(len(results))

        for r, res in enumerate(results):
            self.table_results.setItem(r, 0, QTableWidgetItem(res.word))
            self.table_results.setItem(r, 1, QTableWidgetItem(res.category))
            self.table_results.setItem(r, 2, QTableWidgetItem(str(res.letters_count)))
            self.table_results.setItem(r, 3, QTableWidgetItem(res.match_position))

    def _copy_word_to_clipboard(self, row: int, col: int) -> None:
        item = self.table_results.item(row, 0)
        if item:
            word = item.text()
            QApplication.clipboard().setText(word)
            self.lbl_status.setText(f"📋 Parola '{word}' copiata negli appunti!")

    def _add_custom_word(self) -> None:
        term = self.txt_custom_term.text().strip().upper()
        if not term:
            return

        cat = self.combo_custom_cat.currentText()
        session = self.db_mgr.get_user_session()
        try:
            uw = UserWord(term=term, length=len(term), category=cat)
            session.add(uw)
            session.commit()
            QMessageBox.information(self, "Successo", f"Termine '{term}' aggiunto al dizionario utente!")
            self.txt_custom_term.clear()
            self._load_user_words_table()
        except Exception as e:
            session.rollback()
            QMessageBox.warning(self, "Attenzione", f"Impossibile aggiungere il termine (già presente o errore): {str(e)}")
        finally:
            session.close()

    def _load_user_words_table(self) -> None:
        session = self.db_mgr.get_user_session()
        try:
            user_words = session.query(UserWord).all()
            self.table_user_words.setRowCount(len(user_words))
            for r, uw in enumerate(user_words):
                self.table_user_words.setItem(r, 0, QTableWidgetItem(uw.term))
                self.table_user_words.setItem(r, 1, QTableWidgetItem(uw.category))
                self.table_user_words.setItem(r, 2, QTableWidgetItem("Sì" if uw.is_blacklisted else "No"))
        finally:
            session.close()
