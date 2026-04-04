import streamlit as st
import json
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Simulatore Andromeda 4.0", layout="wide")

# --- CONFIGURAZIONE MEMORIA ETERNA ---
# Ho aggiunto le virgolette che mancavano per correggere l'errore
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1gfus3uS8C_K-niCduLi_qiB323T82LdWEfyd68MzwWW/edit?gid=0#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)

# Stile grafico "Bando Veneto"
st.markdown("""
    <style>
    .domanda-titolo { font-weight: bold; font-size: 18pt; color: #1E88E5; }
    .quesito-testo { font-size: 16pt; font-style: italic; padding-top: 10px; padding-bottom: 20px; }
    .stRadio p { font-size: 10pt !important; font-style: normal !important; font-weight: normal !important; }
    </style>
""", unsafe_allow_html=True)

def carica_database():
    try:
        with open('database_3000.json', 'r', encoding='utf-8') as f: return json.load(f)
    except:
        st.error("❌ Database JSON non trovato su GitHub!")
        st.stop()

def carica_statistiche():
    try:
        df = conn.read(spreadsheet=URL_FOGLIO, ttl=0)
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
    data = []
    for q_id, val in stats.items():
        data.append({"id": q_id, "corrette": val['corrette'], "errate": val['errate'], "cartella": val['cartella']})
    df = pd.DataFrame(data)
    conn.update(spreadsheet=URL_FOGLIO, data=df)

# --- LOGICA APP ---
db = carica_database()
if 'stats' not in st.session_state:
    st.session_state.stats = carica_statistiche()

# Inizializzazione automatica del foglio Google se vuoto
if not st.session_state.stats:
    with st.spinner("Sincronizzazione con Google Sheets..."):
        for q in db:
            q_id = str(q['id'])
            st.session_state.stats[q_id] = {"corrette": 0, "errate": 0, "cartella": "Calderone"}
        salva_statistiche(st.session_state.stats)
        st.rerun()

# Sidebar: Filtri
st.sidebar.title("⚙️ Filtri Bando")
moduli = sorted(list(set([str(q.get('modulo', 'N/A')) for q in db])))
mod_scelto = st.sidebar.selectbox("Modulo:", ["Tutti"] + moduli)

# Filtro dinamico per Sezione
if mod_scelto == "Tutti":
    sezioni = sorted(list(set([str(q.get('sezione', 'N.S.')) for q in db])))
else:
    sezioni = sorted(list(set([str(q.get('sezione', 'N.S.')) for q in db if str(q.get('modulo')) == mod_scelto])))
sez_scelta = st.sidebar.selectbox("Sezione:", ["Tutte"] + sezioni)

cartelle_disponibili = ["Calderone", "Allenamento", "Campo", "Cassaforte"]
cart_scelta = st.sidebar.selectbox("📂 Cartella:", ["Tutte"] + cartelle_disponibili)

# Applicazione Filtri
domande_filtrate = [q for q in db if 
    (mod_scelto == "Tutti" or str(q.get('modulo')) == mod_scelto) and
    (sez_scelta == "Tutte" or str(q.get('sezione', 'N.S.')) == sez_scelta) and
    (cart_scelta == "Tutte" or st.session_state.stats[str(q['id'])]["cartella"] == cart_scelta)
]

st.sidebar.success(f"🎯 Trovate: {len(domande_filtrate)}")

# Navigazione
if 'indice' not in st.session_state: st.session_state.indice = 0

if not domande_filtrate:
    st.warning("Nessuna domanda trovata con questi filtri.")
    st.stop()

if st.session_state.indice >= len(domande_filtrate): st.session_state.indice = 0

q = domande_filtrate[st.session_state.indice]
q_id = str(q['id'])

# Interfaccia Domanda
st.title("🚀 Andromeda 4.0 - Simulatore Online")
st.markdown("---")

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"<div class='domanda-titolo'>Domanda {q['id']}</div>", unsafe_allow_html=True)
with col2:
    attuale = st.session_state.stats[q_id]["cartella"]
    nuova = st.selectbox("Sposta in:", cartelle_disponibili, index=cartelle_disponibili.index(attuale), key=f"c_{q_id}")
    if nuova != attuale:
        st.session_state.stats[q_id]["cartella"] = nuova
        salva_statistiche(st.session_state.stats)
        st.rerun()

st.markdown(f"<div class='quesito-testo'>{q['testo']}</div>", unsafe_allow_html=True)

scelta = st.radio("Opzioni:", list(q['opzioni'].keys()), format_func=lambda x: f"{x.lower()}) {q['opzioni'][x]}", index=None, key=f"r_{q_id}")

if st.button("Conferma Risposta"):
    if scelta == q['corretta']:
        st.success(f"✅ Esatto! La risposta è {q['corretta'].upper()}")
        st.session_state.stats[q_id]["corrette"] += 1
    else:
        st.error(f"❌ Sbagliato. La risposta corretta era {q['corretta'].upper()}")
        st.session_state.stats[q_id]["errate"] += 1
    salva_statistiche(st.session_state.stats)

st.write("---")
c_prev, c_txt, c_next = st.columns([1, 2, 1])
with c_prev:
    if st.button("⬅️ Indietro") and st.session_state.indice > 0:
        st.session_state.indice -= 1
        st.rerun()
with c_txt:
    st.markdown(f"<div style='text-align: center;'>{st.session_state.indice + 1} / {len(domande_filtrate)}</div>", unsafe_allow_html=True)
with c_next:
    if st.button("Avanti ➡️") and st.session_state.indice < len(domande_filtrate) - 1:
        st.session_state.indice += 1
        st.rerun()
