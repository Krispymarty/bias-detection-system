"""
FairSight AI — Settings Page
Profile settings, preferences toggles, and account actions.
"""
import streamlit as st
from utils.auth import get_user


def render_html(html_str):
    """Helper to prevent Streamlit from rendering HTML chunks as Markdown code blocks.
    It removes newlines so that no line has >= 4 spaces of indentation."""
    cleaned = html_str.replace('\n', '')
    st.markdown(cleaned, unsafe_allow_html=True)


def render():
    render_html(
        """
        <style>
        .settings-header {
            margin-bottom: 20px;
            padding-top: 10px;
        }
        .settings-title {
            color: #ffffff;
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 10px;
            letter-spacing: -0.5px;
        }
        .settings-subtitle {
            color: #8b9bb4;
            font-size: 0.95rem;
            margin-bottom: 30px;
        }
        
        .nav-tabs {
            display: flex;
            gap: 30px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            margin-bottom: 40px;
        }
        .nav-tab {
            color: #a0aec0;
            font-size: 0.9rem;
            font-weight: 600;
            padding-bottom: 12px;
            cursor: pointer;
            position: relative;
        }
        .nav-tab.active {
            color: #00FFD1;
        }
        .nav-tab.active::after {
            content: '';
            position: absolute;
            bottom: -1px;
            left: 0;
            width: 100%;
            height: 2px;
            background: #00FFD1;
            box-shadow: 0 0 10px #00FFD1;
        }
        
        .prof-card {
            background: linear-gradient(180deg, #161b2e 0%, #111827 100%);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 40px 20px;
            text-align: center;
            margin-bottom: 20px;
        }
        @keyframes avatar-glow {
            0% { box-shadow: 0 0 15px rgba(0,255,209,0.2), inset 0 0 15px rgba(0,255,209,0.2); }
            50% { box-shadow: 0 0 35px rgba(0,255,209,0.5), inset 0 0 25px rgba(0,255,209,0.4); }
            100% { box-shadow: 0 0 15px rgba(0,255,209,0.2), inset 0 0 15px rgba(0,255,209,0.2); }
        }
        .avatar-circle {
            width: 110px;
            height: 110px;
            border-radius: 50%;
            background: #00FFD1;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.2rem;
            font-weight: 800;
            color: #111827;
            position: relative;
            animation: avatar-glow 3s infinite;
        }
        .avatar-edit {
            position: absolute;
            bottom: 0px;
            right: 0px;
            background: #2d3748;
            color: #fff;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            border: 3px solid #111827;
            cursor: pointer;
        }
        .prof-name { color: #ffffff; font-size: 1.15rem; font-weight: 700; margin-bottom: 5px; }
        .prof-role { color: #a0aec0; font-size: 0.85rem; margin-bottom: 15px; }
        .prof-org {
            display: inline-block;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            color: #a0aec0;
            padding: 5px 14px;
            border-radius: 20px;
            font-size: 0.75rem;
        }
        
        .quota-card {
            background: #111827;
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
        }
        .quota-title { color: #ffffff; font-size: 0.85rem; font-weight: 600; margin-bottom: 15px; }
        .quota-labels { display: flex; justify-content: space-between; color: #a0aec0; font-size: 0.75rem; margin-bottom: 8px; }
        .quota-bar-bg { width: 100%; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; position: relative; overflow: hidden; }
        @keyframes fillBar {
            0% { width: 0%; }
            100% { width: 78%; }
        }
        .quota-bar-fill {
            position: absolute;
            top: 0; left: 0; height: 100%;
            background: #00FFD1;
            border-radius: 3px;
            animation: fillBar 1.5s ease-out forwards;
            box-shadow: 0 0 10px rgba(0,255,209,0.5);
        }
        
        .section-header-title {
            color: #ffffff;
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
        }
        .section-header-title span { margin-right: 10px; font-size: 1.2rem; }
        
        .clearance-box {
            background: #0d121c;
            border-radius: 8px;
            padding: 15px 20px;
            color: #a0aec0;
            font-size: 0.85rem;
            line-height: 1.5;
            margin-bottom: 20px;
            margin-top: 5px;
        }
        .bio-label { color: rgba(255,255,255,0.6); font-size: 0.75rem; margin-bottom: 5px; display: block; }
        
        .btn-save-wrap { display: flex; justify-content: flex-end; margin-bottom: 40px;}
        .btn-save {
            background: #00FFD1;
            color: #000;
            border: none;
            padding: 10px 24px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.85rem;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,255,209,0.3);
            transition: transform 0.2s;
            text-decoration: none;
            display: inline-block;
        }
        .btn-save:hover { transform: translateY(-2px); }
        
        .danger-box {
            background: #111827;
            border: 1px solid rgba(255,100,100,0.2);
            border-left: 4px solid #ff6464;
            border-radius: 8px;
            padding: 25px 30px;
            margin-top: 30px;
            margin-bottom: 20px;
        }
        .danger-header { color: #ff6464; font-size: 1.05rem; font-weight: 700; margin-bottom: 10px; display: flex; align-items: center; }
        .danger-header span { margin-right: 10px; }
        .danger-txt { color: #8b9bb4; font-size: 0.85rem; line-height: 1.5; margin-bottom: 25px; }
        .danger-row { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 20px; }
        .danger-label { color: #fff; font-size: 0.9rem; }
        .btn-danger {
            background: transparent;
            border: 1px solid #ff6464;
            color: #ff6464;
            padding: 8px 20px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.85rem;
            cursor: pointer;
            transition: background 0.2s;
            text-decoration: none;
            display: inline-block;
        }
        .btn-danger:hover { background: rgba(255,100,100,0.1); }
        </style>
        """
    )
    
    # Header & Tab Navigation Mockup
    render_html(
        """
        <div class="settings-header">
            <div class="settings-title">Settings</div>
            <div class="settings-subtitle">Manage your account configurations, security protocols, and system appearance preferences.</div>
        </div>
        <div class="nav-tabs">
            <div class="nav-tab active">Account</div>
            <div class="nav-tab">Security</div>
            <div class="nav-tab">Notifications</div>
            <div class="nav-tab">API Keys</div>
            <div class="nav-tab">Appearance</div>
            <div class="nav-tab">Team</div>
        </div>
        """
    )

    # 2 Column layout
    c1, c2 = st.columns([1, 2.5])

    with c1:
        # User details Card
        render_html(
            """
            <div class="prof-card">
                <div class="avatar-circle">
                    ER
                    <div class="avatar-edit">✏️</div>
                </div>
                <div class="prof-name">Elena Rostova</div>
                <div class="prof-role">Lead Ethics Auditor</div>
                <div class="prof-org">🏢 FairSight AI</div>
            </div>
            
            <div class="quota-card">
                <div class="quota-title">System Access</div>
                <div class="quota-labels">
                    <span>API Quota</span>
                    <span style="color:#fff;font-weight:700;">78%</span>
                </div>
                <div class="quota-bar-bg"><div class="quota-bar-fill"></div></div>
            </div>
            """
        )

    with c2:
        # Personal Information
        render_html(
            """<div class="section-header-title"><span>👤</span> Personal Information</div>"""
        )
        
        r1c1, r1c2 = st.columns(2)
        with r1c1: st.text_input("Full Name", value="Elena Rostova", key="p_name")
        with r1c2: st.text_input("Email Address", value="elena.rostova@fairsight.ai", key="p_email")
        
        r2c1, r2c2 = st.columns(2)
        with r2c1: st.text_input("Organization", value="FairSight AI", key="p_org")
        with r2c2: st.text_input("Role", value="Lead Ethics Auditor", key="p_role")
        
        # Clearance Box & Save Button
        render_html(
            """
            <span class="bio-label">Bio / Clearance Level Notes</span>
            <div class="clearance-box">
                Level 4 Clearance. Primary oversight for generative models deployed in European sector.
            </div>
            <div class="btn-save-wrap">
                <a href="#" class="btn-save">💾 Save Changes</a>
            </div>
            """
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Preferences Box
        render_html(
            """<div class="section-header-title"><span>🌐</span> Preferences</div>"""
        )
        
        r3c1, r3c2 = st.columns(2)
        with r3c1: st.selectbox("Language", ["English (US)", "French", "German"], key="pref_lang")
        with r3c2: st.selectbox("Timezone", ["(UTC-05:00) Eastern Time", "UTC", "PST"], key="pref_tz")
        
        # Danger Zone
        render_html(
            """
            <div class="danger-box">
                <div class="danger-header"><span>⚠️</span> Danger Zone</div>
                <div class="danger-txt">
                    Permanently remove your personal account and all associated data from the FairSight AI platform. This action is irreversible.
                </div>
                <div class="danger-row">
                    <div class="danger-label">Delete Account</div>
                    <a href="#" class="btn-danger">✖ Delete Account</a>
                </div>
            </div>
            """
        )
