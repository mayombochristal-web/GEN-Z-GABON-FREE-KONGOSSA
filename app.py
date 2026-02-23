import streamlit as st
import hashlib
import secrets
import time
import json
import uuid

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="GEN-Z GABON FREE-KONGOSSA",
    page_icon="🌍",
    layout="centered"
)

# =====================================================
# SHARED GLOBAL DB (V16 CORE — DISTANCE OK)
# =====================================================

@st.cache_resource
def get_db():
    return {
        "MESSAGES": [],
        "PRESENCE": {},
        "SEEN": set()
    }

DB = get_db()

# =====================================================
# IDENTITY (V20 IMPROVED)
# =====================================================

if "identity" not in st.session_state:
    private = secrets.token_hex(32)
    public = hashlib.sha256(private.encode()).hexdigest()

    st.session_state.identity = {
        "private": private,
        "public": public
    }

UID = st.session_state.identity["public"][:10]

# =====================================================
# SIGNATURE
# =====================================================

def sign(payload):
    raw = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(
        (raw + st.session_state.identity["private"]).encode()
    ).hexdigest()

# =====================================================
# PRESENCE SYSTEM
# =====================================================

DB["PRESENCE"][UID] = time.time()

active = len([
    u for u, t in DB["PRESENCE"].items()
    if time.time() - t < 20
])

# =====================================================
# UI HEADER
# =====================================================

c1, c2 = st.columns([3,1])

c1.title("🌍 GEN-Z GABON FREE-KONGOSSA")
c2.metric("🟢 ACTIFS", active)

st.caption(f"Node : {UID}")

st.divider()

# =====================================================
# DISPLAY MESSAGES
# =====================================================

if not DB["MESSAGES"]:
    st.info("Tunnel silencieux...")

for msg in reversed(DB["MESSAGES"]):

    mine = msg["author"] == UID
    color = "#00ffaa" if mine else "#444"

    st.markdown(
        f"""
        <div style="
        background:#111;
        padding:12px;
        border-radius:12px;
        margin-bottom:10px;
        border-left:5px solid {color};
        ">
        <b>{"VOUS" if mine else msg["author"]}</b><br>
        {msg["text"]}
        <br><small>{msg["time"]}</small>
        </div>
        """,
        unsafe_allow_html=True
    )

# =====================================================
# SEND MESSAGE
# =====================================================

st.divider()

msg = st.text_input("💬 Ton kongossa")

if st.button("Envoyer") and msg:

    payload = {
        "author": UID,
        "text": msg,
        "time": time.strftime("%H:%M")
    }

    payload["signature"] = sign(payload)

    mid = hashlib.sha256(
        json.dumps(payload).encode()
    ).hexdigest()

    if mid not in DB["SEEN"]:
        DB["SEEN"].add(mid)
        DB["MESSAGES"].append(payload)

    st.rerun()

# =====================================================
# AUTO REFRESH (GLOBAL REALTIME)
# =====================================================

time.sleep(3)
st.rerun()
