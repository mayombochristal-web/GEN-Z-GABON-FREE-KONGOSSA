import streamlit as st
import json
import hashlib
import secrets
import time
from pathlib import Path

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="GEN-Z GABON FREE-KONGOSSA",
    page_icon="🌍",
    layout="centered"
)

DATA = Path("mesh_data")
DATA.mkdir(exist_ok=True)

IDENTITY_FILE = DATA / "identity.json"
LOG_FILE = DATA / "events.json"

# =====================================================
# SAFE JSON (ANTI CRASH V17/V18)
# =====================================================

def safe_load(path):

    if not path.exists():
        return []

    raw = path.read_bytes()

    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return json.loads(raw.decode(enc))
        except:
            pass

    return []


def safe_save(data, path):
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

# =====================================================
# IDENTITY (V16 STABLE STYLE)
# =====================================================

def load_identity():

    if not IDENTITY_FILE.exists():

        private_key = secrets.token_hex(32)
        public_key = hashlib.sha256(
            private_key.encode()
        ).hexdigest()

        identity = {
            "public_key": public_key,
            "private_key": private_key
        }

        safe_save(identity, IDENTITY_FILE)
        return identity

    return json.loads(
        IDENTITY_FILE.read_text(encoding="utf-8")
    )


IDENTITY = load_identity()

# =====================================================
# SIGNATURE
# =====================================================

def sign(payload):

    raw = json.dumps(payload, sort_keys=True)

    return hashlib.sha256(
        (raw + IDENTITY["private_key"]).encode()
    ).hexdigest()

# =====================================================
# EVENT LOG (AFRICAN MESH SIMPLE)
# =====================================================

def append_event(event):

    log = safe_load(LOG_FILE)

    event["timestamp"] = time.time()

    event["id"] = hashlib.sha256(
        json.dumps(event, sort_keys=True).encode()
    ).hexdigest()

    log.append(event)

    safe_save(log, LOG_FILE)


def rebuild_state():

    log = safe_load(LOG_FILE)

    state = {"messages": []}

    for e in log:
        if e.get("type") == "message":
            state["messages"].append(e)

    return state

# =====================================================
# MERGE PEER STATE
# =====================================================

def merge(local, remote):

    seen = set()
    merged = []

    for m in local["messages"] + remote.get("messages", []):
        if m["id"] not in seen:
            merged.append(m)
            seen.add(m["id"])

    return {"messages": merged}

# =====================================================
# UI
# =====================================================

STATE = rebuild_state()

st.title("🌍 GEN-Z GABON FREE-KONGOSSA V20")
st.caption(f"Node ID : {IDENTITY['public_key'][:16]}")

# =====================================================
# SEND MESSAGE
# =====================================================

msg = st.text_input("💬 Ton kongossa")

if st.button("Envoyer") and msg:

    payload = {
        "type": "message",
        "author": IDENTITY["public_key"],
        "data": {"text": msg}
    }

    payload["signature"] = sign(payload)

    append_event(payload)

    st.success("Signal diffusé 📡")
    st.rerun()

# =====================================================
# DISPLAY
# =====================================================

st.subheader("📡 Flux Mesh")

if not STATE["messages"]:
    st.info("Tunnel silencieux...")

for m in reversed(STATE["messages"]):

    st.markdown(
        f"""
        **{m['author'][:10]}**
        > {m['data']['text']}
        """
    )

# =====================================================
# SYNC PEER (MANUEL MAIS STABLE)
# =====================================================

st.divider()
st.subheader("🔄 Synchronisation Peer")

remote_json = st.text_area("Coller état distant JSON")

if st.button("Fusionner") and remote_json:

    try:
        remote = json.loads(remote_json)
        STATE = merge(STATE, remote)

        st.success("Fusion réussie ✅")

    except:
        st.error("JSON invalide")

# =====================================================
# EXPORT STATE
# =====================================================

if st.button("Exporter mon état réseau"):

    st.download_button(
        "Télécharger",
        json.dumps(STATE, indent=2, ensure_ascii=False),
        "mesh_state.json",
        "application/json"
    )
