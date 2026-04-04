import streamlit as st
import json
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Simulatore Andromeda 4.0", layout="wide")

# --- CONFIGURAZIONE GOOGLE SHEETS ---
# Sostituisci il link qui sotto con quello che hai copiato dal tuo foglio Google
URL_FOGLIO = "INCOLLA_QUI_IL_TUO_LINK_DI_GOOGLE_SHEETS"

conn = st.connection("gsheets", type=GSheetsConnection)

def carica_database():
    try:
        with open('database_3000.json', 'r', encoding='utf-8') as f: return json.load(f)
    except:
        st.error("❌ Errore: Database JSON non trovato!")
        st.stop()

def carica_statistiche():
    try:
        df = conn.read(spreadsheet=URL_FOGLIO, ttl=0)
        # Convertiamo il foglio in un dizionario usabile
        stats = {}
        for _, row in df.iterrows():
            stats[str(row['id'])] = {
                "corrette": int(row['corrette']),
                "errate": int(row['errate']),
                "cartella": str(row['cartella'])
            }
        return stats
    except:
        return {}

def salva_statistiche(stats):
    # Trasformiamo il dizionario in una lista per Google Sheets
    data = []
    for q_id, val in stats.items():
        data.append({"id": q_id, "corrette": val['corrette'], "errate": val['errate'], "cartella": val['cartella']})
    df = pd.DataFrame(data)
    conn.update(spreadsheet=URL_FOGLIO, data=df)

# --- AVVIO APP ---
db = carica_database()
if 'stats' not in st.session_state:
    st.session_state.stats = carica_statistiche()

# Se il foglio è vuoto, inizializziamo le 3000 domande
if not st.session_state.stats:
    with st.spinner("Inizializzazione database eterno in corso..."):
        for q in db:
            q_id = str(q['id'])
            st.session_state.stats[q_id] = {"corrette": 0, "errate": 0, "cartella": "Calderone"}
        salva_statistiche(st.session_state.stats)
        st.rerun()

# [IL RESTO DEL TUO CODICE PER FILTRI E DOMANDE RIMANE UGUALE...]
# Nota: ricordati di usare 'st.session_state.stats' invece di 'stats' ovunque nel codice
