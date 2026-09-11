from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
import datetime

# =========================================================
# ENUMERAZIONI
# =========================================================

class livelloAccesso(str, Enum): # str fa sì che ogni valore di Enum sia anche una stringa
    MANAGER = "MANAGER"
    DIPENDENTE = "DIPENDENTE"

class TipoMovimento(str, Enum):
    ENTRATA = "ENTRATA"
    USCITA = "USCITA"

class TipoUscita(str, Enum):
    SPESE_DI_MANUTENZIONE = "SPESE DI MANUTENZIONE"
    SPESE_DI_PRODUZIONE = "SPESE DI PRODUZIONE"
    SPESE_DI_VENDITA = "SPESE DI VENDITA"
    STIPENDI = "STIPENDI"
    SPESE_STRAORDINARIE = "SPESE STRAORDINARIE"
    TASSE = "TASSE"
    ASSICURAZIONI = "ASSICURAZIONI"

# =========================================================
# UTENTI E AUTENTICAZIONE
# =========================================================

@dataclass
class Utente:
    id: str
    nomeUtente: str
    password: str
    nome: str
    cognome: str
    email: str
    telefono: str
    dataNascita: str
    ruolo: livelloAccesso
    ultimoLogin: Optional[str] = None
    statoAttivo: bool = True    # Per disattivare l'account senza cancellarlo

    @staticmethod
    def valida_password(password: str) -> bool:
        """La password deve contenere almeno 8 caratteri alfanumerici."""
        if not password or len(password) < 8:
            return False
        return password.isalnum()

    def modificaProfiloUtente(self, nome: str, cognome: str, email: str, telefono: str, dataNascita: str, password: Optional[str] = None):
        # Significa che se password è None, non viene modificata. Se è una stringa, viene validata e aggiornata.
        self.nome = nome
        self.cognome = cognome
        self.email = email
        self.telefono = telefono
        self.dataNascita = dataNascita
        if password:
            if not self.valida_password(password):
                raise ValueError("La nuova password deve contenere almeno 8 caratteri alfanumerici.")
            self.password = password

@dataclass
class Manager(Utente):
    codiceAutorizzazione: str = "MNG-AUTH-DEFAULT"

    def __post_init__(self):  # Metodo eseguuto subito dopo l'inizializzazione dell'oggetto
        self.ruolo = livelloAccesso.MANAGER

@dataclass
class Dipendente(Utente):
    dataAssunzione: str = ""
    mansione: str = ""
    stipendioMensile: float = 0.0  

    def __post_init__(self):
        self.ruolo = livelloAccesso.DIPENDENTE

# =========================================================
# PRODOTTI AGRICOLI
# =========================================================

@dataclass
class CategoriaProdotto:
    nome: str
    unitaMisura: str 

@dataclass
class Prodotto:
    idProdotto: str
    nome: str
    descrizione: str
    prezzoUnitario: float
    quantitaVendita: float = 0.0
    tipoProdotto: str = "Agricolo"
    unitaMisura: str = "kg"

    def aggiornaPrezzoListino(self, nuovoPrezzo: float):
        if nuovoPrezzo <= 0:
            raise ValueError("Il prezzo unitario non può essere negativo.")
        self.prezzoUnitario = nuovoPrezzo

    def calcolaPrezzoTotale(self, quantita: float) -> float:
        return self.prezzoUnitario * quantita

    # Sconto su acquisti multipli
    def calcolaPrezzoScontato(self, quantita: float, percentualeSconto: float) -> float: 
        totale = self.calcolaPrezzoTotale(quantita)
        return totale * (1.0 - (percentualeSconto / 100.0))

    def getDescrizioneFattura(self) -> str:
        return f"{self.nome} - {self.descrizione} (€{self.prezzoUnitario:.2f})"

    def getNomeConQuantita(self) -> str:
        if self.quantitaVendita and self.quantitaVendita > 0:
            q_str = f"{self.quantitaVendita:g}"
            u = formatta_unita(self.unitaMisura)
            u_suffix = u if u in ("kg", "g", "l") else (f" {u}" if u else "")
            return f"{self.nome} ({q_str}{u_suffix})"
        return self.nome

def formatta_unita(unita: str) -> str:
    u = (unita or "").strip().lower()
    if u in ("kilogrammi"):
        return "kg"
    if u in ("grammi"):
        return "g"
    if u in ("litri"):
        return "l"
    return unita.strip()

# =========================================================
# CONTATTI E CLIENTI/FORNITORI
# =========================================================

@dataclass
class Contatto:
    idContatto: str
    email: str
    telefono: str
    indirizzo: str

    def getDatiFatturazione(self) -> str:
        return f"ID: {self.idContatto}, Email: {self.email}, Tel: {self.telefono}, Indirizzo: {self.indirizzo}"

@dataclass
class Azienda(Contatto):
    ragioneSociale: str = ""
    partitaIVA: str = ""
    codiceDestinatarioSDI: str = ""

    def getDatiFatturazione(self) -> str:
        base = super().getDatiFatturazione()
        return f"Azienda: {self.ragioneSociale}, P.IVA: {self.partitaIVA}, SDI: {self.codiceDestinatarioSDI} | {base}"

@dataclass
class Privato(Contatto):
    Nome: str = ""
    Cognome: str = ""
    codiceFiscale: str = ""

    def getDatiFatturazione(self) -> str:
        base = super().getDatiFatturazione()
        return f"Privato: {self.Nome} {self.Cognome}, CF: {self.codiceFiscale} | {base}"

# =========================================================
# ALLEGATI E DOCUMENTI
# =========================================================

@dataclass
class Documento:
    numeroDocumento: str
    enteEmettitore: str
    allegatoPDF: str = "" 
    dataCaricamento: str = ""

    def __post_init__(self):
        if not self.dataCaricamento:
            self.dataCaricamento = datetime.date.today().isoformat()

# =========================================================
# MOVIMENTI FINANZIARI
# =========================================================

@dataclass
class Movimento:
    idMovimento: str
    tipo: TipoMovimento
    quantita: float
    prezzoTotale: float
    dataMovimento: str
    descrizione: str
    sottoTipoEntrata: Optional[str] = None
    sottoTipoUscita: Optional[str] = None
    prodottoId: Optional[str] = None
    prodottoNome: Optional[str] = None
    contattoId: Optional[str] = None
    contattoDescrizione: Optional[str] = None
    documento: Optional[Documento] = None
    creatoreUsername: str = "admin"

    def __post_init__(self):
        if len(self.descrizione) > 500:
            raise ValueError("La descrizione del movimento non può superare i 500 caratteri.")

# =========================================================
# REPORT GUADAGNO
# =========================================================

@dataclass
class ReportGuadagno:
    periodoRiferimento: int 
    totaleEntrate: float
    totaleUscite: float
    margineNetto: float

    @classmethod
    def genera(cls, anno: int, movimenti: List[Movimento]) -> 'ReportGuadagno':
        entrate = 0.0
        uscite = 0.0
        for m in movimenti:
            try:
                # Converte la string in datetime
                dt = datetime.datetime.strptime(m.dataMovimento, "%Y-%m-%d")
                m_anno = dt.year
            except Exception:
                # Se la data non può essere interpretata, considera il movimento come appartenente all’anno richiesto
                m_anno = anno

            if m_anno == anno:
                if m.tipo == TipoMovimento.ENTRATA:
                    entrate += m.prezzoTotale
                elif m.tipo == TipoMovimento.USCITA:
                    uscite += m.prezzoTotale

        margine = entrate - uscite
        return cls(periodoRiferimento=anno, totaleEntrate=entrate, totaleUscite=uscite, margineNetto=margine)

# =========================================================
# AUTENTICATORE E SESSIONE
# =========================================================

@dataclass
class Sessione:
    utente: Utente
    timestampLogin: str     # Orario quando utente effettua login
    sessioneAttiva: bool = True
    ultimaAttivita: Optional[str] = None
