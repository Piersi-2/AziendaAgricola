import unittest
import tempfile
import shutil
import os
from app.repositories import DataRepository
from app.services import UserManager, ProductService, FinancialService

class TestPersistenceAndBackup(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo = DataRepository(data_dir=self.temp_dir)
        self.user_manager = UserManager(self.repo)
        self.product_service = ProductService(self.repo)
        self.financial_service = FinancialService(self.repo)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_backup_and_restore_rf23(self):
        # 1. Popola dati
        self.user_manager.registra_primo_manager(
            "m1", "Pass1234", "Mario", "Rossi", "mario@azienda.it", "123", "1980-01-01"
        )
        self.product_service.aggiungi_prodotto_agricolo(
            "Miele Acacia", "Miele biologico", 8.5, "vasetti", "Miele", 50.0
        )
        self.financial_service.registra_entrata(
            "MIELE", "Privato", 425.0, 50.0, "2026-07-22", "Vendita miele"
        )

        self.assertEqual(len(self.repo.load_users()), 1)
        self.assertEqual(len(self.repo.load_products()), 1)
        self.assertEqual(len(self.repo.load_movements()), 1)

        # 2. Esegui backup
        backup_folder = self.repo.esegui_backup()
        self.assertTrue(os.path.exists(backup_folder))

        # 3. Svuota il database corrente
        self.repo.save_users([])
        self.repo.save_products([])
        self.repo.save_movements([])

        self.assertEqual(len(self.repo.load_users()), 0)
        self.assertEqual(len(self.repo.load_products()), 0)
        self.assertEqual(len(self.repo.load_movements()), 0)

        # 4. Ripristina da backup
        self.repo.ripristina_dati(backup_folder)

        # 5. Verifica che i dati siano stati completamente ripristinati
        self.assertEqual(len(self.repo.load_users()), 1)
        self.assertEqual(len(self.repo.load_products()), 1)
        self.assertEqual(len(self.repo.load_movements()), 1)
        self.assertEqual(self.repo.load_products()[0].nome, "Miele Acacia")

if __name__ == '__main__':
    unittest.main()
