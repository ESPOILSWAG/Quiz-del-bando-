import streamlit as st
import json
import requests

st.set_page_config(page_title="Andromeda 4.0 - Simulatore Avanzato", layout="wide")

# --- CONFIGURAZIONE MEMORIA ETERNA ---
URL_MEMORIA = "https://script.google.com/macros/s/AKfycbycL7hgRkaDC0KSMsStCMkU8QZNhkAto5d1eLGDRRecpAoQl6V7ks4A48P-avYo2E6I/exec"

st.markdown("""
<style>
    .domanda-titolo { font-weight: bold; font-size: 18pt; color: #1E88E5; }
    .quesito-testo { font-size: 16pt; font-style: italic; padding-top: 10px; padding-bottom: 20px; }
    .stRadio p { font-size: 10pt !important; font-weight: normal !important; }
</style>
""", unsafe_allow_html=True)

def carica_database():
    with open('database_3000.json', 'r', encoding='utf-8') as f: return json.load(f)

def carica_statistiche():
    try:
        r = requests.get(URL_MEMORIA, timeout=10)
        dati = r.json()
        stats = {}
        if len(dati) > 1:
            for row in dati[1:]:
                stats[str(row[0])] = {"corrette": int(row[1]), "errate": int(row[2]), "cartella": str(row[3])}
        return stats
    except: return None

def salva_statistiche(stats):
    payload = []
    for q_id, val in stats.items():
        payload.append({"id": q_id, "corrette": val['corrette'], "errate": val['errate'], "cartella": val['cartella']})
    try:
        requests.post(URL_MEMORIA, json=payload, timeout=15)
        return True
    except:
        return False

# --- LOGICA DI AVVIO ---
db = carica_database()

if 'stats' not in st.session_state:
    stats_remote = carica_statistiche()
    if stats_remote:
        st.session_state.stats = stats_remote
    else:
        st.session_state.stats = {str(q['id']): {"corrette": 0, "errate": 0, "cartella": "Calderone"} for q in db}

# --- SIDEBAR E FILTRI ---
st.sidebar.title("⚙️ Pannello di Controllo")
search_term = st.sidebar.text_input("🔍 Cerca parola (Testo o Opzioni):", "").lower()
ids_input = st.sidebar.text_input("🎯 ID specifici (es: 1, 5, 23):", "")
specific_ids = [s.strip() for s in ids_input.split(",") if s.strip()]

col1, col2 = st.sidebar.columns(2)
start_range = col1.number_input("Da ID:", 1, 3000, 1)
end_range = col2.number_input("A ID:", 1, 3000, 3000)

moduli = sorted(list(set([str(q.get('modulo', 'N/A')) for q in db])))
mod_scelto = st.sidebar.selectbox("Modulo:", ["Tutti"] + moduli)

# Aggiornato: Campo scuro -> Campo sicuro
cartelle_lista = ["Calderone", "Allenamento", "Campo sicuro", "Cassaforte"]
cart_scelta = st.sidebar.selectbox("📂 Cartella:", ["Tutte"] + cartelle_lista)

# --- FILTRAGGIO ---
domande_filtrate = []
for q in db:
    q_id_str = str(q['id'])
    testo_c = (q['testo'] + " ".join(q['opzioni'].values()).lower()).lower()
    
    if specific_ids and q_id_str not in specific_ids: continue
    if not (start_range <= int(q['id']) <= end_range): continue
    if search_term and search_term not in testo_c: continue
    if mod_scelto != "Tutti" and str(q.get('modulo')) != mod_scelto: continue
    if cart_scelta != "Tutte" and st.session_state.stats[q_id_str]["cartella"] != cart_scelta: continue
    
    domande_filtrate.append(q)

# --- RICERCA INTELLIGENTE ---
if not domande_filtrate and specific_ids:
    for sid in specific_ids:
        if sid in st.session_state.stats:
            dove = st.session_state.stats[sid]['cartella']
            st.info(f"💡 La domanda **{sid}** non è qui: si trova in **{dove}**.")

if not domande_filtrate:
    st.warning("Nessuna domanda trovata.")
    st.stop()

# --- NAVIGAZIONE ---
if 'indice' not in st.session_state: st.session_state.indice = 0
if st.session_state.indice >= len(domande_filtrate): st.session_state.indice = 0
q = domande_filtrate[st.session_state.indice]
q_id = str(q['id'])

# --- INTERFACCIA ---
st.title("🚀 Progetto Andromeda 4.0 Online")
st.markdown(f"<div class='domanda-titolo'>Domanda {q['id']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='quesito-testo'>{q['testo']}</div>", unsafe_allow_html=True)

scelta = st.radio("Risposta:", list(q['opzioni'].keys()), format_func=lambda x: f"{x.lower()}) {q['opzioni'][x]}", index=None, key=f"r_{q_id}")

if 'answered' not in st.session_state: st.session_state.answered = False

c_conf, c_salt = st.columns(2)
with c_conf:
    if st.button("✅ Conferma Risposta", use_container_width=True):
        if scelta:
            st.session_state.answered = True
            if scelta == q['corretta']:
                st.session_state.esito = "ok"
                st.session_state.stats[q_id]["corrette"] += 1
            else:
                st.session_state.esito = "no"
                st.session_state.stats[q_id]["errate"] += 1
            st.rerun()
with c_salt:
    if st.button("⏭️ Salta / Avanti", use_container_width=True):
        st.session_state.answered = True
        st.session_state.esito = "skip"
        st.rerun()

# --- SMISTAMENTO ---
if st.session_state.answered:
    if st.session_state.esito == "ok": st.success(f"CORRETTO! Era la {q['corretta'].upper()}")
    elif st.session_state.esito == "no": st.error(f"ERRORE! Era la {q['corretta'].upper()}")
    
    st.subheader("📂 In quale cartella vuoi spostarla?")
    attuale = st.session_state.stats[q_id]["cartella"]
    cols = st.columns(4)
    for i, c_name in enumerate(cartelle_lista):
        if cols[i].button(c_name, key=f"b_{c_name}", type="primary" if attuale == c_name else "secondary", use_container_width=True):
            st.session_state.stats[q_id]["cartella"] = c_name
            with st.spinner("Salvataggio..."):
                salva_statistiche(st.session_state.stats)
            st.session_state.answered = False
            if st.session_state.indice < len(domande_filtrate) - 1:
                st.session_state.indice += 1
            st.rerun()

# --- NAVIGAZIONE IN FONDO ---
st.write("---")
n_prev, n_count, n_next = st.columns([1, 2, 1])
with n_prev:
    if st.button("⬅️ Indietro") and st.session_state.indice > 0:
        st.session_state.indice -= 1
        st.session_state.answered = False
        st.rerun()
with n_count:
    st.markdown(f<div style='text-align: center;'><b>{st.session_state.indice + 1} / {len(domande_filtrate)}</b></div>, unsafe_allow_html=True)
with n_next:
    if st.button("Avanti ➡️") and st.session_state.indice < len(domande_filtrate) - 1:
        st.session_state.indice += 1
        st.session_state.answered = False
        st.rerun()
