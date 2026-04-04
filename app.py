import streamlit as st
import json
import requests

st.set_page_config(page_title="Andromeda 4.0 Online", layout="wide")

# --- COLLANTE CON GOOGLE (APPS SCRIPT) ---
# INCOLLA QUI IL LINK CHE HAI COPIATO DA GOOGLE (quello che inizia con https://script.google.com/...)
URL_MEMORIA = "https://script.google.com/macros/s/AKfycbycL7hgRkaDC0KSMsStCMkU8QZNhkAto5d1eLGDRRecpAoQl6V7ks4A48P-avYo2E6I/exec"

# Stile grafico Bando Veneto
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
        st.error("❌ Errore: File database_3000.json non trovato su GitHub!")
        st.stop()

def carica_statistiche():
    try:
        r = requests.get(URL_MEMORIA)
        dati = r.json()
        stats = {}
        # Saltiamo l'intestazione (riga 0)
        for row in dati[1:]:
            stats[str(row[0])] = {"corrette": int(row[1]), "errate": int(row[2]), "cartella": str(row[3])}
        return stats
    except:
        return {}

def salva_statistiche(stats):
    payload = []
    for q_id, val in stats.items():
        payload.append({"id": q_id, "corrette": val['corrette'], "errate": val['errate'], "cartella": val['cartella']})
    try:
        requests.post(URL_MEMORIA, json=payload)
    except:
        st.error("⚠️ Errore nel salvataggio su Google Fogli.")

# --- INIZIO LOGICA ---
db = carica_database()

if 'stats' not in st.session_state:
    with st.spinner("Sincronizzazione con la memoria eterna..."):
        st.session_state.stats = carica_statistiche()

# Se il foglio è nuovo o vuoto, inizializziamo
if not st.session_state.stats:
    for q in db:
        st.session_state.stats[str(q['id'])] = {"corrette": 0, "errate": 0, "cartella": "Calderone"}

# Sidebar: Filtri
st.sidebar.title("⚙️ Filtri Bando")
moduli = sorted(list(set([str(q.get('modulo', 'N/A')) for q in db])))
mod_scelto = st.sidebar.selectbox("Filtra per Modulo:", ["Tutti"] + moduli)

sezioni = sorted(list(set([str(q.get('sezione', 'N.S.')) for q in db if mod_scelto == "Tutti" or str(q.get('modulo')) == mod_scelto])))
sez_scelta = st.sidebar.selectbox("Filtra per Sezione:", ["Tutte"] + sezioni)

cartelle_disponibili = ["Calderone", "Allenamento", "Campo", "Cassaforte"]
cart_scelta = st.sidebar.selectbox("📂 Filtra per Cartella:", ["Tutte"] + cartelle_disponibili)

# Applicazione Filtri
domande_filtrate = [q for q in db if 
    (mod_scelto == "Tutti" or str(q.get('modulo')) == mod_scelto) and
    (sez_scelta == "Tutte" or str(q.get('sezione', 'N.S.')) == sez_scelta) and
    (cart_scelta == "Tutte" or st.session_state.stats[str(q['id'])]["cartella"] == cart_scelta)
]

st.sidebar.success(f"🎯 Domande trovate: {len(domande_filtrate)}")

# Navigazione
if 'indice' not in st.session_state: st.session_state.indice = 0
if not domande_filtrate:
    st.warning("Nessuna domanda trovata.")
    st.stop()
if st.session_state.indice >= len(domande_filtrate): st.session_state.indice = 0

q = domande_filtrate[st.session_state.indice]
q_id = str(q['id'])

st.title("🚀 Andromeda 4.0 Online")
st.markdown("---")

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"<div class='domanda-titolo'>Domanda {q['id']}</div>", unsafe_allow_html=True)
with col2:
    attuale = st.session_state.stats[q_id]["cartella"]
    nuova = st.selectbox("📂 Sposta in:", cartelle_disponibili, index=cartelle_disponibili.index(attuale), key=f"c_{q_id}")
    if nuova != attuale:
        st.session_state.stats[q_id]["cartella"] = nuova
        salva_statistiche(st.session_state.stats)
        st.rerun()

st.markdown(f"<div class='quesito-testo'>{q['testo']}</div>", unsafe_allow_html=True)

scelta = st.radio("Scegli la risposta:", list(q['opzioni'].keys()), format_func=lambda x: f"{x.lower()}) {q['opzioni'][x]}", index=None, key=f"r_{q_id}")

if st.button("Conferma Risposta"):
    if scelta == q['corretta']:
        st.success(f"✅ Esatto! La risposta corretta è {q['corretta'].upper()}")
        st.session_state.stats[q_id]["corrette"] += 1
    else:
        st.error(f"❌ Sbagliato. La risposta corretta era {q['corretta'].upper()}")
        st.session_state.stats[q_id]["errate"] += 1
    salva_statistiche(st.session_state.stats)

st.write("---")
cp, ct, cn = st.columns([1, 2, 1])
with cp:
    if st.button("⬅️ Indietro") and st.session_state.indice > 0:
        st.session_state.indice -= 1
        st.rerun()
with ct:
    st.markdown(f"<div style='
