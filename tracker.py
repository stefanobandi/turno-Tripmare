import streamlit as st
import datetime
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
