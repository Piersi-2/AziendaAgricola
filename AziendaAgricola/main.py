import os
import sys
from PyQt5.QtWidgets import QApplication
from app.repositories import DataRepository
from app.services import AuthService, UserManager
from app.views.login_dialog import LoginDialog
from app.views.main_window import MainWindow

def main() -> int:
    app = QApplication(sys.argv)

    # Prende percorso relativo ai JSON e chiama repository
    base_dir = os.path.dirname(os.path.abspath(__file__))   #__file__ è il file corrente main.py
    data_dir = os.path.join(base_dir, "data")
    repo = DataRepository(data_dir=data_dir)        # 1) Nome del parametro in DataRepository(), 2) Nome della variabile in main()
    auth_service = AuthService(repo)
    user_manager = UserManager(repo)

    # Finestra di Login / Registrazione iniziale
    login_dialog = LoginDialog(auth_service, user_manager)

    logged_user = None

    def on_login_success(user):
        nonlocal logged_user    # Prende la variabile globale
        logged_user = user

    login_dialog.login_success.connect(on_login_success)    # Connette l'utente emesso (login_dialog, ln 192)

    if login_dialog.exec() == LoginDialog.DialogCode.Accepted and logged_user:  # Si ha "Accepted" grazie a self.accept()
        window = MainWindow(logged_user, repo, auth_service)
        window.show()
        return app.exec_()  # Esecuzione ciclo eventi Qt

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
