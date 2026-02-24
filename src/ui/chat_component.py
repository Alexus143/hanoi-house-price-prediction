# src/ui/chat_component.py
import streamlit as st
from streamlit_float import *
from src.ai_engine.chatbot import generate_chatbot_response

def render_chatbot(df, api_key):
    """
    Hàm hiển thị Chatbot AI Floating có bộ nhớ ngữ cảnh trên giao diện.
    """
    # --- 1. CSS & STYLE ---
    button_css = "position: fixed; bottom: 30px; right: 30px; z-index: 10000;"
    chat_box_css = """
        position: fixed; 
        bottom: 100px; 
        right: 30px; 
        width: 400px; 
        background-color: white; 
        border-radius: 10px; 
        border: 1px solid #ddd; 
        box-shadow: 0px 5px 20px rgba(0,0,0,0.2); 
        z-index: 9999;
        overflow: hidden;
    """

    st.markdown(
        f"""
        <style>
        div.stButton > button[kind="secondary"] {{
            {button_css}
            border-radius: 50%;
            width: 60px;
            height: 60px;
            background-color: #0084FF;
            color: white;
            font-size: 24px;
            border: none;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            transition: transform 0.2s;
        }}
        div.stButton > button[kind="secondary"]:hover {{
            transform: scale(1.1);
            background-color: #0073e6;
        }}
        </style>
        """, 
        unsafe_allow_html=True
    )

    # --- 2. QUẢN LÝ TRẠNG THÁI (SESSION STATE) ---
    if "show_chat" not in st.session_state:
        st.session_state.show_chat = False
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Chào bạn! Tôi là trợ lý AI Bất động sản Hà Đông. Bạn muốn tìm hiểu giá nhà ở khu vực nào?"}
        ]

    # --- 3. NÚT BẤM MỞ CHAT ---
    with st.container():
        if st.button("💬", key="toggle_chat"):
            st.session_state.show_chat = not st.session_state.show_chat

    # --- 4. HỘP CHAT CHÍNH ---
    if st.session_state.show_chat:
        chat_container = st.container()
        
        with chat_container:
            st.markdown("""
            <div style="background-color: #0084FF; color: white; padding: 10px; border-radius: 10px 10px 0 0; font-weight: bold; text-align: center;">
                🤖 Trợ lý AI Bất Động Sản
            </div>
            """, unsafe_allow_html=True)
            
            messages_container = st.container(height=350)
            with messages_container:
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

            if prompt := st.chat_input("Nhập câu hỏi... (VD: Giá nhà Văn Quán)"):
                # Hiển thị ngay câu hỏi của user
                st.session_state.messages.append({"role": "user", "content": prompt})
                with messages_container:
                    with st.chat_message("user"):
                        st.markdown(prompt)

                # Gọi API Engine để lấy phản hồi
                try:
                    # Truyền lịch sử chat (không bao gồm tin nhắn vừa nhập để khớp logic cũ)
                    chat_history = st.session_state.messages[:-1] 
                    
                    ai_reply = generate_chatbot_response(
                        prompt=prompt, 
                        df=df, 
                        chat_history=chat_history, 
                        api_key=api_key
                    )
                    
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                    st.rerun() 
                    
                except Exception as e:
                    st.error(f"Đã xảy ra lỗi: {e}")

        # Float container lên trên UI chính
        chat_container.float(chat_box_css)