import streamlit as st
from authlib.integrations.requests_client import OAuth2Session


import json
import os

USERS_FILE = "users.json"

# 🔑 Your credentials
CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"

AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USER_INFO = "https://www.googleapis.com/oauth2/v1/userinfo"

REDIRECT_URI = "http://localhost:8501"

def google_login():
    oauth = OAuth2Session(
        CLIENT_ID,
        CLIENT_SECRET,
        scope="openid email profile",
        redirect_uri=REDIRECT_URI
    )

    uri, state = oauth.create_authorization_url(AUTHORIZATION_ENDPOINT)

    st.session_state["oauth_state"] = state

    st.markdown(f"[👉 Click here to Sign in with Google]({uri})")

def handle_callback():
    query_params = st.query_params

    if "code" not in query_params:
        return

    code = query_params.get("code")

    oauth = OAuth2Session(
        CLIENT_ID,
        CLIENT_SECRET,
        scope="openid email profile",
        redirect_uri=REDIRECT_URI
    )

    token = oauth.fetch_token(
        TOKEN_ENDPOINT,
        code=code,
        client_secret=CLIENT_SECRET
    )

    resp = oauth.get(USER_INFO)  # type: ignore
    user_info = resp.json()

    st.session_state["user"] = user_info
    st.session_state["logged_in"] = True

    st.success(f"Welcome {user_info.get('name', '')} 🎉")
    save_session(user_info)

    # ---------- SESSION HELPERS ----------
SESSION_FILE = "session.json"

def save_session(user):
    """No-op: persistence removed to prevent cross-user session leakage."""
    pass

def load_session():
    """No-op: persistence removed to prevent cross-user session leakage."""
    return None

def init_auth():
    """Initialise auth state in memory."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = None


def is_logged_in():
    return st.session_state.get("logged_in", False)


def get_user():
    return st.session_state.get("user", None)


def logout_user():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.current_page = "Login"
    if os.path.exists(SESSION_FILE):
        try:
            os.remove(SESSION_FILE)
        except:
            pass

def navigate_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


# ---------- SIGNUP ----------
def signup_user(name, email, password, organization="", role="", bio=""):
    users = load_users()

    if email in users:
        return False

    users[email] = {
        "name": name,
        "password": password,
        "organization": organization,
        "role": role,
        "bio": bio,
    }

    save_users(users)
    return True


# ---------- UPDATE USER ----------
def update_user(email, user_data):
    """Update an existing user's profile in the DB and session."""
    users = load_users()
    if email in users:
        users[email].update(user_data)
        save_users(users)
        # Sync session
        session_user = {
            "name": users[email].get("name", ""),
            "email": email,
            "organization": users[email].get("organization", ""),
            "role": users[email].get("role", ""),
            "bio": users[email].get("bio", ""),
        }
        st.session_state["user"] = session_user
        save_session(session_user)
        return True
    return False


# ---------- LOGIN ----------
def login_user(email, password):
    users = load_users()

    if email in users and users[email]["password"] == password:
        user_data = {
            "name": users[email]["name"],
            "email": email,
            "organization": users[email].get("organization", ""),
            "role": users[email].get("role", ""),
            "bio": users[email].get("bio", ""),
        }
        st.session_state["user"] = user_data
        st.session_state["logged_in"] = True
        save_session(user_data)
        return True

    return False