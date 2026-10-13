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
    Genera il foglio presenze mensile da zero in PDF vettoriale A4 Landscape nativo (842 x 595 pt),
    riproducendo fedelmente layout, riquadri ed evidenziazioni del modulo originale Tripmare.
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

    # Suddivisione orizzontale:
    # Etichette sinistra: 165 pt (suddivise internamente in 4 sottocolonne come in Excel)
    LABEL_COL_W = 165.0
    TOTAL_COL_W = 28.0
    GRID_DAYS_W = TABLE_W - LABEL_COL_W - TOTAL_COL_W
    DAY_COL_W = GRID_DAYS_W / 31.0

    X_LABEL_START = MARGIN_LEFT
    X_DAYS_START = MARGIN_LEFT + LABEL_COL_W
    X_TOTAL_START = MARGIN_RIGHT - TOTAL_COL_W

    # Sottocolonne dell'area etichette sinistra (165 pt)
    # X0: Start (0)
    # X1: Num voce (1..17) -> +14 pt
    # X2: Qualificatore (Str. / Risc.) -> +24 pt
    # X3: Orario servizio / Dalle-Alle divider -> +105 pt
    X_SUB_NUM = X_LABEL_START + 14.0
    X_SUB_QUAL = X_SUB_NUM + 24.0
    X_SUB_ORARIO = X_LABEL_START + 105.0

    def get_cx(d: int) -> float:
        return X_DAYS_START + (d - 1) * DAY_COL_W + (DAY_COL_W / 2.0)

    # 1. STRUTTURA RIGHE
    # Definizione altezze verticali dal bordo superiore
    Y_TABLE_TOP = PAGE_H - 24.0

    H_TOP_HEADER = 20.0     # Riga Mese, Cognome, Nome, Codice
    H_ROW_NUM_DAYS = 13.0   # Riga Anno + Numeri 1..31
    H_ROW_WEEKDAY = 13.0    # giorno della settimana
    H_ROW_CREW = 13.0       # Equipaggio
    H_ROW_DALLE = 12.0      # Dalle
    H_ROW_ALLE = 12.0       # Alle
    H_ROW_ITEM = 12.0       # Righe voci 1..17
    H_ROW_CAPO_COG = 14.0   # Cognome del Capo Servizio
    H_ROW_CAPO_FIRMA = 26.0 # Firma del Capo Servizio

    # Elenco righe per la griglia delle voci (da riga 1 a riga 17 + capi)
    items_def = [
        ("STR_1", "1", "Str.", "Diu. Feriale"),
        ("STR_2", "2", "", "Nott. Fer./ Diu. Festivo"),
        ("STR_3", "3", "", "Nott. Festivo"),
        ("VOCE_4", "4", "", "Servizi Prolungati"),
        ("VOCE_5", "5", "", "Maggiorazione Notturna"),
        ("VOCE_6", "6", "", "Indennità Navigazione"),
        ("VOCE_7", "7", "", "Indennità Sostitutiva"),
        ("VOCE_8", "8", "", "Festivo"),
        ("VOCE_9", "9", "", "Lavori non rientranti"),
        ("VOCE_10", "10", "", "Passaggio"),
        ("VOCE_11", "11", "Risc.", "Diurno"),
        ("VOCE_12", "12", "", "Notturno"),
        ("VOCE_13", "13", "", "Compensativo/i Maturato/i"),
        ("VOCE_14", "14", "", "Reperibilità (solo 8-20 00-08)"),
        ("VOCE_15", "15", "", "Buoni pasto"),
        ("VOCE_16", "16", "", "Ore Sciopero"),
        ("VOCE_17", "17", "", ""),
        ("CAPO_COG", "", "", "Cognome del Capo Servizio"),
        ("CAPO_FIRMA", "", "", "Firma del Capo Servizio")
    ]

    # Coordinate verticali
    y_top_header = Y_TABLE_TOP
    y_num_days = y_top_header - H_TOP_HEADER
    y_weekday = y_num_days - H_ROW_NUM_DAYS
    y_crew = y_weekday - H_ROW_WEEKDAY
    y_dalle = y_crew - H_ROW_CREW
    y_alle = y_dalle - H_ROW_DALLE
    y_items_start = y_alle - H_ROW_ALLE

    # Calcolo coordinate Y per ogni riga voci
    item_rows_coords = []
    curr_y = y_items_start
    for code, num_str, qual_str, desc_str in items_def:
        h = H_ROW_CAPO_FIRMA if code == "CAPO_FIRMA" else (H_ROW_CAPO_COG if code == "CAPO_COG" else H_ROW_ITEM)
        y_top = curr_y
        y_bot = curr_y - h
        item_rows_coords.append((code, num_str, qual_str, desc_str, y_top, y_bot))
        curr_y = y_bot

    Y_TABLE_BOTTOM = curr_y

    # =========================================================================
    # DISEGNO GRIGLIA, RIGHE E BORDINI
    # =========================================================================

    # 1. TESTATA SUPERIORE (Mese, Cognome, Nome, Codice)
    c.setLineWidth(0.5)
    # Linea divisoria tra Mese e Giorni
    c.line(MARGIN_LEFT, y_num_days, MARGIN_RIGHT, y_num_days)

    # Separatori verticali della testata
    x_h_cognome = MARGIN_LEFT + 105.0
    x_h_nome = x_h_cognome + 240.0
    x_h_codice = x_h_nome + 225.0

    c.line(x_h_cognome, y_num_days, x_h_cognome, y_top_header)
    c.line(x_h_nome, y_num_days, x_h_nome, y_top_header)
    c.line(x_h_codice, y_num_days, x_h_codice, y_top_header)

    c.setFont("Helvetica-Bold", 8.0)
    c.drawString(MARGIN_LEFT + 4.0, y_top_header - 9.0, "Mese")
    c.drawString(x_h_cognome + 6.0, y_top_header - 9.0, "Cognome")
    c.drawString(x_h_nome + 6.0, y_top_header - 9.0, "Nome")
    c.drawString(x_h_codice + 6.0, y_top_header - 9.0, "Codice")

    # Mese selezionato scritto in maiuscolo
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(MARGIN_LEFT + 32.0, y_top_header - 14.5, MESI_MAIUSCOLO[month])

    # 2. RIGA NUMERI GIORNO (SULLA STESSA RIGA DELL'ANNO!)
    # Separatore tra Anno e Giorno 1
    c.line(X_DAYS_START, y_weekday, X_DAYS_START, y_num_days)

    # Scrittura dell'Anno nella casellina a sinistra
    c.setFont("Helvetica-Bold", 10.0)
    c.drawCentredString(MARGIN_LEFT + LABEL_COL_W / 2.0, y_num_days - 10.0, str(year))

    # Linee orizzontali del blocco superiore
    c.setLineWidth(0.5)
    c.line(MARGIN_LEFT, y_weekday, MARGIN_RIGHT, y_weekday)  # sotto numeri giorni
    c.line(MARGIN_LEFT, y_crew, MARGIN_RIGHT, y_crew)        # sotto giorno settimana
    c.line(MARGIN_LEFT, y_dalle, MARGIN_RIGHT, y_dalle)      # sotto equipaggio
    c.line(X_SUB_ORARIO, y_alle, MARGIN_RIGHT, y_alle)       # tra Dalle e Alle

    # LINEA GRASSETTO: Sotto "Alle" (separa orari di servizio dalle voci straordinari/indennità)
    c.setLineWidth(1.4)
    c.line(MARGIN_LEFT, y_items_start, MARGIN_RIGHT, y_items_start)

    # Testi etichette blocco orario a sinistra
    c.setFont("Helvetica", 7.5)
    c.drawString(MARGIN_LEFT + 4.0, y_weekday - 9.5, "giorno della settimana")
    c.drawString(MARGIN_LEFT + 4.0, y_crew - 9.5, "Equipaggio")
    
    # "Orario di servizio" centrato verticalmente nel suo riquadro doppio
    c.drawCentredString(MARGIN_LEFT + (X_SUB_ORARIO - MARGIN_LEFT) / 2.0, y_dalle - 14.0, "Orario di servizio")
    c.line(X_SUB_ORARIO, y_dalle, X_SUB_ORARIO, y_items_start)
    c.drawString(X_SUB_ORARIO + 6.0, y_dalle - 9.0, "Dalle")
    c.drawString(X_SUB_ORARIO + 6.0, y_alle - 9.0, "Alle")

    # Scrittura "Tot." sopra la colonna totale (a cavallo tra Dalle e Alle)
    c.setFont("Helvetica-Bold", 8.0)
    c.drawCentredString(X_TOTAL_START + TOTAL_COL_W / 2.0, y_dalle - 14.0, "Tot.")

    # 3. LINEE ORIZZONTALI DELLE VOCI (1..17 E CAPI) CON I RISPETTIVI GRASSETTI
    c.setLineWidth(0.5)
    for code, num_str, qual_str, desc_str, y_t, y_b in item_rows_coords:
        # Controllo linee marcate / in grassetto come da modulo ufficiale
        if code == "STR_3":
            # LINEA GRASSETTO: separa straordinari 1, 2, 3 dalle indennità 4..17
            c.setLineWidth(1.4)
            c.line(MARGIN_LEFT, y_b, MARGIN_RIGHT, y_b)
            c.setLineWidth(0.5)
        elif code == "VOCE_17":
            # LINEA GRASSETTO: separa le voci dai capi servizio
            c.setLineWidth(1.4)
            c.line(MARGIN_LEFT, y_b, MARGIN_RIGHT, y_b)
            c.setLineWidth(0.5)
        elif code == "CAPO_FIRMA":
            # Bordo inferiore finale (tracciato poi dal bordo esterno)
            pass
        else:
            c.setLineWidth(0.5)
            c.line(MARGIN_LEFT, y_b, MARGIN_RIGHT, y_b)

        # Scrittura testi etichette con sottocolonne allineate
        y_text = y_b + (y_t - y_b) / 2.0 - 2.5
        c.setFont("Helvetica-Bold", 7.2)
        if num_str:
            c.drawCentredString(MARGIN_LEFT + 7.0, y_text, num_str)

        c.setFont("Helvetica-Bold" if qual_str else "Helvetica", 7.0)
        if qual_str:
            c.drawString(X_SUB_NUM + 2.0, y_text, qual_str)

        c.setFont("Helvetica", 6.8 if "Reperibilità" in desc_str else 7.2)
        x_desc = X_SUB_QUAL + 2.0 if (num_str or qual_str) else MARGIN_LEFT + 4.0
        c.drawString(x_desc, y_text, desc_str)

    # Tracciamento linee verticali sottocolonne a sinistra (solo per le righe delle voci 1..17)
    c.setLineWidth(0.4)
    y_voci_bot = item_rows_coords[16][5] # Fondo riga 17
    c.line(X_SUB_NUM, y_items_start, X_SUB_NUM, y_voci_bot)
    c.line(X_SUB_QUAL, y_items_start, X_SUB_QUAL, y_voci_bot)

    # 4. LINEE VERTICALI DELLE COLONNE GIORNI
    c.setLineWidth(0.4)
    for day in range(1, 31):
        x_c = X_DAYS_START + day * DAY_COL_W
        c.line(x_c, y_num_days, x_c, Y_TABLE_BOTTOM)

    # LINEE VERTICALI IN GRASSETTO
    c.setLineWidth(1.4)
    # Linea che separa etichette sinistra dai giorni
    c.line(X_DAYS_START, y_num_days, X_DAYS_START, Y_TABLE_BOTTOM)
    # Linea che separa i giorni dalla colonna Totale
    c.line(X_TOTAL_START, y_num_days, X_TOTAL_START, Y_TABLE_BOTTOM)

    # BORDO ESTERNO GENERALE IN GRASSETTO
    c.setLineWidth(1.4)
    c.rect(MARGIN_LEFT, Y_TABLE_BOTTOM, TABLE_W, Y_TABLE_TOP - Y_TABLE_BOTTOM, stroke=1, fill=0)

    # =========================================================================
    # POPOLAMENTO DEI DATI DEL TURNO
    # =========================================================================
    days_dict = data["days"]

    for day in range(1, 32):
        d_info = days_dict[day]
        cx = get_cx(day)

        # Se il giorno non esiste (es. 31 nei mesi da 30), traccia la barra diagonale
        if not d_info["exists"]:
            c.setLineWidth(0.8)
            col_x1 = X_DAYS_START + (day - 1) * DAY_COL_W
            col_x2 = col_x1 + DAY_COL_W
            c.line(col_x1, y_num_days, col_x2, Y_TABLE_BOTTOM)
            continue

        # Numero del giorno (1..31)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(cx, y_num_days - 9.5, str(day))

        # Giorno della settimana (L, M, M, G, V, S, D)
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
            c.drawCentredString(cx, y_dalle - 9.0, d_info["dalle"])
        if d_info["alle"]:
            c.drawCentredString(cx, y_alle - 9.0, d_info["alle"])

        # Competenze e Indennità
        for code, _, _, _, y_t, y_b in item_rows_coords:
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
    for code, _, _, _, y_t, y_b in item_rows_coords:
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
    # TABELLA RIEPILOGO FERIE E COMPENSATIVI (IN BASSO A SINISTRA)
    # =========================================================================
    Y_SUMMARY_TOP = Y_TABLE_BOTTOM - 6.0
    SUMMARY_W = 440.0
    SUMMARY_H = 36.0

    c.setLineWidth(1.0)
    c.rect(MARGIN_LEFT, Y_SUMMARY_TOP - SUMMARY_H, SUMMARY_W, SUMMARY_H, stroke=1, fill=0)

    # Linee orizzontali interne
    c.setLineWidth(0.5)
    c.line(MARGIN_LEFT, Y_SUMMARY_TOP - 12.0, MARGIN_LEFT + SUMMARY_W, Y_SUMMARY_TOP - 12.0)
    c.line(MARGIN_LEFT, Y_SUMMARY_TOP - 24.0, MARGIN_LEFT + SUMMARY_W, Y_SUMMARY_TOP - 24.0)

    # Linee verticali divisorie colonne
    col_splits = [110.0, 192.5, 275.0, 357.5]
    for split_x in col_splits:
        c.line(MARGIN_LEFT + split_x, Y_SUMMARY_TOP, MARGIN_LEFT + split_x, Y_SUMMARY_TOP - SUMMARY_H)

    c.setFont("Helvetica-Bold", 7.0)
    c.drawCentredString(MARGIN_LEFT + 151.0, Y_SUMMARY_TOP - 9.0, "Saldo inizio mese")
    c.drawCentredString(MARGIN_LEFT + 233.5, Y_SUMMARY_TOP - 9.0, "Fruito")
    c.drawCentredString(MARGIN_LEFT + 316.0, Y_SUMMARY_TOP - 9.0, "Maturato")
    c.drawCentredString(MARGIN_LEFT + 398.5, Y_SUMMARY_TOP - 9.0, "Saldo fine mese")

    c.setFont("Helvetica", 7.5)
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
