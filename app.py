import streamlit as st
import datetime
import calendar
import os
from engine import (
    get_week_index,
    get_shift_for_crew,
    get_holiday_type,
    validate_day_integrity,
    validate_schedule_period,
    generate_ics_calendar,
    ANCHOR_DATE
)
from faq import render_documentation_section, render_faq_section
from timesheet import generate_monthly_timesheet_pdf, find_template_path

st.set_page_config(page_title="Proiezione turno Tripmare", layout="wide")

# Caricamento del foglio di stile esterno (style.css)
if os.path.exists("style.css"):
    with open("style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Controllo parametro debug nell'URL (?debug=true)
query_params = st.query_params
debug_mode = query_params.get("debug", "").lower() in ["true", "1", "yes"]

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
    lines = [f"EQ{crew_num} - {date_formatted}"]

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
        selected_crew = st.selectbox(
            "Seleziona Equipaggio",
            options=list(range(1, 22)),
            index=7,
            format_func=lambda x: f"Equipaggio {x} 🎱" if x == 8 else f"Equipaggio {x}"
        )
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
    st.markdown(f"### Mese di **{MESI_ITALIANO[month]} {year}**")
else:
    start_monday = curr - datetime.timedelta(days=curr.weekday())
    total_days = num_weeks * 7
    dates_to_show = [start_monday + datetime.timedelta(days=i) for i in range(total_days)]
    st.markdown(f"### Visualizzazione **{num_weeks} Settimana/e** (dal {dates_to_show[0].strftime('%d/%m/%Y')} al {dates_to_show[-1].strftime('%d/%m/%Y')})")

# Validazione di integrità del periodo corrente
validation_report = validate_schedule_period(dates_to_show)

if not validation_report["is_valid"]:
    st.error(
        "⚠️ **Attenzione: Rilevata anomalia nel calcolo del turno per il periodo selezionato. "
        "I dati visualizzati potrebbero non essere affidabili. Si prega cortesemente di contattare l'amministratore (Stefano).**"
    )

# Pannello Riservato Debug Mode (visibile solo con ?debug=true nell'URL)
if debug_mode:
    with st.expander("🛠️ PANNELLO DIAGNOSTICO SVILUPPATORE (Debug Mode Attivo)", expanded=True):
        st.write("### Parametri di Ancoraggio e Sfasamento Temporale")
        target_ref = dates_to_show[0]
        target_monday = target_ref - datetime.timedelta(days=target_ref.weekday())
        delta_days = (target_monday - ANCHOR_DATE).days
        delta_weeks = delta_days // 7
        curr_week_idx = delta_weeks % 21

        d_col1, d_col2, d_col3, d_col4 = st.columns(4)
        d_col1.metric("Data Ancora Master", ANCHOR_DATE.strftime("%d/%m/%Y"))
        d_col2.metric("Delta Giorni", f"{delta_days} gg")
        d_col3.metric("Delta Settimane", f"{delta_weeks} sett")
        d_col4.metric("Indice Settimana (mod 21)", f"Settimana {curr_week_idx + 1} (idx {curr_week_idx})")

        st.write("---")
        st.write("### Verifica Integrità Periodo Visualizzato")
        if validation_report["is_valid"]:
            st.success(f"✅ Quadratura verificata al 100% per tutti i {validation_report['total_days']} giorni del periodo selezionato.")
        else:
            st.error(f"❌ Rilevate {validation_report['invalid_count']} giornate non conformi su {validation_report['total_days']} giorni.")
            for inv in validation_report["invalid_days"]:
                st.write(f"**Data {inv['date'].strftime('%d/%m/%Y')}**: {', '.join(inv['errors'])}")

        st.write("---")
        st.write("### Test Ciclo Master Completo (147 giorni continui)")
        master_dates = [ANCHOR_DATE + datetime.timedelta(days=i) for i in range(21 * 7)]
        master_report = validate_schedule_period(master_dates)
        if master_report["is_valid"]:
            st.success("✅ Il ciclo master di 21 settimane (147 giorni) rispetta integralmente tutti i vincoli operativi (4-4-4-3-1-1-1-1-1-1).")
        else:
            st.error(f"❌ Anomalie nel ciclo master su {master_report['invalid_count']} giorni.")

# Determinazione della lista equipaggi da stampare
if view_type == "Equipaggio Specifico":
    crews_to_render = [selected_crew]
elif view_type == "Terzina":
    start_c = (terzina_choice - 1) * 3 + 1
    crews_to_render = [start_c, start_c + 1, start_c + 2]
else:
    crews_to_render = list(range(1, 22))

# Generazione della tabella HTML
html_table = ['<div class="matrix-wrapper"><table class="matrix-table">']
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

for c_num in crews_to_render:
    label_text = f"Eq. {c_num} 🎱" if c_num == 8 else f"Eq. {c_num}"
    html_table.append(f'<tr><td class="crew-label-cell">{label_text}</td>')
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

# Voce di integrità del turno verificata
if validation_report["is_valid"]:
    st.markdown(
        '<div class="integrity-ok-badge">✅ Integrità del turno verificata (21 equipaggi conformi)</div>',
        unsafe_allow_html=True
    )

# Sezione Esportazioni per Equipaggio Specifico
if view_type == "Equipaggio Specifico":
    st.write("")
    
    col_export_1, col_export_2 = st.columns(2)

    with col_export_1:
        st.markdown("##### 📅 Sincronizzazione Smartphone")
        ics_data = generate_ics_calendar(selected_crew, dates_to_show)
        file_suffix = f"{dates_to_show[0].strftime('%Y_%m')}" if time_horizon == "Mese Completo" else f"{dates_to_show[0].strftime('%Y_%m_%d')}"
        ics_filename = f"turno_tripmare_eq{selected_crew}_{file_suffix}.ics"
        
        st.download_button(
            label=f"Scarica Calendario (.ics) - Eq. {selected_crew}",
            data=ics_data,
            file_name=ics_filename,
            mime="text/calendar",
            use_container_width=True
        )
        st.caption("Consiglio: importalo come calendario secondario per accenderlo/spegnerlo o cancellarlo con un clic.")

    with col_export_2:
        st.markdown("##### 📄 Foglio Presenze Aziendale (Work in progress)")
        template_file = find_template_path()
        if template_file:
            try:
                timesheet_pdf_data = generate_monthly_timesheet_pdf(curr.year, curr.month, selected_crew)
                pdf_filename = f"presenze_tripmare_eq{selected_crew}_{curr.year}_{curr.month:02d}.pdf"
                st.download_button(
                    label=f"Scarica Modulo PDF - Eq. {selected_crew} ({MESI_ITALIANO[curr.month]} {curr.year})",
                    data=timesheet_pdf_data,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    use_container_width=True
                )
                st.caption("Modulo precompilato pronto per la stampa in B/N con indennità, maggiorazioni, festivi e buoni pasto.")
            except Exception as e:
                st.error(f"Errore durante la compilazione del PDF: {e}")
        else:
            st.button("Scarica Modulo PDF (Template non trovato)", disabled=True, use_container_width=True, help="Carica il file 'straordinario ed extra tripmare.pdf' nel repository.")
            st.caption("Carica il file 'straordinario ed extra tripmare.pdf' nel repository per attivare la stampa.")

# Box Legenda
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

# Render Sezioni Documenti e FAQ
render_documentation_section()
render_faq_section()
