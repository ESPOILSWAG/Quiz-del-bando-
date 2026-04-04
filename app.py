import streamlit as st
import json
import requests

st.set_page_config(page_title="Andromeda 4.0 - Simulatore Avanzato", layout="wide")

# --- CONFIGURAZIONE MEMORIA ETERNA ---
URL_MEMORIA = "https://script.google.com/macros/s/AKfycbycL7hgRkaDC0KSMsStCMkU8QZNhkAto5d1eLGDRRecpAoQl6V7ks4A48P-avYo2E6I/exec"

# Stile grafico Bando Veneto e layout compatto
st.markdown("""
<style>
    .domanda-titolo { font-weight: bold; font-size: 18pt; color: #1E88E5; }
    .quesito-testo { font-size: 16pt; font-style: italic; padding-top: 10px; padding-bottom: 20px; }
    .stRadio p { font-size: 10pt !important; }
    div[data-testid="stExpander"] { border: 1px solid #1E88E5; border-radius: 10px; }
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
    with st.spinner("Sincronizzazione dati..."):
        st.session_state.stats = carica_statistiche()

if not st.session_state.stats:
    for q in db: st.session_state.stats[str(q['id'])] = {"corrette": 0, "errate": 0, "cartella": "Calderone"}

# --- SIDEBAR: FILTRI AVANZATI ---
st.sidebar.title("⚙️ Pannello di Controllo")

# 1. Ricerca Parola Chiave
search_term = st.sidebar.text_input("🔍 Cerca parola (Testo o Opzioni):", "").lower()

# 2. Ricerca Numeri Specifici
ids_input = st.sidebar.text_input("🎯 ID specifici (es: 1, 5, 23):", "")
specific_ids = [s.strip() for s in ids_input.split(",") if s.strip()]

# 3. Ricerca Intervallo
col1, col2 = st.sidebar.columns(2)
start_range = col1.number_input("Da ID:", min_value=1, max_value=3000, value=1)
end_range = col2.number_input("A ID:", min_value=1, max_value=3000, value=3000)

# Altri Filtri
moduli = sorted(list(set([str(q.get('modulo', 'N/A')) for q in db])))
mod_scelto = st.sidebar.selectbox("Filtra Modulo:", ["Tutti"] + moduli)

# 4. Cartelle Personalizzate
cartelle_lista = ["Calderone", "Allenamento", "Campo scuro", "Cassaforte"]
cart_scelta = st.sidebar.selectbox("📂 Filtra Cartella:", ["Tutte"] + cartelle_lista)

# --- LOGICA FILTRO CHIRURGICO ---
domande_filtrate = []
for q in db:
    q_id_str = str(q['id'])
    testo_completo = q['testo'].lower() + " ".join(q['opzioni'].values()).lower()
    
    # Controllo ID specifici
    if specific_ids and q_id_str not in specific_ids: continue
    # Controllo Intervallo
    if not (start_range <= int(q['id']) <= end_range): continue
    # Controllo Parola Chiave
    if search_term and search_term not in testo_completo: continue
    # Controllo Modulo
    if mod_scelto != "Tutti" and str(q.get('modulo')) != mod_scelto: continue
    # Controllo Cartella
    if cart_scelta != "Tutte" and st.session_state.stats[q_id_str]["cartella"] != cart_scelta: continue
    
    domande_filtrate.append(q)

st.sidebar.success(f"🎯 Trovate: {len(domande_filtrate)}")

# --- NAVIGAZIONE ---
if 'indice' not in st.session_state: st.session_state.indice = 0
if not domande_filtrate:
    st.warning("Nessuna domanda trovata con questi criteri.")
    st.stop()
if st.session_state.indice >= len(domande_filtrate): st.session_state.indice = 0

q = domande_filtrate[st.session_state.indice]
q_id = str(q['id'])

# --- VISUALIZZAZIONE ---
st.title("🚀 Progetto Andromeda 4.0 Online")
st.markdown("---")

st.markdown(f"<div class='domanda-titolo'>Domanda {q['id']}</div>", unsafe_allow_html=True)
st.markdown(f"<div style='color: gray; font-size: 10pt;'>Modulo: {q.get('modulo', 'N/A')} | Sezione: {q.get('sezione', 'N/A')}</div>", unsafe_allow_html=True)

st.markdown(f"<div class='quesito-testo'>{q['testo']}</div>", unsafe_allow_html=True)

scelta = st.radio("Seleziona la risposta:", list(q['opzioni'].keys()), 
                 format_func=lambda x: f"{x.lower()}) {q['opzioni'][x]}", 
                 index=None, key=f"r_{q_id}")

# Variabile di stato per mostrare il selettore cartella dopo l'azione
if 'mostra_cartella' not in st.session_state: st.session_state.mostra_cartella = False

col_a, col_b = st.columns(2)
with col_a:
    if st.button("✅ Conferma Risposta", use_container_width=True):
        st.session_state.mostra_cartella = True
        if scelta == q['corretta']:
            st.success(f"ESATTO! La risposta corretta è la {q['corretta'].upper()}")
            st.session_state.stats[q_id]["corrette"] += 1
        else:
            st.error(f"SBAGLIATO. La risposta corretta era la {q['corretta'].upper()}")
            st.session_state.stats[q_id]["errate"] += 1
        salva_statistiche(st.session_state.stats)

with col_b:
    if st.button("⏭️ Salta / Avanti", use_container_width=True):
        st.session_state.mostra_cartella = True
        # Non salva statistiche di errore, ma attiva la scelta cartella

# --- 5. LOGICA POSIZIONAMENTO CARTELLA (DOPO RISPOSTA O SALTO) ---
if st.session_state.mostra_cartella:
    st.markdown("---")
    st.subheader("📂 Dove vuoi posizionare questa domanda?")
    attuale = st.session_state.stats[q_id]["cartella"]
    
    # Pulsanti rapidi per le cartelle
    cols_cart = st.columns(4)
    for i, c_name in enumerate(cartelle_lista):
        if cols_cart[i].button(f"{c_name}", key=f"btn_{c_name}", type="primary" if attuale == c_name else "secondary"):
            st.session_state.stats[q_id]["cartella"] = c_name
            salva_statistiche(st.session_state.stats)
            st.toast(f"Spostata in {c_name}")
            st.session_state.mostra_cartella = False # Nasconde i tasti cartella dopo la scelta
            st.rerun()

st.write("---")
# Pulsanti navigazione
nav_prev, nav_count, nav_next = st.columns([1, 2, 1])
with nav_prev:
    if st.button("⬅️ Precedente") and st.session_state.indice > 0:
        st.session_state.indice -= 1
        st.session_state.mostra_cartella = False
        st.rerun()
with nav_count:
    st.markdown(f"<div style='text-align: center; font-weight: bold;'>{st.session_state.indice + 1} / {len(domande_filtrate)}</div>", unsafe_allow_html=True)
with nav_next:
    if st.button("Successiva ➡️") and st.session_state.indice < len(domande_filtrate) - 1:
        st.session_state.indice += 1
        st.session_state.mostra_cartella = False
        st.rerun()
