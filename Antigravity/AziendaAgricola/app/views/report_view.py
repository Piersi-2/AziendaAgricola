from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QMessageBox, QGroupBox, QComboBox, QTextEdit
)
from PyQt6.QtCore import Qt, QDate
from app.services import ReportService
from app.models import ReportGuadagno

class ReportView(QWidget):
    def __init__(self, report_service: ReportService, repo=None, parent=None):
        super().__init__(parent)
        self.report_service = report_service
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # ---------------------------------------------------------
        # GUADAGNO AZIENDALE
        # ---------------------------------------------------------
        report_group = QGroupBox("Guadagno Aziendale Annuo")
        r_layout = QVBoxLayout(report_group)

        top_r = QHBoxLayout()
        top_r.addWidget(QLabel("Seleziona Anno di Riferimento:"))

        self.cb_anno = QComboBox()
        self.cb_anno.setMinimumWidth(90)
        curr_year = QDate.currentDate().year()
        for y in range(curr_year, curr_year - 20, -1):
            self.cb_anno.addItem(str(y))

        self.cb_anno.currentTextChanged.connect(lambda: self.handle_calculate_report())

        top_r.addWidget(self.cb_anno)
        top_r.addStretch()

        r_layout.addLayout(top_r)

        self.report_display = QTextEdit()
        self.report_display.setReadOnly(True)
        self.report_display.setMinimumHeight(300)
        r_layout.addWidget(self.report_display)

        main_layout.addWidget(report_group)
        main_layout.addStretch()

        # Inizializza con il calcolo dell'anno corrente
        self.handle_calculate_report()

    def handle_calculate_report(self):
        try:
            anno = int(self.cb_anno.currentText())
            rep = self.report_service.calcola_guadagno_aziendale(anno)

            res_text = f"""==================================================
  REPORT GUADAGNO AZIENDALE ANNO {anno}
==================================================
  - Totale Entrate:   € {rep.totaleEntrate:,.2f}
  - Totale Uscite:    € {rep.totaleUscite:,.2f}
--------------------------------------------------
  = GUADAGNO NETTO:   € {rep.margineNetto:,.2f}
==================================================="""

            if rep.margineNetto >= 0:
                res_text += "\n  ESITO: Bilancio in Utile (+) "
            else:
                res_text += "\n  ESITO: Bilancio in Disavanzo / Perdita (-) "
            res_text += "\n=================================================="
            self.report_display.setPlainText(res_text)
        except Exception as e:
            QMessageBox.critical(self, "Errore", str(e))

# Alias per retrocompatibilita
ReportAndBackupView = ReportView
