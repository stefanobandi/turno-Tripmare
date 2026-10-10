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
    Genera il foglio presenze mensile in formato A4 Landscape nativo (842 x 595 pt),
    sovrapponendo testo, orari e indennità nelle celle della tabella aziendale.
    """
    template_path = find_template_path()
    if not template_path:
        raise FileNotFoundError("File template 'straordinario ed extra tripmare.pdf' non trovato.")

    PAGE_W = 841.89
    PAGE_H = 595.28

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(PAGE_W, PAGE_H))

    # --- CALIBRAZIONE GEOMETRICA GRIGLIA LANDSCAPE ---
    # Centratura orizzontale delle 31 colonne
    X_COL_1_START = 141.0
    COL_W = 20.10
    X_TOT_COL = 787.5

    def get_cx(d_idx: int) -> float:
        return X_COL_1_START + (d_idx - 1) * COL_W + (COL_W / 2.0)

    # Coordinate verticali Y (dal basso verso l'alto, 0..595)
    Y_MESE_TEXT = 544.0
    Y_ANNO_TEXT = 524.0
    Y_ROW_GIORNO_SETT = 507.0
    Y_ROW_EQUIPAGGIO = 491.0
    Y_ROW_DALLE = 475.0
    Y_ROW_ALLE = 460.0
    Y_ROW_NOTTURNA = 371.0     # Riga 5 Maggiorazione Notturna
    Y_ROW_NAVIGAZIONE = 355.0   # Riga 6 Indennità Navigazione
    Y_ROW_FESTIVO = 324.0       # Riga 8 Festivo
    Y_ROW_BUONI_PASTO = 217.5   # Riga 15 Buoni pasto

    # 1. Mascheratura del vecchio "2022" prestampato e scrittura Anno / Mese
    c.setFillColorRGB(1, 1, 1)  # Bianco
    # Rettangolo bianco di copertura sopra la cella dell'anno
    c.rect(48.0, 520.0, 52.0, 14.0, fill=1, stroke=0)

    c.setFillColorRGB(0, 0, 0)  # Nero
    c.setStrokeColorRGB(0, 0, 0)

    c.setFont("Helvetica-Bold", 10.0)
    nome_mese = MESI_MAIUSCOLO[month]
    c.drawString(45.0, Y_MESE_TEXT, nome_mese)

    c.setFont("Helvetica-Bold", 9.5)
    c.drawCentredString(74.0, Y_ANNO_TEXT, str(year))

    # 2. Elaborazione giorni del mese
    _, num_days = calendar.monthrange(year, month)

    tot_notturna = 0
    tot_navigazione = 0
    tot_festivo = 0
    tot_buoni_pasto = 0

    for day in range(1, 32):
        cx = get_cx(day)

        if day > num_days:
            # Giorno inesistente: linea diagonale di sbarramento
            c.setLineWidth(0.7)
            col_left = X_COL_1_START + (day - 1) * COL_W + 1.0
            col_right = col_left + COL_W - 2.0
            c.line(col_left, Y_ROW_GIORNO_SETT + 8.0, col_right, Y_ROW_BUONI_PASTO - 6.0)
            continue

        target_date = datetime.date(year, month, day)
        shift = get_shift_for_crew(crew_num, target_date)
        is_hol, _, _ = get_holiday_type(target_date)
        stato = shift.get("stato", "")

        # A. Lettera giorno della settimana
        giorno_lett = GIORNI_SETT_LETTERE[target_date.weekday()]
        c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(cx, Y_ROW_GIORNO_SETT, giorno_lett)

        # Ellisse sottile sui festivi
        if is_hol:
            c.setLineWidth(0.6)
            c.ellipse(cx - 5.5, Y_ROW_GIORNO_SETT - 2.5, cx + 5.5, Y_ROW_GIORNO_SETT + 8.5)

        # B. Equipaggio
        if stato.startswith("R"):
            # Riserva: 'R' piccola in alto a sinistra della casella
            c.setFont("Helvetica-Bold", 5.5)
            c.drawString(cx - 6.5, Y_ROW_EQUIPAGGIO + 2.5, "R")
        elif stato in ["20", "08", "08:20"]:
            # Servizio effettivo: numero equipaggio centrato
            c.setFont("Helvetica-Bold", 8.0)
            c.drawCentredString(cx, Y_ROW_EQUIPAGGIO, str(crew_num))

        # C. Orari Dalle / Alle e Competenze
        dalle_str = ""
        alle_str = ""
        val_notturna = None
        val_navigazione = None
        val_festivo = None
        val_buono = None

        if stato == "20":
            # Montante Notte: 20:00 - 24:00
            dalle_str = "20"
            alle_str = "24"
            val_notturna = 4
            val_navigazione = 4
            val_buono = 1
            if is_hol:
                val_festivo = 1
        elif stato == "08":
            # Smontante Notte: 00:00 - 08:00
            dalle_str = "00"
            alle_str = "08"
            val_notturna = 6
            val_navigazione = 8
            val_buono = 1
            if is_hol:
                val_festivo = 1
        elif stato == "08:20":
            # Diurno: 08:00 - 20:00
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

        # 5. Maggiorazione Notturna
        if val_notturna is not None:
            c.drawCentredString(cx, Y_ROW_NOTTURNA, str(val_notturna))
            tot_notturna += val_notturna

        # 6. Indennità Navigazione
        if val_navigazione is not None:
            c.drawCentredString(cx, Y_ROW_NAVIGAZIONE, str(val_navigazione))
            tot_navigazione += val_navigazione

        # 8. Festivo
        if val_festivo is not None:
            c.drawCentredString(cx, Y_ROW_FESTIVO, str(val_festivo))
            tot_festivo += val_festivo

        # 15. Buoni pasto
        if val_buono is not None:
            c.drawCentredString(cx, Y_ROW_BUONI_PASTO, str(val_buono))
            tot_buoni_pasto += val_buono

    # 3. Totali colonna destra
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

    # 4. Fusione vettoriale e orientamento Landscape nativo
    overlay_reader = PdfReader(packet)
    overlay_page = overlay_reader.pages[0]

    template_reader = PdfReader(template_path)
    base_page = template_reader.pages[0]

    orig_w = float(base_page.mediabox.width)
    orig_h = float(base_page.mediabox.height)

    # Se il template originale è memorizzato in Portrait, ruota di 90° in Landscape
    if orig_h > orig_w:
        base_page.rotate(90)

    base_page.merge_page(overlay_page)

    writer = PdfWriter()
    final_page = writer.add_blank_page(width=PAGE_W, height=PAGE_H)
    final_page.merge_page(base_page)

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)

    return output_stream.getvalue()
