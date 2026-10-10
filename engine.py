import datetime

# Data di ancoraggio certa (verificata dalla matrice a 21 settimane)
# Lunedì 12 Gennaio 2026 = Lunedì della Settimana 1 (indice 0 internamente)
ANCHOR_DATE = datetime.date(2026, 1, 12)

# Ciclo Base deterministico di 18 giorni (indicizzato da 0 a 17)
BASE_CYCLE_18 = [
    # Blocco A (Mezzi 1 e 3)
    {"giorno_ciclo": 1,  "blocco": "A", "mezzo": 1,    "stato": "20"},      # idx 0
    {"giorno_ciclo": 2,  "blocco": "A", "mezzo": 1,    "stato": "08"},      # idx 1
    {"giorno_ciclo": 3,  "blocco": "A", "mezzo": 1,    "stato": "08:20"},   # idx 2
    {"giorno_ciclo": 4,  "blocco": "A", "mezzo": 3,    "stato": "08:20"},   # idx 3
    {"giorno_ciclo": 5,  "blocco": "A", "mezzo": None, "stato": "L1"},      # idx 4
    {"giorno_ciclo": 6,  "blocco": "A", "mezzo": None, "stato": "L"},       # idx 5
    # Blocco B (Mezzi 2 e 4)
    {"giorno_ciclo": 7,  "blocco": "B", "mezzo": 2,    "stato": "20"},      # idx 6
    {"giorno_ciclo": 8,  "blocco": "B", "mezzo": 2,    "stato": "08"},      # idx 7
    {"giorno_ciclo": 9,  "blocco": "B", "mezzo": 2,    "stato": "08:20"},   # idx 8
    {"giorno_ciclo": 10, "blocco": "B", "mezzo": 4,    "stato": "08:20"},   # idx 9
    {"giorno_ciclo": 11, "blocco": "B", "mezzo": None, "stato": "L2"},      # idx 10
    {"giorno_ciclo": 12, "blocco": "B", "mezzo": None, "stato": "L"},       # idx 11
    # Blocco C (Mezzi 3 e 4)
    {"giorno_ciclo": 13, "blocco": "C", "mezzo": 3,    "stato": "20"},      # idx 12
    {"giorno_ciclo": 14, "blocco": "C", "mezzo": 3,    "stato": "08"},      # idx 13
    {"giorno_ciclo": 15, "blocco": "C", "mezzo": 4,    "stato": "20"},      # idx 14
    {"giorno_ciclo": 16, "blocco": "C", "mezzo": 4,    "stato": "08"},      # idx 15
    {"giorno_ciclo": 17, "blocco": "C", "mezzo": None, "stato": "L3"},      # idx 16
    {"giorno_ciclo": 18, "blocco": "C", "mezzo": None, "stato": "L"},       # idx 17
]

# Indici nel ciclo base per gli stati di rientro
CYCLE_RETURN_INDICES = {
    "L1": 4,   # Giorno 5
    "L2": 10,  # Giorno 11
    "L3": 16,  # Giorno 17
}

# Rotazione dei ruoli e dei rientri per le 3 tranche da 7 settimane
# Posizione terzina: 0 (primo equipaggio), 1 (secondo), 2 (terzo)
# Formato tupla: (tipo_riserva, stato_rientro)
TRANCHE_CONFIG = [
    # Tranche 0 (Settimane 1-7)
    [("R1", "L1"), ("R2", "L3"), ("R3", "L2")],
    # Tranche 1 (Settimane 8-14)
    [("R2", "L2"), ("R3", "L1"), ("R1", "L3")],
    # Tranche 2 (Settimane 15-21)
    [("R3", "L3"), ("R1", "L2"), ("R2", "L1")],
]

def calculate_easter(year: int) -> datetime.date:
    """
    Calcolo astronomico della domenica di Pasqua tramite algoritmo di Butcher/Meeus.
    Valido per qualsiasi anno gregoriano.
    """
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime.date(year, month, day)

def get_holiday_type(target_date: datetime.date) -> tuple:
    """
    Determina se una data è Festiva (rosso pieno), Semifestiva (rosso tenue) o Ordinaria.
    Restituisce una tupla: (is_holiday, is_semiholiday, nome_festivita)
    """
    year = target_date.year
    month = target_date.month
    day = target_date.day
    weekday = target_date.weekday()  # 6 = Domenica
    
    # 1. Festività fisse CCNL (incluse San Giusto il 3 nov e Unità Nazionale il 4 nov)
    fixed_holidays = {
        (1, 1): "Capodanno",
        (1, 6): "Epifania",
        (4, 25): "Liberazione",
        (5, 1): "Festa del Lavoro",
        (6, 2): "Festa della Repubblica",
        (8, 15): "Assunzione",
        (11, 1): "Ognissanti",
        (11, 3): "San Giusto",
        (11, 4): "Unità Nazionale",
        (12, 8): "Immacolata Concezione",
        (12, 25): "Natale",
        (12, 26): "Santo Stefano",
    }
    
    # 2. Festività e semifestivi mobili (Pasqua e Pasquetta, Sabato Santo)
    easter = calculate_easter(year)
    easter_monday = easter + datetime.timedelta(days=1)
    easter_eve = easter - datetime.timedelta(days=1)
    
    # Controllo Festivi (Rosso Pieno)
    if (month, day) in fixed_holidays:
        return (True, False, fixed_holidays[(month, day)])
    if target_date == easter:
        return (True, False, "Pasqua")
    if target_date == easter_monday:
        return (True, False, "Pasquetta")
    if weekday == 6:
        return (True, False, "Domenica")
        
    # Controllo Semifestivi (Rosso Tenue)
    if target_date == easter_eve:
        return (False, True, "Vigilia di Pasqua")
    if month == 12 and day == 24:
        return (False, True, "Vigilia di Natale")
        
    return (False, False, "")

def get_week_index(target_date: datetime.date) -> int:
    """
    Restituisce l'indice della settimana da 0 a 20 rispetto all'ancora.
    """
    target_monday = target_date - datetime.timedelta(days=target_date.weekday())
    delta_days = (target_monday - ANCHOR_DATE).days
    delta_weeks = delta_days // 7
    return delta_weeks % 21

def build_21week_schedule_matrix() -> dict:
    """
    Costruisce l'intera matrice per i 21 equipaggi lungo le 21 settimane (147 giorni).
    Chiave: (crew_num, week_idx, day_idx)
    """
    matrix = {}
    ANCHOR_EQ8_START_IDX = 2  # Equipaggio 8 inizia a Lun 12 Gen 2026 dal Giorno 3 (indice 2)
    
    for crew_num in range(1, 22):
        terzina_num = ((crew_num - 1) // 3) + 1  # 1..7
        pos_in_terzina = (crew_num - 1) % 3     # 0..2
        full_timeline = [None] * (21 * 7)
        
        # 1. Configurazione delle 3 settimane di riserva
        reserve_events = {}
        for tranche in range(3):
            w_idx = (terzina_num - 1) + tranche * 7
            r_type, return_state = TRANCHE_CONFIG[tranche][pos_in_terzina]
            reserve_events[w_idx] = {
                "tipo_riserva": r_type,
                "rientro_stato": return_state,
                "rientro_idx": CYCLE_RETURN_INDICES[return_state]
            }
            start_day = w_idx * 7
            for d in range(7):
                full_timeline[start_day + d] = {"mezzo": None, "stato": r_type}
        
        # 2. Propagazione ciclo
        if crew_num == 8:
            cycle_cursor = ANCHOR_EQ8_START_IDX
            for day_abs in range(21 * 7):
                w = day_abs // 7
                if w in reserve_events:
                    continue
                if day_abs % 7 == 0 and ((w - 1) % 21) in reserve_events:
                    prev_res = reserve_events[(w - 1) % 21]
                    cycle_cursor = prev_res["rientro_idx"]
                
                step = BASE_CYCLE_18[cycle_cursor % 18]
                full_timeline[day_abs] = {
                    "mezzo": step["mezzo"],
                    "stato": step["stato"]
                }
                cycle_cursor += 1
        else:
            for w_res, res_info in sorted(reserve_events.items()):
                next_mon = (w_res + 1) * 7
                cycle_cursor = res_info["rientro_idx"]
                for d_off in range(6 * 7):
                    curr_d = (next_mon + d_off) % (21 * 7)
                    if full_timeline[curr_d] is None:
                        step = BASE_CYCLE_18[cycle_cursor % 18]
                        full_timeline[curr_d] = {
                            "mezzo": step["mezzo"],
                            "stato": step["stato"]
                        }
                        cycle_cursor += 1
                        
        # 3. Inserimento in matrice
        for w in range(21):
            for d in range(7):
                day_total = w * 7 + d
                matrix[(crew_num, w, d)] = full_timeline[day_total]
                
    return matrix

SCHEDULE_MATRIX = build_21week_schedule_matrix()

def get_shift_for_crew(crew_num: int, target_date: datetime.date) -> dict:
    """
    Restituisce il turno e lo stato festivo per una data ed equipaggio specifici.
    """
    week_idx = get_week_index(target_date)
    day_idx = target_date.weekday()
    shift = SCHEDULE_MATRIX.get((crew_num, week_idx, day_idx), {
        "mezzo": None,
        "stato": "ND"
    }).copy()
    
    is_holiday, is_semiholiday, holiday_name = get_holiday_type(target_date)
    shift["is_holiday"] = is_holiday
    shift["is_semiholiday"] = is_semiholiday
    shift["holiday_name"] = holiday_name
    return shift

def validate_day_integrity(target_date: datetime.date) -> dict:
    """
    Valida la quadratura esatta di tutti i 21 equipaggi per una specifica data.
    Regole richieste:
    - Esattamente 4 equipaggi montanti notte ('20'), uno per ciascun mezzo [1, 2, 3, 4]
    - Esattamente 4 equipaggi smontanti notte ('08'), uno per ciascun mezzo [1, 2, 3, 4]
    - Esattamente 4 equipaggi diurni ('08:20'), uno per ciascun mezzo [1, 2, 3, 4]
    - Esattamente 3 equipaggi liberi ('L')
    - Esattamente 1 equipaggio in disponibilità 'L1', 1 in 'L2', 1 in 'L3'
    - Esattamente 1 equipaggio in riserva 'R1', 1 in 'R2', 1 in 'R3'
    """
    errors = []
    counts = {
        "20": 0,
        "08": 0,
        "08:20": 0,
        "L": 0,
        "L1": 0,
        "L2": 0,
        "L3": 0,
        "R1": 0,
        "R2": 0,
        "R3": 0,
        "altro": 0
    }
    
    mezzi_assegnati = {
        "20": [],
        "08": [],
        "08:20": []
    }
    
    for crew_num in range(1, 22):
        shift = get_shift_for_crew(crew_num, target_date)
        st_val = shift.get("stato")
        m_val = shift.get("mezzo")
        
        if st_val in counts:
            counts[st_val] += 1
        else:
            counts["altro"] += 1
            errors.append(f"Eq. {crew_num}: stato imprevisto '{st_val}'")
            
        if st_val in mezzi_assegnati:
            if m_val is None:
                errors.append(f"Eq. {crew_num} in turno '{st_val}' senza mezzo assegnato")
            else:
                mezzi_assegnati[st_val].append((crew_num, m_val))
                
    expected_counts = {
        "20": 4,
        "08": 4,
        "08:20": 4,
        "L": 3,
        "L1": 1,
        "L2": 1,
        "L3": 1,
        "R1": 1,
        "R2": 1,
        "R3": 1
    }
    
    for key, exp_val in expected_counts.items():
        if counts[key] != exp_val:
            errors.append(f"Stato '{key}': trovati {counts[key]} equipaggi invece di {exp_val}")
            
    for shift_type in ["20", "08", "08:20"]:
        assigned_m = [item[1] for item in mezzi_assegnati[shift_type]]
        sorted_m = sorted(assigned_m)
        if sorted_m != [1, 2, 3, 4]:
            errors.append(f"Copertura mezzi anomala per turno '{shift_type}': mezzi rilevati {sorted_m} (attesi [1, 2, 3, 4])")
            
    return {
        "date": target_date,
        "is_valid": len(errors) == 0,
        "errors": errors,
        "counts": counts
    }

def validate_schedule_period(dates_list: list) -> dict:
    """
    Esegue la validazione su un elenco di date (es. mese visualizzato o intero ciclo).
    """
    total_days = len(dates_list)
    invalid_days = []
    
    for d in dates_list:
        res = validate_day_integrity(d)
        if not res["is_valid"]:
            invalid_days.append(res)
            
    return {
        "total_days": total_days,
        "is_valid": len(invalid_days) == 0,
        "invalid_count": len(invalid_days),
        "invalid_days": invalid_days
    }

def generate_ics_calendar(crew_num: int, dates_list: list) -> str:
    """
    Genera una stringa formattata standard iCalendar (.ics) per l'equipaggio selezionato.
    Esclude i liberi (L) e gli smontanti (08) già coperti dal montante notte (20:00-08:00).
    """
    now_stamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Tripmare S.p.A.//Turno Rimorchiatori//IT",
        f"X-WR-CALNAME:Turno Tripmare - Eq. {crew_num}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]

    for d in dates_list:
        shift = get_shift_for_crew(crew_num, d)
        mezzo = shift.get("mezzo")
        stato = shift.get("stato")
        
        if stato in ["L", "08"]:
            continue

        dislocazione = f"Rimorchiatore {mezzo} ({'SIOT' if mezzo in [1, 2] else 'PFV/Base'})" if mezzo else ""
        date_str = d.strftime("%Y%m%d")
        next_d_str = (d + datetime.timedelta(days=1)).strftime("%Y%m%d")
        uid = f"tripmare-eq{crew_num}-{date_str}-{stato}@trieste.harbour"

        if stato == "20":
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now_stamp}",
                f"DTSTART:{date_str}T200000",
                f"DTEND:{next_d_str}T080000",
                f"SUMMARY:⚓ Eq.{crew_num} - Notte (20:00 - 08:00)",
                f"DESCRIPTION:Turno Notturno su {dislocazione}",
                f"LOCATION:{dislocazione}",
                "END:VEVENT"
            ])
        elif stato == "08:20":
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now_stamp}",
                f"DTSTART:{date_str}T080000",
                f"DTEND:{date_str}T200000",
                f"SUMMARY:⚓ Eq.{crew_num} - Diurno (08:00 - 20:00)",
                f"DESCRIPTION:Turno Diurno su {dislocazione}",
                f"LOCATION:{dislocazione}",
                "END:VEVENT"
            ])
        elif stato in ["L1", "L2", "L3"]:
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now_stamp}",
                f"DTSTART;VALUE=DATE:{date_str}",
                f"DTEND;VALUE=DATE:{next_d_str}",
                f"SUMMARY:📞 Eq.{crew_num} - Disponibilità {stato}",
                f"DESCRIPTION:Giornata di disponibilità attiva {stato}",
                "END:VEVENT"
            ])
        elif stato.startswith("R"):
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now_stamp}",
                f"DTSTART;VALUE=DATE:{date_str}",
                f"DTEND;VALUE=DATE:{next_d_str}",
                f"SUMMARY:🛡️ Eq.{crew_num} - Riserva {stato}",
                f"DESCRIPTION:Settimana di Riserva ({stato})",
                "END:VEVENT"
            ])

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)
