import unittest
import tempfile
import shutil
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QDate

from app.repositories import DataRepository
from app.services import AuthService, UserManager, ProductService, FinancialService, ReportService
from app.models import Manager, Dipendente, livelloAccesso
from app.views.main_window import MainWindow
from app.views.product_view import ProductManagementView
from app.views.movement_view import FinancialMovementView
from app.views.user_management_view import UserManagementView
from app.views.report_view import ReportView
from app.views.login_dialog import LoginDialog

app = QApplication.instance()
if not app:
    app = QApplication([])


class TestViews(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo = DataRepository(data_dir=self.temp_dir)
        self.auth_service = AuthService(self.repo)
        self.user_manager = UserManager(self.repo)
        self.product_service = ProductService(self.repo)
        self.financial_service = FinancialService(self.repo)
        self.report_service = ReportService(self.repo)

        self.manager_user = self.user_manager.registra_primo_manager(
            username="admin",
            password="Password123",
            nome="Admin",
            cognome="Manager",
            email="admin@azienda.it",
            telefono="1234567890",
            dataNascita="1985-01-01"
        )

        self.dipendente_user = self.user_manager.crea_dipendente(
            username="dip1",
            password="Password123",
            nome="Mario",
            cognome="Rossi",
            email="mario.rossi@azienda.it",
            telefono="0987654321",
            dataNascita="1995-05-15"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    # -------------------------------------------------------------
    # 1. Test Vista Prodotti
    # -------------------------------------------------------------
    def test_product_view_columns_and_headers(self):
        """Verifica le 5 colonne e le intestazioni della vista Catalogo Prodotti."""
        view = ProductManagementView(self.product_service)
        headers = [view.table.horizontalHeaderItem(i).text() for i in range(view.table.columnCount())]

        expected_headers = [
            "Nome Prodotto", "Categoria / Tipo", "Unità di Misura", "Descrizione", "Prezzo Unitario"
        ]
        self.assertEqual(headers, expected_headers)

    # -------------------------------------------------------------
    # 2. Test Vista Movimenti Finanziari
    # -------------------------------------------------------------
    def test_entrate_table_columns(self):
        """Verifica le 9 colonne della tabella Entrate (inclusa UdM tra Quantità e Importo)."""
        view = FinancialMovementView(self.financial_service, self.product_service, self.manager_user)
        headers = [view.table_entrate.horizontalHeaderItem(i).text() for i in range(view.table_entrate.columnCount())]

        expected_headers = [
            "Data", "Prodotto", "Categoria Prodotto", "Cliente",
            "Quantità", "Unità di Misura", "Importo Totale (€)", "Descrizione", "Allegato PDF"
        ]
        self.assertEqual(headers, expected_headers)

    def test_uscite_table_columns(self):
        """Verifica le 6 colonne della tabella Uscite (Quantità rimossa)."""
        view = FinancialMovementView(self.financial_service, self.product_service, self.manager_user)
        headers = [view.table_uscite.horizontalHeaderItem(i).text() for i in range(view.table_uscite.columnCount())]

        expected_headers = [
            "Data", "Categoria Spesa", "Fornitore", "Importo Totale (€)", "Descrizione", "Allegato PDF"
        ]
        self.assertEqual(headers, expected_headers)

    def test_movement_view_filters(self):
        """Verifica la configurazione dei filtri in Entrate e Uscite."""
        view = FinancialMovementView(self.financial_service, self.product_service, self.manager_user)

        # Filtro prodotto presente in entrambe le sezioni
        self.assertTrue(hasattr(view, "cb_prod_entrate"))
        self.assertTrue(hasattr(view, "cb_prod_uscite"))
        self.assertEqual(view.cb_prod_entrate.itemText(0), "Tutti i prodotti")
        self.assertEqual(view.cb_prod_uscite.itemText(0), "Tutti i prodotti")

        # Filtro tipo cliente presente SOLO in Entrate
        self.assertTrue(hasattr(view, "cb_cliente_entrate"))
        self.assertFalse(hasattr(view, "cb_cliente_uscite"))
        client_options = [view.cb_cliente_entrate.itemText(i) for i in range(view.cb_cliente_entrate.count())]
        self.assertEqual(client_options, ["Tutti i clienti", "Azienda", "Privato"])

    # -------------------------------------------------------------
    # 3. Test Finestra Principale e Ruoli
    # -------------------------------------------------------------
    def test_main_window_tabs_for_manager(self):
        """Il Manager deve avere accesso a 4 tab, incluso Guadagno Aziendale."""
        window = MainWindow(self.manager_user, self.repo, self.auth_service)
        tab_titles = [window.tabs.tabText(i) for i in range(window.tabs.count())]

        expected_tabs = [
            "Gestione Utenti",
            "Catalogo Prodotti Agricoli",
            "Movimenti",
            "Guadagno Aziendale"
        ]
        self.assertEqual(tab_titles, expected_tabs)

    def test_main_window_tabs_for_dipendente(self):
        """Il Dipendente deve avere solo 3 tab (senza Guadagno Aziendale)."""
        window = MainWindow(self.dipendente_user, self.repo, self.auth_service)
        tab_titles = [window.tabs.tabText(i) for i in range(window.tabs.count())]

        expected_tabs = [
            "Gestione Utenti",
            "Catalogo Prodotti Agricoli",
            "Movimenti"
        ]
        self.assertEqual(tab_titles, expected_tabs)
        self.assertNotIn("Guadagno Aziendale", tab_titles)

    # -------------------------------------------------------------
    # 4. Test Vista Gestione Utenti
    # -------------------------------------------------------------
    def test_user_management_view_permissions(self):
        """Il Manager vede la tabella utenti aziendali, il Dipendente solo il proprio profilo."""
        view_mgr = UserManagementView(self.manager_user, self.user_manager, self.auth_service)
        self.assertTrue(hasattr(view_mgr, "users_table"))
        self.assertEqual(view_mgr.users_table.columnCount(), 6)

        headers = [view_mgr.users_table.horizontalHeaderItem(i).text() for i in range(view_mgr.users_table.columnCount())]
        self.assertEqual(headers, ["Username", "Ruolo", "Nome", "Cognome", "Email", "Ultimo Login"])

        view_dip = UserManagementView(self.dipendente_user, self.user_manager, self.auth_service)
        self.assertFalse(hasattr(view_dip, "users_table"))

    # -------------------------------------------------------------
    # 5. Test Vista Report Guadagno
    # -------------------------------------------------------------
    def test_report_view_elements(self):
        """Verifica la presenza del selettore anno e del pannello di visualizzazione report."""
        view = ReportView(self.report_service)
        self.assertTrue(hasattr(view, "cb_anno"))
        self.assertTrue(hasattr(view, "report_display"))

        curr_year = QDate.currentDate().year()
        self.assertEqual(view.cb_anno.itemText(0), str(curr_year))
        self.assertIn("REPORT GUADAGNO AZIENDALE", view.report_display.toPlainText())

    # -------------------------------------------------------------
    # 6. Test Dialog di Autenticazione
    # -------------------------------------------------------------
    def test_login_dialog_modes(self):
        """Verifica che con manager registrato si apra la schermata di login normale."""
        dialog = LoginDialog(self.auth_service, self.user_manager)
        self.assertEqual(dialog.stacked_widget.currentWidget(), dialog.login_widget)

        # Se non ci fossero manager, deve mostrare la schermata del primo manager
        empty_dir = tempfile.mkdtemp()
        try:
            empty_repo = DataRepository(data_dir=empty_dir)
            empty_um = UserManager(empty_repo)
            empty_auth = AuthService(empty_repo)
            dialog_first = LoginDialog(empty_auth, empty_um)
            self.assertEqual(dialog_first.stacked_widget.currentWidget(), dialog_first.first_manager_widget)
        finally:
            shutil.rmtree(empty_dir)


if __name__ == "__main__":
    unittest.main()
