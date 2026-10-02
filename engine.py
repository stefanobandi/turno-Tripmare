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
# - Dopo R1 si riparte da L3 (Giorno 17 -> indice 16)
# - Dopo R2 si riparte da L2 (Giorno 11 -> indice 10)
# - Dopo R3 si riparte da L1 (Giorno 5 -> indice 4)
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
    
    # Mappatura della rotazione dei ruoli di riserva per le 3 tranche da 7 settimane
    # Posizione nella terzina: 0 (primo), 1 (secondo), 2 (terzo)
    # Tranche: 0 (sett. 1-7), 1 (sett. 8-14), 2 (sett. 15-21)
    role_rotation = [
        ["R1", "R2", "R3"],  # Tranche 0: primo=R1, secondo=R2, terzo=R3
        ["R2", "R3", "R1"],  # Tranche 1: primo=R2, secondo=R3, terzo=R1
        ["R3", "R1", "R2"]   # Tranche 2: primo=R3, secondo=R1, terzo=R2
    ]
    
    for crew_num in range(1, 22):
        terzina_idx = (crew_num - 1) // 3        # Terzina da 0 a 6
        pos_in_terzina = (crew_num - 1) % 3     # 0, 1 o 2
        
        full_timeline = [None] * (21 * 7)
        
        # Le 3 settimane di riserva per questo equipaggio con il relativo tipo dinamico
        reserve_events = []
        for tranche in range(3):
            week_num_idx = terzina_idx + tranche * 7
            tipo_riserva = role_rotation[tranche][pos_in_terzina]
            reserve_events.append((week_num_idx, tipo_riserva))
            
            # Assegna i 7 giorni di riserva
            start_day = week_num_idx * 7
            for d in range(7):
                full_timeline[start_day + d] = {"mezzo": None, "stato": tipo_riserva}
                
        # Propaga il ciclo a 18 giorni partendo dal rientro del lunedì successivo a ciascuna riserva.
        # Il blocco lavorativo dura esattamente 6 settimane (42 giorni).
        for week_num_idx, tipo_riserva in reserve_events:
            next_monday = (week_num_idx + 1) * 7
            return_start_idx = RESERVE_RETURN_INDICES[tipo_riserva]
            cycle_cursor = return_start_idx
            
            for day_offset in range(6 * 7):
                curr_day = (next_monday + day_offset) % (21 * 7)
                step = BASE_CYCLE_18[cycle_cursor % 18]
                full_timeline[curr_day] = {
                    "mezzo": step["mezzo"],
                    "stato": step["stato"]
                }
                cycle_cursor += 1
                
        # Popola la matrice accessibile per l'interfaccia
        for w in range(21):
            for d in range(7):
                day_total = w * 7 + d
                matrix[(crew_num, w, d)] = full_timeline[day_total]
                
    return matrix

# Istanza precalcolata della matrice globale
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
