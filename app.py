import streamlit as st
import json
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Andromeda 4.0 - Accesso Riservato", layout="wide")

# --- CONFIGURAZIONE MEMORIA ETERNA ---
URL_MEMORIA = "https://script.google.com/macros/s/AKfycbycL7hgRkaDC0KSMsStCMkU8QZNhkAto5d1eLGDRRecpAoQl6V7ks4A48P-avYo2E6I/exec"

st.markdown("""
<style>
    .domanda-titolo { font-weight: bold; font-size: 18pt; color: #1E88E5; }
    .quesito-testo { font-size: 16pt; font-style: italic; padding-top: 10px; padding-bottom: 20px; }
    .stRadio p { font-size: 10pt !important; font-weight: normal !important; }
</style>
""", unsafe_allow_html=True)

# --- 1. GESTIONE ACCESSO (LOGIN) E SICUREZZA ---
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None

# Controllo Scadenza Sessione (2 ore)
if st.session_state.logged_in_user is not None:
    if 'login_time' in st.session_state:
        if datetime.now() - st.session_state.login_time > timedelta(hours=2):
            st.session_state.logged_in_user = None
            st.warning("⏱️ Sessione scaduta per sicurezza (2 ore). Effettua nuovamente l'accesso.")

# Schermata di Login
if st.session_state.logged_in_user is None:
    st.markdown("<h1 style='text-align: center;'>🛡️ Andromeda 4.0</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: gray; margin-bottom: 40px;'>Seleziona il tuo profilo per iniziare l'allenamento</h4>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style='background-color: #1E88E5; padding: 40px; text-align: center; border-radius: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px;'>
            <h1 style='color: white; font-size: 80px; margin: 0;'>T</h1>
        </div>
        """, unsafe_allow_html=True)
        # Modificato il nome del bottone
        if st.button("Topolino", use_container_width=True):
            st.session_state.selected_acc = 'T'

    with col2:
        st.markdown("""
        <div style='background-color: #E91E63; padding: 40px; text-align: center; border-radius: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px;'>
            <h1 style='color: white; font-size: 80px; margin: 0;'>P</h1>
        </div>
        """, unsafe_allow_html=True)
        # Modificato il nome del bottone
        if st.button("Panciccia", use_container_width=True):
            st.session_state.selected_acc = 'P'

    if 'selected_acc' in st.session_state:
        acc = st.session_state.selected_acc
        st.markdown("---")
        pwd = st.text_input(f"🔑 Inserisci la password per sbloccare l'account:", type="password")
        if st.button("Sblocca Sistema", type="primary"):
            if (acc == 'T' and pwd == "topolino") or (acc == 'P' and pwd == "panciccia"):
                st.session_state.logged_in_user = acc
                st.session_state.login_time = datetime.now()
                st.rerun()
            else:
                st.error("❌ Password errata. Accesso negato.")
    
    st.stop() 

# --- 2. FUNZIONI DI DATABASE E SALVATAGGIO ---
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
    payload = [{"id": q_id, "corrette": val['corrette'], "errate": val['errate'], "cartella": val['cartella']} for q_id, val in stats.items()]
    try:
        requests.post(URL_MEMORIA, json=payload, timeout=15)
        return True
    except: return False

def u_key(base_id):
    return str(base_id) if st.session_state.logged_in_user == 'T' else f"{base_id}_P"

# --- 3. LOGICA DI AVVIO GLOBALE ---
db = carica_database()

if 'global_stats' not in st.session_state:
    stats_remote = carica_statistiche()
    g_stats = stats_remote if stats_remote else {}
    
    for q in db:
        base_id = str(q['id'])
        id_p = f"{base_id}_P"
        if base_id not in g_stats:
            g_stats[base_id] = {"corrette": 0, "errate": 0, "cartella": "Calderone"}
        if id_p not in g_stats:
            g_stats[id_p] = {"corrette": 0, "errate": 0, "cartella": "Calderone"}
            
    st.session_state.global_stats = g_stats

# --- 4. SIDEBAR E FILTRI ---
utente_attuale = "Topolino" if st.session_state.logged_in_user == 'T' else "Panciccia"
st.sidebar.success(f"👤 Connesso come: **{utente_attuale}**")
if st.sidebar.button("🚪 Esci (Logout)"):
    st.session_state.logged_in_user = None
    st.rerun()

st.sidebar.title("⚙️ Pannello di Controllo")
search_term = st.sidebar.text_input("🔍 Cerca parola (Testo o Opzioni):", "").lower()
ids_input = st.sidebar.text_input("🎯 ID specifici (es: 1, 5, 23):", "")
specific_ids = [s.strip() for s in ids_input.split(",") if s.strip()]

col1, col2 = st.sidebar.columns(2)
start_range = col1.number_input("Da ID:", 1, 3000, 1)
end_range = col2.number_input("A ID:", 1, 3000, 3000)

moduli = sorted(list(set([str(q.get('modulo', 'N/A')) for q in db])))
mod_scelto = st.sidebar.selectbox("Modulo:", ["Tutti"] + moduli)

cartelle_lista = ["Calderone", "Allenamento", "Campo sicuro", "Cassaforte"]
cart_scelta = st.sidebar.selectbox("📂 Cartella:", ["Tutte"] + cartelle_lista)

# --- 5. FILTRAGGIO ---
domande_filtrate = []
for q in db:
    q_id_str = str(q['id'])
    testo_c = (q['testo'] + " ".join(q['opzioni'].values())).lower()
    
    if specific_ids and q_id_str not in specific_ids: continue
    if not (start_range <= int(q['id']) <= end_range): continue
    if search_term and search_term not in testo_c: continue
    if mod_scelto != "Tutti" and str(q.get('modulo')) != mod_scelto: continue
    if cart_scelta != "Tutte" and st.session_state.global_stats[u_key(q_id_str)]["cartella"] != cart_scelta: continue
    
    domande_filtrate.append(q)

# --- 6. RICERCA INTELLIGENTE ---
if not domande_filtrate and specific_ids:
    for sid in specific_ids:
        k = u_key(sid)
        if k in st.session_state.global_stats:
            dove = st.session_state.global_stats[k]['cartella']
            st.info(f"💡 Nel tuo profilo, la domanda **{sid}** si trova in **{dove}**.")

if not domande_filtrate:
    st.warning("Nessuna domanda trovata nel tuo account con questi filtri.")
    st.stop()

# --- 7. NAVIGAZIONE E STATO ---
if 'indice' not in st.session_state: st.session_state.indice = 0
if st.session_state.indice >= len(domande_filtrate): st.session_state.indice = 0
q = domande_filtrate[st.session_state.indice]
q_id = str(q['id'])
chiave_utente_q = u_key(q_id)

if 'current_q_id' not in st.session_state or st.session_state.current_q_id != q_id:
    st.session_state.current_q_id = q_id
    st.session_state.answered = False
    st.session_state.esito = None

# --- 8. INTERFACCIA DOMANDA ---
st.title("🚀 Andromeda 4.0 Online")
st.markdown(f"<div class='domanda-titolo'>Domanda {q['id']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='quesito-testo'>{q['testo']}</div>", unsafe_allow_html=True)

scelta = st.radio("Risposta:", list(q['opzioni'].keys()), 
                  format_func=lambda x: f"{x.lower()}) {q['opzioni'][x]}", 
                  index=None, key=f"r_{q_id}", 
                  disabled=st.session_state.answered)

if scelta and not st.session_state.answered:
    st.session_state.answered = True
    if scelta == q['corretta']:
        st.session_state.esito = "ok"
        st.session_state.global_stats[chiave_utente_q]["corrette"] += 1
    else:
        st.session_state.esito = "no"
        st.session_state.global_stats[chiave_utente_q]["errate"] += 1
    st.rerun()

# --- 9. SMISTAMENTO POST-RISPOSTA ---
if st.session_state.answered:
    if st.session_state.esito == "ok": st.success(f"✅ CORRETTO! Era la {q['corretta'].upper()}")
    elif st.session_state.esito == "no": st.error(f"❌ ERRORE! Era la {q['corretta'].upper()}")
    
    st.subheader("📂 In quale cartella vuoi spostarla?")
    attuale = st.session_state.global_stats[chiave_utente_q]["cartella"]
    cols = st.columns(4)
    for i, c_name in enumerate(cartelle_lista):
        if cols[i].button(c_name, key=f"b_{c_name}", type="primary" if attuale == c_name else "secondary", use_container_width=True):
            st.session_state.global_stats[chiave_utente_q]["cartella"] = c_name
            with st.spinner("Salvataggio..."):
                salva_statistiche(st.session_state.global_stats)
            if st.session_state.indice < len(domande_filtrate) - 1:
                st.session_state.indice += 1
            st.rerun()

# --- 10. NAVIGAZIONE IN FONDO ---
st.write("---")
n_prev, n_count, n_next = st.columns([1, 2, 1])
with n_prev:
    if st.button("⬅️ Indietro") and st.session_state.indice > 0:
        st.session_state.indice -= 1
        st.rerun()
with n_count:
    st.markdown(f"<div style='text-align: center;'><b>{st.session_state.indice + 1} / {len(domande_filtrate)}</b></div>", unsafe_allow_html=True)
with n_next:
    if st.button("Avanti ➡️") and st.session_state.indice < len(domande_filtrate) - 1:
        st.session_state.indice += 1
        st.rerun()
