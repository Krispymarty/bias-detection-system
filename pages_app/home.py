"""
FairSight AI — Home Page
Exactly matching the requested dashboard UI with floating animations.
"""
import streamlit as st
from utils.auth import navigate_to

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
        .auditor-badge {
            background: linear-gradient(90deg, rgba(0, 255, 209, 0.15) 0%, rgba(0, 255, 209, 0.05) 100%);
            border: 1px solid rgba(0, 255, 209, 0.4);
            color: #00FFD1;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
            display: inline-block;
            margin-bottom: 20px;
        }
        .hero-head {
            font-size: 2.8rem;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 15px;
            line-height: 1.2;
        }
        .hero-desc {
            font-size: 1rem;
            color: #a0aec0;
            max-width: 600px;
            margin-bottom: 30px;
            line-height: 1.6;
        }
        .btn-primary {
            background: linear-gradient(135deg, #00FFD1, #00CCA6);
            color: #0a0f1e !important;
            padding: 10px 24px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.85rem;
            text-decoration: none;
            display: inline-block;
            border: none;
            cursor: pointer;
            text-transform: uppercase;
        }
        .btn-outline {
            background: transparent;
            color: #00FFD1;
            padding: 10px 24px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.85rem;
            text-decoration: none;
            display: inline-block;
            border: 1px solid #00FFD1;
            cursor: pointer;
            text-transform: uppercase;
            margin-left: 15px;
        }
        .feature-tags {
            margin-top: 30px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .f-tag {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #a0aec0;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.75rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .f-tag::before {
            content: '';
            display: inline-block;
            width: 6px;
            height: 6px;
            background: #00FFD1;
            border-radius: 50%;
        }
        .kpi-card {
            background: #111827;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
        }
        .kpi-title {
            color: #00FFD1;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .kpi-value {
            color: #ffffff;
            font-size: 2rem;
            font-weight: 700;
        }
        .kpi-trend {
            font-size: 0.75rem;
            color: #00FFD1;
            margin-left: 10px;
        }
        
        .dash-card {
            background: #111827;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 24px;
            height: 100%;
        }
        .card-header {
            color: #ffffff;
            font-weight: 600;
            font-size: 1.1rem;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .badge {
            background: rgba(0, 255, 209, 0.15);
            color: #00FFD1;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.7rem;
            font-weight: 700;
        }
        .badge.warn {
            background: rgba(255, 184, 0, 0.15);
            color: #FFB800;
        }
        @keyframes float {
            0% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-15px) rotate(2deg); }
            100% { transform: translateY(0px) rotate(0deg); }
        }
        .animate-float {
            animation: float 6s ease-in-out infinite;
        }
        @keyframes floatReverse {
            0% { transform: translateY(0px); }
            50% { transform: translateY(15px); }
            100% { transform: translateY(0px); }
        }
        .animate-float-rev {
            animation: floatReverse 7s ease-in-out infinite;
        }
        
        .team-card {
            background: #111827;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        .team-img {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: #1a2333;
            margin: 0 auto 15px;
            border: 2px solid #00FFD1;
            color: #fff;
        }
        .team-name { color: #ffffff; font-weight: 600; font-size: 0.95rem; }
        .team-role { color: #00FFD1; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; margin-top: 5px; }
        
        .mod-card {
            background: #111827;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            transition: all 0.3s;
        }
        .mod-card:hover {
            transform: translateY(-5px);
            border-color: rgba(0, 255, 209, 0.3);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        .mod-icon {
            color: #00FFD1;
            font-size: 1.5rem;
            margin-bottom: 15px;
        }
        .mod-title { color: #ffffff; font-weight: 600; font-size: 1rem; margin-bottom: 10px; }
        .mod-desc { color: #a0aec0; font-size: 0.85rem; line-height: 1.5; }
        
        .roadmap-item {
            position: relative;
            padding-left: 30px;
            margin-bottom: 30px;
            border-left: 1px dashed rgba(255,255,255,0.1);
        }
        .roadmap-icon {
            position: absolute;
            left: -15px;
            top: 0;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: #111827;
            border: 1px solid #00FFD1;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #00FFD1;
            font-size: 0.8rem;
        }
        .roadmap-title { color: #ffffff; font-weight: 600; font-size: 1rem; margin-bottom: 5px; }
        .roadmap-desc { color: #a0aec0; font-size: 0.85rem; }
        .roadmap-status { 
            background: rgba(0, 255, 209, 0.15); color: #00FFD1; 
            padding: 3px 8px; border-radius: 4px; font-size: 0.65rem; font-weight: 700;
            display: inline-block; margin-top: 10px;
        }
        </style>
        """
    )
    
    # Hero section matching the top of the image
    render_html(
        """
        <div style="position:relative; margin-top: 20px; margin-bottom: 50px;">
            <div style="position:absolute; right:5%; top:-10%; pointer-events:none; opacity: 0.4;" class="animate-float">
               <svg width="350" height="350" viewBox="0 0 400 400" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="200" cy="200" r="150" stroke="#00FFD1" stroke-width="1" stroke-dasharray="8 8"/>
                <circle cx="320" cy="120" r="6" fill="#00FFD1" style="filter:drop-shadow(0 0 10px #00FFD1);"/>
               </svg>
            </div>
            <div style="position:absolute; right:20%; top:20%; pointer-events:none; opacity: 0.3;" class="animate-float-rev">
               <svg width="200" height="200" viewBox="0 0 200 200" fill="none">
                <path d="M100 0 L200 100 L100 200 L0 100 Z" stroke="#00FFD1" stroke-width="0.5"/>
               </svg>
            </div>
            
            <div class="auditor-badge">AUDITOR MODE</div>
            <div class="hero-head">Ensuring Fairness in AI</div>
            <div class="hero-desc">
                Continuous monitoring and bias mitigation for mission-critical neural architectures. Deploy with confidence, audit with precision.
            </div>
            
            <div>
                <a href="#" class="btn-primary" style="margin-right:15px;">VIEW LANDING PAGE</a>
                <a href="#" class="btn-outline">HIRING PORTAL</a>
            </div>
            
            <div class="feature-tags">
                <div class="f-tag">Counterfactual Ready</div>
                <div class="f-tag">Bias Trend Tracking</div>
                <div class="f-tag">Compliance Logs</div>
            </div>
        </div>
        """
    )

    # Simulator Integration for Metrics
    results = st.session_state.get('simulation_results', None)
    if results:
        fairness = f"{results['fairness']:.2f}"
        bias = results['bias'] * 100
        bias_str = f"{bias:.2f}%"
        impact = f"{(results['fairness'] / 100):.3f}"
        acc = f"{results['accuracy']:.2f}%"
    else:
        fairness = "90.00"
        bias_str = "10.00%"
        impact = "0.920"
        acc = "88.00%"

    # Top KPI Metrics Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_html(f'<div class="kpi-card"><div class="kpi-title">Fairness Score</div><div class="kpi-value">{fairness}<span class="kpi-trend">↗ +2.1%</span></div></div>')
    with c2:
        render_html(f'<div class="kpi-card"><div class="kpi-title">Biasness %</div><div class="kpi-value">{bias_str}<span class="kpi-trend" style="color:#FFB800;">↘ -0.5%</span></div></div>')
    with c3:
        render_html(f'<div class="kpi-card"><div class="kpi-title">Disparate Impact</div><div class="kpi-value">{impact}<span class="kpi-trend">↗ +0.02</span></div></div>')
    with c4:
        render_html(f'<div class="kpi-card"><div class="kpi-title">Model Accuracy</div><div class="kpi-value">{acc}<span class="kpi-trend">↗ +1.1%</span></div></div>')

    st.markdown("<br><br>", unsafe_allow_html=True)

    # 2 Column layout: Chart vs Audit Runs
    col1, col2 = st.columns([2.2, 1])
    with col1:
        render_html(
            """
            <div class="dash-card">
                <div class="card-header">
                    Fairness vs Bias Trend
                    <div>
                        <span class="badge" style="background:#00FFD1; color:#000;">7 DAYS</span>
                        <span class="badge" style="background:transparent; border:1px solid rgba(255,255,255,0.2); color:#fff; margin-left:8px;">30 DAYS</span>
                    </div>
                </div>
                <div style="height: 250px; display:flex; align-items:flex-end; justify-content:space-between; padding-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.05); margin-top:40px;">
                    <!-- Mocking the line chart visually -->
                    <div style="width:100%; height:150px; position:relative;">
                        <svg viewBox="0 0 100 40" preserveAspectRatio="none" style="width:100%; height:100%; overflow:visible;">
                            <!-- Fairness line -->
                            <path d="M0,35 Q15,25 30,30 T60,20 T100,5" fill="none" stroke="#00FFD1" stroke-width="1.5" />
                            <!-- Bias line -->
                            <path d="M0,5 Q15,10 30,8 T60,15 T100,25" fill="none" stroke="#FF5050" stroke-width="1" stroke-dasharray="2 2" />
                        </svg>
                    </div>
                </div>
                <div style="display:flex; justify-content:space-between; margin-top:20px; color:#666; font-size:0.75rem; font-weight:600;">
                    <span>MON</span><span>TUE</span><span>WED</span><span>THU</span><span>FRI</span><span>SAT</span><span>SUN</span>
                </div>
            </div>
            """
        )
    with col2:
        render_html(
            """
            <div class="dash-card" style="margin-bottom: 15px; height: auto;">
                <div class="card-header" style="margin-bottom: 15px;">Latest Audit Run <span class="badge">PASS</span></div>
                <div style="font-size:0.7rem; color:rgba(255,255,255,0.3); font-weight:700; text-transform:uppercase; margin-bottom:5px;">RUN ID</div>
                <div style="font-family:monospace; color:#fff; margin-bottom:15px; font-size:0.85rem;">AMJO-882319-RF-2524</div>
                <div style="font-size:0.7rem; color:rgba(255,255,255,0.3); font-weight:700; text-transform:uppercase; margin-bottom:5px;">TIMESTAMP</div>
                <div style="font-family:monospace; color:#fff; margin-bottom:15px; font-size:0.85rem;">Oct 24, 2023 - 14:22:11 GMT</div>
                <div style="font-size:0.7rem; color:rgba(255,255,255,0.3); font-weight:700; text-transform:uppercase; margin-bottom:5px;">STATUS REPORT</div>
                <div style="color:rgba(255,255,255,0.6); font-size:0.8rem; line-height:1.5;">Zero critical bias found. Minor drift detected in demographic parity for "Age" feature cluster.</div>
            </div>
            <div class="dash-card" style="height: auto;">
                <div class="card-header" style="margin-bottom:10px;">Pending Warning <span class="badge warn">WARN</span></div>
                <div style="color:rgba(255,255,255,0.6); font-size:0.8rem; line-height:1.5;">Model calibration required for subgroup 'Region-03'.</div>
            </div>
            """
        )

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Core Governance Team
    render_html('<h3 style="color:#fff; font-size:1.1rem; font-weight:600; margin-bottom:20px;">Core Governance Team</h3>')
    tc1, tc2, tc3, tc4, tc5 = st.columns(5)
    
    team = [
        ("Alex Thorne", "AL/ML ENGINEER", "👨‍💻"),
        ("Elena Vance", "BACKEND DEV", "👩‍💻"),
        ("Maya Koto", "FRONTEND DEV", "👩‍🎨"),
        ("Julian Read", "DATA ENGINEER", "🧑‍🔬"),
        ("Sarah Jin", "PRODUCT", "👩‍💼")
    ]
    
    for col, (name, role, emoji) in zip([tc1, tc2, tc3, tc4, tc5], team):
        with col:
            render_html(f'<div class="team-card"><div class="team-img" style="display:flex;align-items:center;justify-content:center;font-size:1.8rem;">{emoji}</div><div class="team-name">{name}</div><div class="team-role">{role}</div></div>')

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Analytical Modules
    render_html('<h3 style="color:#fff; font-size:1.1rem; font-weight:600; margin-bottom:20px;">Analytical Modules</h3>')
    mc1, mc2, mc3 = st.columns(3)
    
    with mc1:
        render_html('<div class="mod-card"><div class="mod-icon">🔍</div><div class="mod-title">Bias Detection</div><div class="mod-desc">Automated identification of disparate impact across 50+ protected attributes.</div></div>')
        render_html('<div class="mod-card"><div class="mod-icon">👁️</div><div class="mod-title">Explainability Engine</div><div class="mod-desc">SHAP and LIME integration for granular feature contribution analysis.</div></div>')
    with mc2:
        render_html('<div class="mod-card"><div class="mod-icon">💬</div><div class="mod-title">AI Chat</div><div class="mod-desc">Conversational interface for deep-diving into model decision logic and logs.</div></div>')
        render_html('<div class="mod-card"><div class="mod-icon">🛡️</div><div class="mod-title">Admin Dashboard</div><div class="mod-desc">Enterprise-level control for permissions, API keys, and global policies.</div></div>')
    with mc3:
        render_html('<div class="mod-card"><div class="mod-icon">📊</div><div class="mod-title">Bias Score Analyzer</div><div class="mod-desc">Real-time quantification of parity metrics and statistical significance.</div></div>')
        render_html('<div class="mod-card"><div class="mod-icon">💡</div><div class="mod-title">What-If Simulator <span class="badge">V2</span></div><div class="mod-desc">Simulate hypothetical data shifts to stress-test model robustness before release.</div></div>')

    st.markdown("<br>", unsafe_allow_html=True)

    # 2 Column layout: Heatmap vs Performance
    hc1, hc2 = st.columns(2)
    with hc1:
        render_html(
            """
            <div class="dash-card">
                <div class="card-header">Global Fairness Heatmap</div>
                <div style="height:250px; display:flex; align-items:center; justify-content:center; position:relative;" class="animate-float">
                    <!-- Placeholder for world map since literal map image asset isn't present, we draw stylized SVG world dots -->
                    <svg viewBox="0 0 400 200" width="100%" height="100%" opacity="0.6">
                        <!-- Simplified map shapes or generic interconnected nodes -->
                        <path d="M50 40 Q80 20 120 50 T200 80 T300 40 T380 90" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
                        <path d="M30 140 Q80 180 150 120 T250 150 T360 120" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
                        <circle cx="120" cy="50" r="3" fill="#00FFD1" style="filter:drop-shadow(0 0 8px #00FFD1);"/>
                        <circle cx="200" cy="80" r="5" fill="#00FFD1" style="filter:drop-shadow(0 0 10px #00FFD1);"/>
                        <circle cx="300" cy="40" r="3" fill="#00FFD1"/>
                        <circle cx="150" cy="120" r="4" fill="#00FFD1" style="filter:drop-shadow(0 0 5px #00FFD1);"/>
                        <circle cx="250" cy="150" r="2" fill="#00FFD1"/>
                        <circle cx="360" cy="120" r="4" fill="#00FFD1" style="filter:drop-shadow(0 0 10px #00FFD1);"/>
                        <circle cx="80" cy="140" r="3" fill="#00FFD1"/>
                    </svg>
                </div>
            </div>
            """
        )
    with hc2:
         render_html(
            """
            <div class="dash-card" style="height: 100%; display: flex; flex-direction: column;">
                <div class="card-header">Bias Detection Performance</div>
                <div style="margin-top:20px; flex-grow: 1; display: flex; flex-direction: column; justify-content: center;">
                    <div style="display:flex; justify-content:space-between; color:#fff; font-size:0.85rem; margin-bottom:8px;">
                        <span>Detection Precision</span><span style="color:#00FFD1; font-weight:bold;">98.4%</span>
                    </div>
                    <div style="width:100%; height:6px; background:rgba(255,255,255,0.1); border-radius:3px; margin-bottom:30px;">
                        <div style="width:98.4%; height:100%; background:#00FFD1; border-radius:3px; box-shadow:0 0 10px rgba(0,255,209,0.5);"></div>
                    </div>
                    
                    <div style="display:flex; justify-content:space-between; color:#fff; font-size:0.85rem; margin-bottom:8px;">
                        <span>Dataset Coverage</span><span style="color:#00FFD1; font-weight:bold;">82.1%</span>
                    </div>
                    <div style="width:100%; height:6px; background:rgba(255,255,255,0.1); border-radius:3px; margin-bottom:40px;">
                        <div style="width:82.1%; height:100%; background:#00FFD1; border-radius:3px; box-shadow:0 0 10px rgba(0,255,209,0.5);"></div>
                    </div>
                    
                    <a href="#" style="background:#00FFD1; color:#000; display:block; text-align:center; padding:12px; border-radius:8px; font-weight:700; font-size:0.85rem; text-decoration:none; margin-top: auto;">GENERATE AUDIT REPORT</a>
                </div>
            </div>
            """
        )   

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Intelligence Roadmap
    render_html('<div style="display:flex; justify-content:center; align-items:center; margin-bottom:40px;"><h3 style="color:#fff; font-size:1.2rem; font-weight:700;">Intelligence Roadmap</h3></div>')
    
    render_html(
        """
        <div style="max-width: 700px; margin: 0 auto; padding-left:20px; padding-bottom:50px;">
            <div class="roadmap-item">
                <div class="roadmap-icon">✓</div>
                <div class="roadmap-title">Foundation</div>
                <div class="roadmap-desc">Core bias detection algorithms and integration APIs established. Multi-tenant support activated.</div>
                <div class="roadmap-status">COMPLETED</div>
            </div>
            
            <div class="roadmap-item" style="border-left-color:#00FFD1;">
                <div class="roadmap-icon" style="border-color:#00FFD1; background:#00FFD1; color:#000; box-shadow:0 0 15px rgba(0,255,209,0.5);">⚡</div>
                <div class="roadmap-title" style="color:#00FFD1;">Intelligence</div>
                <div class="roadmap-desc" style="color:#fff;">What-if scenario modeling and real-time counterfactual analysis launch. LLM bias auditing integration.</div>
                <div class="roadmap-status" style="background:transparent; border:1px solid rgba(255,255,255,0.2); color:#fff; font-weight:600;">IN PROGRESS</div>
            </div>
            
            <div class="roadmap-item" style="border-left:none;">
                <div class="roadmap-icon" style="border-color:rgba(255,255,255,0.2); color:rgba(255,255,255,0.4);">🚀</div>
                <div class="roadmap-title" style="color:rgba(255,255,255,0.6);">Delivery</div>
                <div class="roadmap-desc" style="color:rgba(255,255,255,0.4);">Global marketplace for pre-certified unbiased models and autonomous governance agents.</div>
                <div class="roadmap-status" style="background:transparent; color:rgba(255,255,255,0.4); padding:0; margin-top:5px;">Q4 2024</div>
            </div>
        </div>
        """
    )
