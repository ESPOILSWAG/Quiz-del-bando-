import streamlit as st
import json
import requests

st.set_page_config(page_title="Andromeda 4.0 - Simulatore Avanzato", layout="wide")

# --- CONFIGURAZIONE MEMORIA ETERNA ---
URL_MEMORIA = "https://script.google.com/macros/s/AKfycbycL7hgRkaDC0KSMsStCMkU8QZNhkAto5d1eLGDRRecpAoQl6V7ks4A48P-avYo2E6I/exec"

# Stile grafico Bando Veneto
st.markdown("""
<style>
    .domanda-titolo { font-weight: bold; font-size: 18pt; color: #1E88E5; }
    .quesito-testo { font-size: 16pt; font-style: italic; padding-top: 10px; padding-bottom: 20px; }
    .stRadio p { font-size: 10pt !important; font-weight: normal !important; font-style: normal !important; }
</style>
""", unsafe_allow_html=True)

def carica_database():
    try:
        with open('database_3000.json', 'r', encoding='utf-8') as f: return json.load(f)
    except:
        st.error("File database_3000.json non trovato.")
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
    except: st.error("Errore salvataggio Google.")

# --- INIZIALIZZAZIONE ---
db = carica_database()
if 'stats' not in st.session_state:
    with st.spinner("Sincronizzazione dati con Google Fogli..."):
        st.session_state.stats = carica_statistiche()

for q in db: 
    if str(q['id']) not in st.session_state.stats:
        st.session_state.stats[str(q['id'])] = {"corrette": 0, "errate": 0, "cartella": "Calderone"}

# --- SIDEBAR: FILTRI AVANZATI ---
st.sidebar.title("⚙️ Pannello di Controllo")

search_term = st.sidebar.text_input("🔍 Cerca parola (Testo o Opzioni):", "").lower()

ids_input = st.sidebar.text_input("🎯 ID specifici (es: 1, 5, 23):", "")
specific_ids = [s.strip() for s in ids_input.split(",") if s.strip()]

col1, col2 = st.sidebar.columns(2)
start_range = col1.number_input("Da ID:", min_value=1, max_value=3000, value=1)
end_range = col2.number_input("A ID:", min_value=1, max_value=3000, value=3000)

moduli = sorted(list(set([str(q.get('modulo', 'N/A')) for q in db])))
mod_scelto = st.sidebar.selectbox("Filtra Modulo:", ["Tutti"] + moduli)

cartelle_lista = ["Calderone", "Allenamento", "Campo scuro", "Cassaforte"]
cart_scelta = st.sidebar.selectbox("📂 Filtra Cartella:", ["Tutte"] + cartelle_lista)

# --- LOGICA FILTRO CHIRURGICO ---
domande_filtrate = []
for q in db:
    q_id_str = str(q['id'])
    testo_completo = q['testo'].lower() + " ".join(q['opzioni'].values()).lower()
    
    if specific_ids and q_id_str not in specific_ids: continue
    if not (start_range <= int(q['id']) <= end_range): continue
    if search_term and search_term not in testo_completo: continue
    if mod_scelto != "Tutti" and str(q.get('modulo')) != mod_scelto: continue
    if cart_scelta != "Tutte" and st.session_state.stats[q_id_str]["cartella"] != cart_scelta: continue
    
    domande_filtrate.append(q)

st.sidebar.success(f"🎯 Trovate: {len(domande_filtrate)}")

# --- IL RICERCATORE INTELLIGENTE ---
if not domande_filtrate:
    st.warning("Nessuna domanda trovata con i filtri attuali.")
    # Se ha cercato un ID specifico, gli diciamo dove si trova
    if specific_ids:
        for sid in specific_ids:
            if sid in st.session_state.stats:
                cartella_reale = st.session_state.stats[sid]["cartella"]
                st.info(f"💡 **Ricerca Intelligente:** La domanda {sid} si trova attualmente nella cartella **{cartella_reale}**.")
    st.stop()

# --- NAVIGAZIONE E GESTIONE STATO ---
if 'indice' not in st.session_state: st.session_state.indice = 0
if st.session_state.indice >= len(domande_filtrate): st.session_state.indice = 0

q = domande_filtrate[st.session_state.indice]
q_id = str(q['id'])

# Resetta lo stato se la domanda cambia
if 'current_q_id' not in st.session_state or st.session_state.current_q_id != q_id:
    st.session_state.current_q_id = q_id
    st.session_state.answered = False
    st.session_state.esito = None

# --- VISUALIZZAZIONE DOMANDA ---
st.title("🚀 Progetto Andromeda 4.0 Online")
st.markdown("---")

st.markdown(f"<div class='domanda-titolo'>Domanda {q['id']}</div>", unsafe_allow_html=True)
st.markdown(f"<div style='color: gray; font-size: 10pt;'>Modulo: {q.get('modulo', 'N/A')} | Sezione: {q.get('sezione', 'N/A')}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='quesito-testo'>{q['testo']}</div>", unsafe_allow_html=True)

scelta = st.radio("Seleziona la risposta:", list(q['opzioni'].keys()), 
                 format_func=lambda x: f"{x.lower()}) {q['opzioni'][x]}", 
                 index=None, key=f"r_{q_id}")

# --- FASE 1: PULSANTI DI AZIONE ---
if not st.session_state.answered:
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("✅ Conferma Risposta", use_container_width=True):
            if scelta is None:
                st.warning("Seleziona un'opzione prima di confermare!")
            else:
                st.session_state.answered = True
                if scelta == q['corretta']:
                    st.session_state.esito = "corretta"
                    st.session_state.stats[q_id]["corrette"] += 1
                else:
                    st.session_state.esito = "errata"
                    st.session_state.stats[q_id]["errate"] += 1
                salva_statistiche(st.session_state.stats)
                st.rerun()
    with col_b:
        if st.button("⏭️ Salta / Avanti", use_container_width=True):
            st.session_state.answered = True
            st.session_state.esito = "saltata"
            st.rerun()

# --- FASE 2: ESITO E SCELTA CARTELLA ---
if st.session_state.answered:
    # Mostra Esito
    if st.session_state.esito == "corretta":
        st.success(f"✅ ESATTO! La risposta corretta è la {q['corretta'].upper()}")
    elif st.session_state.esito == "errata":
        st.error(f"❌ SBAGLIATO. La risposta corretta era la {q['corretta'].upper()}: {q['opzioni'][q['corretta']]}")
    else:
        st.info("⏭️ Domanda saltata senza rispondere.")

    st.markdown("---")
    st.subheader("📂 In quale cartella vuoi posizionare questa domanda?")
    attuale = st.session_state.stats[q_id]["cartella"]
    st.write(f"Posizione attuale: **{attuale}**")
    
    # Mostra i 4 tasti per lo smistamento
    cols_cart = st.columns(4)
    for i, c_name in enumerate(cartelle_lista):
        if cols_cart[i].button(f"{c_name}", key=f"btn_{c_name}", type="primary" if attuale == c_name else "secondary", use_container_width=True):
            # Salva la nuova cartella
            st.session_state.stats[q_id]["cartella"] = c_name
            salva_statistiche(st.session_state.stats)
            st.toast(f"Domanda {q_id} spostata in {c_name}!")
            
            # Passaggio automatico alla domanda successiva
            if st.session_state.indice < len(domande_filtrate) - 1:
                st.session_state.indice += 1
            st.rerun()

# --- NAVIGAZIONE MANUALE ---
st.write("---")
nav_prev, nav_count, nav_next = st.columns([1, 2, 1])
with nav_prev:
    if st.button("⬅️ Precedente") and st.session_state.indice > 0:
        st.session_state.indice -= 1
        st.rerun()
with nav_count:
    st.markdown(f"<div style='text-align: center; font-weight: bold;'>{st.session_state.indice + 1} / {len(domande_filtrate)}</div>", unsafe_allow_html=True)
with nav_next:
    if st.button("Successiva ➡️") and st.session_state.indice < len(domande_filtrate) - 1:
        st.session_state.indice += 1
        st.rerun()
