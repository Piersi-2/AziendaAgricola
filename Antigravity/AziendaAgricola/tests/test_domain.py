import unittest
from app.models import (
    Utente, Manager, Dipendente, livelloAccesso,
    ProdottoAgricolo, Movimento, TipoMovimento, TipoUscita,
    ReportGuadagno
)

class TestDomainModels(unittest.TestCase):
    def test_valida_password_rnf3(self):
        """RNF3: Validazione password >= 8 caratteri alfanumerici."""
        self.assertTrue(Utente.valida_password("Pass1234"))
        self.assertTrue(Utente.valida_password("abcdefgh1"))

        # Troppo corta (< 8)
        self.assertFalse(Utente.valida_password("Pass1"))

        # Caratteri non alfanumerici (!, ?, @)
        self.assertFalse(Utente.valida_password("Password123!"))
        self.assertFalse(Utente.valida_password("Pass 1234"))

    def test_movimento_descrizione_limit_rnf8(self):
        """RNF8: Descrizione del movimento <= 500 caratteri."""
        desc_ok = "A" * 500
        m = Movimento(
            idMovimento="M1",
            tipo=TipoMovimento.ENTRATA,
            quantita=10.0,
            prezzoTotale=100.0,
            dataMovimento="2026-07-22",
            descrizione=desc_ok
        )
        self.assertEqual(len(m.descrizione), 500)

        # Oltre 500 caratteri deve sollevare ValueError
        desc_too_long = "A" * 501
        with self.assertRaises(ValueError):
            Movimento(
                idMovimento="M2",
                tipo=TipoMovimento.ENTRATA,
                quantita=10.0,
                prezzoTotale=100.0,
                dataMovimento="2026-07-22",
                descrizione=desc_too_long
            )

    def test_prodotto_calcoli(self):
        p = ProdottoAgricolo(
            idProdotto="P1",
            nome="Olio EVO",
            descrizione="Olio Extravergine",
            prezzoUnitario=12.0,
            quantitaDisponibile=100.0,
            tipoProdotto="Olio",
            unitaMisura="litri"
        )
        self.assertEqual(p.calcolaPrezzoTotale(5), 60.0)
        self.assertEqual(p.calcolaPrezzoScontato(5, 10), 54.0)

    def test_report_guadagno_rf22(self):
        movs = [
            Movimento("M1", TipoMovimento.ENTRATA, 10, 500.0, "2026-05-10", "Vendita olio"),
            Movimento("M2", TipoMovimento.ENTRATA, 5, 200.0, "2026-06-15", "Vendita vino"),
            Movimento("M3", TipoMovimento.USCITA, 1, 150.0, "2026-04-01", "Acquisto concime"),
            Movimento("M4", TipoMovimento.USCITA, 1, 50.0, "2025-04-01", "Spesa anno precedente")
        ]

        rep2026 = ReportGuadagno.genera(2026, movs)
        self.assertEqual(rep2026.totaleEntrate, 700.0)
        self.assertEqual(rep2026.totaleUscite, 150.0)
        self.assertEqual(rep2026.margineNetto, 550.0)

if __name__ == '__main__':
    unittest.main()
