"""
FairSight AI — Sign Up Page (Futuristic AI SaaS Redesign)
"""

import streamlit as st
import base64
from utils.auth import signup_user, google_login, handle_callback

@st.cache_data
def load_image_base64(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""


def render():
    # ✅ HANDLE GOOGLE CALLBACK FIRST
    handle_callback()

    # ✅ IF GOOGLE LOGIN SUCCESS → AUTO SIGNUP
    if st.session_state.get("logged_in") and st.session_state.get("user"):
        user = st.session_state["user"]
        name = user.get("name", "")
        email = user.get("email", "")

        signup_user(name, email, "google_oauth")

        st.session_state.signed_up = True
        st.session_state.signup_email = email
        st.session_state.current_page = "Home"

        st.success(f"Welcome {name} 🎉")
        st.rerun()

    bg_img_b64 = load_image_base64("assets/cyan_wave_particles.png")
    bg_style = f"background-image: url('data:image/png;base64,{bg_img_b64}');" if bg_img_b64 else "background-color: #02040a;"

    # Injecting single complete style block
    st.markdown(
        f"""
        <style>
        /* 1. LAYOUT & RESET */
        [data-testid="stSidebar"], header[data-testid="stHeader"] {{ display: none !important; }}
        .block-container {{ padding: 0 !important; max-width: 100% !important; }}
        [data-testid="stHorizontalBlock"] {{ gap: 0 !important; align-items: stretch; }}
        [data-testid="column"]:nth-child(1) {{ padding: 0 !important; margin: 0 !important; }}
        [data-testid="column"]:nth-child(2) {{
            padding: 4vh 4rem !important;
            min-height: 100vh;
            background: linear-gradient(135deg, #02040a 0%, #0a0f1e 100%);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}

        /* Hide scrollbar visually */
        ::-webkit-scrollbar {{ display: none !important; }}
        * {{ -ms-overflow-style: none !important; scrollbar-width: none !important; }}

        /* 2. ANIMATIONS */
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes pulseGlow {{
            0% {{ box-shadow: 0 0 10px rgba(0, 255, 209, 0.2); }}
            50% {{ box-shadow: 0 0 25px rgba(0, 255, 209, 0.4); }}
            100% {{ box-shadow: 0 0 10px rgba(0, 255, 209, 0.2); }}
        }}
        @keyframes flowWave {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        @keyframes glassFloat {{
            0%, 100% {{ transform: translateY(0) rotateX(0deg) rotateY(0deg); }}
            50% {{ transform: translateY(-10px) rotateX(2deg) rotateY(-2deg); }}
        }}

        /* 3. HERO SECTION (LEFT) */
        .hero-section {{
            height: 100vh;
            width: 100%;
            {bg_style}
            background-size: 150% 150%;
            animation: flowWave 25s ease-in-out infinite;
            position: sticky;
            top: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            perspective: 1000px;
        }}
        .glass-box {{
            z-index: 10;
            padding: 3.5rem;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            background: rgba(255, 255, 255, 0.05);
            border-radius: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 20px 50px rgba(0,0,0,0.8), inset 0 0 30px rgba(0,255,209,0.05);
            animation: glassFloat 8s ease-in-out infinite, fadeInUp 1s ease-out;
            transform-style: preserve-3d;
            transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }}
        .glass-box:hover {{
            transform: scale(1.02) rotateX(3deg) rotateY(-3deg);
        }}
        .hero-title {{
            color: #ffffff;
            font-size: 4rem;
            font-weight: 900;
            text-align: center;
            margin: 0;
            line-height: 1.1;
            text-shadow: 0 0 25px rgba(0, 255, 209, 0.5);
            letter-spacing: -0.02em;
        }}

        /* 4. CARD OVERLAY (RIGHT) */
        .auth-form-wrapper {{
            max-width: 440px;
            margin: 0 auto;
            width: 100%;
            animation: fadeInUp 0.8s ease-out forwards;
        }}
        .auth-header {{
            color: #ffffff !important;
            font-size: 2.5rem !important;
            font-weight: 800 !important;
            margin-bottom: 0.5rem !important;
        }}
        .auth-subheader {{
            color: rgba(255, 255, 255, 0.5) !important;
            font-size: 1rem !important;
            margin-bottom: 1.5rem !important;
        }}

        div[data-testid="stForm"] {{
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 20px !important;
            padding: 2rem !important;
            backdrop-filter: blur(15px) !important;
            box-shadow: 0 15px 40px rgba(0,0,0,0.5) !important;
            transition: all 0.3s ease !important;
            margin-bottom: 1.5rem !important;
        }}
        div[data-testid="stForm"]:hover {{
            border-color: rgba(0, 255, 209, 0.2) !important;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6), 0 0 20px rgba(0,255,209,0.05) !important;
            transform: translateY(-2px);
        }}

        /* 5. FORM INPUTS */
        .stTextInput, .stSelectbox {{
            position: relative !important;
            margin-bottom: 0.5rem !important;
        }}
        .stTextInput label, .stSelectbox label {{
            color: rgba(255, 255, 255, 0.6) !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            margin-bottom: 0.3rem !important;
            transition: all 0.3s ease !important;
        }}
        .stTextInput > div > div > input,
        .stSelectbox > div > div > div {{
            background: rgba(0, 0, 0, 0.3) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            color: #fff !important;
            padding: 0.8rem 1.2rem !important;
            font-size: 1rem !important;
            transition: all 0.3s ease !important;
        }}
        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > div:focus-within {{
            border-color: #00FFD1 !important;
            box-shadow: 0 0 15px rgba(0, 255, 209, 0.3) !important;
            background: rgba(0, 255, 209, 0.03) !important;
        }}
        button[title="View password"] {{ color: #00FFD1 !important; }}
        
        .stCheckbox [data-testid="stMarkdownContainer"] p {{
            font-size: 0.9rem !important;
            color: rgba(255,255,255,0.7) !important;
        }}

        /* 6. BUTTONS */
        button[kind="primary"] {{
            background: linear-gradient(135deg, #00FFD1 0%, #00CCA6 100%) !important;
            color: #040914 !important;
            font-weight: 800 !important;
            border-radius: 12px !important;
            padding: 0.6rem 1rem !important;
            border: none !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            animation: pulseGlow 3s infinite;
            margin-top: 1rem !important;
        }}
        button[kind="primary"]:hover {{
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 10px 25px rgba(0, 255, 209, 0.4) !important;
            filter: brightness(1.1) !important;
        }}
        button[kind="primary"]:active {{ transform: scale(0.96) !important; }}

        button[kind="secondary"] {{
            background: #ffffff !important;
            color: #000000 !important;
            border-radius: 12px !important;
            border: none !important;
            font-weight: 700 !important;
            padding: 0.6rem 1rem !important;
            transition: all 0.3s ease !important;
        }}
        button[kind="secondary"]:hover {{
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 8px 20px rgba(255, 255, 255, 0.15) !important;
        }}
        button[kind="secondary"]:active {{ transform: scale(0.96) !important; }}
        
        .divider {{
            display: flex;
            align-items: center;
            margin: 1.5rem 0;
        }}
        .divider hr {{
            flex-grow: 1;
            border-color: rgba(255,255,255,0.1);
            margin: 0;
        }}
        .divider span {{
            padding: 0 1rem;
            color: rgba(255,255,255,0.3);
            font-size: 0.8rem;
            font-weight: 600;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([1.2, 1])

    with left_col:
        st.markdown(
            """
            <div class="hero-section">
                <div class="glass-box">
                    <h1 class="hero-title">Join the Fight<br>Against AI Bias</h1>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )

    with right_col:
        st.markdown(
            """
            <div class="auth-form-wrapper">
                <div class="auth-header">Create account</div>
                <div class="auth-subheader">Start making AI fair and unbiased</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown('<div class="auth-form-wrapper">', unsafe_allow_html=True)

        # ✅ REAL GOOGLE SIGNUP BUTTON
        if st.button("🌐 Sign up with Google", use_container_width=True, type="secondary"):
            google_login()

        st.markdown(
            """
            <div class="divider">
                <hr><span>OR REGISTER WITH EMAIL</span><hr>
            </div>
            """, unsafe_allow_html=True
        )

        with st.form("signup_form"):
            c1, c2 = st.columns(2)
            with c1:
                fname = st.text_input("👤 First Name", placeholder="Jane")
            with c2:
                lname = st.text_input("👥 Last Name", placeholder="Doe")

            email = st.text_input("✉️ Work Email", placeholder="jane@company.com")
            password = st.text_input("🔒 Password", type="password", placeholder="••••••••")

            c3, c4 = st.columns(2)
            with c3:
                org = st.text_input("🏢 Organization", placeholder="Acme Corp")
            with c4:
                role = st.selectbox("🎯 Role", ["Select...", "Data Scientist", "ML Engineer", "Product Manager", "Other"])

            agree = st.checkbox("I agree to Terms & Conditions")

            submitted = st.form_submit_button("Create Account →", use_container_width=True)

            if submitted:
                if not fname or not lname or not email or not password or not org or role == "Select..." or not agree:
                    st.error("⚠️ Fill all required fields and accept terms")
                else:
                    success = signup_user(f"{fname} {lname}", email, password)
                    if success:
                        st.success("✅ Account created successfully!")
                        st.session_state.current_page = "Login"
                        st.rerun()
                    else:
                        st.error("❌ Email already exists or invalid")

        if st.button("Already have an account? Sign in", use_container_width=True, type="secondary"):
            st.session_state.current_page = "Login"
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)