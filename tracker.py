import streamlit as st
import datetime
from collections import Counter
import firebase_admin
from firebase_admin import credentials, firestore

def init_firebase():
    """Inizializza Firebase Admin SDK utilizzando i secrets di Streamlit."""
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets:
                fb_dict = dict(st.secrets["firebase"])
                cred = credentials.Certificate(fb_dict)
                firebase_admin.initialize_app(cred)
            else:
                return None
        except Exception:
            return None
    try:
        return firestore.client()
    except Exception:
        return None

def log_page_view():
    """Registra una visita alla pagina una sola volta per sessione utente."""
    if st.session_state.get("_logged_page_view", False):
        return

    db = init_firebase()
    if not db:
        return

    try:
        now_ts = datetime.datetime.now(datetime.timezone.utc)
        doc_data = {
            "timestamp": now_ts,
            "data_str": now_ts.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "tipo": "visita"
        }
        db.collection("analytics_visite").add(doc_data)
        st.session_state["_logged_page_view"] = True
    except Exception:
        pass

def log_download(tipo_file: str, dettaglio: str = ""):
    """Registra l'evento di download di un file (PDF, Excel, ICS)."""
    db = init_firebase()
    if not db:
        return

    try:
        now_ts = datetime.datetime.now(datetime.timezone.utc)
        doc_data = {
            "timestamp": now_ts,
            "data_str": now_ts.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "tipo_file": tipo_file,
            "dettaglio": dettaglio
        }
        db.collection("analytics_download").add(doc_data)
    except Exception:
        pass

def get_analytics_summary() -> dict:
    """
    Recupera i dati aggregati da Firestore per la dashboard riservata dell'amministratore.
    """
    db = init_firebase()
    if not db:
        return {"connected": False}

    try:
        # Conteggio visite
        visite_ref = db.collection("analytics_visite")
        visite_docs = list(visite_ref.stream())
        tot_visite = len(visite_docs)

        # Download e dettagli
        dl_ref = db.collection("analytics_download").order_by("timestamp", direction=firestore.Query.DESCENDING)
        dl_docs = list(dl_ref.limit(200).stream())
        tot_download = len(dl_docs)

        tipi_counter = Counter()
        crews_counter = Counter()
        recent_events = []

        for d in dl_docs:
            data = d.to_dict()
            t_file = data.get("tipo_file", "sconosciuto")
            det = data.get("dettaglio", "")
            d_str = data.get("data_str", "")

            tipi_counter[t_file] += 1

            if "Eq." in det:
                parts = det.split("-")[0].strip()
                crews_counter[parts] += 1
            elif "Equipaggio" in det:
                parts = det.split("-")[0].strip()
                crews_counter[parts] += 1

            recent_events.append({
                "Data/Ora (UTC)": d_str,
                "Tipo": t_file,
                "Dettaglio": det
            })

        return {
            "connected": True,
            "tot_visite": tot_visite,
            "tot_download": tot_download,
            "tipi_download": dict(tipi_counter),
            "crews_stats": dict(crews_counter),
            "recent_events": recent_events[:20]
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}
