import streamlit as st
import json
import requests
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="Andromeda 4.0 - Training Center", layout="wide")

# --- CONFIGURAZIONE ---
URL_MEMORIA = "https://script.google.com/macros/s/AKfycbycL7hgRkaDC0KSMsStCMkU8QZNhkAto5d1eLGDRRecpAoQl6V7ks4A48P-avYo2E6I/exec"

st.markdown("""
<style>
    .domanda-titolo { font-weight: bold; font-size: 18pt; color: #1E88E5; }
    .quesito-testo { font-size: 16pt; font-style: italic; padding-top: 10px; padding-bottom: 20px; }
    .stRadio p { font-size: 10pt !important; font-weight: normal !important; }
    .figura-alert { background-color: #FFF3E0; border-left: 5px solid #FF9800; padding: 10px; color: #E65100; font-weight: bold; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 1. ACCESSO E SICUREZZA ---
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None

if st.session_state.logged_in_user is not None:
    if 'login_time' in st.session_state:
        if datetime.now() - st.session_state.login_time > timedelta(hours=2):
            st.session_state.logged_in_user = None
            st.rerun()

if st.session_state.logged_in_user is None:
    st.markdown("<h1 style='text-align: center;'>🛡️ Andromeda 4.0</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div style='background-color: #1E88E5; padding: 40px; text-align: center; border-radius: 20px;'><h1 style='color: white; font-size: 80px; margin: 0;'>T</h1></div>", unsafe_allow_html=True)
        if st.button("Topolino", use_container_width=True): st.session_state.selected_acc = 'T'
    with col2:
        st.markdown("<div style='background-color: #E91E63; padding: 40px; text-align: center; border-radius: 20px;'><h1 style='color: white; font-size: 80px; margin: 0;'>P</h1></div>", unsafe_allow_html=True)
        if st.button("Panciccia", use_container_width=True): st.session_state.selected_acc = 'P'

    if 'selected_acc' in st.session_state:
        pwd = st.text_input(f"Password per {st.session_state.selected_acc}:", type="password")
        if st.button("Sblocca", type="primary"):
            if (st.session_state.selected_acc == 'T' and pwd == "topolino") or (st.session_state.selected_acc == 'P' and pwd == "panciccia"):
                st.session_state.logged_in_user = st.session_state.selected_acc
                st.session_state.login_time = datetime.now()
                st.rerun()
    st.stop()

# --- 2. FUNZIONI DATI ---
def carica_database():
    with open('database_3000.json', 'r', encoding='utf-8') as f: return json.load(f)

def carica_statistiche():
    try:
        r = requests.get(URL_MEMORIA, timeout=10)
        dati = r.json()
        return {str(row[0]): {"corrette": int(row[1]), "errate": int(row[2]), "cartella": str(row[3]), "data_mod": str(row[4]) if len(row)>4 else ""} for row in dati[1:]}
    except: return None

def salva_statistiche(stats):
    payload = [{"id": k, "corrette": v['corrette'], "errate": v['errate'], "cartella": v['cartella'], "data_modifica": v.get('data_mod', '')} for k, v in stats.items()]
    requests.post(URL_MEMORIA, json=payload, timeout=15)

def u_key(base_id): return str(base_id) if st.session_state.logged_in_user == 'T' else f"{base_id}_P"

db = carica_database()
if 'global_stats' not in st.session_state:
    remote = carica_statistiche()
    st.session_state.global_stats = remote if remote else {}
    for q in db:
        for k in [str(q['id']), f"{q['id']}_P"]:
            if k not in st.session_state.global_stats:
                st.session_state.global_stats[k] = {"corrette": 0, "errate": 0, "cartella": "Calderone", "data_mod": ""}

# --- 3. SIDEBAR E PDF (Punto 3) ---
st.sidebar.title("📚 Risorse PDF")
try:
    with open("Quiz_Parte_1.pdf", "rb") as f1:
        st.sidebar.download_button("📄 Scarica PDF 1 (Fondamenti)", f1, file_name="Quiz_Parte_1.pdf")
    with open("Quiz_Parte_2.pdf", "rb") as f2:
        st.sidebar.download_button("📄 Scarica PDF 2 (Ricettazione)", f2, file_name="Quiz_Parte_2.pdf")
except:
    st.sidebar.info("Carica i file PDF su GitHub per abilitarli.")

st.sidebar.markdown("---")
modalita = st.sidebar.radio("Modalità:", ["📚 Esplorazione", "🎯 Active Recall"])

# --- 4. FILTRO DATE AVANZATO (Punto 2) ---
st.sidebar.markdown("---")
st.sidebar.subheader("📅 Filtro Temporale")
abilita_data = st.sidebar.checkbox("Attiva filtro date")
range_date = None
if abilita_data:
    range_date = st.sidebar.date_input("Seleziona Giorno o Intervallo", value=(), help="Seleziona inizio e fine per un intervallo")

# Altri filtri
search_term = st.sidebar.text_input("🔍 Cerca parola:", "").lower()
mod_scelto = st.sidebar.selectbox("Modulo:", ["Tutti"] + sorted(list(set([str(q.get('modulo', 'N/A')) for q in db]))))
cartelle_lista = ["Calderone", "Allenamento", "Campo sicuro", "Cassaforte"]
cart_scelta = st.sidebar.selectbox("📂 Cartella:", ["Tutte"] + cartelle_lista)

# --- 5. LOGICA DI FILTRAGGIO ---
def filtra_domande():
    risultato = []
    for q in db:
        k = u_key(q['id'])
        stat = st.session_state.global_stats[k]
        
        # Filtro Data
        if abilita_data and range_date and len(range_date) == 2:
            try:
                d_mod = datetime.strptime(stat.get('data_mod', ''), "%d/%m/%Y").date()
                if not (range_date[0] <= d_mod <= range_date[1]): continue
            except: continue
        elif abilita_data and range_date and len(range_date) == 1:
            if stat.get('data_mod') != range_date[0].strftime("%d/%m/%Y"): continue
        
        if search_term and search_term not in (q['testo'] + " ".join(q['opzioni'].values())).lower(): continue
        if mod_scelto != "Tutti" and str(q.get('modulo')) != mod_scelto: continue
        if cart_scelta != "Tutte" and stat["cartella"] != cart_scelta: continue
        risultato.append(q)
    return risultato

domande_filtrate_base = filtra_domande()

# Gestione Simulazione
if modalita == "🎯 Active Recall":
    if 'sim_ids' not in st.session_state or st.sidebar.button("🎲 Nuova Simulazione"):
        n_q = st.sidebar.number_input("Domande:", 1, len(domande_filtrate_base), min(10, len(domande_filtrate_base)))
        st.session_state.sim_ids = [q['id'] for q in random.sample(domande_filtrate_base, n_q)]
        st.session_state.indice = 0
    domande_filtrate = [q for q in db if q['id'] in st.session_state.sim_ids]
else:
    domande_filtrate = domande_filtrate_base

# --- 6. VISUALIZZAZIONE ---
if 'indice' not in st.session_state: st.session_state.indice = 0
if st.session_state.indice >= len(domande_filtrate): st.session_state.indice = 0

if not domande_filtrate:
    st.warning("Nessuna domanda trovata.")
    st.stop()

q = domande_filtrate[st.session_state.indice]
k_q = u_key(q['id'])

# Informazioni Modulo e Sottomodulo (Punto 6)
st.title("🚀 Andromeda 4.0")
st.markdown(f"**Domanda {q['id']}** | Modulo: `{q.get('modulo', 'N/A')}` | Sezione: `{q.get('sezione', 'N/A')}`")

# Avviso Figure (Punto 1)
# Assumendo che nel JSON ci sia 'figura': 'FIGURA'
if q.get('figura') == 'FIGURA':
    st.markdown("<div class='figura-alert'>⚠️ QUESTA DOMANDA CONTIENE UNA FIGURA (Vedi file originale)</div>", unsafe_allow_html=True)

st.markdown(f"<div class='quesito-testo'>{q['testo']}</div>", unsafe_allow_html=True)

if 'answered' not in st.session_state: st.session_state.answered = False

scelta = st.radio("Risposta:", list(q['opzioni'].keys()), format_func=lambda x: f"{x.lower()}) {q['opzioni'][x]}", index=None, key=f"r_{q['id']}", disabled=st.session_state.answered)

if scelta and not st.session_state.answered:
    st.session_state.answered = True
    st.session_state.global_stats[k_q]["data_mod"] = datetime.now().strftime("%d/%m/%Y")
    if scelta == q['corretta']:
        st.session_state.esito = "ok"; st.session_state.global_stats[k_q]["corrette"] += 1
    else:
        st.session_state.esito = "no"; st.session_state.global_stats[k_q]["errate"] += 1
    st.rerun()

if st.session_state.answered:
    if st.session_state.esito == "ok": st.success(f"Corretto! La risposta è {q['corretta'].upper()}")
    else: st.error(f"Sbagliato! La risposta corretta è {q['corretta'].upper()}")
    
    st.subheader("Sposta in:")
    cols = st.columns(4)
    for i, c_name in enumerate(cartelle_lista):
        if cols[i].button(c_name, key=f"b_{c_name}", use_container_width=True):
            st.session_state.global_stats[k_q]["cartella"] = c_name
            st.session_state.global_stats[k_q]["data_mod"] = datetime.now().strftime("%d/%m/%Y")
            salva_statistiche(st.session_state.global_stats)
            st.session_state.answered = False
            # BUG FIX: Non incrementiamo l'indice se la domanda esce dal filtro attuale (scalano le altre)
            if cart_scelta != "Tutte":
                pass 
            else:
                st.session_state.indice += 1
            st.rerun()

# Navigazione
st.write("---")
c1, c2, c3 = st.columns([1, 2, 1])
if c1.button("⬅️ Indietro"):
    st.session_state.indice -= 1; st.session_state.answered = False; st.rerun()
c2.markdown(f"<center>{st.session_state.indice + 1} / {len(domande_filtrate)}</center>", unsafe_allow_html=True)
if c3.button("Avanti ➡️"):
    st.session_state.indice += 1; st.session_state.answered = False; st.rerun()
