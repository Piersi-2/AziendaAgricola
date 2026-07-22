import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QGroupBox, QFormLayout, QComboBox, QTextEdit, QFileDialog
)
from PyQt6.QtCore import Qt, QDate
from app.services import ReportService
from app.repositories import DataRepository

class ReportAndBackupView(QWidget):
    def __init__(self, report_service: ReportService, repo: DataRepository, parent=None):
        super().__init__(parent)
        self.report_service = report_service
        self.repo = repo
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # ---------------------------------------------------------
        # SECTION 1: GUADAGNO AZIENDALE (RF22)
        # ---------------------------------------------------------
        report_group = QGroupBox("Guadagno Aziendale Annuo (RF22)")
        r_layout = QVBoxLayout(report_group)

        top_r = QHBoxLayout()
        top_r.addWidget(QLabel("Seleziona Anno di Riferimento:"))

        self.cb_anno = QComboBox()
        curr_year = QDate.currentDate().year()
        for y in range(curr_year, curr_year - 6, -1):
            self.cb_anno.addItem(str(y))

        btn_calc = QPushButton("Calcola Guadagno Aziendale")
        btn_calc.clicked.connect(self.handle_calculate_report)

        btn_export = QPushButton("Esporta Report Sintetico PDF / TXT")
        btn_export.clicked.connect(self.handle_export_report)

        top_r.addWidget(self.cb_anno)
        top_r.addWidget(btn_calc)
        top_r.addWidget(btn_export)
        top_r.addStretch()

        r_layout.addLayout(top_r)

        self.report_display = QTextEdit()
        self.report_display.setReadOnly(True)
        self.report_display.setMaximumHeight(220)
        r_layout.addWidget(self.report_display)

        main_layout.addWidget(report_group)

        # ---------------------------------------------------------
        # SECTION 2: GESTIONE BACKUP E RIPRISTINO (RF23 / GestoreBackup)
        # ---------------------------------------------------------
        backup_group = QGroupBox("Gestore Backup e Ripristino Dati (RF23)")
        b_layout = QVBoxLayout(backup_group)

        info_lbl = QLabel(
            "Il sistema effettua un salvataggio periodico di sicurezza. "
            "Da questa sezione è possibile eseguire un backup immediato o ripristinare i dati da una copia precedente."
        )
        info_lbl.setWordWrap(True)
        b_layout.addWidget(info_lbl)

        btn_box = QHBoxLayout()
        btn_backup = QPushButton("Esegui Backup Immediato")
        btn_backup.clicked.connect(self.handle_run_backup)

        btn_restore = QPushButton("Ripristina Dati da Backup")
        btn_restore.setStyleSheet("background-color: #616161;")
        btn_restore.clicked.connect(self.handle_restore_backup)

        btn_box.addWidget(btn_backup)
        btn_box.addWidget(btn_restore)
        btn_box.addStretch()

        b_layout.addLayout(btn_box)

        self.lbl_backup_status = QLabel("Stato Backup: Pronto")
        self.lbl_backup_status.setStyleSheet("color: #2e7d32; font-weight: bold;")
        b_layout.addWidget(self.lbl_backup_status)

        main_layout.addWidget(backup_group)
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
=================================================="""

            if rep.margineNetto >= 0:
                res_text += "\n  ESITO: Bilancio in Utile (+) "
            else:
                res_text += "\n  ESITO: Bilancio in Disavanzo / Perdita (-) "

            self.report_display.setPlainText(res_text)
        except Exception as e:
            QMessageBox.critical(self, "Errore", str(e))

    def handle_export_report(self):
        anno = int(self.cb_anno.currentText())
        save_path, _ = QFileDialog.getSaveFileName(
            self, f"Esporta Report {anno}", f"Report_Guadagno_{anno}.txt", "Documento di Testo (*.txt);;Tutti i file (*.*)"
        )
        if save_path:
            try:
                self.report_service.genera_report_pdf(anno, save_path)
                QMessageBox.information(self, "Esportazione", f"Report esportato con successo in:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Errore Esportazione", str(e))

    def handle_run_backup(self):
        try:
            target_path = self.repo.esegui_backup()
            self.lbl_backup_status.setText(f"Ultimo backup salvato con successo in: {target_path}")
            QMessageBox.information(self, "Backup Completato", f"Backup dei dati eseguito con successo!\nCartella: {target_path}")
        except Exception as e:
            QMessageBox.critical(self, "Errore Backup", str(e))

    def handle_restore_backup(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleziona la cartella di backup da ripristinare", self.repo.backup_dir)
        if folder:
            confirm = QMessageBox.question(
                self, "Conferma Ripristino",
                "Attenzione: Il ripristino sovrascriverà i dati attuali con quelli del backup selezionato. Continuare?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                try:
                    self.repo.ripristina_dati(folder)
                    QMessageBox.information(self, "Ripristino Completato", "I dati sono stati ripristinati con successo!")
                    self.handle_calculate_report()
                except Exception as e:
                    QMessageBox.critical(self, "Errore Ripristino", str(e))
