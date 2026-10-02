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

# Indici nel ciclo a 18 giorni per gli stati di rientro
CYCLE_RETURN_INDICES = {
    "L1": 4,   # Giorno 5
    "L2": 10,  # Giorno 11
    "L3": 16,  # Giorno 17
}

# Matrice esatta per Tranche (0=sett. 1-7, 1=sett. 8-14, 2=sett. 15-21)
# e posizione nella terzina (0=primo, 1=secondo, 2=terzo):
# formato: (tipo_riserva, stato_rientro)
TRANCHE_CONFIG = [
    # Tranche 0 (Settimane 1-7)
    [("R1", "L1"), ("R2", "L3"), ("R3", "L2")],
    # Tranche 1 (Settimane 8-14)
    [("R2", "L2"), ("R3", "L1"), ("R1", "L3")],
    # Tranche 2 (Settimane 15-21)
    [("R3", "L3"), ("R1", "L2"), ("R2", "L1")],
]

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
    
    # Ancoraggio verificato per Equipaggio 8 a Lunedì 12 Gennaio 2026:
    # Lun 12 Gen è 08:20 sul mezzo 1 -> Giorno 3 del ciclo base (indice 2)
    ANCHOR_EQ8_START_IDX = 2
    
    for crew_num in range(1, 22):
        terzina_num = ((crew_num - 1) // 3) + 1  # Terzina da 1 a 7
        pos_in_terzina = (crew_num - 1) % 3     # 0 (primo), 1 (secondo), 2 (terzo)
        
        full_timeline = [None] * (21 * 7)
        
        # 1. Assegna le 3 settimane di riserva e registra il tipo e lo stato di rientro
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
        
        # 2. Propaga il ciclo lavorativo di 18 giorni
        if crew_num == 8:
            cycle_cursor = ANCHOR_EQ8_START_IDX
            for day_abs in range(21 * 7):
                w = day_abs // 7
                if w in reserve_events:
                    continue
                # Se è il lunedì successivo a una settimana di riserva, applica il rientro esatto
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
            # Per tutti gli altri equipaggi si propaga a partire da ciascun rientro post-riserva
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
                        
        # 3. Popola la matrice accessibile dall'interfaccia
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
