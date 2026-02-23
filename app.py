import streamlit as st
from cryptography.fernet import Fernet
import hashlib
import time
import uuid
import base64
import os

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="FREE-KONGOSSA V14 ULTRA",
    page_icon="🛰️",
    layout="centered"
)

# =====================================================
# GLOBAL SHARED MEMORY
# =====================================================
@st.cache_resource
def get_db():
    return {
        "FLUX": {},
        "PRESENCE": {},
        "SIGNATURES": set()
    }

DB = get_db()

# =====================================================
# TTU ENGINE ULTRA
# =====================================================
class TTUEngine:

    # ---- tunnel id ----
    @staticmethod
    def tunnel_id(secret):
        return hashlib.sha256(secret.encode()).hexdigest()[:16]

    # ---- derive stable key ----
    @staticmethod
    def derive_key(secret):
        k = hashlib.pbkdf2_hmac(
            "sha256",
            secret.encode(),
            b"KONGOSSA-SALT",
            100000
        )
        return base64.urlsafe_b64encode(k[:32])

    # ---- triadic encryption ----
    @staticmethod
    def encrypt(secret, data):

        key = TTUEngine.derive_key(secret)
        box = Fernet(key).encrypt(data)

        n = len(box)
        cuts = [n//3, 2*n//3]

        return [
            box[:cuts[0]],
            box[cuts[0]:cuts[1]],
            box[cuts[1]:]
        ]

    # ---- decrypt ----
    @staticmethod
    def decrypt(secret, frags):
        key = TTUEngine.derive_key(secret)
        return Fernet(key).decrypt(b"".join(frags))

ENGINE = TTUEngine()

# =====================================================
# DESIGN ULTRA
# =====================================================
st.markdown("""
<style>
.stApp {background:#040404;color:white;font-family:monospace;}
.msg{
 padding:14px;border-radius:14px;margin:10px 0;
 background:#101010;border:1px solid #222;
}
.me{border-left:5px solid #00ffaa;}
.other{border-left:5px solid #555;}
.timer{opacity:.6;font-size:12px}
.badge{
 background:#00ffaa22;
 padding:4px 10px;
 border-radius:20px;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# SESSION INIT
# =====================================================
if "uid" not in st.session_state:
    st.session_state.uid = f"Z-{uuid.uuid4().hex[:4]}"

if "auth" not in st.session_state:
    st.session_state.auth = False

# =====================================================
# AUTH
# =====================================================
if not st.session_state.auth:

    st.title("🛰️ FREE-KONGOSSA ULTRA")

    secret = st.text_input("Code secret", type="password")

    if st.button("ENTRER"):
        if secret:
            st.session_state.secret = secret
            st.session_state.sid = ENGINE.tunnel_id(secret)
            st.session_state.auth = True
            st.rerun()

    st.stop()

secret = st.session_state.secret
sid = st.session_state.sid

if sid not in DB["FLUX"]:
    DB["FLUX"][sid] = []

# =====================================================
# PRESENCE HEARTBEAT
# =====================================================
now = time.time()
DB["PRESENCE"][st.session_state.uid] = now

# cleanup ghosts
DB["PRESENCE"] = {
    u:t for u,t in DB["PRESENCE"].items()
    if now - t < 25
}

active = len(DB["PRESENCE"])

# =====================================================
# AUTO PURGE EXPIRED
# =====================================================
TTL = 120  # secondes

new_flux = []
for m in DB["FLUX"][sid]:
    if now < m["expiry"]:
        new_flux.append(m)

DB["FLUX"][sid] = new_flux

# =====================================================
# HEADER
# =====================================================
c1,c2 = st.columns([3,1])
c1.title("💬 Tunnel sécurisé")
c2.markdown(f"<div class='badge'>🟢 {active}</div>",
            unsafe_allow_html=True)

# =====================================================
# DISPLAY
# =====================================================
for m in reversed(DB["FLUX"][sid]):

    is_me = m["sender"] == st.session_state.uid
    cls = "me" if is_me else "other"

    try:
        raw = ENGINE.decrypt(secret, m["frags"])

        remaining = int(m["expiry"] - time.time())

        st.markdown(f"<div class='msg {cls}'>",
                    unsafe_allow_html=True)

        st.caption("VOUS" if is_me else m["sender"])

        if m["type"] == "text":
            st.write(raw.decode())

        elif "image" in m["type"]:
            st.image(raw)

        elif "video" in m["type"]:
            st.video(raw)

        elif "audio" in m["type"]:
            st.audio(raw)

        st.markdown(
            f"<div class='timer'>⏳ {remaining}s</div>",
            unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    except:
        pass

# =====================================================
# SEND SIGNAL
# =====================================================
st.divider()

mode = st.radio(
    "Signal",
    ["Texte","Média","Vocal"],
    horizontal=True
)

def push_message(data, mtype):

    frags = ENGINE.encrypt(secret, data)

    signature = hashlib.sha256(
        data + secret.encode()
    ).hexdigest()

    if signature in DB["SIGNATURES"]:
        return

    DB["SIGNATURES"].add(signature)

    DB["FLUX"][sid].append({
        "sender": st.session_state.uid,
        "frags": frags,
        "type": mtype,
        "expiry": time.time() + TTL
    })

if mode == "Texte":
    txt = st.text_area("Message")
    if st.button("ENVOYER"):
        if txt:
            push_message(txt.encode(),"text")
            st.rerun()

elif mode == "Média":
    f = st.file_uploader("Upload")
    if f and st.button("DIFFUSER"):
        push_message(f.getvalue(), f.type)
        st.rerun()

elif mode == "Vocal":
    a = st.audio_input("Micro")
    if a and st.button("ENVOYER VOCAL"):
        push_message(a.getvalue(),"audio/wav")
        st.rerun()

# =====================================================
# SMART REFRESH
# =====================================================
time.sleep(3)
st.rerun()
