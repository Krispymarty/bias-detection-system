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

    # ---------- SESSION HELPERS ----------

def init_auth():
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
        json.dump(users, f)


# ---------- SIGNUP ----------
def signup_user(name, email, password):
    users = load_users()

    if email in users:
        return False

    users[email] = {
        "name": name,
        "password": password
    }

    save_users(users)
    return True


# ---------- LOGIN ----------
def login_user(email, password):
    users = load_users()

    if email in users and users[email]["password"] == password:
        st.session_state["user"] = {
            "name": users[email]["name"],
            "email": email
        }
        st.session_state["logged_in"] = True
        return True

    return False