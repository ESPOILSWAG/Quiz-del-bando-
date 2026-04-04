import streamlit as st
import json
import requests

st.set_page_config(page_title="Andromeda 4.0 Online", layout="wide")

# --- CONFIGURAZIONE MEMORIA ETERNA ---
# Incolla qui il tuo link di Google (deve iniziare e finire con le virgolette " ")
URL_MEMORIA = "https://script.google.com/macros/s/AKfycbycL7hgRkaDC0KSMsStCMkU8QZNhkAto5d1eLGDRRecpAoQl6V7ks4A48P-avYo2E6I/exec"

# Stile grafico Bando Veneto
st.markdown("""
<style>
    .domanda-titolo { font-weight: bold; font-size: 18pt; color: #1E88E5; }
    .quesito-testo { font-size: 16pt; font-style: italic; padding-top: 10px; padding-bottom: 20px; }
    .stRadio p { font-size: 10pt !important; }
</style>
""", unsafe_allow_html=True)

def carica_database():
    try:
        with open('database_3000.json', 'r', encoding='utf-8') as f: return json.load(f)
    except:
        st.error("File database_3000.json non trovato su GitHub.")
        st.stop()

def carica_statistiche():
    try:
        r = requests.get(URL_MEMORIA)
        dati = r.json()
        stats = {}
        for row in dati[1:]:
            stats[str(row[0])] = {"corrette": int(row[1]), "errate": int(row[2]), "cartella": str(row[3])}
        return stats
    except: return {}

def salva_statistiche(stats):
    payload = []
    for q_id, val in stats.items():
        payload.append({"id": q_id, "corrette": val['corrette'], "errate": val['errate'], "cartella": val['cartella']})
    try: requests.post(URL_MEMORIA, json=payload)
    except: st.error("Errore connessione Google.")

# --- AVVIO APP ---
db = carica_database()
if 'stats' not in st.session_state:
    st.session_state.stats = carica_statistiche()

if not st.session_state.stats:
    for q in db: st.session_state.stats[str(q['id'])] = {"corrette": 0, "errate": 0, "cartella": "Calderone"}

# Sidebar Filtri
st.sidebar.title("⚙️ Filtri")
moduli = sorted(list(set([str(q.get('modulo', 'N/A')) for q in db])))
mod_scelto = st.sidebar.selectbox("Modulo:", ["Tutti"] + moduli)
sezioni = sorted(list(set([str(q.get('sezione', 'N.S.')) for q in db if mod_scelto == "Tutti" or str(q.get('modulo')) == mod_scelto])))
sez_scelta = st.sidebar.selectbox("Sezione:", ["Tutte"] + sezioni)
cartelle = ["Calderone", "Allenamento", "Campo", "Cassaforte"]
cart_scelta = st.sidebar.selectbox("Cartella:", ["Tutte"] + cartelle)

domande_filtrate = [q for q in db if 
    (mod_scelto == "Tutti" or str(q.get('modulo')) == mod_scelto) and
    (sez_scelta == "Tutte" or str(q.get('sezione', 'N.S.')) == sez_scelta) and
    (cart_scelta == "Tutte" or st.session_state.stats[str(q['id'])]["cartella"] == cart_scelta)
]

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
    st.markdown(f"**Domanda {q['id']}** (Modulo {q.get('modulo', 'N/A')})")
with col2:
    attuale = st.session_state.stats[q_id]["cartella"]
    nuova = st.selectbox("📂 Cartella:", cartelle, index=cartelle.index(attuale), key=f"c_{q_id}")
    if nuova != attuale:
        st.session_state.stats[q_id]["cartella"] = nuova
        salva_statistiche(st.session_state.stats)
        st.rerun()

st.markdown(f"<div class='quesito-testo'>{q['testo']}</div>", unsafe_allow_html=True)

scelta = st.radio("Risposta:", list(q['opzioni'].keys()), format_func=lambda x: f"{x.lower()}) {q['opzioni'][x]}", index=None, key=f"r_{q_id}")

if st.button("Conferma Risposta"):
    if scelta == q['corretta']:
        st.success(f"✅ ESATTO! Risposta: {q['corretta'].upper()}")
        st.session_state.stats[q_id]["corrette"] += 1
    else:
        st.error(f"❌ SBAGLIATO. Era: {q['corretta'].upper()}")
        st.session_state.stats[q_id]["errate"] += 1
    salva_statistiche(st.session_state.stats)

st.write("---")
cp, ct, cn = st.columns([1, 2, 1])
with cp:
    if st.button("⬅️ Precedente") and st.session_state.indice > 0:
        st.session_state.indice -= 1
        st.rerun()
with ct:
    # Riga corretta per evitare l'errore unterminated f-string
    testo_contatore = f"{st.session_state.indice + 1} / {len(domande_filtrate)}"
    st.markdown(f"<div style='text-align: center;'><b>{testo_contatore}</b></div>", unsafe_allow_html=True)
with cn:
    if st.button("Successiva ➡️") and st.session_state.indice < len(domande_filtrate) - 1:
        st.session_state.indice += 1
        st.rerun()
