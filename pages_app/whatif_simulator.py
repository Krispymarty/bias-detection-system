"""
FairSight AI — What-If Simulator Page
Premium SaaS-grade UI with full backend integration.
"""
import streamlit as st
import json
import plotly.graph_objects as go
from datetime import datetime
from utils.whatif.simulator import run_audit, compare_runs, get_fairness_report, parse_audit_response
from utils.whatif.pdf_report import generate_pdf_report
from utils.firebase_logger import log_simulation


def _make_hashable(d):
    """Convert a dict to a hashable frozenset for caching."""
    items = []
    for k, v in sorted(d.items()):
        if isinstance(v, dict):
            items.append((k, _make_hashable(v)))
        elif isinstance(v, list):
            items.append((k, tuple(v)))
        else:
            items.append((k, v))
    return tuple(items)


@st.cache_data(show_spinner=False)
def cached_run(_payload_hash, payload):
    """Cached API call. _payload_hash is used for cache key only."""
    return run_audit(payload)


def generate_ai_insight(result):
    if not result or "error" in result:
        return "⚠️ Simulation could not run properly."
    fairness = result.get("fairness_score", 0)
    if fairness < 50:
        return "⚠️ High bias detected. Consider improving diversity inputs."
    elif fairness < 80:
        return "🟡 Moderate fairness. Some bias risk exists."
    else:
        return "🟢 Model appears fair and balanced."

def transform_input(data):
    return {
        "CODE_GENDER": "M" if data["gender"] == "Male" else "F",
        "AGE": data["age"],
        "INCOME_GROUP": "Low" if "Low" in data["income"] else "Medium",
        "OCCUPATION_TYPE": data["job"],
        "NAME_EDUCATION_TYPE": data["education"],
        "AMT_CREDIT": data["credit"],

        # SAFE DEFAULTS (to avoid API error)
        "AMT_INCOME_TOTAL": 100000,
        "AMT_ANNUITY": 5000,
        "EXT_SOURCE_1": 0.5,
        "EXT_SOURCE_2": 0.5,
        "EXT_SOURCE_3": 0.5
    }


# ──────────────────────────────────────────────
# Theme Constants
# ──────────────────────────────────────────────
CYAN = "#00FFD1"
CYAN_DIM = "rgba(0,255,209,0.15)"
PURPLE = "#A855F7"
PURPLE_DIM = "rgba(168,85,247,0.15)"
RED = "#FF5050"
YELLOW = "#FFD700"
BG_DARK = "#0a0f1e"
CARD_BG = "rgba(255,255,255,0.03)"
BORDER = "rgba(255,255,255,0.06)"


# ──────────────────────────────────────────────
# Gauge Chart Builder
# ──────────────────────────────────────────────
def _gauge(value, title, max_val=100, suffix="%"):
    """Premium dark gauge chart."""
    if value > 80:
        bar_color = CYAN
    elif value > 60:
        bar_color = YELLOW
    else:
        bar_color = RED

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(font=dict(color=bar_color, size=36, family="Inter"), suffix=suffix if suffix else ""),
        title=dict(text=title, font=dict(color="rgba(255,255,255,0.55)", size=12, family="Inter")),
        gauge=dict(
            axis=dict(range=[0, max_val], tickcolor="rgba(255,255,255,0.15)", dtick=20,
                      tickfont=dict(size=9, color="rgba(255,255,255,0.2)")),
            bar=dict(color=bar_color, thickness=0.75),
            bgcolor="rgba(255,255,255,0.02)",
            borderwidth=0,
            steps=[
                dict(range=[0, max_val * 0.6], color="rgba(255,80,80,0.05)"),
                dict(range=[max_val * 0.6, max_val * 0.8], color="rgba(255,215,0,0.05)"),
                dict(range=[max_val * 0.8, max_val], color="rgba(0,255,209,0.05)"),
            ],
            threshold=dict(line=dict(color=CYAN, width=2), thickness=0.8, value=value),
        ),
    ))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif"),
        height=200,
        margin=dict(l=18, r=18, t=45, b=8),
    )
    return fig


def _risk_badge(risk):
    """HTML risk level badge."""
    colors = {
        "Low": (CYAN, "rgba(0,255,209,0.12)"),
        "Medium": (YELLOW, "rgba(255,215,0,0.12)"),
        "High": (RED, "rgba(255,80,80,0.12)"),
        "Error": ("#999", "rgba(150,150,150,0.12)"),
        "Unknown": ("#666", "rgba(100,100,100,0.08)"),
    }
    fg, bg = colors.get(risk, ("#999", "rgba(150,150,150,0.1)"))
    return (
        f'<span style="background:{bg}; color:{fg}; padding:6px 18px; border-radius:30px; '
        f'font-weight:700; font-size:0.85rem; letter-spacing:0.04em; '
        f'border:1px solid {fg}30; display:inline-block;">{risk.upper()}</span>'
    )


def _metric_tile(label, value, icon, color=CYAN):
    """Glass metric tile HTML."""
    return f'''
    <div style="background:{CARD_BG}; border:1px solid {BORDER}; border-radius:14px;
                padding:20px 16px; text-align:center; position:relative; overflow:hidden;">
        <div style="position:absolute; top:-20px; right:-20px; font-size:4rem; opacity:0.04;">{icon}</div>
        <div style="font-size:0.7rem; color:rgba(255,255,255,0.4); text-transform:uppercase;
                    letter-spacing:0.1em; font-weight:600; margin-bottom:8px;">{label}</div>
        <div style="font-size:1.6rem; font-weight:800; color:{color};
                    text-shadow:0 0 20px {color}40;">{value}</div>
    </div>
    '''


# ──────────────────────────────────────────────
# Page CSS
# ──────────────────────────────────────────────
PAGE_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

.sim-hero {{
    background: linear-gradient(135deg, #111827 0%, #0d121c 60%, #0f1729 100%);
    border: 1px solid rgba(0,255,209,0.12);
    border-radius:22px; padding:36px 40px; margin-bottom:36px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04);
    position:relative; overflow:hidden;
}}
.sim-hero::before {{
    content:''; position:absolute; top:-50%; right:-30%; width:500px; height:500px;
    background:radial-gradient(circle, rgba(0,255,209,0.06) 0%, transparent 70%);
    pointer-events:none;
}}
.sim-hero::after {{
    content:''; position:absolute; bottom:-40%; left:-20%; width:400px; height:400px;
    background:radial-gradient(circle, rgba(168,85,247,0.05) 0%, transparent 70%);
    pointer-events:none;
}}
.sim-hero-title {{
    font-size:2.2rem; font-weight:900; color:#fff; margin-bottom:8px;
    text-shadow:0 0 30px rgba(0,255,209,0.3); position:relative; z-index:1;
}}
.sim-hero-sub {{
    font-size:1rem; color:rgba(255,255,255,0.5); line-height:1.7;
    position:relative; z-index:1; max-width:600px;
}}
.panel-label {{
    background:{CARD_BG}; border:1px solid {BORDER}; border-radius:12px;
    padding:12px 18px; color:{CYAN}; font-weight:800; text-transform:uppercase;
    font-size:0.78rem; letter-spacing:0.08em; margin-bottom:24px;
    display:flex; align-items:center; gap:8px;
}}
.insight-panel {{
    background:rgba(0,255,209,0.02); border:1px solid rgba(0,255,209,0.1);
    border-radius:16px; padding:26px 28px; margin-top:24px;
    position:relative; overflow:hidden;
}}
.insight-panel::before {{
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:linear-gradient(90deg, {CYAN}, {PURPLE}, {CYAN});
}}
.history-item {{
    background:{CARD_BG}; border:1px solid {BORDER}; border-radius:10px;
    padding:12px 16px; margin-bottom:8px; cursor:pointer;
    transition:all 0.2s ease;
}}
.history-item:hover {{
    border-color:rgba(0,255,209,0.2); background:rgba(0,255,209,0.03);
}}
.export-btn-wrap {{
    background:{CARD_BG}; border:1px solid {BORDER}; border-radius:14px;
    padding:20px; margin-top:16px;
}}
.tag-live {{
    background:{CYAN}; color:#000; padding:3px 12px; border-radius:30px;
    font-size:0.7rem; font-weight:800; letter-spacing:0.05em;
    animation: pulse-glow 2s ease-in-out infinite;
}}
@keyframes pulse-glow {{
    0%, 100% {{ box-shadow: 0 0 8px rgba(0,255,209,0.3); }}
    50% {{ box-shadow: 0 0 20px rgba(0,255,209,0.6); }}
}}
.divider {{
    height:1px; background:linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
    margin:20px 0;
}}
</style>
"""


# ──────────────────────────────────────────────
# Main Render Function
# ──────────────────────────────────────────────
def render():
    st.markdown(PAGE_CSS, unsafe_allow_html=True)

    # ── Hero Header ──
    st.markdown(f'''
    <div class="sim-hero">
        <div class="sim-hero-title">
            What-If Simulator
            <span class="tag-live">LIVE API ENGINE</span>
        </div>
        <div class="sim-hero-sub">
            Simulate fairness impact of AI decisions in real-time.
            Adjust parameters and watch bias metrics respond instantly.
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # ── Session State Init ──
    if "auto_run" not in st.session_state:
        st.session_state["auto_run"] = False
        
    home_input = st.session_state.get("simulation_input", None)
    auto_run = st.session_state.get("auto_run", False)

    if "history" not in st.session_state:
        st.session_state.history = []
    if "sim_results" not in st.session_state:
        st.session_state.sim_results = None
    if "sim_input" not in st.session_state:
        st.session_state.sim_input = None
    if "sim_report" not in st.session_state:
        st.session_state.sim_report = None

    # ── Two Column Layout ──
    input_col, dash_col = st.columns([1, 1.7], gap="large")

    # ═══════════════════════════════════════════
    # LEFT: Control Panel
    # ═══════════════════════════════════════════
    with input_col:
        st.markdown('<div class="panel-label">⚙️ Control Panel</div>', unsafe_allow_html=True)

        home_state = st.session_state.get("simulation_input", {})
        
        gender = st.selectbox("👤 Who are you?", ["Male", "Female"], index=["Male", "Female"].index(home_state.get("gender", "Male")))
        job = st.selectbox("💼 Work Type", ["Private Job", "Self-Employed", "Student", "Unemployed"], index=["Private Job", "Self-Employed", "Student", "Unemployed"].index(home_state.get("job", "Private Job")))
        age = st.slider("🎂 Age Group", 18, 65, int(home_state.get("age", 25)))
        education = st.selectbox("🎓 Education", ["School", "Graduate", "Postgraduate"], index=["School", "Graduate", "Postgraduate"].index(home_state.get("education", "School")))
        income = st.selectbox("💰 Income Category", ["Low Income", "Middle Income", "High Income"], index=["Low Income", "Middle Income", "High Income"].index(home_state.get("income", "Low Income")))
        credit = st.slider("🏦 Loan Requirement", 1000, 1000000, int(home_state.get("credit", 50000)))

        model_type = st.selectbox(
            "Select ML model",
            options=[
                "XGBoost Classifier (Production)",
                "XGBoost Classifier (V1)",
                "Fair Model (Mitigated)",
            ],
            index=0,
            help="Choose which trained model to run simulation against"
        )

        mitigation_toggle = st.toggle("Apply Bias Mitigation", value=False)
        input_data = {
            "gender": gender,
            "age": age,
            "income": income,
            "job": job,
            "education": education,
            "credit": credit
        }

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # Run button
        run_clicked = st.button(
            "🚀  Run Simulation",
            use_container_width=True,
            type="primary",
        )

        if run_clicked:
            st.session_state.firebase_logged = False
            # Sync inputs back to home so changes here reflect on the home page too
            st.session_state["simulation_input"] = input_data
            
            payload = {
                "domain": "lending",
                "features": transform_input(input_data),
                "apply_mitigation": mitigation_toggle
            }
            
            with st.expander("Debug API (Request)"):
                st.json(payload)

            with st.spinner("Running AI fairness audit..."):
                resp = cached_run(_make_hashable(payload), payload)
                report_resp = get_fairness_report()
                
                if not resp["ok"]:
                    st.error(f"🔴 API Error ({resp.get('status')}):")
                    st.code(resp.get("error"))
                    st.session_state.sim_results = {"error": resp.get("error")}
                else:
                    # Parse the raw API response into a normalised flat dict
                    parsed = parse_audit_response(resp["data"])
                    
                    if report_resp["ok"]:
                        st.session_state.sim_report = report_resp["data"]
                    else:
                        st.session_state.sim_report = {"error": report_resp.get("error", "Unknown report error")}
                    
                    # Store previous result before overwriting
                    if st.session_state.sim_results and "error" not in st.session_state.sim_results:
                        st.session_state["previous_result"] = st.session_state.sim_results.copy()
                        
                    st.session_state.sim_results = parsed
                    
                    user = st.session_state.get("user")
                    user_email = user.get("email", "guest") if user else "guest"
                    
                    try:
                        fairness_score = float(parsed.get("fairness_score", 0))
                    except (ValueError, TypeError):
                        fairness_score = 0.0
                        
                    try:
                        bias_gap = float(parsed.get("bias", 0))
                    except (ValueError, TypeError):
                        bias_gap = 0.0
                        
                    disparate_impact = fairness_score / 100.0 if fairness_score else 0.0
                    risk_level = str(parsed.get("risk", "Unknown"))
                    
                    st.session_state.sim_input = payload
                    
                    # Store result locally for dashboard (fairness_score is now a top-level key)
                    combined_result = {
                        "fairness": {
                            "score": parsed.get("fairness_score", 0)
                        },
                        "probability": parsed.get("probability", 0),
                        "prediction": parsed.get("prediction", "N/A"),
                        "bias": parsed.get("bias", 0),
                        "risk": parsed.get("risk", "Unknown"),
                        "accuracy": parsed.get("accuracy", 0),
                        "report": st.session_state.sim_report
                    }
                    st.session_state["last_result"] = combined_result
                    try:
                        with open("last_result.json", "w") as f:
                            json.dump(combined_result, f)
                    except Exception:
                        pass
                    
                    # Save to history
                    run_id = f"Run {len(st.session_state.history) + 1}"
                    st.session_state.history.append({
                        "run_id": run_id,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "ui_inputs": input_data.copy(),
                        "inputs": payload.copy(),
                        "results": parsed.copy(),
                        "raw_response": resp["data"],
                        "report": st.session_state.sim_report
                    })
                    
                    st.rerun()

        # ── Auto Run Block ──
        if home_input and auto_run:
            st.session_state.firebase_logged = False
            st.info("⚡ Running simulation from Home input...")
            
            try:
                features = transform_input(home_input)
                
                payload = {
                    "domain": "lending",
                    "features": features,
                    "apply_mitigation": False
                }
                
                resp = cached_run(_make_hashable(payload), payload)
                report_resp = get_fairness_report()
                
                if resp["ok"]:
                    result = parse_audit_response(resp["data"])
                    st.session_state["sim_results"] = result
                    
                    user = st.session_state.get("user")
                    user_email = user.get("email", "guest") if user else "guest"
                    
                    try:
                        fairness_score = float(result.get("fairness_score", 0))
                    except (ValueError, TypeError):
                        fairness_score = 0.0
                        
                    try:
                        bias_gap = float(result.get("bias", 0))
                    except (ValueError, TypeError):
                        bias_gap = 0.0
                        
                    disparate_impact = fairness_score / 100.0 if fairness_score else 0.0
                    risk_level = str(result.get("risk", "Unknown"))
                    
                    st.session_state["sim_input"] = payload
                    if report_resp["ok"]:
                        st.session_state.sim_report = report_resp["data"]
                    else:
                        st.session_state.sim_report = {"error": report_resp.get("error", "Unknown report error")}
                else:
                    raise Exception(resp.get("error"))
                    
            except Exception as e:
                st.error("API Error")
                st.write(str(e))
                
            # PREVENT LOOP
            st.session_state["auto_run"] = False
            
        result = st.session_state.get("sim_results", None)
        if result and not "error" in result:
            st.success("✅ Simulation Completed")

            # --- FIREBASE LOGGING TRIGGER BLOCK ---
            if "firebase_logged" not in st.session_state:
                st.session_state.firebase_logged = False

            if not st.session_state.firebase_logged:
                user = st.session_state.get("user")
                user_email = user.get("email", "guest") if user else "guest"
                
                try:
                    fairness_score = float(result.get("fairness_score", 0))
                except (ValueError, TypeError):
                    fairness_score = 0.0
                    
                try:
                    bias_gap = float(result.get("bias", 0))
                except (ValueError, TypeError):
                    bias_gap = 0.0
                    
                disparate_impact = fairness_score / 100.0 if fairness_score else 0.0
                risk_level = str(result.get("risk", "Unknown"))

                from firebase_admin import firestore

                data = {
                    "user_id": user_email,
                    "fairness_score": fairness_score,
                    "bias_gap": bias_gap,
                    "disparate_impact": disparate_impact,
                    "risk_level": risk_level,
                    "timestamp": firestore.SERVER_TIMESTAMP
                }

                try:
                    from utils.firebase_logger import log_simulation
                    log_simulation(data)
                    st.session_state.firebase_logged = True
                    print("✅ Firebase log inserted")
                except Exception as e:
                    print("❌ Firebase logging failed:", e)
            # --- END FIREBASE LOGGING TRIGGER BLOCK ---

        # ── History Panel ──
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        if st.session_state.history:
            with st.expander(f"📜 Simulation History ({len(st.session_state.history)} runs)", expanded=False):
                # Reverse history for display
                for entry in reversed(st.session_state.history):
                    r = entry["results"]
                    risk = r.get("risk", "Unknown") or "Unknown"
                    fairness = r.get("fairness_score") or 0
                    ui = entry.get("ui_inputs", {})
                    gender_pct = ui.get("gender_ratio", "--")
                    risk_color = {
                        "Low": CYAN, "Medium": YELLOW, "High": RED
                    }.get(risk, "#999")

                    st.markdown(f'''
                    <div class="history-item">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="color:rgba(255,255,255,0.6); font-size:0.78rem; font-weight:600;">
                                {entry["run_id"]} — {entry["timestamp"]}
                            </span>
                            <span style="color:{risk_color}; font-size:0.72rem; font-weight:700;">
                                {risk} Risk
                            </span>
                        </div>
                        <div style="color:rgba(255,255,255,0.35); font-size:0.7rem; margin-top:4px;">
                            Fairness: {fairness}% | Gender: {gender_pct}% F
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)

                    if st.button(f"↩ Load {entry['run_id']}", key=f"load_{entry['run_id']}", use_container_width=True):
                        st.session_state.sim_results = entry["results"]
                        st.session_state.sim_input = entry["inputs"]
                        st.session_state.sim_report = entry.get("report")
                        st.rerun()

    # ═══════════════════════════════════════════
    # RIGHT: Intelligence Dashboard
    # ═══════════════════════════════════════════
    with dash_col:
        # API Status Header
        header_col1, header_col2 = st.columns([1, 1])
        with header_col1:
            st.markdown('<div class="panel-label">📊 Intelligence Dashboard</div>', unsafe_allow_html=True)
        
        results = st.session_state.sim_results
        report = st.session_state.sim_report
        
        with header_col2:
            if results and "error" not in results:
                st.markdown(f'''
                <div style="text-align:right; margin-bottom:24px;">
                    <span style="background:rgba(0,255,209,0.1); color:{CYAN}; padding:6px 12px; border-radius:20px; font-size:0.75rem; font-weight:700; border:1px solid {CYAN}40;">
                        🟢 API ONLINE
                    </span>
                </div>
                ''', unsafe_allow_html=True)
            elif results and "error" in results:
                st.markdown(f'''
                <div style="text-align:right; margin-bottom:24px;">
                    <span style="background:rgba(255,80,80,0.1); color:{RED}; padding:6px 12px; border-radius:20px; font-size:0.75rem; font-weight:700; border:1px solid {RED}40;">
                        🔴 API ERROR
                    </span>
                </div>
                ''', unsafe_allow_html=True)

        if results is None or "error" in results:
            # ── Placeholder State ──
            placeholder_msg = "Run simulation to see AI fairness interpretation."
            if results and "error" in results:
                placeholder_msg = f"⚠️ {results['error']}"

            g1, g2 = st.columns(2)
            with g1:
                st.plotly_chart(_gauge(0, "Fairness"), use_container_width=True, key="g_f_ph")
            with g2:
                st.plotly_chart(_gauge(0, "Approval Prob."), use_container_width=True, key="g_a_ph")

            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(_metric_tile("Prediction", "--", "✅"), unsafe_allow_html=True)
            with m2:
                st.markdown(_metric_tile("Fairness", "--", "⚖️", "#999"), unsafe_allow_html=True)
            with m3:
                st.markdown(_metric_tile("Risk Level", _risk_badge("Unknown"), "🛡️", "#666"),
                            unsafe_allow_html=True)

            st.markdown(f'''
            <div class="insight-panel">
                <div style="color:rgba(255,255,255,0.6); font-weight:700; margin-bottom:8px;
                            display:flex; align-items:center; gap:8px;">
                    🤖 AI Insights
                </div>
                <div style="color:rgba(255,255,255,0.35); font-size:0.9rem; font-style:italic;">
                    {placeholder_msg}
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            if results and "error" in results:
                with st.expander("Debug Details"):
                    st.write(results)
            st.info("👆 Start a simulation from Home page or use the Control Panel")
            return

        # ═══════════════════════════════════════
        # LIVE RESULTS
        # ═══════════════════════════════════════

        fairness = float(results.get("fairness_score") or 0) if isinstance(results, dict) else 0.0
        probability = float(results.get("probability") or 0) if isinstance(results, dict) else 0.0
        prob_pct = round(probability * 100, 1)
        bias = float(results.get("bias") or 0) if isinstance(results, dict) else 0.0
        risk = str(results.get("risk") or "Unknown") if isinstance(results, dict) else "Unknown"
        prediction = results.get("prediction", "N/A") if isinstance(results, dict) else "N/A"
        confidence = results.get("confidence", "N/A") if isinstance(results, dict) else "N/A"
        badge = results.get("fairness_badge", "") if isinstance(results, dict) else ""

        # Determine colors
        f_color = CYAN if fairness > 80 else (YELLOW if fairness > 60 else RED)
        p_color = CYAN if prob_pct > 60 else (YELLOW if prob_pct > 40 else RED)
        b_color = CYAN if bias < 0.05 else (YELLOW if bias < 0.15 else RED)
        pred_color = CYAN if prediction == "Approved" else RED

        # ── Top Row ──
        t1, t2, t3 = st.columns(3)
        with t1:
            st.plotly_chart(_gauge(fairness, "Fairness"), use_container_width=True, key="g_f")
        with t2:
            st.plotly_chart(_gauge(prob_pct, "Approval Prob."), use_container_width=True, key="g_a")
        with t3:
            st.markdown('<div style="height:45px;"></div>', unsafe_allow_html=True) # alignment spacer
            st.markdown(_metric_tile("Prediction", prediction, "✅", pred_color), unsafe_allow_html=True)

        # ── Second Row ──
        s1, s2 = st.columns(2)
        with s1:
            st.markdown(_metric_tile("Bias Gap", f"{bias:.4f}", "🎯", b_color), unsafe_allow_html=True)
        with s2:
            st.markdown(_metric_tile("Risk Level", _risk_badge(risk), "🛡️"), unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(generate_ai_insight(results))
        
        if st.session_state.get("previous_result") and st.session_state.get("previous_result") != results:
            if st.button("📊 Compare with Previous", use_container_width=True):
                st.session_state["show_compare_modal"] = True
                
        if st.session_state.get("show_compare_modal", False):
            prev = st.session_state.get("previous_result", {})
            curr = results
            st.markdown(f'''
            <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:12px; padding:16px; margin-top:10px;">
                <h4 style="color:#fff; margin-bottom:10px;">📉 Run Comparison</h4>
                <div style="display:flex; justify-content:space-between;">
                    <div style="color:rgba(255,255,255,0.6); font-size:0.9rem;">Previous Fairness: <b style="color:#FFD700;">{prev.get("fairness_score", 0)}%</b></div>
                    <div style="color:rgba(255,255,255,0.6); font-size:0.9rem;">Current Fairness: <b style="color:#00FFD1;">{curr.get("fairness_score", 0)}%</b></div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            if st.button("Close Comparison"):
                st.session_state["show_compare_modal"] = False
                st.rerun()

        # ── API Report Rendering ──
        if isinstance(report, dict) and "error" not in report:
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

            # Extract real report data
            baseline = report.get("baseline_model", {})
            fair = report.get("fair_model", {})
            improvement = report.get("improvement", {})
            constraint = report.get("constraint", "N/A")
            sensitive = report.get("sensitive_feature", "N/A")

            # ── Overview Card ──
            b_gap = baseline.get("selection_rate_gap", 0)
            f_gap = fair.get("selection_rate_gap", 0)
            gap_change = improvement.get("selection_rate_gap_change", 0)
            b_acc = baseline.get("accuracy", 0)
            f_acc = fair.get("accuracy", 0)
            acc_change = improvement.get("accuracy_change", 0)

            st.markdown(f'''
            <div style="background:{CARD_BG}; border:1px solid {BORDER}; border-radius:14px; padding:22px 24px; margin-bottom:16px;">
                <div style="font-size:0.78rem; color:{CYAN}; font-weight:800; text-transform:uppercase;
                            letter-spacing:0.08em; margin-bottom:18px;">📊 Fairness Report: Baseline vs Mitigated</div>
                <div style="display:flex; gap:20px; flex-wrap:wrap;">
                    <div style="flex:1; min-width:140px;">
                        <div style="color:rgba(255,255,255,0.4); font-size:0.72rem; text-transform:uppercase; margin-bottom:4px;">Constraint</div>
                        <div style="color:#fff; font-weight:700;">{constraint}</div>
                    </div>
                    <div style="flex:1; min-width:140px;">
                        <div style="color:rgba(255,255,255,0.4); font-size:0.72rem; text-transform:uppercase; margin-bottom:4px;">Sensitive Feature</div>
                        <div style="color:#fff; font-weight:700;">{sensitive}</div>
                    </div>
                    <div style="flex:1; min-width:140px;">
                        <div style="color:rgba(255,255,255,0.4); font-size:0.72rem; text-transform:uppercase; margin-bottom:4px;">Bias Gap Change</div>
                        <div style="color:{CYAN}; font-weight:800; font-size:1.1rem;">{gap_change:+.4f}</div>
                    </div>
                    <div style="flex:1; min-width:140px;">
                        <div style="color:rgba(255,255,255,0.4); font-size:0.72rem; text-transform:uppercase; margin-bottom:4px;">Accuracy Change</div>
                        <div style="color:{YELLOW}; font-weight:800; font-size:1.1rem;">{acc_change:+.4f}</div>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

            # ── Side-by-side Comparison ──
            st.markdown(f'''
            <div style="background:rgba(168,85,247,0.03); border:1px solid rgba(168,85,247,0.15); border-radius:14px; padding:22px 24px; margin-bottom:16px;">
                <div style="font-size:0.78rem; color:{PURPLE}; font-weight:800; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:14px;">
                    ✨ Model Comparison: Baseline → Fair
                </div>
                <div style="display:flex; gap:24px; flex-wrap:wrap;">
                    <div style="flex:1; min-width:200px; background:rgba(255,80,80,0.05); border:1px solid rgba(255,80,80,0.1); border-radius:10px; padding:16px;">
                        <div style="color:{RED}; font-weight:700; margin-bottom:10px; font-size:0.82rem;">🔴 Baseline Model</div>
                        <div style="color:rgba(255,255,255,0.6); font-size:0.8rem;">
                            Accuracy: <span style="color:#fff; font-weight:600;">{b_acc:.4f}</span><br>
                            ROC AUC: <span style="color:#fff; font-weight:600;">{baseline.get("roc_auc", 0):.4f}</span><br>
                            Selection Rate Gap: <span style="color:{RED}; font-weight:600;">{b_gap:.4f}</span><br>
                            TPR Gap: <span style="color:#fff; font-weight:600;">{baseline.get("tpr_gap", 0):.4f}</span>
                        </div>
                    </div>
                    <div style="flex:1; min-width:200px; background:rgba(0,255,209,0.03); border:1px solid rgba(0,255,209,0.1); border-radius:10px; padding:16px;">
                        <div style="color:{CYAN}; font-weight:700; margin-bottom:10px; font-size:0.82rem;">🟢 Fair Model (Mitigated)</div>
                        <div style="color:rgba(255,255,255,0.6); font-size:0.8rem;">
                            Accuracy: <span style="color:#fff; font-weight:600;">{f_acc:.4f}</span><br>
                            ROC AUC: <span style="color:#fff; font-weight:600;">{fair.get("roc_auc", 0):.4f}</span><br>
                            Selection Rate Gap: <span style="color:{CYAN}; font-weight:600;">{f_gap:.4f}</span><br>
                            TPR Gap: <span style="color:#fff; font-weight:600;">{fair.get("tpr_gap", 0):.4f}</span>
                        </div>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.warning("Fairness report could not be retrieved from the API.")

        # ── Export Section ──
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        pdf_bytes = generate_pdf_report(results, report, st.session_state.sim_input)
        st.download_button(
            label="📥 Download Comparison Report (PDF)",
            data=pdf_bytes,
            file_name=f"bias_comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        with st.expander("🐛 Debug API Response"):
            st.write("Results Payload:", results)
            st.write("Report Payload:", report)

    # ═══════════════════════════════════════════
    # FULL WIDTH: Baseline vs Fair Model Comparison
    # ═══════════════════════════════════════════
    if st.session_state.sim_input is not None:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown(f'''
        <div style="font-size:1.4rem; color:#fff; font-weight:800; margin-bottom:20px; text-align:center;">
            📊 Baseline vs Fair Model Comparison
        </div>
        <div style="text-align:center; color:rgba(255,255,255,0.4); font-size:0.85rem; margin-bottom:20px;">
            Compare how the same applicant is evaluated by the original model vs the bias-mitigated model.
        </div>
        ''', unsafe_allow_html=True)

        c1, c2 = st.columns([1, 1], gap="large")

        with c1:
            st.markdown(f'<div style="color:{CYAN}; font-weight:800; margin-bottom:12px; font-size:1.1rem;">🔍 Current Applicant Profile</div>', unsafe_allow_html=True)

            current_payload = st.session_state.sim_input
            with st.expander("View Payload Being Compared"):
                st.json(current_payload)

            if st.button("⚡ Compare Baseline vs Fair Model", use_container_width=True):
                with st.spinner("Calling /v1/audit/compare..."):
                    comp_resp = compare_runs(current_payload)
                    if comp_resp["ok"]:
                        st.session_state.compare_result = comp_resp["data"]
                    else:
                        st.session_state.compare_result = {"error": comp_resp.get("error", "Unknown error")}

        with c2:
            if "compare_result" in st.session_state:
                res = st.session_state.compare_result
                if "error" in res:
                    st.error("API Error during comparison")
                    st.code(res["error"])
                else:
                    st.markdown(f'<div style="color:{PURPLE}; font-weight:800; margin-bottom:12px; font-size:1.1rem;">✨ Comparison Results</div>', unsafe_allow_html=True)

                    # Render all returned keys dynamically
                    st.markdown(f'''
                    <div style="background:{CARD_BG}; border:1px solid {BORDER}; border-radius:14px; padding:20px;">
                    ''', unsafe_allow_html=True)

                    for key, val in res.items():
                        if isinstance(val, dict):
                            st.markdown(f'<div style="color:{CYAN}; font-weight:700; margin-top:8px;">{key}</div>', unsafe_allow_html=True)
                            for k2, v2 in val.items():
                                st.markdown(f'<div style="color:rgba(255,255,255,0.5); font-size:0.82rem; margin-left:12px;">{k2}: <span style="color:#fff; font-weight:600;">{v2}</span></div>', unsafe_allow_html=True)
                        else:
                            display_color = CYAN if "fair" in str(key).lower() else YELLOW
                            st.markdown(f'''
                            <div style="margin-bottom:10px;">
                                <span style="color:rgba(255,255,255,0.5); font-size:0.85rem; text-transform:uppercase;">{key}</span><br>
                                <span style="color:{display_color}; font-size:1.2rem; font-weight:800;">{val}</span>
                            </div>
                            ''', unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)

                    with st.expander("Raw Comparison JSON"):
                        st.json(res)

                    comp_pdf_bytes = generate_pdf_report(
                        results=results,
                        report=report,
                        input_payload=current_payload,
                        comparison=res
                    )
                    st.download_button(
                        label="📥 Download Comparison Report (PDF)",
                        data=comp_pdf_bytes,
                        file_name="comparison_result.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

