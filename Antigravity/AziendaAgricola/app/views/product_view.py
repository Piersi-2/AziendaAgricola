from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox, QFormLayout,
    QHeaderView, QComboBox, QDialog
)
from PyQt6.QtCore import Qt
from app.services import ProductService
from app.models import Prodotto, ProdottoAgricolo, MaterialeConsumo, ServizioEsterno, TipoEntrata

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

        btn_edit = QPushButton("Modifica Prodotto Selezionato")
        btn_edit.clicked.connect(self.show_edit_product_dialog)

        btn_del = QPushButton("- Elimina Prodotto")
        btn_del.setStyleSheet("background-color: #c62828;")
        btn_del.clicked.connect(self.handle_delete_product)

        top_bar.addWidget(btn_add)
        top_bar.addWidget(btn_edit)
        top_bar.addWidget(btn_del)
        top_bar.addStretch()

        main_layout.addLayout(top_bar)

        # Tabella Prodotti
        group = QGroupBox("Catalogo Prodotti Agricoli e Materiali")
        g_layout = QVBoxLayout(group)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID Prodotto", "Nome Prodotto", "Categoria / Tipo", "Descrizione",
            "Prezzo Unitario (€)", "Quantità Disponibile", "Unità Misura"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
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
            self.table.setItem(idx, 4, QTableWidgetItem(f"{p.prezzoUnitario:.2f}"))
            self.table.setItem(idx, 5, QTableWidgetItem(f"{p.quantitaDisponibile:.2f}"))

            unita_str = getattr(p, 'unitaMisura', 'unità')
            self.table.setItem(idx, 6, QTableWidgetItem(unita_str))

    def show_add_product_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Aggiungi Nuovo Prodotto Agricolo")
        dlg.setFixedSize(400, 360)
        layout = QVBoxLayout(dlg)

        form = QFormLayout()
        cb_tipo = QComboBox()
        cb_tipo.addItems([e.value for e in TipoEntrata] + ["Materiale Consumo", "Servizio Esterno"])

        input_nome = QLineEdit()
        input_desc = QLineEdit()
        input_prezzo = QLineEdit("0.0")
        input_quantita = QLineEdit("0.0")
        input_unita = QComboBox()
        input_unita.addItems(["kg", "litri", "bottiglie", "quintali", "pezzi"])

        form.addRow("Tipo Prodotto / Categoria:", cb_tipo)
        form.addRow("Nome Prodotto (Unico):", input_nome)
        form.addRow("Descrizione:", input_desc)
        form.addRow("Prezzo Unitario (€):", input_prezzo)
        form.addRow("Quantità Iniziale:", input_quantita)
        form.addRow("Unità di Misura:", input_unita)

        layout.addLayout(form)

        btn_save = QPushButton("Salva Prodotto")
        def save_action():
            try:
                nome = input_nome.text().strip()
                desc = input_desc.text().strip()
                prezzo = float(input_prezzo.text().strip() or "0")
                qta = float(input_quantita.text().strip() or "0")
                tipo = cb_tipo.currentText()
                unita = input_unita.currentText()

                if not nome:
                    QMessageBox.warning(dlg, "Attenzione", "Inserire il nome del prodotto.")
                    return

                if tipo in [e.value for e in TipoEntrata]:
                    self.product_service.aggiungi_prodotto_agricolo(
                        nome=nome, descrizione=desc, prezzo=prezzo, unita=unita, tipo=tipo, quantita=qta
                    )
                else:
                    self.product_service.aggiungi_materiale(
                        nome=nome, descrizione=desc, prezzo=prezzo, tipo_materiale=tipo, quantita=qta
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
        dlg.setFixedSize(380, 280)
        layout = QVBoxLayout(dlg)

        form = QFormLayout()
        input_nome = QLineEdit(target.nome)
        input_desc = QLineEdit(target.descrizione)
        input_prezzo = QLineEdit(str(target.prezzoUnitario))
        input_quantita = QLineEdit(str(target.quantitaDisponibile))

        form.addRow("Nome Prodotto:", input_nome)
        form.addRow("Descrizione:", input_desc)
        form.addRow("Prezzo Unitario (€):", input_prezzo)
        form.addRow("Quantità Disponibile:", input_quantita)

        layout.addLayout(form)

        btn_save = QPushButton("Aggiorna Prodotto")
        def update_action():
            try:
                self.product_service.modifica_prodotto(
                    prodotto_id=pid,
                    nome=input_nome.text().strip(),
                    descrizione=input_desc.text().strip(),
                    prezzo=float(input_prezzo.text().strip()),
                    quantita=float(input_quantita.text().strip())
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
