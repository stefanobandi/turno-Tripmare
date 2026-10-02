import datetime

# Data di ancoraggio certa verificata dalla matrice
ANCHOR_DATE = datetime.date(2026, 1, 12)  # Lunedì 12 Gennaio 2026 = Settimana 1 (indice 0)

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

# Indici di rientro nel ciclo di 18 giorni dopo la settimana di riserva:
# - Da R1 si rientra su L3 (indice 16)
# - Da R2 si rientra su L2 (indice 10)
# - Da R3 si rientra su L1 (indice 4)
RESERVE_RETURN_INDICES = {
    "R1": 16,  # L3
    "R2": 10,  # L2
    "R3": 4,   # L1
}

def get_week_index(target_date: datetime.date) -> int:
    """
    Restituisce l'indice della settimana da 0 a 20 (Settimane 1..21)
    rispetto al lunedì di ancoraggio.
    """
    target_monday = target_date - datetime.timedelta(days=target_date.weekday())
    delta_days = (target_monday - ANCHOR_DATE).days
    delta_weeks = delta_days // 7
    return delta_weeks % 21

def build_21week_schedule_matrix() -> dict:
    """
    Costruisce l'intera matrice deterministica per i 21 equipaggi lungo le 21 settimane.
    Chiave: (crew_num, week_idx, day_idx) dove day_idx 0=Lun, 6=Dom.
    """
    matrix = {}
    
    # Rotazione dei ruoli di riserva per le 3 tranche da 7 settimane:
    # Posizione nella terzina: 0 (primo), 1 (secondo), 2 (terzo)
    role_rotation = [
        ["R1", "R2", "R3"],  # Tranche 1 (sett. 1-7)
        ["R2", "R3", "R1"],  # Tranche 2 (sett. 8-14)
        ["R3", "R1", "R2"]   # Tranche 3 (sett. 15-21)
    ]
    
    # Stato iniziale certo per l'Equipaggio 8 a Lunedì 12 Gennaio 2026:
    # Lunedì 12 Gennaio è 08:20 sul mezzo 1 -> Giorno 3 del ciclo base (indice 2)
    ANCHOR_EQ8_START_IDX = 2
    
    for crew_num in range(1, 22):
        terzina_num = ((crew_num - 1) // 3) + 1  # Terzina 1..7
        pos_in_terzina = (crew_num - 1) % 3     # 0 (primo), 1 (secondo), 2 (terzo)
        
        full_timeline = [None] * (21 * 7)
        
        # 1. Assegna le 3 settimane di riserva per questa terzina (settimane w: 0..20)
        # Terzina 1 va in riserva alla settimana 0 (Settimana 1), poi 7 (Settimana 8), 14 (Settimana 15)
        # Terzina 2 va in riserva alla settimana 1 (Settimana 2), ecc.
        # Terzina 3 va in riserva alla settimana 2 (Settimana 3), ecc.
        res_weeks_info = {}
        for tranche in range(3):
            w_idx = (terzina_num - 1) + tranche * 7
            r_type = role_rotation[tranche][pos_in_terzina]
            res_weeks_info[w_idx] = r_type
            start_day = w_idx * 7
            for d in range(7):
                full_timeline[start_day + d] = {"mezzo": None, "stato": r_type}
        
        # 2. Per l'Equipaggio 8, sappiamo che parte a w_idx=0 con indice ANCHOR_EQ8_START_IDX
        if crew_num == 8:
            cycle_cursor = ANCHOR_EQ8_START_IDX
            for day_abs in range(21 * 7):
                w = day_abs // 7
                if w in res_weeks_info:
                    # Settimana di riserva: il ciclo di lavoro non avanza qui
                    continue
                # Se è il lunedì successivo a una settimana di riserva, il ciclo rientra da RESERVE_RETURN_INDICES
                if day_abs % 7 == 0 and ((w - 1) % 21) in res_weeks_info:
                    prev_res_type = res_weeks_info[(w - 1) % 21]
                    cycle_cursor = RESERVE_RETURN_INDICES[prev_res_type]
                
                step = BASE_CYCLE_18[cycle_cursor % 18]
                full_timeline[day_abs] = {
                    "mezzo": step["mezzo"],
                    "stato": step["stato"]
                }
                cycle_cursor += 1
        else:
            # Per gli altri equipaggi, propaghiamo partendo dal rientro della loro prima riserva
            for w_res, r_type in sorted(res_weeks_info.items()):
                next_mon = (w_res + 1) * 7
                cycle_cursor = RESERVE_RETURN_INDICES[r_type]
                for d_off in range(6 * 7):
                    curr_d = (next_mon + d_off) % (21 * 7)
                    if full_timeline[curr_d] is None:
                        step = BASE_CYCLE_18[cycle_cursor % 18]
                        full_timeline[curr_d] = {
                            "mezzo": step["mezzo"],
                            "stato": step["stato"]
                        }
                        cycle_cursor += 1
                        
        # 3. Mappa su matrix
        for w in range(21):
            for d in range(7):
                day_total = w * 7 + d
                matrix[(crew_num, w, d)] = full_timeline[day_total]
                
    return matrix

SCHEDULE_MATRIX = build_21week_schedule_matrix()

def get_shift_for_crew(crew_num: int, target_date: datetime.date) -> dict:
    """
    Restituisce il turno esatto per qualsiasi data ed equipaggio interrogando la matrice.
    """
    week_idx = get_week_index(target_date)
    day_idx = target_date.weekday()
    return SCHEDULE_MATRIX.get((crew_num, week_idx, day_idx), {
        "mezzo": None,
        "stato": "ND"
    })
