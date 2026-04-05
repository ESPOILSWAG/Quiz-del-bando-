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
            else:
                st.error("❌ Password errata.")
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

# --- 3. SIDEBAR E PDF ---
utente_attuale = "Topolino" if st.session_state.logged_in_user == 'T' else "Panciccia"
st.sidebar.success(f"👤 Connesso come: **{utente_attuale}**")
if st.sidebar.button("🚪 Esci"):
    st.session_state.logged_in_user = None
    st.rerun()

st.sidebar.title("📚 Risorse PDF")
try:
    with open("Quiz_Parte_1.pdf", "rb") as f1:
        st.sidebar.download_button("📄 PDF 1 (Fondamenti)", f1, file_name="Quiz_Parte_1.pdf")
    with open("Quiz_Parte_2.pdf", "rb") as f2:
        st.sidebar.download_button("📄 PDF 2 (Ricettazione)", f2, file_name="Quiz_Parte_2.pdf")
except:
    st.sidebar.info("Carica i file PDF su GitHub per scaricarli.")

st.sidebar.markdown("---")
modalita = st.sidebar.radio("🧠 Modalità:", ["📚 Esplorazione Libera", "🎯 Active Recall"])

# --- 4. PANNELLO FILTRI ---
st.sidebar.markdown("---")
st.sidebar.subheader("📅 Filtro Temporale")
abilita_data = st.sidebar.checkbox("Attiva filtro date")
range_date = None
if abilita_data:
    range_date = st.sidebar.date_input("Seleziona data o intervallo (trascina)", value=[])

st.sidebar.subheader("🎯 Filtri Numerici")
ids_input = st.sidebar.text_input("ID specifici (es: 1, 5, 23):", "")
specific_ids = [s.strip() for s in ids_input.split(",") if s.strip()]
col1, col2 = st.sidebar.columns(2)
start_range = col1.number_input("Da ID:", 1, 3000, 1)
end_range = col2.number_input("A ID:", 1, 3000, 3000)

st.sidebar.subheader("🏷️ Filtri Contenuto")
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
        q_id_int = int(q['id'])
        q_id_str = str(q['id'])
        
        # Filtri Numerici
        if specific_ids and q_id_str not in specific_ids: continue
        if not (start_range <= q_id_int <= end_range): continue
        
        # Filtro Data (Resiliente a Google Sheets)
        if abilita_data and range_date:
            d_str = stat.get('data_mod', '')
            if not d_str: continue # Nessuna data salvata
            try:
                # Prova prima formato ITA (es. 05/04/2026)
                d_mod = datetime.strptime(d_str, "%d/%m/%Y").date()
            except ValueError:
                try:
                    # Altrimenti interpreta il formato Google (es. 2026-04-05T22...)
                    d_mod = datetime.strptime(d_str[:10], "%Y-%m-%d").date()
                except: continue # Se proprio è illeggibile, salta
                
            if len(range_date) == 2:
                if not (range_date[0] <= d_mod <= range_date[1]): continue
            elif len(range_date) == 1:
                if d_mod != range_date[0]: continue
        
        # Altri Filtri
        if search_term and search_term not in (q['testo'] + " ".join(q['opzioni'].values())).lower(): continue
        if mod_scelto != "Tutti" and str(q.get('modulo')) != mod_scelto: continue
        if cart_scelta != "Tutte" and stat["cartella"] != cart_scelta: continue
        
        risultato.append(q)
    return risultato

domande_filtrate_base = filtra_domande()

# Gestione Simulazione Active Recall
if modalita == "🎯 Active Recall":
    st.sidebar.markdown("---")
    n_max = len(domande_filtrate_base)
    if n_max == 0:
        st.sidebar.warning("Nessuna domanda trovata coi filtri.")
        domande_filtrate = []
    else:
        n_q = st.sidebar.number_input("Quante domande?", 1, n_max, min(10, n_max))
        if st.sidebar.button("🎲 Genera Simulazione", type="primary", use_container_width=True):
            st.session_state.sim_ids = [q['id'] for q in random.sample(domande_filtrate_base, n_q)]
            st.session_state.indice = 0
            st.rerun()
            
        if 'sim_ids' in st.session_state and st.session_state.sim_ids:
            domande_filtrate = [q for q in db if q['id'] in st.session_state.sim_ids]
            st.sidebar.success(f"🔥 Simulazione attiva: {len(domande_filtrate)} domande")
        else:
            st.info("Imposta i filtri e clicca 'Genera Simulazione'.")
            st.stop()
else:
    domande_filtrate = domande_filtrate_base

# --- 6. VISUALIZZAZIONE ---
if not domande_filtrate:
    st.warning("Nessuna domanda trovata.")
    st.stop()

if 'indice' not in st.session_state: st.session_state.indice = 0
if st.session_state.indice >= len(domande_filtrate): st.session_state.indice = 0

q = domande_filtrate[st.session_state.indice]
k_q = u_key(q['id'])

if 'current_q_id' not in st.session_state or st.session_state.current_q_id != q['id']:
    st.session_state.current_q_id = q['id']
    st.session_state.answered = False
    st.session_state.esito = None

st.title("🚀 Andromeda 4.0")
st.markdown(f"**Domanda {q['id']}** | Modulo: `{q.get('modulo', 'N/A')}` | Sezione: `{q.get('sezione', 'N/A')}`")

if q.get('figura') == 'FIGURA':
    st.markdown("<div class='figura-alert'>⚠️ QUESTA DOMANDA CONTIENE UNA FIGURA (Controlla i PDF originali)</div>", unsafe_allow_html=True)

st.markdown(f"<div class='quesito-testo'>{q['testo']}</div>", unsafe_allow_html=True)

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
            
            # Controllo intelligente dell'indice
            if modalita == "📚 Esplorazione Libera" and cart_scelta != "Tutte":
                pass # Non avanza l'indice perché la domanda sparisce dalla lista filtrata
            else:
                if st.session_state.indice < len(domande_filtrate) - 1:
                    st.session_state.indice += 1
            st.rerun()

st.write("---")
c1, c2, c3 = st.columns([1, 2, 1])
if c1.button("⬅️ Indietro") and st.session_state.indice > 0:
    st.session_state.indice -= 1; st.session_state.answered = False; st.rerun()
c2.markdown(f"<center><b>{st.session_state.indice + 1} / {len(domande_filtrate)}</b></center>", unsafe_allow_html=True)
if c3.button("Avanti ➡️") and st.session_state.indice < len(domande_filtrate) - 1:
    st.session_state.indice += 1; st.session_state.answered = False; st.rerun()
