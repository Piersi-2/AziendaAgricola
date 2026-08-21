import unittest
import tempfile
import shutil
import os
from app.repositories import DataRepository
from app.services import AuthService, UserManager, ProductService, FinancialService, ReportService
from app.models import livelloAccesso, TipoMovimento, TipoUscita

class TestServices(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo = DataRepository(data_dir=self.temp_dir)
        self.auth_service = AuthService(self.repo)
        self.user_manager = UserManager(self.repo)
        self.product_service = ProductService(self.repo)
        self.financial_service = FinancialService(self.repo)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_registrazione_primo_manager_e_dipendente(self):
        # Nessun utente inizialmente
        self.assertFalse(self.user_manager.ha_manager())

        # Registrazione primo Manager (RF1, RF27)
        manager = self.user_manager.registra_primo_manager(
            username="manager1",
            password="Password123",
            nome="Mario",
            cognome="Rossi",
            email="mario.rossi@azienda.it",
            telefono="3331234567",
            dataNascita="1980-01-01"
        )
        self.assertEqual(manager.ruolo, livelloAccesso.MANAGER)
        self.assertTrue(self.user_manager.ha_manager())

        # Tentativo registrazione secondo primo Manager fallisce
        with self.assertRaises(ValueError):
            self.user_manager.registra_primo_manager(
                "manager2", "Password123", "Luigi", "Verdi", "luigi@azienda.it", "123", "1990-01-01"
            )

        # Creazione Dipendente da parte del Manager (RF2)
        dip = self.user_manager.crea_dipendente(
            username="dipendente1",
            password="SecretPass1",
            nome="Anna",
            cognome="Bianchi",
            email="anna.bianchi@azienda.it",
            telefono="3409876543",
            dataNascita="1995-05-05",
            dataAssunzione="2024-01-10",
            mansione="Raccolta Olive",
            stipendio=1500.0
        )
        self.assertEqual(dip.ruolo, livelloAccesso.DIPENDENTE)

    def test_unicita_email_rnf4(self):
        self.user_manager.registra_primo_manager(
            "m1", "Pass1234", "M", "R", "mario@azienda.it", "123", "1980-01-01"
        )

        with self.assertRaises(ValueError):
            self.user_manager.crea_dipendente(
                "m2", "Pass1234", "A", "B", "mario@azienda.it", "456", "1990-01-01", "", "", 0.0
            )

    def test_unicita_prodotto_rnf5(self):
        p1 = self.product_service.aggiungi_prodotto_agricolo(
            nome="Vino Chianti", descrizione="Rosso DOCG", prezzo=15.0, unita="bottiglie", tipo="Vino"
        )
        self.assertIsNotNone(p1)

        # Duplicato deve sollevare errore
        with self.assertRaises(ValueError):
            self.product_service.aggiungi_prodotto_agricolo(
                nome="Vino Chianti", descrizione="Altro", prezzo=20.0, unita="bottiglie", tipo="Vino"
            )

    def test_login_logout_e_recupero_password(self):
        self.user_manager.registra_primo_manager(
            "manager1", "Password123", "Mario", "Rossi", "mario@azienda.it", "123", "1980-01-01"
        )

        user = self.auth_service.effettuaLogin("manager1", "Password123")
        self.assertIsNotNone(user)
        self.assertTrue(self.auth_service.is_session_valid())

        # Logout
        self.assertTrue(self.auth_service.effettuaLogout())
        self.assertFalse(self.auth_service.is_session_valid())

        # Recupero password (RNF6)
        ok, msg = self.auth_service.recupera_password_email("mario@azienda.it")
        self.assertTrue(ok)
        self.assertIn("Password123", msg)

    def test_registrazione_entrate_e_uscite(self):
        # Registra categoria e prodotto prima (Richiesto da RNF / PROMPT3)
        cat = self.product_service.aggiungi_categoria("OLIO", "litri")
        prod = self.product_service.aggiungi_prodotto_agricolo(
            nome="Olio di Oliva",
            descrizione="Extravergine",
            prezzo=12.0,
            unita="litri",
            tipo="OLIO"
        )

        # Registrazione entrata
        e = self.financial_service.registra_entrata(
            categoria_prodotto="OLIO",
            prodotto_id=prod.idProdotto,
            cliente_tipo="Azienda",
            importo=1200.0,
            data="2026-07-20",
            descrizione="Fornitura olio extravergine ristorante",
            cliente_dettagli={"ragioneSociale": "Ristorante Da Mario", "partitaIVA": "12345678901"}
        )
        self.assertEqual(e.prezzoTotale, 1200.0)
        self.assertEqual(e.prodottoId, prod.idProdotto)
        self.assertEqual(e.prodottoNome, "Olio di Oliva")

        # Registrazione uscita
        u = self.financial_service.registra_uscita(
            categoria_uscita="OLIO",
            prodotto_id=prod.idProdotto,
            importo=350.0,
            data="2026-07-21",
            descrizione="Acquisto bottiglie olio",
            fornitore_note="AgriBio Srl"
        )
        self.assertEqual(u.prezzoTotale, 350.0)
        self.assertEqual(u.prodottoId, prod.idProdotto)

        movs = self.financial_service.get_all_movements()
        self.assertEqual(len(movs), 2)

    def test_categorie_dinamiche_e_unita_misura(self):
        # 1. Aggiunta categoria valida
        cat = self.product_service.aggiungi_categoria("MIELE", "grammi")
        self.assertEqual(cat.nome, "MIELE")
        self.assertEqual(cat.unitaMisura, "grammi")

        # 2. Controllo duplicato categoria
        with self.assertRaises(ValueError):
            self.product_service.aggiungi_categoria("MIELE", "litri")

        # 3. Controllo unita di misura non valida
        with self.assertRaises(ValueError):
            self.product_service.aggiungi_categoria("VINO", "bottiglie")

        # 4. Creazione prodotto e ereditarieta dell'unita di misura
        cats = self.product_service.get_all_categories()
        miele_cat = next((c for c in cats if c.nome == "MIELE"), None)
        self.assertIsNotNone(miele_cat)
        
        prod = self.product_service.aggiungi_prodotto_agricolo(
            nome="Miele Millefiori",
            descrizione="Vasetto 500g",
            prezzo=6.50,
            unita=miele_cat.unitaMisura,
            tipo="MIELE"
        )
        self.assertEqual(prod.unitaMisura, "grammi")
        self.assertEqual(prod.tipoProdotto, "MIELE")

if __name__ == '__main__':
    unittest.main()
