# AziendaAgricola
Il progetto prevede la realizzazione di un sistema gestionale desktop per un’azienda agricola. Il software nasce con l’obiettivo di sostituire la gestione manuale dei conti aziendali, permettendo di registrare in un unico strumento entrate, uscite, prodotti venduti e personale.

Al primo avvio viene registrato il manager, cioè il proprietario dell’azienda, che ha accesso a tutte le funzionalità e può creare, modificare ed eliminare i profili dei dipendenti. I dipendenti accedono con le proprie credenziali e hanno permessi limitati. Ogni utente può modificare il proprio profilo. La password deve avere almeno 8 caratteri alfanumerici, l’email deve essere unica e la sessione scade dopo un periodo di inattività.

Il catalogo raccoglie i prodotti agricoli dell’azienda. Ogni prodotto, identificato da un nome unico, appartiene a una categoria con la propria unità di misura ed è descritto da una descrizione e da un prezzo unitario. Il sistema permette di aggiungere, modificare ed eliminare prodotti e categorie.

Le entrate rappresentano le vendite e sono registrate indicando prodotto, quantità, importo, data e una descrizione di massimo 500 caratteri. Ogni vendita è associata a un cliente, che può essere un’azienda, identificata da ragione sociale, partita IVA e codice SDI, oppure un privato, identificato da nome, cognome e codice fiscale. In questo modo le entrate sono separate per tipo di cliente.

Le uscite comprendono le spese di manutenzione, produzione e vendita, le tasse, gli stipendi, le assicurazioni, lo smaltimento rifiuti e le spese straordinarie, con l’indicazione facoltativa del fornitore e del prodotto di riferimento.

A ogni movimento è possibile allegare uno o più documenti PDF, come fatture o ricevute, visualizzabili direttamente dal programma. Entrate e uscite possono essere modificate, eliminate e filtrate per prodotto, per anno e, nel caso delle entrate, per tipo di cliente.

Nella sezione dedicata al guadagno aziendale, accessibile solo al manager, il sistema calcola per l’anno selezionato il totale delle entrate, il totale delle uscite e il margine netto, e permette di generare un report riepilogativo.

L’applicazione è sviluppata in Python 3, con interfaccia grafica realizzata in PyQt5 e salvataggio dei dati in file JSON.

