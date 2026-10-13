# ⚓ Proiezione Turno Tripmare - Trieste

Applicazione web sviluppata in **Python** e **Streamlit** per la gestione, la consultazione e l'esportazione dei turni operativi del personale marittimo di **Tripmare S.p.A.** nel porto di Trieste.

L'applicazione proietta con esattezza matematica la rotazione continua degli equipaggi su un orizzonte pluriennale (2020–2035), consentendo la sincronizzazione del calendario su smartphone e la generazione istantanea dei moduli presenze e fogli turno pronti per la stampa.

---

## 🚀 Funzionalità Principali

### 1. Motore di Calcolo e Proiezione (`engine.py`)
- **Rotazione su Ciclo Master di 21 Settimane (147 giorni)**: proiezione deterministica continua ancorata alla settimana ufficiale master di riferimento (18-24 novembre 2024).
- **Quadratura Operativa Giornaliera (4-4-4-3-1-1-1-1-1-1)**:
  - 4 rimorchiatori sempre coperti sui turni operativi (`08:20` diurno, `20` montante notte, `08` smontante notte).
  - 3 equipaggi in disponibilità/reperibilità (`L1`, `L2`, `L3`).
  - 6 equipaggi in riposo totale (`L`).
  - 3 equipaggi dedicati alla settimana di Riserva (`R1`, `R2`, `R3`).
  - 1 equipaggio in salto/smonto riserva.
  - 4 equipaggi nei giorni di riposo ciclo base.
- **Calendario Festività CCNL Rimorchiatori (Art. 28)**:
  - Riconoscimento automatico delle 15 festività fisse nazionali e locali (incluso il Santo Patrono di Trieste, **San Giusto - 3 novembre**).
  - Gestione della Pasqua e del Lunedì dell'Angelo con calcolo computazionale dell'algoritmo di Meeus.
  - Evidenziazione dei semifestivi di contratto (Vigilia di Natale e Capodanno).

### 2. Visualizzazione Web Interattiva (`app.py`)
- **Modalità di Visualizzazione Multiple**:
  - *Equipaggio Specifico*: visuale focalizzata per singolo marittimo (con indicazione iconica per Eq. 8 🎱).
  - *Terzina*: raggruppamento per terzine operative storiche (3 equipaggi affiancati).
  - *Tutti gli Equipaggi*: panoramica integrale matriciale dei 21 equipaggi.
- **Orizzonte Temporale Flessibile**:
  - Navigazione rapida per *Mese Completo* o per *Settimane* (1, 2 o 3 settimane).
  - Pulsanti rapidi *Precedente*, *Oggi*, *Successivo* e selettori immediati Mese/Anno.
- **Diagnostica di Integrità a Schermo**: validazione automatica in tempo reale della copertura operativa di ogni singola giornata visualizzata.

### 3. Esportazioni e Stampe Dedicate

#### A. Stampa Turno Visualizzato in Bianco e Nero (`schedule_pdf.py`)
- Generazione dinamica in PDF vettoriale formato **A4 Landscape** della matrice attualmente visualizzata a schermo (singolo equipaggio, terzina o tutti i 21 equipaggi).
- **Grafica ad alto contrasto B/N**: priva di campiture di colore o retinature grigie per azzerare il consumo di inchiostro della stampante.
- Iniziali dei giorni maiuscole (`Lu`, `Ma`, `Me`, ...) ed evidenziazione dei festivi con ellisse discreta.

#### B. Foglio Presenze Mensile Aziendale (`timesheet.py`)
Riproduzione conforme al decimo di millimetro del modulo ufficiale aziendale cartaceo ed Excel:
- **Esportazione PDF Vettoriale (A4 Landscape)**:
  - Testata completa (*Mese*, *Anno*, *Cognome*, *Nome*, *Codice*).
  - Tabella delle 31 giornate con orari solari di servizio (*Dalle* / *Alle*).
  - Celle mergiate conformi per *Str.* (righe 1..3) e *Risc.* (righe 11..12).
  - Competenze compilate (*Maggiorazione Notturna*, *Indennità Navigazione*, *Festivo*, *Buoni pasto*).
  - Colonna finale *Tot.* lasciata in bianco per la verifica e quadratura a fine mese.
  - Spazio ampio per la *Firma del Capo Servizio* e tabella riepilogo a tutta larghezza per *Ferie* e *Compensativi*.
- **Esportazione Excel Nativo (`.xlsx`)**:
  - File modificabile speculare al PDF per eventuali integrazioni o variazioni turno.
  - Formule dinamiche `=SOMMA(...)` integrate nella colonna totali per l'aggiornamento automatico delle ore.

#### C. Sincronizzazione Calendario Smartphone (`engine.py`)
- Download del file di calendario standard **`.ics`** per importare i propri turni con gli orari esatti su Google Calendar, Apple Calendar o Microsoft Outlook.

---

## 📂 Struttura del Progetto

```text
├── app.py              # Interfaccia grafica Streamlit, routing e navigazione
├── engine.py           # Motore matematico del ciclo a 21 equipaggi e festività CCNL
├── timesheet.py        # Generatore vettoriale PDF ed Excel (.xlsx) del foglio presenze aziendale
├── schedule_pdf.py     # Generatore PDF in Bianco e Nero per la stampa del turno a video
├── faq.py              # Sezioni documentali integrate e domande frequenti sul turno
├── style.css           # Personalizzazione grafica, scrollbar e tema responsive
└── requirements.txt    # Dipendenze Python necessarie per il deployment
