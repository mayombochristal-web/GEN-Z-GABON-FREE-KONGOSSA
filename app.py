import streamlit as st
from supabase import create_client
import hashlib
from datetime import datetime

st.set_page_config(page_title="Test Auth")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def hash_string(s): return hashlib.sha256(s.encode()).hexdigest()

st.title("Test inscription/connexion")

tab1, tab2 = st.tabs(["Connexion", "Inscription"])

with tab1:
    email = st.text_input("Email")
    pwd = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": pwd})
            st.success("Connecté !")
            st.json(res.user)
        except Exception as e:
            st.error(f"Erreur: {e}")

with tab2:
    new_email = st.text_input("Email")
    new_pwd = st.text_input("Mot de passe", type="password")
    username = st.text_input("Nom d'utilisateur")
    admin_code = st.text_input("Code admin (optionnel)", type="password")
    if st.button("Créer compte"):
        try:
            res = supabase.auth.sign_up({"email": new_email, "password": new_pwd})
            user = res.user
            if user:
                role = "admin" if (hash_string(new_email) == st.secrets["admin"]["email_hash"] and
                                   hash_string(admin_code) == st.secrets["admin"]["password_hash"]) else "user"
                supabase.table("profiles").insert({
                    "id": user.id,
                    "username": username,
                    "bio": "",
                    "location": "",
                    "profile_pic": "",
                    "role": role,
                    "created_at": datetime.now().isoformat()
                }).execute()
                st.success("Compte créé !")
        except Exception as e:
            st.error(f"Erreur: {e}")