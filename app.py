import streamlit as st
from cryptography.fernet import Fernet
import hashlib
import time
import uuid
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# =====================================================
# 1. CONFIGURATION AVANCÉE
# =====================================================
st.set_page_config(page_title="KONGOSSA ULTRA V14", page_icon="🥷", layout="wide")

# Initialisation de la base de données SQL locale
def init_db():
    conn = sqlite3.connect('vault.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (id TEXT, tunnel_id TEXT, sender TEXT, key TEXT, frags BLOB, 
                  m_type TEXT, timestamp DATETIME)''')
    conn.commit()
    return conn

db_conn = init_db()

# =====================================================
# 2. MOTEUR CRYPTO RENFORCÉ
# =====================================================
class UltraEngine:
    @staticmethod
    def get_sid(passkey):
        return hashlib.sha3_512(passkey.encode()).hexdigest()[:16]

    @staticmethod
    def pack(data):
        key = Fernet.generate_key()
        f = Fernet(key)
        token = f.encrypt(data)
        # Division dynamique en 3 segments
        size = len(token)
        parts = [token[:size//3], token[size//3:2*size//3], token[2*size//3:]]
        return key.decode(), parts

    @staticmethod
    def unpack(key, parts):
        f = Fernet(key.encode())
        return f.decrypt(b"".join(parts))

ENGINE = UltraEngine()

# =====================================================
# 3. DESIGN "DEEP WEB"
# =====================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;500&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #030303;
        color: #00ff41;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .stTextInput>div>div>input { background-color: #111; color: #00ff41; border: 1px solid #00ff41; }
    
    .msg-box {
        background: rgba(10, 10, 10, 0.9);
        border: 1px solid #1a1a1a;
        padding: 20px;
        border-radius: 5px;
        margin: 10px 0;
        transition: 0.3s;
    }
    .msg-box:hover { border-color: #00ff41; box-shadow: 0 0 10px #00ff4133; }
    
    .meta { font-size: 0.7em; color: #555; margin-bottom: 10px; }
    .sender-id { color: #ff0055; font-weight: bold; }
    .status-bar { border-top: 1px solid #333; padding-top: 10px; font-size: 0.8em; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# 4. LOGIQUE DE SESSION
# =====================================================
if "uid" not in st.session_state:
    st.session_state.uid = f"NODE-{str(uuid.uuid4())[:6].upper()}"

if "authenticated" not in st.session_state:
    st.title("📟 ACCÈS TERMINAL KONGOSSA")
    access_code = st.text_input("PASSWORD_ENTRY >", type="password")
    if st.button("INITIALISER LE TUNNEL"):
        if access_code:
            st.session_state.sid = ENGINE.get_sid(access_code)
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# =====================================================
# 5. ACTIONS DB (ÉCRITURE/LECTURE)
# =====================================================
def send_signal(content, m_type):
    key, frags = ENGINE.pack(content)
    c = db_conn.cursor()
    c.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?)",
              (str(uuid.uuid4()), st.session_state.sid, st.session_state.uid, 
               key, sqlite3.Binary(b"||".join(frags)), m_type, datetime.now()))
    db_conn.commit()

def get_signals():
    # Suppression auto des messages de + de 24h
    c = db_conn.cursor()
    limit = datetime.now() - timedelta(hours=24)
    c.execute("DELETE FROM messages WHERE timestamp < ?", (limit,))
    db_conn.commit()
    
    # Récupération du tunnel actuel
    df = pd.read_sql_query(f"SELECT * FROM messages WHERE tunnel_id='{st.session_state.sid}' ORDER BY timestamp DESC", db_conn)
    return df

# =====================================================
# 6. INTERFACE DE DIFFUSION
# =====================================================
sid = st.session_state.sid
st.sidebar.title(f"🛰️ TUNNEL: {sid}")
st.sidebar.write(f"VOTRE_ID: {st.session_state.uid}")

if st.sidebar.button("LOGOUT / PURGE"):
    st.session_state.clear()
    st.rerun()

with st.container():
    col1, col2 = st.columns([4, 1])
    with col1:
        msg_input = st.chat_input("Transmettre un signal dans le tunnel...")
    with col2:
        file_upload = st.file_uploader("Fichier", label_visibility="collapsed")

if msg_input:
    send_signal(msg_input.encode(), "text")
    st.rerun()

if file_upload:
    send_signal(file_upload.getvalue(), file_upload.type)
    st.success("Média injecté.")
    time.sleep(1)
    st.rerun()

# =====================================================
# 7. FLUX DE RÉCEPTION (DECRYPT)
# =====================================================
signals = get_signals()

for _, row in signals.iterrows():
    with st.container():
        st.markdown(f'<div class="msg-box">', unsafe_allow_html=True)
        st.markdown(f'<div class="meta"><span class="sender-id">{row["sender"]}</span> @ {row["timestamp"][:16]}</div>', unsafe_allow_html=True)
        
        try:
            # Reconstruction des fragments
            frags = row["frags"].split(b"||")
            raw_data = ENGINE.unpack(row["key"], frags)
            
            if "text" in row["m_type"]:
                st.write(raw_data.decode())
            elif "image" in row["m_type"]:
                st.image(raw_data)
            elif "video" in row["m_type"]:
                st.video(raw_data)
            elif "audio" in row["m_type"]:
                st.audio(raw_data)
        except:
            st.error("SIGNAL CORROMPU OU CLÉ INVALIDE")
            
        st.markdown('</div>', unsafe_allow_html=True)

# Rafraîchissement intelligent
time.sleep(10)
st.rerun()
