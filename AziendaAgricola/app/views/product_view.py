from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox, QFormLayout,
    QHeaderView, QComboBox, QDialog, QAbstractItemView
)
from PyQt6.QtCore import Qt
from app.services import ProductService
from app.models import Prodotto, ProdottoAgricolo, MaterialeConsumo, ServizioEsterno, CategoriaProdotto

class ProductManagementView(QWidget):
    def __init__(self, product_service: ProductService, parent=None):
        super().__init__(parent)
        self.product_service = product_service
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Barra Azioni Superiore
        top_bar = QHBoxLayout()
        btn_add = QPushButton("+ Aggiungi Nuovo Prodotto Agricolo")
        btn_add.clicked.connect(self.show_add_product_dialog)

        btn_add_category = QPushButton("+ Aggiungi Nuova Categoria")
        btn_add_category.setStyleSheet("background-color: #0288d1; color: white; border: 1px solid #01579b;")
        btn_add_category.clicked.connect(self.show_add_category_dialog)

        btn_del_category = QPushButton("- Elimina Categoria")
        btn_del_category.setStyleSheet("background-color: #e65100; color: white; border: 1px solid #bf360c;")
        btn_del_category.clicked.connect(self.show_delete_category_dialog)

        btn_edit = QPushButton("Modifica Prodotto Selezionato")
        btn_edit.clicked.connect(self.show_edit_product_dialog)

        btn_del = QPushButton("- Elimina Prodotto")
        btn_del.setStyleSheet("background-color: #c62828; color: white; border: 1px solid #b71c1c;")
        btn_del.clicked.connect(self.handle_delete_product)

        top_bar.addWidget(btn_add)
        top_bar.addWidget(btn_add_category)
        top_bar.addWidget(btn_del_category)
        top_bar.addWidget(btn_edit)
        top_bar.addWidget(btn_del)
        top_bar.addStretch()

        main_layout.addLayout(top_bar)

        # Tabella Prodotti
        group = QGroupBox("Catalogo Prodotti Agricoli")
        g_layout = QVBoxLayout(group)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID Prodotto", "Nome Prodotto", "Categoria / Tipo", "Descrizione",
            "Prezzo Unitario (€)"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Disabilita modifica diretta dei campi
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        g_layout.addWidget(self.table)

        main_layout.addWidget(group)
        self.load_products_table()

    def load_products_table(self):
        prods = self.product_service.get_all_products()
        self.table.setRowCount(len(prods))

        for idx, p in enumerate(prods):
            self.table.setItem(idx, 0, QTableWidgetItem(p.idProdotto))
            self.table.setItem(idx, 1, QTableWidgetItem(p.nome))

            cat_str = getattr(p, 'tipoProdotto', getattr(p, 'tipoMateriale', getattr(p, 'fornitore', 'Generico')))
            self.table.setItem(idx, 2, QTableWidgetItem(cat_str))
            self.table.setItem(idx, 3, QTableWidgetItem(p.descrizione))
            self.table.setItem(idx, 4, QTableWidgetItem(f"€ {p.prezzoUnitario:.2f}"))

    def show_add_product_dialog(self):
        cats = self.product_service.get_all_categories()
        if not cats:
            QMessageBox.warning(
                self,
                "Attenzione",
                "Impossibile aggiungere un prodotto se prima non è stata inserita una categoria."
            )
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Aggiungi Nuovo Prodotto Agricolo")
        dlg.setFixedSize(400, 260)
        layout = QVBoxLayout(dlg)

        form = QFormLayout()
        cb_tipo = QComboBox()
        tipi = [c.nome for c in cats]
        cb_tipo.addItems(tipi)

        input_nome = QLineEdit()
        input_desc = QLineEdit()
        input_prezzo = QLineEdit("0.0")

        form.addRow("Tipo Prodotto / Categoria:", cb_tipo)
        form.addRow("Nome Prodotto (Unico):", input_nome)
        form.addRow("Descrizione:", input_desc)
        form.addRow("Prezzo Unitario (€):", input_prezzo)

        layout.addLayout(form)

        btn_save = QPushButton("Salva Prodotto")
        def save_action():
            try:
                tipo = cb_tipo.currentText().strip()
                if not tipo:
                    QMessageBox.warning(dlg, "Attenzione", "Impossibile aggiungere un prodotto se prima non è stata inserita una categoria.")
                    return

                nome = input_nome.text().strip()
                desc = input_desc.text().strip()
                prezzo = float(input_prezzo.text().strip() or "0")

                if not nome:
                    QMessageBox.warning(dlg, "Attenzione", "Inserire il nome del prodotto.")
                    return

                # Il software non si occupa di gestire le scorte, passiamo valori di default
                self.product_service.aggiungi_prodotto_agricolo(
                    nome=nome, descrizione=desc, prezzo=prezzo, unita="kg", tipo=tipo, quantita=0.0
                )

                QMessageBox.information(dlg, "Successo", f"Prodotto '{nome}' aggiunto con successo!")
                self.load_products_table()
                dlg.accept()
            except Exception as e:
                QMessageBox.critical(dlg, "Errore Inserimento", str(e))

        btn_save.clicked.connect(save_action)
        layout.addWidget(btn_save)
        dlg.exec()

    def show_edit_product_dialog(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Attenzione", "Selezionare un prodotto dalla tabella.")
            return

        pid = self.table.item(row, 0).text()
        prods = self.product_service.get_all_products()
        target = next((p for p in prods if p.idProdotto == pid), None)
        if not target:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Modifica Prodotto")
        dlg.setFixedSize(380, 240)
        layout = QVBoxLayout(dlg)

        form = QFormLayout()
        input_nome = QLineEdit(target.nome)
        input_desc = QLineEdit(target.descrizione)
        input_prezzo = QLineEdit(str(target.prezzoUnitario))

        form.addRow("Nome Prodotto:", input_nome)
        form.addRow("Descrizione:", input_desc)
        form.addRow("Prezzo Unitario (€):", input_prezzo)

        layout.addLayout(form)

        btn_save = QPushButton("Aggiorna Prodotto")
        def update_action():
            try:
                self.product_service.modifica_prodotto(
                    prodotto_id=pid,
                    nome=input_nome.text().strip(),
                    descrizione=input_desc.text().strip(),
                    prezzo=float(input_prezzo.text().strip()),
                    quantita=target.quantitaDisponibile # Mantiene la quantità invariata
                )
                QMessageBox.information(dlg, "Successo", "Prodotto aggiornato!")
                self.load_products_table()
                dlg.accept()
            except Exception as e:
                QMessageBox.critical(dlg, "Errore Modifica", str(e))

        btn_save.clicked.connect(update_action)
        layout.addWidget(btn_save)
        dlg.exec()

    def handle_delete_product(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Attenzione", "Selezionare un prodotto da eliminare.")
            return

        pid = self.table.item(row, 0).text()
        pname = self.table.item(row, 1).text()

        confirm = QMessageBox.question(
            self, "Conferma Eliminazione",
            f"Sei sicuro di voler eliminare il prodotto '{pname}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.product_service.elimina_prodotto(pid)
                QMessageBox.information(self, "Successo", "Prodotto eliminato.")
                self.load_products_table()
            except Exception as e:
                QMessageBox.critical(self, "Errore", str(e))

    def show_add_category_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Aggiungi Nuova Categoria")
        dlg.setFixedSize(350, 180)
        layout = QVBoxLayout(dlg)

        form = QFormLayout()
        input_nome = QLineEdit()
        
        cb_unita = QComboBox()
        cb_unita.addItems(["kilogrammi", "grammi", "litri"])

        form.addRow("Nome Categoria:", input_nome)
        form.addRow("Unità di Misura:", cb_unita)

        layout.addLayout(form)

        btn_save = QPushButton("Salva Categoria")
        def save_action():
            try:
                nome = input_nome.text().strip()
                unita = cb_unita.currentText()

                if not nome:
                    QMessageBox.warning(dlg, "Attenzione", "Inserire il nome della categoria.")
                    return

                self.product_service.aggiungi_categoria(nome=nome, unita=unita)
                QMessageBox.information(dlg, "Successo", f"Categoria '{nome}' aggiunta con successo!")
                dlg.accept()
            except Exception as e:
                QMessageBox.critical(dlg, "Errore Inserimento", str(e))

        btn_save.clicked.connect(save_action)
        layout.addWidget(btn_save)
        dlg.exec()

    def show_delete_category_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Elimina Categoria")
        dlg.setFixedSize(350, 180)
        layout = QVBoxLayout(dlg)

        form = QFormLayout()
        cb_cat = QComboBox()
        cats = [c.nome for c in self.product_service.get_all_categories()]
        cb_cat.addItems(cats)

        form.addRow("Seleziona Categoria:", cb_cat)
        layout.addLayout(form)

        btn_delete = QPushButton("Elimina Categoria e Prodotti Associati")
        btn_delete.setStyleSheet("background-color: #c62828; color: white; border: 1px solid #b71c1c;")
        
        def delete_action():
            cat_name = cb_cat.currentText()
            if not cat_name:
                QMessageBox.warning(dlg, "Attenzione", "Nessuna categoria selezionata.")
                return

            confirm = QMessageBox.question(
                dlg, "Conferma Eliminazione",
                f"Sei sicuro di voler eliminare la categoria '{cat_name}'?\nQuesto eliminerà anche TUTTI i prodotti associati ad essa!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                try:
                    self.product_service.elimina_categoria(cat_name)
                    QMessageBox.information(dlg, "Successo", f"Categoria '{cat_name}' e prodotti associati eliminati.")
                    self.load_products_table()
                    dlg.accept()
                except Exception as e:
                    QMessageBox.critical(dlg, "Errore", str(e))

        btn_delete.clicked.connect(delete_action)
        layout.addWidget(btn_delete)
        dlg.exec()

