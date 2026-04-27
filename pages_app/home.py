"""
FairSight AI — Home Page
Exactly matching the requested dashboard UI with floating animations.
"""
import streamlit as st
from utils.auth import navigate_to
import json
import os
import matplotlib.pyplot as plt

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

    # ── Smart Simulation Input Experience ──
    st.markdown('<div class="panel-label" style="margin-top: 30px; margin-bottom: 20px; font-size:1.1rem; color:#00FFD1;">✨ Start Smart Simulation</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('''
        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(0,255,209,0.2); border-radius:16px; padding:24px; margin-bottom:40px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
        ''', unsafe_allow_html=True)
        
        col_in1, col_in2, col_in3 = st.columns(3)
        with col_in1:
            gender = st.selectbox("👤 Who are you?", ["Male", "Female"])
            job = st.selectbox("💼 Work Type", ["Private Job", "Self-Employed", "Student", "Unemployed"])
        with col_in2:
            age = st.slider("🎂 Age Group", 18, 65, 25)
            education = st.selectbox("🎓 Education", ["School", "Graduate", "Postgraduate"])
        with col_in3:
            income = st.selectbox("💰 Income Category", ["Low Income", "Middle Income", "High Income"])
            credit = st.slider("🏦 Loan Requirement", 1000, 1000000, 50000)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("⚡ Analyze My Fairness Score", use_container_width=True, type="primary"):
            st.session_state["simulation_input"] = {
                "gender": gender,
                "age": age,
                "income": income,
                "job": job,
                "education": education,
                "credit": credit
            }
            # ADD FLAGS (DO NOT TOUCH OTHER STATE)
            st.session_state["auto_run"] = True
            st.session_state["from_home"] = True
            # Custom App Routing
            st.session_state["current_page"] = "What-If Simulator"
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

    # Simulator Integration for Metrics
    def load_last_result():
        if os.path.exists("last_result.json"):
            try:
                with open("last_result.json", "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    results = st.session_state.get('last_result') or load_last_result()

    if results:
        fairness_score = results.get("fairness", {}).get("score", 0)
        prob_score = results.get("probability", 0)
        bias_score = results.get("bias", 0)
        risk_level = results.get("risk", "Unknown")
        acc_score = results.get("accuracy", 0)

        fairness_str = f"{fairness_score:.2f}%"
        bias_str = f"{bias_score:.4f}"
        impact_str = f"{(fairness_score / 100):.3f}"
        acc_str = f"{acc_score:.2f}%"
    else:
        fairness_score = 90.00
        prob_score = 0.85
        fairness_str = "90.00%"
        bias_str = "0.0125"
        impact_str = "0.900"
        acc_str = "88.00%"
        risk_level = "Low"

    # Top KPI Metrics Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_html(f'<div class="kpi-card"><div class="kpi-title">Fairness Score</div><div class="kpi-value">{fairness_str}</div></div>')
    with c2:
        render_html(f'<div class="kpi-card"><div class="kpi-title">Bias Gap</div><div class="kpi-value">{bias_str}</div></div>')
    with c3:
        render_html(f'<div class="kpi-card"><div class="kpi-title">Disparate Impact</div><div class="kpi-value">{impact_str}</div></div>')
    with c4:
        render_html(f'<div class="kpi-card"><div class="kpi-title">Risk Level</div><div class="kpi-value">{risk_level}</div></div>')

    st.markdown("<br><br>", unsafe_allow_html=True)

    # 2 Column layout: Chart vs Audit Runs
    col1, col2 = st.columns([2.2, 1])
    with col1:
        st.markdown('<h4 style="color:#fff;">Fairness vs Approval Probability</h4>', unsafe_allow_html=True)
        # Matplotlib integration
        fig, ax = plt.subplots(figsize=(6, 3))
        fig.patch.set_facecolor('#111827')
        ax.set_facecolor('#111827')
        labels = ["Fairness", "Approval Probability"]
        values = [fairness_score, prob_score * 100]
        bars = ax.bar(labels, values, color=['#00FFD1', '#A855F7'])
        
        ax.set_ylim(0, 100)
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_edgecolor((1.0, 1.0, 1.0, 0.2))
            
        st.pyplot(fig)
        
    with col2:
        st.markdown('<h4 style="color:#fff;">Latest Audit Report</h4>', unsafe_allow_html=True)
        if results:
            st.success("Simulation data available.")
            if st.button("Toggle Audit Report" if st.session_state.get("show_audit_report", False) else "Generate Audit Report", use_container_width=True):
                st.session_state.show_audit_report = not st.session_state.get("show_audit_report", False)
                st.rerun()
        else:
            st.warning("No simulation data available. Go to the simulator to run an audit.")

    st.markdown("<br><br>", unsafe_allow_html=True)

    if st.session_state.get("show_audit_report", False) and results:
        st.markdown('<h3 style="color:#fff; font-size:1.3rem; font-weight:700; margin-bottom:20px;">Demographic Fairness Report</h3>', unsafe_allow_html=True)
        report_data = results.get("report", {})
        fair_model = report_data.get("fair_model", {})
        by_group = fair_model.get("by_group", {})
        
        if not by_group and "baseline_model" in report_data:
            by_group = report_data["baseline_model"].get("by_group", {})
            
        if by_group:
            # 3-column layout for the cards to save vertical space
            cols = st.columns(3)
            idx = 0
            for group, metrics in by_group.items():
                group_name = group.replace("_", " ")
                sel_rate = metrics.get("selection_rate", 0) * 100
                tpr = metrics.get("true_positive_rate", 0) * 100
                fpr = metrics.get("false_positive_rate", 0) * 100
                fnr = metrics.get("false_negative_rate", 0) * 100
                count = int(metrics.get("count", 0))
                
                tpr_color = "#00FFD1" if tpr > 60 else ("#FFB800" if tpr > 40 else "#FF5050")
                
                card_html = f'''
                <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); border-radius:12px; padding:16px; margin-bottom:16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
                        <span style="font-size:1.2rem;">👥</span>
                        <h5 style="color:#fff; margin:0; font-size:1rem; font-weight:600;">{group_name}</h5>
                    </div>
                    
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                        <span style="color:#A0AEC0; font-size:0.85rem;">Selection Rate</span>
                        <span style="color:#FFF; font-weight:600; font-size:0.85rem;">{sel_rate:.2f}%</span>
                    </div>
                    <div style="width:100%; background:rgba(255,255,255,0.1); border-radius:4px; height:6px; margin-bottom:12px;">
                        <div style="width:{sel_rate:.2f}%; background:#A855F7; height:6px; border-radius:4px;"></div>
                    </div>
                    
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                        <span style="color:#A0AEC0; font-size:0.85rem;">True Positive Rate</span>
                        <span style="color:{tpr_color}; font-weight:700; font-size:0.85rem;">{tpr:.2f}%</span>
                    </div>
                    <div style="width:100%; background:rgba(255,255,255,0.1); border-radius:4px; height:6px; margin-bottom:12px;">
                        <div style="width:{tpr:.2f}%; background:{tpr_color}; height:6px; border-radius:4px;"></div>
                    </div>
                    
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                        <span style="color:#A0AEC0; font-size:0.85rem;">False Positive Rate</span>
                        <span style="color:#FFF; font-weight:600; font-size:0.85rem;">{fpr:.2f}%</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                        <span style="color:#A0AEC0; font-size:0.85rem;">False Negative Rate</span>
                        <span style="color:#FFF; font-weight:600; font-size:0.85rem;">{fnr:.2f}%</span>
                    </div>
                    
                    <div style="border-top:1px dashed rgba(255,255,255,0.1); padding-top:10px; display:flex; justify-content:space-between;">
                        <span style="color:#A0AEC0; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.05em;">Sample Count</span>
                        <span style="color:#FFF; font-weight:700; font-size:0.85rem;">{count:,}</span>
                    </div>
                </div>
                '''
                with cols[idx % 3]:
                    render_html(card_html)
                idx += 1
        else:
            st.warning("No demographic group metrics found in the report.")
            with st.expander("Raw Data"):
                st.json(results)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
    
    # # Core Governance Team
    # render_html('<h3 style="color:#fff; font-size:1.1rem; font-weight:600; margin-bottom:20px;">Core Governance Team</h3>')
    # tc1, tc2, tc3, tc4, tc5 = st.columns(5)
    
    # team = [
    #     ("Alex Thorne", "AL/ML ENGINEER", "👨‍💻"),
    #     ("Elena Vance", "BACKEND DEV", "👩‍💻"),
    #     ("Maya Koto", "FRONTEND DEV", "👩‍🎨"),
    #     ("Julian Read", "DATA ENGINEER", "🧑‍🔬"),
    #     ("Sarah Jin", "PRODUCT", "👩‍💼")
    # ]
    
    # for col, (name, role, emoji) in zip([tc1, tc2, tc3, tc4, tc5], team):
    #     with col:
    #         render_html(f'<div class="team-card"><div class="team-img" style="display:flex;align-items:center;justify-content:center;font-size:1.8rem;">{emoji}</div><div class="team-name">{name}</div><div class="team-role">{role}</div></div>')

    # st.markdown("<br><br>", unsafe_allow_html=True)
    
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
