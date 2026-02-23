import streamlit as st
from cryptography.fernet import Fernet
import hashlib, time, uuid, base64, json

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="🇬🇦 GEN-Z GABON • FREE_KONGOSSA V17.5",
    page_icon="🌍",
    layout="centered"
)

# =====================================================
# NODE DATABASE
# =====================================================
@st.cache_resource
def NODE():
    return {
        "TUNNELS": {},
        "CHAIN": {},
        "KNOWN_HASHES": set(),
        "NODE_ID": uuid.uuid4().hex[:6]
    }

NODE = NODE()

# =====================================================
# CRYPTO ENGINE
# =====================================================
class HARD:

    @staticmethod
    def tunnel(secret):
        return hashlib.sha256(secret.encode()).hexdigest()[:20]

    @staticmethod
    def key(secret):
        k = hashlib.pbkdf2_hmac(
            "sha256",
            secret.encode(),
            b"GENZ-GABON-HARDENED",
            150000
        )
        return base64.urlsafe_b64encode(k[:32])

    @staticmethod
    def encrypt(secret,data):
        f = Fernet(HARD.key(secret))
        c = f.encrypt(data)
        n=len(c)
        return [c[:n//3],c[n//3:2*n//3],c[2*n//3:]]

    @staticmethod
    def decrypt(secret,frags):
        return Fernet(HARD.key(secret)).decrypt(b"".join(frags))

# =====================================================
# SERIALIZATION SAFE
# =====================================================
def serialize(messages):
    safe=[]
    for m in messages:
        safe.append({
            "u":m["u"],
            "h":m["h"],
            "f":[base64.b64encode(x).decode() for x in m["f"]]
        })
    return safe

def deserialize(messages):
    out=[]
    for m in messages:
        out.append({
            "u":m["u"],
            "h":m["h"],
            "f":[base64.b64decode(x) for x in m["f"]]
        })
    return out

# =====================================================
# SESSION IDENTITY
# =====================================================
if "uid" not in st.session_state:
    nick=st.text_input("Pseudo GEN-Z 🇬🇦")
    if nick:
        st.session_state.uid=f"🇬🇦{nick}@{NODE['NODE_ID']}"
        st.rerun()
    st.stop()

# =====================================================
# TUNNEL ACCESS
# =====================================================
secret=st.text_input("Code Tunnel",type="password")
if not secret:
    st.stop()

sid=HARD.tunnel(secret)

if sid not in NODE["TUNNELS"]:
    NODE["TUNNELS"][sid]=[]
    NODE["CHAIN"][sid]=b"GENESIS"

st.title("🌍 GEN-Z GABON • FREE_KONGOSSA")
st.caption(f"Node {NODE['NODE_ID']}")

# =====================================================
# DISPLAY
# =====================================================
activity=0

for m in reversed(NODE["TUNNELS"][sid]):
    try:
        raw=HARD.decrypt(secret,m["f"])
        st.caption(m["u"])
        st.write(raw.decode())
        activity+=1
    except:
        pass

# =====================================================
# SEND MESSAGE (LEDGER SECURE)
# =====================================================
msg=st.text_area("Message")

if st.button("Envoyer"):
    if msg:

        fr=HARD.encrypt(secret,msg.encode())

        prev=NODE["CHAIN"][sid]
        h=hashlib.sha256(prev+msg.encode()).hexdigest()

        if h not in NODE["KNOWN_HASHES"]:
            NODE["KNOWN_HASHES"].add(h)

            NODE["TUNNELS"][sid].append({
                "u":st.session_state.uid,
                "f":fr,
                "h":h
            })

            NODE["CHAIN"][sid]=bytes.fromhex(h)

        st.rerun()

# =====================================================
# EXPORT / IMPORT (DIFFERENTIAL SYNC)
# =====================================================
st.divider()
st.subheader("🌐 Mesh Sync")

export=json.dumps(serialize(NODE["TUNNELS"][sid]))

st.download_button(
    "⬇️ Export Sync",
    export,
    file_name="free_kongossa_mesh.json"
)

imp=st.file_uploader("Importer Sync")

if imp:
    incoming=deserialize(json.load(imp))

    added=0
    for m in incoming:
        if m["h"] not in NODE["KNOWN_HASHES"]:
            NODE["KNOWN_HASHES"].add(m["h"])
            NODE["TUNNELS"][sid].append(m)
            added+=1

    st.success(f"{added} nouveaux messages synchronisés")
    st.rerun()

# =====================================================
# SMART REFRESH
# =====================================================
delay=2 if activity>5 else 4 if activity>1 else 7
time.sleep(delay)
st.rerun()
