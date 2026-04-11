import streamlit as st
import json
import re

st.set_page_config(page_title="Andromeda Hybrid Repair")
st.title("🛠️ Officina Andromeda: Riparazione Ibrida")
st.write("Sto fondendo il vecchio database (buono) con i nuovi testi (corretti)...")

def pulisci_testo(t):
    # Sistema i problemi comuni di conversione Word -> Text
    t = t.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
    return t.strip()

try:
    # 1. Carica il database vecchio (quello con le 2846 domande perfette)
    with open('database_vecchio.json', 'r', encoding='utf-8') as f:
        db = json.load(f)
        
    # 2. Tenta di leggere il quiz.txt con diverse codifiche per non perdere gli accenti
    try:
        with open('quiz.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open('quiz.txt', 'r', encoding='latin-1') as f:
            lines = f.readlines()
        
    parsed_data = {}
    current_q = None
    q_pattern = re.compile(r'^Domanda\s+(\d+)', re.IGNORECASE)
    opt_pattern = re.compile(r'^([a-e])\.\s*(.*)', re.IGNORECASE)

    for line in lines:
        text = line.strip()
        if not text: continue
        
        q_match = q_pattern.match(text)
        if q_match:
            current_q = str(q_match.group(1))
            parsed_data[current_q] = {'testo': [], 'opzioni': {}}
            continue
            
        if current_q:
            opt_match = opt_pattern.match(text)
            if opt_match:
                letter = opt_match.group(1).lower()
                content = pulisci_testo(opt_match.group(2))
                if content.lower().startswith('e. '): content = content[3:].strip()
                elif content.lower() == 'e.': content = "Nessuna delle precedenti" 
                parsed_data[current_q]['opzioni'][letter] = content
            else:
                if not parsed_data[current_q]['opzioni']:
                    parsed_data[current_q]['testo'].append(pulisci_testo(text))

    # 3. OPERAZIONE CHIRURGICA
    riparate = 0
    mantenute = 0
    
    for q in db:
        q_id = str(q['id'])
        # SOVRASCRIVE SOLO SE la domanda era "vuota" o aveva l'errore del PDF
        if "Da definire" in str(q['opzioni']) or "[QUESITO DA VERIFICARE]" in q['testo']:
            if q_id in parsed_data:
                q['testo'] = " ".join(parsed_data[q_id]['testo'])
                q['opzioni'] = parsed_data[q_id]['opzioni']
                riparate += 1
        else:
            mantenute += 1

    st.success(f"✅ Operazione riuscita!")
    st.info(f"Omsa: {mantenute} domande originali preservate (ortografia intatta).")
    st.info(f"Riparate: {riparate} domande che erano vuote o errate.")
    
    # Controllo domanda 3000
    if "3000" in parsed_data and len(db) < 3000:
        st.warning("Sto aggiungendo la domanda 3000 che mancava nel vecchio file...")
        nuova_3000 = {
            "id": 3000,
            "testo": " ".join(parsed_data["3000"]['testo']),
            "opzioni": parsed_data["3000"]['opzioni'],
            "corretta": "a", # Da verificare manualmente
            "modulo": "2",
            "sezione": "Burocrazia"
        }
        db.append(nuova_3000)

    json_string = json.dumps(db, ensure_ascii=False, indent=4)
    st.download_button(
        label="📥 SCARICA IL DATABASE IBRIDO PERFETTO",
        data=json_string,
        file_name="database_3000.json",
        type="primary"
    )
    
except Exception as e:
    st.error(f"Errore: {e}. Assicurati di avere 'database_vecchio.json' e 'quiz.txt' su GitHub.")
