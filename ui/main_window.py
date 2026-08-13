"""
Main Window (Root Window) for AREPO (Enigmistica Suite).
Includes Odoo-style Dark Sidebar Drawer, Topbar with Breadcrumbs, and Stacked View Navigation.
"""

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame,
    QLabel, QPushButton, QStackedWidget, QApplication
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont

from ui.views.dashboard_view import DashboardView
from ui.views.rebus_view import RebusView
from ui.views.verse_view import VerseView
from ui.views.crossword_view import CrosswordView
from ui.views.dictionary_view import DictionaryView
from ui.views.system_view import SystemView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AREPO - Enigmistica Suite")
        self.resize(1280, 850)
        self.setMinimumSize(1100, 720)

        # Load QSS Style Sheet
        self._load_stylesheet()

        # Root Central Widget
        root_widget = QWidget()
        self.setCentralWidget(root_widget)

        root_layout = QHBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Sidebar Drawer
        self.sidebar = QFrame()
        self.sidebar.setObjectName("SidebarDrawer")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(4)

        # Sidebar Header / Logo
        header_lbl = QLabel("🎯 AREPO SUITE")
        header_lbl.setObjectName("SidebarHeader")
        sidebar_layout.addWidget(header_lbl)

        # Navigation Buttons
        self.btn_dashboard = self._create_sidebar_btn("🏠 Dashboard", "dashboard")
        self.btn_rebus = self._create_sidebar_btn("🧩 Rebus & Anarebus", "rebus")
        self.btn_verse = self._create_sidebar_btn("📜 Giochi in Versi", "verse")
        self.btn_cross = self._create_sidebar_btn("✏️ Cruciverba", "crossword")
        self.btn_dict = self._create_sidebar_btn("🔤 Dizionario", "dictionary")
        self.btn_system = self._create_sidebar_btn("⚙️ Dipendenze & Sistema", "system")

        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_rebus)
        sidebar_layout.addWidget(self.btn_verse)
        sidebar_layout.addWidget(self.btn_cross)
        sidebar_layout.addWidget(self.btn_dict)
        sidebar_layout.addWidget(self.btn_system)
        sidebar_layout.addStretch()

        root_layout.addWidget(self.sidebar)

        # 2. Right Main Content Area (Topbar + Stacked Views)
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top Bar
        topbar = QFrame()
        topbar.setObjectName("TopBar")
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(16, 0, 16, 0)

        self.breadcrumb_lbl = QLabel("Dashboard")
        self.breadcrumb_lbl.setObjectName("BreadcrumbLabel")

        db_status_lbl = QLabel("🟢 DB Dual-Layer Attivo (280k parole)")
        db_status_lbl.setStyleSheet("color: #27AE60; font-weight: bold; font-size: 12px;")

        topbar_layout.addWidget(self.breadcrumb_lbl)
        topbar_layout.addStretch()
        topbar_layout.addWidget(db_status_lbl)

        content_layout.addWidget(topbar)

        # Stacked Views Widget
        self.stacked_widget = QStackedWidget()

        self.view_dashboard = DashboardView()
        self.view_dashboard.navigate_requested.connect(self._navigate_by_name)

        self.view_rebus = RebusView()
        self.view_verse = VerseView()
        self.view_crossword = CrosswordView()
        self.view_dictionary = DictionaryView()
        self.view_system = SystemView()

        self.stacked_widget.addWidget(self.view_dashboard)    # Index 0
        self.stacked_widget.addWidget(self.view_rebus)        # Index 1
        self.stacked_widget.addWidget(self.view_verse)        # Index 2
        self.stacked_widget.addWidget(self.view_crossword)    # Index 3
        self.stacked_widget.addWidget(self.view_dictionary)   # Index 4
        self.stacked_widget.addWidget(self.view_system)       # Index 5

        content_layout.addWidget(self.stacked_widget)
        root_layout.addWidget(content_area)

        # Set default view
        self._navigate_to(0, "Dashboard", self.btn_dashboard)

    def _create_sidebar_btn(self, text: str, page_name: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("SidebarButton")
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self._navigate_by_name(page_name))
        return btn

    def _navigate_by_name(self, page_name: str) -> None:
        nav_map = {
            "dashboard": (0, "Dashboard", self.btn_dashboard),
            "rebus": (1, "Rebus & Anarebus", self.btn_rebus),
            "verse": (2, "Giochi in Versi", self.btn_verse),
            "crossword": (3, "Cruciverba & Derivati", self.btn_cross),
            "dictionary": (4, "Dizionario & Ricerca Parole", self.btn_dict),
            "system": (5, "Gestione Dipendenze & Sistema", self.btn_system)
        }
        if page_name in nav_map:
            idx, title, btn = nav_map[page_name]
            self._navigate_to(idx, title, btn)

    def _navigate_to(self, index: int, title: str, active_btn: QPushButton) -> None:
        self.stacked_widget.setCurrentIndex(index)
        self.breadcrumb_lbl.setText(title)

        for btn in [self.btn_dashboard, self.btn_rebus, self.btn_verse, self.btn_cross, self.btn_dict, self.btn_system]:
            btn.setChecked(btn == active_btn)

    def _load_stylesheet(self) -> None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        qss_path = os.path.join(base_dir, "assets", "odoo_style.qss")
        if os.path.exists(qss_path):
            with open(qss_path, encoding="utf-8") as f:
                self.setStyleSheet(f.read())
