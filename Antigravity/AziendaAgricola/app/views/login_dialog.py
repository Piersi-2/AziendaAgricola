from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QStackedWidget, QWidget, QFormLayout, QGroupBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from app.services import AuthService, UserManager
from app.models import Utente

# Palette di base pulita e minimale - Nero su Bianco
STYLE_LOGIN = """
QDialog {
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
    font-size: 13px;
}
QLabel#TitleLabel {
    font-size: 20px;
    font-weight: bold;
    color: #1b5e20;
}
QLineEdit {
    padding: 8px;
    border: 1px solid #cccccc;
    border-radius: 4px;
    background-color: #ffffff;
    color: #000000;
    font-size: 13px;
}
QLineEdit:focus {
    border: 1px solid #2e7d32;
}
QPushButton {
    background-color: #2e7d32;
    color: white;
    font-weight: bold;
    padding: 9px 15px;
    border: none;
    border-radius: 4px;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #1b5e20;
}
QPushButton#SecondaryButton {
    background-color: #757575;
    color: white;
}
QPushButton#SecondaryButton:hover {
    background-color: #616161;
}
QGroupBox {
    background-color: #ffffff;
    color: #000000;
    border: 1px solid #dcdcdc;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 15px;
    font-weight: bold;
}
"""

class LoginDialog(QDialog):
    login_success = pyqtSignal(object)  # Emette l'oggetto Utente autenticato

    def __init__(self, auth_service: AuthService, user_manager: UserManager, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.user_manager = user_manager
        self.setWindowTitle("Azienda Agricola - Autenticazione")
        self.setFixedSize(440, 480)
        self.setStyleSheet(STYLE_LOGIN)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 25, 30, 25)

        # Intestazione
        title = QLabel("Azienda Agricola")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Gestione Entrate, Uscite e Guadagno Aziendale")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666666; font-size: 12px; margin-bottom: 15px; background-color: transparent;")

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # Stack per passare tra Login e Registrazione Primo Manager
        self.stacked_widget = QStackedWidget()
        self.login_widget = self.create_login_widget()
        self.first_manager_widget = self.create_first_manager_widget()

        self.stacked_widget.addWidget(self.login_widget)
        self.stacked_widget.addWidget(self.first_manager_widget)

        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

        # Se non esistono manager registrati, mostra la schermata di registrazione iniziale
        if not self.user_manager.ha_manager():
            self.stacked_widget.setCurrentWidget(self.first_manager_widget)
        else:
            self.stacked_widget.setCurrentWidget(self.login_widget)

    def create_login_widget(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Accesso Utente")
        form = QFormLayout(group)
        form.setSpacing(12)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nome utente")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow("Username:", self.username_input)
        form.addRow("Password:", self.password_input)

        layout.addWidget(group)

        # Bottoni
        btn_login = QPushButton("Accedi")
        btn_login.clicked.connect(self.handle_login)

        layout.addWidget(btn_login)
        layout.addStretch()
        return widget

    def create_first_manager_widget(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Inizializzazione Sistema - Registrazione Manager")
        form = QFormLayout(group)
        form.setSpacing(8)

        self.m_username = QLineEdit()
        self.m_password = QLineEdit()
        self.m_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.m_nome = QLineEdit()
        self.m_cognome = QLineEdit()
        self.m_email = QLineEdit()
        self.m_telefono = QLineEdit()
        self.m_data_nascita = QLineEdit()
        self.m_data_nascita.setPlaceholderText("YYYY-MM-DD")

        form.addRow("Username:", self.m_username)
        form.addRow("Password (min 8 alfanum):", self.m_password)
        form.addRow("Nome:", self.m_nome)
        form.addRow("Cognome:", self.m_cognome)
        form.addRow("Email:", self.m_email)
        form.addRow("Telefono:", self.m_telefono)
        form.addRow("Data Nascita:", self.m_data_nascita)

        layout.addWidget(group)

        btn_register = QPushButton("Registra Manager Iniziale")
        btn_register.clicked.connect(self.handle_register_first_manager)

        layout.addWidget(btn_register)
        return widget

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Attenzione", "Inserire nome utente e password.")
            return

        try:
            user = self.auth_service.effettuaLogin(username, password)
            self.login_success.emit(user)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Errore Autenticazione", str(e))

    def handle_register_first_manager(self):
        username = self.m_username.text().strip()
        password = self.m_password.text()
        nome = self.m_nome.text().strip()
        cognome = self.m_cognome.text().strip()
        email = self.m_email.text().strip()
        telefono = self.m_telefono.text().strip()
        data_nascita = self.m_data_nascita.text().strip()

        if not all([username, password, nome, cognome, email]):
            QMessageBox.warning(self, "Attenzione", "Compilare tutti i campi obbligatori.")
            return

        try:
            manager = self.user_manager.registra_primo_manager(
                username=username,
                password=password,
                nome=nome,
                cognome=cognome,
                email=email,
                telefono=telefono,
                dataNascita=data_nascita or "1990-01-01"
            )
            QMessageBox.information(self, "Successo", f"Profilo Manager '{manager.nomeUtente}' creato con successo! Ora puoi accedere.")
            self.stacked_widget.setCurrentWidget(self.login_widget)
            self.username_input.setText(username)
        except Exception as e:
            QMessageBox.critical(self, "Errore Registrazione", str(e))


