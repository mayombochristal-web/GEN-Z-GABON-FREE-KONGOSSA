import streamlit as st
from cryptography.fernet import Fernet
import hashlib, time, uuid, base64, os

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="FREE-KONGOSSA V15 GODMODE",
    page_icon="🛰️",
    layout="centered"
)

# =====================================================
# SHARED MEMORY
# =====================================================
@st.cache_resource
def DB():
    return {
        "FLUX": {},
        "PRESENCE": {},
        "CHAIN": {},
        "SIGN": set()
    }

DB = DB()

# =====================================================
# GODMODE ENGINE
# =====================================================
class GOD:

    @staticmethod
    def tunnel(secret):
        return hashlib.sha256(secret.encode()).hexdigest()[:18]

    # ---- initial key ----
    @staticmethod
    def seed(secret):
        k = hashlib.pbkdf2_hmac(
            "sha256",
            secret.encode(),
            b"GODMODE",
            120000
        )
        return k

    # ---- evolving key ----
    @staticmethod
    def evolve(key, payload):
        return hashlib.sha256(key + payload).digest()

    @staticmethod
    def fernet_key(key):
        return base64.urlsafe_b64encode(key[:32])

    # ---- encrypt ----
    @staticmethod
    def encrypt(key, data):

        f = Fernet(GOD.fernet_key(key))
        box = f.encrypt(data)

        n=len(box)
        return [
            box[:n//3],
            box[n//3:2*n//3],
            box[2*n//3:]
        ]

    @staticmethod
    def decrypt(key, frags):
        f = Fernet(GOD.fernet_key(key))
        return f.decrypt(b"".join(frags))

# =====================================================
# SESSION
# =====================================================
if "uid" not in st.session_state:
    st.session_state.uid=f"Z-{uuid.uuid4().hex[:4]}"

if "auth" not in st.session_state:
    st.session_state.auth=False

# =====================================================
# AUTH
# =====================================================
if not st.session_state.auth:

    st.title("🛰️ FREE-KONGOSSA GODMODE")

    s=st.text_input("Code Tunnel",type="password")
    ghost=st.checkbox("👁️ Mode Fantôme")

    if st.button("ENTRER"):
        if s:
            st.session_state.secret=s
            st.session_state.sid=GOD.tunnel(s)
            st.session_state.key=GOD.seed(s)
            st.session_state.ghost=ghost
            st.session_state.auth=True
            st.rerun()

    st.stop()

sid=st.session_state.sid
secret=st.session_state.secret

if sid not in DB["FLUX"]:
    DB["FLUX"][sid]=[]
    DB["CHAIN"][sid]=b"GENESIS"

# =====================================================
# PRESENCE
# =====================================================
now=time.time()

if not st.session_state.ghost:
    DB["PRESENCE"][st.session_state.uid]=now

DB["PRESENCE"]={
u:t for u,t in DB["PRESENCE"].items()
if now-t<30
}

active=len(DB["PRESENCE"])

# =====================================================
# AUTO CLEAN TTL
# =====================================================
TTL=180

DB["FLUX"][sid]=[
m for m in DB["FLUX"][sid]
if now<m["exp"]
]

# =====================================================
# HEADER
# =====================================================
c1,c2=st.columns([3,1])
c1.title("💬 GODMODE TUNNEL")
c2.metric("ACTIFS",active)

# =====================================================
# DISPLAY
# =====================================================
activity=0

for m in reversed(DB["FLUX"][sid]):

    try:
        raw=GOD.decrypt(m["key"],m["frags"])
        activity+=1

        st.markdown("----")
        st.caption("VOUS" if m["sender"]==st.session_state.uid else m["sender"])

        if m["type"]=="text":
            st.write(raw.decode())
        elif "image" in m["type"]:
            st.image(raw)
        elif "video" in m["type"]:
            st.video(raw)
        else:
            st.audio(raw)

        remain=int(m["exp"]-time.time())
        st.caption(f"⏳ {remain}s")

    except:
        pass

# =====================================================
# SEND
# =====================================================
mode=st.radio("Signal",["Texte","Média","Vocal"],horizontal=True)

def send(data,typ):

    key=st.session_state.key

    # evolve key
    new_key=GOD.evolve(key,data)
    st.session_state.key=new_key

    frags=GOD.encrypt(new_key,data)

    # chain integrity
    prev=DB["CHAIN"][sid]
    chain=hashlib.sha256(prev+data).digest()
    DB["CHAIN"][sid]=chain

    sig=hashlib.sha256(chain).hexdigest()
    if sig in DB["SIGN"]:
        return

    DB["SIGN"].add(sig)

    DB["FLUX"][sid].append({
        "sender":st.session_state.uid,
        "frags":frags,
        "type":typ,
        "key":new_key,
        "exp":time.time()+TTL
    })

if mode=="Texte":
    t=st.text_area("Message")
    if st.button("ENVOYER"):
        if t:
            send(t.encode(),"text")
            st.rerun()

elif mode=="Média":
    f=st.file_uploader("Upload")
    if f and st.button("DIFFUSER"):
        send(f.getvalue(),f.type)
        st.rerun()

elif mode=="Vocal":
    a=st.audio_input("Micro")
    if a and st.button("ENVOYER VOCAL"):
        send(a.getvalue(),"audio/wav")
        st.rerun()

# =====================================================
# SMART REFRESH
# =====================================================
delay=2 if activity>5 else 5
time.sleep(delay)
st.rerun()
