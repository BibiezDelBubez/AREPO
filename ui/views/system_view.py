"""
System & Dependencies View for AREPO.
Displays installed Python package versions, spaCy models, and provides buttons to install/upgrade via pip.
"""

import sys
import subprocess
import importlib.metadata
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal
from ui.components.odoo_card import OdooCard

REQUIRED_PACKAGES = [
    ("PySide6", "Interfaccia Grafica Qt"),
    ("sqlalchemy", "Database ORM SQLite"),
    ("spacy", "Motore NLP italiano"),
    ("reportlab", "Esportatore PDF vettoriale"),
    ("pandas", "Gestione dati ed esportazione CSV"),
    ("pillow", "Manipolazione immagini"),
    ("greenlet", "Dipendenza SQLAlchemy")
]


class PipInstallerThread(QThread):
    log_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, cmd_args: list):
        super().__init__()
        self.cmd_args = cmd_args

    def run(self):
        cmd = [sys.executable, "-m"] + self.cmd_args
        self.log_signal.emit(f"Esecuzione comando: {' '.join(cmd)}\n")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            for line in process.stdout:
                self.log_signal.emit(line)
            process.wait()

            if process.returncode == 0:
                self.finished_signal.emit(True, "Operazione completata con successo!")
            else:
                self.finished_signal.emit(False, f"Comando terminato con codice di errore {process.returncode}.")
        except Exception as e:
            self.finished_signal.emit(False, f"Errore durante l'esecuzione: {str(e)}")


class SystemView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.installer_thread = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Overview Card
        card = OdooCard(
            title="⚙️ Gestione Dipendenze & Sistema",
            subtitle="Riepilogo delle librerie Python installate e strumenti per l'aggiornamento automatico tramite pip."
        )

        h_btn = QHBoxLayout()
        self.btn_refresh = QPushButton("🔄 Verifica Dipendenze")
        self.btn_refresh.setProperty("class", "SecondaryAction")
        self.btn_refresh.clicked.connect(self.check_dependencies)
        h_btn.addWidget(self.btn_refresh)

        self.btn_upgrade_all = QPushButton("⚡ Aggiorna Tutte le Librerie (pip)")
        self.btn_upgrade_all.setProperty("class", "PrimaryAction")
        self.btn_upgrade_all.clicked.connect(self._upgrade_all_packages)
        h_btn.addWidget(self.btn_upgrade_all)

        self.btn_spacy_model = QPushButton("📥 Scarica Modello spaCy (it_core_news_sm)")
        self.btn_spacy_model.setProperty("class", "SecondaryAction")
        self.btn_spacy_model.clicked.connect(self._download_spacy_model)
        h_btn.addWidget(self.btn_spacy_model)

        h_btn.addStretch()
        card.add_layout(h_btn)
        main_layout.addWidget(card)

        # Dependencies Table
        self.table_deps = QTableWidget(0, 4)
        self.table_deps.setHorizontalHeaderLabels(["Libreria / Modello", "Descrizione", "Versione Installata", "Stato"])
        self.table_deps.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.table_deps)

        # Terminal Output Area
        output_card = OdooCard(title="🖥️ Log Operazioni PIP / Download")
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setPlaceholderText("I log di installazione ed aggiornamento pip verranno mostrati qui...")
        output_card.add_widget(self.txt_log)
        main_layout.addWidget(output_card)

        # Check dependencies on startup
        self.check_dependencies()

    def check_dependencies(self) -> None:
        self.table_deps.setRowCount(0)

        # 1. Python packages
        for pkg_name, desc in REQUIRED_PACKAGES:
            try:
                ver = importlib.metadata.version(pkg_name)
                status = "🟢 Installato"
            except importlib.metadata.PackageNotFoundError:
                ver = "Non installato"
                status = "❌ Mancante"

            r = self.table_deps.rowCount()
            self.table_deps.insertRow(r)
            self.table_deps.setItem(r, 0, QTableWidgetItem(pkg_name))
            self.table_deps.setItem(r, 1, QTableWidgetItem(desc))
            self.table_deps.setItem(r, 2, QTableWidgetItem(ver))
            self.table_deps.setItem(r, 3, QTableWidgetItem(status))

        # 2. Check spaCy model it_core_news_sm
        try:
            import spacy
            has_spacy_model = spacy.util.is_package("it_core_news_sm")
            m_ver = "Installato" if has_spacy_model else "Non installato"
            m_status = "🟢 Presente" if has_spacy_model else "⚠️ Mancante (Necessario per NLP)"
        except Exception:
            m_ver = "Non installato"
            m_status = "❌ Mancante"

        r = self.table_deps.rowCount()
        self.table_deps.insertRow(r)
        self.table_deps.setItem(r, 0, QTableWidgetItem("it_core_news_sm"))
        self.table_deps.setItem(r, 1, QTableWidgetItem("Modello di Lingua Italiana spaCy"))
        self.table_deps.setItem(r, 2, QTableWidgetItem(m_ver))
        self.table_deps.setItem(r, 3, QTableWidgetItem(m_status))

    def _upgrade_all_packages(self) -> None:
        pkgs = [p[0] for p in REQUIRED_PACKAGES]
        cmd_args = ["pip", "install", "--upgrade"] + pkgs
        self._run_pip_cmd(cmd_args)

    def _download_spacy_model(self) -> None:
        cmd_args = ["spacy", "download", "it_core_news_sm"]
        self._run_pip_cmd(cmd_args)

    def _run_pip_cmd(self, cmd_args: list) -> None:
        self.txt_log.clear()
        self.btn_upgrade_all.setEnabled(False)
        self.btn_spacy_model.setEnabled(False)

        self.installer_thread = PipInstallerThread(cmd_args)
        self.installer_thread.log_signal.connect(self._append_log)
        self.installer_thread.finished_signal.connect(self._on_pip_finished)
        self.installer_thread.start()

    def _append_log(self, text: str) -> None:
        self.txt_log.append(text.strip())

    def _on_pip_finished(self, success: bool, msg: str) -> None:
        self.btn_upgrade_all.setEnabled(True)
        self.btn_spacy_model.setEnabled(True)
        self._append_log(f"\n>>> {msg}\n")
        self.check_dependencies()

        if success:
            QMessageBox.information(self, "Successo", msg)
        else:
            QMessageBox.warning(self, "Attenzione", msg)
