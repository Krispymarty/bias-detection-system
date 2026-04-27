"""
 Debiasiq AI — About Page
Hero, mission cards, team section, and technology overview.
"""
import streamlit as st
import textwrap
import base64
import os

def get_img_html(filepath, fallback_emoji):
    if os.path.exists(filepath):
        try:
            with open(filepath, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
                ext = filepath.split('.')[-1].lower()
                mime = "jpeg" if ext in ["jpg", "jpeg"] else ext
                return f'<img src="data:image/{mime};base64,{encoded}" style="width:100%; height:100%; object-fit:cover; border-radius:50%;">'
        except Exception:
            pass
    return fallback_emoji

def render_html(html_str):
    """Helper to prevent Streamlit from rendering HTML chunks as Markdown code blocks.
    It removes newlines so that no line has >= 4 spaces of indentation."""
    # Remove all newlines to make it a single line HTML string
    cleaned = html_str.replace('\n', '')
    st.markdown(cleaned, unsafe_allow_html=True)

def render():
    render_html(
        """
        <style>
        .hero-banner {
            background: linear-gradient(180deg, #161b2e 0%, #111827 100%);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 80px 40px;
            text-align: center;
            margin-bottom: 50px;
            position: relative;
            overflow: hidden;
        }
        .hero-banner::before {
            content: "";
            position: absolute;
            top: -50%; left: 50%; transform: translateX(-50%);
            width: 600px; height: 600px;
            background: radial-gradient(circle, rgba(0, 255, 209, 0.05) 0%, transparent 60%);
            pointer-events: none;
        }
        .mission-tag {
            color: #00FFD1; font-size: 0.75rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 20px;
        }
        .hero-title {
            color: #ffffff; font-size: 3.5rem; font-weight: 800; line-height: 1.1; margin-bottom: 25px; text-shadow: 0 0 20px rgba(255,255,255,0.1);
        }
        .hero-subtitle {
            color: #8b9bb4; font-size: 1.1rem; max-width: 650px; margin: 0 auto; line-height: 1.6;
        }
        
        .section-title {
            color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 25px; margin-top: 20px;
        }
        
        .tenet-card {
            background: #161b2a;
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 30px;
            height: 100%;
            position: relative;
            overflow: hidden;
            transition: transform 0.3s ease;
        }
        .tenet-card:hover {
             transform: translateY(-5px);
        }
        
        .tenet-icon {
            width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
            margin-bottom: 20px; float: right; font-size: 1.2rem;
        }
        .tenet-title { color: #ffffff; font-size: 1.1rem; font-weight: 700; margin-bottom: 15px; clear: both; }
        .tenet-desc { color: #8b9bb4; font-size: 0.85rem; line-height: 1.6; }
        
        /* Specific card treatments */
        .card-eq .tenet-icon { background: rgba(0,255,209,0.1); color: #00FFD1; }
        .card-tr .tenet-icon { background: rgba(139,146,246,0.1); color: #8b92f6; }
        .card-di .tenet-icon { background: rgba(255,100,100,0.1); color: #ff6464; }
        .card-dc { background: #161b2a url('data:image/svg+xml;utf8,<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="40" stroke="rgba(255,255,255,0.02)" stroke-width="1" fill="none"/></svg>') no-repeat center center; background-size: cover; }
        .card-dc .tenet-icon { background: rgba(0,255,209,0.1); color: #00FFD1; }
        
        .hackathon-banner {
            background: linear-gradient(90deg, #111827 0%, #0d1e20 100%);
            border: 1px solid rgba(0,255,209,0.2);
            border-radius: 12px;
            padding: 25px 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 50px 0;
        }
        .hackathon-icon {
            width: 50px; height: 50px; background: #0a0f1e; border: 1px solid #00FFD1; border-radius: 50%;
            display: flex; align-items: center; justify-content: center; color: #00FFD1; font-size: 1.4rem;
            margin-right: 20px; flex-shrink: 0; box-shadow: 0 0 15px rgba(0,255,209,0.2);
        }
        .hackathon-text-wrapper { flex-grow: 1; }
        .hackathon-title { color: #ffffff; font-size: 1.1rem; font-weight: 700; margin-bottom: 5px; }
        .hackathon-desc { color: #8b9bb4; font-size: 0.85rem; }
        .btn-outline-2 {
            border: 1px solid #00FFD1; color: #00FFD1; padding: 8px 20px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; text-decoration: none;
            transition: all 0.2s;
        }
        .btn-outline-2:hover { background: rgba(0,255,209,0.1); color: #00FFD1; }
        
        .arch-card {
            background: #161b2a; border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 30px 20px; text-align: center;
            height: 100%; transition: all 0.3s;
        }
        .arch-card:hover { transform: translateY(-5px); border-color: rgba(0,255,209,0.3); box-shadow: 0 10px 20px rgba(0,0,0,0.2); }
        .arch-img-cont {
            width: 91px; height: 120px; border-radius: 50%; margin: 0 auto 20px; overflow: hidden; border: 2px solid #1a2333;
            background: #111827; display: flex; align-items: center; justify-content: center; font-size: 3rem; color: #fff;
        }
        .arch-name { color: #ffffff; font-size: 1rem; font-weight: 700; margin-bottom: 5px; }
        .arch-role { color: #00FFD1; font-size: 0.75rem; font-weight: 700; margin-bottom: 15px; }
        .arch-desc { color: #8b9bb4; font-size: 0.75rem; line-height: 1.5; }
        
        .arch-img-cont img {
            border-radius: 50%;
            object-fit: cover;
            width: 100%;
            height: 100%;
        }
        
        .footer-wrap {
            margin-top: 80px; padding-top: 30px; border-top: 1px solid rgba(255,255,255,0.05);
            display: flex; justify-content: space-between; align-items: center; color: #6b7280; font-size: 0.75rem;
        }
        .footer-logo { color: #00FFD1; font-weight: 700; font-size: 1rem; }
        .footer-links { display: flex; gap: 20px; }
        .footer-links a { color: #6b7280; text-decoration: none; transition: color 0.2s; }
        .footer-links a:hover { color: #00FFD1; }
        </style>
        """
    )

    # Hero Banner
    render_html(
        """
        <div class="hero-banner">
            <div class="mission-tag">OUR MISSION</div>
            <div class="hero-title">Building the Ethereal<br>Arbiter</div>
            <div class="hero-subtitle">
                We are engineering unbiased intelligence.  Debiasiq AI exists to<br>
                dismantle algorithmic prejudice, replacing opaque decision-making<br>
                with mathematically pure, highly conductive truth.
            </div>
        </div>
        """
    )
    
    # Core Tenets Section
    render_html('<div class="section-title">Core Tenets</div>')
    
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        render_html(
            """
            <div class="tenet-card card-eq">
                <div class="tenet-icon">⚖️</div>
                <div class="tenet-title">Mathematical Equity</div>
                <div class="tenet-desc">Our algorithms are built from the ground up to recognize and neutralize bias before it manifests in the output layer.</div>
            </div>
            """
        )
    with r1c2:
        render_html(
            """
            <div class="tenet-card card-tr">
                <div class="tenet-icon">👁️</div>
                <div class="tenet-title">Absolute Transparency</div>
                <div class="tenet-desc">Every decision node is mapped, tracked, and explainable in real-time.</div>
            </div>
            """
        )

    st.markdown("<br>", unsafe_allow_html=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        render_html(
            """
            <div class="tenet-card card-di">
                <div class="tenet-icon">🛡️</div>
                <div class="tenet-title">Data Integrity</div>
                <div class="tenet-desc">We treat user data as an immutable asset, protected by cryptographic isolation.</div>
            </div>
            """
        )
    with r2c2:
        render_html(
            """
            <div class="tenet-card card-dc">
                <div class="tenet-icon">⚛️</div>
                <div class="tenet-title">Decentralized Cognition</div>
                <div class="tenet-desc">Distributing the processing load to ensure no single node dictates the 'truth' of the network.</div>
            </div>
            """
        )

    # Hackathon Banner
    render_html(
        """
        <div class="hackathon-banner">
            <div style="display:flex; align-items:center;">
                <div class="hackathon-icon">🏆</div>
                <div class="hackathon-text-wrapper">
                    <div class="hackathon-title">Global AI Ethics Hackathon Winners</div>
                    <div class="hackathon-desc">Recognized for our breakthrough in algorithmic fairness tracking.</div>
                </div>
            </div>
            <div>
                <a href="#" class="btn-outline-2">Read Report</a>
            </div>
        </div>
        """
    )
    
    # The Architects
    render_html('<div class="section-title">The Architects</div>')
    
    ac1, ac2, ac3, ac4 = st.columns(4)
    with ac1:
        render_html(
            f"""
            <div class="arch-card">
                <div class="arch-img-cont">{get_img_html('assets/team/member_1.jpeg', '👨‍🔬')}</div>
                <div class="arch-name">Yashmit Singh</div>
                <div class="arch-role">Ml model Training</div>
                <div class="arch-desc">Pioneered the 'Blind Node' architecture for unbiased data parsing.</div>
            </div>
            """
        )
    with ac2:
        render_html(
            f"""
            <div class="arch-card">
                <div class="arch-img-cont">{get_img_html('assets/team/member_2.jpeg', '👩‍💻')}</div>
                <div class="arch-name">Shiva Tyagi</div>
                <div class="arch-role">Full Stack </div>
                <div class="arch-desc">Former lead architect at a major quantum computing firm.</div>
            </div>
            """
        )
    with ac3:
        render_html(
            f"""
            <div class="arch-card">
                <div class="arch-img-cont">{get_img_html('assets/team/member_3.jpeg', '🧑‍🏫')}</div>
                <div class="arch-name">Sanyam Gambhir</div>
                <div class="arch-role">Automation</div>
                <div class="arch-desc">Ensures all models adhere to the strict Debiasiq Doctrine.</div>
            </div>
            """
        )
    with ac4:
        render_html(
            f"""
            <div class="arch-card">
                <div class="arch-img-cont">{get_img_html('assets/team/member_4.jpeg', '👩‍🎨')}</div>
                <div class="arch-name">Amishi Jain</div>
                <div class="arch-role">Data Cleaning</div>
                <div class="arch-desc">Translating complex AI decisions into the 'Ethereal Arbiter' interface.</div>
            </div>
            """
        )

    # Footer
    render_html(
        """
        <div class="footer-wrap">
            <div style="flex-grow:1; text-align:center;">© 2024 Debiasiq AI. Built for the Ethereal Arbiter.</div>
        </div>
        """
    )
