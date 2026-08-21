import os
import json
import shutil
import datetime
from typing import List, Dict, Optional, Any
from app.models import (
    Utente, Manager, Dipendente, livelloAccesso,
    Prodotto, ProdottoAgricolo, MaterialeConsumo, ServizioEsterno,
    Contatto, Azienda, Privato,
    Documento, Movimento, TipoMovimento,
    GestoreBackupInfo, CategoriaProdotto
)

class DataRepository:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.products_file = os.path.join(self.data_dir, "products.json")
        self.movements_file = os.path.join(self.data_dir, "movements.json")
        self.contacts_file = os.path.join(self.data_dir, "contacts.json")
        self.login_history_file = os.path.join(self.data_dir, "login_history.json")
        self.categories_file = os.path.join(self.data_dir, "categories.json")
        self.backup_dir = os.path.join(self.data_dir, "backups")
        self.uploads_dir = os.path.join(self.data_dir, "uploads")

        self._ensure_directories()

    def _ensure_directories(self):
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.uploads_dir, exist_ok=True)

    # ---------------------------------------------------------
    # UTENTI
    # ---------------------------------------------------------
    def load_users(self) -> List[Utente]:
        if not os.path.exists(self.users_file):
            return []
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                raw_list = json.load(f)
            users = []
            for d in raw_list:
                ruolo = livelloAccesso(d.get("ruolo", d.get("ruolo", "DIPENDENTE")))
                if ruolo == livelloAccesso.MANAGER:
                    u = Manager(
                        id=d["id"],
                        nomeUtente=d["nomeUtente"],
                        password=d["password"],
                        nome=d["nome"],
                        cognome=d["cognome"],
                        email=d["email"],
                        telefono=d["telefono"],
                        dataNascita=d["dataNascita"],
                        ruolo=ruolo,
                        ultimoLogin=d.get("ultimoLogin"),
                        statoAttivo=d.get("statoAttivo", True),
                        codiceAutorizzazione=d.get("codiceAutorizzazione", "MNG-AUTH-DEFAULT")
                    )
                else:
                    u = Dipendente(
                        id=d["id"],
                        nomeUtente=d["nomeUtente"],
                        password=d["password"],
                        nome=d["nome"],
                        cognome=d["cognome"],
                        email=d["email"],
                        telefono=d["telefono"],
                        dataNascita=d["dataNascita"],
                        ruolo=ruolo,
                        ultimoLogin=d.get("ultimoLogin"),
                        statoAttivo=d.get("statoAttivo", True),
                        dataAssunzione=d.get("dataAssunzione", ""),
                        mansione=d.get("mansione", ""),
                        stipendioMensile=float(d.get("stipendioMensile", 0.0))
                    )
                users.append(u)
            return users
        except Exception as e:
            print(f"Errore caricamento utenti: {e}")
            return []

    def save_users(self, users: List[Utente]):
        raw_list = []
        for u in users:
            d = {
                "id": u.id,
                "nomeUtente": u.nomeUtente,
                "password": u.password,
                "nome": u.nome,
                "cognome": u.cognome,
                "email": u.email,
                "telefono": u.telefono,
                "dataNascita": u.dataNascita,
                "ruolo": u.ruolo.value,
                "ultimoLogin": u.ultimoLogin,
                "statoAttivo": u.statoAttivo
            }
            if isinstance(u, Manager):
                d["codiceAutorizzazione"] = u.codiceAutorizzazione
            elif isinstance(u, Dipendente):
                d["dataAssunzione"] = u.dataAssunzione
                d["mansione"] = u.mansione
                d["stipendioMensile"] = u.stipendioMensile
            raw_list.append(d)

        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(raw_list, f, indent=2, ensure_ascii=False)

    # ---------------------------------------------------------
    # HISTORIC LOGIN TRACKING (UML: Autenticatore/Manager requirement)
    # ---------------------------------------------------------
    def record_login(self, username: str):
        history = self.load_login_history()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if username not in history:
            history[username] = []
        history[username].append(now_str)

        with open(self.login_history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def load_login_history(self) -> Dict[str, List[str]]:
        if not os.path.exists(self.login_history_file):
            return {}
        try:
            with open(self.login_history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    # ---------------------------------------------------------
    # CATEGORIE PRODOTTO
    # ---------------------------------------------------------
    def load_categories(self) -> List[CategoriaProdotto]:
        if not os.path.exists(self.categories_file):
            return []
        try:
            with open(self.categories_file, 'r', encoding='utf-8') as f:
                raw_list = json.load(f)
            return [CategoriaProdotto(nome=d["nome"], unitaMisura=d["unitaMisura"]) for d in raw_list]
        except Exception as e:
            print(f"Errore caricamento categorie: {e}")
            return []

    def save_categories(self, categories: List[CategoriaProdotto]):
        raw_list = [{"nome": c.nome, "unitaMisura": c.unitaMisura} for c in categories]
        with open(self.categories_file, 'w', encoding='utf-8') as f:
            json.dump(raw_list, f, indent=2, ensure_ascii=False)

    # ---------------------------------------------------------
    # PRODOTTI
    # ---------------------------------------------------------
    def load_products(self) -> List[Prodotto]:
        if not os.path.exists(self.products_file):
            return []
        try:
            with open(self.products_file, 'r', encoding='utf-8') as f:
                raw_list = json.load(f)
            prods = []
            for d in raw_list:
                ptype = d.get("class_type", "ProdottoAgricolo")
                if ptype == "MaterialeConsumo":
                    p = MaterialeConsumo(
                        idProdotto=d["idProdotto"],
                        nome=d["nome"],
                        descrizione=d["descrizione"],
                        prezzoUnitario=float(d["prezzoUnitario"]),
                        quantitaDisponibile=float(d.get("quantitaDisponibile", 0.0)),
                        tipoMateriale=d.get("tipoMateriale", "Generico")
                    )
                elif ptype == "ServizioEsterno":
                    p = ServizioEsterno(
                        idProdotto=d["idProdotto"],
                        nome=d["nome"],
                        descrizione=d["descrizione"],
                        prezzoUnitario=float(d["prezzoUnitario"]),
                        quantitaDisponibile=float(d.get("quantitaDisponibile", 0.0)),
                        fornitore=d.get("fornitore", "Fornitore Esterno")
                    )
                else:
                    p = ProdottoAgricolo(
                        idProdotto=d["idProdotto"],
                        nome=d["nome"],
                        descrizione=d["descrizione"],
                        prezzoUnitario=float(d["prezzoUnitario"]),
                        quantitaDisponibile=float(d.get("quantitaDisponibile", 0.0)),
                        tipoProdotto=d.get("tipoProdotto", "Agricolo"),
                        unitaMisura=d.get("unitaMisura", "kg")
                    )
                prods.append(p)
            return prods
        except Exception as e:
            print(f"Errore caricamento prodotti: {e}")
            return []

    def save_products(self, products: List[Prodotto]):
        raw_list = []
        for p in products:
            d = {
                "idProdotto": p.idProdotto,
                "nome": p.nome,
                "descrizione": p.descrizione,
                "prezzoUnitario": p.prezzoUnitario,
                "quantitaDisponibile": p.quantitaDisponibile,
                "class_type": p.__class__.__name__
            }
            if isinstance(p, ProdottoAgricolo):
                d["tipoProdotto"] = p.tipoProdotto
                d["unitaMisura"] = p.unitaMisura
            elif isinstance(p, MaterialeConsumo):
                d["tipoMateriale"] = p.tipoMateriale
            elif isinstance(p, ServizioEsterno):
                d["fornitore"] = p.fornitore
            raw_list.append(d)

        with open(self.products_file, 'w', encoding='utf-8') as f:
            json.dump(raw_list, f, indent=2, ensure_ascii=False)

    # ---------------------------------------------------------
    # MOVIMENTI FINANZIARI
    # ---------------------------------------------------------
    def load_movements(self) -> List[Movimento]:
        if not os.path.exists(self.movements_file):
            return []
        try:
            with open(self.movements_file, 'r', encoding='utf-8') as f:
                raw_list = json.load(f)
            movs = []
            for d in raw_list:
                doc = None
                if d.get("documento"):
                    doc_dict = d["documento"]
                    doc = Documento(
                        numeroDocumento=doc_dict["numeroDocumento"],
                        enteEmettitore=doc_dict["enteEmettitore"],
                        allegatoPDF=doc_dict.get("allegatoPDF", ""),
                        dataCaricamento=doc_dict.get("dataCaricamento", "")
                    )

                m = Movimento(
                    idMovimento=d["idMovimento"],
                    tipo=TipoMovimento(d["tipo"]),
                    quantita=float(d["quantita"]),
                    prezzoTotale=float(d["prezzoTotale"]),
                    dataMovimento=d["dataMovimento"],
                    descrizione=d["descrizione"],
                    sottoTipoEntrata=d.get("sottoTipoEntrata"),
                    sottoTipoUscita=d.get("sottoTipoUscita"),
                    prodottoId=d.get("prodottoId"),
                    prodottoNome=d.get("prodottoNome"),
                    contattoId=d.get("contattoId"),
                    contattoDescrizione=d.get("contattoDescrizione"),
                    documento=doc,
                    creatoreUsername=d.get("creatoreUsername", "admin")
                )
                movs.append(m)
            return movs
        except Exception as e:
            print(f"Errore caricamento movimenti: {e}")
            return []

    def save_movements(self, movements: List[Movimento]):
        raw_list = []
        for m in movements:
            doc_dict = None
            if m.documento:
                doc_dict = {
                    "numeroDocumento": m.documento.numeroDocumento,
                    "enteEmettitore": m.documento.enteEmettitore,
                    "allegatoPDF": m.documento.allegatoPDF,
                    "dataCaricamento": m.documento.dataCaricamento
                }

            d = {
                "idMovimento": m.idMovimento,
                "tipo": m.tipo.value,
                "quantita": m.quantita,
                "prezzoTotale": m.prezzoTotale,
                "dataMovimento": m.dataMovimento,
                "descrizione": m.descrizione,
                "sottoTipoEntrata": m.sottoTipoEntrata,
                "sottoTipoUscita": m.sottoTipoUscita,
                "prodottoId": m.prodottoId,
                "prodottoNome": m.prodottoNome,
                "contattoId": m.contattoId,
                "contattoDescrizione": m.contattoDescrizione,
                "documento": doc_dict,
                "creatoreUsername": m.creatoreUsername
            }
            raw_list.append(d)

        with open(self.movements_file, 'w', encoding='utf-8') as f:
            json.dump(raw_list, f, indent=2, ensure_ascii=False)

    # ---------------------------------------------------------
    # CONTATTI (Aziende e Privati)
    # ---------------------------------------------------------
    def load_contacts(self) -> List[Contatto]:
        if not os.path.exists(self.contacts_file):
            return []
        try:
            with open(self.contacts_file, 'r', encoding='utf-8') as f:
                raw_list = json.load(f)
            contacts = []
            for d in raw_list:
                ctype = d.get("class_type", "Privato")
                if ctype == "Azienda":
                    c = Azienda(
                        idContatto=d["idContatto"],
                        email=d["email"],
                        telefono=d["telefono"],
                        indirizzo=d["indirizzo"],
                        ragioneSociale=d.get("ragioneSociale", ""),
                        partitaIVA=d.get("partitaIVA", ""),
                        codiceDestinatarioSDI=d.get("codiceDestinatarioSDI", "")
                    )
                else:
                    c = Privato(
                        idContatto=d["idContatto"],
                        email=d["email"],
                        telefono=d["telefono"],
                        indirizzo=d["indirizzo"],
                        Nome=d.get("Nome", ""),
                        Cognome=d.get("Cognome", ""),
                        codiceFiscale=d.get("codiceFiscale", "")
                    )
                contacts.append(c)
            return contacts
        except Exception as e:
            print(f"Errore caricamento contatti: {e}")
            return []

    def save_contacts(self, contacts: List[Contatto]):
        raw_list = []
        for c in contacts:
            d = {
                "idContatto": c.idContatto,
                "email": c.email,
                "telefono": c.telefono,
                "indirizzo": c.indirizzo,
                "class_type": c.__class__.__name__
            }
            if isinstance(c, Azienda):
                d["ragioneSociale"] = c.ragioneSociale
                d["partitaIVA"] = c.partitaIVA
                d["codiceDestinatarioSDI"] = c.codiceDestinatarioSDI
            elif isinstance(c, Privato):
                d["Nome"] = c.Nome
                d["Cognome"] = c.Cognome
                d["codiceFiscale"] = c.codiceFiscale
            raw_list.append(d)

        with open(self.contacts_file, 'w', encoding='utf-8') as f:
            json.dump(raw_list, f, indent=2, ensure_ascii=False)

    # ---------------------------------------------------------
    # GESTORE BACKUP (UML: GestoreBackup, RF23)
    # ---------------------------------------------------------
    def esegui_backup(self, dest_folder: Optional[str] = None) -> str:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        target_dir = dest_folder or os.path.join(self.backup_dir, f"backup_{timestamp}")
        os.makedirs(target_dir, exist_ok=True)

        for filename in [self.users_file, self.products_file, self.movements_file, self.contacts_file, self.login_history_file, self.categories_file]:
            if os.path.exists(filename):
                shutil.copy2(filename, target_dir)

        # Informazioni di backup
        info = {
            "timestamp": timestamp,
            "data_backup": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "statoSistema": "COMPLETATO"
        }
        with open(os.path.join(target_dir, "backup_info.json"), 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2)

        return target_dir

    def ripristina_dati(self, backup_folder: str):
        if not os.path.exists(backup_folder):
            raise FileNotFoundError("La cartella di backup specificata non esiste.")

        for fname in ["users.json", "products.json", "movements.json", "contacts.json", "login_history.json", "categories.json"]:
            src = os.path.join(backup_folder, fname)
            if os.path.exists(src):
                dst = os.path.join(self.data_dir, fname)
                shutil.copy2(src, dst)
