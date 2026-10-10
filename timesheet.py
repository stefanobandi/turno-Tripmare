import io
import os
import calendar
import datetime
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from engine import get_shift_for_crew, get_holiday_type

MESI_MAIUSCOLO = [
    "", "GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO",
    "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"
]

GIORNI_SETT_LETTERE = ["L", "M", "M", "G", "V", "S", "D"]

def find_template_path() -> str:
    """Cerca il file PDF template nel root o nella cartella documenti."""
    candidates = [
        "straordinario ed extra tripmare.pdf",
        os.path.join("documenti", "straordinario ed extra tripmare.pdf"),
        "straordinario_ed_extra_tripmare.pdf",
        os.path.join("documenti", "straordinario_ed_extra_tripmare.pdf")
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

def generate_monthly_timesheet_pdf(year: int, month: int, crew_num: int) -> bytes:
    """
    Sovrascrive il PDF template del modulo presenze mensile con i dati dell'equipaggio.
    Ritorna il flusso di byte del PDF finale generato.
    """
    template_path = find_template_path()
    if not template_path:
        raise FileNotFoundError("File template 'straordinario ed extra tripmare.pdf' non trovato.")

    reader = PdfReader(template_path)
    base_page = reader.pages[0]
    page_w = float(base_page.mediabox.width)
    page_h = float(base_page.mediabox.height)

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_w, page_h))
    c.setFillColorRGB(0, 0, 0)
    c.setStrokeColorRGB(0, 0, 0)

    # --- GEOMETRIA DELLA GRIGLIA ---
    # Il modulo ha 31 colonne per i giorni del mese + 1 colonna a destra per i totali
    X_START_DAY1 = 120.0
    X_TOTAL_END = 574.0
    COL_WIDTH = (X_TOTAL_END - X_START_DAY1) / 31.0
    X_TOT_COL = X_TOTAL_END + 11.0

    def col_center_x(day_idx: int) -> float:
        # day_idx da 1 a 31
        return X_START_DAY1 + (day_idx - 1) * COL_WIDTH + (COL_WIDTH / 2.0)

    # Coordinate verticali Y (dal basso verso l'alto nel sistema PDF)
    Y_MESE_TEXT = 780.0
    Y_ANNO_TEXT = 770.0
    Y_ROW_GIORNO_SETT = 753.0
    Y_ROW_EQUIPAGGIO = 741.0
    Y_ROW_DALLE = 728.0
    Y_ROW_ALLE = 716.0
    Y_ROW_NOTTURNA = 642.0     # Riga 5 Maggiorazione Notturna
    Y_ROW_NAVIGAZIONE = 629.0   # Riga 6 Indennità Navigazione
    Y_ROW_FESTIVO = 604.0       # Riga 8 Festivo
    Y_ROW_BUONI_PASTO = 515.0   # Riga 15 Buoni pasto

    # 1. Intestazione: Mese e Anno
    c.setFont("Helvetica-Bold", 10)
    nome_mese = MESI_MAIUSCOLO[month]
    c.drawString(45.0, Y_MESE_TEXT, nome_mese)
    c.drawString(68.0, Y_ANNO_TEXT, str(year))

    # 2. Calcolo dati per ciascun giorno del mese
    _, num_days = calendar.monthrange(year, month)

    tot_notturna = 0
    tot_navigazione = 0
    tot_festivo = 0
    tot_buoni_pasto = 0

    for day in range(1, 32):
        cx = col_center_x(day)

        if day > num_days:
            # Giorno inesistente nel mese: traccia una riga diagonale nera di cancellazione
            c.setLineWidth(0.8)
            col_x1 = X_START_DAY1 + (day - 1) * COL_WIDTH
            col_x2 = col_x1 + COL_WIDTH
            y_top_grid = Y_ROW_GIORNO_SETT + 8.0
            y_bottom_grid = Y_ROW_BUONI_PASTO - 15.0
            c.line(col_x1, y_top_grid, col_x2, y_bottom_grid)
            continue

        target_date = datetime.date(year, month, day)
        shift = get_shift_for_crew(crew_num, target_date)
        is_hol, is_semi, _ = get_holiday_type(target_date)
        stato = shift.get("stato", "")

        # A. Lettera giorno della settimana
        giorno_lett = GIORNI_SETT_LETTERE[target_date.weekday()]
        c.setFont("Helvetica", 7.5)
        c.drawCentredString(cx, Y_ROW_GIORNO_SETT, giorno_lett)

        # Se festivo (Domenica o festività contrattuale CCNL), disegna ellisse sottile nera
        if is_hol:
            c.setLineWidth(0.6)
            c.ellipse(cx - 5.5, Y_ROW_GIORNO_SETT - 3.0, cx + 5.5, Y_ROW_GIORNO_SETT + 8.5)

        # B. Equipaggio
        if stato.startswith("R"):
            # Giorno di riserva: 'R' minuscola/piccola in alto a sinistra della cella
            c.setFont("Helvetica-Bold", 5.5)
            c.drawString(cx - 5.5, Y_ROW_EQUIPAGGIO + 2.0, "R")
        elif stato in ["20", "08", "08:20"]:
            # Giorno lavorativo effettivo: numero equipaggio
            c.setFont("Helvetica-Bold", 7.5)
            c.drawCentredString(cx, Y_ROW_EQUIPAGGIO, str(crew_num))
        # Per L, L1, L2, L3 la cella equipaggio rimane in bianco

        # C. Orari Dalle / Alle e Competenze
        dalle_str = ""
        alle_str = ""
        val_notturna = None
        val_navigazione = None
        val_festivo = None
        val_buono = None

        if stato == "20":
            # Montante Notte
            dalle_str = "20"
            alle_str = "24"
            val_notturna = 4
            val_navigazione = 4
            val_buono = 1
            if is_hol:
                val_festivo = 1
        elif stato == "08":
            # Smontante Notte
            dalle_str = "00"
            alle_str = "08"
            val_notturna = 6
            val_navigazione = 8
            val_buono = 1
            if is_hol:
                val_festivo = 1
        elif stato == "08:20":
            # Diurno
            dalle_str = "08"
            alle_str = "20"
            val_navigazione = 12
            val_buono = 1
            if is_hol:
                val_festivo = 1

        c.setFont("Helvetica", 7.0)
        if dalle_str:
            c.drawCentredString(cx, Y_ROW_DALLE, dalle_str)
        if alle_str:
            c.drawCentredString(cx, Y_ROW_ALLE, alle_str)

        # Riga 5 - Maggiorazione Notturna
        if val_notturna is not None:
            c.drawCentredString(cx, Y_ROW_NOTTURNA, str(val_notturna))
            tot_notturna += val_notturna

        # Riga 6 - Indennità Navigazione
        if val_navigazione is not None:
            c.drawCentredString(cx, Y_ROW_NAVIGAZIONE, str(val_navigazione))
            tot_navigazione += val_navigazione

        # Riga 8 - Festivo
        if val_festivo is not None:
            c.drawCentredString(cx, Y_ROW_FESTIVO, str(val_festivo))
            tot_festivo += val_festivo

        # Riga 15 - Buoni pasto
        if val_buono is not None:
            c.drawCentredString(cx, Y_ROW_BUONI_PASTO, str(val_buono))
            tot_buoni_pasto += val_buono

    # 3. Totali colonna di destra
    c.setFont("Helvetica-Bold", 7.5)
    if tot_notturna > 0:
        c.drawCentredString(X_TOT_COL, Y_ROW_NOTTURNA, str(tot_notturna))
    if tot_navigazione > 0:
        c.drawCentredString(X_TOT_COL, Y_ROW_NAVIGAZIONE, str(tot_navigazione))
    if tot_festivo > 0:
        c.drawCentredString(X_TOT_COL, Y_ROW_FESTIVO, str(tot_festivo))
    if tot_buoni_pasto > 0:
        c.drawCentredString(X_TOT_COL, Y_ROW_BUONI_PASTO, str(tot_buoni_pasto))

    c.save()
    packet.seek(0)

    # 4. Fusione del livello grafico sopra il template PDF originale
    overlay_reader = PdfReader(packet)
    overlay_page = overlay_reader.pages[0]

    base_page.merge_page(overlay_page)

    writer = PdfWriter()
    writer.add_page(base_page)

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)

    return output_stream.getvalue()
