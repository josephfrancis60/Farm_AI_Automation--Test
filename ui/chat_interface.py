import streamlit as st
from datetime import datetime
from agents.run_agent import run_agent

def start_ui():
    st.title("Farm AI Agent 🌱")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "time" in message:
                st.markdown(f"{message['content']} <div style='text-align: right; color: gray; font-size: 0.8em;'>{message['time']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about your farm..."):
        now = datetime.now().strftime("%I:%M %p")
        
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt, "time": now})
        with st.chat_message("user"):
            st.markdown(f"{prompt} <div style='text-align: right; color: gray; font-size: 0.8em;'>{now}</div>", unsafe_allow_html=True)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = run_agent(prompt)
                resp_time = datetime.now().strftime("%I:%M %p")
                st.markdown(f"{response} <div style='text-align: right; color: gray; font-size: 0.8em;'>{resp_time}</div>", unsafe_allow_html=True)
        
        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response, "time": resp_time})