import streamlit as st
from cryptography.fernet import Fernet
import hashlib, time, uuid, base64, json

# =====================================================
# CONFIG GEN-Z GABON
# =====================================================
st.set_page_config(
    page_title="GEN-Z GABON • FREE-KONGOSSA V16",
    page_icon="🇬🇦",
    layout="centered"
)

# =====================================================
# NODE DATABASE (SOVEREIGN NODE)
# =====================================================
@st.cache_resource
def NODE():
    return {
        "TUNNELS": {},
        "CHAIN": {},
        "PRESENCE": {},
        "PUBLIC": []
    }

NODE = NODE()

# =====================================================
# SOVEREIGN ENGINE
# =====================================================
class SOVEREIGN:

    @staticmethod
    def tunnel(secret):
        return hashlib.sha256(secret.encode()).hexdigest()[:20]

    @staticmethod
    def key(secret):
        k=hashlib.pbkdf2_hmac(
            "sha256",
            secret.encode(),
            b"GABON-SOVEREIGN",
            150000
        )
        return base64.urlsafe_b64encode(k[:32])

    @staticmethod
    def encrypt(secret,data):
        f=Fernet(SOVEREIGN.key(secret))
        c=f.encrypt(data)
        n=len(c)
        return [c[:n//3],c[n//3:2*n//3],c[2*n//3:]]

    @staticmethod
    def decrypt(secret,frags):
        f=Fernet(SOVEREIGN.key(secret))
        return f.decrypt(b"".join(frags))

# =====================================================
# SESSION GEN-Z
# =====================================================
if "uid" not in st.session_state:
    nick=st.text_input("Pseudo GEN-Z 🇬🇦")
    if nick:
        st.session_state.uid=f"🇬🇦{nick}#{uuid.uuid4().hex[:3]}"
        st.rerun()
    st.stop()

# =====================================================
# AUTH TUNNEL
# =====================================================
secret=st.text_input("Code Tunnel",type="password")

if not secret:
    st.stop()

sid=SOVEREIGN.tunnel(secret)

if sid not in NODE["TUNNELS"]:
    NODE["TUNNELS"][sid]=[]
    NODE["CHAIN"][sid]=b"GENESIS"

# =====================================================
# PRESENCE
# =====================================================
now=time.time()
NODE["PRESENCE"][st.session_state.uid]=now
NODE["PRESENCE"]={
u:t for u,t in NODE["PRESENCE"].items()
if now-t<30
}

active=len(NODE["PRESENCE"])

st.title("🇬🇦 FREE-KONGOSSA — SOVEREIGN")

st.caption(f"🟢 {active} actifs | Node Local")

# =====================================================
# DISPLAY
# =====================================================
for m in reversed(NODE["TUNNELS"][sid]):
    try:
        raw=SOVEREIGN.decrypt(secret,m["f"])
        st.caption(m["u"])

        if m["t"]=="text":
            st.write(raw.decode())
        elif "image" in m["t"]:
            st.image(raw)
        elif "video" in m["t"]:
            st.video(raw)
        else:
            st.audio(raw)

    except:
        pass

# =====================================================
# SEND
# =====================================================
mode=st.radio("Signal",["Texte","Média","Vocal"],horizontal=True)

def push(data,typ):

    frags=SOVEREIGN.encrypt(secret,data)

    prev=NODE["CHAIN"][sid]
    chain=hashlib.sha256(prev+data).digest()
    NODE["CHAIN"][sid]=chain

    NODE["TUNNELS"][sid].append({
        "u":st.session_state.uid,
        "f":frags,
        "t":typ,
        "ts":time.time()
    })

if mode=="Texte":
    txt=st.text_area("Message")
    if st.button("Envoyer"):
        push(txt.encode(),"text")
        st.rerun()

elif mode=="Média":
    f=st.file_uploader("Upload")
    if f and st.button("Diffuser"):
        push(f.getvalue(),f.type)
        st.rerun()

elif mode=="Vocal":
    a=st.audio_input("Micro")
    if a and st.button("Vocal"):
        push(a.getvalue(),"audio/wav")
        st.rerun()

# =====================================================
# SOVEREIGN SYNC EXPORT
# =====================================================
st.divider()
st.subheader("🌐 Sync Souverain")

export_data=json.dumps(NODE["TUNNELS"][sid])
st.download_button(
    "⬇️ Export Tunnel",
    export_data,
    file_name="kongossa_sync.json"
)

imp=st.file_uploader("Importer Sync")

if imp:
    incoming=json.load(imp)
    NODE["TUNNELS"][sid].extend(incoming)
    st.success("Fusion Node OK")
    st.rerun()

# =====================================================
# REFRESH ADAPTATIF
# =====================================================
time.sleep(4)
st.rerun()
