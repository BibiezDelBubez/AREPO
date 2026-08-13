"""
Rebus & Anarebus View for AREPO.
Includes NLP Syntagm Extractor, Anarebus Golden Rules Evaluator, Scomposizione, and Stereorebus Engine.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QLineEdit,
    QPushButton, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QTableWidget, QTableWidgetItem, QFileDialog, QHeaderView, QMessageBox,
    QProgressBar, QTextEdit, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal
from ui.components.odoo_card import OdooCard
from ui.components.letter_diff_widget import LetterDiffWidget
from core.engine.anarebus_engine import AnarebusEngine
from core.engine.nlp_engine import NLPEngine
from core.engine.stereorebus_engine import StereorebusEngine
from exporter.data_exporter import DataExporter


class NLPScanThread(QThread):
    progress_signal = Signal(float, str)
    log_signal = Signal(str)
    finished_signal = Signal(list)

    def __init__(self, nlp_engine: NLPEngine, path: str, is_dir: bool, params: dict):
        super().__init__()
        self.nlp_engine = nlp_engine
        self.path = path
        self.is_dir = is_dir
        self.params = params
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        if self.is_dir:
            results = self.nlp_engine.process_directory(
                self.path,
                self.params,
                progress_callback=lambda pct, msg: self.progress_signal.emit(pct, msg),
                log_callback=lambda msg: self.log_signal.emit(msg),
                is_cancelled=lambda: self._cancelled
            )
        else:
            results = self.nlp_engine.process_file(
                self.path,
                self.params,
                progress_callback=lambda pct, msg: self.progress_signal.emit(pct, msg),
                log_callback=lambda msg: self.log_signal.emit(msg),
                is_cancelled=lambda: self._cancelled
            )
        self.finished_signal.emit(results)


class RebusView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.anarebus_engine = AnarebusEngine()
        self.stereorebus_engine = StereorebusEngine()
        self.nlp_engine = None
        self.nlp_results = []
        self.scan_thread = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Tab Widget for Rebus Sub-tools
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self._build_nlp_tab()
        self._build_anarebus_tab()
        self._build_stereorebus_tab()

    # --- Sub-tab 1: NLP Extractor (Full Richness from Indovinista) ---
    def _build_nlp_tab(self) -> None:
        nlp_widget = QWidget()
        layout = QVBoxLayout(nlp_widget)

        ctrl_card = OdooCard(
            title="🔍 Estrattore Sintagmi Rebus (NLP spaCy)",
            subtitle="Analizza file di testo (.txt) per estrarre combinazioni evocative di parole adatte ai rebus."
        )

        h_files = QHBoxLayout()
        self.btn_select_file = QPushButton("Seleziona File TXT")
        self.btn_select_file.setProperty("class", "SecondaryAction")
        self.btn_select_file.clicked.connect(self._select_file)
        
        self.btn_select_dir = QPushButton("Seleziona Cartella TXT")
        self.btn_select_dir.setProperty("class", "SecondaryAction")
        self.btn_select_dir.clicked.connect(self._select_dir)

        self.lbl_selected_path = QLabel("Nessun file o cartella selezionati")
        self.lbl_selected_path.setStyleSheet("font-weight: bold; color: #2C3E50;")

        h_files.addWidget(self.btn_select_file)
        h_files.addWidget(self.btn_select_dir)
        h_files.addWidget(self.lbl_selected_path)
        h_files.addStretch()
        ctrl_card.add_layout(h_files)

        # Parameters Box 1: Words & Letters
        h_p1 = QHBoxLayout()
        h_p1.addWidget(QLabel("Min Parole:"))
        self.spin_min_w = QSpinBox()
        self.spin_min_w.setRange(1, 10)
        self.spin_min_w.setValue(2)
        h_p1.addWidget(self.spin_min_w)

        h_p1.addWidget(QLabel("Max Parole:"))
        self.spin_max_w = QSpinBox()
        self.spin_max_w.setRange(1, 10)
        self.spin_max_w.setValue(5)
        h_p1.addWidget(self.spin_max_w)

        h_p1.addWidget(QLabel("Min Lettere:"))
        self.spin_min_l = QSpinBox()
        self.spin_min_l.setRange(5, 40)
        self.spin_min_l.setValue(10)
        h_p1.addWidget(self.spin_min_l)

        h_p1.addWidget(QLabel("Max Lettere:"))
        self.spin_max_l = QSpinBox()
        self.spin_max_l.setRange(5, 50)
        self.spin_max_l.setValue(30)
        h_p1.addWidget(self.spin_max_l)

        ctrl_card.add_layout(h_p1)

        # Parameters Box 2: Sweet Spot & Filters
        h_p2 = QHBoxLayout()
        h_p2.addWidget(QLabel("Sweet Spot Min:"))
        self.spin_sweet_min = QSpinBox()
        self.spin_sweet_min.setRange(5, 40)
        self.spin_sweet_min.setValue(12)
        h_p2.addWidget(self.spin_sweet_min)

        h_p2.addWidget(QLabel("Sweet Spot Max:"))
        self.spin_sweet_max = QSpinBox()
        self.spin_sweet_max.setRange(5, 40)
        self.spin_sweet_max.setValue(20)
        h_p2.addWidget(self.spin_sweet_max)

        h_p2.addWidget(QLabel("Score Minimo:"))
        self.spin_min_score = QDoubleSpinBox()
        self.spin_min_score.setRange(1.0, 10.0)
        self.spin_min_score.setSingleStep(0.5)
        self.spin_min_score.setValue(5.0)
        h_p2.addWidget(self.spin_min_score)

        self.chk_strict_verbs = QCheckBox("Escludi Verbi (Strict)")
        self.chk_strict_verbs.setChecked(True)
        h_p2.addWidget(self.chk_strict_verbs)

        self.chk_random = QCheckBox("Campionamento Casuale")
        self.chk_random.setChecked(True)
        h_p2.addWidget(self.chk_random)

        ctrl_card.add_layout(h_p2)

        # Scan Buttons
        h_scan = QHBoxLayout()
        self.btn_start_scan = QPushButton("🚀 Avvia Scansione NLP")
        self.btn_start_scan.setProperty("class", "PrimaryAction")
        self.btn_start_scan.clicked.connect(self._start_nlp_scan)
        h_scan.addWidget(self.btn_start_scan)

        self.btn_cancel_scan = QPushButton("🛑 Interrompi Scansione")
        self.btn_cancel_scan.setProperty("class", "SecondaryAction")
        self.btn_cancel_scan.setEnabled(False)
        self.btn_cancel_scan.clicked.connect(self._cancel_nlp_scan)
        h_scan.addWidget(self.btn_cancel_scan)

        h_scan.addStretch()
        ctrl_card.add_layout(h_scan)
        layout.addWidget(ctrl_card)

        # Progress Bar & Status
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        layout.addWidget(self.lbl_status)

        # Results Table
        self.nlp_table = QTableWidget(0, 8)
        self.nlp_table.setHorizontalHeaderLabels(["Sintagma", "Parole", "Lettere", "Sweet Spot", "Score", "Fonte", "Riga", "Contesto"])
        self.nlp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.nlp_table)

        # Export Buttons
        export_layout = QHBoxLayout()
        self.btn_export_csv = QPushButton("Esporta CSV (Excel BOM)")
        self.btn_export_csv.setProperty("class", "SecondaryAction")
        self.btn_export_csv.clicked.connect(self._export_nlp_csv)

        self.btn_export_json = QPushButton("Esporta JSON")
        self.btn_export_json.setProperty("class", "SecondaryAction")
        self.btn_export_json.clicked.connect(self._export_nlp_json)

        export_layout.addStretch()
        export_layout.addWidget(self.btn_export_csv)
        export_layout.addWidget(self.btn_export_json)
        layout.addLayout(export_layout)

        self.tabs.addTab(nlp_widget, "🔍 Estrattore Sintagmi (NLP)")

    def _select_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleziona File TXT", "", "Text Files (*.txt)")
        if file_path:
            self.lbl_selected_path.setText(file_path)
            self.selected_path = file_path
            self.is_dir_selected = False

    def _select_dir(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(self, "Seleziona Cartella")
        if dir_path:
            self.lbl_selected_path.setText(dir_path)
            self.selected_path = dir_path
            self.is_dir_selected = True

    def _start_nlp_scan(self) -> None:
        if not hasattr(self, 'selected_path') or not self.selected_path:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima un file o una cartella TXT!")
            return

        if self.nlp_engine is None:
            try:
                self.nlp_engine = NLPEngine()
            except Exception as e:
                QMessageBox.critical(self, "Errore spaCy", str(e))
                return

        params = {
            "min_words": self.spin_min_w.value(),
            "max_words": self.spin_max_w.value(),
            "min_letters": self.spin_min_l.value(),
            "max_letters": self.spin_max_l.value(),
            "sweet_spot_min": self.spin_sweet_min.value(),
            "sweet_spot_max": self.spin_sweet_max.value(),
            "strict_verb_filter": self.chk_strict_verbs.isChecked(),
            "min_score": self.spin_min_score.value(),
            "random_sample": self.chk_random.isChecked(),
            "max_results": 100
        }

        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.btn_start_scan.setEnabled(False)
        self.btn_cancel_scan.setEnabled(True)

        self.scan_thread = NLPScanThread(self.nlp_engine, self.selected_path, self.is_dir_selected, params)
        self.scan_thread.progress_signal.connect(self._on_scan_progress)
        self.scan_thread.log_signal.connect(self._on_scan_log)
        self.scan_thread.finished_signal.connect(self._on_scan_finished)
        self.scan_thread.start()

    def _cancel_nlp_scan(self) -> None:
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.cancel()
            self.lbl_status.setText("Interruzione scansione richiesta...")

    def _on_scan_progress(self, pct: float, msg: str) -> None:
        self.progress_bar.setValue(int(pct * 100))
        self.lbl_status.setText(msg)

    def _on_scan_log(self, msg: str) -> None:
        self.lbl_status.setText(msg)

    def _on_scan_finished(self, results: list) -> None:
        self.nlp_results = results
        self.progress_bar.hide()
        self.btn_start_scan.setEnabled(True)
        self.btn_cancel_scan.setEnabled(False)
        self.lbl_status.setText(f"Scansione completata. Trovati {len(results)} sintagmi.")

        self.nlp_table.setRowCount(len(results))
        for r, item in enumerate(results):
            d = item.to_dict()
            self.nlp_table.setItem(r, 0, QTableWidgetItem(d["Sintagma"]))
            self.nlp_table.setItem(r, 1, QTableWidgetItem(str(d["Parole"])))
            self.nlp_table.setItem(r, 2, QTableWidgetItem(str(d["Lettere"])))
            self.nlp_table.setItem(r, 3, QTableWidgetItem(d["In Sweet Spot"]))
            self.nlp_table.setItem(r, 4, QTableWidgetItem(str(d["Score"])))
            self.nlp_table.setItem(r, 5, QTableWidgetItem(d["Opera / Fonte"]))
            self.nlp_table.setItem(r, 6, QTableWidgetItem(str(d["Riga"])))
            self.nlp_table.setItem(r, 7, QTableWidgetItem(d["Contesto"]))

    def _export_nlp_csv(self) -> None:
        if not self.nlp_results:
            QMessageBox.information(self, "Info", "Nessun risultato da esportare.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Salva CSV", "sintagmi_rebus.csv", "CSV Files (*.csv)")
        if path:
            DataExporter.export_to_csv(self.nlp_results, path)
            QMessageBox.information(self, "Successo", f"Risultati esportati in: {path}")

    def _export_nlp_json(self) -> None:
        if not self.nlp_results:
            QMessageBox.information(self, "Info", "Nessun risultato da esportare.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Salva JSON", "sintagmi_rebus.json", "JSON Files (*.json)")
        if path:
            DataExporter.export_to_json(self.nlp_results, path)
            QMessageBox.information(self, "Successo", f"Risultati esportati in: {path}")

    # --- Sub-tab 2: Anarebus & Regole d'Oro (Full Richness from Indovinista) ---
    def _build_anarebus_tab(self) -> None:
        anarebus_widget = QWidget()
        layout = QVBoxLayout(anarebus_widget)

        input_card = OdooCard(
            title="🧩 Valutatore Anarebus & Regole d'Oro",
            subtitle="Valuta l'Equazione Perfetta, il Rimescolamento (Difetto di Radice), l'Innocenza Visiva e la Fluidezza Grammaticale."
        )

        grid_inputs = QHBoxLayout()
        v_keys = QVBoxLayout()
        v_keys.addWidget(QLabel("Chiavi / Prima Lettura (es: DITO ROSA):"))
        self.txt_keys = QLineEdit()
        self.txt_keys.textChanged.connect(self._on_anarebus_input_changed)
        v_keys.addWidget(self.txt_keys)

        v_sol = QVBoxLayout()
        v_sol.addWidget(QLabel("Frase Risolutiva (es: RIDATO SO):"))
        self.txt_sol = QLineEdit()
        self.txt_sol.textChanged.connect(self._on_anarebus_input_changed)
        v_sol.addWidget(self.txt_sol)

        grid_inputs.addLayout(v_keys)
        grid_inputs.addLayout(v_sol)
        input_card.add_layout(grid_inputs)
        layout.addWidget(input_card)

        # Letter Difference Assistant Widget
        self.letter_diff_widget = LetterDiffWidget()
        layout.addWidget(self.letter_diff_widget)

        # Evaluation Output Card
        self.eval_card = OdooCard(title="🏆 Esito Valutazione Regole d'Oro")
        self.lbl_eval_score = QLabel("Punteggio Qualità: -")
        self.lbl_eval_score.setStyleSheet("font-size: 16px; font-weight: bold; color: #017E84;")
        self.lbl_eval_badge = QLabel("-")
        self.lbl_eval_rimescolamento = QLabel("Rimescolamento: -")
        self.lbl_eval_innocence = QLabel("Innocenza Immagine: -")
        self.lbl_eval_grammar = QLabel("Fluidezza Grammaticale: -")

        self.eval_card.add_widget(self.lbl_eval_score)
        self.eval_card.add_widget(self.lbl_eval_badge)
        self.eval_card.add_widget(self.lbl_eval_rimescolamento)
        self.eval_card.add_widget(self.lbl_eval_innocence)
        self.eval_card.add_widget(self.lbl_eval_grammar)
        layout.addWidget(self.eval_card)

        # Parametric Generator Box
        gen_card = OdooCard(title="⚡ Generatore & Solutore Parametrico")
        h_gen_params = QHBoxLayout()

        h_gen_params.addWidget(QLabel("Lettere Extra ammesse:"))
        self.spin_extra_letters = QSpinBox()
        self.spin_extra_letters.setRange(0, 5)
        self.spin_extra_letters.setValue(0)
        h_gen_params.addWidget(self.spin_extra_letters)

        h_gen_params.addWidget(QLabel("Max Parole Soluzione:"))
        self.spin_max_sol_words = QSpinBox()
        self.spin_max_sol_words.setRange(2, 6)
        self.spin_max_sol_words.setValue(4)
        h_gen_params.addWidget(self.spin_max_sol_words)

        self.chk_deep_search = QCheckBox("Ricerca Profonda (Deep Search)")
        self.chk_deep_search.setChecked(True)
        h_gen_params.addWidget(self.chk_deep_search)

        gen_card.add_layout(h_gen_params)

        btn_layout = QHBoxLayout()
        btn_decomp = QPushButton("Scomponi Soluzione in Prima Lettura")
        btn_decomp.setProperty("class", "SecondaryAction")
        btn_decomp.clicked.connect(self._decompose_solution)

        btn_solve = QPushButton("Genera Soluzioni da Prima Lettura")
        btn_solve.setProperty("class", "PrimaryAction")
        btn_solve.clicked.connect(self._solve_from_keys)

        btn_layout.addWidget(btn_decomp)
        btn_layout.addWidget(btn_solve)
        gen_card.add_layout(btn_layout)
        layout.addWidget(gen_card)

        # Action Results Table
        self.anarebus_table = QTableWidget(0, 4)
        self.anarebus_table.setHorizontalHeaderLabels(["Chiavi", "Soluzione", "Score", "Badge / Rimescolamento"])
        self.anarebus_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.anarebus_table)

        self.tabs.addTab(anarebus_widget, "🧩 Anarebus & Regole d'Oro")

    def _on_anarebus_input_changed(self) -> None:
        keys_text = self.txt_keys.text()
        sol_text = self.txt_sol.text()
        if not keys_text.strip() or not sol_text.strip():
            return

        eval_res = self.anarebus_engine.evaluate_anarebus(keys_text, sol_text)
        self.letter_diff_widget.update_diff(eval_res.missing_letters, eval_res.surplus_letters, eval_res.is_perfect_anagram)

        self.lbl_eval_score.setText(f"Punteggio Qualità: {eval_res.overall_quality_score} / 10.0")
        self.lbl_eval_badge.setText(eval_res.length_status_badge)
        self.lbl_eval_rimescolamento.setText(f"Rimescolamento: {eval_res.rimescolamento_rating}")
        self.lbl_eval_innocence.setText(f"Innocenza Immagine: {eval_res.innocence_feedback}")
        self.lbl_eval_grammar.setText(f"Fluidezza Grammaticale: {eval_res.grammar_feedback}")

    def _decompose_solution(self) -> None:
        sol_text = self.txt_sol.text()
        if not sol_text.strip():
            QMessageBox.warning(self, "Attenzione", "Inserisci la frase risolutiva!")
            return

        results = self.anarebus_engine.decompose_solution(sol_text)
        self.anarebus_table.setRowCount(len(results))
        for r, res in enumerate(results):
            self.anarebus_table.setItem(r, 0, QTableWidgetItem(res["keys_text"]))
            self.anarebus_table.setItem(r, 1, QTableWidgetItem(res["solution_text"]))
            self.anarebus_table.setItem(r, 2, QTableWidgetItem(str(res["score"])))
            self.anarebus_table.setItem(r, 3, QTableWidgetItem(res["rimescolamento"]))

    def _solve_from_keys(self) -> None:
        keys_text = self.txt_keys.text()
        if not keys_text.strip():
            QMessageBox.warning(self, "Attenzione", "Inserisci le chiavi di prima lettura!")
            return

        results = self.anarebus_engine.solve_from_keys(
            keys_text,
            extra_letters_allowed=self.spin_extra_letters.value(),
            max_words=self.spin_max_sol_words.value(),
            deep_search=self.chk_deep_search.isChecked()
        )
        self.anarebus_table.setRowCount(len(results))
        for r, res in enumerate(results):
            self.anarebus_table.setItem(r, 0, QTableWidgetItem(res["keys_text"]))
            self.anarebus_table.setItem(r, 1, QTableWidgetItem(res["solution_text"]))
            self.anarebus_table.setItem(r, 2, QTableWidgetItem(str(res["score"])))
            self.anarebus_table.setItem(r, 3, QTableWidgetItem(res["badge"]))

    # --- Sub-tab 3: Rebus Stereoscopici (Motore Linguistico AI) ---
    def _build_stereorebus_tab(self) -> None:
        stereo_widget = QWidget()
        layout = QVBoxLayout(stereo_widget)

        card = OdooCard(
            title="🔄 Motore Linguistico per Rebus Stereoscopici (Stereorebus)",
            subtitle="Progetta la struttura linguistica differenziale di uno stereorebus basata su verbi al passato/futuro (3ª persona) e soggetti visivi."
        )

        # Mode A: Top-Down (Soluzione -> Prima Lettura)
        grp_topdown = QGroupBox("Modalità A: Generazione da Seconda Lettura (Top-Down)")
        v_topdown = QVBoxLayout(grp_topdown)
        h_td = QHBoxLayout()
        h_td.addWidget(QLabel("Frase Risolutiva / Seconda Lettura:"))
        self.txt_stereo_sol = QLineEdit()
        self.txt_stereo_sol.setPlaceholderText("Es: UN INTENSA EMOZIONE")
        h_td.addWidget(self.txt_stereo_sol)

        btn_gen_stereo = QPushButton("⚡ Genera Combinazioni Stereorebus")
        btn_gen_stereo.setProperty("class", "PrimaryAction")
        btn_gen_stereo.clicked.connect(self._generate_stereorebus_topdown)
        h_td.addWidget(btn_gen_stereo)
        v_topdown.addLayout(h_td)
        card.add_widget(grp_topdown)

        # Mode B: Bottom-Up (Vignetta A / Vignetta B -> Soluzione)
        grp_bottomup = QGroupBox("Modalità B: Analizzatore Differenziale (Bottom-Up)")
        v_bottomup = QVBoxLayout(grp_bottomup)
        h_bu = QHBoxLayout()
        h_bu.addWidget(QLabel("Vignetta A (Soggetti/Stato):"))
        self.txt_vignette_a = QLineEdit()
        self.txt_vignette_a.setPlaceholderText("Es: PINO CASSA")
        h_bu.addWidget(self.txt_vignette_a)

        h_bu.addWidget(QLabel("Vignetta B (Cambiamento/Azione):"))
        self.txt_vignette_b = QLineEdit()
        self.txt_vignette_b.setPlaceholderText("Es: RECISO SVUOTATA")
        h_bu.addWidget(self.txt_vignette_b)

        btn_analyze_stereo = QPushButton("🔍 Analizza Differenza & Risolvi")
        btn_analyze_stereo.setProperty("class", "SecondaryAction")
        btn_analyze_stereo.clicked.connect(self._analyze_stereorebus_bottomup)
        h_bu.addWidget(btn_analyze_stereo)
        v_bottomup.addLayout(h_bu)
        card.add_widget(grp_bottomup)

        layout.addWidget(card)

        # Results Table for Stereorebus
        self.stereo_table = QTableWidget(0, 6)
        self.stereo_table.setHorizontalHeaderLabels([
            "Prima Lettura (Grafemi + Soggetto + Verbo 3ª pers)",
            "Seconda Lettura",
            "Verbo Azione (Passato/Futuro)",
            "Lettere",
            "Punteggio Qualità (0-100)",
            "Stato / Coerenza"
        ])
        self.stereo_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.stereo_table)

        self.tabs.addTab(stereo_widget, "🔄 Motore Stereorebus")

    def _generate_stereorebus_topdown(self) -> None:
        sol_text = self.txt_stereo_sol.text().strip()
        if not sol_text:
            QMessageBox.warning(self, "Attenzione", "Inserisci la frase di seconda lettura!")
            return

        candidates = self.stereorebus_engine.generate_from_solution(sol_text)
        self._display_stereorebus_results(candidates)

    def _analyze_stereorebus_bottomup(self) -> None:
        va = self.txt_vignette_a.text().strip()
        vb = self.txt_vignette_b.text().strip()
        if not va or not vb:
            QMessageBox.warning(self, "Attenzione", "Inserisci gli elementi di Vignetta A e Vignetta B!")
            return

        candidates = self.stereorebus_engine.analyze_differential_states(va, vb)
        self._display_stereorebus_results(candidates)

    def _display_stereorebus_results(self, candidates: list) -> None:
        self.stereo_table.setRowCount(len(candidates))
        for r, cand in enumerate(candidates):
            self.stereo_table.setItem(r, 0, QTableWidgetItem(cand.keys_text))
            self.stereo_table.setItem(r, 1, QTableWidgetItem(cand.solution_text))
            self.stereo_table.setItem(r, 2, QTableWidgetItem(cand.action_verb))
            self.stereo_table.setItem(r, 3, QTableWidgetItem(str(cand.total_letters)))
            self.stereo_table.setItem(r, 4, QTableWidgetItem(f"{cand.score} / 100"))
            self.stereo_table.setItem(r, 5, QTableWidgetItem(cand.badge))
