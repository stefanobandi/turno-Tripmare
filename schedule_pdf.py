import io
import datetime
import calendar
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from engine import get_shift_for_crew, get_holiday_type

def generate_schedule_bn_pdf(dates_to_show, crews_to_render, title_pdf, is_color=False):
    """
    Genera un PDF di una singola pagina (o tabella) per le date specificate.
    Se is_color=True, usa i colori della web app, altrimenti stampa in B/N ottimizzato.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1*cm,
        bottomMargin=1*cm
    )
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=1,
        spaceAfter=12
    )

    elements.append(Paragraph(title_pdf, title_style))

    # Costruzione Dati Tabella
    data = []
    
    # RIGA 1: Numeri del giorno
    row_days = ["Eq."]
    for d in dates_to_show:
        row_days.append(d.strftime("%d"))
    data.append(row_days)

    # RIGA 2: Nomi dei giorni
    day_names_it = ["lu", "ma", "me", "gi", "ve", "sa", "do"]
    row_day_names = [""]
    for d in dates_to_show:
        row_day_names.append(day_names_it[d.weekday()])
    data.append(row_day_names)

    # RIGHE EQUIPAGGI
    for c_num in crews_to_render:
        label = f"Eq. {c_num} 🎱" if c_num == 8 else f"Eq. {c_num}"
        row = [label]
        for d in dates_to_show:
            shift = get_shift_for_crew(c_num, d)
            mezzo = shift["mezzo"]
            stato = shift["stato"]
            
            if mezzo:
                cell_text = f"{mezzo}\n{stato}"
            else:
                cell_text = stato
            row.append(cell_text)
        data.append(row)

    # Impostazione layout base tabella
    num_cols = len(dates_to_show) + 1
    # La prima colonna (Eq.) è più larga, le altre calcolate equamente
    avail_width = landscape(A4)[0] - 2*cm
    col_w = (avail_width - 2.5*cm) / (num_cols - 1)
    col_widths = [2.5*cm] + [col_w] * (num_cols - 1)

    t = Table(data, colWidths=col_widths, repeatRows=2)

    # Stile base tabella (B/N o Colori condizionato per celle specifiche)
    base_style = [
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('FONTNAME', (0,0), (-1,1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,0), (-1,1), colors.lightgrey if not is_color else colors.whitesmoke),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey if not is_color else colors.whitesmoke),
    ]

    # Applichiamo gli stili condizionali (Festivi, Riposi)
    today_date = datetime.date.today()
    for col_idx, d in enumerate(dates_to_show):
        c = col_idx + 1
        is_hol, is_semi, _ = get_holiday_type(d)
        is_today = (d == today_date)

        # Intestazione Colonne
        if is_color:
            if is_hol:
                base_style.append(('BACKGROUND', (c, 0), (c, 1), colors.HexColor("#fecaca"))) # Rosso chiaro
            elif is_semi:
                base_style.append(('BACKGROUND', (c, 0), (c, 1), colors.HexColor("#fed7aa"))) # Arancione/Salmone chiaro
        else:
            if is_hol or is_semi:
                # Nel B/N usiamo un tratto più spesso per la testata
                base_style.append(('BOX', (c, 0), (c, 1), 1.5, colors.black))
        
        if is_today:
             base_style.append(('BOX', (c, 0), (c, -1), 1.5, colors.blue if is_color else colors.black))

        # Celle Dati
        for row_idx, c_num in enumerate(crews_to_render):
            r = row_idx + 2
            shift = get_shift_for_crew(c_num, d)
            stato = shift["stato"]

            if is_color:
                if stato == "L":
                    base_style.append(('BACKGROUND', (c, r), (c, r), colors.HexColor("#dcfce7"))) # Verde L
                elif stato in ["L1", "L2", "L3"]:
                    base_style.append(('BACKGROUND', (c, r), (c, r), colors.HexColor("#fef9c3"))) # Giallo L disp
                elif stato.startswith("R"):
                    base_style.append(('BACKGROUND', (c, r), (c, r), colors.HexColor("#e2e8f0"))) # Grigio R
                else:
                    base_style.append(('BACKGROUND', (c, r), (c, r), colors.white)) # Lavoro bianco
            else:
                # Se è B/N non impostiamo sfondi per risparmiare inchiostro, il nero standard basta
                pass

    t.setStyle(TableStyle(base_style))
    elements.append(t)
    
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def generate_annual_schedule_pdf(year: int, crews_to_render: list, is_color: bool = False):
    """
    Genera un PDF di 12 pagine (da Gennaio a Dicembre) per l'anno specificato.
    Ciascuna pagina formatta un singolo mese, esattamente come la schermata Mese Completo.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1*cm,
        bottomMargin=1*cm
    )
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=1,
        spaceAfter=12
    )
    
    mesi_italiano = [
        "", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]
    day_names_it = ["lu", "ma", "me", "gi", "ve", "sa", "do"]
    today_date = datetime.date.today()

    for month in range(1, 13):
        title_pdf = f"Turno Tripmare - {mesi_italiano[month]} {year}"
        elements.append(Paragraph(title_pdf, title_style))
        
        _, num_days = calendar.monthrange(year, month)
        dates_to_show = [datetime.date(year, month, day) for day in range(1, num_days + 1)]
        
        data = []
        # RIGA 1: Numeri del giorno
        row_days = ["Eq."]
        for d in dates_to_show:
            row_days.append(d.strftime("%d"))
        data.append(row_days)

        # RIGA 2: Nomi dei giorni
        row_day_names = [""]
        for d in dates_to_show:
            row_day_names.append(day_names_it[d.weekday()])
        data.append(row_day_names)

        # RIGHE EQUIPAGGI
        for c_num in crews_to_render:
            label = f"Eq. {c_num} 🎱" if c_num == 8 else f"Eq. {c_num}"
            row = [label]
            for d in dates_to_show:
                shift = get_shift_for_crew(c_num, d)
                mezzo = shift["mezzo"]
                stato = shift["stato"]
                
                if mezzo:
                    cell_text = f"{mezzo}\n{stato}"
                else:
                    cell_text = stato
                row.append(cell_text)
            data.append(row)

        num_cols = len(dates_to_show) + 1
        avail_width = landscape(A4)[0] - 2*cm
        col_w = (avail_width - 2.5*cm) / (num_cols - 1)
        col_widths = [2.5*cm] + [col_w] * (num_cols - 1)

        t = Table(data, colWidths=col_widths, repeatRows=2)

        base_style = [
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('FONTNAME', (0,0), (-1,1), 'Helvetica-Bold'),
            ('BACKGROUND', (0,0), (-1,1), colors.lightgrey if not is_color else colors.whitesmoke),
            ('BACKGROUND', (0,0), (0,-1), colors.lightgrey if not is_color else colors.whitesmoke),
        ]

        for col_idx, d in enumerate(dates_to_show):
            c = col_idx + 1
            is_hol, is_semi, _ = get_holiday_type(d)
            is_today = (d == today_date)

            if is_color:
                if is_hol:
                    base_style.append(('BACKGROUND', (c, 0), (c, 1), colors.HexColor("#fecaca")))
                elif is_semi:
                    base_style.append(('BACKGROUND', (c, 0), (c, 1), colors.HexColor("#fed7aa")))
            else:
                if is_hol or is_semi:
                    base_style.append(('BOX', (c, 0), (c, 1), 1.5, colors.black))
            
            if is_today:
                 base_style.append(('BOX', (c, 0), (c, -1), 1.5, colors.blue if is_color else colors.black))

            for row_idx, c_num in enumerate(crews_to_render):
                r = row_idx + 2
                shift = get_shift_for_crew(c_num, d)
                stato = shift["stato"]

                if is_color:
                    if stato == "L":
                        base_style.append(('BACKGROUND', (c, r), (c, r), colors.HexColor("#dcfce7")))
                    elif stato in ["L1", "L2", "L3"]:
                        base_style.append(('BACKGROUND', (c, r), (c, r), colors.HexColor("#fef9c3")))
                    elif stato.startswith("R"):
                        base_style.append(('BACKGROUND', (c, r), (c, r), colors.HexColor("#e2e8f0")))
                    else:
                        base_style.append(('BACKGROUND', (c, r), (c, r), colors.white))

        t.setStyle(TableStyle(base_style))
        elements.append(t)
        
        # Aggiungiamo un'interruzione di pagina nativa di ReportLab dopo ogni mese (tranne Dicembre)
        if month < 12:
            elements.append(PageBreak())

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
