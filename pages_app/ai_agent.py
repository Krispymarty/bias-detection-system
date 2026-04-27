"""
FairSight AI — AI Agent Page
Chat interface with message bubbles, suggested prompts, and typing animation.
"""
import streamlit as st
import time
from utils.mock_data import get_ai_responses


def render():
    st.markdown(
        """
        <div style="margin-bottom:1.5rem;">
            <h1 style="font-size:1.8rem;font-weight:700;color:white;margin-bottom:0.3rem;">
                🤖 AI Agent
            </h1>
            <p style="color:rgba(255,255,255,0.5);font-size:0.9rem;">
                Chat with our AI assistant about fairness, bias detection, and responsible AI
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Initialise chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! I'm FairSight AI's analytical assistant. 👋\n\n"
                    "I can help you understand algorithmic fairness, detect bias patterns, "
                    "and explore mitigation strategies. What would you like to know?"
                ),
            }
        ]

    # ── Suggested prompts (shown only before first user message) ──
    user_msgs = [m for m in st.session_state.chat_messages if m["role"] == "user"]
    if not user_msgs:
        st.markdown(
            '<p style="color:rgba(255,255,255,0.35);font-size:0.82rem;margin-bottom:0.5rem;">'
            "💡 Suggested prompts:</p>",
            unsafe_allow_html=True,
        )
        cols = st.columns(3)
        prompts = [
            "What is algorithmic fairness?",
            "How does bias detection work?",
            "Show me fairness metrics",
        ]
        for col, prompt_text in zip(cols, prompts):
            with col:
                if st.button(prompt_text, key=f"sp_{prompt_text}", use_container_width=True):
                    responses = get_ai_responses()
                    st.session_state.chat_messages.append({"role": "user", "content": prompt_text})
                    st.session_state.chat_messages.append(
                        {"role": "assistant", "content": responses.get(prompt_text, responses["default"])}
                    )
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

    # ── Chat history ──
    for msg in st.session_state.chat_messages:
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # ── Chat input ──
    if user_input := st.chat_input("Ask about AI fairness, bias detection, or metrics…"):
        # Display user message
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        # Generate and display assistant response with typing effect
        with st.chat_message("assistant", avatar="🤖"):
            responses = get_ai_responses()
            response = responses.get(user_input, responses["default"])

            placeholder = st.empty()
            displayed = ""
            for char in response:
                displayed += char
                placeholder.markdown(displayed + "▌")
                time.sleep(0.008)
            placeholder.markdown(displayed)

        st.session_state.chat_messages.append({"role": "assistant", "content": response})
