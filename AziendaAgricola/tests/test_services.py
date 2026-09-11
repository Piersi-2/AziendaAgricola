import unittest
import tempfile
import shutil
import os
import datetime
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
        self.assertFalse(self.user_manager.has_manager())

        # Registrazione primo Manager
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
        self.assertTrue(self.user_manager.has_manager())

        # Tentativo registrazione secondo primo Manager fallisce
        with self.assertRaises(ValueError):
            self.user_manager.registra_primo_manager(
                "manager2", "Password123", "Luigi", "Verdi", "luigi@azienda.it", "123", "1990-01-01"
            )

        # Creazione Dipendente da parte del Manager
        dip = self.user_manager.crea_dipendente(
            username="dipendente1",
            password="SecretPass1",
            nome="Anna",
            cognome="Bianchi",
            email="anna.bianchi@azienda.it",
            telefono="3409876543",
            dataNascita="1995-05-05"
        )
        self.assertEqual(dip.ruolo, livelloAccesso.DIPENDENTE)

    def test_unicita_email_rnf4(self):
        self.user_manager.registra_primo_manager(
            "m1", "Pass1234", "M", "R", "mario@azienda.it", "123", "1980-01-01"
        )

        with self.assertRaises(ValueError):
            self.user_manager.crea_dipendente(
                "m2", "Pass1234", "A", "B", "mario@azienda.it", "456", "1990-01-01"
            )

    def test_data_nascita_obbligatoria(self):
        # Tentativo registrazione manager con data di nascita vuota fallisce
        with self.assertRaises(ValueError):
            self.user_manager.registra_primo_manager(
                "m_empty", "Password123", "Mario", "Rossi", "empty_dob@azienda.it", "123", ""
            )

        # Registrazione con data nascita valida
        self.user_manager.registra_primo_manager(
            "m1", "Password123", "Mario", "Rossi", "mario@azienda.it", "123", "01/01/1980"
        )

        # Tentativo creazione dipendente con data di nascita vuota fallisce
        with self.assertRaises(ValueError):
            self.user_manager.crea_dipendente(
                "d1", "SecretPass1", "Anna", "Bianchi", "anna@azienda.it", "456", "   "
            )

    def test_impossibile_aggiungere_prodotto_senza_categoria(self):
        # Nessuna categoria ancora presente: deve sollevare ValueError
        with self.assertRaises(ValueError) as ctx:
            self.product_service.aggiungi_prodotto_agricolo(
                nome="Mele Golden", descrizione="Frutta fresca", prezzo=1.5, unita="kilogrammi", tipo="FRUTTA"
            )
        self.assertIn("categoria", str(ctx.exception).lower())

        # Anche con categorie esistenti, se si specifica una categoria non registrata, deve fallire
        self.product_service.aggiungi_categoria("FRUTTA", "kilogrammi")
        with self.assertRaises(ValueError) as ctx2:
            self.product_service.aggiungi_prodotto_agricolo(
                nome="Mele Golden", descrizione="Frutta fresca", prezzo=1.5, unita="litri", tipo="NON_ESISTE"
            )
        self.assertIn("non esiste", str(ctx2.exception).lower())

    def test_unicita_prodotto_rnf5(self):
        self.product_service.aggiungi_categoria("VINO", "litri")
        p1 = self.product_service.aggiungi_prodotto_agricolo(
            nome="Vino Chianti", descrizione="Rosso DOCG", prezzo=15.0, unita="litri", tipo="VINO"
        )
        self.assertIsNotNone(p1)

        # Duplicato deve sollevare errore
        with self.assertRaises(ValueError):
            self.product_service.aggiungi_prodotto_agricolo(
                nome="Vino Chianti", descrizione="Altro", prezzo=20.0, unita="litri", tipo="VINO"
            )

    def test_login_logout(self):
        self.user_manager.registra_primo_manager(
            "manager1", "Password123", "Mario", "Rossi", "mario@azienda.it", "123", "1980-01-01"
        )

        user = self.auth_service.effettuaLogin("manager1", "Password123")
        self.assertIsNotNone(user)
        self.assertTrue(self.auth_service.is_session_valid())

        # Logout
        self.assertTrue(self.auth_service.effettuaLogout())
        self.assertFalse(self.auth_service.is_session_valid())

    def test_sessione_timeout_inattivita(self):
        self.user_manager.registra_primo_manager(
            "m_timeout", "Password123", "Mario", "Rossi", "mario@azienda.it", "123", "1980-01-01"
        )
        self.auth_service.effettuaLogin("m_timeout", "Password123")
        self.assertEqual(self.auth_service.session_timeout_minutes, 10)
        self.assertTrue(self.auth_service.is_session_valid())

        # Simula inattività superiore a 10 minuti (es. 11 minuti)
        past_dt = datetime.datetime.now() - datetime.timedelta(minutes=11)
        self.auth_service._last_activity_dt = past_dt
        self.auth_service.current_session.ultimaAttivita = past_dt.strftime("%Y-%m-%d %H:%M:%S")

        # La sessione deve essere scaduta per inattività
        self.assertFalse(self.auth_service.is_session_valid())

    def test_registrazione_entrate_e_uscite(self):
        # Registra categoria e prodotto prima
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
            categoria_uscita="SPESE DI PRODUZIONE",
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

    def test_singolo_manager_vincolo(self):
        # Registra il primo manager con successo
        m1 = self.user_manager.registra_primo_manager(
            "boss", "Password123", "Boss", "Unico", "boss@azienda.it", "123", "1985-01-01"
        )
        self.assertIsNotNone(m1.id)
        self.assertEqual(len(m1.id), 8)

        # Tentativo con registra_primo_manager fallisce
        with self.assertRaises(ValueError):
            self.user_manager.registra_primo_manager(
                "boss2", "Password123", "Boss2", "Due", "boss2@azienda.it", "123", "1986-01-01"
            )

        # Tentativo diretto con crea_manager fallisce anch'esso
        with self.assertRaises(ValueError) as ctx:
            self.user_manager.crea_manager(
                "boss3", "Password123", "Boss3", "Tre", "boss3@azienda.it", "123", "1987-01-01"
            )
        self.assertIn("manager", str(ctx.exception).lower())

    def test_id_randomici_e_univoci(self):
        # 1. Test ID Utenti
        u1 = self.user_manager.registra_primo_manager(
            "mng1", "Password123", "M", "R", "mng1@azienda.it", "111", "1980-01-01"
        )
        self.assertEqual(len(u1.id), 8)

        u2 = self.user_manager.crea_dipendente(
            "dip1", "Password123", "D", "B", "dip1@azienda.it", "222", "1990-01-01"
        )
        self.assertEqual(len(u2.id), 8)
        self.assertNotEqual(u1.id, u2.id)

        u3 = self.user_manager.crea_dipendente(
            "dip2", "Password123", "D2", "B2", "dip2@azienda.it", "333", "1992-02-02"
        )
        self.assertEqual(len(u3.id), 8)
        self.assertNotEqual(u2.id, u3.id)

        # 2. Test ID Prodotti
        self.product_service.aggiungi_categoria("FRUTTA", "kilogrammi")
        p1 = self.product_service.aggiungi_prodotto_agricolo("Mele", "Mele rosse", 2.0, "kilogrammi", "FRUTTA")
        self.assertEqual(len(p1.idProdotto), 8)

        p2 = self.product_service.aggiungi_prodotto_agricolo("Pere", "Pere Williams", 2.5, "kilogrammi", "FRUTTA")
        self.assertEqual(len(p2.idProdotto), 8)
        self.assertNotEqual(p1.idProdotto, p2.idProdotto)

        # 3. Test ID Contatti e Movimenti
        m1 = self.financial_service.registra_entrata(
            categoria_prodotto="FRUTTA",
            prodotto_id=p1.idProdotto,
            cliente_tipo="Privato",
            importo=20.0,
            data="2026-09-11",
            descrizione="Vendita mele",
            cliente_dettagli={"Nome": "Mario", "Cognome": "Rossi", "email": "mario@mail.it"}
        )
        self.assertTrue(m1.idMovimento.startswith("MOV-ENT-"))
        self.assertEqual(len(m1.contattoId), 8)

        m2 = self.financial_service.registra_entrata(
            categoria_prodotto="FRUTTA",
            prodotto_id=p2.idProdotto,
            cliente_tipo="Azienda",
            importo=50.0,
            data="2026-09-11",
            descrizione="Vendita pere",
            cliente_dettagli={"ragioneSociale": "BioMarket", "email": "info@biomarket.it"}
        )
        self.assertTrue(m2.idMovimento.startswith("MOV-ENT-"))
        self.assertNotEqual(m1.idMovimento, m2.idMovimento)
        self.assertNotEqual(m1.contattoId, m2.contattoId)

        m3 = self.financial_service.registra_uscita(
            categoria_uscita="SPESE DI MANUTENZIONE",
            prodotto_id=None,
            importo=15.0,
            data="2026-09-11",
            descrizione="Riparazione cassetta"
        )
        self.assertTrue(m3.idMovimento.startswith("MOV-USC-"))
        self.assertNotEqual(m1.idMovimento, m3.idMovimento)

    def test_prodotto_unificato_backend(self):
        from app.models import Prodotto
        self.product_service.aggiungi_categoria("ORTAGGI", "kilogrammi")
        p = self.product_service.aggiungi_prodotto_agricolo(
            nome="Carote",
            descrizione="Carote fresche",
            prezzo=1.80,
            unita="kilogrammi",
            tipo="ORTAGGI"
        )
        self.assertIsInstance(p, Prodotto)
        self.assertEqual(p.tipoProdotto, "ORTAGGI")
        self.assertEqual(p.unitaMisura, "kilogrammi")
        self.assertEqual(p.calcolaPrezzoScontato(10, 10), 16.20)

        # Verifica ricaricamento da repo
        loaded = self.repo.load_products()
        self.assertEqual(len(loaded), 1)
        self.assertIsInstance(loaded[0], Prodotto)
        self.assertEqual(loaded[0].idProdotto, p.idProdotto)
        self.assertEqual(loaded[0].tipoProdotto, "ORTAGGI")

    def test_quantita_vendita_e_unicita_combinata(self):
        self.product_service.aggiungi_categoria("MIELE", "kilogrammi")
        # 1. Prodotto a quantita 0.5 kg
        p1 = self.product_service.aggiungi_prodotto_agricolo(
            nome="Miele Millefiori", descrizione="Vasetto piccolo", prezzo=5.0, unita="kilogrammi", tipo="MIELE", quantita=0.5
        )
        self.assertEqual(p1.quantitaVendita, 0.5)

        # 2. Stesso nome ma quantita 1.0 kg deve essere consentito
        p2 = self.product_service.aggiungi_prodotto_agricolo(
            nome="Miele Millefiori", descrizione="Vasetto grande", prezzo=9.0, unita="kilogrammi", tipo="MIELE", quantita=1.0
        )
        self.assertEqual(p2.quantitaVendita, 1.0)
        self.assertNotEqual(p1.idProdotto, p2.idProdotto)

        # 3. Tentativo con stesso nome E stessa quantita (0.5 kg) deve fallire
        with self.assertRaises(ValueError) as ctx:
            self.product_service.aggiungi_prodotto_agricolo(
                nome="Miele Millefiori", descrizione="Altro piccolo", prezzo=5.5, unita="kilogrammi", tipo="MIELE", quantita=0.5
            )
        self.assertIn("quantità", str(ctx.exception).lower())

    def test_id_univoci_dopo_cancellazione(self):
        # 1. Creazione e cancellazione utenti
        m = self.user_manager.registra_primo_manager(
            "m1", "Pass1234", "M", "R", "m1@azienda.it", "1", "1980-01-01"
        )
        d1 = self.user_manager.crea_dipendente(
            "d1", "Pass1234", "D1", "B", "d1@azienda.it", "2", "1990-01-01"
        )
        d2 = self.user_manager.crea_dipendente(
            "d2", "Pass1234", "D2", "B", "d2@azienda.it", "3", "1991-01-01"
        )

        # Cancella d2
        self.user_manager.elimina_dipendente(d2.id)
        users = self.user_manager.get_all_users()
        self.assertEqual(len(users), 2)

        # Il nuovo utente ha un proprio ID univoco
        d3 = self.user_manager.crea_dipendente(
            "d3", "Pass1234", "D3", "B", "d3@azienda.it", "4", "1992-01-01"
        )
        self.assertNotEqual(d3.id, d2.id)
        self.assertNotEqual(d3.id, d1.id)

        # 2. Creazione e cancellazione prodotti
        self.product_service.aggiungi_categoria("FRUTTA", "kilogrammi")
        prod1 = self.product_service.aggiungi_prodotto_agricolo("Mele", "Desc", 2.0, "kilogrammi", "FRUTTA", 1.0)
        prod2 = self.product_service.aggiungi_prodotto_agricolo("Pere", "Desc", 2.5, "kilogrammi", "FRUTTA", 1.0)

        # Elimina prod2
        self.product_service.elimina_prodotto(prod2.idProdotto)
        prod3 = self.product_service.aggiungi_prodotto_agricolo("Banane", "Desc", 3.0, "kilogrammi", "FRUTTA", 1.0)
        self.assertNotEqual(prod3.idProdotto, prod2.idProdotto)
        self.assertNotEqual(prod3.idProdotto, prod1.idProdotto)

        # 3. Creazione e cancellazione movimenti
        mov1 = self.financial_service.registra_entrata(
            categoria_prodotto="FRUTTA",
            prodotto_id=prod1.idProdotto,
            cliente_tipo="Privato",
            importo=10.0,
            data="2026-09-11",
            descrizione="Vendita 1"
        )
        mov2 = self.financial_service.registra_entrata(
            categoria_prodotto="FRUTTA",
            prodotto_id=prod1.idProdotto,
            cliente_tipo="Privato",
            importo=20.0,
            data="2026-09-11",
            descrizione="Vendita 2"
        )

        # Elimina mov2
        self.financial_service.elimina_movimento(mov2.idMovimento)
        mov3 = self.financial_service.registra_uscita(
            categoria_uscita="SPESE DI MANUTENZIONE",
            prodotto_id=None,
            importo=5.0,
            data="2026-09-11",
            descrizione="Spesa"
        )
        self.assertNotEqual(mov3.idMovimento, mov2.idMovimento)
        self.assertNotEqual(mov3.idMovimento, mov1.idMovimento)

if __name__ == '__main__':
    unittest.main()

