import streamlit as st
import datetime
import calendar
import os
import pandas as pd
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
from timesheet import generate_monthly_timesheet_pdf, generate_monthly_timesheet_excel
from schedule_pdf import generate_schedule_bn_pdf, generate_annual_schedule_pdf
from tracker import log_page_view, log_download, get_analytics_summary

st.set_page_config(page_title="Proiezione turno Tripmare", layout="wide")

# Registrazione silenziosa dell'accesso alla pagina
log_page_view()

# Caricamento dello stile esterno
if os.path.exists("style.css"):
    with open("style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

query_params = st.query_params
debug_mode = query_params.get("debug", "").lower() in ["true", "1", "yes"]

# Controllo chiave segreta per l'accesso riservato alla dashboard statistiche
url_key = query_params.get("key", "")
stats_mode = url_key in ["aksgw8e574", "aksgw8e574%$", "aksgw8e574%25$"]

MESI_ITALIANO = [
    "", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
]

MESI_BREVI_ITALIANO = [
    "", "gen", "feb", "mar", "apr", "mag", "giu",
    "lug", "ago", "set", "ott", "nov", "dic"
]

# =========================================================================
# DASHBOARD STATISTICHE RISERVATA (Attiva solo con ?key=aksgw8e574)
# =========================================================================
if stats_mode:
    with st.expander("📊 DASHBOARD STATISTICHE E DOWNLOAD (Firestore)", expanded=True):
        summary = get_analytics_summary()
        if not summary.get("connected", False):
            st.error(f"Impossibile collegarsi a Firebase Firestore: {summary.get('error', 'Credenziali non trovate')}")
        else:
            col_s1, col_s2, col_s3 = st.columns(3)
            col_s1.metric("Visite Totali Registrate", summary.get("tot_visite", 0))
            col_s2.metric("Download Eseguiti", summary.get("tot_download", 0))

            recenti = summary.get("recent_events", [])
            last_date = recenti[0]["Data/Ora (UTC)"] if recenti else "Nessuna attività"
            col_s3.metric("Ultima Attività", last_date)

            st.write("---")
            c_tipi, c_crew = st.columns(2)

            with c_tipi:
                st.markdown("##### 📁 Ripartizione Download per File")
                tipi = summary.get("tipi_download", {})
                if tipi:
                    label_map = {
                        "pdf_presenze": "Foglio Presenze (PDF)",
                        "excel_presenze": "Foglio Presenze (Excel)",
                        "calendario_ics": "Calendario (.ics)",
                        "pdf_turno_bn": "Turno Stampa (PDF B/N)",
                        "pdf_turno_colori": "Turno Stampa (PDF Colori)",
                        "pdf_turno_annuale_bn": "Turno Annuale (PDF B/N)",
                        "pdf_turno_annuale_colori": "Turno Annuale (PDF Colori)",
                    }
                    df_tipi = pd.DataFrame([
                        {"Tipo File": label_map.get(k, k), "Download": v}
                        for k, v in tipi.items()
                    ])
                    st.dataframe(df_tipi, use_container_width=True, hide_index=True)
                else:
                    st.info("Nessun download ancora registrato.")

            with c_crew:
                st.markdown("##### ⚓ Equipaggi più Attivi")
                crews_st = summary.get("crews_stats", {})
                if crews_st:
                    df_crews = pd.DataFrame([
                        {"Equipaggio": k, "Conteggio": v}
                        for k, v in sorted(crews_st.items(), key=lambda x: x[1], reverse=True)
                    ])
                    st.dataframe(df_crews, use_container_width=True, hide_index=True)
                else:
                    st.info("Nessun dato per equipaggio disponibile.")

            if recenti:
                st.write("---")
                st.markdown("##### ⏱️ Ultimi 20 Eventi Registrati")
                st.dataframe(pd.DataFrame(recenti), use_container_width=True, hide_index=True)

def build_cell_tooltip(crew_num: int, target_date: datetime.date, mezzo: int, stato: str) -> str:
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

if "current_date" not in st.session_state:
    st.session_state.current_date = datetime.date.today()

st.title("⚓ Proiezione turno Tripmare")
st.warning("⚠️ **Lavori in corso**: stiamo aggiornando alcune funzioni. L'applicazione potrebbe essere temporaneamente instabile. Il banner verrà rimosso a fine lavori.")
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
    period_label = f"Mese di {MESI_ITALIANO[month]} {year}"
    st.markdown(f"### Mese di **{MESI_ITALIANO[month]} {year}**")
else:
    start_monday = curr - datetime.timedelta(days=curr.weekday())
    total_days = num_weeks * 7
    dates_to_show = [start_monday + datetime.timedelta(days=i) for i in range(total_days)]
    period_label = f"{num_weeks} Settimane (dal {dates_to_show[0].strftime('%d/%m/%Y')} al {dates_to_show[-1].strftime('%d/%m/%Y')})"
    st.markdown(f"### Visualizzazione **{num_weeks} Settimana/e** (dal {dates_to_show[0].strftime('%d/%m/%Y')} al {dates_to_show[-1].strftime('%d/%m/%Y')})")

validation_report = validate_schedule_period(dates_to_show)

if not validation_report["is_valid"]:
    st.error(
        "⚠️ **Attenzione: Rilevata anomalia nel calcolo del turno per il periodo selezionato. "
        "I dati visualizzati potrebbero non essere affidabili. Si prega cortesemente di contattare l'amministratore (Stefano).**"
    )

# Determinazione della lista equipaggi
if view_type == "Equipaggio Specifico":
    crews_to_render = [selected_crew]
    title_pdf = f"Equipaggio {selected_crew} - {period_label}"
elif view_type == "Terzina":
    start_c = (terzina_choice - 1) * 3 + 1
    crews_to_render = [start_c, start_c + 1, start_c + 2]
    title_pdf = f"Terzina {terzina_choice} (Eq. {start_c}-{start_c+1}-{start_c+2}) - {period_label}"
else:
    crews_to_render = list(range(1, 22))
    title_pdf = f"Tutti i 21 Equipaggi - {period_label}"

# ---------------------------------------------------------
# SEZIONE STAMPA TURNO (Colore vs B/N e Mese vs Anno)
# ---------------------------------------------------------
col_style, col_btn_month, col_btn_year = st.columns([1.5, 1.5, 1.5])
with col_style:
    print_style = st.radio(
        "Stile di stampa (PDF):",
        options=["🖨️ Bianco e Nero (Carta)", "🎨 A Colori (Digitale)"],
        index=0,
        horizontal=True
    )
    is_color = "A Colori" in print_style
    style_suffix = "Colori" if is_color else "BN"
    tracker_prefix = "pdf_turno_colori" if is_color else "pdf_turno_bn"
    tracker_annual = "pdf_turno_annuale_colori" if is_color else "pdf_turno_annuale_bn"

with col_btn_month:
    try:
        schedule_pdf_data = generate_schedule_bn_pdf(dates_to_show, crews_to_render, title_pdf, is_color)
        clean_file_label = period_label.replace(" ", "_").replace("/", "-")
        pdf_name_schedule = f"Turno_Tripmare_{clean_file_label}_{style_suffix}.pdf"
        
        st.download_button(
            label="📄 Scarica Turno Visualizzato (1 Pagina)",
            data=schedule_pdf_data,
            file_name=pdf_name_schedule,
            mime="application/pdf",
            use_container_width=True,
            on_click=log_download,
            args=(tracker_prefix, title_pdf)
        )
    except Exception as e:
        st.error(f"Errore stampa turno mensile: {e}")

with col_btn_year:
    btn_year_label = f"📅 Scarica Intero Anno {curr.year} (12 Pagine)"
    try:
        annual_pdf_data = generate_annual_schedule_pdf(curr.year, crews_to_render, is_color)
        pdf_name_annual = f"Turno_Tripmare_Anno_{curr.year}_{style_suffix}.pdf"
        
        st.download_button(
            label=btn_year_label,
            data=annual_pdf_data,
            file_name=pdf_name_annual,
            mime="application/pdf",
            use_container_width=True,
            on_click=log_download,
            args=(tracker_annual, f"Anno intero {curr.year}")
        )
    except Exception as e:
        st.error(f"Errore stampa turno annuale: {e}")

# ---------------------------------------------------------
# GENERAZIONE TABELLA HTML A VIDEO
# ---------------------------------------------------------
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

if validation_report["is_valid"]:
    st.markdown(
        '<div class="integrity-ok-badge">✅ Integrità del turno verificata (21 equipaggi conformi)</div>',
        unsafe_allow_html=True
    )

# Sezione Esportazioni per Equipaggio Specifico
if view_type == "Equipaggio Specifico":
    st.write("---")
    st.markdown("### 📥 Esportazione e Sincronizzazione (Equipaggio Specifico)")

    col_exp_1, col_exp_2 = st.columns(2)

    with col_exp_1:
        st.markdown("##### 📅 Sincronizzazione Smartphone (.ics)")
        ics_data = generate_ics_calendar(selected_crew, dates_to_show)
        file_suffix = f"{dates_to_show[0].strftime('%Y_%m')}" if time_horizon == "Mese Completo" else f"{dates_to_show[0].strftime('%Y_%m_%d')}"
        ics_filename = f"turno_tripmare_eq{selected_crew}_{file_suffix}.ics"

        st.download_button(
            label=f"Scarica Calendario (.ics) - Eq. {selected_crew}",
            data=ics_data,
            file_name=ics_filename,
            mime="text/calendar",
            use_container_width=True,
            on_click=log_download,
            args=("calendario_ics", f"Eq. {selected_crew} - {file_suffix}")
        )
        st.caption("Consiglio: importalo come calendario secondario su Google Calendar / Apple Calendar per accenderlo o spegnerlo a piacere.")

    with col_exp_2:
        st.markdown("##### 📄 Foglio Presenze Mensile")

        btn_c1, btn_c2 = st.columns(2)

        try:
            pdf_data = generate_monthly_timesheet_pdf(curr.year, curr.month, selected_crew)
            pdf_name = f"presenze_tripmare_eq{selected_crew}_{curr.year}_{curr.month:02d}.pdf"
            with btn_c1:
                st.download_button(
                    label="📄 Scarica PDF (A4 Stampa)",
                    data=pdf_data,
                    file_name=pdf_name,
                    mime="application/pdf",
                    use_container_width=True,
                    on_click=log_download,
                    args=("pdf_presenze", f"Eq. {selected_crew} - {curr.year}_{curr.month:02d}")
                )
        except Exception as e:
            with btn_c1:
                st.error(f"Errore generazione PDF: {e}")

        try:
            excel_data = generate_monthly_timesheet_excel(curr.year, curr.month, selected_crew)
            excel_name = f"presenze_tripmare_eq{selected_crew}_{curr.year}_{curr.month:02d}.xlsx"
            with btn_c2:
                st.download_button(
                    label="📊 Scarica Excel (.xlsx)",
                    data=excel_data,
                    file_name=excel_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    on_click=log_download,
                    args=("excel_presenze", f"Eq. {selected_crew} - {curr.year}_{curr.month:02d}")
                )
        except Exception as e:
            with btn_c2:
                st.error(f"Errore generazione Excel: {e}")

        st.caption("Modulo precompilato (PDF vettoriale o foglio Excel con formule di somma) con turni solari, indennità e maggiorazioni.")

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

render_documentation_section()
render_faq_section()
