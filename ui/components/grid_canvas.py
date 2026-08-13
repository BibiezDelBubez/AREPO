"""
Grid Canvas Component for PySide6.
Provides interactive QTableWidget grid for Crossword puzzles.
"""

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from core.modules.crossword_logic import CrosswordGrid


class CrosswordGridWidget(QTableWidget):
    cell_toggled = Signal(int, int)

    def __init__(self, rows: int = 11, cols: int = 11, parent: QWidget = None):
        super().__init__(rows, cols, parent)
        self.grid_logic = CrosswordGrid(rows, cols)
        
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setSelectionMode(QTableWidget.SingleSelection)
        
        self.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.cellClicked.connect(self._on_cell_clicked)
        self.cellChanged.connect(self._on_cell_changed)
        
        self.refresh_grid_display()

    def set_grid_dimensions(self, rows: int, cols: int) -> None:
        self.setRowCount(rows)
        self.setColumnCount(cols)
        self.grid_logic = CrosswordGrid(rows, cols)
        self.refresh_grid_display()

    def _on_cell_clicked(self, row: int, col: int) -> None:
        # Left click toggle or selection
        pass

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if item and event.button() == Qt.RightButton:
            row = item.row()
            col = item.column()
            self.grid_logic.toggle_black_cell(row, col)
            self.refresh_grid_display()
            self.cell_toggled.emit(row, col)
        super().mousePressEvent(event)

    def _on_cell_changed(self, row: int, col: int) -> None:
        item = self.item(row, col)
        if item:
            val = item.text().strip().upper()
            if val and val != '#':
                self.grid_logic.set_cell_letter(row, col, val[0])

    def refresh_grid_display(self) -> None:
        self.blockSignals(True)
        for r in range(self.grid_logic.rows):
            for c in range(self.grid_logic.cols):
                val = self.grid_logic.grid[r][c]
                item = self.item(r, c)
                if not item:
                    item = QTableWidgetItem()
                    self.setItem(r, c, item)

                item.setTextAlignment(Qt.AlignCenter)
                if val == '#':
                    item.setBackground(QColor("#2C3E50"))
                    item.setForeground(QColor("#2C3E50"))
                    item.setText("#")
                else:
                    item.setBackground(QColor("#FFFFFF"))
                    item.setForeground(QColor("#2C3E50"))
                    item.setText(val if val != ' ' else "")
        self.blockSignals(False)
