import unittest
import tempfile
import shutil
import os
import sys
import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.repositories import DataRepository
from app.services import Autenticatore, GestoreUtenti, GestoreProdotti, GestoreMovimenti, GestoreReport
from app.models import livelloAccesso, TipoMovimento, TipoUscita

class TestServices(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo = DataRepository(data_dir=self.temp_dir)
        self.auth_service = Autenticatore(self.repo)
        self.user_manager = GestoreUtenti(self.repo)
        self.product_service = GestoreProdotti(self.repo)
        self.financial_service = GestoreMovimenti(self.repo)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_registrazione_primo_manager_e_dipendente(self):
        """Verifica la registrazione iniziale del primo Manager, il blocco di un secondo Manager e la creazione di Dipendenti."""
        # Nessun utente inizialmente
        self.assertFalse(self.user_manager.presenzaManager())

        # Registrazione primo Manager
        manager = self.user_manager.creaManager(
            username="manager1",
            password="Password123",
            nome="Mario",
            cognome="Rossi",
            email="mario.rossi@azienda.it",
            telefono="3331234567",
            dataNascita="1980-01-01"
        )
        self.assertEqual(manager.ruolo, livelloAccesso.MANAGER)
        self.assertTrue(self.user_manager.presenzaManager())

        # Tentativo registrazione secondo primo Manager fallisce
        with self.assertRaises(ValueError):
            self.user_manager.creaManager(
                "manager2", "Password123", "Luigi", "Verdi", "luigi@azienda.it", "123", "1990-01-01"
            )

        # Creazione Dipendente da parte del Manager
        dip = self.user_manager.creaDipendente(
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
        self.user_manager.creaManager(
            "m1", "Pass1234", "M", "R", "mario@azienda.it", "123", "1980-01-01"
        )

        with self.assertRaises(ValueError):
            self.user_manager.creaDipendente(
                "m2", "Pass1234", "A", "B", "mario@azienda.it", "456", "1990-01-01"
            )

    def test_data_nascita_obbligatoria(self):
        """Verifica che la data di nascita sia un campo obbligatorio per qualsiasi profilo utente."""
        # Tentativo registrazione manager con data di nascita vuota fallisce
        with self.assertRaises(ValueError):
            self.user_manager.creaManager(
                "m_empty", "Password123", "Mario", "Rossi", "empty_dob@azienda.it", "123", ""
            )

        # Registrazione con data nascita valida
        self.user_manager.creaManager(
            "m1", "Password123", "Mario", "Rossi", "mario@azienda.it", "123", "01/01/1980"
        )

        # Tentativo creazione dipendente con data di nascita vuota fallisce
        with self.assertRaises(ValueError):
            self.user_manager.creaDipendente(
                "d1", "SecretPass1", "Anna", "Bianchi", "anna@azienda.it", "456", "   "
            )

    def test_impossibile_aggiungere_prodotto_senza_categoria(self):
        """Verifica che non sia possibile aggiungere un prodotto senza una categoria valida o preesistente."""
        # Nessuna categoria ancora presente: deve sollevare ValueError
        with self.assertRaises(ValueError) as ctx:
            self.product_service.aggiungiProdotto(
                nome="Mele Golden", descrizione="Frutta fresca", prezzo=1.5, unita="kilogrammi", tipo="FRUTTA"
            )
        self.assertIn("categoria", str(ctx.exception).lower())

        # Anche con categorie esistenti, se si specifica una categoria non registrata, deve fallire
        self.product_service.aggiungiCategoria("FRUTTA", "kilogrammi")
        with self.assertRaises(ValueError) as ctx2:
            self.product_service.aggiungiProdotto(
                nome="Mele Golden", descrizione="Frutta fresca", prezzo=1.5, unita="litri", tipo="NON_ESISTE"
            )
        self.assertIn("non esiste", str(ctx2.exception).lower())

    def test_unicita_prodotto_rnf5(self):
        """RNF5: Verifica che non sia consentita l'aggiunta di categorie o prodotti con nomi già esistenti."""
        # 1. Test unicità categoria (RNF5)
        self.product_service.aggiungiCategoria("VINO", "litri")
        with self.assertRaises(ValueError):
            self.product_service.aggiungiCategoria("VINO", "litri")

        # 2. Test unicità prodotto (RNF5)
        p1 = self.product_service.aggiungiProdotto(
            nome="Vino Chianti", descrizione="Rosso DOCG", prezzo=15.0, unita="litri", tipo="VINO"
        )
        self.assertIsNotNone(p1)

        # Duplicato deve sollevare errore
        with self.assertRaises(ValueError):
            self.product_service.aggiungiProdotto(
                nome="Vino Chianti", descrizione="Altro", prezzo=20.0, unita="litri", tipo="VINO"
            )

    def test_login_logout(self):
        """Verifica il ciclo di vita dell'autenticazione (login, validità sessione e logout)."""
        self.user_manager.creaManager(
            "manager1", "Password123", "Mario", "Rossi", "mario@azienda.it", "123", "1980-01-01"
        )

        user = self.auth_service.effettuaLogin("manager1", "Password123")
        self.assertIsNotNone(user)
        self.assertTrue(self.auth_service.verificaSessione())

        # Logout
        self.assertTrue(self.auth_service.effettuaLogout())
        self.assertFalse(self.auth_service.verificaSessione())

    def test_sessione_timeout_inattivita(self):
        """Verifica l'invalidazione automatica della sessione utente dopo il timeout di inattività (10 minuti)."""
        self.user_manager.creaManager(
            "m_timeout", "Password123", "Mario", "Rossi", "mario@azienda.it", "123", "1980-01-01"
        )
        self.auth_service.effettuaLogin("m_timeout", "Password123")
        self.assertEqual(self.auth_service.session_timeout_minutes, 10)
        self.assertTrue(self.auth_service.verificaSessione())

        # Simula inattività superiore a 10 minuti (es. 11 minuti)
        past_dt = datetime.datetime.now() - datetime.timedelta(minutes=11)
        self.auth_service._last_activity_dt = past_dt
        self.auth_service.current_session.ultimaAttivita = past_dt.strftime("%Y-%m-%d %H:%M:%S")

        # La sessione deve essere scaduta per inattività
        self.assertFalse(self.auth_service.verificaSessione())

    def test_registrazione_entrate_e_uscite(self):
        """Verifica la corretta registrazione e persistenza di movimenti finanziari di entrata e di uscita."""
        # Registra categoria e prodotto prima
        cat = self.product_service.aggiungiCategoria("OLIO", "litri")
        prod = self.product_service.aggiungiProdotto(
            nome="Olio di Oliva",
            descrizione="Extravergine",
            prezzo=12.0,
            unita="litri",
            tipo="OLIO"
        )

        # Registrazione entrata
        e = self.financial_service.registraEntrata(
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
        u = self.financial_service.registraUscita(
            categoria_uscita="SPESE DI PRODUZIONE",
            prodotto_id=prod.idProdotto,
            importo=350.0,
            data="2026-07-21",
            descrizione="Acquisto bottiglie olio",
            fornitore_note="AgriBio Srl"
        )
        self.assertEqual(u.prezzoTotale, 350.0)
        self.assertEqual(u.prodottoId, prod.idProdotto)

        movs = self.financial_service.getAllMovements()
        self.assertEqual(len(movs), 2)

    def test_modifica_movimento(self):
        """Verifica la modifica di un movimento finanziario e le relative validazioni."""
        e = self.financial_service.registraEntrata(
            categoria_prodotto="FRUTTA",
            prodotto_id=None,
            cliente_tipo="Privato",
            importo=50.0,
            data="2026-08-01",
            descrizione="Vendita mele",
            quantita=10.0
        )

        # Modifica con successo
        mod = self.financial_service.modificaMovimento(
            movimento_id=e.idMovimento,
            data="2026-08-02",
            importo=75.0,
            quantita=15.0,
            descrizione="Vendita mele e pere"
        )
        self.assertEqual(mod.dataMovimento, "2026-08-02")
        self.assertEqual(mod.prezzoTotale, 75.0)
        self.assertEqual(mod.quantita, 15.0)
        self.assertEqual(mod.descrizione, "Vendita mele e pere")

        # Verifica persistenza nel repository
        loaded = self.financial_service.getAllMovements()
        target = next((m for m in loaded if m.idMovimento == e.idMovimento), None)
        self.assertIsNotNone(target)
        self.assertEqual(target.prezzoTotale, 75.0)

        # Validazione importo negativo
        with self.assertRaises(ValueError):
            self.financial_service.modificaMovimento(e.idMovimento, "2026-08-02", -10.0, 5.0, "Err")

        # Validazione quantità negativa
        with self.assertRaises(ValueError):
            self.financial_service.modificaMovimento(e.idMovimento, "2026-08-02", 10.0, -5.0, "Err")

        # Validazione descrizione > 500 caratteri
        with self.assertRaises(ValueError):
            self.financial_service.modificaMovimento(e.idMovimento, "2026-08-02", 10.0, 5.0, "A" * 501)

        # Validazione ID non esistente
        with self.assertRaises(ValueError):
            self.financial_service.modificaMovimento("ID-NON-ESISTE", "2026-08-02", 10.0, 5.0, "Desc")

    def test_categorie_dinamiche_e_unita_misura(self):
        """Verifica l'aggiunta di categorie dinamiche, la validazione delle unità di misura e l'ereditarietà nei prodotti."""
        # 1. Aggiunta categoria valida
        cat = self.product_service.aggiungiCategoria("MIELE", "grammi")
        self.assertEqual(cat.nome, "MIELE")
        self.assertEqual(cat.unitaMisura, "grammi")

        # 2. Controllo duplicato categoria
        with self.assertRaises(ValueError):
            self.product_service.aggiungiCategoria("MIELE", "litri")

        # 3. Controllo unita di misura non valida
        with self.assertRaises(ValueError):
            self.product_service.aggiungiCategoria("VINO", "bottiglie")

        # 4. Creazione prodotto e ereditarieta dell'unita di misura
        cats = self.product_service.getAllCategories()
        miele_cat = next((c for c in cats if c.nome == "MIELE"), None)
        self.assertIsNotNone(miele_cat)
        
        prod = self.product_service.aggiungiProdotto(
            nome="Miele Millefiori",
            descrizione="Vasetto 500g",
            prezzo=6.50,
            unita=miele_cat.unitaMisura,
            tipo="MIELE"
        )
        self.assertEqual(prod.unitaMisura, "grammi")
        self.assertEqual(prod.categoria, "MIELE")

    def test_singolo_manager_vincolo(self):
        """Verifica che sia impossibile creare più di un profilo Manager nel sistema."""
        # Registra il primo manager con successo
        m1 = self.user_manager.creaManager(
            "boss", "Password123", "Boss", "Unico", "boss@azienda.it", "123", "1985-01-01"
        )
        self.assertIsNotNone(m1.id)
        self.assertEqual(len(m1.id), 8)

        # Tentativo di registrazione secondo manager fallisce
        with self.assertRaises(ValueError):
            self.user_manager.creaManager(
                "boss2", "Password123", "Boss2", "Due", "boss2@azienda.it", "123", "1986-01-01"
            )

        # Tentativo diretto con creaManager fallisce anch'esso
        with self.assertRaises(ValueError) as ctx:
            self.user_manager.creaManager(
                "boss3", "Password123", "Boss3", "Tre", "boss3@azienda.it", "123", "1987-01-01"
            )
        self.assertIn("manager", str(ctx.exception).lower())

    def test_prodotto_unificato_backend(self):
        """Verifica la corretta creazione e persistenza del modello unificato Prodotto con unità di misura."""
        from app.models import Prodotto
        self.product_service.aggiungiCategoria("ORTAGGI", "kilogrammi")
        p = self.product_service.aggiungiProdotto(
            nome="Carote",
            descrizione="Carote fresche",
            prezzo=1.80,
            unita="kilogrammi",
            tipo="ORTAGGI"
        )
        self.assertIsInstance(p, Prodotto)
        self.assertEqual(p.categoria, "ORTAGGI")
        self.assertEqual(p.unitaMisura, "kilogrammi")

        # Verifica ricaricamento da repo
        loaded = self.repo.caricaProdotti()
        self.assertEqual(len(loaded), 1)
        self.assertIsInstance(loaded[0], Prodotto)
        self.assertEqual(loaded[0].idProdotto, p.idProdotto)
        self.assertEqual(loaded[0].categoria, "ORTAGGI")

    def test_unicita_nome_prodotto(self):
        """Verifica il blocco della creazione di due prodotti aventi lo stesso nome."""
        self.product_service.aggiungiCategoria("MIELE", "kilogrammi")
        p1 = self.product_service.aggiungiProdotto(
            nome="Miele Millefiori", descrizione="Vasetto", prezzo=5.0, unita="kilogrammi", tipo="MIELE"
        )
        self.assertEqual(p1.nome, "Miele Millefiori")

        # Tentativo con stesso nome deve fallire
        with self.assertRaises(ValueError) as ctx:
            self.product_service.aggiungiProdotto(
                nome="Miele Millefiori", descrizione="Altro vasetto", prezzo=6.0, unita="kilogrammi", tipo="MIELE"
            )
        self.assertIn("esiste già", str(ctx.exception).lower())

    def test_id_univoci_dopo_cancellazione(self):
        """Verifica che dopo l'eliminazione di entità i nuovi identificativi generati rimangano univoci."""
        # 1. Creazione e cancellazione utenti
        m = self.user_manager.creaManager(
            "m1", "Pass1234", "M", "R", "m1@azienda.it", "1", "1980-01-01"
        )
        d1 = self.user_manager.creaDipendente(
            "d1", "Pass1234", "D1", "B", "d1@azienda.it", "2", "1990-01-01"
        )
        d2 = self.user_manager.creaDipendente(
            "d2", "Pass1234", "D2", "B", "d2@azienda.it", "3", "1991-01-01"
        )

        # Cancella d2
        self.user_manager.eliminaDipendente(d2.id)
        users = self.user_manager.getAllUsers()
        self.assertEqual(len(users), 2)
        d3 = self.user_manager.creaDipendente(
            "d3", "Pass1234", "D3", "B", "d3@azienda.it", "4", "1992-01-01"
        )
        self.assertNotEqual(d3.id, d2.id)
        self.assertNotEqual(d3.id, d1.id)

        # 2. Creazione e cancellazione prodotti
        self.product_service.aggiungiCategoria("FRUTTA", "kilogrammi")
        prod1 = self.product_service.aggiungiProdotto("Mele", "Desc", 2.0, "kilogrammi", "FRUTTA")
        prod2 = self.product_service.aggiungiProdotto("Pere", "Desc", 2.5, "kilogrammi", "FRUTTA")

        # Elimina prod2
        self.product_service.eliminaProdotto(prod2.idProdotto)
        prod3 = self.product_service.aggiungiProdotto("Banane", "Desc", 3.0, "kilogrammi", "FRUTTA")
        self.assertNotEqual(prod3.idProdotto, prod2.idProdotto)
        self.assertNotEqual(prod3.idProdotto, prod1.idProdotto)

        # 3. Creazione e cancellazione movimenti
        mov1 = self.financial_service.registraEntrata(
            categoria_prodotto="FRUTTA",
            prodotto_id=prod1.idProdotto,
            cliente_tipo="Privato",
            importo=10.0,
            data="2026-09-11",
            descrizione="Vendita 1"
        )
        mov2 = self.financial_service.registraEntrata(
            categoria_prodotto="FRUTTA",
            prodotto_id=prod1.idProdotto,
            cliente_tipo="Privato",
            importo=20.0,
            data="2026-09-11",
            descrizione="Vendita 2"
        )

        # Elimina mov2
        self.financial_service.eliminaMovimento(mov2.idMovimento)
        mov3 = self.financial_service.registraUscita(
            categoria_uscita="SPESE DI MANUTENZIONE",
            prodotto_id=None,
            importo=5.0,
            data="2026-09-11",
            descrizione="Spesa"
        )
        self.assertNotEqual(mov3.idMovimento, mov2.idMovimento)
        self.assertNotEqual(mov3.idMovimento, mov1.idMovimento)

    def test_filtra_uscite(self):
        """Verifica che il metodo filtraUscite filtri correttamente per anno e tipo spesa."""
        self.financial_service.registraUscita(
            categoria_uscita=TipoUscita.SPESE_DI_MANUTENZIONE.value,
            prodotto_id=None,
            importo=150.0,
            data="2026-03-10",
            descrizione="Manutenzione impianto"
        )
        self.financial_service.registraUscita(
            categoria_uscita=TipoUscita.SPESE_DI_PRODUZIONE.value,
            prodotto_id=None,
            importo=300.0,
            data="2026-04-15",
            descrizione="Concime"
        )
        self.financial_service.registraUscita(
            categoria_uscita=TipoUscita.SPESE_DI_MANUTENZIONE.value,
            prodotto_id=None,
            importo=80.0,
            data="2025-11-20",
            descrizione="Riparazione recinzione"
        )

        # Nessun filtro (o tutti)
        tutte = self.financial_service.filtraUscite()
        self.assertEqual(len(tutte), 3)

        # Filtro solo per anno 2026
        uscite_2026 = self.financial_service.filtraUscite(anno="2026")
        self.assertEqual(len(uscite_2026), 2)

        # Filtro per tipo spesa MANUTENZIONE
        manutenzione = self.financial_service.filtraUscite(tipo_spesa=TipoUscita.SPESE_DI_MANUTENZIONE.value)
        self.assertEqual(len(manutenzione), 2)

        # Filtro combinato anno 2026 + tipo spesa MANUTENZIONE
        comb = self.financial_service.filtraUscite(anno="2026", tipo_spesa=TipoUscita.SPESE_DI_MANUTENZIONE.value)
        self.assertEqual(len(comb), 1)
        self.assertEqual(comb[0].prezzoTotale, 150.0)

    def test_filtra_entrate(self):
        """Verifica che il metodo filtraEntrate filtri correttamente per anno, prodotto e tipo cliente."""
        cat = self.product_service.aggiungiCategoria("VERDURA", "kg")
        prod = self.product_service.aggiungiProdotto(
            nome="Pomodori",
            descrizione="San Marzano",
            prezzo=2.5,
            unita="kg",
            tipo="VERDURA"
        )

        self.financial_service.registraEntrata(
            categoria_prodotto="VERDURA",
            prodotto_id=prod.idProdotto,
            cliente_tipo="Azienda",
            importo=500.0,
            data="2026-06-01",
            descrizione="Vendita ingrosso",
            cliente_dettagli={"ragioneSociale": "Supermercati Spa", "partitaIVA": "11223344556"}
        )
        self.financial_service.registraEntrata(
            categoria_prodotto="VERDURA",
            prodotto_id=None,
            cliente_tipo="Privato",
            importo=30.0,
            data="2025-07-01",
            descrizione="Vendita dettaglio",
            cliente_dettagli={"Nome": "Giuseppe Verdi", "codiceFiscale": "VRDGPP80A01H501U"}
        )

        # Filtro per anno
        entrate_2026 = self.financial_service.filtraEntrate(anno="2026")
        self.assertEqual(len(entrate_2026), 1)
        self.assertEqual(entrate_2026[0].prezzoTotale, 500.0)

        # Filtro per prodotto
        entrate_prod = self.financial_service.filtraEntrate(prodotto_id=prod.idProdotto)
        self.assertEqual(len(entrate_prod), 1)

        # Filtro per tipo cliente Azienda vs Privato
        aziende = self.financial_service.filtraEntrate(tipo_cliente="Azienda")
        self.assertEqual(len(aziende), 1)
        privati = self.financial_service.filtraEntrate(tipo_cliente="Privato")
        self.assertEqual(len(privati), 1)

if __name__ == '__main__':
    unittest.main()


