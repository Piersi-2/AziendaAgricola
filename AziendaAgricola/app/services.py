import uuid
import os
import shutil
import datetime
import re
from typing import List, Optional, Dict, Tuple, Any
from app.models import (
    Utente, Manager, Dipendente, livelloAccesso,
    Prodotto,
    Contatto, Azienda, Privato,
    Documento, Movimento, TipoMovimento, TipoUscita,
    ReportGuadagno, Sessione, CategoriaProdotto
)
from app.repositories import DataRepository

# ---------------------------------------------------------
# AUTHSERVICE - gestisce autenticazione, autorizzazione, sessioni e log accessi
# ---------------------------------------------------------

class AuthService:
    def __init__(self, repo: DataRepository, session_timeout_minutes: int = 10):
        self.repo = repo
        self.session_timeout_minutes = session_timeout_minutes
        self.current_session: Optional[Sessione] = None
        self._last_activity_dt: Optional[datetime.datetime] = None

    def effettuaLogin(self, username: str, password: str) -> Utente:
        users = self.repo.caricaUtenti()
        user = next((u for u in users if u.nomeUtente.lower() == username.lower()), None)     

        if not user:
            raise ValueError("Nome utente non trovato o account disattivato.")

        if user.password != password:
            raise ValueError("Password errata.")

        # Aggiorna ultimo login
        now_dt = datetime.datetime.now()
        now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
        user.ultimoLogin = now_str
        self.repo.salvaUtenti(users)
        self.repo.cronologiaLogin(user.nomeUtente)

        # Attiva sessione
        self._last_activity_dt = now_dt
        self.current_session = Sessione(
            utente=user,
            timestampLogin=now_str,
            sessioneAttiva=True,
            ultimaAttivita=now_str
        )
        return user

    def effettuaLogout(self) -> bool:
        self._last_activity_dt = None
        if self.current_session:
            self.current_session.sessioneAttiva = False
            self.current_session = None
            return True
        return False

    def update_activity(self):
        #   Aggiorna il timestamp dell'ultima attività. Chiamato da eventFilter()
        if self.current_session and self.current_session.sessioneAttiva:    # Controlla che la sessione esiste e sia ancora attiva
            now = datetime.datetime.now()
            if self._last_activity_dt is None or (now - self._last_activity_dt).total_seconds() >= 5:   # Prima condizione si ha se non esiste ancora un orario dell'ultima attività
                self._last_activity_dt = now
                self.current_session.ultimaAttivita = now.strftime("%Y-%m-%d %H:%M:%S")

    def is_session_valid(self) -> bool:
        if not self.current_session or not self.current_session.sessioneAttiva:
            return False
        try:
            ref_str = self.current_session.ultimaAttivita or self.current_session.timestampLogin
            last_dt = datetime.datetime.strptime(ref_str, "%Y-%m-%d %H:%M:%S")
            elapsed = datetime.datetime.now() - last_dt
            if elapsed.total_seconds() > self.session_timeout_minutes * 60:
                self.effettuaLogout()
                return False
        except Exception:
            pass
        return True

    def get_login_history(self, username: Optional[str] = None) -> Dict[str, List[str]]:
        history = self.repo.caricaCronologiaLogin()
        if username:
            return {username: history.get(username, [])}
        return history

# ---------------------------------------------------------
# GESTIONE UTENTE - gestisce utenti e manager
# ---------------------------------------------------------

class GestioneUtente:
    def __init__(self, repo: DataRepository):
        self.repo = repo

    # Verifica se esiste almeno un Manager registrato
    def presenzaManager(self) -> bool:
        users = self.repo.caricaUtenti()
        return any(isinstance(u, Manager) or u.ruolo == livelloAccesso.MANAGER for u in users)

    def crea_manager(self, username: str, password: str, nome: str, cognome: str, email: str, telefono: str, dataNascita: str, codiceAutorizzazione: str = "MNG-ADMIN") -> Manager:
        if self.presenzaManager():
            raise ValueError("Esiste già un profilo Manager nel sistema. Non è possibile crearne più di uno.")
        self._valida_nuovo_utente(username, email, password, dataNascita)
        users = self.repo.caricaUtenti()
        m = Manager(
            id=str(uuid.uuid4())[:8],
            nomeUtente=username,
            password=password,
            nome=nome,
            cognome=cognome,
            email=email,
            telefono=telefono,
            dataNascita=dataNascita,
            ruolo=livelloAccesso.MANAGER,
            codiceAutorizzazione=codiceAutorizzazione
        )
        users.append(m)
        self.repo.salvaUtenti(users)
        return m

    def crea_dipendente(self, username: str, password: str, nome: str, cognome: str, email: str, telefono: str, dataNascita: str, dataAssunzione: str = "", mansione: str = "", stipendio: float = 0.0) -> Dipendente:
        self._valida_nuovo_utente(username, email, password, dataNascita)
        users = self.repo.caricaUtenti()
        d = Dipendente(
            id=str(uuid.uuid4())[:8],
            nomeUtente=username,
            password=password,
            nome=nome,
            cognome=cognome,
            email=email,
            telefono=telefono,
            dataNascita=dataNascita,
            ruolo=livelloAccesso.DIPENDENTE,
        )
        users.append(d)
        self.repo.salvaUtenti(users)
        return d

    def modifica_profilo(self, user_id: str, nome: str, cognome: str, email: str, telefono: str, dataNascita: str, password: Optional[str] = None):
        if not dataNascita or not str(dataNascita).strip():
            raise ValueError("La data di nascita è obbligatoria.")

        users = self.repo.caricaUtenti()
        u = next((x for x in users if x.id == user_id), None)
        if not u:
            raise ValueError(f"Utente con ID '{user_id}' non trovato.")

        for other in users:
            if other.id != user_id and other.email.lower() == email.lower():
                raise ValueError(f"L'email '{email}' è già utilizzata da un altro utente.")

        u.modificaProfiloUtente(
            nome=nome,
            cognome=cognome,
            email=email,
            telefono=telefono,
            dataNascita=dataNascita,
            password=password
        )
        self.repo.salvaUtenti(users)

    def elimina_dipendente(self, user_id: str):
        users = self.repo.caricaUtenti()
        target = next((x for x in users if x.id == user_id), None)
        if not target:
            raise ValueError("Profilo utente non trovato.")

        if isinstance(target, Manager):
            raise ValueError("Non è possibile eliminare un profilo Manager da questa procedura.")

        users = [x for x in users if x.id != user_id]
        self.repo.salvaUtenti(users)

    def get_all_users(self) -> List[Utente]:
        return self.repo.caricaUtenti()

    def _valida_nuovo_utente(self, username: str, email: str, password: str, dataNascita: str = ""):
        if not dataNascita or not str(dataNascita).strip():
            raise ValueError("La data di nascita è obbligatoria.")

        if not password or len(password) < 8 or not password.isalnum():
            raise ValueError("La password deve contenere almeno 8 caratteri alfanumerici.")

        users = self.repo.caricaUtenti()
        if any(u.nomeUtente.lower() == username.lower() for u in users):
            raise ValueError(f"Il nome utente '{username}' è già occupato.")

        if any(u.email.lower() == email.lower() for u in users):
            raise ValueError(f"L'indirizzo email '{email}' è già associato a un account.")

# ---------------------------------------------------------
# GESTIONE PRODOTTO - gestisce catalogo prodotti agricoli e categorie
# ---------------------------------------------------------

class GestioneProdotto:
    def __init__(self, repo: DataRepository):
        self.repo = repo

    def aggiungi_prodotto(self, nome: str, descrizione: str, prezzo: float, unita: str, tipo: str) -> Prodotto:
        prods = self.repo.caricaProdotti()
        if any(p.nome.lower() == nome.lower() for p in prods):
            raise ValueError(f"Un prodotto con nome '{nome}' esiste già a catalogo.")

        categories = self.repo.caricaCategorie()
        if not categories:
            raise ValueError("Impossibile aggiungere un prodotto se prima non è stata inserita una categoria.")

        cat_match = next((c for c in categories if c.nome.strip().upper() == tipo.strip().upper()), None)
        if not cat_match:
            raise ValueError(f"La categoria '{tipo}' non esiste. Aggiungerla prima di procedere.")

        effettiva_unita = cat_match.unitaMisura

        p = Prodotto(
            idProdotto=str(uuid.uuid4())[:8],
            nome=nome,
            descrizione=descrizione,
            prezzoUnitario=prezzo,
            categoria=tipo,
            unitaMisura=effettiva_unita
        )
        prods.append(p)
        self.repo.salvaProdotti(prods)
        return p

    def modifica_prodotto(self, prodotto_id: str, nome: str, descrizione: str, prezzo: float):
        prods = self.repo.caricaProdotti()
        p = next((x for x in prods if x.idProdotto == prodotto_id), None)
        if not p:
            raise ValueError(f"Prodotto ID '{prodotto_id}' non trovato.")

        for other in prods:
            if other.idProdotto != prodotto_id and other.nome.lower() == nome.lower():
                raise ValueError(f"Un prodotto con nome '{nome}' è già registrato.")

        p.nome = nome
        p.descrizione = descrizione
        p.aggiornaPrezzoListino(prezzo)
        self.repo.salvaProdotti(prods)

    def elimina_prodotto(self, prodotto_id: str):
        prods = self.repo.caricaProdotti()
        prods = [p for p in prods if p.idProdotto != prodotto_id]
        self.repo.salvaProdotti(prods)

    def get_all_products(self) -> List[Prodotto]:
        return self.repo.caricaProdotti()

    def aggiungi_categoria(self, nome: str, unita: str) -> CategoriaProdotto:
        nome_clean = nome.strip().upper()
        if not nome_clean:
            raise ValueError("Il nome della categoria non può essere vuoto.")

        unita_valide = ["kg", "g", "l", "kilogrammi", "grammi", "litri"]
        if unita not in unita_valide:
            raise ValueError(f"Unità di misura non valida. Scegliere tra: {', '.join(unita_valide)}.")

        categories = self.repo.caricaCategorie()
        if any(c.nome == nome_clean for c in categories):
            raise ValueError(f"La categoria '{nome_clean}' esiste già.")

        cat = CategoriaProdotto(nome=nome_clean, unitaMisura=unita)
        categories.append(cat)
        self.repo.salvaCategorie(categories)
        return cat

    def get_all_categories(self) -> List[CategoriaProdotto]:
        return self.repo.caricaCategorie()

    def elimina_categoria(self, nome_categoria: str):
        nome_clean = nome_categoria.strip().upper()
        
        categories = self.repo.caricaCategorie()
        categories = [c for c in categories if c.nome != nome_clean]
        self.repo.salvaCategorie(categories)

        # Rimuove tutti i prodotti associati a questa categoria
        prods = self.repo.caricaProdotti()
        prods = [p for p in prods if p.categoria.strip().upper() != nome_clean]
        self.repo.salvaProdotti(prods)

# ---------------------------------------------------------
# GESTIONE MOVIMENTO - gestisce transazioni e registri finanziari
# ---------------------------------------------------------

class GestioneMovimento:
    def __init__(self, repo: DataRepository):
        self.repo = repo

    def salva_allegato_pdf(self, source_path: str) -> str:
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Il file '{source_path}' non esiste.")

        dest_name = f"doc_{str(uuid.uuid4())[:8]}_{os.path.basename(source_path)}"
        dest_path = os.path.join(self.repo.uploads_dir, dest_name)
        shutil.copy2(source_path, dest_path)    # Copia il file nel dest_path mantenendo i metadati
        return dest_path

    def registra_entrata(self, categoria_prodotto: str, prodotto_id: str, cliente_tipo: str, importo: float, data: str, descrizione: str, cliente_dettagli: Optional[Dict[str, str]] = None, pdf_path: Optional[str] = None, quantita: float = 1.0) -> Movimento:
        mov_id = f"MOV-ENT-{str(uuid.uuid4())[:8]}"

        doc = None
        if pdf_path:
            saved_pdf = self.salva_allegato_pdf(pdf_path)
            doc = Documento(
                numeroDocumento=f"DOC-ENT-{str(uuid.uuid4())[:6]}",
                allegatoPDF=saved_pdf
            )

        contatto_id = None
        contatto_desc = cliente_tipo
        if cliente_dettagli:
            contacts = self.repo.caricaContatti()
            c_id = str(uuid.uuid4())[:8]
            if cliente_tipo == "Azienda":
                c = Azienda(
                    idContatto=c_id,
                    email=cliente_dettagli.get("email", ""),
                    ragioneSociale=cliente_dettagli.get("ragioneSociale", ""),
                    partitaIVA=cliente_dettagli.get("partitaIVA", "")
                )
            else:
                c = Privato(
                    idContatto=c_id,
                    email=cliente_dettagli.get("email", ""),
                    Nome=cliente_dettagli.get("Nome", ""),
                    codiceFiscale=cliente_dettagli.get("codiceFiscale", "")
                )
            contacts.append(c)
            self.repo.salvaContatti(contacts)
            contatto_id = c_id
            contatto_desc = c.getDatiFatturazione()

        prods = self.repo.caricaProdotti()
        prod = next((x for x in prods if x.idProdotto == prodotto_id), None)
        prod_nome = prod.nome if prod else None

        m = Movimento(
            idMovimento=mov_id,
            tipo=TipoMovimento.ENTRATA,
            quantita=quantita,
            prezzoTotale=importo,
            dataMovimento=data or datetime.date.today().isoformat(),
            descrizione=descrizione,
            sottoTipoEntrata=categoria_prodotto,
            prodottoId=prodotto_id,
            prodottoNome=prod_nome,
            contattoId=contatto_id,
            contattoDescrizione=contatto_desc,
            documento=doc,
        )

        movs = self.repo.caricaMovimenti()
        movs.append(m)
        self.repo.salvaMovimenti(movs)
        return m

    def registra_uscita(self, categoria_uscita: str, prodotto_id: Optional[str], importo: float, data: str, descrizione: str, fornitore_note: str = "", pdf_path: Optional[str] = None) -> Movimento:
        mov_id = f"MOV-USC-{str(uuid.uuid4())[:8]}"

        doc = None
        if pdf_path:
            saved_pdf = self.salva_allegato_pdf(pdf_path)
            doc = Documento(
                numeroDocumento=f"DOC-USC-{str(uuid.uuid4())[:6]}",
                allegatoPDF=saved_pdf
            )

        prods = self.repo.caricaProdotti()
        prod = next((x for x in prods if x.idProdotto == prodotto_id), None)
        prod_nome = prod.nome if prod else None

        m = Movimento(
            idMovimento=mov_id,
            tipo=TipoMovimento.USCITA,
            quantita=1.0,
            prezzoTotale=importo,
            dataMovimento=data or datetime.date.today().isoformat(),
            descrizione=descrizione,
            sottoTipoUscita=categoria_uscita,
            prodottoId=prodotto_id,
            prodottoNome=prod_nome,
            contattoDescrizione=fornitore_note,
            documento=doc,
        )

        movs = self.repo.caricaMovimenti()
        movs.append(m)
        self.repo.salvaMovimenti(movs)
        return m

    def get_all_movements(self) -> List[Movimento]:
        return self.repo.caricaMovimenti()

    def get_uscite(self) -> List[Movimento]:
        return [m for m in self.repo.caricaMovimenti() if m.tipo == TipoMovimento.USCITA]

    def elimina_movimento(self, movimento_id: str):
        movs = self.repo.caricaMovimenti()
        movs = [m for m in movs if m.idMovimento != movimento_id]
        self.repo.salvaMovimenti(movs)

# ---------------------------------------------------------
# GESTIONE REPORT - calcolo del guadagno aziendale
# ---------------------------------------------------------

class GestioneReport:
    def __init__(self, repo: DataRepository):
        self.repo = repo

    def calcola_guadagno_aziendale(self, anno: int) -> ReportGuadagno:
        movs = self.repo.caricaMovimenti()
        return ReportGuadagno.genera(anno, movs)
