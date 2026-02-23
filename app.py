import streamlit as st
from cryptography.fernet import Fernet
import hashlib
import time
import uuid
import base64

# =====================================================
# 1. CONFIGURATION (IMPERATIF EN PREMIER)
# =====================================================
st.set_page_config(page_title="FREE-KONGOSSA V13", page_icon="🛰️", layout="centered")

# =====================================================
# 2. CACHE GLOBAL (LE TUNNEL COMMUN)
# =====================================================
@st.cache_resource
def get_shared_db():
    # Cette base est partagée entre TOUS les utilisateurs du serveur
    return {
        "FLUX": {},        # Contenu des messages
        "PRESENCE": {},    # Utilisateurs actifs
        "HISTORY": set()   # Anti-doublons
    }

DB = get_shared_db()

# =====================================================
# 3. MOTEUR DE CHIFFREMENT TTU
# =====================================================
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
# 4. DESIGN SOUVERAIN
# =====================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;600;900&display=swap');
.stApp { background:#050505; color:white; font-family:'Outfit', sans-serif; }
.msg-card {
    background: #111; padding: 15px; border-radius: 15px;
    margin-bottom: 15px; border: 1px solid #222;
}
.msg-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.user-tag { color: #00ffaa; font-weight: 900; font-size: 0.8em; }
.time-tag { opacity: 0.5; font-size: 0.7em; }
.presence-info { background: #00ffaa11; color: #00ffaa; padding: 5px 15px; border-radius: 20px; font-weight: bold; border: 1px solid #00ffaa; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# 5. SESSION & AUTH
# =====================================================
if "uid" not in st.session_state:
    st.session_state.uid = f"Z-{str(uuid.uuid4())[:4]}"

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🛰️ ACCÈS TUNNEL")
    key = st.text_input("Entrez le code secret", type="password")
    if st.button("OUVRIR LE FLUX"):
        sid = ENGINE.tunnel_id(key)
        if sid:
            st.session_state.sid = sid
            st.session_state.auth = True
            st.rerun()
    st.stop()

sid = st.session_state.sid
if sid not in DB["FLUX"]:
    DB["FLUX"][sid] = []

# Mise à jour de la présence (Qui est là ?)
DB["PRESENCE"][st.session_state.uid] = time.time()
active_count = len([u for u, t in DB["PRESENCE"].items() if time.time() - t < 20])

# =====================================================
# 6. AFFICHAGE DES MESSAGES (FIL PUBLIC)
# =====================================================
c1, c2 = st.columns([2,1])
c1.title("💬 Flux Public")
c2.markdown(f"<br><span class='presence-info'>🟢 {active_count} ACTIFS</span>", unsafe_allow_html=True)

st.markdown("---")

# On affiche TOUS les messages contenus dans DB["FLUX"][sid]
messages = DB["FLUX"][sid]

if not messages:
    st.info("Le tunnel est vide. Soyez le premier à briser le silence.")

for p in reversed(messages):
    is_me = p["sender"] == st.session_state.uid
    border_color = "#00ffaa" if is_me else "#444"
    
    st.markdown(f"""
    <div class="msg-card" style="border-left: 5px solid {border_color};">
        <div class="msg-header">
            <span class="user-tag">{"VOUS" if is_me else p['sender']}</span>
            <span class="time-tag">{p['time']}</span>
        </div>
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
        st.error("Échec de déchiffrement du signal")
    
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# 7. ENVOI DE MESSAGE
# =====================================================
st.markdown("<br><br>", unsafe_allow_html=True)
if "reset_key" not in st.session_state:
    st.session_state.reset_key = str(uuid.uuid4())

with st.expander("➕ DIFFUSER UN SIGNAL", expanded=True):
    t_signal = st.text_input("Titre (Optionnel)", key=f"t_{st.session_state.reset_key}")
    m_type = st.radio("Type de signal", ["Texte", "Média", "Vocal"], horizontal=True)

    if m_type == "Texte":
        txt = st.text_area("Votre message...", key=f"m_{st.session_state.reset_key}")
        if st.button("ENVOYER"):
            if txt:
                k, frags = ENGINE.encrypt_triadic(txt.encode())
                DB["FLUX"][sid].append({
                    "id": str(uuid.uuid4()), "sender": st.session_state.uid,
                    "k": k, "frags": frags, "is_txt": True, "type": "text",
                    "time": time.strftime("%H:%M")
                })
                st.session_state.reset_key = str(uuid.uuid4())
                st.rerun()

    elif m_type == "Média":
        file = st.file_uploader("Image ou Vidéo", key=f"f_{st.session_state.reset_key}")
        if file and st.button("DIFFUSER MÉDIA"):
            k, frags = ENGINE.encrypt_triadic(file.getvalue())
            DB["FLUX"][sid].append({
                "id": str(uuid.uuid4()), "sender": st.session_state.uid,
                "k": k, "frags": frags, "is_txt": False, "type": file.type,
                "time": time.strftime("%H:%M")
            })
            st.session_state.reset_key = str(uuid.uuid4())
            st.rerun()

    elif m_type == "Vocal":
        audio = st.audio_input("Microphone", key=f"a_{st.session_state.reset_key}")
        if audio and st.button("DIFFUSER VOCAL"):
            k, frags = ENGINE.encrypt_triadic(audio.getvalue())
            DB["FLUX"][sid].append({
                "id": str(uuid.uuid4()), "sender": st.session_state.uid,
                "k": k, "frags": frags, "is_txt": False, "type": "audio/wav",
                "time": time.strftime("%H:%M")
            })
            st.session_state.reset_key = str(uuid.uuid4())
            st.rerun()

# Rafraîchissement automatique pour voir les messages des autres
time.sleep(5)
st.rerun()
