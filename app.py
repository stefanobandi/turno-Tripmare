import streamlit as st
import datetime
import calendar
import os
from engine import get_week_index, get_shift_for_crew, get_holiday_type

st.set_page_config(page_title="Proiezione turno Tripmare", layout="wide")

# CSS Avanzato per tabella a nastro, sticky headers, evidenziazione oggi e sezioni informative
st.markdown("""
<style>
    /* Rimuove i margini esterni ingombranti di Streamlit */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 100% !important;
    }

    /* Contenitore a scorrimento bidirezionale con altezza controllata per sticky header */
    .matrix-wrapper {
        overflow: auto;
        max-height: 72vh;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        position: relative;
        -webkit-overflow-scrolling: touch;
        background-color: #ffffff;
    }

    .matrix-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        table-layout: fixed;
    }

    .matrix-table th, .matrix-table td {
        border-right: 1px solid #cbd5e1;
        border-bottom: 1px solid #cbd5e1;
        text-align: center;
        padding: 3px 1px;
    }

    /* Sticky Headers: riga 1 (giorno) e riga 2 (nome) bloccate in alto */
    .th-row-1 {
        position: sticky;
        top: 0;
        z-index: 10;
        height: 26px;
    }
    .th-row-2 {
        position: sticky;
        top: 26px;
        z-index: 10;
        height: 22px;
    }

    /* Colonna equipaggi bloccata a sinistra */
    .crew-label-cell {
        background-color: #0f172a !important;
        color: #ffffff !important;
        font-weight: bold;
        font-size: 12px;
        position: sticky;
        left: 0;
        z-index: 5;
        width: 65px;
        min-width: 65px;
        border-right: 2px solid #64748b !important;
    }

    /* Angolo in alto a sinistra (incrocio sticky riga e colonna) */
    .th-corner-1 {
        position: sticky;
        top: 0;
        left: 0;
        z-index: 25 !important;
        background-color: #0f172a !important;
        color: #ffffff !important;
    }
    .th-corner-2 {
        position: sticky;
        top: 26px;
        left: 0;
        z-index: 25 !important;
        background-color: #0f172a !important;
        color: #ffffff !important;
    }

    .header-day-num {
        font-size: 12px;
        font-weight: bold;
    }
    .header-day-name {
        font-size: 10px;
        text-transform: uppercase;
    }

    /* Stili giorni calendario */
    .th-normal {
        background-color: #f1f5f9;
        color: #1e293b;
    }
    .th-holiday {
        background-color: #dc2626 !important;
        color: #ffffff !important;
    }
    .th-semiholiday {
        background-color: #fca5a5 !important;
        color: #7f1d1d !important;
    }

    /* Evidenziazione Colonna Oggi */
    .col-today {
        border-left: 2px solid #2563eb !important;
        border-right: 2px solid #2563eb !important;
    }
    .th-today {
        box-shadow: inset 0 -3px 0 #2563eb;
    }

    /* Celle turno */
    .cell-content {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 44px;
        line-height: 1.1;
        cursor: default;
    }

    .mezzo-num {
        font-weight: 800;
        font-size: 12px;
        color: #0284c7;
    }
    .stato-text {
        font-weight: 600;
        font-size: 11px;
    }

    /* Colori turni e riposi coordinati con la legenda */
    .cell-l {
        background-color: #dcfce7;
        color: #15803d;
    }
    .cell-l-disp {
        background-color: #fef9c3;
        color: #854d0e;
    }
    .cell-reserve {
        background-color: #e2e8f0;
        color: #334155;
        font-weight: bold;
    }
    .cell-work {
        background-color: #ffffff;
        color: #0f172a;
    }

    .device-hint {
        font-size: 13px;
        color: #475569;
        margin-top: -10px;
        margin-bottom: 12px;
        font-style: italic;
    }

    /* Box Legenda */
    .legend-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 16px;
        margin-top: 15px;
        font-size: 12px;
    }
    .legend-color-pill {
        display: inline-block;
        width: 13px;
        height: 13px;
        border-radius: 3px;
        margin-right: 6px;
        vertical-align: -2px;
        border: 1px solid #cbd5e1;
    }

    /* Modalità Portrait su Smartphone */
    @media screen and (orientation: portrait) and (max-width: 768px) {
        .matrix-table {
            table-layout: auto;
        }
        .matrix-table th, .matrix-table td {
            min-width: 38px;
            padding: 3px 2px;
        }
        .crew-label-cell {
            min-width: 55px;
            width: 55px;
            font-size: 11px;
        }
    }

    /* Modalità Landscape su Smartphone/Tablet */
    @media screen and (orientation: landscape) and (max-width: 1024px) {
        .matrix-table {
            table-layout: fixed;
            width: 100%;
        }
        .matrix-table th, .matrix-table td {
            min-width: 0 !important;
            padding: 2px 0px !important;
        }
        .header-day-num {
            font-size: 10px !important;
        }
        .header-day-name {
            font-size: 8px !important;
        }
        .crew-label-cell {
            width: 45px !important;
            min-width: 45px !important;
            font-size: 10px !important;
            padding: 2px 1px !important;
        }
        .cell-content {
            height: 38px !important;
        }
        .mezzo-num {
            font-size: 10px !important;
        }
        .stato-text {
            font-size: 9px !important;
            letter-spacing: -0.5px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Mappatura dei mesi
MESI_ITALIANO = [
    "", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
]

MESI_BREVI_ITALIANO = [
    "", "gen", "feb", "mar", "apr", "mag", "giu",
    "lug", "ago", "set", "ott", "nov", "dic"
]

def build_cell_tooltip(crew_num: int, target_date: datetime.date, mezzo: int, stato: str) -> str:
    """Restituisce il testo esplicativo per il tooltip al passaggio del mouse."""
    mese_abbr = MESI_BREVI_ITALIANO[target_date.month]
    date_formatted = f"{target_date.strftime('%d')} {mese_abbr} {target_date.year}"
    header_line = f"EQ{crew_num} - {date_formatted}"
    lines = [header_line]

    if mezzo:
        dislocazione = "SIOT" if mezzo in [1, 2] else "PFV / Base"
        
        if stato == "20":
            turno_desc = "Montante notte"
        elif stato == "08":
            turno_desc = "Smontante notte"
        elif stato == "08:20":
            turno_desc = "Giorno dalle 08 alle 20"
        else:
            turno_desc = stato

        lines.append(f"Turno: {turno_desc}")
        lines.append(f"Mezzo: Rimorchiatore {mezzo} in {dislocazione}")
    else:
        if stato == "L":
            lines.append("Stato: Libero")
        elif stato in ["L1", "L2", "L3"]:
            lines.append(f"Stato: Disponibilità {stato}")
        elif stato.startswith("R"):
            lines.append(f"Stato: Settimana di Riserva {stato}")
        else:
            lines.append(f"Stato: {stato}")

    return "&#10;".join(lines)

# Inizializzazione session_state per navigazione
if "current_date" not in st.session_state:
    st.session_state.current_date = datetime.date.today()

# Header e Controlli Superiori
st.title("⚓ Proiezione turno Tripmare")
st.markdown('<p class="device-hint">📱 Su dispositivi mobili si consiglia la visualizzazione in orizzontale (Landscape).</p>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns([1.5, 1.2, 1.2, 1.5])

with c1:
    view_type = st.selectbox(
        "Modalità Visualizzazione",
        options=["Equipaggio Specifico", "Terzina", "Tutti gli Equipaggi"],
        index=2
    )

with c2:
    if view_type == "Equipaggio Specifico":
        selected_crew = st.selectbox("Seleziona Equipaggio", options=list(range(1, 22)), index=7)
    elif view_type == "Terzina":
        terzina_choice = st.selectbox(
            "Seleziona Terzina",
            options=list(range(1, 8)),
            format_func=lambda x: f"Terzina {x} (Eq. {(x-1)*3+1}-{(x-1)*3+2}-{(x-1)*3+3})"
        )
    else:
        st.write("")

with c3:
    time_horizon = st.selectbox("Orizzonte Temporale", options=["Mese Completo", "Settimane"], index=0)

with c4:
    if time_horizon == "Settimane":
        num_weeks = st.selectbox("Durata Settimane", options=[1, 2, 3], index=0)
    else:
        num_weeks = 1

# Barra di Navigazione Mese/Anno e Pulsanti Rapidi
st.write("---")
nav1, nav2, nav3, nav4, nav5 = st.columns([1, 1, 1, 1.2, 1.2])

def advance_date(direction: int):
    d = st.session_state.current_date
    if time_horizon == "Mese Completo":
        year = d.year
        month = d.month + direction
        if month > 12:
            month = 1
            year += 1
        elif month < 1:
            month = 12
            year -= 1
        max_days = calendar.monthrange(year, month)[1]
        target_day = min(d.day, max_days)
        st.session_state.current_date = datetime.date(year, month, target_day)
    else:
        delta = datetime.timedelta(weeks=direction * num_weeks)
        st.session_state.current_date = d + delta

with nav1:
    if st.button("◀ Precedente", use_container_width=True):
        advance_date(-1)
        st.rerun()

with nav2:
    if st.button("Oggi", use_container_width=True):
        st.session_state.current_date = datetime.date.today()
        st.rerun()

with nav3:
    if st.button("Successivo ▶", use_container_width=True):
        advance_date(1)
        st.rerun()

# Tendine sincronizzate Mese e Anno (2020 - 2035)
curr_date = st.session_state.current_date

with nav4:
    sel_month = st.selectbox(
        "Mese",
        options=list(range(1, 13)),
        index=curr_date.month - 1,
        format_func=lambda m: MESI_ITALIANO[m],
        label_visibility="collapsed"
    )

with nav5:
    year_options = list(range(2020, 2036))
    curr_year_idx = year_options.index(curr_date.year) if curr_date.year in year_options else 6
    sel_year = st.selectbox(
        "Anno",
        options=year_options,
        index=curr_year_idx,
        label_visibility="collapsed"
    )

# Aggiornamento automatico se l'utente cambia tendina mese/anno
if sel_month != curr_date.month or sel_year != curr_date.year:
    max_days = calendar.monthrange(sel_year, sel_month)[1]
    new_day = min(curr_date.day, max_days)
    st.session_state.current_date = datetime.date(sel_year, sel_month, new_day)
    st.rerun()

# Date da visualizzare
curr = st.session_state.current_date
today_date = datetime.date.today()
dates_to_show = []

if time_horizon == "Mese Completo":
    year = curr.year
    month = curr.month
    _, num_days = calendar.monthrange(year, month)
    dates_to_show = [datetime.date(year, month, day) for day in range(1, num_days + 1)]
    nome_mese_it = MESI_ITALIANO[month]
    st.markdown(f"### Mese di **{nome_mese_it} {year}**")
else:
    start_monday = curr - datetime.timedelta(days=curr.weekday())
    total_days = num_weeks * 7
    dates_to_show = [start_monday + datetime.timedelta(days=i) for i in range(total_days)]
    st.markdown(f"### Visualizzazione **{num_weeks} Settimana/e** (dal {dates_to_show[0].strftime('%d/%m/%Y')} al {dates_to_show[-1].strftime('%d/%m/%Y')})")

# Determinazione della lista equipaggi da stampare
if view_type == "Equipaggio Specifico":
    crews_to_render = [selected_crew]
elif view_type == "Terzina":
    start_c = (terzina_choice - 1) * 3 + 1
    crews_to_render = [start_c, start_c + 1, start_c + 2]
else:
    crews_to_render = list(range(1, 22))

# Generazione della tabella HTML con sticky header e colonna oggi evidenziata
html_table = ['<div class="matrix-wrapper"><table class="matrix-table">']

# Riga Intestazione 1: Numero Giorno
html_table.append('<thead><tr><th class="crew-label-cell th-corner-1">Giorno</th>')
day_names_it = ["lu", "ma", "me", "gi", "ve", "sa", "do"]

for d in dates_to_show:
    is_hol, is_semi, h_name = get_holiday_type(d)
    is_today = (d == today_date)
    
    th_classes = ["th-row-1"]
    if is_hol:
        th_classes.append("th-holiday")
    elif is_semi:
        th_classes.append("th-semiholiday")
    else:
        th_classes.append("th-normal")
        
    if is_today:
        th_classes.append("col-today th-today")
        
    title_attr = f'title="{h_name}"' if h_name else ''
    
    html_table.append(f'<th class="{" ".join(th_classes)}" {title_attr}><span class="header-day-num">{d.strftime("%d")}</span></th>')
html_table.append('</tr>')

# Riga Intestazione 2: Nome Giorno abbreviato
html_table.append('<tr><th class="crew-label-cell th-corner-2">Eq.</th>')
for d in dates_to_show:
    is_hol, is_semi, _ = get_holiday_type(d)
    is_today = (d == today_date)
    
    th_classes = ["th-row-2"]
    if is_hol:
        th_classes.append("th-holiday")
    elif is_semi:
        th_classes.append("th-semiholiday")
    else:
        th_classes.append("th-normal")
        
    if is_today:
        th_classes.append("col-today")
        
    day_name = day_names_it[d.weekday()]
    html_table.append(f'<th class="{" ".join(th_classes)}"><span class="header-day-name">{day_name}</span></th>')
html_table.append('</tr></thead><tbody>')

# Righe degli equipaggi
for c_num in crews_to_render:
    html_table.append(f'<tr><td class="crew-label-cell">Eq. {c_num}</td>')
    for d in dates_to_show:
        shift = get_shift_for_crew(c_num, d)
        mezzo = shift["mezzo"]
        stato = shift["stato"]
        is_today = (d == today_date)
        
        td_classes = []
        if stato == "L":
            td_classes.append("cell-l")
        elif stato in ["L1", "L2", "L3"]:
            td_classes.append("cell-l-disp")
        elif stato.startswith("R"):
            td_classes.append("cell-reserve")
        else:
            td_classes.append("cell-work")
            
        if is_today:
            td_classes.append("col-today")
            
        mezzo_html = f'<span class="mezzo-num">{mezzo}</span>' if mezzo else ''
        stato_html = f'<span class="stato-text">{stato}</span>'
        tooltip_text = build_cell_tooltip(c_num, d, mezzo, stato)
        
        html_table.append(
            f'<td class="{" ".join(td_classes)}" title="{tooltip_text}">'
            f'<div class="cell-content">{mezzo_html}{stato_html}</div>'
            f'</td>'
        )
    html_table.append('</tr>')

html_table.append('</tbody></table></div>')

st.markdown("".join(html_table), unsafe_allow_html=True)

# Legenda Dettagliata ed Esplicativa
st.markdown("""
<div class="legend-box">
    <div style="font-weight: bold; font-size: 13px; margin-bottom: 8px; color: #0f172a;">LEGENDA OPERATIVA E CALENDARIO</div>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px;">
        <div>
            <b>Turni Operativi:</b><br>
            • <span class="legend-color-pill" style="background-color: #ffffff;"></span><b>08:20</b>: Diurno (dalle 08:00 alle 20:00)<br>
            • <span class="legend-color-pill" style="background-color: #ffffff;"></span><b>20</b>: Montante notte (dalle 20:00)<br>
            • <span class="legend-color-pill" style="background-color: #ffffff;"></span><b>08</b>: Smontante notte (fino alle 08:00)
        </div>
        <div>
            <b>Riposi e Riserve:</b><br>
            • <span class="legend-color-pill" style="background-color: #dcfce7;"></span><b>L</b>: Libero (riposo totale)<br>
            • <span class="legend-color-pill" style="background-color: #fef9c3;"></span><b>L1 / L2 / L3</b>: Disponibilità L1, L2 o L3<br>
            • <span class="legend-color-pill" style="background-color: #e2e8f0;"></span><b>R1 / R2 / R3</b>: Settimana di Riserva
        </div>
        <div>
            <b>Rimorchiatori e Dislocazione:</b><br>
            • <b>Mezzi 1 e 2</b>: SIOT<br>
            • <b>Mezzi 3 e 4</b>: PFV / Base<br>
            • <b>Dispari (1, 3)</b>: Voith (VWT)<br>
            • <b>Pari (2, 4)</b>: Azimutale (ASD / RSD)
        </div>
        <div>
            <b>Calendario:</b><br>
            • <span class="legend-color-pill" style="background-color: #dc2626;"></span><b>Rosso</b>: Festivo CCNL (15gg) / Domenica<br>
            • <span class="legend-color-pill" style="background-color: #fca5a5;"></span><b>Salmone</b>: Semifestivo (CCNL Art. 28)<br>
            • <span class="legend-color-pill" style="background-color: #ffffff; border: 2px solid #2563eb;"></span><b>Bordo Blu</b>: Giornata odierna (Oggi)
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sezione Download Accordi e Contratti (PDF)
st.write("---")
st.subheader("📄 Documentazione Contrattuale e Accordi")

files_config = [
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

doc_cols = st.columns(4)

for idx, item in enumerate(files_config):
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
            st.button(f"{item['label']} (Non trovato)", disabled=True, use_container_width=True, help="Verifica che il nome del file coincida esattamente con quello previsto.")

# Sezione FAQ (Espandibili)
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
    * **Giorni semifestivi (CCNL Art. 28 comma 2)**: Sono considerate semifestive, e cioè **festive solo nelle ore pomeridiane**, la Vigilia di Natale (24 dicembre) e la Vigilia di Pasqua (Sabato Santo), evidenziate in calendario in color **salmone**[cite: 2].
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
