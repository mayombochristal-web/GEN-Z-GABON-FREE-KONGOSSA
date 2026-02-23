import streamlit as st
from cryptography.fernet import Fernet
import hashlib
import time
import uuid
import base64

# =====================================================
# CONFIGURATION & STYLE GEN Z GABON
# =====================================================
st.set_page_config(page_title="FREE-KONGOSSA V13", page_icon="🛰️", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;600;900&display=swap');
.stApp { background:#050505; color:white; font-family:'Outfit', sans-serif; }

/* Structure des Bulles de Chat */
.chat-container { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.message-row { display: flex; width: 100%; margin-bottom: 10px; }
.msg-me { justify-content: flex-end; }
.msg-them { justify-content: flex-start; }

.bubble {
    max-width: 80%; padding: 12px 16px; border-radius: 18px;
    position: relative; font-size: 0.95em; line-height: 1.4;
}
.bubble-me { background: #00ffaa; color: black; border-bottom-right-radius: 2px; }
.bubble-them { background: #1a1a1a; color: white; border: 1px solid #333; border-bottom-left-radius: 2px; }

.meta { font-size: 0.7em; margin-top: 5px; opacity: 0.6; display: block; }
.user-id { font-weight: 900; font-size: 0.75em; color: #00ffaa; margin-bottom: 4px; display: block; }
.meta-me { color: #004422; text-align: right; }

/* Badge présence */
.presence-badge {
    background: #00ffaa22; color: #00ffaa; border: 1px solid #00ffaa;
    padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# MOTEUR TTU-MC3 & CACHE
# =====================================================
@st.cache_resource
def init_vault():
    return {
        "FLUX": {},
        "PRESENCE": {}, # {user_id: last_seen_timestamp}
        "REACTIONS": {},
        "LAST_SYNC": time.time()
    }

DB = init_vault()

class TTUEngine:
    @staticmethod
    def tunnel_id(key):
        return hashlib.sha256(key.encode()).hexdigest()[:12] if key else None

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
# SESSION & AUTHENTIFICATION
# =====================================
if "uid" not in st.session_state:
    st.session_state.uid = f"Z-{str(uuid.uuid4())[:4]}" # Identifiant unique de l'appareil

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center;'>🛰️ FREE-KONGOSSA</h1>", unsafe_allow_html=True)
    key = st.text_input("Code Secret du Tunnel", type="password")
    if st.button("OUVRIR LE SIGNAL"):
        sid = ENGINE.tunnel_id(key)
        if sid:
            st.session_state.sid, st.session_state.auth = sid, True
            st.rerun()
    st.stop()

sid = st.session_state.sid
if sid not in DB["FLUX"]: DB["FLUX"][sid] = []

# Update Présence (TST Sync)
DB["PRESENCE"][st.session_state.uid] = time.time()
active_users = [u for u, t in DB["PRESENCE"].items() if time.time() - t < 15]

# =====================================================
# INTERFACE DE CONVERSATION
# =====================================================
cols = st.columns([2, 1])
cols[0].title("💬 Tunnel Flux")
cols[1].markdown(f"<div style='text-align:right; margin-top:25px;'><span class='presence-badge'>🟢 {len(active_users)} Actifs</span></div>", unsafe_allow_html=True)

# Affichage des messages organisés
st.markdown("---")
for p in DB["FLUX"][sid]:
    is_me = p["sender"] == st.session_state.uid
    row_class = "msg-me" if is_me else "msg-them"
    bubble_class = "bubble-me" if is_me else "bubble-them"
    meta_class = "meta-me" if is_me else ""

    st.markdown(f"""
    <div class="message-row {row_class}">
        <div class="bubble {bubble_class}">
            {f'<span class="user-id">{p["sender"]}</span>' if not is_me else ""}
            <div class="content">
    """, unsafe_allow_html=True)

    try:
        raw = ENGINE.decrypt_triadic(p["k"], p["frags"])
        if p["is_txt"]:
            st.write(raw.decode())
        else:
            if "image" in p["type"]: st.image(raw)
            elif "video" in p["type"]: st.video(raw)
            elif "audio" in p["type"]: st.audio(raw)
    except:
        st.error("Signal corrompu")

    st.markdown(f"""
            </div>
            <span class="meta {meta_class}">{p['time']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# EMISSION (STATION DE SIGNAL)
# =====================================================
st.markdown("<br><br>", unsafe_allow_html=True)
if "reset_key" not in st.session_state: st.session_state.reset_key = str(uuid.uuid4())

with st.container():
    tabs = st.tabs(["💬 Texte", "📸 Média", "🎙️ Vocal"])
    
    with tabs[0]:
        with st.form("text_form", clear_on_submit=True):
            txt = st.text_area("Message secret...", placeholder="Raconte ici...")
            if st.form_submit_button("DIFFUSER"):
                if txt:
                    k, frags = ENGINE.encrypt_triadic(txt.encode())
                    DB["FLUX"][sid].append({
                        "id": str(uuid.uuid4()), "sender": st.session_state.uid,
                        "k": k, "frags": frags, "is_txt": True, "type": "text",
                        "time": time.strftime("%H:%M")
                    })
                    st.rerun()

    with tabs[1]:
        file = st.file_uploader("Image/Vidéo", key=f"file_{st.session_state.reset_key}")
        if file and st.button("Envoyer Média"):
            k, frags = ENGINE.encrypt_triadic(file.getvalue())
            DB["FLUX"][sid].append({
                "id": str(uuid.uuid4()), "sender": st.session_state.uid,
                "k": k, "frags": frags, "is_txt": False, "type": file.type,
                "time": time.strftime("%H:%M")
            })
            st.session_state.reset_key = str(uuid.uuid4())
            st.rerun()

    with tabs[2]:
        audio = st.audio_input("Microphone", key=f"audio_{st.session_state.reset_key}")
        if audio and st.button("🚀 Diffuser Vocal"):
            k, frags = ENGINE.encrypt_triadic(audio.getvalue())
            DB["FLUX"][sid].append({
                "id": str(uuid.uuid4()), "sender": st.session_state.uid,
                "k": k, "frags": frags, "is_txt": False, "type": "audio/wav",
                "time": time.strftime("%H:%M")
            })
            st.session_state.reset_key = str(uuid.uuid4())
            st.rerun()

# Sync Auto (GHOST REFRESH)
time.sleep(5)
st.rerun()
