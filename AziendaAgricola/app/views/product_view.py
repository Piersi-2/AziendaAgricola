from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox, QFormLayout,
    QHeaderView, QComboBox, QDialog, QAbstractItemView, QTextEdit
)
from PyQt5.QtCore import Qt
from app.services import ProductService
from app.models import Prodotto, CategoriaProdotto, formatta_unita

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

        btn_add_category = QPushButton("+ Aggiungi Nuova Categoria")
        btn_add_category.setStyleSheet("background-color: #1b5e20; color: white; border: 1px solid #144718;")
        btn_add_category.clicked.connect(self.show_add_category_dialog)

        btn_add = QPushButton("+ Aggiungi Nuovo Prodotto Agricolo")
        btn_add.clicked.connect(self.show_add_product_dialog)

        btn_edit = QPushButton("Modifica Prodotto Selezionato")
        btn_edit.setStyleSheet("background-color: #c88a00; color: white; border: 1px solid #a87400;")
        btn_edit.clicked.connect(self.show_edit_product_dialog)

        btn_del = QPushButton("- Elimina Prodotto Agricolo")
        btn_del.setStyleSheet("background-color: #ff5858; color: white; border: 1px solid #ff5858;")
        btn_del.clicked.connect(self.handle_delete_product)

        btn_del_category = QPushButton("- Elimina Categoria")
        btn_del_category.setStyleSheet("background-color: #b71c1c; color: white; border: 1px solid #7f0000;")
        btn_del_category.clicked.connect(self.show_delete_category_dialog)

        top_bar.addWidget(btn_add_category)
        top_bar.addWidget(btn_add)
        top_bar.addWidget(btn_edit)
        top_bar.addWidget(btn_del)
        top_bar.addWidget(btn_del_category)
        top_bar.addStretch()

        main_layout.addLayout(top_bar)

        # Tabella Prodotti
        group = QGroupBox("Catalogo Prodotti Agricoli")
        g_layout = QVBoxLayout(group)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Nome Prodotto", "Categoria / Tipo", "Quantità di Vendita", "Descrizione",
            "Prezzo Unitario (€)"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Disabilita modifica diretta dei campi
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Connetti click per visualizzazione della descrizione completa
        self.table.itemClicked.connect(self.handle_table_click)
        self.table.itemDoubleClicked.connect(self.handle_table_click)
        
        g_layout.addWidget(self.table)

        main_layout.addWidget(group)
        self.load_products_table()

    def show_description_dialog(self, nome: str, description: str):
        """Finestra popup che mostra la descrizione completa del prodotto selezionato."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Dettagli Descrizione Prodotto")
        dlg.setFixedSize(420, 300)
        dlg_layout = QVBoxLayout(dlg)

        form = QFormLayout()
        if nome:
            lbl_nome = QLabel(nome)
            lbl_nome.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lbl_nome.setStyleSheet("color: #000000; font-size: 13px;")
            form.addRow("<b>Nome Prodotto:</b>", lbl_nome)
        dlg_layout.addLayout(form)

        lbl_desc_title = QLabel("<b>Descrizione Completa:</b>")
        lbl_desc_title.setStyleSheet("color: #000000; font-size: 13px; margin-top: 5px;")
        dlg_layout.addWidget(lbl_desc_title)

        txt_desc = QTextEdit()
        txt_desc.setReadOnly(True)
        txt_desc.setPlainText(description if description.strip() else "(Nessuna descrizione presente)")
        txt_desc.setStyleSheet("color: #000000; font-size: 13px; background-color: #f9f9f9; border: 1px solid #cccccc; border-radius: 4px; padding: 6px;")
        dlg_layout.addWidget(txt_desc)

        btn_close = QPushButton("Chiudi")
        btn_close.clicked.connect(dlg.accept)
        dlg_layout.addWidget(btn_close)

        dlg.exec()

    def handle_table_click(self, item: QTableWidgetItem):
        if item.column() == 3:  # Colonna Descrizione
            row = item.row()
            p_nome = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
            self.show_description_dialog(p_nome, item.text())

    def load_products_table(self):
        prods = self.product_service.get_all_products()
        self.table.setRowCount(len(prods))

        for idx, p in enumerate(prods):
            tipo = getattr(p, 'tipoProdotto', 'Agricolo')
            unita = formatta_unita(getattr(p, 'unitaMisura', ''))
            q_val = getattr(p, 'quantitaVendita', 1.0)
            q_str = f"{q_val:g} {unita}".strip() if q_val else "-"

            item_nome = QTableWidgetItem(p.nome)
            item_nome.setData(Qt.ItemDataRole.UserRole, p.idProdotto)
            self.table.setItem(idx, 0, item_nome)
            self.table.setItem(idx, 1, QTableWidgetItem(tipo))
            self.table.setItem(idx, 2, QTableWidgetItem(q_str))

            item_desc = QTableWidgetItem(p.descrizione)
            item_desc.setToolTip(p.descrizione if p.descrizione else "(Nessuna descrizione)")
            self.table.setItem(idx, 3, item_desc)

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
        dlg.setFixedSize(400, 300)
        layout = QVBoxLayout(dlg)

        cat_unita_map = {c.nome.strip().upper(): formatta_unita(c.unitaMisura) for c in cats}

        form = QFormLayout()
        cb_tipo = QComboBox()
        tipi = [c.nome for c in cats]
        cb_tipo.addItems(tipi)

        input_nome = QLineEdit()
        input_quantita = QLineEdit("1.0")
        input_desc = QLineEdit()
        input_prezzo = QLineEdit("0.0")

        lbl_quantita = QLabel("Quantità di Vendita:")
        def update_quantita_label():
            sel_cat = cb_tipo.currentText().strip().upper()
            u = cat_unita_map.get(sel_cat, "")
            if u:
                lbl_quantita.setText(f"Quantità di Vendita ({u}):")
            else:
                lbl_quantita.setText("Quantità di Vendita:")

        cb_tipo.currentTextChanged.connect(update_quantita_label)
        update_quantita_label()

        form.addRow("Tipo Prodotto / Categoria:", cb_tipo)
        form.addRow("Nome Prodotto:", input_nome)
        form.addRow(lbl_quantita, input_quantita)
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
                quantita = float(input_quantita.text().strip() or "1")

                if not nome:
                    QMessageBox.warning(dlg, "Attenzione", "Inserire il nome del prodotto.")
                    return
                if quantita <= 0:
                    QMessageBox.warning(dlg, "Attenzione", "La quantità di vendita deve essere maggiore di zero.")
                    return

                sel_cat_obj = next((c for c in cats if c.nome.strip().upper() == tipo.strip().upper()), None)
                unita_effettiva = sel_cat_obj.unitaMisura if sel_cat_obj else "kg"

                self.product_service.aggiungi_prodotto_agricolo(
                    nome=nome, descrizione=desc, prezzo=prezzo, unita=unita_effettiva, tipo=tipo, quantita=quantita
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

        pid = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
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
        input_quantita = QLineEdit(f"{target.quantitaVendita:g}")
        input_desc = QLineEdit(target.descrizione)
        input_prezzo = QLineEdit(str(target.prezzoUnitario))

        u = formatta_unita(getattr(target, 'unitaMisura', ''))
        lbl_qta_text = f"Quantità di Vendita ({u}):" if u else "Quantità di Vendita:"

        form.addRow("Nome Prodotto:", input_nome)
        form.addRow(lbl_qta_text, input_quantita)
        form.addRow("Descrizione:", input_desc)
        form.addRow("Prezzo Unitario (€):", input_prezzo)

        layout.addLayout(form)

        btn_save = QPushButton("Aggiorna Prodotto")
        def update_action():
            try:
                quantita = float(input_quantita.text().strip() or "1")
                if quantita <= 0:
                    QMessageBox.warning(dlg, "Attenzione", "La quantità di vendita deve essere maggiore di zero.")
                    return
                self.product_service.modifica_prodotto(
                    prodotto_id=pid,
                    nome=input_nome.text().strip(),
                    descrizione=input_desc.text().strip(),
                    prezzo=float(input_prezzo.text().strip()),
                    quantita=quantita
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

        pid = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        pname = self.table.item(row, 0).text()

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
