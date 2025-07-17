import os
import random
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime
from two_stage_rag_pipeline import initialize_pinecone, rag_chain, initialize_conversation
import json
import base64
import html
import time

os.environ.pop("SSL_CERT_FILE", None)

# Streamlit 설정(레이아웃, 스타일)
st.set_page_config(page_title="BOO Chat", page_icon=" ", layout="centered")
st.title("BOO Chat")

st.markdown("""
<style>
/* form 자체 스타일 제거 */
div[data-testid="stForm"] {
    background-color: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
    box-shadow: none !important;
}

/* form 안의 모든 버튼 제거 */
div[data-testid="stForm"] button {
    display: none !important;
    visibility: hidden !important;
    height: 0px !important;
    padding: 0px !important;
    margin: 0px !important;
    border: none !important;
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

hide_streamlit_style = """
                <style>
                div[data-testid="stToolbar"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stDecoration"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stStatusWidget"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                #MainMenu {
                visibility: hidden;
                height: 0%;
                }
                header {
                visibility: hidden;
                height: 0%;
                }
                footer {
                visibility: hidden;
                height: 0%;
                }
                </style>
                """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 


with st.spinner("페이지를 로딩 중입니다... 잠시만 기다려주세요."):
    # Pinecone 설정 및 초기화
    if 'vectorstore' not in st.session_state:
        st.session_state.vectorstore = initialize_pinecone()

    # 대화 초기화
    if 'conversation' not in st.session_state:
        from rag_pipeline import initialize_conversation
        st.session_state.conversation = initialize_conversation(st.session_state.vectorstore)

# ---- 소개 페이지 함수 ----
def get_image_base64(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
        return base64.b64encode(data).decode("utf-8")

def show_home():
    img_base64=get_image_base64("01.png")
    st.markdown(f"""
<div style='width: 110%; padding: 20px; border-radius: 15px; background-color: #E3F2FD; display: flex; align-items: center; justify-content: center; gap: 40px;'>  
<div style="flex-shrink: 0;">        
    <img src='data:image/png;base64,{img_base64}' width='180' alt='이미지'>
</div>

<div style="text-align: left; max-width: 500px;">
    <h1 style='color: #0D47A1;'>Boo Chat이란?</h1>
    <p style='font-size:18px;'>
        Boo Chat은 <b>한국외국어대학교 글로벌캠퍼스</b> 학생들을 위해<br>만들어진 챗봇입니다!<br>
        학사정보에 대한 다양한 정보를 쉽고 빠르게 안내합니다.<br><br>
        사이드바에서 <b>"BOO Chat"</b>을 선택하면 자유롭게 질문할 수 있고,<br>
        <b>"자주 묻는 질문(FAQ)"</b>을 선택하면 자주 하는 질문들을 빠르게 확인할 수 있어요!
    </p>
</div>
</div>
""", unsafe_allow_html=True)

# ---- 챗봇 메시지 표시 함수 ----
def display_message(role, content, timestamp):
    content = html.escape(content).replace("\n", "<br>")

    alignment = 'flex-end' if role == "user" else 'flex-start'
    bg_color = '#E3F2FD' if role == "user" else '#F1F0F0'
    text_align = 'right' if role == "user" else 'left'
    label = " " if role == "user" else "BOO Chat"
    timestamp_position = 'left: -60px;' if role == "user" else 'right: -60px;'

    return f"""
        <div style='display: flex; justify-content: {alignment}; margin-bottom: 10px;'>
            <div style='max-width: 60%; position: relative;'>
                <div style='text-align: {text_align}; color: #888;'>{label}</div>
                <div style='background-color: {bg_color}; padding: 10px; border-radius: 10px; color: black; border: 1px solid #C0C0C0;'>
                    {content}
                </div>
                <div style='font-size: 0.8em; color: #555; position: absolute; {timestamp_position} bottom: 0; margin: 0 5px;'>{timestamp}</div>
            </div>
        </div>
    """

# ---- 챗봇 페이지 함수 ----
def show_chatbot():
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []

    submitted = False
    user_input = ""

    chat_container = st.container()

    with chat_container:
        st.markdown(display_message("assistant", "안녕하세요! BOO Chat입니다. 무엇이 궁금하신가요?", ""), unsafe_allow_html=True)
        
        for message in st.session_state['messages']:
            st.markdown(display_message(message['role'], message['content'], message['timestamp']), unsafe_allow_html=True)

    input_container = st.container()
    with input_container:
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input(
                label="",
                placeholder="질문을 입력해주세요..."
            )
            submitted = st.form_submit_button(label="submit", use_container_width=False)

    if submitted and user_input.strip():
        user_input = user_input.strip()
        timestamp = datetime.now().strftime('%p %I:%M')

        st.session_state['messages'].append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        })

        response_timestamp = datetime.now().strftime('%p %I:%M')
        with chat_container:
            st.markdown(display_message("user", user_input, timestamp), unsafe_allow_html=True)
            response_placeholder = st.empty()

        try:
            with response_placeholder.container():
                with st.spinner("답변을 생성 중입니다..."):
                    answer = st.session_state.conversation.invoke(
                        {"input": user_input},
                        config={"configurable": {"session_id": "boo-chat-session"}}
                    )
                    if isinstance(answer, dict):
                        answer = answer.get("answer") or answer.get("output") or json.dumps(answer, ensure_ascii=False)
        except Exception as e:
            answer = f"오류가 발생했습니다: {e}"

        st.session_state['messages'].append({
            "role": "assistant",
            "content": answer,
            "timestamp": response_timestamp
        })

        # streaming 출력(타이핑 효과)
        animated_response = ""
        for char in answer:
            animated_response += char
            response_placeholder.markdown(display_message("assistant", animated_response, response_timestamp), unsafe_allow_html=True)
            time.sleep(0.015)

    # 스타일 추가 
    st.markdown(
        """
        <style>
        .stTextInput, .stAlert {
            border-radius: 10px;
            margin-left: 20px;
        }
        .css-1gkdjib.e1yohnl3 {
            height: 70vh;
            overflow-y: auto;
        }
        .css-1gkdjib.e1yohnl3 > div {
            margin-bottom: 10px;
        }
        .css-145kmo2.e1ewe7hr3 {
            margin-top: auto;
        }
        .stTextInput {
            width: 100%;
            height: 38px;
            margin: 0;
            border-radius: 8px;
            font-size: 16px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# 학교 공식 faq
@st.cache_data
def load_faq_data():
    with open("hufs_faq.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ---- 자주묻는질문 페이지 함수 ----
def show_faq():
    if st.session_state.get('last_page') != "자주 묻는 질문 (FAQ)":
        st.session_state.faq_chat = []

    st.markdown("""
    <div style='text-align: center; padding: 20px; border-radius: 15px; background-color: #E3F2FD; margin-bottom: 25px;'>
        <h2>자주 묻는 질문 (FAQ)</h2>
        <p>아래 버튼을 클릭해 질문과 답변을 확인해보세요!</p>
    </div>
    """, unsafe_allow_html=True)

    # JSON 데이터 불러오기
    faq_data = load_faq_data()
    all_questions = [item["question"] for item in faq_data]
    answer_map = {item["question"]: item["answer"] for item in faq_data}

    # 무작위 9개 질문 선택
    if 'current_questions' not in st.session_state:
        st.session_state.current_questions = random.sample(all_questions, min(9, len(all_questions)))

    cols = st.columns(3)
    for i, question in enumerate(st.session_state.current_questions):
        with cols[i % 3]:
            if st.button(question, key=f"faq_btn_{i}"):
                timestamp = datetime.now().strftime('%p %I:%M')
                st.session_state.faq_chat.append({
                    "role": "user",
                    "content": question,
                    "timestamp": timestamp
                })
                st.session_state.faq_chat.append({
                    "role": "assistant",
                    "content": answer_map.get(question, "죄송합니다. 답변을 찾을 수 없습니다."),
                    "timestamp": datetime.now().strftime('%p %I:%M')
                })

    if st.button("🔁 다른 질문 보기"):
        st.session_state.current_questions = random.sample(all_questions, min(9, len(all_questions)))
        st.rerun()

    st.markdown("---")
    for message in st.session_state.faq_chat:
        content = message['content']
        if isinstance(content, dict):
            content = content.get("answer") or json.dumps(content, ensure_ascii=False)
        
        st.markdown(display_message(message['role'], content, message['timestamp']), unsafe_allow_html=True)

# --- 사이드바 메뉴 ---
menu = st.sidebar.radio("📚 메뉴", ["소개", "BOO Chat", "자주 묻는 질문 (FAQ)"])

if 'last_page' not in st.session_state:
    st.session_state.last_page = None


# --- 함수 실행 ---
if menu == "소개":
    show_home()
elif menu == "BOO Chat":
    show_chatbot()
elif menu == "자주 묻는 질문 (FAQ)":
    show_faq()

st.session_state.last_page = menu



