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

    # Suddivisione orizzontale
    LABEL_COL_W = 166.0
    TOTAL_COL_W = 28.0
    GRID_DAYS_W = TABLE_W - LABEL_COL_W - TOTAL_COL_W
    DAY_COL_W = GRID_DAYS_W / 31.0

    X_LABEL_START = MARGIN_LEFT
    X_DAYS_START = MARGIN_LEFT + LABEL_COL_W
    X_TOTAL_START = MARGIN_RIGHT - TOTAL_COL_W

    # Ripartizione orizzontale della colonna etichette (166 pt)
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
    H_ROW_CAPO_FIRMA = 26.0 # Firma del Capo Servizio

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

    # Intestazione "Mese": grande e centrata nella sua cella superiore
    c.setFont("Helvetica-Bold", 12.0)
    c.drawCentredString(MARGIN_LEFT + LABEL_COL_W / 2.0, y_num_days + 6.5, "Mese")

    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(x_h_cognome + 8.0, y_num_days + 6.0, "Cognome")
    c.drawString(x_h_nome + 8.0, y_num_days + 6.0, "Nome")
    c.drawString(x_h_codice + 8.0, y_num_days + 6.0, "Codice")

    # =========================================================================
    # 2. LINEE ORIZZONTALI E BORDATURE
    # =========================================================================
    # LINEA GRASSETTO: Sotto la testata superiore
    c.setLineWidth(1.4)
    c.line(MARGIN_LEFT, y_num_days, MARGIN_RIGHT, y_num_days)

    # Linee orizzontali sottili intermedie
    c.setLineWidth(0.5)
    c.line(MARGIN_LEFT, y_weekday, MARGIN_RIGHT, y_weekday)  # sotto numeri giorni
    c.line(MARGIN_LEFT, y_crew, MARGIN_RIGHT, y_crew)        # sotto giorno settimana

    # LINEA GRASSETTO: Sotto Equipaggio / sopra Orario di servizio
    c.setLineWidth(1.4)
    c.line(MARGIN_LEFT, y_dalle, MARGIN_RIGHT, y_dalle)

    # Linea sottile tra Dalle e Alle (NON attraversa la colonna Tot. che è mergiata)
    c.setLineWidth(0.5)
    c.line(X_SUB_ORARIO, y_alle, X_TOTAL_START, y_alle)

    # LINEA GRASSETTO: Sotto Alle (separa orari da straordinari)
    c.setLineWidth(1.4)
    c.line(MARGIN_LEFT, y_items_start, MARGIN_RIGHT, y_items_start)

    # Linee orizzontali del blocco voci 1..17
    # (Per le righe 1 e 2, la linea orizzontale salta la colonna di "Str." che è mergiata)
    for code, _, _, _, y_b in item_rows_coords:
        if code in ["STR_1", "STR_2"]:
            c.setLineWidth(0.5)
            # Tratto a sinistra per il numero
            c.line(MARGIN_LEFT, y_b, X_SUB_NUM, y_b)
            # Salto di X_SUB_NUM -> X_SUB_QUAL (cella mergiata di Str.)
            # Tratto da X_SUB_QUAL fino al fondo tabella
            c.line(X_SUB_QUAL, y_b, MARGIN_RIGHT, y_b)
        elif code == "STR_3":
            # Modifica 2: Riga orizzontale normale (0.5 pt) tra Nott. Festivo e Servizi Prolungati
            c.setLineWidth(0.5)
            c.line(MARGIN_LEFT, y_b, MARGIN_RIGHT, y_b)
        elif code == "VOCE_17":
            # Linea marcata che separa le voci dai capi servizio
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
    # Modifica 1: Nome del mese nella casella bianca sotto a Mese, a fianco dell'anno
    c.setFont("Helvetica-Bold", 10.0)
    c.drawCentredString(MARGIN_LEFT + (X_SUB_ORARIO - MARGIN_LEFT) / 2.0, y_num_days - 9.5, MESI_MAIUSCOLO[month])

    # Casellina dell'Anno (sopra Dalle/Alle)
    c.setLineWidth(0.6)
    c.line(X_SUB_ORARIO, y_num_days, X_SUB_ORARIO, y_weekday)
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(X_SUB_ORARIO + (X_DAYS_START - X_SUB_ORARIO) / 2.0, y_num_days - 9.5, str(year))

    # "giorno della settimana": centrato orizzontalmente
    c.setFont("Helvetica", 8.0)
    c.drawCentredString(MARGIN_LEFT + LABEL_COL_W / 2.0, y_weekday - 9.5, "giorno della settimana")

    # "Equipaggio": centrato orizzontalmente
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(MARGIN_LEFT + LABEL_COL_W / 2.0, y_crew - 9.5, "Equipaggio")

    # "Orario di servizio": grassetto marcato, centrato nel riquadro doppio
    c.setLineWidth(0.6)
    c.line(X_SUB_ORARIO, y_dalle, X_SUB_ORARIO, y_items_start)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawCentredString(MARGIN_LEFT + (X_SUB_ORARIO - MARGIN_LEFT) / 2.0, y_dalle - 15.0, "Orario di servizio")

    # "Dalle" e "Alle": centrati nelle rispettive celle
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(X_SUB_ORARIO + (X_DAYS_START - X_SUB_ORARIO) / 2.0, y_dalle - 8.5, "Dalle")
    c.drawCentredString(X_SUB_ORARIO + (X_DAYS_START - X_SUB_ORARIO) / 2.0, y_alle - 8.5, "Alle")

    # Modifica 4: "Tot." mergiato su 2 celle verticali (a cavallo tra Dalle e Alle)
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

    # Modifica 3: Merge delle 3 celle per "Str." sotto Orario di servizio
    c.line(X_SUB_QUAL, y_items_start, X_SUB_QUAL, y_str3_bot)
    c.setFont("Helvetica-Bold", 8.0)
    c.drawCentredString(X_SUB_NUM + (X_SUB_QUAL - X_SUB_NUM) / 2.0, y_items_start - (3 * H_ROW_ITEM) / 2.0 - 2.5, "Str.")

    # Colonnina 'Risc.' (righe 11 e 12)
    y_r11_top = item_rows_coords[10][3]
    y_r12_bot = item_rows_coords[11][4]
    c.line(X_SUB_QUAL, y_r11_top, X_SUB_QUAL, y_r12_bot)
    c.drawCentredString(X_SUB_NUM + (X_SUB_QUAL - X_SUB_NUM) / 2.0, y_r11_top - H_ROW_ITEM - 2.5, "Risc.")

    # Scrittura numeri voci e descrizioni
    for code, num_str, desc_str, y_t, y_b in item_rows_coords:
        y_text = y_b + (y_t - y_b) / 2.0 - 2.5
        c.setFont("Helvetica-Bold", 7.5)
        if num_str:
            c.drawCentredString(MARGIN_LEFT + (X_SUB_NUM - MARGIN_LEFT) / 2.0, y_text, num_str)

        # Descrizione voce
        c.setFont("Helvetica", 6.8 if "Reperibilità" in desc_str else 7.2)
        if code in ["STR_1", "STR_2", "STR_3", "VOCE_11", "VOCE_12"]:
            x_desc = X_SUB_QUAL + 3.0
        elif num_str:
            x_desc = X_SUB_NUM + 3.0
        else:
            x_desc = MARGIN_LEFT + 4.0
        c.drawString(x_desc, y_text, desc_str)

    # =========================================================================
    # 5. LINEE VERTICALI DELLE COLONNE DEI GIORNI E BORDATURE IN GRASSETTO
    # =========================================================================
    c.setLineWidth(0.4)
    for day in range(1, 31):
        x_c = X_DAYS_START + day * DAY_COL_W
        c.line(x_c, y_num_days, x_c, Y_TABLE_BOTTOM)

    # LINEE VERTICALI IN GRASSETTO
    c.setLineWidth(1.4)
    c.line(X_DAYS_START, y_num_days, X_DAYS_START, Y_TABLE_BOTTOM)
    c.line(X_TOTAL_START, y_num_days, X_TOTAL_START, Y_TABLE_BOTTOM)

    # BORDO ESTERNO GENERALE IN GRASSETTO
    c.setLineWidth(1.4)
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

        # Numero del giorno (1..31)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(cx, y_num_days - 9.5, str(day))

        # Giorno della settimana
        c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(cx, y_weekday - 9.5, d_info["giorno_lett"])

        # Ellisse sui festivi
        if d_info["is_holiday"]:
            c.setLineWidth(0.6)
            c.ellipse(cx - 5.5, y_weekday - 12.0, cx + 5.5, y_weekday - 1.0)

        # Equipaggio
        if d_info["is_riserva"]:
            c.setFont("Helvetica-Bold", 5.5)
            c.drawString(cx - 6.0, y_crew - 7.0, "R")
        elif d_info["equipaggio"]:
            c.setFont("Helvetica-Bold", 7.5)
            c.drawCentredString(cx, y_crew - 9.5, d_info["equipaggio"])

        # Orari Dalle / Alle
        c.setFont("Helvetica", 7.0)
        if d_info["dalle"]:
            c.drawCentredString(cx, y_dalle - 8.5, d_info["dalle"])
        if d_info["alle"]:
            c.drawCentredString(cx, y_alle - 8.5, d_info["alle"])

        # Competenze e Indennità
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
    # 7. TABELLA RIEPILOGO FERIE E COMPENSATIVI (LUNGA COME TUTTA LA TABELLA)
    # =========================================================================
    # Modifica 5: SUMMARY_W esteso da MARGIN_LEFT a MARGIN_RIGHT (pari a TABLE_W)
    Y_SUMMARY_TOP = Y_TABLE_BOTTOM - 6.0
    SUMMARY_W = TABLE_W
    SUMMARY_H = 36.0

    c.setLineWidth(1.0)
    c.rect(MARGIN_LEFT, Y_SUMMARY_TOP - SUMMARY_H, SUMMARY_W, SUMMARY_H, stroke=1, fill=0)

    # Linee orizzontali interne
    c.setLineWidth(0.5)
    c.line(MARGIN_LEFT, Y_SUMMARY_TOP - 12.0, MARGIN_LEFT + SUMMARY_W, Y_SUMMARY_TOP - 12.0)
    c.line(MARGIN_LEFT, Y_SUMMARY_TOP - 24.0, MARGIN_LEFT + SUMMARY_W, Y_SUMMARY_TOP - 24.0)

    # Ripartizione colonne riassuntive:
    # 1. Colonna etichette sinistra = LABEL_COL_W (166 pt)
    # 2. Le restanti 4 colonne si dividono equamente lo spazio restante (TABLE_W - LABEL_COL_W)
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
    Genera il file Excel (.xlsx) nativo basato sulla struttura del foglio presenze Tripmare.
    """
    data = get_month_crew_data(year, month, crew_num)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Presenze Eq {crew_num}"

    font_bold = Font(name="Calibri", size=9, bold=True)
    font_regular = Font(name="Calibri", size=9)
    font_title = Font(name="Calibri", size=11, bold=True)
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")

    thin_border_side = Side(border_style="thin", color="000000")
    medium_border_side = Side(border_style="medium", color="000000")
    cell_border = Border(top=thin_border_side, bottom=thin_border_side, left=thin_border_side, right=thin_border_side)

    # Testata
    ws.merge_cells("A1:D1")
    ws["A1"] = "Mese"
    ws["A1"].font = font_bold

    ws.merge_cells("A2:C2")
    ws["A2"] = MESI_MAIUSCOLO[month]
    ws["A2"].font = font_title

    ws["D2"] = year
    ws["D2"].font = font_title
    ws["D2"].alignment = align_center

    ws.merge_cells("E1:P1")
    ws["E1"] = "Cognome"
    ws["E1"].font = font_bold

    ws.merge_cells("Q1:AA1")
    ws["Q1"] = "Nome"
    ws["Q1"].font = font_bold

    ws.merge_cells("AB1:AI1")
    ws["AB1"] = "Codice"
    ws["AB1"].font = font_bold

    # Riga 2 (Numeri 1..31)
    for day in range(1, 32):
        col_letter = openpyxl.utils.get_column_letter(4 + day)
        cell = ws[f"{col_letter}2"]
        cell.value = day
        cell.font = font_bold
        cell.alignment = align_center
        cell.border = cell_border

    row_labels = [
        (3, "giorno della settimana"),
        (4, "Equipaggio"),
        (5, "Orario di servizio - Dalle"),
        (6, "Orario di servizio - Alle"),
        (7, "1. Str. Diu. Feriale"),
        (8, "2. Str. Nott. Fer./ Diu. Festivo"),
        (9, "3. Str. Nott. Festivo"),
        (10, "4. Servizi Prolungati"),
        (11, "5. Maggiorazione Notturna"),
        (12, "6. Indennità Navigazione"),
        (13, "7. Indennità Sostitutiva"),
        (14, "8. Festivo"),
        (15, "9. Lavori non rientranti"),
        (16, "10. Passaggio"),
        (17, "11. Risc. Diurno"),
        (18, "12. Risc. Notturno"),
        (19, "13. Compensativo/i Maturato/i"),
        (20, "14. Reperibilità (solo 8-20 00-08)"),
        (21, "15. Buoni pasto"),
        (22, "16. Ore Sciopero"),
        (23, "17."),
        (24, "Cognome del Capo Servizio"),
        (25, "Firma del Capo Servizio")
    ]

    for r_idx, label in row_labels:
        ws.merge_cells(start_row=r_idx, start_column=1, end_row=r_idx, end_column=4)
        c_lbl = ws.cell(row=r_idx, column=1)
        c_lbl.value = label
        c_lbl.font = font_bold if r_idx in [3, 4] else font_regular
        c_lbl.alignment = align_left

        for c_i in range(1, 5):
            ws.cell(row=r_idx, column=c_i).border = cell_border

    ws.cell(row=6, column=36, value="Tot.").font = font_bold
    ws.cell(row=6, column=36).alignment = align_center

    days_dict = data["days"]
    for day in range(1, 32):
        col_idx = 4 + day
        d_info = days_dict[day]

        for r_idx in range(3, 26):
            cell = ws.cell(row=r_idx, column=col_idx)
            cell.border = cell_border
            cell.alignment = align_center

            if not d_info["exists"]:
                cell.value = "-"
                continue

            if r_idx == 3:
                cell.value = d_info["giorno_lett"]
                cell.font = font_bold
            elif r_idx == 4:
                cell.value = d_info["equipaggio"]
                cell.font = font_bold
            elif r_idx == 5:
                cell.value = d_info["dalle"]
            elif r_idx == 6:
                cell.value = d_info["alle"]
            elif r_idx == 11:
                cell.value = d_info["notturna"]
            elif r_idx == 12:
                cell.value = d_info["navigazione"]
            elif r_idx == 14:
                cell.value = d_info["festivo"]
            elif r_idx == 21:
                cell.value = d_info["buoni_pasto"]

    tot_map = {
        11: data["tot_notturna"],
        12: data["tot_navigazione"],
        14: data["tot_festivo"],
        21: data["tot_buoni_pasto"]
    }

    for r_idx in range(7, 24):
        cell_tot = ws.cell(row=r_idx, column=36)
        cell_tot.border = cell_border
        cell_tot.alignment = align_center
        cell_tot.font = font_bold
        if r_idx in tot_map and tot_map[r_idx] > 0:
            cell_tot.value = tot_map[r_idx]

    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 6
    ws.column_dimensions["C"].width = 6
    ws.column_dimensions["D"].width = 6
    for day in range(1, 32):
        col_letter = openpyxl.utils.get_column_letter(4 + day)
        ws.column_dimensions[col_letter].width = 4.0
    ws.column_dimensions["AJ"].width = 6.0

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()
