# ⚓ Proiezione Turno Tripmare — Rimorchiatori Trieste

Applicazione web interattiva sviluppata in **Python** e **Streamlit** per la proiezione, il calcolo e la visualizzazione tabellare a nastro dei turni di servizio per i **21 equipaggi** dei rimorchiatori portuali in servizio a Trieste.

L'interfaccia simula il foglio presenze operativo, ottimizzata sia per l'uso su **desktop/Chromebook** che su **dispositivi mobili** (consigliata la rotazione orizzontale in Landscape).

---

## 🎯 Funzionalità Principali

* **Matrice a nastro mensile e settimanale**: visualizzazione orizzontale continua del calendario con blocco dei riquadri in alto (*sticky header* per giorno e data) e a sinistra (colonna equipaggi bloccata).
* **Motore di calcolo ciclico (`engine.py`)**:
  * Rotazione master su **21 settimane** (147 giorni) suddivisa in 3 tranche da 7 settimane per le 7 terzine di equipaggi.
  * Gestione automatica delle settimane di riserva (**R1, R2, R3**) e dei punti di rientro (**L1, L2, L3**) sul ciclo base di 18 giorni.
  * Turni operativi: Diurno (`08:20`), Montante notte (`20`), Smontante notte (`08`).
* **Calendario integrato delle festività**:
  * Evidenziazione in **rosso** di tutte le domeniche e delle 15 festività da CCNL Sez. 11 (inclusi il Santo Patrono San Giusto il 3 novembre e il 4 novembre).
  * Evidenziazione in **salmone** delle semifestività (Vigilia di Pasqua e Vigilia di Natale pomeridiane, CCNL Art. 28).
  * Evidenziazione visiva immediata della **giornata odierna (Oggi)** con binario verticale blu dedicato.
* **Navigazione rapida**:
  * Tasti veloci `◀ Precedente`, `Oggi`, `Successivo ▶`.
  * Tendine sincronizzate per il cambio istantaneo di **Mese** e **Anno** (esteso dal 2020 al 2035).
* **Filtri di visualizzazione**: visualizzazione di tutti i 21 equipaggi contemporaneamente, per singola terzina o per equipaggio specifico.
* **Tooltip informativi**: passaggio del mouse/cursore su ogni cella per visualizzare equipaggio, data, turno, mezzo e zona operativa.
* **Area Documentale**: download diretto dei PDF contrattuali (CIA 2018, CCNL Sez. 11, Rinnovo 2024, Piantina ormeggi Trieste).
* **FAQ Operative**: risposte rapide alle domande più frequenti su scivolamenti, straordinari 2x1/3x1, riposi e dislocazione mezzi.

---

## 🚢 Flotta e Dislocazione Portuale

* **Postazione SIOT (Terminal Petrolifero)**: Mezzi **1** e **2**.
* **Postazione PFV / Base (Porto Franco Vecchio)**: Mezzi **3** e **4**.
* **Tipologia di Propulsione**:
  * Numeri dispari (**1, 3**): Propulsione cicloidale Voith Schneider (**VWT**).
  * Numeri pari (**2, 4**): Propulsione azimutale (**ASD** / **RSD**).

---

## 🛠️ Struttura del Progetto

```text
├── app.py                      # Interfaccia grafica Streamlit, layout CSS e rendering HTML
├── engine.py                   # Algoritmo matematico dei turni e calcolo festività
├── cia_tripmare_2018.pdf       # Documento CIA 2018 per il download
├── ccnl_sez11_rimorchio.pdf    # Testo CCNL Sez. 11 Rimorchio portuale
├── aggiornamento_ccnl_2024.pdf # Accordo di rinnovo 2024
├── ormeggi_trieste.pdf         # Piantina degli ormeggi del porto di Trieste
└── README.md                   # Documentazione del progetto
