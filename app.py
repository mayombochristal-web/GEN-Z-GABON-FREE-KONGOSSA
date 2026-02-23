import streamlit as st

from identity import load_identity, sign
from mesh import append_event, rebuild_state, merge

# ---------- INIT ----------

st.set_page_config(page_title="GEN-Z GABON FREE-KONGOSSA")

IDENTITY = load_identity()
STATE = rebuild_state()

st.title("🌍 GEN-Z GABON FREE-KONGOSSA — V20")

st.caption(f"Node ID: {IDENTITY['public_key'][:16]}")

# ---------- SEND MESSAGE ----------

msg = st.text_input("Message kongossa")

if st.button("Envoyer") and msg:

    payload = {
        "type": "message",
        "author": IDENTITY["public_key"],
        "data": {"text": msg}
    }

    payload["signature"] = sign(
        payload,
        IDENTITY["private_key"]
    )

    append_event(payload)

    st.success("Message envoyé ✅")
    st.rerun()


# ---------- DISPLAY ----------

st.subheader("📡 Messages réseau")

for m in reversed(STATE["messages"]):
    st.write(
        f"**{m['author'][:10]}** : {m['data']['text']}"
    )


# ---------- IMPORT REMOTE STATE ----------

st.divider()
st.subheader("🔄 Sync Peer")

remote_json = st.text_area("Coller état distant (JSON)")

if st.button("Fusionner") and remote_json:

    import json

    try:
        remote = json.loads(remote_json)
        STATE = merge(STATE, remote)

        st.success("Synchronisation réussie ✅")

    except Exception as e:
        st.error("JSON invalide")
