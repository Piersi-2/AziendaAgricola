Scrivi il codice per il progetto inserito nella cartella "UML" tramite il file XMI e PDF.
Attieniti alle regole inserite nella cartella "skills".

Un'introduzione al nostro programma è questa:

L’azienda si occupa della produzione, trasformazione  e  vendita  olio, vino, miele,  grano,  girasoli, uva,  olive . Il software si occupa della gestione di:
·      Entrate ricavate dalle vendite ad aziende
·      Entrate ricavate dalle vendite al privato
·      Uscite:
§  Spese di manutenzione:
Ø Mezzi agricoli
Ø Altro
§  Spese di produzione (fertilizzante, semi, acqua, diserbanti, carburante):
§  Spese di vendita (bottiglie, etichette, tappi)
§  Stipendi dipendenti
§  Spese straordinarie (acquisto utensili e/o macchinari, imprevisti)
§  Tasse fisse (iva,imu, tari e smaltimento rifiuti speciali(olio motore, contenitori fitosanitari e concimi))
§  Assicurazioni:
Ø Dei dipendenti
Ø Dei mezzi agricoli
Ø Dell’azienda
·      Sistema:
prevede la realizzazione di un guadagno aziendale annuo di uno specifico anno dopo l’esecuzione del comando da parte dell’utente sommando algebricamente uscite ed entrate confrontate tramite il backup del sistema.
Inoltre il sistema deve essere in grado (tramite l’autenticatore) di individuare l’ultima data di login di un qualsiasi utente visibile solo dal manager.
Deve anche fare il logout dell’utente una volta che la sessione è scaduta.
Si dovrà accedere con nome utente e password; i manager potranno vedere la cronologia d’accesso dei suoi dipendenti.
Inizialmente si inizia registrando un manager che a sua volta potrà crearne altri.
 
 
REQUISITI FUNZIONALI
Area: Gestione Utenti
RF1: Registrazione profilo Manager
 Il sistema dovrà consentire al manager di registrarsi.
RF2: Creazione profilo utente
 Il sistema dovrà consentire ai manager di creare un profilo per un utente
RF3: Accesso profilo utente
 Il sistema dovrà consentire agli utenti di accedere all’account creato dal manager
RF4: Modifica profilo utente e manager
 Il sistema dovrà consentire agli utenti e manager di gestire il proprio profilo e modificarlo.
RF5: Elimina profilo utente
 Il sistema dovrà consentire ai manager di eliminare il profilo di un utente
 
Area: Gestione prodotti
RF6: Aggiungi prodotto
 Il sistema deve permettere di aggiungere un nuovo prodotto agricolo
RF7: Modifica prodotto
 Il sistema deve permettere di modificare un prodotto agricolo presente (prezzo, quantità, singolo o privato…)
RF8: Elimina prodotto
 Il sistema deve permettere di eliminare un nuovo prodotto agricolo
 
Area: Gestione entrate
RF9: Registrazione entrate per prodotto
 Il sistema deve permettere la registrazione delle vendite catalogate per prodotti
RF10: Separazione delle entrate in base al tipo di cliente
 Il sistema deve permettere la separazione delle entrate in base al tipo di cliente
 
Area: Gestione uscite
RF11: Registrazione spese di manutenzione
 Il sistema deve permettere la registrazione di spese legate alla manutenzione di varia natura
RF12: Registrazione spese di produzione
 Il sistema deve permettere la registrazione di spese legate alla produzione dei prodotti agricoli
RF13: Registrazione spese di vendita
 Il sistema deve permettere la registrazione di spese di confezionamento
RF14: Registrazione delle spese dovute a tasse
 Il sistema deve permettere la registrazione delle spese dovute alle tasse
RF15: Registrazione del pagamento dei salari dei dipendenti
 Il sistema deve permettere la registrazione del pagamento dei salari dei dipendenti
RF16: Registrazione delle spese dovute ad assicurazioni
 Il sistema deve permettere la registrazione delle spese derivanti dal pagamento di assicurazioni
RF17: Registrazione delle spese di smaltimento rifiuti
 Il sistema deve permettere la registrazione delle spese legate allo smaltimento dei rifiuti
RF18: Registrazione delle spese straordinarie
 Il sistema deve permettere la registrazione di tutte le spese che non rientrano nelle categorie precedenti
 
Area: Gestione sistema
RF19: Allegazione di documento relativo al movimento finanziario
Il sistema deve permettere di allegare uno o più documenti relativi alle entrate ed alle uscite, in più deve permettere di visualizzare tale documento
RF20: Catalogazione delle entrate per prodotto
 Il sistema deve mostrare le entrate catalogate per prodotto e per anno
RF21: Catalogazione delle uscite per prodotto
 Il sistema deve mostrare le uscite catalogate per prodotto e per anno
RF22: Guadagno aziendale
 Il sistema deve mostrare in una sezione guadagno la differenza fra entrate ed uscite
RF23: Backup
 Il sistema dovrà effettuare un backup periodico dei dati.
 




 
REQUISITI NON FUNZIONALI
 
RNF1: Implementazione in Python 3
 Il sistema dovrà essere implementato in linguaggio Python3.
RNF2: Implementazione grafica
 Il sistema dovrà implementare un’interfaccia grafica in PyQt6.
RNF3: Validazione password
 Il sistema dovrà validare la password di un utente o un owner solo se è di almeno 8 caratteri alfanumerici
RNF4: Unicità email
 Il sistema non dovrà consentire l’utilizzo di un’email utente già in uso
RNF5: Unicità prodotto
 Il sistema non dovrà consentire l’aggiunta di un prodotto già esistente.
RNF6: Gestione recupero password tramite email
 Il sistema permetterà all’utente di recuperare la propria password tramite email
RNF7: Gestione data inserimento prodotto
 Il sistema dovrà permettere di inserire la data di vendita e acquisto del prodotto
RNF8: Limite di caratteri circa la lunghezza della descrizione del movimento
Il sistema non dovrà accettare descrizioni con più di 500 caratteri
