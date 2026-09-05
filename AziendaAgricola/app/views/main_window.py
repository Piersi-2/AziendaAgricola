from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QMessageBox, QStatusBar, QDateEdit #QStatusBar aggiunge barra sotto
)
from PyQt5.QtCore import QTimer, Qt, QEvent #QTimer aggiunge timer per scadenza sessione
from app.models import Utente, livelloAccesso
from app.repositories import DataRepository
from app.services import AuthService, UserManager, ProductService, FinancialService, ReportService
from app.views.user_management_view import UserManagementView
from app.views.product_view import ProductManagementView
from app.views.movement_view import FinancialMovementView
from app.views.report_view import ReportView

STYLE_MAIN = """
QMainWindow {
    background-color: #ffffff;
    font-family: 'Segoe UI', sans-serif;
}
QWidget {
    background-color: #ffffff;
    color: #000000;
}
QLabel {
    background-color: transparent;
    color: #000000;
}
QTabWidget::pane {
    border: 1px solid #dcdcdc;
    background: #ffffff;
}
QTabBar::tab {
    background-color: #f2f2f2;
    color: #000000;
    border: 1px solid #dcdcdc;
    border-bottom: none;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
    min-width: 120px;
}
QTabBar::tab:selected {
    background-color: #ffffff;
    color: #000000;
    border-bottom: 3px solid #2e7d32;
}
QPushButton {
    background-color: #2e7d32;
    color: #ffffff;
    font-weight: bold;
    border: 1px solid #1b5e20;
    border-radius: 4px;
    padding: 7px 14px;
}
QPushButton:hover {
    background-color: #1b5e20;
}
QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}
QLineEdit, QTextEdit, QComboBox, QDateEdit {
    background-color: #ffffff;
    color: #000000;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 4px;
}
QTableWidget {
    background-color: #ffffff;
    color: #000000;
    gridline-color: #dcdcdc;
    border: 1px solid #dcdcdc;
}
QHeaderView::section {
    background-color: #f2f2f2;
    color: #000000;
    border: 1px solid #dcdcdc;
    padding: 4px;
    font-weight: bold;
}
QGroupBox {
    background-color: #ffffff;
    color: #000000;
    border: 1px solid #dcdcdc;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 3px;
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
        lbl_app_name.setStyleSheet("font-size: 18px; font-weight: bold; color: #1b5e20; background-color: transparent;")

        self.lbl_user_info = QLabel(f"Utente collegato: <b>{self.current_user.nome} {self.current_user.cognome}</b> ({self.current_user.ruolo.value})")
        self.lbl_user_info.setStyleSheet("font-size: 13px; color: #000000; background-color: transparent;")

        btn_logout = QPushButton("Disconnetti (Logout)")
        btn_logout.setStyleSheet("background-color: #757575; color: white; border: 1px solid #616161;")
        btn_logout.clicked.connect(self.handle_logout)

        header_box.addWidget(lbl_app_name)
        header_box.addStretch()
        header_box.addWidget(self.lbl_user_info)
        header_box.addWidget(btn_logout)

        main_layout.addLayout(header_box)

        # Tab Principali
        self.tabs = QTabWidget()

        self.user_view = UserManagementView(self.current_user, self.user_manager, self.auth_service)
        self.product_view = ProductManagementView(self.product_service)
        self.movement_view = FinancialMovementView(self.financial_service, self.product_service, self.current_user)

        self.tabs.addTab(self.user_view, "Gestione Utenti")
        self.tabs.addTab(self.product_view, "Catalogo Prodotti Agricoli")
        self.tabs.addTab(self.movement_view, "Movimenti")

        # Dipendente non deve vedere il guadagno aziendale
        if self.current_user.ruolo == livelloAccesso.MANAGER:
            self.report_view = ReportView(self.report_service)
            self.tabs.addTab(self.report_view, "Guadagno Aziendale")

        # Connetti segnale per aggiornamento del nome in header_box
        self.user_view.profile_updated.connect(self.update_user_header)

        main_layout.addWidget(self.tabs)
        self.setCentralWidget(central)

        # Status Bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.setStyleSheet("background-color: #f2f2f2; color: #000000; border-top: 1px solid #dcdcdc;")
        self.statusBar.showMessage(f"Sessione attiva per l'utente {self.current_user.nomeUtente} | Ultimo Login: {self.current_user.ultimoLogin or 'Oggi'}")

    def update_user_header(self):
        self.lbl_user_info.setText(f"Utente collegato: <b>{self.current_user.nome} {self.current_user.cognome}</b> ({self.current_user.ruolo.value})")
        self.setWindowTitle(f"Azienda Agricola - Gestione Integrata [{self.current_user.nomeUtente} ({self.current_user.ruolo.value})]")

    def init_session_timer(self):
        """Timer di controllo inattività e validità della sessione."""
        self.session_timer = QTimer(self)
        self.session_timer.setInterval(60000)  # Controlla ogni minuto
        self.session_timer.timeout.connect(self.check_session_status)
        self.session_timer.start()

        # Installa il filtro eventi sull'applicazione per intercettare l'interazione utente e resettare l'inattività
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() in (
            QEvent.MouseMove,
            QEvent.MouseButtonPress,
            QEvent.KeyPress,
            QEvent.Wheel,
        ):
            self.auth_service.update_activity()

        # Disabilita la modifica della data tramite rotellina del mouse sui QDateEdit
        if event.type() == QEvent.Wheel:
            parent = getattr(watched, 'parent', lambda: None)()
            if isinstance(watched, QDateEdit) or isinstance(parent, QDateEdit):
                event.ignore()
                return True

        return super().eventFilter(watched, event)

    def closeEvent(self, event):
        app = QApplication.instance()
        if app:
            app.removeEventFilter(self)
        super().closeEvent(event)

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
