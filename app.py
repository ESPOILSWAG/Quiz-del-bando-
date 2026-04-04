import streamlit as st
import json
import os

st.set_page_config(page_title="Simulatore Andromeda 4.0", layout="wide")

st.markdown("""
    <style>
    .domanda-titolo { font-weight: bold; font-size: 18pt; }
    .quesito-testo { font-size: 16pt; font-style: italic; padding-top: 10px; padding-bottom: 20px; }
    .stRadio p { font-size: 10pt !important; font-style: normal !important; font-weight: normal !important; }
    </style>
""", unsafe_allow_html=True)

DB_FILE = 'database_3000.json'
STATS_FILE = 'statistiche.json'

def carica_database():
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except FileNotFoundError:
        st.error(f"❌ Errore: Non trovo il file {DB_FILE}!")
        st.stop()

def carica_statistiche():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return {}

def salva_statistiche(stats):
    with open(STATS_FILE, 'w', encoding='utf-8') as f: json.dump(stats, f, indent=4)

db = carica_database()
stats = carica_statistiche()

for q in db:
    q_id = str(q['id'])
    if q_id not in stats: stats[q_id] = {"corrette": 0, "errate": 0, "cartella": "Calderone"}

moduli_disponibili = sorted(list(set([str(q.get('modulo', 'Sconosciuto')) for q in db])))
cartelle_disponibili = ["Calderone", "Allenamento", "Campo", "Cassaforte"]

st.sidebar.title("⚙️ Filtri Avanzati")
modulo_scelto = st.sidebar.selectbox("Filtra per Modulo:", ["Tutti"] + moduli_disponibili)

# LOGICA SEZIONI
if modulo_scelto == "Tutti":
    sezioni_disponibili = sorted(list(set([str(q.get('sezione', 'N.S.')) for q in db])))
else:
    sezioni_disponibili = sorted(list(set([str(q.get('sezione', 'N.S.')) for q in db if str(q.get('modulo')) == modulo_scelto])))
    cartella_ns_forzata = f"N.S. {modulo_scelto}"
    if cartella_ns_forzata not in sezioni_disponibili:
        sezioni_disponibili.append(cartella_ns_forzata)
        sezioni_disponibili.sort()

sezione_scelta = st.sidebar.selectbox("Filtra per Sezione:", ["Tutte"] + sezioni_disponibili)

# LOGICA SOTTOSEZIONI
if sezione_scelta == "Tutte":
    if modulo_scelto == "Tutti":
        sotto_disponibili = sorted(list(set([str(q.get('sottosezione', 'N.S.')) for q in db])))
    else:
        sotto_disponibili = sorted(list(set([str(q.get('sottosezione', 'N.S.')) for q in db if str(q.get('modulo')) == modulo_scelto])))
else:
    sotto_disponibili = sorted(list(set([str(q.get('sottosezione', 'N.S.')) for q in db if str(q.get('modulo')) == modulo_scelto and str(q.get('sezione')) == sezione_scelta])))

sottosezione_scelta = st.sidebar.selectbox("Filtra per Sottosezione:", ["Tutte"] + sotto_disponibili)

st.sidebar.markdown("---")
colA, colB = st.sidebar.columns(2)
filtro_min = colA.number_input("Da n°:", min_value=0, value=0, step=1)
filtro_max = colB.number_input("A n°:", min_value=0, value=0, step=1)

st.sidebar.markdown("---")
parola_chiave = st.sidebar.text_input("🔍 Cerca parola nel testo:")

st.sidebar.markdown("---")
cartella_scelta = st.sidebar.selectbox("📂 Filtra per Cartella:", ["Tutte le cartelle"] + cartelle_disponibili)

domande_filtrate = []
for q in db:
    q_id_str = str(q['id'])
    q_num = int(q['id'])
    testo_lower = q['testo'].lower()
    
    if modulo_scelto != "Tutti" and str(q.get('modulo')) != modulo_scelto: continue
    if sezione_scelta != "Tutte" and str(q.get('sezione', 'N.S.')) != sezione_scelta: continue
    if sottosezione_scelta != "Tutte" and str(q.get('sottosezione', 'N.S.')) != sottosezione_scelta: continue
    if filtro_min > 0 and q_num < filtro_min: continue
    if filtro_max > 0 and q_num > filtro_max: continue
    if parola_chiave and parola_chiave.lower() not in testo_lower: continue
    if cartella_scelta != "Tutte le cartelle" and stats[q_id_str]["cartella"] != cartella_scelta: continue
    
    domande_filtrate.append(q)

st.sidebar.success(f"🎯 Domande trovate: {len(domande_filtrate)}")

st.title("🚀 Simulatore Progetto Andromeda 4.0")
st.markdown("---")

current_filters = (modulo_scelto, sezione_scelta, sottosezione_scelta, filtro_min, filtro_max, parola_chiave, cartella_scelta)
if 'domande_correnti' not in st.session_state or st.session_state.get('last_filters') != current_filters:
    st.session_state.domande_correnti = domande_filtrate
    st.session_state.indice = 0
    st.session_state.risposta_confermata = False
    st.session_state.last_filters = current_filters

if not st.session_state.domande_correnti:
    st.warning("Nessuna domanda in questa cartella.")
    st.stop()

if st.session_state.indice >= len(st.session_state.domande_correnti):
    st.session_state.indice = len(st.session_state.domande_correnti) - 1

q = st.session_state.domande_correnti[st.session_state.indice]
q_id_str = str(q['id'])
cartella_q = stats[q_id_str]["cartella"]
sezione_q = str(q.get('sezione', 'N.S.'))
sottosezione_q = str(q.get('sottosezione', 'N.S.'))

col_titolo, col_cartella = st.columns([3, 1])
with col_titolo:
    st.markdown(f"<div class='domanda-titolo'>Domanda {q['id']}</div> <div style='font-size: 11pt; color: gray;'>Modulo: {q.get('modulo', 'N/A')} | Sezione: {sezione_q} | Sottosezione: {sottosezione_q}</div>", unsafe_allow_html=True)
with col_cartella:
    nuova_cartella = st.selectbox("📂 Cartella attuale:", cartelle_disponibili, index=cartelle_disponibili.index(cartella_q), key=f"cart_{q_id_str}")
    if nuova_cartella != cartella_q:
        stats[q_id_str]["cartella"] = nuova_cartella
        salva_statistiche(stats)
        st.rerun()

st.markdown(f"<div class='quesito-testo'>{q['testo']}</div>", unsafe_allow_html=True)

opzioni = q['opzioni']
chiavi_opzioni = list(opzioni.keys())
scelta = st.radio("Scegli un'opzione (Nascosto via CSS):", chiavi_opzioni, format_func=lambda x: f"{x.lower()}) {opzioni[x]}", index=None, key=f"rad_{q_id_str}", label_visibility="collapsed")

if st.button("Conferma Risposta"):
    if scelta is None:
        st.warning("Seleziona prima un'opzione!")
    else:
        st.session_state.risposta_confermata = True
        if scelta == q['corretta']:
            st.success(f"✅ Esatto! La risposta corretta è la {q['corretta'].lower()}).")
            stats[q_id_str]["corrette"] += 1
        else:
            st.error(f"❌ Sbagliato. La risposta corretta era la {q['corretta'].lower()}): {opzioni[q['corretta']]}")
            stats[q_id_str]["errate"] += 1
        salva_statistiche(stats)

st.write("---")

col_prev, col_center, col_next = st.columns([1, 2, 1])
with col_prev:
    if st.button("⬅️ Indietro") and st.session_state.indice > 0:
        st.session_state.indice -= 1
        st.session_state.risposta_confermata = False
        st.rerun()
with col_center:
    st.markdown(f"<div style='text-align: center;'>Domanda <b>{st.session_state.indice + 1}</b> di <b>{len(st.session_state.domande_correnti)}</b></div>", unsafe_allow_html=True)
with col_next:
    if st.button("Avanti ➡️") and st.session_state.indice < len(st.session_state.domande_correnti) - 1:
        st.session_state.indice += 1
        st.session_state.risposta_confermata = False
        st.rerun()
