from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox, QFormLayout,
    QHeaderView, QTextEdit, QDialog, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from app.services import UserManager, AuthService
from app.models import Utente, Manager, Dipendente, livelloAccesso

class UserManagementView(QWidget):
    profile_updated = pyqtSignal()  # Segnale per notificare modifiche al proprio profilo

    def __init__(self, current_user: Utente, user_manager: UserManager, auth_service: AuthService, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.user_manager = user_manager
        self.auth_service = auth_service
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Sezione il mio profilo
        profile_box = QGroupBox(f"Il Mio Profilo ({self.current_user.ruolo.value})")
        profile_form = QFormLayout(profile_box)

        self.p_nome = QLineEdit(self.current_user.nome)
        self.p_cognome = QLineEdit(self.current_user.cognome)
        self.p_email = QLineEdit(self.current_user.email)
        self.p_telefono = QLineEdit(self.current_user.telefono)
        self.p_nascita = QLineEdit(self.current_user.dataNascita)
        self.p_password = QLineEdit()
        self.p_password.setPlaceholderText("Lascia vuoto se inalterata")
        self.p_password.setEchoMode(QLineEdit.EchoMode.Password)

        profile_form.addRow("Nome:", self.p_nome)
        profile_form.addRow("Cognome:", self.p_cognome)
        profile_form.addRow("Email:", self.p_email)
        profile_form.addRow("Telefono:", self.p_telefono)
        profile_form.addRow("Data Nascita:", self.p_nascita)
        profile_form.addRow("Nuova Password:", self.p_password)

        btn_update_profile = QPushButton("Salva Modifiche Profilo")
        btn_update_profile.clicked.connect(self.handle_update_self)
        profile_form.addRow("", btn_update_profile)

        main_layout.addWidget(profile_box)

        # Se Manager: Gestione Dipendenti e Cronologia Login
        if isinstance(self.current_user, Manager):
            manager_box = QGroupBox("Gestione Utenti e Dipendenti (Riservato Manager)")
            m_layout = QVBoxLayout(manager_box)

            # Bottoni per azioni
            top_bar = QHBoxLayout()
            btn_add_user = QPushButton("+ Crea Nuovo Profilo Dipendente")
            btn_add_user.clicked.connect(self.show_create_user_dialog)

            btn_edit_user = QPushButton("Modifica Profilo Dipendente")
            btn_edit_user.setStyleSheet("background-color: #c88a00; color: white; border: 1px solid #a87400;")
            btn_edit_user.clicked.connect(self.show_edit_user_dialog)

            btn_del_user = QPushButton("- Elimina Profilo Dipendente")
            btn_del_user.setStyleSheet("background-color: #ff5858; color: white; border: 1px solid #ff5858;")
            btn_del_user.clicked.connect(self.handle_delete_user)

            btn_login_hist = QPushButton("Visualizza Cronologia Login Dipendenti")
            btn_login_hist.setStyleSheet("background-color: #3ac5ff; color: white; border: 1px solid #3ac5ff;")
            btn_login_hist.clicked.connect(self.show_login_history_dialog)

            top_bar.addWidget(btn_add_user)
            top_bar.addWidget(btn_edit_user)
            top_bar.addWidget(btn_del_user)
            top_bar.addWidget(btn_login_hist)
            m_layout.addLayout(top_bar)

            # Tabella Utenti
            self.users_table = QTableWidget()
            self.users_table.setColumnCount(7)
            self.users_table.setHorizontalHeaderLabels([
                "ID", "Username", "Ruolo", "Nome", "Cognome", "Email", "Ultimo Login"
            ])
            self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
            # Disabilita modifica diretta dei campi
            self.users_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            
            m_layout.addWidget(self.users_table)

            main_layout.addWidget(manager_box)
            self.load_users_table()

    def load_users_table(self):
        if not hasattr(self, 'users_table'):
            return

        users = self.user_manager.get_all_users()
        self.users_table.setRowCount(len(users))

        for idx, u in enumerate(users):
            self.users_table.setItem(idx, 0, QTableWidgetItem(u.id))
            self.users_table.setItem(idx, 1, QTableWidgetItem(u.nomeUtente))
            self.users_table.setItem(idx, 2, QTableWidgetItem(u.ruolo.value))
            self.users_table.setItem(idx, 3, QTableWidgetItem(u.nome))
            self.users_table.setItem(idx, 4, QTableWidgetItem(u.cognome))
            self.users_table.setItem(idx, 5, QTableWidgetItem(u.email))
            self.users_table.setItem(idx, 6, QTableWidgetItem(u.ultimoLogin or "Mai connesso"))

    def handle_update_self(self):
        nome = self.p_nome.text().strip()
        cognome = self.p_cognome.text().strip()
        email = self.p_email.text().strip()
        telefono = self.p_telefono.text().strip()
        data_nascita = self.p_nascita.text().strip()
        pwd = self.p_password.text().strip() or None

        if not all([nome, cognome, email]):
            QMessageBox.warning(self, "Attenzione", "Nome, cognome ed email sono obbligatori.")
            return

        try:
            self.user_manager.modifica_profilo(
                user_id=self.current_user.id,
                nome=nome,
                cognome=cognome,
                email=email,
                telefono=telefono,
                dataNascita=data_nascita,
                password=pwd
            )
            
            # Aggiorna i dati in memoria dell'utente connesso
            self.current_user.nome = self.p_nome.text().strip()
            self.current_user.cognome = self.p_cognome.text().strip()
            self.current_user.email = self.p_email.text().strip()
            self.current_user.telefono = self.p_telefono.text().strip()
            self.current_user.dataNascita = self.p_nascita.text().strip()
            if pwd:
                self.current_user.password = pwd

            QMessageBox.information(self, "Successo", "Profilo aggiornato con successo!")
            self.p_password.clear()
            self.profile_updated.emit() # Notifica MainWindow per cambiare l'header
            self.load_users_table()
        except Exception as e:
            QMessageBox.critical(self, "Errore Aggiornamento", str(e))

    def show_create_user_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Crea Nuovo Profilo Utente")
        dlg.setFixedSize(380, 360)
        layout = QVBoxLayout(dlg)

        form = QFormLayout()
        u_username = QLineEdit()
        u_password = QLineEdit()
        u_password.setEchoMode(QLineEdit.EchoMode.Password)
        u_nome = QLineEdit()
        u_cognome = QLineEdit()
        u_email = QLineEdit()
        u_telefono = QLineEdit()
        u_nascita = QLineEdit()
        u_nascita.setPlaceholderText("YYYY-MM-DD")

        form.addRow("Username:", u_username)
        form.addRow("Password (min 8 alfanum):", u_password)
        form.addRow("Nome:", u_nome)
        form.addRow("Cognome:", u_cognome)
        form.addRow("Email:", u_email)
        form.addRow("Telefono:", u_telefono)
        form.addRow("Data Nascita:", u_nascita)

        layout.addLayout(form)

        btn = QPushButton("Crea Dipendente")
        def create_action():
            try:
                self.user_manager.crea_dipendente(
                    username=u_username.text().strip(),
                    password=u_password.text(),
                    nome=u_nome.text().strip(),
                    cognome=u_cognome.text().strip(),
                    email=u_email.text().strip(),
                    telefono=u_telefono.text().strip(),
                    dataNascita=u_nascita.text().strip()
                )
                QMessageBox.information(dlg, "Successo", "Profilo dipendente creato!")
                self.load_users_table()
                dlg.accept()
            except Exception as e:
                QMessageBox.critical(dlg, "Errore", str(e))

        btn.clicked.connect(create_action)
        layout.addWidget(btn)
        dlg.exec()

    def show_edit_user_dialog(self):
        row = self.users_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Attenzione", "Selezionare un utente dalla tabella degli utenti.")
            return

        uid = self.users_table.item(row, 0).text()
        users = self.user_manager.get_all_users()
        target = next((u for u in users if u.id == uid), None)
        if not target:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Modifica Profilo Dipendente")
        dlg.setFixedSize(380, 360)
        layout = QVBoxLayout(dlg)

        form = QFormLayout()
        u_nome = QLineEdit(target.nome)
        u_cognome = QLineEdit(target.cognome)
        u_email = QLineEdit(target.email)
        u_telefono = QLineEdit(target.telefono)
        u_nascita = QLineEdit(target.dataNascita)
        u_password = QLineEdit()
        u_password.setPlaceholderText("Lascia vuoto se inalterata")
        u_password.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow("Nome:", u_nome)
        form.addRow("Cognome:", u_cognome)
        form.addRow("Email:", u_email)
        form.addRow("Telefono:", u_telefono)
        form.addRow("Data Nascita:", u_nascita)
        form.addRow("Nuova Password:", u_password)

        layout.addLayout(form)

        btn = QPushButton("Salva Modifiche")
        def save_action():
            try:
                pwd = u_password.text().strip() or None
                self.user_manager.modifica_profilo(
                    user_id=uid,
                    nome=u_nome.text().strip(),
                    cognome=u_cognome.text().strip(),
                    email=u_email.text().strip(),
                    telefono=u_telefono.text().strip(),
                    dataNascita=u_nascita.text().strip(),
                    password=pwd
                )

                # Se e l'utente corrente in sessione, aggiorna in memoria e aggiorna la UI
                if uid == self.current_user.id:
                    self.current_user.nome = u_nome.text().strip()
                    self.current_user.cognome = u_cognome.text().strip()
                    self.current_user.email = u_email.text().strip()
                    self.current_user.telefono = u_telefono.text().strip()
                    self.current_user.dataNascita = u_nascita.text().strip()
                    if pwd:
                        self.current_user.password = pwd
                    
                    self.p_nome.setText(self.current_user.nome)
                    self.p_cognome.setText(self.current_user.cognome)
                    self.p_email.setText(self.current_user.email)
                    self.p_telefono.setText(self.current_user.telefono)
                    self.p_nascita.setText(self.current_user.dataNascita)
                    
                    self.profile_updated.emit()

                QMessageBox.information(dlg, "Successo", "Profilo modificato con successo!")
                self.load_users_table()
                dlg.accept()
            except Exception as e:
                QMessageBox.critical(dlg, "Errore", str(e))

        btn.clicked.connect(save_action)
        layout.addWidget(btn)
        dlg.exec()

    def handle_delete_user(self):
        row = self.users_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Attenzione", "Selezionare una riga dalla tabella degli utenti.")
            return

        user_id = self.users_table.item(row, 0).text()
        username = self.users_table.item(row, 1).text()

        confirm = QMessageBox.question(
            self, "Conferma Eliminazione",
            f"Sei sicuro di voler eliminare definitivamente il profilo '{username}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.user_manager.elimina_dipendente(user_id)
                QMessageBox.information(self, "Successo", "Profilo eliminato con successo.")
                self.load_users_table()
            except Exception as e:
                QMessageBox.critical(self, "Errore", str(e))

    def show_login_history_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Cronologia Login Utenti (Manager View)")
        dlg.resize(500, 400)
        layout = QVBoxLayout(dlg)

        hist = self.auth_service.get_login_history()
        txt = QTextEdit()
        txt.setReadOnly(True)

        log_str = "========================================\nCRONOLOGIA LOGIN E ULTIME SESSIONI\n========================================\n\n"
        for uname, logins in hist.items():
            log_str += f"Utente: {uname}\n"
            for l in reversed(logins[-10:]):  # Ultimi 10 login
                log_str += f"  - {l}\n"
            log_str += "\n"

        txt.setPlainText(log_str)
        layout.addWidget(txt)
        dlg.exec()
