import streamlit as st
import datetime
import calendar
from engine import get_week_index, get_shift_for_crew, get_holiday_type

st.set_page_config(page_title="Proiezione turno Tripmare", layout="wide")

# CSS personalizzato responsive e stile popup modale
st.markdown("""
<style>
    /* Rimuove i margini esterni ingombranti di Streamlit */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 100% !important;
    }

    .matrix-table {
        width: 100%;
        border-collapse: collapse;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        margin-top: 10px;
        margin-bottom: 20px;
        table-layout: fixed;
    }
    
    .matrix-table th, .matrix-table td {
        border: 1px solid #cbd5e1;
        text-align: center;
        padding: 3px 1px;
    }

    .header-day-num {
        font-size: 12px;
        font-weight: bold;
    }
    .header-day-name {
        font-size: 10px;
        text-transform: uppercase;
    }
    
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

    .crew-label-cell {
        background-color: #0f172a;
        color: #ffffff;
        font-weight: bold;
        font-size: 12px;
        position: sticky;
        left: 0;
        z-index: 2;
        width: 65px;
        min-width: 65px;
    }

    .clickable-cell {
        cursor: pointer;
        user-select: none;
        -webkit-tap-highlight-color: rgba(0,0,0,0.1);
    }

    .cell-content {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 44px;
        line-height: 1.1;
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
        margin-top: -12px;
        margin-bottom: 12px;
        font-style: italic;
    }

    /* Modal / Popup nativo per smartphone e desktop */
    #infoModal {
        border: none;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        padding: 20px;
        max-width: 320px;
        width: 85%;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    #infoModal::backdrop {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(2px);
    }
    .modal-title {
        font-size: 16px;
        font-weight: bold;
        color: #0f172a;
        margin-bottom: 10px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 6px;
    }
    .modal-body {
        font-size: 14px;
        color: #334155;
        line-height: 1.5;
        margin-bottom: 16px;
        white-space: pre-line;
    }
    .modal-btn {
        background-color: #0284c7;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: 600;
        width: 100%;
        cursor: pointer;
    }

    /* Modalità Portrait (smartphone in verticale) */
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

    /* Modalità Landscape (smartphone/tablet in orizzontale) */
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

<!-- Dialog modale HTML nativo con script di ascolto tap/click -->
<dialog id="infoModal">
    <div id="modalTitle" class="modal-title">Dettaglio Turno</div>
    <div id="modalBody" class="modal-body"></div>
    <button class="modal-btn" onclick="document.getElementById('infoModal').close()">Chiudi</button>
</dialog>

<script>
function showShiftInfo(title, details) {
    var modal = document.getElementById('infoModal');
    if (modal) {
        document.getElementById('modalTitle').innerText = title;
        document.getElementById('modalBody').innerText = details;
        modal.showModal();
    }
}
</script>
""", unsafe_allow_html=True)

# Mappatura dei mesi in italiano
MESI_ITALIANO = [
    "", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
]

def build_cell_info(crew_num: int, target_date: datetime.date, mezzo: int, stato: str) -> tuple:
    """
    Restituisce (titolo, testo_dettagliato) per il popup al tocco e tooltip.
    Senza dettagli su propulsione (VWT/ASD), solo 'Rimorchiatore X in Canale/Base'.
    """
    date_str = target_date.strftime("%d/%m/%Y")
    title = f"Equipaggio {crew_num} • {date_str}"
    lines = []

    if mezzo:
        dislocazione = "Canale" if mezzo in [1, 2] else "Base"
        
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

    return title, "\n".join(lines)

# Inizializzazione session_state sincronizzato
if "current_date" not in st.session_state:
    st.session_state.current_date = datetime.date.today()

if "date_selector" not in st.session_state:
    st.session_state.date_selector = st.session_state.current_date

def on_date_picker_change():
    st.session_state.current_date = st.session_state.date_selector

# Titolo e Avviso Orientamento Dispositivo
st.title("⚓ Proiezione turno Tripmare")
st.markdown('<p class="device-hint">📱 Su dispositivi mobili si consiglia la visualizzazione in orizzontale (Landscape). Tocca qualsiasi casella per i dettagli del turno.</p>', unsafe_allow_html=True)

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

# Barra Navigazione Temporale Ibrida (Pulsanti + Datepicker)
st.write("---")
nav1, nav2, nav3, nav4 = st.columns([1, 1, 1, 2])

def set_new_date(new_date: datetime.date):
    st.session_state.current_date = new_date
    st.session_state.date_selector = new_date

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
        set_new_date(datetime.date(year, month, target_day))
    else:
        delta = datetime.timedelta(weeks=direction * num_weeks)
        set_new_date(d + delta)

with nav1:
    if st.button("◀ Precedente", use_container_width=True):
        advance_date(-1)
        st.rerun()

with nav2:
    if st.button("Oggi", use_container_width=True):
        set_new_date(datetime.date.today())
        st.rerun()

with nav3:
    if st.button("Successivo ▶", use_container_width=True):
        advance_date(1)
        st.rerun()

with nav4:
    st.date_input(
        "Vai direttamente a data:",
        key="date_selector",
        on_change=on_date_picker_change,
        label_visibility="collapsed"
    )

# Calcolo delle date da visualizzare
curr = st.session_state.current_date
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

# Generazione della tabella HTML orizzontale a nastro
html_table = ['<div style="overflow-x: auto; -webkit-overflow-scrolling: touch;"><table class="matrix-table">']

# Riga Intestazione 1: Numero Giorno
html_table.append('<thead><tr><th class="crew-label-cell">Giorno</th>')
day_names_it = ["lu", "ma", "me", "gi", "ve", "sa", "do"]

for d in dates_to_show:
    is_hol, is_semi, h_name = get_holiday_type(d)
    th_class = "th-normal"
    if is_hol:
        th_class = "th-holiday"
    elif is_semi:
        th_class = "th-semiholiday"
    title_attr = f'title="{h_name}"' if h_name else ''
    html_table.append(f'<th class="{th_class}" {title_attr}><span class="header-day-num">{d.strftime("%d")}</span></th>')
html_table.append('</tr>')

# Riga Intestazione 2: Nome Giorno abbreviato
html_table.append('<tr><th class="crew-label-cell">Eq.</th>')
for d in dates_to_show:
    is_hol, is_semi, _ = get_holiday_type(d)
    th_class = "th-normal"
    if is_hol:
        th_class = "th-holiday"
    elif is_semi:
        th_class = "th-semiholiday"
    day_name = day_names_it[d.weekday()]
    html_table.append(f'<th class="{th_class}"><span class="header-day-name">{day_name}</span></th>')
html_table.append('</tr></thead><tbody>')

# Righe degli equipaggi
for c_num in crews_to_render:
    html_table.append(f'<tr><td class="crew-label-cell">Eq. {c_num}</td>')
    for d in dates_to_show:
        shift = get_shift_for_crew(c_num, d)
        mezzo = shift["mezzo"]
        stato = shift["stato"]
        
        # Classificazione cella
        if stato == "L":
            cell_cls = "cell-l"
        elif stato in ["L1", "L2", "L3"]:
            cell_cls = "cell-l-disp"
        elif stato.startswith("R"):
            cell_cls = "cell-reserve"
        else:
            cell_cls = "cell-work"
            
        mezzo_html = f'<span class="mezzo-num">{mezzo}</span>' if mezzo else ''
        stato_html = f'<span class="stato-text">{stato}</span>'
        
        # Testo del tooltip / popup modale
        title_info, details_info = build_cell_info(c_num, d, mezzo, stato)
        # Escape per JavaScript inline
        clean_title = title_info.replace("'", "\\'")
        clean_details = details_info.replace("\n", "\\n").replace("'", "\\'")
        onclick_attr = f"onclick=\"showShiftInfo('{clean_title}', '{clean_details}')\""
        
        html_table.append(
            f'<td class="{cell_cls} clickable-cell" title="{details_info}" {onclick_attr}>'
            f'<div class="cell-content">{mezzo_html}{stato_html}</div>'
            f'</td>'
        )
    html_table.append('</tr>')

html_table.append('</tbody></table></div>')

st.markdown("".join(html_table), unsafe_allow_html=True)

# Legenda a fondo pagina
leg1, leg2, leg3, leg4, leg5 = st.columns(5)
with leg1:
    st.markdown("🔴 **Festivo / Dom**")
with leg2:
    st.markdown("🟠 **Semifestivo**")
with leg3:
    st.markdown("🟢 **Riposo (L)**")
with leg4:
    st.markdown("🟡 **Disp. (L1-3)**")
with leg5:
    st.markdown("⚪ **Riserva (R)**")
