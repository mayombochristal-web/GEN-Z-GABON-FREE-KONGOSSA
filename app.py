import streamlit as st
from cryptography.fernet import Fernet
import hashlib
import time
import datetime
import base64
import uuid

# =====================================================
# CONFIG APP
# =====================================================
st.set_page_config(
    page_title="GEN Z GABON FREE-KONGOSSA",
    page_icon="🛰️",
    layout="centered"
)

# =====================================================
# LOAD LOGO
# =====================================================
def load_logo(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

LOGO = load_logo("logo_free_kongossa.png")

# =====================================================
# VAULT TTU (ETAT FANTÔME PERMANENT)
# =====================================================
@st.cache_resource
def init_vault():
    return {
        "FLUX": {},
        "COMMENTS": {},
        "REACTIONS": {},
        "HISTORY": set(),
        "LAST_UPDATE": time.time()
    }

DB = init_vault()

# =====================================================
# TTU ENGINE
# =====================================================
class TTUEngine:
    @staticmethod
    def tunnel_id(key):
        if not key: return None
        return hashlib.sha256(key.encode()).hexdigest()[:12]

    @staticmethod
    def encrypt_triadic(data):
        k = Fernet.generate_key()
        box = Fernet(k).encrypt(data)
        l = len(box)
        return k, [box[:l//3], box[l//3:2*l//3], box[2*l//3:]]

    @staticmethod
    def decrypt_triadic(k, frags):
        return Fernet(k).decrypt(b"".join(frags))

ENGINE = TTUEngine()

# =====================================================
# DESIGN TTU SOUVERAIN
# =====================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;600;900&display=swap');
.stApp { background:#050505; color:white; font-family:'Outfit', sans-serif; }
.title { text-align:center; font-size:28px; font-weight:800; color:#00ffaa; margin-bottom:20px; }
.card { background:#0f0f0f; padding:20px; margin-bottom:25px; border-radius:18px; border:1px solid #1c1c1c; position:relative; }
.signal-header { color:#00ffaa; font-weight:900; text-transform:uppercase; font-size:0.9em; letter-spacing:1px; margin-bottom:10px; border-bottom:1px solid #00ffaa22; padding-bottom:5px; }
.comment { background:#1a1a1a; padding:10px; margin:8px 0; border-left:3px solid #00ffaa; border-radius:8px; font-size:0.85em; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# AUTH TUNNEL
# =====================================================
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    if LOGO:
        st.markdown(f"<center><img src='data:image/png;base64,{LOGO}' width='140'></center>", unsafe_allow_html=True)
    st.markdown("<div class='title'>ACCÈS AU TUNNEL</div>", unsafe_allow_html=True)
    key = st.text_input("Code Tunnel", type="password")
    if st.button("S'AUTHENTIFIER"):
        sid = ENGINE.tunnel_id(key)
        if sid:
            st.session_state.sid = sid
            st.session_state.auth = True
            st.rerun()
    st.stop()

sid = st.session_state.sid
if sid not in DB["FLUX"]: DB["FLUX"][sid] = []

# =====================================================
# FIL D'ACTUALITÉ
# =====================================================
st.markdown("<div class='title'>GEN Z GABON — FREE KONGOSSA</div>", unsafe_allow_html=True)

for p in reversed(DB["FLUX"][sid]):
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        if p.get("title"):
            st.markdown(f"<div class='signal-header'>{p['title']}</div>", unsafe_allow_html=True)
        
        try:
            raw = ENGINE.decrypt_triadic(p["k"], p["frags"])
            if p["is_txt"]: st.write(raw.decode())
            else:
                if "image" in p["type"]: st.image(raw, use_container_width=True)
                elif "video" in p["type"]: st.video(raw)
                elif "audio" in p["type"]: st.audio(raw)
        except:
            st.warning("Signal corrompu ou expiré")

        # DISCUSSIONS
        comms = DB["COMMENTS"].get(p["id"], [])
        with st.expander(f"💬 Discussions ({len(comms)})"):
            for c in comms:
                st.markdown(f"<div class='comment'>{c}</div>", unsafe_allow_html=True)
            
            t_input = st.text_input("Ajouter un commentaire", key=f"in_{p['id']}")
            if st.button("Envoyer", key=f"btn_{p['id']}"):
                if t_input:
                    DB["COMMENTS"].setdefault(p["id"], []).append(t_input)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# EMISSION DE SIGNAL
# =====================================================
st.markdown("---")
with st.expander("➕ ÉMETTRE UN NOUVEAU SIGNAL", expanded=False):
    t_signal = st.text_input("Titre du Signal")
    tabs = st.tabs(["💬 Texte", "📸 Média", "🎙️ Vocal"])

    with tabs[0]:
        txt = st.text_area("Votre message")
        if st.button("Diffuser Texte"):
            if txt:
                data = txt.encode()
                k, frags = ENGINE.encrypt_triadic(data)
                DB["FLUX"][sid].append({
                    "id": str(uuid.uuid4()), "k": k, "frags": frags,
                    "is_txt": True, "type": "text", "title": t_signal, "ts": time.time()
                })
                st.rerun()

    with tabs[1]:
        file = st.file_uploader("Fichier")
        if file and st.button("Diffuser Média"):
            k, frags = ENGINE.encrypt_triadic(file.getvalue())
            DB["FLUX"][sid].append({
                "id": str(uuid.uuid4()), "k": k, "frags": frags,
                "is_txt": False, "type": file.type, "title": t_signal, "ts": time.time()
            })
            st.rerun()

    with tabs[2]:
        audio = st.audio_input("Microphone")
        if audio:
            k, frags = ENGINE.encrypt_triadic(audio.getvalue())
            DB["FLUX"][sid].append({
                "id": str(uuid.uuid4()), "k": k, "frags": frags,
                "is_txt": False, "type": "audio/wav", "title": t_signal, "ts": time.time()
            })
            st.rerun()

# GHOST REFRESH (TST SYNC)
time.sleep(8)
st.rerun()
