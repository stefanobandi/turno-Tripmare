import io
import datetime
from reportlab.pdfgen import canvas
from engine import get_shift_for_crew, get_holiday_type

MESI_ITALIANO = [
    "", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
]

GIORNI_SETT_SHORT = ["lu", "ma", "me", "gi", "ve", "sa", "do"]

def generate_schedule_bn_pdf(dates_list: list, crews_list: list, title_desc: str) -> bytes:
    """
    Genera un documento PDF in formato A4 Landscape nativo (842 x 595 pt),
    in Bianco e Nero puro ad alta leggibilità, ottimizzato per la stampa su carta.
    
    Regole grafiche:
    - Nessun colore e nessun riempimento grigio.
    - Riposi (L, L1..L3) e riserve (R1..R3) stampati a carattere normale (no grassetto).
    - Festivi e domeniche indicati con un'ellisse sottile attorno al giorno nella testata.
    - I turni lavorativi mostrano il numero mezzo sopra e l'orario/stato sotto.
    """
    PAGE_W = 841.89
    PAGE_H = 595.28

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(PAGE_W, PAGE_H))

    # Margini del foglio A4
    MARGIN_LEFT = 24.0
    MARGIN_RIGHT = PAGE_W - 24.0
    TABLE_W = MARGIN_RIGHT - MARGIN_LEFT
    MARGIN_TOP = PAGE_H - 24.0

    num_days = len(dates_list)
    num_crews = len(crews_list)

    # 1. Intestazione Titolo
    c.setFont("Helvetica-Bold", 12.0)
    c.drawString(MARGIN_LEFT, MARGIN_TOP - 12.0, "⚓ Proiezione turno Tripmare - Trieste")

    c.setFont("Helvetica", 9.5)
    c.drawRightString(MARGIN_RIGHT, MARGIN_TOP - 12.0, title_desc)

    # 2. Geometria griglia dinamica
    Y_GRID_TOP = MARGIN_TOP - 22.0
    Y_GRID_BOTTOM = 24.0
    TOTAL_GRID_H = Y_GRID_TOP - Y_GRID_BOTTOM

    # Larghezza etichetta equipaggio
    LABEL_COL_W = 54.0 if num_days > 14 else 68.0
    DAY_COL_W = (TABLE_W - LABEL_COL_W) / float(num_days)

    # Altezza righe testata
    H_HEADER_1 = 14.0  # Riga numero giorno
    H_HEADER_2 = 14.0  # Riga lettera giorno
    H_HEADERS = H_HEADER_1 + H_HEADER_2

    # Calcolo altezza singola riga equipaggio
    avail_crew_h = TOTAL_GRID_H - H_HEADERS
    row_crew_h = min(avail_crew_h / float(num_crews), 28.0)
    actual_table_h = H_HEADERS + row_crew_h * num_crews
    y_table_bot = Y_GRID_TOP - actual_table_h

    # Coordinate verticali
    y_h1_bot = Y_GRID_TOP - H_HEADER_1
    y_h2_bot = y_h1_bot - H_HEADER_2

    # Tracciamento linee orizzontali testata
    c.setLineWidth(1.0)
    c.line(MARGIN_LEFT, Y_GRID_TOP, MARGIN_RIGHT, Y_GRID_TOP)
    c.setLineWidth(0.5)
    c.line(MARGIN_LEFT, y_h1_bot, MARGIN_RIGHT, y_h1_bot)
    c.setLineWidth(1.0)
    c.line(MARGIN_LEFT, y_h2_bot, MARGIN_RIGHT, y_h2_bot)

    # Testo angolo in alto a sinistra
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(MARGIN_LEFT + LABEL_COL_W / 2.0, Y_GRID_TOP - 10.0, "Giorno")
    c.drawCentredString(MARGIN_LEFT + LABEL_COL_W / 2.0, y_h1_bot - 10.0, "Eq.")

    # 3. Testata Colonne Giorni
    font_day_size = 7.5 if num_days > 14 else 8.5
    for idx, d in enumerate(dates_list):
        cx = MARGIN_LEFT + LABEL_COL_W + idx * DAY_COL_W + (DAY_COL_W / 2.0)
        is_hol, _, _ = get_holiday_type(d)

        # Riga 1: Numero del giorno
        c.setFont("Helvetica-Bold", font_day_size)
        c.drawCentredString(cx, Y_GRID_TOP - 10.0, str(d.day))

        # Riga 2: Sigla giorno settimana
        day_str = GIORNI_SETT_SHORT[d.weekday()]
        c.setFont("Helvetica-Bold", font_day_size)
        c.drawCentredString(cx, y_h1_bot - 10.0, day_str)

        # Ellisse sui festivi
        if is_hol:
            c.setLineWidth(0.6)
            c.ellipse(cx - 5.5, y_h1_bot - 12.0, cx + 5.5, y_h1_bot - 1.0)

    # 4. Righe Equipaggi e Popolamento Dati
    font_cell_size = 7.0 if (num_crews > 10 or num_days > 21) else 8.0
    c.setLineWidth(0.5)

    for r_idx, c_num in enumerate(crews_list):
        y_top_row = y_h2_bot - r_idx * row_crew_h
        y_bot_row = y_top_row - row_crew_h

        # Bordo inferiore riga
        c.line(MARGIN_LEFT, y_bot_row, MARGIN_RIGHT, y_bot_row)

        # Etichetta equipaggio a sinistra
        c.setFont("Helvetica-Bold", font_cell_size + 0.5)
        eq_label = f"Eq. {c_num}"
        c.drawCentredString(MARGIN_LEFT + LABEL_COL_W / 2.0, y_bot_row + (row_crew_h / 2.0) - 2.5, eq_label)

        # Celle del turno
        for d_idx, d in enumerate(dates_list):
            cx = MARGIN_LEFT + LABEL_COL_W + d_idx * DAY_COL_W + (DAY_COL_W / 2.0)
            shift = get_shift_for_crew(c_num, d)
            stato = shift.get("stato", "")
            mezzo = shift.get("mezzo")

            # Stampa B/N: carattere normale (no grassetto) per riposi e riserve
            if stato == "L":
                c.setFont("Helvetica", font_cell_size)
                c.drawCentredString(cx, y_bot_row + (row_crew_h / 2.0) - 2.5, "L")
            elif stato in ["L1", "L2", "L3"]:
                c.setFont("Helvetica", font_cell_size)
                c.drawCentredString(cx, y_bot_row + (row_crew_h / 2.0) - 2.5, stato)
            elif stato.startswith("R"):
                c.setFont("Helvetica", font_cell_size)
                c.drawCentredString(cx, y_bot_row + (row_crew_h / 2.0) - 2.5, stato)
            else:
                # Turno lavorativo operativo: mezzo sopra, stato sotto
                if mezzo:
                    c.setFont("Helvetica-Bold", font_cell_size)
                    c.drawCentredString(cx, y_bot_row + (row_crew_h / 2.0) + 1.5, str(mezzo))
                    c.setFont("Helvetica", font_cell_size - 0.5)
                    c.drawCentredString(cx, y_bot_row + (row_crew_h / 2.0) - 7.0, stato)
                else:
                    c.setFont("Helvetica", font_cell_size)
                    c.drawCentredString(cx, y_bot_row + (row_crew_h / 2.0) - 2.5, stato)

    # 5. Linee Verticali
    c.setLineWidth(0.4)
    for col_idx in range(1, num_days):
        x_div = MARGIN_LEFT + LABEL_COL_W + col_idx * DAY_COL_W
        c.line(x_div, Y_GRID_TOP, x_div, y_table_bot)

    # Bordo verticale separatore tra etichetta equipaggio e giorni
    c.setLineWidth(1.2)
    c.line(MARGIN_LEFT + LABEL_COL_W, Y_GRID_TOP, MARGIN_LEFT + LABEL_COL_W, y_table_bot)

    # Perimetro esterno marcato
    c.setLineWidth(1.2)
    c.rect(MARGIN_LEFT, y_table_bot, TABLE_W, actual_table_h, stroke=1, fill=0)

    # Didascalia a piè di pagina sobria
    c.setFont("Helvetica", 7.0)
    c.drawString(MARGIN_LEFT, y_table_bot - 10.0, "Tripmare S.p.A. - Turno Operativo Rimorchiatori Trieste (Stampa B/N)")

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
