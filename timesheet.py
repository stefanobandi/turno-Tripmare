import io
import calendar
import datetime
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from reportlab.pdfgen import canvas
from engine import get_shift_for_crew, get_holiday_type

MESI_MAIUSCOLO = [
    "", "GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO",
    "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"
]

GIORNI_SETT_LETTERE = ["L", "M", "M", "G", "V", "S", "D"]

def get_month_crew_data(year: int, month: int, crew_num: int) -> dict:
    """
    Calcola per ciascun giorno del mese (1..31) i valori teorici standard del turno.
    """
    _, num_days = calendar.monthrange(year, month)
    days_data = {}

    tot_notturna = 0
    tot_navigazione = 0
    tot_festivo = 0
    tot_buoni_pasto = 0

    for day in range(1, 32):
        if day > num_days:
            days_data[day] = {"exists": False}
            continue

        target_date = datetime.date(year, month, day)
        shift = get_shift_for_crew(crew_num, target_date)
        is_hol, _, _ = get_holiday_type(target_date)
        stato = shift.get("stato", "")
        giorno_lett = GIORNI_SETT_LETTERE[target_date.weekday()]

        eq_str = ""
        is_riserva = False
        if stato.startswith("R"):
            is_riserva = True
            eq_str = "R"
        elif stato in ["20", "08", "08:20"]:
            eq_str = str(crew_num)

        dalle_str = ""
        alle_str = ""
        v_nott = None
        v_nav = None
        v_fest = None
        v_buono = None

        if stato == "20":
            dalle_str = "20"
            alle_str = "24"
            v_nott = 4
            v_nav = 4
            v_buono = 1
            if is_hol:
                v_fest = 1
        elif stato == "08":
            dalle_str = "00"
            alle_str = "08"
            v_nott = 6
            v_nav = 8
            v_buono = 1
            if is_hol:
                v_fest = 1
        elif stato == "08:20":
            dalle_str = "08"
            alle_str = "20"
            v_nav = 12
            v_buono = 1
            if is_hol:
                v_fest = 1

        if v_nott:
            tot_notturna += v_nott
        if v_nav:
            tot_navigazione += v_nav
        if v_fest:
            tot_festivo += v_fest
        if v_buono:
            tot_buoni_pasto += v_buono

        days_data[day] = {
            "exists": True,
            "giorno_lett": giorno_lett,
            "is_holiday": is_hol,
            "is_riserva": is_riserva,
            "equipaggio": eq_str,
            "dalle": dalle_str,
            "alle": alle_str,
            "notturna": v_nott,
            "navigazione": v_nav,
            "festivo": v_fest,
            "buoni_pasto": v_buono
        }

    return {
        "year": year,
        "month": month,
        "crew_num": crew_num,
        "num_days": num_days,
        "days": days_data,
        "tot_notturna": tot_notturna,
        "tot_navigazione": tot_navigazione,
        "tot_festivo": tot_festivo,
        "tot_buoni_pasto": tot_buoni_pasto
    }


def generate_monthly_timesheet_pdf(year: int, month: int, crew_num: int) -> bytes:
    """
    Genera il foglio presenze mensile in PDF vettoriale A4 Landscape nativo (842 x 595 pt),
    con fedeltà geometrica al modulo originale Tripmare.
    """
    PAGE_W = 841.89
    PAGE_H = 595.28

    data = get_month_crew_data(year, month, crew_num)
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(PAGE_W, PAGE_H))

    # Margini pagina A4 Landscape
    MARGIN_LEFT = 26.0
    MARGIN_RIGHT = PAGE_W - 26.0
    TABLE_W = MARGIN_RIGHT - MARGIN_LEFT

    LABEL_COL_W = 166.0
    TOTAL_COL_W = 28.0
    GRID_DAYS_W = TABLE_W - LABEL_COL_W - TOTAL_COL_W
    DAY_COL_W = GRID_DAYS_W / 31.0

    X_LABEL_START = MARGIN_LEFT
    X_DAYS_START = MARGIN_LEFT + LABEL_COL_W
    X_TOTAL_START = MARGIN_RIGHT - TOTAL_COL_W

    X_SUB_NUM = X_LABEL_START + 16.0
    X_SUB_QUAL = X_SUB_NUM + 26.0
    X_SUB_ORARIO = X_DAYS_START - 36.0

    def get_cx(d: int) -> float:
        return X_DAYS_START + (d - 1) * DAY_COL_W + (DAY_COL_W / 2.0)

    # Coordinate verticali
    Y_TABLE_TOP = PAGE_H - 24.0

    H_TOP_HEADER = 21.0     # Riga Mese, Cognome, Nome, Codice
    H_ROW_NUM_DAYS = 13.0   # Riga Anno + Numeri 1..31
    H_ROW_WEEKDAY = 13.0    # giorno della settimana
    H_ROW_CREW = 13.0       # Equipaggio
    H_ROW_DALLE = 12.0      # Dalle
    H_ROW_ALLE = 12.0       # Alle
    H_ROW_ITEM = 12.0       # Righe voci 1..17
    H_ROW_CAPO_COG = 14.0   # Cognome del Capo Servizio
    H_ROW_CAPO_FIRMA = 38.0 # Firma del Capo Servizio (riga alta per la firma autografa)

    items_def = [
        ("STR_1", "1", "Diu. Feriale"),
        ("STR_2", "2", "Nott. Fer./ Diu. Festivo"),
        ("STR_3", "3", "Nott. Festivo"),
        ("VOCE_4", "4", "Servizi Prolungati"),
        ("VOCE_5", "5", "Maggiorazione Notturna"),
        ("VOCE_6", "6", "Indennità Navigazione"),
        ("VOCE_7", "7", "Indennità Sostitutiva"),
        ("VOCE_8", "8", "Festivo"),
        ("VOCE_9", "9", "Lavori non rientranti"),
        ("VOCE_10", "10", "Passaggio"),
        ("VOCE_11", "11", "Diurno"),
        ("VOCE_12", "12", "Notturno"),
        ("VOCE_13", "13", "Compensativo/i Maturato/i"),
        ("VOCE_14", "14", "Reperibilità (solo 8-20 00-08)"),
        ("VOCE_15", "15", "Buoni pasto"),
        ("VOCE_16", "16", "Ore Sciopero"),
        ("VOCE_17", "17", ""),
        ("CAPO_COG", "", "Cognome del Capo Servizio"),
        ("CAPO_FIRMA", "", "Firma del Capo Servizio")
    ]

    y_top_header = Y_TABLE_TOP
    y_num_days = y_top_header - H_TOP_HEADER
    y_weekday = y_num_days - H_ROW_NUM_DAYS
    y_crew = y_weekday - H_ROW_WEEKDAY
    y_dalle = y_crew - H_ROW_CREW
    y_alle = y_dalle - H_ROW_DALLE
    y_items_start = y_alle - H_ROW_ALLE

    item_rows_coords = []
    curr_y = y_items_start
    for code, num_str, desc_str in items_def:
        h = H_ROW_CAPO_FIRMA if code == "CAPO_FIRMA" else (H_ROW_CAPO_COG if code == "CAPO_COG" else H_ROW_ITEM)
        y_top = curr_y
        y_bot = curr_y - h
        item_rows_coords.append((code, num_str, desc_str, y_top, y_bot))
        curr_y = y_bot

    Y_TABLE_BOTTOM = curr_y

    # =========================================================================
    # 1. TESTATA SUPERIORE (Mese, Cognome, Nome, Codice)
    # =========================================================================
    x_h_cognome = X_DAYS_START
    x_h_nome = x_h_cognome + 240.0
    x_h_codice = x_h_nome + 225.0

    c.setLineWidth(0.6)
    c.line(x_h_cognome, y_num_days, x_h_cognome, y_top_header)
    c.line(x_h_nome, y_num_days, x_h_nome, y_top_header)
    c.line(x_h_codice, y_num_days, x_h_codice, y_top_header)

    c.setFont("Helvetica-Bold", 12.0)
    c.drawCentredString(MARGIN_LEFT + LABEL_COL_W / 2.0, y_num_days + 6.5, "Mese")

    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(x_h_cognome + 8.0, y_num_days + 6.0, "Cognome")
    c.drawString(x_h_nome + 8.0, y_num_days + 6.0, "Nome")
    c.drawString(x_h_codice + 8.0, y_num_days + 6.0, "Codice")

    # =========================================================================
    # 2. LINEE ORIZZONTALI E BORDATURE
    # =========================================================================
    c.setLineWidth(1.4)
    c.line(MARGIN_LEFT, y_num_days, MARGIN_RIGHT, y_num_days)

    c.setLineWidth(0.5)
    c.line(MARGIN_LEFT, y_weekday, MARGIN_RIGHT, y_weekday)
    c.line(MARGIN_LEFT, y_crew, MARGIN_RIGHT, y_crew)

    # Sotto Equipaggio / sopra Orario di servizio
    c.setLineWidth(1.4)
    c.line(MARGIN_LEFT, y_dalle, MARGIN_RIGHT, y_dalle)

    # Linea sottile tra Dalle e Alle (salta la colonna Tot. che è unita)
    c.setLineWidth(0.5)
    c.line(X_SUB_ORARIO, y_alle, X_TOTAL_START, y_alle)

    # Sotto Alle (separa orari da straordinari)
    c.setLineWidth(1.4)
    c.line(MARGIN_LEFT, y_items_start, MARGIN_RIGHT, y_items_start)

    # Linee orizzontali del blocco voci 1..17
    for code, _, _, _, y_b in item_rows_coords:
        if code in ["STR_1", "STR_2"]:
            c.setLineWidth(0.5)
            c.line(MARGIN_LEFT, y_b, X_SUB_NUM, y_b)
            c.line(X_SUB_QUAL, y_b, MARGIN_RIGHT, y_b)
        elif code == "VOCE_11":
            # Per riga 11, la linea orizzontale salta la colonna 'Risc.' (mergiata tra 11 e 12)
            c.setLineWidth(0.5)
            c.line(MARGIN_LEFT, y_b, X_SUB_NUM, y_b)
            c.line(X_SUB_QUAL, y_b, MARGIN_RIGHT, y_b)
        elif code == "STR_3":
            c.setLineWidth(0.5)
            c.line(MARGIN_LEFT, y_b, MARGIN_RIGHT, y_b)
        elif code == "VOCE_17":
            c.setLineWidth(1.4)
            c.line(MARGIN_LEFT, y_b, MARGIN_RIGHT, y_b)
        elif code == "CAPO_FIRMA":
            pass
        else:
            c.setLineWidth(0.5)
            c.line(MARGIN_LEFT, y_b, MARGIN_RIGHT, y_b)

    # =========================================================================
    # 3. ETICHETTE E ALLINEAMENTI DELLA COLONNA SINISTRA
    # =========================================================================
    # Nome del mese a fianco dell'anno
    c.setFont("Helvetica-Bold", 10.0)
    c.drawCentredString(MARGIN_LEFT + (X_SUB_ORARIO - MARGIN_LEFT) / 2.0, y_num_days - 9.5, MESI_MAIUSCOLO[month])

    # Casellina dell'Anno (sopra Dalle/Alle)
    c.setLineWidth(0.6)
    c.line(X_SUB_ORARIO, y_num_days, X_SUB_ORARIO, y_weekday)
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(X_SUB_ORARIO + (X_DAYS_START - X_SUB_ORARIO) / 2.0, y_num_days - 9.5, str(year))

    # "giorno della settimana" ed "Equipaggio"
    c.setFont("Helvetica", 8.0)
    c.drawCentredString(MARGIN_LEFT + LABEL_COL_W / 2.0, y_weekday - 9.5, "giorno della settimana")
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(MARGIN_LEFT + LABEL_COL_W / 2.0, y_crew - 9.5, "Equipaggio")

    # "Orario di servizio" centrato
    c.setLineWidth(0.6)
    c.line(X_SUB_ORARIO, y_dalle, X_SUB_ORARIO, y_items_start)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawCentredString(MARGIN_LEFT + (X_SUB_ORARIO - MARGIN_LEFT) / 2.0, y_dalle - 15.0, "Orario di servizio")

    # "Dalle" e "Alle"
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(X_SUB_ORARIO + (X_DAYS_START - X_SUB_ORARIO) / 2.0, y_dalle - 8.5, "Dalle")
    c.drawCentredString(X_SUB_ORARIO + (X_DAYS_START - X_SUB_ORARIO) / 2.0, y_alle - 8.5, "Alle")

    # "Tot." unito verticalmente su Dalle/Alle
    c.setFont("Helvetica-Bold", 8.0)
    c.drawCentredString(X_TOTAL_START + TOTAL_COL_W / 2.0, y_dalle - 14.0, "Tot.")

    # =========================================================================
    # 4. SUDDIVISIONE SOTTOCOLONNE DELLE VOCI (1..17)
    # =========================================================================
    y_str3_bot = item_rows_coords[2][4]  # Fondo riga 3
    y_voci_bot = item_rows_coords[16][4] # Fondo riga 17

    c.setLineWidth(0.5)
    # Colonnina numeri 1..17
    c.line(X_SUB_NUM, y_items_start, X_SUB_NUM, y_voci_bot)

    # 1) Merge 3 celle per "Str." (righe 1..3)
    c.line(X_SUB_QUAL, y_items_start, X_SUB_QUAL, y_str3_bot)
    c.setFont("Helvetica-Bold", 8.0)
    c.drawCentredString(X_SUB_NUM + (X_SUB_QUAL - X_SUB_NUM) / 2.0, y_items_start - (3 * H_ROW_ITEM) / 2.0 - 2.5, "Str.")

    # 2) Merge 2 celle per "Risc." (righe 11 e 12)
    y_r11_top = item_rows_coords[10][3]
    y_r12_bot = item_rows_coords[11][4]
    c.line(X_SUB_QUAL, y_r11_top, X_SUB_QUAL, y_r12_bot)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(X_SUB_NUM + (X_SUB_QUAL - X_SUB_NUM) / 2.0, y_r11_top - H_ROW_ITEM - 2.5, "Risc.")

    # Scrittura numeri voci e descrizioni
    for code, num_str, desc_str, y_t, y_b in item_rows_coords:
        y_text = y_b + (y_t - y_b) / 2.0 - 2.5
        c.setFont("Helvetica-Bold", 7.5)
        if num_str:
            c.drawCentredString(MARGIN_LEFT + (X_SUB_NUM - MARGIN_LEFT) / 2.0, y_text, num_str)

        c.setFont("Helvetica", 6.8 if "Reperibilità" in desc_str else 7.2)
        if code in ["STR_1", "STR_2", "STR_3", "VOCE_11", "VOCE_12"]:
            x_desc = X_SUB_QUAL + 3.0
        elif num_str:
            x_desc = X_SUB_NUM + 3.0
        else:
            x_desc = MARGIN_LEFT + 4.0
        c.drawString(x_desc, y_text, desc_str)

    # =========================================================================
    # 5. LINEE VERTICALI DELLE COLONNE DEI GIORNI E BORDATURE
    # =========================================================================
    c.setLineWidth(0.4)
    for day in range(1, 31):
        x_c = X_DAYS_START + day * DAY_COL_W
        c.line(x_c, y_num_days, x_c, Y_TABLE_BOTTOM)

    c.setLineWidth(1.4)
    c.line(X_DAYS_START, y_num_days, X_DAYS_START, Y_TABLE_BOTTOM)
    c.line(X_TOTAL_START, y_num_days, X_TOTAL_START, Y_TABLE_BOTTOM)
    c.rect(MARGIN_LEFT, Y_TABLE_BOTTOM, TABLE_W, Y_TABLE_TOP - Y_TABLE_BOTTOM, stroke=1, fill=0)

    # =========================================================================
    # 6. POPOLAMENTO DATI DEL TURNO
    # =========================================================================
    days_dict = data["days"]

    for day in range(1, 32):
        d_info = days_dict[day]
        cx = get_cx(day)

        if not d_info["exists"]:
            c.setLineWidth(0.8)
            col_x1 = X_DAYS_START + (day - 1) * DAY_COL_W
            col_x2 = col_x1 + DAY_COL_W
            c.line(col_x1, y_num_days, col_x2, Y_TABLE_BOTTOM)
            continue

        c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(cx, y_num_days - 9.5, str(day))
        c.drawCentredString(cx, y_weekday - 9.5, d_info["giorno_lett"])

        if d_info["is_holiday"]:
            c.setLineWidth(0.6)
            c.ellipse(cx - 5.5, y_weekday - 12.0, cx + 5.5, y_weekday - 1.0)

        if d_info["is_riserva"]:
            c.setFont("Helvetica-Bold", 5.5)
            c.drawString(cx - 6.0, y_crew - 7.0, "R")
        elif d_info["equipaggio"]:
            c.setFont("Helvetica-Bold", 7.5)
            c.drawCentredString(cx, y_crew - 9.5, d_info["equipaggio"])

        c.setFont("Helvetica", 7.0)
        if d_info["dalle"]:
            c.drawCentredString(cx, y_dalle - 8.5, d_info["dalle"])
        if d_info["alle"]:
            c.drawCentredString(cx, y_alle - 8.5, d_info["alle"])

        for code, _, _, y_t, y_b in item_rows_coords:
            y_m = y_b + (y_t - y_b) / 2.0 - 2.5
            if code == "VOCE_5" and d_info["notturna"]:
                c.setFont("Helvetica", 7.5)
                c.drawCentredString(cx, y_m, str(d_info["notturna"]))
            elif code == "VOCE_6" and d_info["navigazione"]:
                c.setFont("Helvetica", 7.5)
                c.drawCentredString(cx, y_m, str(d_info["navigazione"]))
            elif code == "VOCE_8" and d_info["festivo"]:
                c.setFont("Helvetica", 7.5)
                c.drawCentredString(cx, y_m, str(d_info["festivo"]))
            elif code == "VOCE_15" and d_info["buoni_pasto"]:
                c.setFont("Helvetica", 7.5)
                c.drawCentredString(cx, y_m, str(d_info["buoni_pasto"]))

    # Totali colonna destra
    cx_tot = X_TOTAL_START + TOTAL_COL_W / 2.0
    c.setFont("Helvetica-Bold", 7.5)
    for code, _, _, y_t, y_b in item_rows_coords:
        y_m = y_b + (y_t - y_b) / 2.0 - 2.5
        if code == "VOCE_5" and data["tot_notturna"] > 0:
            c.drawCentredString(cx_tot, y_m, str(data["tot_notturna"]))
        elif code == "VOCE_6" and data["tot_navigazione"] > 0:
            c.drawCentredString(cx_tot, y_m, str(data["tot_navigazione"]))
        elif code == "VOCE_8" and data["tot_festivo"] > 0:
            c.drawCentredString(cx_tot, y_m, str(data["tot_festivo"]))
        elif code == "VOCE_15" and data["tot_buoni_pasto"] > 0:
            c.drawCentredString(cx_tot, y_m, str(data["tot_buoni_pasto"]))

    # =========================================================================
    # 7. TABELLA RIEPILOGO FERIE E COMPENSATIVI (A TUTTA LARGHEZZA)
    # =========================================================================
    Y_SUMMARY_TOP = Y_TABLE_BOTTOM - 6.0
    SUMMARY_W = TABLE_W
    SUMMARY_H = 36.0

    c.setLineWidth(1.0)
    c.rect(MARGIN_LEFT, Y_SUMMARY_TOP - SUMMARY_H, SUMMARY_W, SUMMARY_H, stroke=1, fill=0)

    c.setLineWidth(0.5)
    c.line(MARGIN_LEFT, Y_SUMMARY_TOP - 12.0, MARGIN_LEFT + SUMMARY_W, Y_SUMMARY_TOP - 12.0)
    c.line(MARGIN_LEFT, Y_SUMMARY_TOP - 24.0, MARGIN_LEFT + SUMMARY_W, Y_SUMMARY_TOP - 24.0)

    X_REST_START = MARGIN_LEFT + LABEL_COL_W
    SUB_COL_W = (TABLE_W - LABEL_COL_W) / 4.0

    c.line(X_REST_START, Y_SUMMARY_TOP, X_REST_START, Y_SUMMARY_TOP - SUMMARY_H)
    for i in range(1, 4):
        x_div = X_REST_START + i * SUB_COL_W
        c.line(x_div, Y_SUMMARY_TOP, x_div, Y_SUMMARY_TOP - SUMMARY_H)

    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(X_REST_START + 0.5 * SUB_COL_W, Y_SUMMARY_TOP - 9.0, "Saldo inizio mese")
    c.drawCentredString(X_REST_START + 1.5 * SUB_COL_W, Y_SUMMARY_TOP - 9.0, "Fruito")
    c.drawCentredString(X_REST_START + 2.5 * SUB_COL_W, Y_SUMMARY_TOP - 9.0, "Maturato")
    c.drawCentredString(X_REST_START + 3.5 * SUB_COL_W, Y_SUMMARY_TOP - 9.0, "Saldo fine mese")

    c.setFont("Helvetica", 8.0)
    c.drawString(MARGIN_LEFT + 6.0, Y_SUMMARY_TOP - 21.0, "Ferie")
    c.drawString(MARGIN_LEFT + 6.0, Y_SUMMARY_TOP - 33.0, "Compensativi")

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def generate_monthly_timesheet_excel(year: int, month: int, crew_num: int) -> bytes:
    """
    Genera il file Excel (.xlsx) nativo basato sulla struttura del foglio presenze Tripmare,
    speculare al layout e alle formattazioni del modulo PDF ufficiale.
    """
    data = get_month_crew_data(year, month, crew_num)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Presenze Eq {crew_num}"

    # Stili Font
    font_header_title = Font(name="Calibri", size=11, bold=True)
    font_bold_sm = Font(name="Calibri", size=9, bold=True)
    font_regular_sm = Font(name="Calibri", size=8.5)
    font_regular_xs = Font(name="Calibri", size=8)

    # Allineamenti
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")

    # Bordi
    thin_s = Side(border_style="thin", color="000000")
    medium_s = Side(border_style="medium", color="000000")
    b_thin = Border(top=thin_s, bottom=thin_s, left=thin_s, right=thin_s)

    def apply_range_border(start_r, start_c, end_r, end_c, border_style=b_thin):
        for r in range(start_r, end_r + 1):
            for c in range(start_c, end_c + 1):
                ws.cell(row=r, column=c).border = border_style

    # =========================================================================
    # 1. TESTATA SUPERIORE (Righe 1 e 2)
    # =========================================================================
    # Riga 1: Mese (A1:D1), Cognome (E1:P1), Nome (Q1:AA1), Codice (AB1:AJ1)
    ws.merge_cells("A1:D1")
    ws["A1"] = "Mese"
    ws["A1"].font = font_header_title
    ws["A1"].alignment = align_center

    ws.merge_cells("E1:P1")
    ws["E1"] = "Cognome"
    ws["E1"].font = font_bold_sm
    ws["E1"].alignment = align_left

    ws.merge_cells("Q1:AA1")
    ws["Q1"] = "Nome"
    ws["Q1"].font = font_bold_sm
    ws["Q1"].alignment = align_left

    ws.merge_cells("AB1:AJ1")
    ws["AB1"] = "Codice"
    ws["AB1"].font = font_bold_sm
    ws["AB1"].alignment = align_left

    apply_range_border(1, 1, 1, 4)
    apply_range_border(1, 5, 1, 16)
    apply_range_border(1, 17, 1, 27)
    apply_range_border(1, 28, 1, 36)

    # Riga 2: Nome Mese a fianco dell'Anno
    ws.merge_cells("A2:C2")
    ws["A2"] = MESI_MAIUSCOLO[month]
    ws["A2"].font = font_bold_sm
    ws["A2"].alignment = align_center

    ws["D2"] = year
    ws["D2"].font = font_bold_sm
    ws["D2"].alignment = align_center

    apply_range_border(2, 1, 2, 3)
    ws["D2"].border = b_thin

    # Numeri 1..31 da Colonna E (5) a AI (35)
    for day in range(1, 32):
        cell = ws.cell(row=2, column=4 + day, value=day)
        cell.font = font_bold_sm
        cell.alignment = align_center
        cell.border = b_thin

    # Cella vuota sopra Totale in Colonna AJ (36)
    ws.cell(row=2, column=36).border = b_thin

    # =========================================================================
    # 2. RIGHE DI SERVIZIO (3: giorno della settimana, 4: Equipaggio, 5..6: Orari)
    # =========================================================================
    # Riga 3: giorno della settimana
    ws.merge_cells("A3:D3")
    ws["A3"] = "giorno della settimana"
    ws["A3"].font = font_regular_sm
    ws["A3"].alignment = align_center
    apply_range_border(3, 1, 3, 4)

    # Riga 4: Equipaggio
    ws.merge_cells("A4:D4")
    ws["A4"] = "Equipaggio"
    ws["A4"].font = font_bold_sm
    ws["A4"].alignment = align_center
    apply_range_border(4, 1, 4, 4)

    # Righe 5 e 6: Orario di servizio (A5:C6 unito) + Dalle (D5) / Alle (D6)
    ws.merge_cells("A5:C6")
    ws["A5"] = "Orario di servizio"
    ws["A5"].font = font_bold_sm
    ws["A5"].alignment = align_center
    apply_range_border(5, 1, 6, 3)

    ws["D5"] = "Dalle"
    ws["D5"].font = font_regular_sm
    ws["D5"].alignment = align_center
    ws["D5"].border = b_thin

    ws["D6"] = "Alle"
    ws["D6"].font = font_regular_sm
    ws["D6"].alignment = align_center
    ws["D6"].border = b_thin

    # Merge Tot. sulle righe 5 e 6 in colonna AJ (36)
    ws.merge_cells("AJ5:AJ6")
    ws["AJ5"] = "Tot."
    ws["AJ5"].font = font_bold_sm
    ws["AJ5"].alignment = align_center
    apply_range_border(5, 36, 6, 36)

    # =========================================================================
    # 3. VOCI 1..17 E CAPI SERVIZIO (Righe da 7 a 25)
    # =========================================================================
    items_rows_excel = [
        (7,  "1",  "Diu. Feriale"),
        (8,  "2",  "Nott. Fer./ Diu. Festivo"),
        (9,  "3",  "Nott. Festivo"),
        (10, "4",  "Servizi Prolungati"),
        (11, "5",  "Maggiorazione Notturna"),
        (12, "6",  "Indennità Navigazione"),
        (13, "7",  "Indennità Sostitutiva"),
        (14, "8",  "Festivo"),
        (15, "9",  "Lavori non rientranti"),
        (16, "10", "Passaggio"),
        (17, "11", "Diurno"),
        (18, "12", "Notturno"),
        (19, "13", "Compensativo/i Maturato/i"),
        (20, "14", "Reperibilità (solo 8-20 00-08)"),
        (21, "15", "Buoni pasto"),
        (22, "16", "Ore Sciopero"),
        (23, "17", ""),
        (24, "",   "Cognome del Capo Servizio"),
        (25, "",   "Firma del Capo Servizio")
    ]

    for r_idx, num_str, desc_str in items_rows_excel:
        if num_str:
            ws.cell(row=r_idx, column=1, value=num_str).alignment = align_center
            ws.cell(row=r_idx, column=1).font = font_bold_sm
            ws.cell(row=r_idx, column=1).border = b_thin

        # Merge qualificatori o descrizioni
        if r_idx in [7, 8, 9]:
            # Righe 1, 2, 3: Colonna B è unita per "Str.", Col C..D per descrizione
            ws.merge_cells(start_row=r_idx, start_column=3, end_row=r_idx, end_column=4)
            ws.cell(row=r_idx, column=3, value=desc_str).alignment = align_left
            ws.cell(row=r_idx, column=3).font = font_regular_sm
            apply_range_border(r_idx, 3, r_idx, 4)
        elif r_idx in [17, 18]:
            # Righe 11, 12: Colonna B è unita per "Risc.", Col C..D per descrizione
            ws.merge_cells(start_row=r_idx, start_column=3, end_row=r_idx, end_column=4)
            ws.cell(row=r_idx, column=3, value=desc_str).alignment = align_left
            ws.cell(row=r_idx, column=3).font = font_regular_sm
            apply_range_border(r_idx, 3, r_idx, 4)
        elif r_idx in [24, 25]:
            # Capi Servizio: uniti su A..D
            ws.merge_cells(start_row=r_idx, start_column=1, end_row=r_idx, end_column=4)
            ws.cell(row=r_idx, column=1, value=desc_str).alignment = align_left
            ws.cell(row=r_idx, column=1).font = font_regular_sm
            apply_range_border(r_idx, 1, r_idx, 4)
        else:
            # Righe 4..10 e 13..17: Colonna B..D per descrizione
            ws.merge_cells(start_row=r_idx, start_column=2, end_row=r_idx, end_column=4)
            ws.cell(row=r_idx, column=2, value=desc_str).alignment = align_left
            ws.cell(row=r_idx, column=2).font = font_regular_xs if "Reperibilità" in desc_str else font_regular_sm
            apply_range_border(r_idx, 2, r_idx, 4)

    # 1) Merge 3 celle di "Str." (B7:B9)
    ws.merge_cells("B7:B9")
    ws["B7"] = "Str."
    ws["B7"].font = font_bold_sm
    ws["B7"].alignment = align_center
    apply_range_border(7, 2, 9, 2)

    # 2) Merge 2 celle di "Risc." (B17:B18)
    ws.merge_cells("B17:B18")
    ws["B17"] = "Risc."
    ws["B17"].font = font_bold_sm
    ws["B17"].alignment = align_center
    apply_range_border(17, 2, 18, 2)

    # =========================================================================
    # 4. POPOLAMENTO DATI NELLE 31 COLONNE (Righe 3..25)
    # =========================================================================
    days_dict = data["days"]
    for day in range(1, 32):
        c_idx = 4 + day
        d_info = days_dict[day]

        for r_idx in range(3, 26):
            cell = ws.cell(row=r_idx, column=c_idx)
            cell.border = b_thin
            cell.alignment = align_center

            if not d_info["exists"]:
                cell.value = "-"
                continue

            if r_idx == 3:
                cell.value = d_info["giorno_lett"]
                cell.font = font_bold_sm
            elif r_idx == 4:
                cell.value = d_info["equipaggio"]
                cell.font = font_bold_sm
            elif r_idx == 5:
                cell.value = d_info["dalle"]
                cell.font = font_regular_sm
            elif r_idx == 6:
                cell.value = d_info["alle"]
                cell.font = font_regular_sm
            elif r_idx == 11:
                cell.value = d_info["notturna"]
                cell.font = font_regular_sm
            elif r_idx == 12:
                cell.value = d_info["navigazione"]
                cell.font = font_regular_sm
            elif r_idx == 14:
                cell.value = d_info["festivo"]
                cell.font = font_regular_sm
            elif r_idx == 21:
                cell.value = d_info["buoni_pasto"]
                cell.font = font_regular_sm

    # Totali colonna 36 (AJ) per le voci di riga
    tot_map = {
        11: data["tot_notturna"],
        12: data["tot_navigazione"],
        14: data["tot_festivo"],
        21: data["tot_buoni_pasto"]
    }

    for r_idx in range(7, 24):
        cell_tot = ws.cell(row=r_idx, column=36)
        cell_tot.border = b_thin
        cell_tot.alignment = align_center
        cell_tot.font = font_bold_sm
        if r_idx in tot_map and tot_map[r_idx] > 0:
            cell_tot.value = tot_map[r_idx]

    # =========================================================================
    # 5. TABELLA RIEPILOGO FERIE E COMPENSATIVI (A TUTTA LARGHEZZA)
    # =========================================================================
    # Riga 27: Intestazioni riepilogo
    ws.merge_cells("A27:D27")
    apply_range_border(27, 1, 27, 4)

    ws.merge_cells("E27:L27")
    ws["E27"] = "Saldo inizio mese"
    ws["E27"].font = font_bold_sm
    ws["E27"].alignment = align_center
    apply_range_border(27, 5, 27, 12)

    ws.merge_cells("M27:T27")
    ws["M27"] = "Fruito"
    ws["M27"].font = font_bold_sm
    ws["M27"].alignment = align_center
    apply_range_border(27, 13, 27, 20)

    ws.merge_cells("U27:AB27")
    ws["U27"] = "Maturato"
    ws["U27"].font = font_bold_sm
    ws["U27"].alignment = align_center
    apply_range_border(27, 21, 27, 28)

    ws.merge_cells("AC27:AJ27")
    ws["AC27"] = "Saldo fine mese"
    ws["AC27"].font = font_bold_sm
    ws["AC27"].alignment = align_center
    apply_range_border(27, 29, 27, 36)

    # Riga 28: Ferie
    ws.merge_cells("A28:D28")
    ws["A28"] = "Ferie"
    ws["A28"].font = font_regular_sm
    ws["A28"].alignment = align_left
    apply_range_border(28, 1, 28, 4)
    ws.merge_cells("E28:L28")
    apply_range_border(28, 5, 28, 12)
    ws.merge_cells("M28:T28")
    apply_range_border(28, 13, 28, 20)
    ws.merge_cells("U28:AB28")
    apply_range_border(28, 21, 28, 28)
    ws.merge_cells("AC28:AJ28")
    apply_range_border(28, 29, 28, 36)

    # Riga 29: Compensativi
    ws.merge_cells("A29:D29")
    ws["A29"] = "Compensativi"
    ws["A29"].font = font_regular_sm
    ws["A29"].alignment = align_left
    apply_range_border(29, 1, 29, 4)
    ws.merge_cells("E29:L29")
    apply_range_border(29, 5, 29, 12)
    ws.merge_cells("M29:T29")
    apply_range_border(29, 13, 29, 20)
    ws.merge_cells("U29:AB29")
    apply_range_border(29, 21, 29, 28)
    ws.merge_cells("AC29:AJ29")
    apply_range_border(29, 29, 29, 36)

    # =========================================================================
    # 6. DIMENSIONAMENTO COLONNE E ALTEZZE RIGHE (SPECULARI AL PDF)
    # =========================================================================
    ws.column_dimensions["A"].width = 3.6
    ws.column_dimensions["B"].width = 5.2
    ws.column_dimensions["C"].width = 13.5
    ws.column_dimensions["D"].width = 6.8

    for day in range(1, 32):
        col_letter = openpyxl.utils.get_column_letter(4 + day)
        ws.column_dimensions[col_letter].width = 3.6

    ws.column_dimensions["AJ"].width = 5.5

    # Altezze righe Excel
    ws.row_dimensions[1].height = 20
    ws.row_dimensions[2].height = 16
    ws.row_dimensions[3].height = 15
    ws.row_dimensions[4].height = 15
    ws.row_dimensions[5].height = 14
    ws.row_dimensions[6].height = 14
    for r in range(7, 24):
        ws.row_dimensions[r].height = 14
    ws.row_dimensions[24].height = 16
    ws.row_dimensions[25].height = 36  # Riga alta per Firma Capo Servizio!
    ws.row_dimensions[26].height = 8   # Spaziatore
    ws.row_dimensions[27].height = 15
    ws.row_dimensions[28].height = 16
    ws.row_dimensions[29].height = 16

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()
