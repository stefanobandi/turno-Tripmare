import streamlit as st
import datetime
import calendar
from engine import get_week_index, get_shift_for_crew, get_holiday_type

st.set_page_config(page_title="Turni Rimorchiatori", layout="wide")

# CSS personalizzato per la matrice orizzontale a nastro
st.markdown("""
<style>
    .matrix-table {
        width: 100%;
        border-collapse: collapse;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        margin-top: 15px;
        margin-bottom: 25px;
    }
    .matrix-table th, .matrix-table td {
        border: 1px solid #c0c0c0;
        text-align: center;
        padding: 4px 2px;
        min-width: 42px;
    }
    .header-day-num {
        font-size: 13px;
        font-weight: bold;
    }
    .header-day-name {
        font-size: 11px;
        text-transform: uppercase;
    }
    .th-normal {
        background-color: #f0f2f6;
        color: #1f2937;
    }
    .th-holiday {
        background-color: #d32f2f !important;
        color: #ffffff !important;
    }
    .th-semiholiday {
        background-color: #ffcdd2 !important;
        color: #b71c1c !important;
    }
    .crew-label-cell {
        background-color: #1e293b;
        color: #ffffff;
        font-weight: bold;
        font-size: 13px;
        position: sticky;
        left: 0;
        z-index: 2;
        min-width: 90px;
    }
    .cell-content {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 48px;
        font-size: 11px;
    }
    .mezzo-num {
        font-weight: 800;
        font-size: 13px;
        color: #0284c7;
        line-height: 1.1;
    }
    .stato-text {
        font-weight: 600;
        font-size: 11px;
        line-height: 1.1;
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
</style>
""", unsafe_allow_html=True)

# Inizializzazione session_state per navigazione
if "current_date" not in st.session_state:
    st.session_state.current_date = datetime.date.today()

# Header e Controlli Superiori
st.title("⚓ Gestione e Proiezione Turni Equipaggi")

c1, c2, c3, c4 = st.columns([1.5, 1.2, 1.2, 1.5])

with c1:
    view_type = st.selectbox(
        "Modalità Visualizzazione",
        options=["Equipaggio Specifico", "Terzina", "Tutti gli Equipaggi"],
        index=0
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
        num_weeks = None

# Barra di Navigazione Temporale Ibrida (Pulsanti + Datepicker)
st.write("---")
nav1, nav2, nav3, nav4 = st.columns([1, 1, 1, 2])

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
        st.session_state.current_date = datetime.date(year, month, 1)
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

with nav4:
    picker_date = st.date_input(
        "Vai direttamente a data:",
        value=st.session_state.current_date,
        key="date_selector",
        label_visibility="collapsed"
    )
    if picker_date != st.session_state.current_date:
        st.session_state.current_date = picker_date
        st.rerun()

# Calcolo delle date da visualizzare
curr = st.session_state.current_date
dates_to_show = []

if time_horizon == "Mese Completo":
    year = curr.year
    month = curr.month
    _, num_days = calendar.monthrange(year, month)
    dates_to_show = [datetime.date(year, month, day) for day in range(1, num_days + 1)]
    st.markdown(f"### Mese di **{calendar.month_name[month].capitalize()} {year}**")
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
html_table = ['<div style="overflow-x: auto;"><table class="matrix-table">']

# Riga Intestazione 1: Numero Giorno
html_table.append('<thead><tr><th class="crew-label-cell" style="top:0;">Giorno</th>')
day_names_it = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]

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

# Riga Intestazione 2: Nome Giorno
html_table.append('<tr><th class="crew-label-cell" style="top:0;">Equipaggio</th>')
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
        
        # Scelta stile cella
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
        
        html_table.append(f'<td class="{cell_cls}"><div class="cell-content">{mezzo_html}{stato_html}</div></td>')
    html_table.append('</tr>')

html_table.append('</tbody></table></div>')

st.markdown("".join(html_table), unsafe_allow_html=True)

# Legenda di supporto a fondo pagina
leg1, leg2, leg3, leg4, leg5 = st.columns(5)
with leg1:
    st.markdown("🔴 **Festivo / Domenica**: Rosso")
with leg2:
    st.markdown("🟠 **Semifestivo**: Salmone")
with leg3:
    st.markdown("🟢 **Riposo (L)**: Verde")
with leg4:
    st.markdown("🟡 **Disponibilità (L1/L2/L3)**: Giallo")
with leg5:
    st.markdown("⚪ **Riserva (R1/R2/R3)**: Grigio")
