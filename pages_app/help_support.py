"""
FairSight AI — Help & Support Page
Search bar, FAQ accordion, contact form, and support links.
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
        .help-hero {
            text-align: center;
            padding: 40px 0;
        }
        .help-title {
            color: #ffffff;
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 25px;
        }
        .help-title-teal {
            color: #00FFD1;
        }
        
        .search-container {
            max-width: 650px;
            margin: 0 auto;
            position: relative;
        }
        .search-input {
            width: 100%;
            padding: 15px 25px;
            border-radius: 8px;
            border: none;
            font-size: 1rem;
            background: #ffffff;
            color: #000;
            outline: none;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }
        .search-btn {
            position: absolute;
            right: 15px;
            top: 50%;
            transform: translateY(-50%);
            background: #00FFD1;
            color: #000;
            border: none;
            width: 35px;
            height: 35px;
            border-radius: 4px;
            font-size: 1.1rem;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,255,209,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s;
        }
        .search-btn:hover { transform: translateY(-50%) scale(1.05); }
        
        .quick-link-card {
            background: #0d121c;
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 25px;
            height: 100%;
            transition: all 0.3s;
            margin-bottom: 20px;
        }
        .quick-link-card:hover {
            transform: translateY(-5px);
            border-color: rgba(0,255,209,0.2);
            box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        }
        .ql-icon {
            color: #00FFD1;
            font-size: 1.5rem;
            margin-bottom: 15px;
        }
        .ql-title { color: #ffffff; font-size: 1rem; font-weight: 700; margin-bottom: 10px; }
        .ql-desc { color: #8b9bb4; font-size: 0.8rem; line-height: 1.5; margin-bottom: 20px; }
        .ql-link { color: #00FFD1; font-size: 0.8rem; font-weight: 700; text-decoration: none; display: inline-block;}
        
        .kb-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            margin-bottom: 20px;
            margin-top: 50px;
        }
        .kb-sup { color: #00FFD1; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
        .kb-title { color: #ffffff; font-size: 1.6rem; font-weight: 800; }
        .kb-browse { color: #8b9bb4; font-size: 0.85rem; font-weight: 600; text-decoration: none; transition: color 0.2s;}
        .kb-browse:hover { color: #00FFD1; }
        
        .topic-card {
            background: #111827;
            border: 1px solid rgba(255,255,255,0.05);
            border-left: 3px solid #00FFD1;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
            transition: all 0.3s;
            cursor: pointer;
        }
        .topic-card:hover { background: #161b2e; border-color: rgba(0,255,209,0.2); }
        .topic-title { color: #ffffff; font-size: 1rem; font-weight: 700; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;}
        .topic-badge { background: rgba(0,255,209,0.1); color: #00FFD1; padding: 3px 8px; border-radius: 4px; font-size: 0.65rem; font-weight: 700; margin-left: 10px;}
        .topic-desc { color: #8b9bb4; font-size: 0.85rem; line-height: 1.5; margin-bottom: 20px; }
        .topic-link { color: #00FFD1; font-size: 0.85rem; font-weight: 700; text-decoration: none; }
        
        .chat-card {
            background: linear-gradient(180deg, #161b2e 0%, #111827 100%);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 40px 30px;
            text-align: center;
            height: 100%;
        }
        .chat-icon-wrap {
            width: 80px; height: 80px; background: #00FFD1; border-radius: 20px; margin: 0 auto 25px;
            display: flex; align-items: center; justify-content: center; position: relative;
            box-shadow: 0 10px 20px rgba(0,255,209,0.2);
        }
        .chat-icon { font-size: 2.2rem; }
        @keyframes pulse-badge {
            0% { box-shadow: 0 0 0 0 rgba(0,255,209,0.4); }
            70% { box-shadow: 0 0 0 10px rgba(0,255,209,0); }
            100% { box-shadow: 0 0 0 0 rgba(0,255,209,0); }
        }
        .online-badge {
            position: absolute; top: -10px; right: -10px; background: #111827; color: #00FFD1; border: 1px solid #00FFD1;
            padding: 3px 8px; border-radius: 12px; font-size: 0.65rem; font-weight: 800; text-transform: uppercase;
            animation: pulse-badge 2s infinite;
        }
        .chat-title { color: #ffffff; font-size: 1.3rem; font-weight: 700; margin-bottom: 15px; }
        .chat-desc { color: #8b9bb4; font-size: 0.85rem; line-height: 1.6; margin-bottom: 30px; }
        .btn-live { background: #00FFD1; color: #000; padding: 12px 0; border: none; border-radius: 6px; width: 100%;
            font-weight: 700; font-size: 0.9rem; cursor: pointer; display: block; text-decoration: none; box-shadow: 0 5px 15px rgba(0,255,209,0.3); transition: transform 0.2s;}
        .btn-live:hover { transform: translateY(-3px); }
        .chat-meta { color: rgba(255,255,255,0.3); font-size: 0.7rem; margin-top: 15px; text-transform: uppercase; font-weight: 700; }
        
        .contact-box { padding-top: 5px; }
        .c-title { color: #ffffff; font-size: 1.3rem; font-weight: 700; margin-bottom: 10px; }
        .c-desc { color: #8b9bb4; font-size: 0.85rem; margin-bottom: 30px; }
        
        .faq-sect-title { text-align: center; color: #ffffff; font-size: 1.6rem; font-weight: 800; margin: 60px 0 20px; }
        .faq-tags { display: flex; justify-content: center; gap: 10px; margin-bottom: 40px; }
        .faq-tag { background: rgba(0,255,209,0.1); color: #00FFD1; border: 1px solid rgba(0,255,209,0.2); padding: 5px 15px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; cursor: pointer; transition: background 0.2s; text-transform: uppercase; }
        .faq-tag:hover, .faq-tag.active { background: rgba(0,255,209,0.2); }
        
        .faq-details { background: #111827; border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 12px; overflow: hidden; transition: all 0.3s; }
        .faq-summary { padding: 20px; color: #ffffff; font-size: 0.95rem; font-weight: 600; cursor: pointer; list-style: none; display: flex; justify-content: space-between; align-items: center; }
        .faq-summary::-webkit-details-marker { display: none; }
        .faq-summary::after { content: "▼"; font-size: 0.7rem; color: #8b9bb4; transition: transform 0.2s; }
        .faq-details[open] .faq-summary::after { transform: rotate(180deg); color: #00FFD1; }
        .faq-details[open] .faq-summary { color: #00FFD1; border-bottom: 1px solid rgba(255,255,255,0.05); background: #161b2e; }
        .faq-details[open] { border-color: rgba(0,255,209,0.2); box-shadow: 0 0 15px rgba(0,255,209,0.05); }
        .faq-body { padding: 20px; color: #8b9bb4; font-size: 0.85rem; line-height: 1.6; background: #0d121c; }
        </style>
        """
    )
    
    # Hero & Search
    render_html(
        """
        <div class="help-hero">
            <div class="help-title">How can we <span class="help-title-teal">help you?</span></div>
            <div class="search-container">
                <input type="text" class="search-input" placeholder="Search for documentation, tutorials, or system logs..." />
                <button class="search-btn">🔍</button>
            </div>
        </div>
        """
    )
    
    # Quick Links Row
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        render_html(
            """
            <div class="quick-link-card">
                <div class="ql-icon">📖</div>
                <div class="ql-title">Documentation</div>
                <div class="ql-desc">Full technical specs and fairness protocol guides.</div>
                <a href="#" class="ql-link">Explore docs ↗</a>
            </div>
            """
        )
    with q2:
        render_html(
            """
            <div class="quick-link-card">
                <div class="ql-icon">▶️</div>
                <div class="ql-title">Video Tutorials</div>
                <div class="ql-desc">Guided walkthroughs of the Arbiter AI environment.</div>
                <a href="#" class="ql-link">Watch now ↗</a>
            </div>
            """
        )
    with q3:
        render_html(
            """
            <div class="quick-link-card">
                <div class="ql-icon">💬</div>
                <div class="ql-title">Live Chat</div>
                <div class="ql-desc">Instant access to our fairness engineering team.</div>
                <a href="#" class="ql-link">Connect live ↗</a>
            </div>
            """
        )
    with q4:
        render_html(
            """
            <div class="quick-link-card">
                <div class="ql-icon">🪲</div>
                <div class="ql-title">Report a Bug</div>
                <div class="ql-desc">Found an anomaly? Let us audit the logic.</div>
                <a href="#" class="ql-link">Submit report ↗</a>
            </div>
            """
        )

    # Popular Topics
    render_html(
        """
        <div class="kb-header">
            <div>
                <div class="kb-sup">Knowledge Base</div>
                <div class="kb-title">Popular Topics</div>
            </div>
            <a href="#" class="kb-browse">Browse All Categories</a>
        </div>
        """
    )
    
    t1, t2 = st.columns(2)
    with t1:
        render_html(
            """
            <div class="topic-card">
                <div class="topic-title">Understanding Dataset Parity Metrics <span class="topic-badge">ALL SYSTEMS OPERATIONAL</span></div>
                <div class="topic-desc">Learn how the Arbiter AI calculates the delta between dataset parity and model performance metrics.</div>
                <a href="#" class="topic-link">View Article ↗</a>
            </div>
            <div class="topic-card">
                <div class="topic-title">Regulatory Compliance Automations</div>
                <div class="topic-desc">Setting up recurring fairness reports for GDPR and EU AI Act adherence.</div>
                <a href="#" class="topic-link">View Article ↗</a>
            </div>
            """
        )
    with t2:
         render_html(
            """
            <div class="topic-card" style="border-left-color: rgba(255,255,255,0.1);">
                <div class="topic-title">Secure Tunneling for On-Prem Audit <span style="background:rgba(255,255,255,0.05); color:#a0aec0;" class="topic-badge">PROTOCOL VERSION 4.2.8 / SYN: 99% <span style="color:#00FFD1; margin-left:5px;">Detailed Notes ↗</span></span></div>
                <div class="topic-desc">A deep dive into our secure tunneling protocol for on-premise dataset auditing.</div>
                <a href="#" class="topic-link">View Article ↗</a>
            </div>
            <div class="topic-card">
                <div class="topic-title">User Management & Role Permissions</div>
                <div class="topic-desc">Managing access levels for data scientists, auditors, and executive stakeholders.</div>
                <a href="#" class="topic-link">View Article ↗</a>
            </div>
            """
        )
         
    st.markdown("<br><br>", unsafe_allow_html=True)
         
    # Contact Row
    c1, c2 = st.columns([1, 1.3])
    with c1:
        render_html(
            """
            <div class="chat-card">
                <div class="chat-icon-wrap">
                    <div class="online-badge">● ONLINE NOW</div>
                    <div class="chat-icon">💬</div>
                </div>
                <div class="chat-title">Direct Access</div>
                <div class="chat-desc">Chat directly with our system engineers for immediate technical resolution.</div>
                <a href="#" class="btn-live">Start Live Chat</a>
                <div class="chat-meta">TYPICAL RESPONSE: < 2 MINUTES</div>
            </div>
            """
        )
    with c2:
        render_html(
            """
            <div style="padding-left:10px;">
                <div class="c-title">Send a Message</div>
                <div class="c-desc">Prefer email? Our specialists will review your case within 24 hours.</div>
                
                <div style="display:flex; justify-content:space-between; margin-bottom:15px; gap:15px;">
                    <div style="flex-grow:1;">
                        <div style="color:#a0aec0; font-size:0.7rem; font-weight:700; margin-bottom:8px; text-transform:uppercase; letter-spacing:1px;">Subject</div>
                        <input type="text" placeholder="Audit error help" style="width:100%; padding:14px 15px; background:#0d121c; border:1px solid rgba(255,255,255,0.1); border-radius:6px; color:#fff; outline:none; font-family:inherit;" />
                    </div>
                    <div style="flex-grow:1;">
                        <div style="color:#a0aec0; font-size:0.7rem; font-weight:700; margin-bottom:8px; text-transform:uppercase; letter-spacing:1px;">Category</div>
                        <select style="width:100%; padding:14px 15px; background:#0d121c; border:1px solid rgba(255,255,255,0.1); border-radius:6px; color:#fff; outline:none; font-family:inherit;">
                            <option>Technical Issue</option>
                            <option>Billing</option>
                            <option>General</option>
                        </select>
                    </div>
                </div>
                <div style="margin-bottom:20px;">
                    <div style="color:#a0aec0; font-size:0.7rem; font-weight:700; margin-bottom:8px; text-transform:uppercase; letter-spacing:1px;">Your Message</div>
                    <textarea placeholder="Describe the behavior you're seeing..." style="width:100%; padding:15px; background:#0d121c; border:1px solid rgba(255,255,255,0.1); border-radius:6px; color:#fff; outline:none; height:130px; font-family:inherit; resize:none;"></textarea>
                </div>
                <button style="width:100%; padding:14px; background:#00FFD1; color:#000; border:none; border-radius:6px; font-weight:700; cursor:pointer; font-size:0.9rem; transition:transform 0.2s;">Send Message</button>
            </div>
            """
        )

    # FAQ Section
    render_html(
        """
        <div class="faq-sect-title">Frequently Asked Questions</div>
        <div class="faq-tags">
            <div class="faq-tag">GENERAL</div>
            <div class="faq-tag">BILLING</div>
            <div class="faq-tag active">TECHNICAL</div>
        </div>
        
        <div style="max-width:800px; margin:0 auto; padding-bottom:50px;">
            <details class="faq-details">
                <summary class="faq-summary">How often are the fairness logs updated?</summary>
                <div class="faq-body">Fairness logs are generated in real-time as data streams through the Arbiter models. Full dashboard compilations occur hourly.</div>
            </details>
            <details class="faq-details">
                <summary class="faq-summary">Can I export compliance reports in PDF format?</summary>
                <div class="faq-body">Yes, all compliance reports can be downloaded in PDF, CSV, and HTML formats directly from your analytics export suite.</div>
            </details>
            <details class="faq-details" open>
                <summary class="faq-summary">Is my data encrypted during the audit process?</summary>
                <div class="faq-body">Yes, all data silos connected to the Arbiter AI are encrypted using AES-256 at rest and TLS 1.3 in transit. We use Zero-Knowledge Proofs (ZKPs) for many of our fairness calculations, ensuring your raw data never leaves your environment.</div>
            </details>
            <details class="faq-details">
                <summary class="faq-summary">How do I change my subscription tier?</summary>
                <div class="faq-body">Navigate to Settings > Account Configuration > Billing Details. From there, you can upgrade or downgrade your organizational tier.</div>
            </details>
            <details class="faq-details">
                <summary class="faq-summary">What AI models are currently supported for auditing?</summary>
                <div class="faq-body">We natively support all standard SKLearn tree-based models, logistic regression, and advanced neural networks deployed via custom PyTorch/TensorFlow endpoints.</div>
            </details>
            <details class="faq-details">
                <summary class="faq-summary">Can I set up custom bias thresholds?</summary>
                <div class="faq-body">Absolutely. You can edit systemic alerting parameter ranges securely inside the Settings tab.</div>
            </details>
        </div>
        """
    )
