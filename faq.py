import streamlit as st
import os

DOCUMENTS_CONFIG = [
    {
        "label": "📥 CIA Tripmare 2018",
        "filename": "cia_tripmare_2018.pdf",
        "desc": "Contratto Integrativo Aziendale Tripmare"
    },
    {
        "label": "📥 CCNL Sez. 11 Rimorchio",
        "filename": "ccnl_sez11_rimorchio.pdf",
        "desc": "CCNL Sezione 11 - Rimorchio Portuale"
    },
    {
        "label": "📥 Aggiornamento CCNL 2024",
        "filename": "aggiornamento_ccnl_2024.pdf",
        "desc": "Accordo di rinnovo e aggiornamento 2024"
    },
    {
        "label": "📥 Ormeggi Trieste",
        "filename": "ormeggi_trieste.pdf",
        "desc": "Piantina ormeggi Trieste"
    }
]

def render_documentation_section():
    """Mostra l'area di download per i contratti e le piantine."""
    st.write("---")
    st.subheader("📄 Documentazione Contrattuale e Accordi")

    doc_cols = st.columns(4)

    for idx, item in enumerate(DOCUMENTS_CONFIG):
        direct_path = item["filename"]
        subfolder_path = os.path.join("documenti", item["filename"])
        file_path = direct_path if os.path.exists(direct_path) else subfolder_path

        with doc_cols[idx]:
            st.markdown(f"**{item['desc']}**")
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    pdf_data = f.read()
                st.download_button(
                    label=item["label"],
                    data=pdf_data,
                    file_name=item["filename"],
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.button(
                    f"{item['label']} (Non trovato)",
                    disabled=True,
                    use_container_width=True,
                    help="Verifica che il file sia presente nella cartella principale o in 'documenti/'."
                )

def render_faq_section():
    """Mostra la sezione delle domande frequenti (FAQ)."""
    st.write("---")
    st.subheader("❓ Domande Frequenti (FAQ)")

    with st.expander("**Cosa segno sul foglio ore in caso di scivolamento?**"):
        st.markdown("""
        In caso di **scivolamento**, la corretta rendicontazione da indicare sul foglio presenze è la seguente (*rif. CIA, pag. 29*):
        * **Dalle ore 20:00 alle ore 24:00**: straordinario calcolato con formula **2x1** (pari a **8 ore di straordinario ad aliquota base diurna**).
        * **Dalle ore 00:00 alle ore 08:00**: **6 ore di straordinario notturno** (ad aliquota feriale o festiva, a seconda del calendario della giornata) + **2 ore di straordinario diurno** (feriale o festivo) + maturazione di **1 giorno compensativo**.
        """)

    with st.expander("**Cosa segno se vengo messo in turno 20-08 dopo aver già preso servizio la mattina alle 08?**"):
        st.markdown("""
        La rendicontazione oraria varia in base all'effettivo riposo intercorso tra le prestazioni (*rif. CIA, pag. 29*):
        
        * **Caso 1 – Preso servizio alle 08:00 e reso libero entro le ore 12:00**:
          * **Dalle 08:00 alle 12:00**: orario e compenso normale.
          * **Dalle 22:00 alle 24:00**: straordinario calcolato con formula **3x1** *(la ripresa del servizio avviene alle 22:00 per garantire il periodo minimo di riposo)*.
          * **Dalle 00:00 alle 08:00**: stessa rendicontazione prevista per lo scivolamento (6 ore straordinario notturno feriale/festivo + 2 ore straordinario diurno feriale/festivo + 1 giorno compensativo).

        * **Caso 2 – Preso servizio alle 08:00 e continuato senza riposo**:
          * **Dalle 08:00 alle 20:00**: orario e compenso normale.
          * **Dalle 20:00 alle 24:00**: straordinario notturno (feriale o festivo).
          * **Dalle 00:00 alle 08:00**: straordinario come da scivolamento (6 ore notturne + 2 ore diurne feriali/festive) + **2 giorni compensativi** + applicazione straordinario **3x1** qualora venga superata la 14ª ora complessiva di prestazione.
        """)

    with st.expander("**Come segno se prolungo il servizio oltre le 08:00 smontando dalla notte?**"):
        st.markdown("""
        La rendicontazione delle ore di prolungamento oltre il normale orario di smonto delle 08:00 dipende dall'orario esatto in cui è stato **preso/voltato il cavo** (*rif. CIA, pag. 30*):

        * **Caso A – Presa cavo DOPO le 08:00**:
          *(Il servizio o la manovra inizia effettivamente dopo il termine del turno ordinario)*
          * **1ª ora (dalle 08:00 alle 09:00)**: **1 ora di straordinario** + maturazione di **1 indennità di servizio prolungato**.
          * **2ª ora (dalle 09:00 alle 10:00)**: **1 ora di straordinario** + maturazione di **1 indennità di servizio prolungato**.
          * **Dalla 3ª ora in poi (dalle 10:00 in avanti)**: straordinario calcolato con formula **3x1** (pari a **3 ore di straordinario per ogni ora effettiva** lavorata).

        * **Caso B – Presa cavo PRIMA delle 08:00**:
          *(La manovra era già in corso prima delle 08:00 e si protrae oltre il termine del turno)*
          * **1ª ora (dalle 08:00 alle 09:00)**: **1 ora** di straordinario.
          * **2ª ora (dalle 09:00 alle 10:00)**: straordinario calcolato con formula **2x1** (pari a **2 ore** di straordinario).
          * **Dalla 3ª ora in poi (dalle 10:00 in avanti)**: straordinario calcolato con formula **3x1** (pari a **3 ore** di straordinario per ogni ora effettiva).
        """)

    with st.expander("Come funziona la rotazione delle 21 settimane e delle riserve?"):
        st.write("""
        I 21 equipaggi sono suddivisi in 7 terzine (da Terzina 1 a Terzina 7).
        Il ciclo completo dura 21 settimane (147 giorni) suddiviso in 3 tranche temporali da 7 settimane ciascuna.
        Durante ogni tranche, a turno, ogni equipaggio della terzina svolge una settimana di riserva (R1, R2 o R3) con un punto di rientro prestabilito (L1, L2 o L3) che determina l'aggancio sul ciclo di lavoro base di 18 giorni.
        """)

    with st.expander("Qual è la differenza tra i giorni L e le disponibilità L1, L2, L3?"):
        st.write("""
        Il codice **L** rappresenta il giorno di libero puro (riposo totale da contratto).
        I codici **L1**, **L2** e **L3** rappresentano i giorni di disponibilità previsti dalla rotazione del ciclo, che precedono o seguono i blocchi di servizio sui mezzi operativi.
        """)

    with st.expander("Come vengono conteggiate le festività e le semifestività (CCNL Art. 28)?"):
        st.markdown("""
        * **Giorni festivi (CCNL Art. 28 comma 1)**: Il calendario evidenzia in **rosso** tutte le domeniche e i 15 giorni festivi riconosciuti da contratto (compresi il Santo Patrono San Giusto il 3 novembre e la festività del 4 novembre).
        * **Giorni semifestivi (CCNL Art. 28 comma 2)**: Sono considerate semifestive, e cioè **festive solo nelle ore pomeridiane**, la Vigilia di Natale (24 dicembre) e la Vigilia di Pasqua (Sabato Santo), evidenziate in calendario in color **salmone**.
        """)

    with st.expander("Come vengono dislocati i rimorchiatori sul porto di Trieste e quali sono i mezzi RSD?"):
        st.markdown("""
        * **Zona SIOT (Terminal Petrolifero)**: Mezzi **1 e 2**.
        * **Zona PFV / Base (Porto Franco Vecchio)**: Mezzi **3 e 4**.
        * **Propulsione**:
          * Mezzi dispari (**1, 3**): propulsione cicloidale Voith Schneider (VWT).
          * Mezzi pari (**2, 4**): propulsione azimutale (ASD).
        * **Rimorchiatori RSD (Reversed Stern Drive)**: operano attualmente in servizio presso la base del **PFV (Porto Franco Vecchio)** sia come mezzo numero **3** che numero **4**.
        """)
