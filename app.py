import streamlit as st
from supabase import create_client
import pandas as pd
import time
from datetime import datetime
import uuid
import re
import unicodedata
from PIL import Image
import io

# =====================================================
# CONFIGURATION
# =====================================================
st.set_page_config(
    page_title="GEN-Z GABON • SOCIAL NETWORK",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# INITIALISATION SUPABASE
# =====================================================
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# =====================================================
# FONCTIONS D'UPLOAD AMÉLIORÉES
# =====================================================
def clean_filename(filename):
    """Supprime accents, remplace espaces, enlève caractères spéciaux"""
    filename = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode("ascii")
    filename = filename.replace(" ", "_")
    filename = re.sub(r"[^a-zA-Z0-9_.-]", "", filename)
    return filename

def compress_image(uploaded_file, max_size=1024):
    """Redimensionne et compresse une image pour optimiser le stockage"""
    image = Image.open(uploaded_file)
    # Redimensionner si trop grande
    image.thumbnail((max_size, max_size))
    buffer = io.BytesIO()
    # Sauvegarder en JPEG avec qualité 85
    image.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)
    return buffer

def upload_to_supabase(bucket, file, user_id, allowed_types=None, max_size_mb=5):
    """
    Upload sécurisé d'un fichier vers Supabase Storage.
    - bucket : nom du bucket ('media' ou 'marketplace')
    - file : fichier uploadé via st.file_uploader
    - user_id : id de l'utilisateur
    - allowed_types : liste des types MIME autorisés (ex: ['image/png','image/jpeg'])
    - max_size_mb : taille max en Mo
    Retourne l'URL publique ou None en cas d'erreur.
    """
    try:
        # Vérification taille
        if file.size > max_size_mb * 1024 * 1024:
            st.error(f"Fichier trop volumineux (max {max_size_mb} Mo)")
            return None

        # Vérification type MIME
        if allowed_types and file.type not in allowed_types:
            st.error(f"Type de fichier non autorisé. Types acceptés : {', '.join(allowed_types)}")
            return None

        # Nettoyer le nom et extraire extension
        safe_name = clean_filename(file.name)
        ext = safe_name.split(".")[-1].lower()
        # Générer un nom unique
        unique_name = f"{user_id}/{uuid.uuid4()}.{ext}"

        # Compression si c'est une image
        if file.type and file.type.startswith("image/"):
            file_data = compress_image(file)
            content_type = "image/jpeg"
        else:
            file_data = file.getvalue()
            content_type = file.type

        # Upload vers Supabase
        supabase.storage.from_(bucket).upload(
            unique_name,
            file_data,
            {"content-type": content_type}
        )

        # Récupérer l'URL publique
        public_url = supabase.storage.from_(bucket).get_public_url(unique_name)
        return public_url

    except Exception as e:
        st.error(f"Erreur lors de l'upload : {e}")
        return None

# =====================================================
# GESTION DE L'AUTHENTIFICATION (SUPABASE AUTH)
# =====================================================
def login_signup():
    """Gère l'écran de connexion / inscription"""
    st.title("🌍 Bienvenue sur le réseau social GEN-Z")

    tab1, tab2 = st.tabs(["Se connecter", "Créer un compte"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Connexion")
            if submitted:
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state["user"] = res.user
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input("Email")
            new_password = st.text_input("Mot de passe", type="password")
            username = st.text_input("Nom d'utilisateur (unique)")
            submitted = st.form_submit_button("Créer mon compte")
            if submitted:
                try:
                    # Création de l'utilisateur dans Supabase Auth
                    res = supabase.auth.sign_up({"email": new_email, "password": new_password})
                    user = res.user
                    if user:
                        # Ajout du profil dans la table profiles
                        profile_data = {
                            "id": user.id,
                            "username": username,
                            "bio": "",
                            "location": "",
                            "profile_pic": "",
                            "created_at": datetime.now().isoformat()
                        }
                        supabase.table("profiles").insert(profile_data).execute()
                        st.success("Compte créé ! Connecte-toi.")
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

def logout():
    supabase.auth.sign_out()
    st.session_state.clear()
    st.rerun()

# Vérifier si l'utilisateur est connecté
if "user" not in st.session_state:
    login_signup()
    st.stop()

# Récupérer l'utilisateur courant
user = st.session_state["user"]

# Charger le profil depuis la table profiles
@st.cache_data(ttl=60)
def get_profile(user_id):
    res = supabase.table("profiles").select("*").eq("id", user_id).execute()
    if res.data:
        return res.data[0]
    return None

profile = get_profile(user.id)

# =====================================================
# NAVIGATION (SIDEBAR)
# =====================================================
st.sidebar.image("https://via.placeholder.com/150x50?text=GEN-Z", use_column_width=True)
st.sidebar.write(f"Connecté en tant que : **{profile['username']}**")
st.sidebar.write(f"ID : {user.id[:8]}...")

menu = st.sidebar.radio(
    "Navigation",
    ["🌐 Feed", "👤 Mon Profil", "✉️ Messages", "🏪 Marketplace", "💰 Wallet", "⚙️ Paramètres"]
)

if st.sidebar.button("🚪 Déconnexion"):
    logout()

# =====================================================
# FONCTIONS UTILES
# =====================================================
def like_post(post_id):
    """Ajoute un like (trigger update like_count)"""
    try:
        supabase.table("likes").insert({
            "post_id": post_id,
            "user_id": user.id
        }).execute()
        st.success("👍 Like ajouté !")
        time.sleep(0.5)
        st.rerun()
    except Exception as e:
        st.error("Vous avez déjà liké ce post.")

def add_comment(post_id, text):
    """Ajoute un commentaire (trigger update comment_count)"""
    supabase.table("comments").insert({
        "post_id": post_id,
        "user_id": user.id,
        "text": text
    }).execute()
    st.success("💬 Commentaire ajouté")
    time.sleep(0.5)
    st.rerun()

# =====================================================
# PAGE FEED
# =====================================================
def feed_page():
    st.header("🌐 Fil d'actualité")

    # Formulaire de création de post
    with st.expander("✍️ Créer un post", expanded=False):
        with st.form("new_post"):
            post_text = st.text_area("Quoi de neuf ?")
            media_file = st.file_uploader(
                "Ajouter une image/vidéo (optionnel)",
                type=["png", "jpg", "jpeg", "mp4", "mov", "avi"]
            )
            submitted = st.form_submit_button("Publier")
            if submitted and post_text:
                media_path = None
                media_type = None
                if media_file:
                    # Types autorisés pour les médias
                    allowed_image = ["image/png", "image/jpeg", "image/jpg"]
                    allowed_video = ["video/mp4", "video/quicktime", "video/x-msvideo"]
                    allowed_all = allowed_image + allowed_video
                    media_url = upload_to_supabase(
                        "media",
                        media_file,
                        user.id,
                        allowed_types=allowed_all,
                        max_size_mb=10  # 10 Mo max pour les vidéos
                    )
                    if media_url:
                        media_path = media_url
                        media_type = media_file.type

                post_data = {
                    "user_id": user.id,
                    "text": post_text,
                    "media_path": media_path,
                    "media_type": media_type,
                    "created_at": datetime.now().isoformat()
                }
                supabase.table("posts").insert(post_data).execute()
                st.success("Post publié !")
                st.rerun()

    # Récupération des posts (feed global, trié par date)
    posts = supabase.table("posts").select(
        "*, profiles!inner(username, profile_pic), likes(count), comments(count)"
    ).order("created_at", desc=True).limit(50).execute()

    if not posts.data:
        st.info("Aucun post pour le moment. Sois le premier à poster !")
        return

    for post in posts.data:
        with st.container():
            col1, col2 = st.columns([1, 20])
            with col1:
                # Avatar
                if post["profiles"]["profile_pic"]:
                    st.image(post["profiles"]["profile_pic"], width=40)
                else:
                    st.image("https://via.placeholder.com/40", width=40)
            with col2:
                st.markdown(f"**{post['profiles']['username']}**  · {post['created_at'][:10]}")
                st.write(post["text"])

                # Affichage média
                if post.get("media_path"):
                    if post["media_type"] and "image" in post["media_type"]:
                        st.image(post["media_path"])
                    elif post["media_type"] and "video" in post["media_type"]:
                        st.video(post["media_path"])

                # Statistiques
                like_count = len(post.get("likes", []))
                comment_count = len(post.get("comments", []))

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button(f"❤️ {like_count}", key=f"like_{post['id']}"):
                        like_post(post["id"])
                with col_b:
                    with st.popover(f"💬 {comment_count} commentaires"):
                        # Afficher les commentaires existants
                        comments = supabase.table("comments").select(
                            "*, profiles(username)"
                        ).eq("post_id", post["id"]).order("created_at").execute()
                        for c in comments.data:
                            st.markdown(f"**{c['profiles']['username']}** : {c['text']}")
                        # Ajouter un commentaire
                        new_comment = st.text_input("Votre commentaire", key=f"input_{post['id']}")
                        if st.button("Envoyer", key=f"send_{post['id']}"):
                            add_comment(post["id"], new_comment)
                with col_c:
                    st.button("🔗 Partager", key=f"share_{post['id']}")

            st.divider()

# =====================================================
# PAGE PROFIL
# =====================================================
def profile_page():
    st.header("👤 Mon Profil")

    # Affichage et édition du profil
    with st.form("edit_profile"):
        username = st.text_input("Nom d'utilisateur", value=profile["username"])
        bio = st.text_area("Bio", value=profile.get("bio", ""))
        location = st.text_input("Localisation", value=profile.get("location", ""))
        # Upload de photo de profil
        profile_image = st.file_uploader(
            "Photo de profil",
            type=["png", "jpg", "jpeg"]
        )
        submitted = st.form_submit_button("Mettre à jour")

    # Traitement en dehors du formulaire pour éviter de re-soumettre l'upload à chaque rerun
    if submitted:
        update_data = {
            "username": username,
            "bio": bio,
            "location": location
        }
        # Si une nouvelle image a été uploadée
        if profile_image:
            image_url = upload_to_supabase(
                "media",
                profile_image,
                user.id,
                allowed_types=["image/png", "image/jpeg", "image/jpg"],
                max_size_mb=2
            )
            if image_url:
                update_data["profile_pic"] = image_url
        supabase.table("profiles").update(update_data).eq("id", user.id).execute()
        st.success("Profil mis à jour")
        st.cache_data.clear()
        st.rerun()

    st.subheader("Mes statistiques")
    # Nombre de posts
    post_count = supabase.table("posts").select("*", count="exact").eq("user_id", user.id).execute()
    st.metric("Posts publiés", post_count.count)

    # Abonnés / abonnements
    followers = supabase.table("follows").select("*", count="exact").eq("followed", user.id).execute()
    following = supabase.table("follows").select("*", count="exact").eq("follower", user.id).execute()
    col1, col2 = st.columns(2)
    col1.metric("Abonnés", followers.count)
    col2.metric("Abonnements", following.count)

# =====================================================
# PAGE MESSAGES
# =====================================================
def messages_page():
    st.header("✉️ Messagerie privée")

    # Liste des conversations (utilisateurs avec qui on a échangé)
    sent = supabase.table("messages").select("recipient").eq("sender", user.id).execute()
    received = supabase.table("messages").select("sender").eq("recipient", user.id).execute()

    contact_ids = set()
    for msg in sent.data:
        contact_ids.add(msg["recipient"])
    for msg in received.data:
        contact_ids.add(msg["sender"])

    if not contact_ids:
        st.info("Aucune conversation pour l'instant.")
        return

    # Charger les profils des contacts
    contacts = supabase.table("profiles").select("id, username").in_("id", list(contact_ids)).execute()
    contact_dict = {c["id"]: c["username"] for c in contacts.data}

    selected_contact = st.selectbox("Choisir un contact", options=list(contact_dict.keys()), format_func=lambda x: contact_dict[x])

    if selected_contact:
        st.subheader(f"Discussion avec {contact_dict[selected_contact]}")

        # Afficher les messages
        messages = supabase.table("messages").select("*").or_(
            f"and(sender.eq.{user.id},recipient.eq.{selected_contact}),and(sender.eq.{selected_contact},recipient.eq.{user.id})"
        ).order("created_at").execute()

        for msg in messages.data:
            if msg["sender"] == user.id:
                st.markdown(f"<div style='text-align: right; background-color: #dcf8c6; padding: 8px; border-radius: 10px; margin:5px;'>Vous : {msg.get('text', '')}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align: left; background-color: #f1f0f0; padding: 8px; border-radius: 10px; margin:5px;'>{contact_dict[selected_contact]} : {msg.get('text', '')}</div>", unsafe_allow_html=True)

        # Envoyer un message
        with st.form("new_message"):
            msg_text = st.text_area("Votre message")
            if st.form_submit_button("Envoyer"):
                supabase.table("messages").insert({
                    "sender": user.id,
                    "recipient": selected_contact,
                    "text": msg_text,
                    "created_at": datetime.now().isoformat()
                }).execute()
                st.success("Message envoyé")
                st.rerun()

# =====================================================
# PAGE MARKETPLACE
# =====================================================
def marketplace_page():
    st.header("🏪 Marketplace")

    # Formulaire pour ajouter une annonce
    with st.expander("➕ Ajouter une annonce"):
        with st.form("new_listing"):
            title = st.text_input("Titre")
            description = st.text_area("Description")
            price = st.number_input("Prix (KC)", min_value=0.0, step=0.1)
            media_file = st.file_uploader(
                "Image du produit",
                type=["png", "jpg", "jpeg"]
            )
            submitted = st.form_submit_button("Publier l'annonce")
            if submitted and title:
                media_url = None
                if media_file:
                    media_url = upload_to_supabase(
                        "marketplace",
                        media_file,
                        user.id,
                        allowed_types=["image/png", "image/jpeg", "image/jpg"],
                        max_size_mb=2
                    )
                supabase.table("marketplace_listings").insert({
                    "user_id": user.id,
                    "title": title,
                    "description": description,
                    "price_kc": price,
                    "media_url": media_url,
                    "media_type": "image" if media_url else None,
                    "created_at": datetime.now().isoformat(),
                    "is_active": True
                }).execute()
                st.success("Annonce ajoutée !")
                st.rerun()

    # Afficher les annonces actives
    st.subheader("Annonces récentes")
    listings = supabase.table("marketplace_listings").select(
        "*, profiles!inner(username)"
    ).eq("is_active", True).order("created_at", desc=True).execute()

    if not listings.data:
        st.info("Aucune annonce pour le moment.")
        return

    cols = st.columns(3)
    for i, listing in enumerate(listings.data):
        with cols[i % 3]:
            st.markdown(f"**{listing['title']}**")
            if listing.get("media_url"):
                st.image(listing["media_url"], use_column_width=True)
            st.write(listing["description"][:100] + "...")
            st.write(f"💰 {listing['price_kc']} KC")
            st.caption(f"Par {listing['profiles']['username']}")

# =====================================================
# PAGE WALLET
# =====================================================
def wallet_page():
    st.header("💰 Mon Wallet")

    # Récupérer ou créer le wallet
    wallet = supabase.table("wallets").select("*").eq("user_id", user.id).execute()
    if not wallet.data:
        # Créer un wallet par défaut
        supabase.table("wallets").insert({
            "user_id": user.id,
            "kongo_balance": 0.0,
            "total_mined": 0.0,
            "last_reward_at": datetime.now().isoformat()
        }).execute()
        wallet = supabase.table("wallets").select("*").eq("user_id", user.id).execute()

    wallet_data = wallet.data[0]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Solde KC", f"{wallet_data['kongo_balance']} KC")
    with col2:
        st.metric("Total miné", f"{wallet_data['total_mined']} KC")

    if st.button("⛏️ Miner (récompense quotidienne)"):
        # Vérifier délai (24h)
        last = datetime.fromisoformat(wallet_data["last_reward_at"].replace("Z", "+00:00"))
        now = datetime.now()
        delta = now - last
        if delta.total_seconds() > 86400:
            # Ajouter 10 KC
            new_balance = wallet_data["kongo_balance"] + 10
            new_mined = wallet_data["total_mined"] + 10
            supabase.table("wallets").update({
                "kongo_balance": new_balance,
                "total_mined": new_mined,
                "last_reward_at": now.isoformat()
            }).eq("user_id", user.id).execute()
            st.success("+10 KC minés !")
            st.rerun()
        else:
            reste = 86400 - delta.total_seconds()
            st.warning(f"Tu pourras re-miner dans {int(reste//3600)}h{int((reste%3600)//60)}m.")

    st.subheader("Historique des transactions (à venir)")

# =====================================================
# PAGE PARAMÈTRES
# =====================================================
def settings_page():
    st.header("⚙️ Paramètres")

    # Gestion de l'abonnement
    sub = supabase.table("subscriptions").select("*").eq("user_id", user.id).execute()
    if sub.data:
        plan = sub.data[0]["plan_type"]
        expires = sub.data[0].get("expires_at")
        st.info(f"Plan actuel : **{plan}**" + (f" (expire le {expires[:10]})" if expires else ""))
    else:
        st.info("Plan actuel : **Gratuit**")
        if st.button("Passer à Premium"):
            # Ici tu pourrais intégrer un paiement
            supabase.table("subscriptions").insert({
                "user_id": user.id,
                "plan_type": "Premium",
                "activated_at": datetime.now().isoformat(),
                "expires_at": (datetime.now().replace(year=datetime.now().year+1)).isoformat(),
                "is_active": True
            }).execute()
            st.success("Compte Premium activé !")
            st.rerun()

    st.divider()
    st.subheader("Zone dangereuse")
    if st.button("Supprimer mon compte", type="primary"):
        # Supprimer l'utilisateur (nécessite admin)
        st.warning("Fonction désactivée pour le moment.")

# =====================================================
# ROUTEUR PRINCIPAL
# =====================================================
if menu == "🌐 Feed":
    feed_page()
elif menu == "👤 Mon Profil":
    profile_page()
elif menu == "✉️ Messages":
    messages_page()
elif menu == "🏪 Marketplace":
    marketplace_page()
elif menu == "💰 Wallet":
    wallet_page()
elif menu == "⚙️ Paramètres":
    settings_page()