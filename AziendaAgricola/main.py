import os
import sys
from PyQt5.QtWidgets import QApplication
from app.repositories import DataRepository
from app.services import AuthService, UserManager
from app.views.login_dialog import LoginDialog
from app.views.main_window import MainWindow

def main() -> int:
    app = QApplication(sys.argv)

    # Inizializzazione Repository e Servizi con percorso assoluto alla cartella data
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    repo = DataRepository(data_dir=data_dir)
    auth_service = AuthService(repo)
    user_manager = UserManager(repo)

    # Finestra di Login / Registrazione iniziale
    login_dialog = LoginDialog(auth_service, user_manager)

    logged_user = None

    def on_login_success(user):
        nonlocal logged_user
        logged_user = user

    login_dialog.login_success.connect(on_login_success)

    if login_dialog.exec() == LoginDialog.DialogCode.Accepted and logged_user:
        window = MainWindow(logged_user, repo, auth_service)
        window.show()
        return app.exec_()

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
