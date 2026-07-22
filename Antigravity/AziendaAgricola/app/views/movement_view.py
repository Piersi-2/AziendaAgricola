import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox, QFormLayout,
    QHeaderView, QComboBox, QDialog, QFileDialog, QTabWidget, QTextEdit,
    QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from app.services import FinancialService, ProductService
from app.models import (
    Utente, TipoEntrata, TipoUscita, TipoMovimento, Movimento
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

        # Tab Widget: Nuova Entrata, Nuova Uscita, Catalogo Entrate (RF20), Catalogo Uscite (RF21)
        self.tabs = QTabWidget()

        self.tab_entrate = self.create_catalogo_widget(TipoMovimento.ENTRATA)
        self.tab_uscite = self.create_catalogo_widget(TipoMovimento.USCITA)

        self.tabs.addTab(self.tab_entrate, "Catalogo Entrate (RF20)")
        self.tabs.addTab(self.tab_uscite, "Catalogo Uscite (RF21)")

        # Pulsanti di registrazione in alto
        top_bar = QHBoxLayout()
        btn_new_entrata = QPushButton("+ Registra Nuova Entrata (RF9/RF10)")
        btn_new_entrata.clicked.connect(self.show_new_entrata_dialog)

        btn_new_uscita = QPushButton("+ Registra Nuova Uscita (RF11-RF18)")
        btn_new_uscita.setStyleSheet("background-color: #d84315;")
        btn_new_uscita.clicked.connect(self.show_new_uscita_dialog)

        top_bar.addWidget(btn_new_entrata)
        top_bar.addWidget(btn_new_uscita)
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
        for y in range(current_year, current_year - 5, -1):
            cb_anno.addItem(str(y))

        filter_bar.addWidget(cb_anno)
        filter_bar.addStretch()

        btn_view_doc = QPushButton("Visualizza Allegato PDF (RF19)")
        btn_view_doc.clicked.connect(lambda: self.handle_view_pdf(tipo))
        filter_bar.addWidget(btn_view_doc)

        layout.addLayout(filter_bar)

        # Tabella
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "ID Movimento", "Data", "Categoria Prodotto / Spesa", "Cliente / Fornitore",
            "Quantità", "Importo Totale (€)", "Descrizione", "Allegato PDF"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        if tipo == TipoMovimento.ENTRATA:
            self.table_entrate = table
            cb_anno.currentTextChanged.connect(lambda: self.filter_table(TipoMovimento.ENTRATA, cb_anno.currentText()))
        else:
            self.table_uscite = table
            cb_anno.currentTextChanged.connect(lambda: self.filter_table(TipoMovimento.USCITA, cb_anno.currentText()))

        layout.addWidget(table)
        return widget

    def load_tables(self):
        movs = self.financial_service.get_all_movements()
        entrate = [m for m in movs if m.tipo == TipoMovimento.ENTRATA]
        uscite = [m for m in movs if m.tipo == TipoMovimento.USCITA]

        self.populate_table(self.table_entrate, entrate)
        self.populate_table(self.table_uscite, uscite)

    def populate_table(self, table: QTableWidget, mov_list: list):
        table.setRowCount(len(mov_list))
        for idx, m in enumerate(mov_list):
            table.setItem(idx, 0, QTableWidgetItem(m.idMovimento))
            table.setItem(idx, 1, QTableWidgetItem(m.dataMovimento))

            cat = m.sottoTipoEntrata or m.sottoTipoUscita or "Generico"
            table.setItem(idx, 2, QTableWidgetItem(cat))
            table.setItem(idx, 3, QTableWidgetItem(m.contattoDescrizione or "-"))
            table.setItem(idx, 4, QTableWidgetItem(f"{m.quantita:.2f}"))
            table.setItem(idx, 5, QTableWidgetItem(f"€ {m.prezzoTotale:.2f}"))
            table.setItem(idx, 6, QTableWidgetItem(m.descrizione))

            pdf_status = "Presente" if (m.documento and m.documento.allegatoPDF) else "Assente"
            item_pdf = QTableWidgetItem(pdf_status)
            if m.documento and m.documento.allegatoPDF:
                item_pdf.setData(Qt.ItemDataRole.UserRole, m.documento.allegatoPDF)
            table.setItem(idx, 7, item_pdf)

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
        dlg.setWindowTitle("Registrazione Nuova Entrata (RF9/RF10)")
        dlg.setFixedSize(500, 560)
        layout = QVBoxLayout(dlg)

        form = QFormLayout()

        cb_categoria = QComboBox()
        cb_categoria.addItems([e.value for e in TipoEntrata])

        cb_cliente_tipo = QComboBox()
        cb_cliente_tipo.addItems(["Azienda", "Privato"])

        input_data = QDateEdit()
        input_data.setCalendarPopup(True)
        input_data.setDate(QDate.currentDate())

        input_importo = QLineEdit("0.0")
        input_quantita = QLineEdit("1.0")

        # Dettagli Cliente
        input_c_nome = QLineEdit()
        input_c_nome.setPlaceholderText("Ragione Sociale o Nome/Cognome")
        input_c_piva_cf = QLineEdit()
        input_c_piva_cf.setPlaceholderText("Partita IVA o Codice Fiscale")
        input_c_email = QLineEdit()
        input_c_tel = QLineEdit()

        # Descrizione movimento (RNF8: <= 500 caratteri)
        input_desc = QTextEdit()
        input_desc.setMaximumHeight(80)

        # File PDF
        self.selected_pdf_entrata = ""
        btn_attach_pdf = QPushButton("Allegata Documento PDF (RF19)")
        lbl_pdf_name = QLabel("Nessun allegato")

        def attach_action():
            path, _ = QFileDialog.getOpenFileName(dlg, "Seleziona Documento PDF", "", "File PDF (*.pdf);;Tutti i file (*.*)")
            if path:
                self.selected_pdf_entrata = path
                lbl_pdf_name.setText(os.path.basename(path))

        btn_attach_pdf.clicked.connect(attach_action)

        form.addRow("Categoria Prodotto (RF9):", cb_categoria)
        form.addRow("Tipo Cliente (RF10):", cb_cliente_tipo)
        form.addRow("Data Vendita (RNF7):", input_data)
        form.addRow("Importo Totale (€):", input_importo)
        form.addRow("Quantità Venduta:", input_quantita)
        form.addRow("Nome Cliente / Ragione Soc.:", input_c_nome)
        form.addRow("P.IVA / Codice Fiscale:", input_c_piva_cf)
        form.addRow("Email / Telefono:", input_c_email)
        form.addRow("Descrizione (max 500 char - RNF8):", input_desc)
        form.addRow(btn_attach_pdf, lbl_pdf_name)

        layout.addLayout(form)

        btn_save = QPushButton("Conferma Registrazione Entrata")
        def save_action():
            try:
                cat = cb_categoria.currentText()
                c_tipo = cb_cliente_tipo.currentText()
                dt = input_data.date().toString("yyyy-MM-dd")
                importo = float(input_importo.text().strip() or "0")
                qta = float(input_quantita.text().strip() or "0")
                desc = input_desc.toPlainText().strip()

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
        dlg.setWindowTitle("Registrazione Nuova Uscita / Spesa (RF11-RF18)")
        dlg.setFixedSize(500, 480)
        layout = QVBoxLayout(dlg)

        form = QFormLayout()

        cb_categoria = QComboBox()
        cb_categoria.addItems([e.value for e in TipoUscita])

        input_data = QDateEdit()
        input_data.setCalendarPopup(True)
        input_data.setDate(QDate.currentDate())

        input_importo = QLineEdit("0.0")
        input_quantita = QLineEdit("1.0")
        input_fornitore = QLineEdit()
        input_fornitore.setPlaceholderText("Fornitore / Ente Emettitore / Note Spesa")

        # Descrizione movimento (RNF8: <= 500 caratteri)
        input_desc = QTextEdit()
        input_desc.setMaximumHeight(80)

        # File PDF
        self.selected_pdf_uscita = ""
        btn_attach_pdf = QPushButton("Allegata Documento / Ricevuta PDF (RF19)")
        lbl_pdf_name = QLabel("Nessun allegato")

        def attach_action():
            path, _ = QFileDialog.getOpenFileName(dlg, "Seleziona Ricevuta PDF", "", "File PDF (*.pdf);;Tutti i file (*.*)")
            if path:
                self.selected_pdf_uscita = path
                lbl_pdf_name.setText(os.path.basename(path))

        btn_attach_pdf.clicked.connect(attach_action)

        form.addRow("Categoria Spesa (RF11-18):", cb_categoria)
        form.addRow("Data Pagamento (RNF7):", input_data)
        form.addRow("Importo Totale (€):", input_importo)
        form.addRow("Quantità / Unità:", input_quantita)
        form.addRow("Fornitore / Ente:", input_fornitore)
        form.addRow("Descrizione (max 500 char - RNF8):", input_desc)
        form.addRow(btn_attach_pdf, lbl_pdf_name)

        layout.addLayout(form)

        btn_save = QPushButton("Conferma Registrazione Uscita")
        btn_save.setStyleSheet("background-color: #d84315;")
        def save_action():
            try:
                cat = cb_categoria.currentText()
                dt = input_data.date().toString("yyyy-MM-dd")
                importo = float(input_importo.text().strip() or "0")
                qta = float(input_quantita.text().strip() or "0")
                forn = input_fornitore.text().strip()
                desc = input_desc.toPlainText().strip()

                if len(desc) > 500:
                    QMessageBox.warning(dlg, "Attenzione", "La descrizione supera il limite di 500 caratteri.")
                    return

                self.financial_service.registra_uscita(
                    categoria_uscita=cat,
                    importo=importo,
                    quantita=qta,
                    data=dt,
                    descrizione=desc,
                    fornitore_note=forn,
                    pdf_path=self.selected_pdf_uscita or None,
                    username=self.current_user.nomeUtente
                )

                QMessageBox.information(dlg, "Successo", "Uscita registrata con successo!")
                self.load_tables()
                dlg.accept()
            except Exception as e:
                QMessageBox.critical(dlg, "Errore", str(e))

        btn_save.clicked.connect(save_action)
        layout.addWidget(btn_save)
        dlg.exec()

    def handle_view_pdf(self, tipo: TipoMovimento):
        table = self.table_entrate if tipo == TipoMovimento.ENTRATA else self.table_uscite
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Attenzione", "Selezionare una riga dalla tabella per visualizzare il relativo allegato PDF.")
            return

        pdf_item = table.item(row, 7)
        pdf_path = pdf_item.data(Qt.ItemDataRole.UserRole)

        if not pdf_path or not os.path.exists(pdf_path):
            QMessageBox.information(self, "Informazione Documento", "Nessun documento PDF allegato a questo movimento finanziario.")
            return

        # Apri il documento con l'applicazione di sistema o mostra anteprima
        try:
            os.startfile(pdf_path)
        except Exception as e:
            QMessageBox.information(self, "Visualizzatore PDF", f"Allegato presente presso:\n{pdf_path}")
