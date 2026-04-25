"""
FairSight AI — Tutorial Page
Step-by-step interactive guide with code snippets and architecture layout.
"""
import streamlit as st

def render_html(html_str):
    """Helper to prevent Streamlit from rendering HTML chunks as Markdown code blocks.
    It removes newlines so that no line has >= 4 spaces of indentation."""
    cleaned = html_str.replace('\n', '')
    st.markdown(cleaned, unsafe_allow_html=True)

def render():
    render_html(
        """
        <style>
        .hero-title {
            color: #ffffff; font-size: 3rem; font-weight: 800; line-height: 1.1; margin-bottom: 20px; padding-top: 20px;
        }
        .hero-title .teal-text { color: #00FFD1; }
        .hero-subtitle {
            color: #8b9bb4; font-size: 1.15rem; max-width: 700px; line-height: 1.6; margin-bottom: 60px;
        }
        
        .step-wrapper {
            position: relative;
            padding-left: 80px;
            margin-bottom: 50px;
        }
        .step-num {
            position: absolute;
            left: 0;
            top: -10px;
            font-size: 4rem;
            font-weight: 900;
            color: rgba(255, 255, 255, 0.05);
            line-height: 1;
            letter-spacing: -2px;
        }
        .step-card {
            background: #111827;
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 30px;
        }
        .step-header {
            display: flex; align-items: center; margin-bottom: 15px;
        }
        .step-icon {
            color: #00FFD1; font-size: 1.5rem; margin-right: 15px;
        }
        .step-title {
            color: #ffffff; font-size: 1.4rem; font-weight: 700;
        }
        .step-desc {
            color: #8b9bb4; font-size: 0.95rem; line-height: 1.6; margin-bottom: 25px;
        }
        
        /* Code Block Styling */
        .code-container {
            background: #0d121c;
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 8px;
            overflow: hidden;
        }
        .code-header {
            display: flex; justify-content: flex-end; padding: 5px 15px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 0.7rem; color: #6b7280; font-family: monospace; text-transform: uppercase;
        }
        .code-col { color: #8b9bb4; font-size: 0.85rem; padding: 15px; font-family: 'Courier New', Courier, monospace; line-height: 1.5; }
        .ky { color: #c678dd; } /* keyword */
        .fn { color: #61afef; } /* function */
        .st { color: #98c379; } /* string */
        .cm { color: #5c6370; font-style: italic; } /* comment */
        .op { color: #56b6c2; } /* operator/punctuation */
        
        /* Scan Results styling */
        .scan-res-container {
            background: #0d121c;
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 20px;
        }
        .scan-header {
            display: flex; justify-content: space-between; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 10px;
        }
        .scan-title { color: #a0aec0; font-size: 0.85rem; font-weight: 600; }
        .scan-status { color: #00FFD1; font-size: 0.7rem; font-weight: 700; letter-spacing: 1px; }
        .metric-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .metric-label { color: #8b9bb4; font-size: 0.85rem; }
        .metric-bar-bg { width: 150px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; display: inline-block; margin-right: 10px; vertical-align: middle; }
        .metric-bar-fill-high { height: 100%; width: 80%; background: #ff7676; border-radius: 3px; }
        .metric-bar-fill-low { height: 100%; width: 25%; background: #00FFD1; border-radius: 3px; }
        .metric-val { font-size: 0.75rem; font-weight: 700; display: inline-block; width: 40px; text-align: right; }
        .val-high { color: #ff7676; }
        .val-low { color: #00FFD1; }
        
        /* Right sidebar panels */
        .side-card {
            background: #111827;
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 12px;
            margin-bottom: 20px;
            overflow: hidden;
        }
        .video-box {
            height: 180px; position: relative; background: #070a12;
            display: flex; align-items: center; justify-content: center;
            overflow: hidden;
        }
        .video-waves {
            position: absolute; top:0; left:0; width:100%; height:100%; opacity: 0.2;
        }
        .play-btn {
            width: 50px; height: 50px; border-radius: 50%; border: 1px solid #00FFD1; color: #00FFD1;
            display: flex; align-items: center; justify-content: center; font-size: 1.2rem; cursor: pointer; z-index: 2;
            background: rgba(0,255,209,0.1);
        }
        .video-label {
            padding: 15px 20px; color: #00FFD1; font-size: 0.7rem; font-weight: 700; letter-spacing: 1px;
        }
        
        .prereq-card { padding: 25px; }
        .prereq-title { color: #fff; font-size: 1.05rem; font-weight: 700; margin-bottom: 20px; display: flex; align-items: center; }
        .prereq-title::before {
            content: ''; display: inline-block; width: 10px; height: 10px; background: #61afef; border-radius: 50%; margin-right: 10px;
        }
        .prereq-item { display: flex; margin-bottom: 15px; color: #a0aec0; font-size: 0.85rem; align-items: flex-start; }
        .prereq-icon { color: #00FFD1; margin-right: 10px; font-size: 1rem; line-height: 1.2; }
        
        .assist-card { padding: 30px 25px; text-align: center; }
        .assist-icon { color: #a0aec0; font-size: 1.6rem; margin-bottom: 15px; }
        .assist-title { color: #fff; font-size: 0.95rem; font-weight: 700; margin-bottom: 10px; }
        .assist-desc { color: #8b9bb4; font-size: 0.8rem; margin-bottom: 20px; }
        .btn-assist {
            display: block; border: 1px solid rgba(255,255,255,0.2); color: #fff; font-size: 0.85rem; font-weight: 600;
            padding: 10px; border-radius: 6px; text-decoration: none; transition: background 0.2s;
        }
        .btn-assist:hover { background: rgba(255,255,255,0.05); }

        .footer-wrap {
            margin-top: 50px; padding-top: 30px; border-top: 1px solid rgba(255,255,255,0.05);
            display: flex; justify-content: space-between; align-items: center; color: #6b7280; font-size: 0.75rem;
        }
        .footer-logo { color: #00FFD1; font-weight: 700; font-size: 1rem; }
        .footer-links { display: flex; gap: 20px; }
        .footer-links a { color: #6b7280; text-decoration: none; transition: color 0.2s; }
        .footer-links a:hover { color: #00FFD1; }
        </style>
        """
    )
    
    render_html(
        """
        <div class="hero-title">Mastering <span class="teal-text">Bias Mitigation.</span></div>
        <div class="hero-subtitle">
            A step-by-step technical guide to integrating FairSight AI's ethereal arbiter into your data pipelines for unprecedented algorithmic justice.
        </div>
        """
    )

    c1, c2 = st.columns([2.2, 1])
    
    with c1:
        render_html(
            """
            <div class="step-wrapper">
                <div class="step-num">01</div>
                <div class="step-card">
                    <div class="step-header">
                        <div class="step-icon">🗄️</div>
                        <div class="step-title">Data Ingestion Protocol</div>
                    </div>
                    <div class="step-desc">
                        Begin by connecting your primary data reservoirs. FairSight AI securely authenticates and streams data, identifying potential demographic or contextual anomalies at the source.
                    </div>
                    
                    <div class="code-container">
                        <div class="code-header">Python</div>
                        <div class="code-col">
                            <span class="ky">from</span> fairsight <span class="ky">import</span> EtherealArbiter<br><br>
                            <span class="cm"># Initialize the arbiter instance</span><br>
                            arbiter <span class="op">=</span> EtherealArbiter<span class="op">(</span>api_key<span class="op">=</span><span class="st">"YOUR_KEY"</span><span class="op">)</span><br><br>
                            <span class="cm"># Connect data reservoir</span><br>
                            reservoir <span class="op">=</span> arbiter<span class="op">.</span>connect<span class="op">(</span><br>
                            &nbsp;&nbsp;&nbsp;&nbsp;source<span class="op">=</span><span class="st">"aws_s3"</span>,<br>
                            &nbsp;&nbsp;&nbsp;&nbsp;uri<span class="op">=</span><span class="st">"s3://datalake-raw/users/"</span><br>
                            <span class="op">)</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="step-wrapper">
                <div class="step-num">02</div>
                <div class="step-card">
                    <div class="step-header">
                        <div class="step-icon">📊</div>
                        <div class="step-title">Bias Surface Mapping</div>
                    </div>
                    <div class="step-desc">
                        Execute the initial scan to generate a comprehensive bias topography report. The system flags historical prejudices embedded within feature matrices.
                    </div>
                    
                    <div class="scan-res-container">
                        <div class="scan-header">
                            <div class="scan-title">Scan Results</div>
                            <div class="scan-status">STATUS: COMPLETE</div>
                        </div>
                        <div class="metric-row">
                            <div class="metric-label">Gender Disparity Index</div>
                            <div>
                                <div class="metric-bar-bg"><div class="metric-bar-fill-high"></div></div>
                                <div class="metric-val val-high">HIGH</div>
                            </div>
                        </div>
                        <div class="metric-row">
                            <div class="metric-label">Age Representation</div>
                            <div>
                                <div class="metric-bar-bg"><div class="metric-bar-fill-low"></div></div>
                                <div class="metric-val val-low">LOW</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="step-wrapper">
                <div class="step-num">03</div>
                <div class="step-card">
                    <div class="step-header">
                        <div class="step-icon">⑂</div>
                        <div class="step-title">Algorithmic Mediation</div>
                    </div>
                    <div class="step-desc">
                        Apply mediation weights to rebalance the dataset. The arbiter continuously monitors drift, ensuring fairness metrics remain within acceptable thresholds during model training.
                    </div>
                </div>
            </div>
            """
        )

    with c2:
        # Top piece: A video placeholder container.
        render_html(
            """
            <div class="side-card">
                <div class="video-box">
                    <svg class="video-waves" viewBox="0 0 200 100" preserveAspectRatio="none">
                        <path fill="none" stroke="rgba(255,255,255,0.7)" stroke-width="0.3" d="M0,50 Q25,30 50,50 T100,50 T150,50 T200,50" />
                        <path fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="0.3" d="M0,40 Q25,60 50,40 T100,40 T150,40 T200,40" />
                        <path fill="none" stroke="rgba(0,255,209,0.5)" stroke-width="0.3" d="M0,60 Q25,40 50,60 T100,60 T150,60 T200,60" />
                        <path fill="none" stroke="rgba(255,255,255,0.6)" stroke-width="0.3" d="M0,45 Q25,65 50,45 T100,45 T150,45 T200,45" />
                        <path fill="none" stroke="rgba(0,255,209,0.3)" stroke-width="0.3" d="M0,55 Q25,35 50,55 T100,55 T150,55 T200,55" />
                    </svg>
                    <div class="play-btn">▶</div>
                </div>
                <div class="video-label">WATCH_DEMO.MP4</div>
            </div>
            """
        )

        # Middle piece: "Prerequisites" card.
        render_html(
            """
            <div class="side-card prereq-card">
                <div class="prereq-title">Prerequisites</div>
                <div class="prereq-item"><div class="prereq-icon">✔</div><div>Python 3.9+ Environment</div></div>
                <div class="prereq-item"><div class="prereq-icon">✔</div><div>Valid FairSight API Key</div></div>
                <div class="prereq-item"><div class="prereq-icon">✔</div><div>Access to standardized CSV/JSON datasets</div></div>
            </div>
            """
        )

        # Bottom piece: "Need Technical Assistance?" card.
        render_html(
            """
            <div class="side-card assist-card">
                <div class="assist-icon">🎧</div>
                <div class="assist-title">Need Technical Assistance?</div>
                <div class="assist-desc">Our engineers are available for architecture reviews.</div>
                <a href="#" class="btn-assist">Contact Support</a>
            </div>
            """
        )

    # Footer
    render_html(
        """
        <div class="footer-wrap">
            <div class="footer-logo">FairSight AI</div>
            <div style="flex-grow:1; text-align:center;">© 2024 FairSight AI. The Ethereal Arbiter of Data Justice.</div>
            <div class="footer-links">
                <a href="#">Privacy Policy</a>
                <a href="#">Terms of Service</a>
                <a href="#">API Docs</a>
                <a href="#">Community</a>
            </div>
        </div>
        """
    )
