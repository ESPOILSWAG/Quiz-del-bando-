import streamlit as st
import json
import requests
import random
import csv
from datetime import datetime, timedelta

# Configurazione Pagina
st.set_page_config(page_title="Andromeda 4.0 - Training Center", layout="wide")

# Link Google Apps Script per la sincronizzazione
URL_MEMORIA = "https://script.google.com/macros/s/AKfycbycL7hgRkaDC0KSMsStCMkU8QZNhkAto5d1eLGDRRecpAoQl6V7ks4A48P-avYo2E6I/exec"

# Funzione per l'orario Italiano esatto (UTC+2)
def get_now_italy():
    return datetime.utcnow() + timedelta(hours=2)

# Traduttore temporale per gestire i formati di Google Sheets e i bug del fuso orario
def estrai_date_possibili(date_str):
    date_str = str(date_str).strip()
    if not date_str: return []
    d_mod = None
    if "T" in date_str:
        try:
            dt_utc = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
            d_mod = (dt_utc + timedelta(hours=2)).date()
        except:
            try: d_mod = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
            except: pass
    else:
        try:
            if "-" in date_str:
                p = date_str.split(" ")[0].split("-")
                d_mod = datetime(int(p[0]), int(p[1]), int(p[2])).date() if len(p[0])==4 else datetime(int(p[2]), int(p[1]), int(p[0])).date()
            elif "/" in date_str:
                p = date_str.split(" ")[0].split("/")
                d_mod = datetime(int(p[2]), int(p[1]), int(p[0])).date() if len(p[2])==4 else datetime(int(p[0]), int(p[1]), int(p[2])).date()
        except: pass
    if not d_mod: return []
    possibili = [d_mod]
    if d_mod.day <= 12 and d_mod.day != d_mod.month:
        try: possibili.append(datetime(d_mod.year, d_mod.day, d_mod.month).date())
        except: pass
    return possibili

# Stili CSS Obbligatori: Domanda grassetto, Testo 16pt corsivo, Opzioni 10pt tondo
st.markdown("""
<style>
    .domanda-titolo { font-weight: bold; font-size: 18pt; color: #1E88E5; }
    .quesito-testo { font-size: 16pt; font-style: italic; padding-top: 10px; padding-bottom: 20px; }
    .stRadio p { font-size: 10pt !important; font-weight: normal !important; }
    .figura-alert { 
        background-color: #FFF3E0; border-left: 5px solid #FF9800; padding: 15px; 
        color: #E65100; font-size: 14pt; font-weight: bold; margin-bottom: 15px; border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# 1. ACCESSO E SICUREZZA (Gestione Account T e P)
if 'logged_in_user' not in st.session_state:
    st.session_state['logged_in_user'] = None

if st.session_state.get('logged_in_user') is not None:
    if 'login_time' in st.session_state:
        if get_now_italy() - st.session_state['login_time'] > timedelta(hours=2):
            st.session_state['logged_in_user'] = None
            st.rerun()

if st.session_state.get('logged_in_user') is None:
    st.markdown("<h1 style='text-align: center;'>🛡️ Andromeda 4.0</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div style='background-color: #1E88E5; padding: 40px; text-align: center; border-radius: 20px;'><h1 style='color: white; font-size: 80px; margin: 0;'>T</h1></div>", unsafe_allow_html=True)
        if st.button("T", use_container_width=True): st.session_state['selected_acc'] = 'T'
    with col2:
        st.markdown("<div style='background-color: #E91E63; padding: 40px; text-align: center; border-radius: 20px;'><h1 style='color: white; font-size: 80px; margin: 0;'>P</h1></div>", unsafe_allow_html=True)
        if st.button("P", use_container_width=True): st.session_state['selected_acc'] = 'P'

    if 'selected_acc' in st.session_state:
        pwd = st.text_input(f"Password per {st.session_state['selected_acc']}:", type="password")
        if st.button("Sblocca", type="primary"):
            if (st.session_state['selected_acc'] == 'T' and pwd == "topolino") or (st.session_state['selected_acc'] == 'P' and pwd == "panciccia"):
                st.session_state['logged_in_user'] = st.session_state['selected_acc']
                st.session_state['login_time'] = get_now_italy()
                st.rerun()
            else: st.error("❌ Password errata.")
    st.stop()

# 2. CARICAMENTO DATI
def carica_database():
    try:
        with open('database_3000.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
    except: return []
    mappatura_figure = {}
    try:
        with open('mappatura.csv', 'r', encoding='utf-8-sig') as f_csv:
            reader = csv.reader(f_csv, delimiter=';' if ';' in f_csv.readline() else ',')
            f_csv.seek(0)
            for row in reader:
                if row and 'FIGURA' in str(row).upper(): mappatura_figure[str(row[0]).strip()] = True
    except: pass
    for q in db: q['figura'] = 'FIGURA' if str(q.get('id')) in mappatura_figure else ''
    return db

def carica_statistiche():
    try:
        r = requests.get(URL_MEMORIA, timeout=10)
        dati = r.json()
        return {str(row[0]): {"corrette": int(row[1]), "errate": int(row[2]), "cartella": str(row[3]), "data_mod": str(row[4]) if len(row) > 4 else ""} for row in dati[1:]}
    except: return None

def salva_statistiche(stats):
    payload = [{"id": k, "corrette": v['corrette'], "errate": v['errate'], "cartella": v['cartella'], "data_modifica": v.get('data_mod', '')} for k, v in stats.items()]
    try: requests.post(URL_MEMORIA, json=payload, timeout=15); return True
    except: return False

def u_key(base_id):
    return str(base_id) if st.session_state.get('logged_in_user') == 'T' else f"{base_id}_P"

db = carica_database()
if 'global_stats' not in st.session_state:
    remote = carica_statistiche()
    st.session_state['global_stats'] = remote if remote else {}
    for q in db:
        for k in [str(q['id']), f"{q['id']}_P"]:
            if k not in st.session_state['global_stats']:
                st.session_state['global_stats'][k] = {"corrette": 0, "errate": 0, "cartella": "Calderone", "data_mod": ""}

# 3. FILTRI SIDEBAR
st.sidebar.success(f"👤 Account: **{st.session_state.get('logged_in_user')}**")
if st.sidebar.button("🚪 Logout"):
    st.session_state['logged_in_user'] = None
    st.rerun()

modalita = st.sidebar.radio("🧠 Modalità:", ["📚 Esplorazione Libera", "🎯 Active Recall"])
abilita_data = st.sidebar.checkbox("Filtra per data")
range_date = st.sidebar.date_input("Periodo:", value=[]) if abilita_data else []

ids_input = st.sidebar.text_input("ID specifici (es: 1, 150):", "")
specific_ids = [s.strip() for s in ids_input.split(",") if s.strip()]
c_n1, c_n2 = st.sidebar.columns(2)
start_range = c_n1.number_input("Da:", 1, 3000, 1)
end_range = c_n2.number_input("A:", 1, 3000, 3000)

search_term = st.sidebar.text_input("🔍 Cerca:", "").lower()
mod_scelto = st.sidebar.selectbox("Modulo:", ["Tutti"] + sorted(list(set([str(q.get('modulo', 'N/A')) for q in db]))))
cartelle_lista = ["Calderone", "Allenamento", "Campo sicuro", "Cassaforte"]
cart_scelta = st.sidebar.selectbox("Cartella:", ["Tutte"] + cartelle_lista)

# 4. LOGICA FILTRO
def filtra_domande():
    risultato = []
    for q in db:
        k = u_key(q['id'])
        stat = st.session_state['global_stats'][k]
        if specific_ids and str(q['id']) not in specific_ids: continue
        if not (start_range <= int(q['id']) <= end_range): continue
        if abilita_data and range_date:
            date_possibili = estrai_date_possibili(stat.get('data_mod', ''))
            match = False
            for d in date_possibili:
                if isinstance(range_date, (list, tuple)):
                    if len(range_date) == 2 and range_date[0] <= d <= range_date[1]: match = True; break
                    elif len(range_date) == 1 and d == range_date[0]: match = True; break
                elif d == range_date: match = True; break
            if not match: continue
        if search_term and search_term not in (q['testo'] + " ".join(q['opzioni'].values())).lower(): continue
        if mod_scelto != "Tutti" and str(q.get('modulo')) != mod_scelto: continue
        if cart_scelta != "Tutte" and stat["cartella"] != cart_scelta: continue
        risultato.append(q)
    return risultato

domande_filtrate = filtra_domande()

# 5. VISUALIZZAZIONE
st.title("🚀 Andromeda 4.0")
if not domande_filtrate: st.warning("Nessuna domanda trovata."); st.stop()

if 'indice' not in st.session_state or st.session_state['indice'] >= len(domande_filtrate):
    st.session_state['indice'] = 0

q = domande_filtrate[st.session_state['indice']]
k_q = u_key(q['id'])

if 'current_q_id' not in st.session_state or st.session_state['current_q_id'] != q['id']:
    st.session_state['current_q_id'] = q['id']; st.session_state['answered'] = False

st.markdown(f"**Domanda {q['id']}** | Modulo: `{q.get('modulo', 'N/A')}`")
if q.get('figura') == 'FIGURA': st.markdown("<div class='figura-alert'>⚠️ QUESTA DOMANDA CONTIENE UNA FIGURA</div>", unsafe_allow_html=True)

st.markdown(f"<div class='quesito-testo'>{q['testo']}</div>", unsafe_allow_html=True)

scelta = st.radio("Risposta:", list(q['opzioni'].keys()), format_func=lambda x: f"{x.lower()}) {q['opzioni'][x]}", index=None, key=f"r_{q['id']}", disabled=st.session_state.get('answered', False))

if scelta and not st.session_state.get('answered', False):
    st.session_state['answered'] = True
    st.session_state['global_stats'][k_q]["data_mod"] = get_now_italy().strftime("%Y-%m-%d")
    if scelta == q['corretta']:
        st.session_state['esito'] = "ok"; st.session_state['global_stats'][k_q]["corrette"] += 1
    else:
        st.session_state['esito'] = "no"; st.session_state['global_stats'][k_q]["errate"] += 1
    st.rerun()

if st.session_state.get('answered', False):
    if st.session_state.get('esito') == "ok": st.success(f"Corretto! Risposta: {q['corretta'].upper()}")
    else: st.error(f"Sbagliato! Era la {q['corretta'].upper()}")
    
    cols = st.columns(4)
    for i, c_name in enumerate(cartelle_lista):
        if cols[i].button(c_name, key=f"b_{c_name}", use_container_width=True):
            st.session_state['global_stats'][k_q]["cartella"] = c_name
            st.session_state['global_stats'][k_q]["data_mod"] = get_now_italy().strftime("%Y-%m-%d")
            salva_statistiche(st.session_state['global_stats'])
            st.session_state['answered'] = False
            if st.session_state['indice'] < len(domande_filtrate) - 1: st.session_state['indice'] += 1
            st.rerun()

st.write("---")
c1, c2, c3 = st.columns([1, 2, 1])
if c1.button("⬅️ Indietro") and st.session_state['indice'] > 0:
    st.session_state['indice'] -= 1; st.session_state['answered'] = False; st.rerun()
c2.markdown(f"<center><b>{st.session_state['indice'] + 1} / {len(domande_filtrate)}</b></center>", unsafe_allow_html=True)
if c3.button("Avanti ➡️") and st.session_state['indice'] < len(domande_filtrate) - 1:
    st.session_state['indice'] += 1; st.session_state['answered'] = False; st.rerun()
