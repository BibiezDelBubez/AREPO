"""
Crossword View for AREPO.
Includes interactive Grid Canvas, Symmetry toggle, Auto-numbering, DFS Solver, and PDF Exporter.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QCheckBox,
    QPushButton, QTableWidget, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from ui.components.odoo_card import OdooCard
from ui.components.grid_canvas import CrosswordGridWidget
from core.engine.dawg_builder import PositionalTrie
from core.modules.crossword_logic import CrosswordSolver
from exporter.pdf_exporter import PDFExporter


class CrosswordView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.trie = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Controls Card
        ctrl_card = OdooCard(
            title="✏️ Editor Cruciverba & Solutore Auto-DFS",
            subtitle="Disegna la griglia (Tasto Destro = casella nera), imposta la simmetria e risolvi automaticamente."
        )

        h_controls = QHBoxLayout()
        h_controls.addWidget(QLabel("Righe:"))
        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(5, 25)
        self.spin_rows.setValue(11)
        h_controls.addWidget(self.spin_rows)

        h_controls.addWidget(QLabel("Colonne:"))
        self.spin_cols = QSpinBox()
        self.spin_cols.setRange(5, 25)
        self.spin_cols.setValue(11)
        h_controls.addWidget(self.spin_cols)

        self.btn_resize = QPushButton("Ridimensiona Griglia")
        self.btn_resize.setProperty("class", "SecondaryAction")
        self.btn_resize.clicked.connect(self._resize_grid)
        h_controls.addWidget(self.btn_resize)

        self.chk_symmetric = QCheckBox("Simmetria 180°")
        self.chk_symmetric.setChecked(True)
        self.chk_symmetric.toggled.connect(self._toggle_symmetry)
        h_controls.addWidget(self.chk_symmetric)

        self.btn_solve = QPushButton("⚡ Auto-Risolvi (DFS)")
        self.btn_solve.setProperty("class", "PrimaryAction")
        self.btn_solve.clicked.connect(self._solve_crossword)
        h_controls.addWidget(self.btn_solve)

        self.btn_export_pdf = QPushButton("📄 Esporta PDF")
        self.btn_export_pdf.setProperty("class", "SecondaryAction")
        self.btn_export_pdf.clicked.connect(self._export_pdf)
        h_controls.addWidget(self.btn_export_pdf)

        ctrl_card.add_layout(h_controls)
        main_layout.addWidget(ctrl_card)

        # Interactive Grid Widget
        self.grid_widget = CrosswordGridWidget(11, 11)
        main_layout.addWidget(self.grid_widget)

    def _resize_grid(self) -> None:
        r = self.spin_rows.value()
        c = self.spin_cols.value()
        self.grid_widget.set_grid_dimensions(r, c)

    def _toggle_symmetry(self, checked: bool) -> None:
        self.grid_widget.grid_logic.symmetric = checked

    def _solve_crossword(self) -> None:
        if self.trie is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            dict_path = os.path.join(base_dir, "data", "dictionaries", "italian_words.txt")
            words = []
            if os.path.exists(dict_path):
                with open(dict_path, encoding="utf-8", errors="ignore") as f:
                    words = [line.strip().upper() for line in f if line.strip()]
            self.trie = PositionalTrie()
            self.trie.populate_from_list(words)

        solver = CrosswordSolver(self.trie)
        solved = solver.solve_grid(self.grid_widget.grid_logic)

        if solved:
            self.grid_widget.refresh_grid_display()
            QMessageBox.information(self, "Successo", "Schema completato con successo!")
        else:
            QMessageBox.warning(self, "Attenzione", "Impossibile trovare una soluzione valida per questa griglia.")

    def _export_pdf(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Salva PDF Cruciverba", "cruciverba.pdf", "PDF Files (*.pdf)")
        if path:
            grid_matrix = self.grid_widget.grid_logic.grid
            ac = [f"{slot.number}. (Orizzontale {slot.length} lettere)" for slot in self.grid_widget.grid_logic.slots_across]
            dn = [f"{slot.number}. (Verticale {slot.length} lettere)" for slot in self.grid_widget.grid_logic.slots_down]

            PDFExporter.export_crossword_pdf(path, "Cruciverba AREPO", grid_matrix, ac, dn, include_solution=True)
            QMessageBox.information(self, "Successo", f"File PDF generato con successo: {path}")
