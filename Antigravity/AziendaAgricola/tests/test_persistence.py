import unittest
import tempfile
import shutil
import os
from app.repositories import DataRepository
from app.services import UserManager, ProductService, FinancialService

class TestPersistence(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo = DataRepository(data_dir=self.temp_dir)
        self.user_manager = UserManager(self.repo)
        self.product_service = ProductService(self.repo)
        self.financial_service = FinancialService(self.repo)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_json_persistence(self):
        # 1. Popola dati
        self.user_manager.registra_primo_manager(
            "m1", "Pass1234", "Mario", "Rossi", "mario@azienda.it", "123", "1980-01-01"
        )
        self.product_service.aggiungi_categoria("MIELE", "grammi")
        prod = self.product_service.aggiungi_prodotto_agricolo(
            "Miele Acacia", "Miele biologico", 8.5, "grammi", "MIELE", 50.0
        )
        self.financial_service.registra_entrata(
            "MIELE", prod.idProdotto, "Privato", 425.0, "2026-07-22", "Vendita miele"
        )

        # 2. Crea una nuova istanza di DataRepository che legge dalla stessa cartella
        repo_reload = DataRepository(data_dir=self.temp_dir)

        users = repo_reload.load_users()
        categories = repo_reload.load_categories()
        products = repo_reload.load_products()
        movements = repo_reload.load_movements()

        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].nomeUtente, "m1")
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0].nome, "MIELE")
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].nome, "Miele Acacia")
        self.assertEqual(len(movements), 1)
        self.assertEqual(movements[0].prezzoTotale, 425.0)

if __name__ == '__main__':
    unittest.main()
