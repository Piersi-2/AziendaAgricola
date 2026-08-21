import uuid
import os
import shutil
import datetime
from typing import List, Optional, Dict, Tuple
from app.models import (
    Utente, Manager, Dipendente, livelloAccesso,
    Prodotto, ProdottoAgricolo, MaterialeConsumo, ServizioEsterno,
    Contatto, Azienda, Privato,
    Documento, Movimento, TipoMovimento, TipoUscita,
    ReportGuadagno, Sessione, CategoriaProdotto
)
from app.repositories import DataRepository

class AuthService:
    def __init__(self, repo: DataRepository, session_timeout_minutes: int = 30):
        self.repo = repo
        self.session_timeout_minutes = session_timeout_minutes
        self.current_session: Optional[Sessione] = None

    def effettuaLogin(self, username: str, password: str) -> Utente:
        users = self.repo.load_users()
        user = next((u for u in users if u.nomeUtente.lower() == username.lower() and u.statoAttivo), None)

        if not user:
            raise ValueError("Nome utente non trovato o account disattivato.")

        if user.password != password:
            raise ValueError("Password errata.")

        # Aggiorna ultimo login
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user.ultimoLogin = now_str
        self.repo.save_users(users)
        self.repo.record_login(user.nomeUtente)

        # Attiva sessione
        self.current_session = Sessione(utente=user, timestampLogin=now_str, sessioneAttiva=True)
        return user

    def effettuaLogout(self) -> bool:
        if self.current_session:
            self.current_session.sessioneAttiva = False
            self.current_session = None
            return True
        return False

    def is_session_valid(self) -> bool:
        if not self.current_session or not self.current_session.sessioneAttiva:
            return False
        try:
            login_dt = datetime.datetime.strptime(self.current_session.timestampLogin, "%Y-%m-%d %H:%M:%S")
            elapsed = datetime.datetime.now() - login_dt
            if elapsed.total_seconds() > self.session_timeout_minutes * 60:
                self.effettuaLogout()
                return False
        except Exception:
            pass
        return True

    def get_login_history(self, username: Optional[str] = None) -> Dict[str, List[str]]:
        history = self.repo.load_login_history()
        if username:
            return {username: history.get(username, [])}
        return history

    def recupera_password_email(self, email: str) -> Tuple[bool, str]:
        """RNF6: Gestione recupero password tramite email."""
        users = self.repo.load_users()
        user = next((u for u in users if u.email.lower() == email.lower()), None)
        if not user:
            return False, "Nessun utente trovato con l'indirizzo email specificato."
        
        # In una vera applicazione invierebbe un'email; qui restituisce le istruzioni/password mock
        return True, f"Istruzioni di recupero inviate all'indirizzo {email}. (Password utente: {user.password})"


class UserManager:
    def __init__(self, repo: DataRepository):
        self.repo = repo

    def count_users(self) -> int:
        return len(self.repo.load_users())

    def ha_manager(self) -> bool:
        users = self.repo.load_users()
        return any(isinstance(u, Manager) for u in users)

    def registra_primo_manager(self, username: str, password: str, nome: str, cognome: str, email: str, telefono: str, dataNascita: str) -> Manager:
        """RF1, RF27: Registrazione iniziale profilo Manager se non ne esistono altri."""
        users = self.repo.load_users()
        if any(isinstance(u, Manager) for u in users):
            raise ValueError("Un Manager è già registrato nel sistema.")

        return self.crea_manager(username, password, nome, cognome, email, telefono, dataNascita)

    def crea_manager(self, username: str, password: str, nome: str, cognome: str, email: str, telefono: str, dataNascita: str, codiceAutorizzazione: str = "MNG-ADMIN") -> Manager:
        """RF1, RF2: Creazione profilo Manager (da parte di un altro Manager)."""
        self._valida_nuovo_utente(username, email, password)
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
        users = self.repo.load_users()
        users.append(m)
        self.repo.save_users(users)
        return m

    def crea_dipendente(self, username: str, password: str, nome: str, cognome: str, email: str, telefono: str, dataNascita: str, dataAssunzione: str, mansione: str, stipendio: float) -> Dipendente:
        """RF2: Creazione profilo Dipendente da parte del Manager."""
        self._valida_nuovo_utente(username, email, password)
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
            dataAssunzione=dataAssunzione or datetime.date.today().isoformat(),
            mansione=mansione,
            stipendioMensile=stipendio
        )
        users = self.repo.load_users()
        users.append(d)
        self.repo.save_users(users)
        return d

    def modifica_profilo(self, user_id: str, nome: str, cognome: str, email: str, telefono: str, dataNascita: str, password: Optional[str] = None):
        """RF4: Modifica profilo utente e manager."""
        users = self.repo.load_users()
        u = next((x for x in users if x.id == user_id), None)
        if not u:
            raise ValueError("Utente non trovato.")

        # RNF4: Unicità email se cambiata
        if email.lower() != u.email.lower():
            if any(x.email.lower() == email.lower() and x.id != user_id for x in users):
                raise ValueError(f"L'email '{email}' è già utilizzata da un altro utente.")

        u.modificaProfiloUtente(nome, cognome, email, telefono, dataNascita, password)
        self.repo.save_users(users)

    def elimina_dipendente(self, dipendente_id: str):
        """RF5: Elimina profilo dipendente da parte del manager."""
        users = self.repo.load_users()
        target = next((x for x in users if x.id == dipendente_id), None)
        if not target:
            raise ValueError("Profilo dipendente non trovato.")

        if isinstance(target, Manager):
            raise ValueError("Non è possibile eliminare un profilo Manager da questa funzione.")

        users = [x for x in users if x.id != dipendente_id]
        self.repo.save_users(users)

    def _valida_nuovo_utente(self, username: str, email: str, password: str):
        users = self.repo.load_users()

        if any(x.nomeUtente.lower() == username.lower() for x in users):
            raise ValueError(f"Il nome utente '{username}' è già in uso.")

        # RNF4: Unicità email
        if any(x.email.lower() == email.lower() for x in users):
            raise ValueError(f"L'email '{email}' è già associata ad un altro profilo.")

        # RNF3: Validazione password >= 8 alfanumerici
        if not Utente.valida_password(password):
            raise ValueError("La password deve contenere almeno 8 caratteri alfanumerici.")

    def get_all_users(self) -> List[Utente]:
        return self.repo.load_users()


class ProductService:
    def __init__(self, repo: DataRepository):
        self.repo = repo

    def aggiungi_prodotto_agricolo(self, nome: str, descrizione: str, prezzo: float, unita: str, tipo: str, quantita: float = 0.0) -> ProdottoAgricolo:
        """RF6, RNF5: Aggiungi nuovo prodotto agricolo con controllo di unicità."""
        self._valida_unicita_prodotto(nome)
        p = ProdottoAgricolo(
            idProdotto=str(uuid.uuid4())[:8],
            nome=nome.strip(),
            descrizione=descrizione.strip(),
            prezzoUnitario=prezzo,
            quantitaDisponibile=quantita,
            tipoProdotto=tipo.strip(),
            unitaMisura=unita.strip()
        )
        prods = self.repo.load_products()
        prods.append(p)
        self.repo.save_products(prods)
        return p

    def aggiungi_materiale(self, nome: str, descrizione: str, prezzo: float, tipo_materiale: str, quantita: float = 0.0) -> MaterialeConsumo:
        self._valida_unicita_prodotto(nome)
        p = MaterialeConsumo(
            idProdotto=str(uuid.uuid4())[:8],
            nome=nome.strip(),
            descrizione=descrizione.strip(),
            prezzoUnitario=prezzo,
            quantitaDisponibile=quantita,
            tipoMateriale=tipo_materiale.strip()
        )
        prods = self.repo.load_products()
        prods.append(p)
        self.repo.save_products(prods)
        return p

    def modifica_prodotto(self, prodotto_id: str, nome: str, descrizione: str, prezzo: float, quantita: float):
        """RF7: Modifica prodotto agricolo o materiale presente."""
        prods = self.repo.load_products()
        p = next((x for x in prods if x.idProdotto == prodotto_id), None)
        if not p:
            raise ValueError("Prodotto non trovato.")

        if nome.strip().lower() != p.nome.lower():
            if any(x.nome.lower() == nome.strip().lower() and x.idProdotto != prodotto_id for x in prods):
                raise ValueError(f"Esiste già un prodotto denominato '{nome}'.")

        p.nome = nome.strip()
        p.descrizione = descrizione.strip()
        p.aggiornaPrezzoListino(prezzo)
        p.quantitaDisponibile = quantita
        self.repo.save_products(prods)

    def elimina_prodotto(self, prodotto_id: str):
        """RF8: Elimina prodotto agricolo."""
        prods = self.repo.load_products()
        prods = [x for x in prods if x.idProdotto != prodotto_id]
        self.repo.save_products(prods)

    def _valida_unicita_prodotto(self, nome: str):
        """RNF5: Unicità prodotto."""
        prods = self.repo.load_products()
        if any(x.nome.lower() == nome.strip().lower() for x in prods):
            raise ValueError(f"Un prodotto con nome '{nome}' esiste già a catalogo.")

    def get_all_products(self) -> List[Prodotto]:
        return self.repo.load_products()

    def aggiungi_categoria(self, nome: str, unita: str) -> CategoriaProdotto:
        nome_clean = nome.strip().upper()
        if not nome_clean:
            raise ValueError("Il nome della categoria non puo essere vuoto.")
        if unita not in ["kilogrammi", "grammi", "litri"]:
            raise ValueError("L'unita di misura selezionata non e valida.")

        categories = self.repo.load_categories()
        if any(c.nome == nome_clean for c in categories):
            raise ValueError(f"La categoria '{nome_clean}' esiste gia.")

        cat = CategoriaProdotto(nome=nome_clean, unitaMisura=unita)
        categories.append(cat)
        self.repo.save_categories(categories)
        return cat

    def get_all_categories(self) -> List[CategoriaProdotto]:
        return self.repo.load_categories()

    def elimina_categoria(self, nome_categoria: str):
        nome_clean = nome_categoria.strip().upper()
        
        # 1. Load categories, filter out this category, save
        categories = self.repo.load_categories()
        categories = [c for c in categories if c.nome != nome_clean]
        self.repo.save_categories(categories)

        # 2. Load products, filter out products belonging to this category, save
        prods = self.repo.load_products()
        prods = [p for p in prods if getattr(p, 'tipoProdotto', getattr(p, 'tipoMateriale', getattr(p, 'fornitore', 'Generico'))).strip().upper() != nome_clean]
        self.repo.save_products(prods)



class FinancialService:
    def __init__(self, repo: DataRepository):
        self.repo = repo

    def salva_allegato_pdf(self, source_path: str) -> str:
        """RF19: Caricamento e salvataggio file PDF di supporto."""
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Il file '{source_path}' non esiste.")

        dest_name = f"doc_{str(uuid.uuid4())[:8]}_{os.path.basename(source_path)}"
        dest_path = os.path.join(self.repo.uploads_dir, dest_name)
        shutil.copy2(source_path, dest_path)
        return dest_path

    def registra_entrata(self, categoria_prodotto: str, prodotto_id: str, cliente_tipo: str, importo: float, data: str, descrizione: str, cliente_dettagli: Optional[Dict[str, str]] = None, pdf_path: Optional[str] = None, username: str = "admin", quantita: float = 1.0) -> Movimento:
        """RF9, RF10: Registrazione entrate catalogate per prodotto e cliente (Azienda o Privato)."""
        doc = None
        if pdf_path:
            saved_pdf = self.salva_allegato_pdf(pdf_path)
            doc = Documento(
                numeroDocumento=f"DOC-ENT-{str(uuid.uuid4())[:6]}",
                enteEmettitore=cliente_tipo,
                allegatoPDF=saved_pdf
            )

        # Gestione contatto cliente
        contatto_id = None
        contatto_desc = cliente_tipo
        if cliente_dettagli:
            contacts = self.repo.load_contacts()
            c_id = str(uuid.uuid4())[:8]
            if cliente_tipo == "Azienda":
                c = Azienda(
                    idContatto=c_id,
                    email=cliente_dettagli.get("email", ""),
                    telefono=cliente_dettagli.get("telefono", ""),
                    indirizzo=cliente_dettagli.get("indirizzo", ""),
                    ragioneSociale=cliente_dettagli.get("ragioneSociale", ""),
                    partitaIVA=cliente_dettagli.get("partitaIVA", ""),
                    codiceDestinatarioSDI=cliente_dettagli.get("codiceDestinatarioSDI", "")
                )
            else:
                c = Privato(
                    idContatto=c_id,
                    email=cliente_dettagli.get("email", ""),
                    telefono=cliente_dettagli.get("telefono", ""),
                    indirizzo=cliente_dettagli.get("indirizzo", ""),
                    Nome=cliente_dettagli.get("Nome", ""),
                    Cognome=cliente_dettagli.get("Cognome", ""),
                    codiceFiscale=cliente_dettagli.get("codiceFiscale", "")
                )
            contacts.append(c)
            self.repo.save_contacts(contacts)
            contatto_id = c_id
            contatto_desc = c.getDatiFatturazione()

        prods = self.repo.load_products()
        prod = next((x for x in prods if x.idProdotto == prodotto_id), None)
        prod_nome = prod.nome if prod else None

        m = Movimento(
            idMovimento=f"MOV-ENT-{str(uuid.uuid4())[:8]}",
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
            creatoreUsername=username
        )

        movs = self.repo.load_movements()
        movs.append(m)
        self.repo.save_movements(movs)
        return m

    def registra_uscita(self, categoria_uscita: str, prodotto_id: Optional[str], importo: float, data: str, descrizione: str, fornitore_note: str = "", pdf_path: Optional[str] = None, username: str = "admin") -> Movimento:
        """RF11-RF18: Registrazione uscite (Manutenzione, Produzione, Vendita, Tasse, Stipendi, Assicurazioni, Rifiuti, Straordinarie)."""
        doc = None
        if pdf_path:
            saved_pdf = self.salva_allegato_pdf(pdf_path)
            doc = Documento(
                numeroDocumento=f"DOC-USC-{str(uuid.uuid4())[:6]}",
                enteEmettitore=fornitore_note or "Fornitore",
                allegatoPDF=saved_pdf
            )

        prods = self.repo.load_products()
        prod = next((x for x in prods if x.idProdotto == prodotto_id), None)
        prod_nome = prod.nome if prod else None

        m = Movimento(
            idMovimento=f"MOV-USC-{str(uuid.uuid4())[:8]}",
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
            creatoreUsername=username
        )

        movs = self.repo.load_movements()
        movs.append(m)
        self.repo.save_movements(movs)
        return m

    def get_all_movements(self) -> List[Movimento]:
        return self.repo.load_movements()

    def get_entrate(self) -> List[Movimento]:
        return [m for m in self.repo.load_movements() if m.tipo == TipoMovimento.ENTRATA]

    def get_uscite(self) -> List[Movimento]:
        return [m for m in self.repo.load_movements() if m.tipo == TipoMovimento.USCITA]


class ReportService:
    def __init__(self, repo: DataRepository):
        self.repo = repo

    def calcola_guadagno_aziendale(self, anno: int) -> ReportGuadagno:
        """RF22: Guadagno aziendale annuo."""
        movs = self.repo.load_movements()
        return ReportGuadagno.genera(anno, movs)

    def genera_report_pdf(self, anno: int, file_path: str) -> str:
        """Generazione report PDF sintetica per l'anno specificato."""
        report = self.calcola_guadagno_aziendale(anno)
        movs = [m for m in self.repo.load_movements() if m.dataMovimento.startswith(str(anno))]

        # Creazione report testuale / PDF
        content = f"""==================================================
AZIENDA AGRICOLA - REPORT FINANZIARIO ANNO {anno}
==================================================
Totale Entrate:   € {report.totaleEntrate:,.2f}
Totale Uscite:    € {report.totaleUscite:,.2f}
--------------------------------------------------
MARGINE NETTO:    € {report.margineNetto:,.2f}
==================================================

DETTAGLIO MOVIMENTI ({len(movs)} registrari):
"""
        for m in movs:
            try:
                dt = datetime.datetime.strptime(m.dataMovimento, "%Y-%m-%d")
                date_str = dt.strftime("%d/%m/%Y")
            except Exception:
                date_str = m.dataMovimento
            content += f"- [{date_str}] {m.tipo.value} - {m.sottoTipoEntrata or m.sottoTipoUscita}: €{m.prezzoTotale:.2f} ({m.descrizione})\n"

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return file_path
