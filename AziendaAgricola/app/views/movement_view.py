import os
import uuid
from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox, QFormLayout,
    QHeaderView, QComboBox, QDialog, QFileDialog, QTabWidget, QTextEdit,
    QDateEdit, QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate
from app.services import FinancialService, ProductService
from app.models import (
    Utente, TipoUscita, TipoMovimento, Movimento, Azienda, Privato, formatta_unita
)

class FinancialMovementView(QWidget):
    def __init__(self, financial_service: FinancialService, product_service: ProductService, current_user: Utente, parent=None):
        super().__init__(parent)
        self.financial_service = financial_service
        self.product_service = product_service
        self.current_user = current_user
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Tab Widget: Catalogo Entrate, Catalogo Uscite
        self.tabs = QTabWidget()

        self.tab_entrate = self.create_catalogo_widget(TipoMovimento.ENTRATA)
        self.tab_uscite = self.create_catalogo_widget(TipoMovimento.USCITA)

        self.tabs.addTab(self.tab_entrate, "Catalogo Entrate")
        self.tabs.addTab(self.tab_uscite, "Catalogo Uscite")

        # Pulsanti di registrazione e modifica in alto
        top_bar = QHBoxLayout()
        btn_new_entrata = QPushButton("+ Registra Nuova Entrata")
        btn_new_entrata.clicked.connect(self.show_new_entrata_dialog)

        btn_new_uscita = QPushButton("+ Registra Nuova Uscita")
        btn_new_uscita.setStyleSheet("background-color: #ff5858; color: white; border: 1px solid #ff5858;")
        btn_new_uscita.clicked.connect(self.show_new_uscita_dialog)

        btn_edit_mov = QPushButton("Modifica Movimento Selezionato")
        btn_edit_mov.setStyleSheet("background-color: #c88a00; color: white; border: 1px solid #a87400;")
        btn_edit_mov.clicked.connect(self.show_edit_movement_dialog)

        btn_delete_mov = QPushButton("- Rimuovi Movimento Selezionato")
        btn_delete_mov.setStyleSheet("background-color: #b71c1c; color: white; border: 1px solid #7f0000;")
        btn_delete_mov.clicked.connect(self.handle_delete_movement)

        top_bar.addWidget(btn_new_entrata)
        top_bar.addWidget(btn_new_uscita)
        top_bar.addWidget(btn_edit_mov)
        top_bar.addWidget(btn_delete_mov)
        top_bar.addStretch()

        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.tabs)

        self.load_tables()

    def create_catalogo_widget(self, tipo: TipoMovimento) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filtro per Anno e Categoria
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(QLabel("Filtra per Anno:"))
        cb_anno = QComboBox()
        cb_anno.addItem("Tutti gli anni")
        current_year = QDate.currentDate().year()
        # Consenti il bilancio/movimenti per gli ultimi 20 anni
        for y in range(current_year, current_year - 20, -1):
            cb_anno.addItem(str(y))

        filter_bar.addWidget(cb_anno)
        filter_bar.addStretch()

        btn_view_doc = QPushButton("Visualizza Allegato PDF")
        btn_view_doc.clicked.connect(lambda: self.handle_view_pdf(tipo))
        filter_bar.addWidget(btn_view_doc)

        layout.addLayout(filter_bar)

        # Tabella
        table = QTableWidget()
        if tipo == TipoMovimento.ENTRATA:
            table.setColumnCount(8)
            table.setHorizontalHeaderLabels([
                "Data", "Prodotto", "Categoria Prodotto", "Cliente",
                "Quantità", "Importo Totale (€)", "Descrizione", "Allegato PDF"
            ])
            # Interactive: permette di modificare la larghezza.
            # ResizeToContents: adatta la larghezza della colonna al contenuto.
            # Stretch: la colonna si espande per occupare lo spazio rimanente.
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
            table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        else:
            table.setColumnCount(7)
            table.setHorizontalHeaderLabels([
                "Data", "Categoria Spesa", "Fornitore",
                "Quantità", "Importo Totale (€)", "Descrizione", "Allegato PDF"
            ])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
            table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        # Disabilita modifica diretta cliccando sui campi
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Connetti click ed doppio click per visualizzazione dettagli
        table.itemClicked.connect(self.handle_table_click)
        table.itemDoubleClicked.connect(self.handle_table_double_click)

        # Mostra la tabella relativamente all'anno selezionato
        if tipo == TipoMovimento.ENTRATA:
            self.table_entrate = table
            cb_anno.currentTextChanged.connect(lambda: self.filter_table(TipoMovimento.ENTRATA, cb_anno.currentText()))
        else:
            self.table_uscite = table
            cb_anno.currentTextChanged.connect(lambda: self.filter_table(TipoMovimento.USCITA, cb_anno.currentText()))

        layout.addWidget(table)
        return widget

    def get_contact_name_and_details(self, contatto_id: Optional[str]) -> tuple[str, dict]:
        if not contatto_id:
            return "-", {}
        
        contacts = self.financial_service.repo.load_contacts()
        c = next((x for x in contacts if x.idContatto == contatto_id), None)
        if not c:
            return "-", {}
        
        if isinstance(c, Azienda):
            name = c.ragioneSociale
            details = {
                "Tipo": "Azienda",
                "Ragione Sociale": c.ragioneSociale,
                "Partita IVA": c.partitaIVA,
                "SDI": c.codiceDestinatarioSDI,
                "Email": c.email,
                "Telefono": c.telefono,
                "Indirizzo": c.indirizzo
            }
        elif isinstance(c, Privato):
            name = f"{c.Nome} {c.Cognome}"
            details = {
                "Tipo": "Privato",
                "Nome": c.Nome,
                "Cognome": c.Cognome,
                "Codice Fiscale": c.codiceFiscale,
                "Email": c.email,
                "Telefono": c.telefono,
                "Indirizzo": c.indirizzo
            }
        else:
            name = "-"
            details = {}
            
        return name, details

    def handle_contact_click(self, item):
        table = item.tableWidget()
        contact_col = 3 if (hasattr(self, 'table_entrate') and table == self.table_entrate) else 2
        if item.column() == contact_col:
            data = item.data(Qt.ItemDataRole.UserRole)
            if data:
                name, details = data
                main_win = self.window()
                if hasattr(main_win, 'statusBar') and main_win.statusBar:
                    main_win.statusBar.showMessage(f"Cliente/Fornitore selezionato: {name}")

    def handle_table_click(self, item):
        table = item.tableWidget()
        contact_col = 3 if (hasattr(self, 'table_entrate') and table == self.table_entrate) else 2
        desc_col = table.columnCount() - 2

        if item.column() == contact_col:
            self.handle_contact_click(item)
        elif item.column() == desc_col:
            row = item.row()
            tipo_str = "ENTRATA" if (hasattr(self, 'table_entrate') and table == self.table_entrate) else "USCITA"
            self.show_description_dialog(item.text(), mov_tipo=tipo_str)

    def handle_contact_double_click(self, item):
        table = item.tableWidget()
        contact_col = 3 if (hasattr(self, 'table_entrate') and table == self.table_entrate) else 2
        if item.column() == contact_col:
            data = item.data(Qt.ItemDataRole.UserRole)
            if data:
                name, details = data
                if not details:
                    return
                
                dlg = QDialog(self)
                dlg.setWindowTitle("Dettagli Contatto")
                dlg.setFixedSize(380, 320)
                dlg_layout = QVBoxLayout(dlg)
                
                form = QFormLayout()
                for key, val in details.items():
                    lbl_val = QLabel(str(val))
                    lbl_val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse) # Configura il tipo di interazione possibile col testo
                    lbl_val.setStyleSheet("color: #000000; font-size: 13px;")
                    form.addRow(f"<b>{key}:</b>", lbl_val)
                
                dlg_layout.addLayout(form)
                
                btn_close = QPushButton("Chiudi")
                btn_close.clicked.connect(dlg.accept)
                dlg_layout.addWidget(btn_close)
                
                dlg.exec()

    def show_description_dialog(self, description: str, mov_tipo: str = ""):
        """Finestra popup che mostra la descrizione completa del movimento selezionato."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Dettagli Descrizione")
        dlg.setFixedSize(420, 300)
        dlg_layout = QVBoxLayout(dlg)

        form = QFormLayout()
        if mov_tipo:
            lbl_tipo = QLabel(mov_tipo)
            lbl_tipo.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lbl_tipo.setStyleSheet("color: #000000; font-size: 13px;")
            form.addRow("<b>Tipo:</b>", lbl_tipo)
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

    def handle_table_double_click(self, item):
        table = item.tableWidget()
        contact_col = 3 if (hasattr(self, 'table_entrate') and table == self.table_entrate) else 2
        desc_col = table.columnCount() - 2

        if item.column() == contact_col:
            self.handle_contact_double_click(item)
        elif item.column() == desc_col:
            row = item.row()
            tipo_str = "ENTRATA" if (hasattr(self, 'table_entrate') and table == self.table_entrate) else "USCITA"
            self.show_description_dialog(item.text(), mov_tipo=tipo_str)


    def load_tables(self):
        movs = self.financial_service.get_all_movements()
        entrate = [m for m in movs if m.tipo == TipoMovimento.ENTRATA]
        uscite = [m for m in movs if m.tipo == TipoMovimento.USCITA]

        self.populate_table(self.table_entrate, entrate)
        self.populate_table(self.table_uscite, uscite)

    def populate_table(self, table: QTableWidget, mov_list: list):
        table.setRowCount(len(mov_list))
        prods = self.product_service.get_all_products()
        prod_map = {p.idProdotto: p for p in prods} # Crea un dizionario id - prodotto
        is_entrate = (hasattr(self, 'table_entrate') and table == self.table_entrate)   # True se la tabella è delle entrate

        for idx, m in enumerate(mov_list):  # idx numero di riga, m movimento
            # Data (entrate e uscite)
            try:
                date_obj = QDate.fromString(m.dataMovimento, "yyyy-MM-dd")
                date_formatted = date_obj.toString("dd/MM/yyyy")
            except Exception:
                date_formatted = m.dataMovimento
            item_date = QTableWidgetItem(date_formatted)
            item_date.setData(Qt.ItemDataRole.UserRole, m.idMovimento)  # Salva l'ID del movimento per operazioni future (quì per eliminare o modificare il movimento)
            table.setItem(idx, 0, item_date)

            # Nome prodotto (entrate)
            col = 1
            if is_entrate:
                p = prod_map.get(m.prodottoId) if m.prodottoId else None
                if p:
                    prod_str = p.nome
                elif m.prodottoNome:    # Se non ha ID ma ha il nome
                    prod_str = m.prodottoNome
                else:
                    prod_str = "-"
                item_prod = QTableWidgetItem(prod_str)
                item_prod.setToolTip(prod_str)  # Mostra nome completo quando mouse passa sopra cella
                table.setItem(idx, col, item_prod)
                col += 1

            # Categoria prodotto (entrate e uscite)
            cat = m.sottoTipoEntrata or m.sottoTipoUscita or "Generico"
            item_cat = QTableWidgetItem(cat)
            item_cat.setToolTip(cat)
            table.setItem(idx, col, item_cat)
            col += 1

            # Cliente / fornitore (entrate e uscite)
            name, details = self.get_contact_name_and_details(m.contattoId)
            if (name == "-" or not name) and m.contattoDescrizione:
                # Fallback parziale
                name = m.contattoDescrizione.split(",")[0].replace("Azienda: ", "").replace("Privato: ", "")
                # Se c'è un delimitatore pipe
                if "|" in name:
                    name = name.split("|")[0].strip()
            
            item_contact = QTableWidgetItem(name)
            item_contact.setData(Qt.ItemDataRole.UserRole, (name, details)) # Mostra i dettagli dietro il nome di privato o impresa
            table.setItem(idx, col, item_contact)
            col += 1

            # Quantità (entrate e uscite)
            table.setItem(idx, col, QTableWidgetItem(f"{m.quantita:.2f}"))
            col += 1

            # Prezzo totale (entrate e uscite)
            table.setItem(idx, col, QTableWidgetItem(f"€ {m.prezzoTotale:.2f}"))
            col += 1

            # Descrizione (entrate e uscite)
            item_desc = QTableWidgetItem(m.descrizione)
            item_desc.setToolTip(m.descrizione if m.descrizione else "(Nessuna descrizione)")
            table.setItem(idx, col, item_desc)
            col += 1

            # Allegato PDF (entrate e uscite)
            pdf_status = "Presente" if (m.documento and m.documento.allegatoPDF) else "Assente"
            item_pdf = QTableWidgetItem(pdf_status)
            if m.documento and m.documento.allegatoPDF:
                item_pdf.setData(Qt.ItemDataRole.UserRole, m.documento.allegatoPDF)
            table.setItem(idx, col, item_pdf)

    def filter_table(self, tipo: TipoMovimento, anno_str: str):
        movs = self.financial_service.get_all_movements()
        target_movs = [m for m in movs if m.tipo == tipo]

        if anno_str != "Tutti gli anni":
            target_movs = [m for m in target_movs if m.dataMovimento.startswith(anno_str)]

        if tipo == TipoMovimento.ENTRATA:
            self.populate_table(self.table_entrate, target_movs)
        else:
            self.populate_table(self.table_uscite, target_movs)

    # ---------------------------------------------------------
    # DIALOG REGISTRAZIONE ENTRATA
    # ---------------------------------------------------------
    def show_new_entrata_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Registrazione Nuova Entrata")
        dlg.setFixedSize(500, 580)
        layout = QVBoxLayout(dlg)

        form = QFormLayout()

        cb_categoria = QComboBox()
        cats = [c.nome for c in self.product_service.get_all_categories()]
        cb_categoria.addItems(cats)

        cb_prodotto = QComboBox()

        lbl_quantita = QLabel("Quantità:")

        def update_quantita_label():
            u = ""
            prod_id = cb_prodotto.currentData() # Recupera l'ID del prodotto
            if prod_id:
                prods = self.product_service.get_all_products()
                prod = next((p for p in prods if p.idProdotto == prod_id), None)
                if prod and getattr(prod, 'unitaMisura', None):
                    u = formatta_unita(prod.unitaMisura)
            if not u:
                selected_cat = cb_categoria.currentText().strip().upper()
                all_cats = self.product_service.get_all_categories()
                cat_obj = next((c for c in all_cats if c.nome.strip().upper() == selected_cat), None)
                if cat_obj and getattr(cat_obj, 'unitaMisura', None):
                    u = formatta_unita(cat_obj.unitaMisura)
            if u:
                lbl_quantita.setText(f"Quantità ({u}):")
            else:
                lbl_quantita.setText("Quantità:")

        def update_entrata_prodotto_combo():
            cb_prodotto.clear()
            selected_cat = cb_categoria.currentText()
            if not selected_cat:
                update_quantita_label()
                return
            prods = self.product_service.get_all_products()
            for p in prods:
                p_cat = getattr(p, 'tipoProdotto', 'Generico')
                if p_cat == selected_cat:
                    cb_prodotto.addItem(p.nome, p.idProdotto)
            update_quantita_label()

        cb_categoria.currentTextChanged.connect(update_entrata_prodotto_combo)
        cb_prodotto.currentIndexChanged.connect(lambda _: update_quantita_label())
        update_entrata_prodotto_combo()

        cb_cliente_tipo = QComboBox()
        cb_cliente_tipo.addItems(["Azienda", "Privato"])

        input_data = QDateEdit()
        input_data.setCalendarPopup(True)
        input_data.setDate(QDate.currentDate())

        input_importo = QLineEdit("0.0")
        input_quantita = QLineEdit("1.0")

        input_c_nome = QLineEdit()
        input_c_piva_cf = QLineEdit()
        input_c_email = QLineEdit()

        # Descrizione movimento (max 500 caratteri)
        input_desc = QTextEdit()
        input_desc.setMaximumHeight(80)

        # File PDF
        self.selected_pdf_entrata = ""
        btn_attach_pdf = QPushButton("Allega Documento PDF")
        lbl_pdf_name = QLabel("Nessun allegato")

        def attach_action():
            path, _ = QFileDialog.getOpenFileName(dlg, "Seleziona Documento PDF", "", "File PDF (*.pdf);;Tutti i file (*.*)")   # Restutuisce path e filtro (ignorato). dlg è la finestra di dialogo (esterna)
            if path:
                self.selected_pdf_entrata = path
                lbl_pdf_name.setText(os.path.basename(path))

        btn_attach_pdf.clicked.connect(attach_action)

        form.addRow("Categoria Prodotto:", cb_categoria)
        form.addRow("Prodotto:", cb_prodotto)
        form.addRow("Tipo Cliente:", cb_cliente_tipo)
        form.addRow("Data Vendita:", input_data)
        form.addRow("Importo Totale (€):", input_importo)
        form.addRow(lbl_quantita, input_quantita)
        form.addRow("Nome Cliente / Ragione Soc.:", input_c_nome)
        form.addRow("P.IVA / Codice Fiscale:", input_c_piva_cf)
        form.addRow("Email / Telefono:", input_c_email)
        form.addRow("Descrizione (max 500 char):", input_desc)
        form.addRow(btn_attach_pdf, lbl_pdf_name)

        layout.addLayout(form)

        btn_save = QPushButton("Conferma Registrazione Entrata")
        def save_action():
            try:
                cat = cb_categoria.currentText()
                prod_idx = cb_prodotto.currentIndex()
                if prod_idx < 0:
                    QMessageBox.warning(dlg, "Attenzione", "Selezionare un prodotto per registrare il movimento. Se non ci sono prodotti, è necessario registrarli prima.")
                    return
                prodotto_id = cb_prodotto.currentData()

                c_tipo = cb_cliente_tipo.currentText()
                dt = input_data.date().toString("yyyy-MM-dd")
                importo = float(input_importo.text().strip() or "0")
                qta = float(input_quantita.text().strip() or "0")
                desc = input_desc.toPlainText().strip() #toPlainText rimuove le formattazioni HTML

                if len(desc) > 500:
                    QMessageBox.warning(dlg, "Attenzione", "La descrizione supera il limite di 500 caratteri.")
                    return

                c_details = {
                    "ragioneSociale": input_c_nome.text().strip() if c_tipo == "Azienda" else "",
                    "Nome": input_c_nome.text().strip() if c_tipo == "Privato" else "",
                    "partitaIVA": input_c_piva_cf.text().strip() if c_tipo == "Azienda" else "",
                    "codiceFiscale": input_c_piva_cf.text().strip() if c_tipo == "Privato" else "",
                    "email": input_c_email.text().strip()
                }

                self.financial_service.registra_entrata(
                    categoria_prodotto=cat,
                    prodotto_id=prodotto_id,
                    cliente_tipo=c_tipo,
                    importo=importo,
                    quantita=qta,
                    data=dt,
                    descrizione=desc,
                    cliente_dettagli=c_details,
                    pdf_path=self.selected_pdf_entrata or None,
                    username=self.current_user.nomeUtente
                )

                QMessageBox.information(dlg, "Successo", "Entrata registrata con successo!")
                self.load_tables()
                
                # Ricalcola bilancio dinamico se possibile
                main_win = self.window()
                if hasattr(main_win, 'report_view') and hasattr(main_win.report_view, 'handle_calculate_report'):
                    main_win.report_view.handle_calculate_report()

                dlg.accept()
            except Exception as e:
                QMessageBox.critical(dlg, "Errore", str(e))

        btn_save.clicked.connect(save_action)
        layout.addWidget(btn_save)
        dlg.exec()

    # ---------------------------------------------------------
    # DIALOG REGISTRAZIONE USCITA
    # ---------------------------------------------------------
    def show_new_uscita_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Registrazione Nuova Uscita / Spesa")
        dlg.setFixedSize(500, 420)
        layout = QVBoxLayout(dlg)

        form = QFormLayout()

        cb_categoria = QComboBox()
        cb_categoria.addItems([e.value for e in TipoUscita])

        input_data = QDateEdit()
        input_data.setCalendarPopup(True)
        input_data.setDate(QDate.currentDate())

        input_importo = QLineEdit("0.0")
        
        input_fornitore = QLineEdit()
        input_fornitore.setPlaceholderText("Fornitore / Ente Emettitore / Note Spesa")

        # Descrizione movimento (max 500 caratteri)
        input_desc = QTextEdit()
        input_desc.setMaximumHeight(80)

        # File PDF
        self.selected_pdf_uscita = ""
        btn_attach_pdf = QPushButton("Allega Documento / Ricevuta PDF")
        lbl_pdf_name = QLabel("Nessun allegato")

        def attach_action():
            path, _ = QFileDialog.getOpenFileName(dlg, "Seleziona Ricevuta PDF", "", "File PDF (*.pdf);;Tutti i file (*.*)")
            if path:
                self.selected_pdf_uscita = path
                lbl_pdf_name.setText(os.path.basename(path))

        btn_attach_pdf.clicked.connect(attach_action)

        form.addRow("Categoria Spesa:", cb_categoria)
        form.addRow("Data Pagamento:", input_data)
        form.addRow("Importo Totale (€):", input_importo)
        form.addRow("Fornitore / Ente:", input_fornitore)
        form.addRow("Descrizione (max 500 char):", input_desc)
        form.addRow(btn_attach_pdf, lbl_pdf_name)

        layout.addLayout(form)

        btn_save = QPushButton("Conferma Registrazione Uscita")
        btn_save.setStyleSheet("background-color: #d84315; color: white;")
        def save_action():
            try:
                cat = cb_categoria.currentText()
                dt = input_data.date().toString("yyyy-MM-dd")
                importo = float(input_importo.text().strip() or "0")
                forn = input_fornitore.text().strip()
                desc = input_desc.toPlainText().strip()

                if len(desc) > 500:
                    QMessageBox.warning(dlg, "Attenzione", "La descrizione supera il limite di 500 caratteri.")
                    return

                self.financial_service.registra_uscita(
                    categoria_uscita=cat,
                    prodotto_id=None,
                    importo=importo,
                    data=dt,
                    descrizione=desc,
                    fornitore_note=forn,
                    pdf_path=self.selected_pdf_uscita or None,
                    username=self.current_user.nomeUtente
                )

                QMessageBox.information(dlg, "Successo", "Uscita registrata con successo!")
                self.load_tables()
                
                # Ricalcola bilancio dinamico se possibile
                main_win = self.window()
                if hasattr(main_win, 'report_view') and hasattr(main_win.report_view, 'handle_calculate_report'):
                    main_win.report_view.handle_calculate_report()

                dlg.accept()
            except Exception as e:
                QMessageBox.critical(dlg, "Errore", str(e))

        btn_save.clicked.connect(save_action)
        layout.addWidget(btn_save)
        dlg.exec()

    # ---------------------------------------------------------
    # DIALOG MODIFICA MOVIMENTO
    # ---------------------------------------------------------
    def show_edit_movement_dialog(self):
        active_tab_index = self.tabs.currentIndex()
        table = self.table_entrate if active_tab_index == 0 else self.table_uscite
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Attenzione", "Selezionare un movimento dalla tabella attiva.")
            return

        mid = table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        movs = self.financial_service.get_all_movements()
        target = next((m for m in movs if m.idMovimento == mid), None)
        if not target:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Modifica Movimento Finanziario")
        dlg.setFixedSize(450, 400)
        layout = QVBoxLayout(dlg)

        form = QFormLayout()

        input_data = QDateEdit()
        input_data.setCalendarPopup(True)
        try:
            curr_date = QDate.fromString(target.dataMovimento, "yyyy-MM-dd")
            input_data.setDate(curr_date)
        except Exception:
            input_data.setDate(QDate.currentDate())

        input_importo = QLineEdit(str(target.prezzoTotale))
        input_quantita = QLineEdit(str(target.quantita))
        input_desc = QTextEdit(target.descrizione)
        input_desc.setMaximumHeight(80)

        lbl_qta_text = "Quantità:"
        if target.tipo == TipoMovimento.ENTRATA:
            u = ""
            if target.prodottoId:
                p = next((x for x in self.product_service.get_all_products() if x.idProdotto == target.prodottoId), None)
                if p and getattr(p, 'unitaMisura', None):
                    u = formatta_unita(p.unitaMisura)
            if not u and target.sottoTipoEntrata:
                all_cats = self.product_service.get_all_categories()
                c_obj = next((c for c in all_cats if c.nome.strip().upper() == target.sottoTipoEntrata.strip().upper()), None)
                if c_obj and getattr(c_obj, 'unitaMisura', None):
                    u = formatta_unita(c_obj.unitaMisura)
            if u:
                lbl_qta_text = f"Quantità ({u}):"

        form.addRow("Data Movimento:", input_data)
        form.addRow("Importo Totale (€):", input_importo)
        form.addRow(lbl_qta_text, input_quantita)
        form.addRow("Descrizione (max 500 char):", input_desc)

        layout.addLayout(form)

        btn_save = QPushButton("Salva Modifiche")
        def save_action():
            try:
                dt = input_data.date().toString("yyyy-MM-dd")
                importo = float(input_importo.text().strip() or "0")
                qta = float(input_quantita.text().strip() or "0")
                desc = input_desc.toPlainText().strip()

                if len(desc) > 500:
                    QMessageBox.warning(dlg, "Attenzione", "La descrizione supera il limite di 500 caratteri.")
                    return

                # Aggiorna gli attributi del movimento
                target.dataMovimento = dt
                target.prezzoTotale = importo
                target.quantita = qta
                target.descrizione = desc

                # Salva su database
                self.financial_service.repo.save_movements(movs)

                QMessageBox.information(dlg, "Successo", "Movimento modificato con successo!")
                self.load_tables()
                
                # Forza il ricalcolo del bilancio nel report
                main_win = self.window()
                if hasattr(main_win, 'report_view') and hasattr(main_win.report_view, 'handle_calculate_report'):
                    main_win.report_view.handle_calculate_report()

                dlg.accept()
            except Exception as e:
                QMessageBox.critical(dlg, "Errore", str(e))

        btn_save.clicked.connect(save_action)
        layout.addWidget(btn_save)
        dlg.exec()

    # ---------------------------------------------------------
    # RIMOZIONE MOVIMENTO
    # ---------------------------------------------------------
    def handle_delete_movement(self):
        active_tab_index = self.tabs.currentIndex()
        table = self.table_entrate if active_tab_index == 0 else self.table_uscite
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Attenzione", "Selezionare un movimento da rimuovere.")
            return

        mid = table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        confirm = QMessageBox.question(
            self, "Conferma Rimozione",
            "Sei sicuro di voler rimuovere il movimento finanziario selezionato?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.financial_service.elimina_movimento(mid)
                
                QMessageBox.information(self, "Successo", "Movimento rimosso con successo.")
                self.load_tables()
                
                # Ricalcola bilancio dinamico se possibile
                main_win = self.window()
                if hasattr(main_win, 'report_view') and hasattr(main_win.report_view, 'handle_calculate_report'):
                    main_win.report_view.handle_calculate_report()
            except Exception as e:
                QMessageBox.critical(self, "Errore", str(e))

    def handle_view_pdf(self, tipo: TipoMovimento):
        table = self.table_entrate if tipo == TipoMovimento.ENTRATA else self.table_uscite
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Attenzione", "Selezionare una riga dalla tabella per visualizzare il relativo allegato PDF.")
            return

        pdf_col = table.columnCount() - 1
        pdf_item = table.item(row, pdf_col)
        pdf_path = pdf_item.data(Qt.ItemDataRole.UserRole)

        if not pdf_path or not os.path.exists(pdf_path):
            QMessageBox.information(self, "Informazione Documento", "Nessun documento PDF allegato a questo movimento finanziario.")
            return

        # Apri il documento con l'applicazione di sistema o mostra anteprima
        try:
            os.startfile(pdf_path)
        except Exception as e:
            QMessageBox.information(self, "Visualizzatore PDF", f"Allegato presente presso:\n{pdf_path}")
