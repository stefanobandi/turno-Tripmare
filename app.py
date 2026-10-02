import streamlit as st
import datetime
import calendar
from engine import get_week_index, get_shift_for_crew, ANCHOR_DATE

st.set_page_config(page_title="Turni Equipaggi Rimorchiatori", layout="wide")

st.title("⚓ Previsione Turni Marittimi")

col1, col2 = st.columns([1, 2])

with col1:
    crew = st.selectbox("Seleziona Equipaggio", options=list(range(1, 22)), index=7)
    query_date = st.date_input("Seleziona Data", value=datetime.date(2026, 1, 12))
    
    week_num = get_week_index(query_date) + 1
    st.info(f"Settimana del ciclo: **{week_num} / 21**")

    shift = get_shift_for_crew(crew, query_date)
    st.subheader(f"Stato per il {query_date.strftime('%d/%m/%Y')}")
    if shift["mezzo"]:
        st.write(f"**Mezzo**: Rimorchiatore {shift['mezzo']}")
    st.write(f"**Turno / Stato**: {shift['stato']}")

with col2:
    st.subheader("Vista Mensile")
    year = query_date.year
    month = query_date.month
    
    num_days = calendar.monthrange(year, month)[1]
    
    # Costruzione tabella mensile
    month_data = []
    for day in range(1, num_days + 1):
        d = datetime.date(year, month, day)
        s = get_shift_for_crew(crew, d)
        month_data.append({
            "Giorno": d.strftime("%a %d"),
            "Mezzo": s["mezzo"] if s["mezzo"] else "-",
            "Stato": s["stato"]
        })
    
    st.table(month_data)
