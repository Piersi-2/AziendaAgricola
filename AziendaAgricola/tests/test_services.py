import unittest
import tempfile
import shutil
import os
import sys
import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
        """Verifica la registrazione iniziale del primo Manager, il blocco di un secondo Manager e la creazione di Dipendenti."""
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
        """RNF4: Verifica il vincolo di unicità dell'indirizzo email tra tutti gli utenti registrati."""
        self.user_manager.registra_primo_manager(
            "m1", "Pass1234", "M", "R", "mario@azienda.it", "123", "1980-01-01"
        )

        with self.assertRaises(ValueError):
            self.user_manager.crea_dipendente(
                "m2", "Pass1234", "A", "B", "mario@azienda.it", "456", "1990-01-01"
            )

    def test_data_nascita_obbligatoria(self):
        """Verifica che la data di nascita sia un campo obbligatorio per qualsiasi profilo utente."""
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
        """Verifica che non sia possibile aggiungere un prodotto senza una categoria valida o preesistente."""
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
        """RNF5: Verifica che non sia consentita l'aggiunta di categorie o prodotti con nomi già esistenti."""
        # 1. Test unicità categoria (RNF5)
        self.product_service.aggiungi_categoria("VINO", "litri")
        with self.assertRaises(ValueError):
            self.product_service.aggiungi_categoria("VINO", "litri")

        # 2. Test unicità prodotto (RNF5)
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
        """Verifica il ciclo di vita dell'autenticazione (login, validità sessione e logout)."""
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
        """Verifica l'invalidazione automatica della sessione utente dopo il timeout di inattività (10 minuti)."""
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
        """Verifica la corretta registrazione e persistenza di movimenti finanziari di entrata e di uscita."""
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
        """Verifica l'aggiunta di categorie dinamiche, la validazione delle unità di misura e l'ereditarietà nei prodotti."""
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
        """Verifica che sia impossibile creare più di un profilo Manager nel sistema."""
        # Registra il primo manager con successo
        m1 = self.user_manager.registra_primo_manager(
            "boss", "Password123", "Boss", "Unico", "boss@azienda.it", "123", "1985-01-01"
        )
        self.assertIsNotNone(m1.id)
        self.assertEqual(len(m1.id), 8)

        # Tentativo di registrazione secondo manager fallisce
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

    def test_prodotto_unificato_backend(self):
        """Verifica la corretta creazione e persistenza del modello unificato Prodotto con unità di misura."""
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

        # Verifica ricaricamento da repo
        loaded = self.repo.load_products()
        self.assertEqual(len(loaded), 1)
        self.assertIsInstance(loaded[0], Prodotto)
        self.assertEqual(loaded[0].idProdotto, p.idProdotto)
        self.assertEqual(loaded[0].tipoProdotto, "ORTAGGI")

    def test_unicita_nome_prodotto(self):
        """Verifica il blocco della creazione di due prodotti aventi lo stesso nome."""
        self.product_service.aggiungi_categoria("MIELE", "kilogrammi")
        p1 = self.product_service.aggiungi_prodotto_agricolo(
            nome="Miele Millefiori", descrizione="Vasetto", prezzo=5.0, unita="kilogrammi", tipo="MIELE"
        )
        self.assertEqual(p1.nome, "Miele Millefiori")

        # Tentativo con stesso nome deve fallire
        with self.assertRaises(ValueError) as ctx:
            self.product_service.aggiungi_prodotto_agricolo(
                nome="Miele Millefiori", descrizione="Altro vasetto", prezzo=6.0, unita="kilogrammi", tipo="MIELE"
            )
        self.assertIn("esiste già", str(ctx.exception).lower())

    def test_id_univoci_dopo_cancellazione(self):
        """Verifica che dopo l'eliminazione di entità i nuovi identificativi generati rimangano univoci."""
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
        d3 = self.user_manager.crea_dipendente(
            "d3", "Pass1234", "D3", "B", "d3@azienda.it", "4", "1992-01-01"
        )
        self.assertNotEqual(d3.id, d2.id)
        self.assertNotEqual(d3.id, d1.id)

        # 2. Creazione e cancellazione prodotti
        self.product_service.aggiungi_categoria("FRUTTA", "kilogrammi")
        prod1 = self.product_service.aggiungi_prodotto_agricolo("Mele", "Desc", 2.0, "kilogrammi", "FRUTTA")
        prod2 = self.product_service.aggiungi_prodotto_agricolo("Pere", "Desc", 2.5, "kilogrammi", "FRUTTA")

        # Elimina prod2
        self.product_service.elimina_prodotto(prod2.idProdotto)
        prod3 = self.product_service.aggiungi_prodotto_agricolo("Banane", "Desc", 3.0, "kilogrammi", "FRUTTA")
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

