"""
FairSight AI — Main Application Entry Point
Handles page configuration, CSS loading, sidebar navigation, and page routing.
"""
import streamlit as st

# ✅ INITIALIZE SESSION STATE
if "current_page" not in st.session_state:
    st.session_state.current_page = "Login"   # or "Home" if you want
import streamlit as st
from streamlit_option_menu import option_menu
from utils.auth import init_auth, is_logged_in, get_user, logout_user
from pages_app import (
    home,
    signup,
    login,
    dashboard,
    about,
    tutorial,
    ai_agent,
    whatif_simulator,
    settings_page,
    help_support,
)

# ──────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="FairSight AI — AI Fairness Platform",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed",
)
from utils.auth import init_auth

init_auth()

if "current_page" not in st.session_state:
    st.session_state.current_page = "Login"

# ──────────────────────────────────────────────
# CSS / Font Loading
# ──────────────────────────────────────────────
@st.cache_resource
def load_css():
    """Load custom CSS and external resources once."""
    with open("assets/style.css") as f:
        return f.read()


# Google Fonts
st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" '
    'rel="stylesheet">',
    unsafe_allow_html=True,
)

# Tailwind CSS (v2 CDN — utility classes for custom HTML blocks)
st.markdown(
    '<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">',
    unsafe_allow_html=True,
)

# Custom theme CSS (loaded after Tailwind so it takes precedence)
st.markdown(f"<style>{load_css()}</style>", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Initialise Authentication State
# ──────────────────────────────────────────────
init_auth()

if st.session_state.get("show_welcome_animation"):
    st.balloons()
    st.toast("Welcome to FairSight AI!", icon="🚀")
    st.session_state.show_welcome_animation = False

# ──────────────────────────────────────────────
# Auth pages get full-screen layout (no sidebar)
# ──────────────────────────────────────────────
AUTH_PAGES = {"Sign Up", "Login"}
current_page = st.session_state.get("current_page", "Sign Up")

if current_page not in AUTH_PAGES:
    # ──────────────────────────────────────────
    # Sidebar Navigation (only for app pages)
    # ──────────────────────────────────────────
    menu_options = [
        "Home",
        "About",
        "Tutorial",
        "Dashboard",
        "AI Agent",
        "What-If Simulator",
        "Settings",
        "Help & Support",
    ]
    menu_icons = [
        "house",
        "info-circle",
        "book",
        "speedometer2",
        "robot",
        "sliders",
        "gear",
        "question-circle",
    ]

    default_idx = menu_options.index(current_page) if current_page in menu_options else 0

    with st.sidebar:
        # Logo
        st.markdown(
            """
            <div style="text-align:center;padding:1.2rem 0 0.8rem;
                        border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:0.8rem;">
                <div style="font-size:2.2rem;margin-bottom:0.2rem;">🔮</div>
                <h1 style="font-size:1.25rem;font-weight:700;color:white;margin:0;">FairSight AI</h1>
                <p style="font-size:0.7rem;color:rgba(255,255,255,0.35);margin:0;letter-spacing:0.06em;">
                    AI FAIRNESS PLATFORM
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        selected = option_menu(
            menu_title=None,
            options=menu_options,
            icons=menu_icons,
            default_index=default_idx,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#00FFD1", "font-size": "14px"},
                "nav-link": {
                    "font-size": "13.5px",
                    "text-align": "left",
                    "margin": "2px 0",
                    "padding": "10px 14px",
                    "border-radius": "8px",
                    "color": "rgba(255,255,255,0.65)",
                    "font-weight": "500",
                    "--hover-color": "rgba(0,255,209,0.08)",
                },
                "nav-link-selected": {
                    "background": "linear-gradient(135deg, #00FFD1, #00CCA6)",
                    "color": "#0a0f1e",
                    "font-weight": "600",
                },
            },
        )

        st.session_state.current_page = selected

        # User info / logout
        if is_logged_in():
            user = get_user()
            st.markdown("---")
            initial = user["name"][0].upper() if user.get("name") else "U"
            st.markdown(
                f"""
                <div style="display:flex;align-items:center;gap:10px;padding:10px;
                            background:rgba(255,255,255,0.03);border-radius:10px;
                            border:1px solid rgba(255,255,255,0.06);">
                    <div style="width:36px;height:36px;background:linear-gradient(135deg,#00FFD1,#00CCA6);
                                border-radius:50%;display:flex;align-items:center;justify-content:center;
                                font-size:0.9rem;color:#0a0f1e;font-weight:700;flex-shrink:0;">{initial}</div>
                    <div style="min-width:0;">
                        <div style="font-weight:600;color:white;font-size:0.82rem;
                                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{user['name']}</div>
                        <div style="font-size:0.68rem;color:rgba(255,255,255,0.35);
                                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{user['email']}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("🚪  Sign Out", use_container_width=True):
                logout_user()
                st.rerun()


# ──────────────────────────────────────────────
# Page Routing
# ──────────────────────────────────────────────
PAGE_MAP = {
    "Home": home.render,
    "Sign Up": signup.render,
    "Login": login.render,
    "Dashboard": dashboard.render,
    "About": about.render,
    "Tutorial": tutorial.render,
    "AI Agent": ai_agent.render,
    "What-If Simulator": whatif_simulator.render,
    "Settings": settings_page.render,
    "Help & Support": help_support.render,
}

page_fn = PAGE_MAP.get(st.session_state.current_page, home.render)
page_fn()
