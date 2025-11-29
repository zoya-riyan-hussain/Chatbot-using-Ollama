import streamlit as st
import ollama
import datetime
import json
import os

warm_beige = "#d7ccc8"
warm_brown = "#6d4c41"
taupe = "#a1887f"
pale_beige = "#efebe9"
dark_brown = "#4b3b2b"
off_white = "#f5f5f1"
moss_green = "#8d6e63"

st.markdown(f"""
    <style>
    .stApp {{
        background-color: {warm_beige};
        color: {dark_brown};
    }}
    .stSidebar {{
        background-color: {taupe};
        color: {off_white};
        padding: 20px;
    }}
    .stSidebar h1, .stSidebar h2, .stSidebar h3 {{
        color: {off_white};
    }}
    .stButton button {{
        background-color: {warm_brown};
        color: {off_white};
        border-radius: 8px;
        border: none;
        padding: 8px 16px;
    }}
    .stButton button:hover {{
        background-color: #5d4037;
    }}
    div.stSidebar button.css-yk16xz.egzxvld1 {{
        background-color: {warm_brown} !important;
        color: {off_white} !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
        margin-bottom: 8px !important;
        font-weight: bold !important;
        text-align: left !important;
        width: 100% !important;
    }}
    .stTextInput input {{
        border-radius: 8px;
        border: 1px solid {moss_green};
        background-color: {pale_beige};
        color: {dark_brown};
    }}
    div[data-testid="stFileUploader"] > label {{
        background-color: {pale_beige} !important;
        color: {dark_brown} !important;
        border-radius: 12px;
        border: 2px solid {warm_brown} !important;
        padding: 18px;
        margin-bottom: 10px;
    }}
    button{{
        background-color: {warm_brown} !important;
        color: {off_white} !important;
        border-radius: 8px !important;
        border: 2px solid {warm_brown} !important;
        font-weight: bold !important;
    }}
    .stChatMessageUser {{
        background-color: #e6d8cc;
        border-left: 5px solid {warm_brown};
        color: {dark_brown};
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }}
    .stChatMessageAssistant {{
        background-color: {off_white};
        border-left: 5px solid {moss_green};
        color: {dark_brown};
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }}
    </style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="💬 Llama3 Chatbot", layout="wide")
st.title("💬 Llama3 (Ollama 3.1) Chatbot")

if "conversations" not in st.session_state:
    st.session_state["conversations"] = {}
if "current_chat" not in st.session_state:
    st.session_state["current_chat"] = None
if "full_message" not in st.session_state:
    st.session_state["full_message"] = ""
if "uploaded_file" not in st.session_state:
    st.session_state["uploaded_file"] = None
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# --------- CHUNKING FEATURE ---------

def chunk_text(text, size=1000):
    return [text[i:i + size] for i in range(0, len(text), size)]

def process_file_to_json(uploaded_file):
    temp_dir = "temp_storage"
    os.makedirs(temp_dir, exist_ok=True)

    file_path = os.path.join(temp_dir, uploaded_file.name)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    text = ""
    uploaded_file.seek(0)
    text = uploaded_file.read().decode("utf-8", errors="ignore")

    chunks = chunk_text(text, size=1000)

    json_path = os.path.join(temp_dir, uploaded_file.name + ".json")
    data = {"file_name": uploaded_file.name, "chunks": chunks}

    with open(json_path, "w", encoding="utf-8") as json_file:
        json_file.write(json.dumps(data, indent=4))

    return chunks, text[:500]

# -------- END CHUNKING -----------

def create_new_chat():
    chat_id = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state["conversations"][chat_id] = {
        "title": "New Chat",
        "messages": [{"role": "assistant", "content": "How can I help you?"}],
    }
    st.session_state["current_chat"] = chat_id
    st.session_state["messages"] = st.session_state["conversations"][chat_id]["messages"]

def get_current_chat():
    if st.session_state["current_chat"] is None:
        create_new_chat()
    return st.session_state["conversations"][st.session_state["current_chat"]]["messages"]

def save_current_chat():
    st.session_state["conversations"][st.session_state["current_chat"]]["messages"] = st.session_state["messages"]

with st.sidebar:
    st.header("🗂️ Chat History")
    for chat_id, chat_data in list(st.session_state["conversations"].items())[::-1]:
        if st.button(chat_data["title"], key=chat_id):
            st.session_state["current_chat"] = chat_id
            st.session_state["messages"] = chat_data["messages"].copy()
            st.experimental_rerun()

    st.divider()
    if st.button("➕ New Chat"):
        create_new_chat()
        st.experimental_rerun()

    st.divider()
    st.header("📎 Attach a File")

    uploaded_file = st.file_uploader(
        "Browse or drag a file",
        type=["txt", "pdf", "csv", "png", "jpg", "jpeg", "docx"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        st.session_state["uploaded_file"] = uploaded_file
        st.info(f"📄 Selected: {uploaded_file.name} ({uploaded_file.size/1024:.1f} KB)")

        if st.button("📤 Send to Bot"):
            file_name = uploaded_file.name
            st.session_state["messages"].append(
                {"role": "user", "content": f"I've uploaded a file named '{file_name}'."}
            )

            try:
                chunks, preview = process_file_to_json(uploaded_file)

                st.session_state["messages"].append(
                    {"role": "user", "content": f"Here's a preview of the file:\n\n{preview}"}
                )

                auto_content = "\n".join([f"Chunk {i+1}: {chunk}" for i, chunk in enumerate(chunks[:3])])

                st.session_state["messages"].append(
                    {"role": "user", "content": f"File processed successfully.\nHere are the first chunks:\n\n{auto_content}"}
                )

            except Exception as e:
                st.session_state["messages"].append(
                    {"role": "user", "content": f"Couldn't read the file: {e}"}
                )

            save_current_chat()
            st.session_state["uploaded_file"] = None

if st.session_state["current_chat"] is None:
    st.session_state["messages"] = get_current_chat()

st.subheader(f"💭 Chat: {st.session_state['conversations'][st.session_state['current_chat']]['title']}")

for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f'<div class="stChatMessageUser">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="stChatMessageAssistant">{msg["content"]}</div>', unsafe_allow_html=True)

def generate_response():
    response = ollama.chat(
        model="llama3",
        stream=True,
        messages=st.session_state["messages"],
        options={"num_predict": 80},
    )
    for part in response:
        token = part["message"]["content"]
        st.session_state["full_message"] += token
        yield token

prompt = st.chat_input("Type your message")
if prompt:
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.markdown(f'<div class="stChatMessageUser">{prompt}</div>', unsafe_allow_html=True)

    if st.session_state["conversations"][st.session_state["current_chat"]]["title"] == "New Chat":
        st.session_state["conversations"][st.session_state["current_chat"]]["title"] = \
            prompt[:30] + ("..." if len(prompt) > 30 else "")

    st.session_state["full_message"] = ""
    st.markdown('<div class="stChatMessageAssistant"><p>', unsafe_allow_html=True)
    st.write_stream(generate_response)
    st.markdown('</p></div>', unsafe_allow_html=True)

    st.session_state["messages"].append(
        {"role": "assistant", "content": st.session_state["full_message"]}
    )

    save_current_chat()
