import streamlit as st
import json
import re

st.set_page_config(page_title="Andromeda Repair Tool")
st.title("🛠️ Officina Andromeda")
st.write("Sto leggendo i file e fondendo le domande...")

try:
    # 1. Legge il database attuale
    with open('database_3000.json', 'r', encoding='utf-8') as f:
        db = json.load(f)
        
    # 2. Legge il file di testo con le 3000 domande
    with open('quiz.txt', 'r', encoding='utf-8', errors='ignore') as f:
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
                content = opt_match.group(2).strip()
                # Corregge le doppie "e. e."
                if content.lower().startswith('e. '):
                    content = content[3:].strip()
                elif content.lower() == 'e.':
                    content = "Nessuna delle precedenti" 
                parsed_data[current_q]['opzioni'][letter] = content
            else:
                if not parsed_data[current_q]['opzioni']:
                    parsed_data[current_q]['testo'].append(text)

    # 3. Inietta il testo nelle domande vuote
    domande_riparate = 0
    for q in db:
        q_id = str(q['id'])
        if q_id in parsed_data and len(parsed_data[q_id]['opzioni']) >= 4:
            q['testo'] = " ".join(parsed_data[q_id]['testo'])
            q['opzioni'] = parsed_data[q_id]['opzioni']
            if "⚠️" in q['testo']:
                q['testo'] = q['testo'].replace("⚠️ [QUESITO DA VERIFICARE] Testo originale non allineato nel PDF.", "").strip()
            domande_riparate += 1

    st.success(f"✅ Fusione completata alla perfezione! Ho riparato {domande_riparate} domande mancanti.")
    
    # Prepara il file per il download
    json_string = json.dumps(db, ensure_ascii=False, indent=4)
    
    st.download_button(
        label="📥 SCARICA IL DATABASE PERFETTO",
        data=json_string,
        file_name="database_3000_perfetto.json",
        mime="application/json",
        type="primary"
    )
    
except Exception as e:
    st.error(f"Impossibile completare. Assicurati che quiz.txt e database_3000.json siano su GitHub. Errore tecnico: {e}")
