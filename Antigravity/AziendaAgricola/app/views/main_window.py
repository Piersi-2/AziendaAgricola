from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QMessageBox, QStatusBar
)
from PyQt6.QtCore import QTimer, Qt
from app.models import Utente
from app.repositories import DataRepository
from app.services import AuthService, UserManager, ProductService, FinancialService, ReportService
from app.views.user_management_view import UserManagementView
from app.views.product_view import ProductManagementView
from app.views.movement_view import FinancialMovementView
from app.views.report_view import ReportAndBackupView

STYLE_MAIN = """
QMainWindow {
    background-color: #f7f9fb;
    font-family: 'Segoe UI', sans-serif;
}
QTabWidget::pane {
    border: 1px solid #dcdcdc;
    background: #ffffff;
    border-radius: 4px;
}
QTabBar::tab {
    background: #e0e0e0;
    color: #333333;
    padding: 10px 18px;
    font-weight: bold;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #2e7d32;
    color: white;
}
QPushButton {
    background-color: #2e7d32;
    color: white;
    font-weight: bold;
    padding: 7px 14px;
    border: none;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #1b5e20;
}
"""

class MainWindow(QMainWindow):
    def __init__(self, current_user: Utente, repo: DataRepository, auth_service: AuthService, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.repo = repo
        self.auth_service = auth_service

        # Servizi
        self.user_manager = UserManager(repo)
        self.product_service = ProductService(repo)
        self.financial_service = FinancialService(repo)
        self.report_service = ReportService(repo)

        self.setWindowTitle(f"Azienda Agricola - Gestione Integrata [{current_user.nomeUtente} ({current_user.ruolo.value})]")
        self.resize(1100, 720)
        self.setStyleSheet(STYLE_MAIN)

        self.init_ui()
        self.init_session_timer()

    def init_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Intestazione Superiore (Barra Utente Attivo)
        header_box = QHBoxLayout()

        lbl_app_name = QLabel("Azienda Agricola")
        lbl_app_name.setStyleSheet("font-size: 18px; font-weight: bold; color: #1b5e20;")

        lbl_user_info = QLabel(f"Utente collegato: <b>{self.current_user.nome} {self.current_user.cognome}</b> ({self.current_user.ruolo.value})")
        lbl_user_info.setStyleSheet("font-size: 13px; color: #333333;")

        btn_logout = QPushButton("Disconnetti (Logout)")
        btn_logout.setStyleSheet("background-color: #757575;")
        btn_logout.clicked.connect(self.handle_logout)

        header_box.addWidget(lbl_app_name)
        header_box.addStretch()
        header_box.addWidget(lbl_user_info)
        header_box.addWidget(btn_logout)

        main_layout.addLayout(header_box)

        # Tab Principali
        self.tabs = QTabWidget()

        self.user_view = UserManagementView(self.current_user, self.user_manager, self.auth_service)
        self.product_view = ProductManagementView(self.product_service)
        self.movement_view = FinancialMovementView(self.financial_service, self.product_service, self.current_user)
        self.report_view = ReportAndBackupView(self.report_service, self.repo)

        self.tabs.addTab(self.user_view, "Gestione Utenti & Profilo")
        self.tabs.addTab(self.product_view, "Catalogo Prodotti Agricoli")
        self.tabs.addTab(self.movement_view, "Entrate & Uscite")
        self.tabs.addTab(self.report_view, "Guadagno Aziendale & Backup")

        main_layout.addWidget(self.tabs)

        self.setCentralWidget(central)

        # Status Bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(f"Sessione attiva per l'utente {self.current_user.nomeUtente} | Ultimo Login: {self.current_user.ultimoLogin or 'Oggi'}")

    def init_session_timer(self):
        """Timer di controllo inattività e validità della sessione."""
        self.session_timer = QTimer(self)
        self.session_timer.setInterval(60000)  # Controlla ogni minuto
        self.session_timer.timeout.connect(self.check_session_status)
        self.session_timer.start()

    def check_session_status(self):
        if not self.auth_service.is_session_valid():
            self.session_timer.stop()
            QMessageBox.warning(self, "Sessione Scaduta", "La sessione di lavoro è scaduta per inattività. Verrai disconnesso.")
            self.close()

    def handle_logout(self):
        confirm = QMessageBox.question(
            self, "Conferma Disconnessione",
            "Sei sicuro di voler effettuare il logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.auth_service.effettuaLogout()
            self.close()
