import streamlit as st
from main import agent_response

st.title("Calender event setiing assistent")



if "messages" not in st.session_state:
    st.session_state.messages = []

if "processed_inputs" not in st.session_state:
    st.session_state.processed_inputs = set()


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Set your reminder")

if user_input and user_input not in st.session_state.messages:
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Creating reminder..."):
            result = agent_response(user_input)
            st.markdown(result)

    st.session_state.messages.append({"role": "assistant", "content": result})

    st.session_state.processed_inputs.add(user_input)
