import streamlit as st
import google.generativeai as genai
from streamlit_float import *

def render_chatbot(df, api_key):
    """
    Hàm hiển thị Chatbot AI Floating
    df: Dataframe chứa dữ liệu bất động sản (để AI tra cứu)
    api_key: Key của Gemini
    """
    
    # Cấu hình API
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"Lỗi API Key: {e}")
        return

    # --- 1. CSS & STYLE ---
    # Nút bấm tròn (Messenger Style)
    button_css = "position: fixed; bottom: 30px; right: 30px; z-index: 10000;"
    
    # Hộp chat (Nền trắng, đổ bóng)
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
        st.session_state.messages = []

    # --- 3. NÚT BẤM MỞ CHAT ---
    with st.container():
        if st.button("💬", key="toggle_chat"):
            st.session_state.show_chat = not st.session_state.show_chat

    # --- 4. HỘP CHAT CHÍNH ---
    if st.session_state.show_chat:
        chat_container = st.container()
        
        with chat_container:
            # Header xanh
            st.markdown("""
            <div style="background-color: #0084FF; color: white; padding: 10px; border-radius: 10px 10px 0 0; font-weight: bold; text-align: center;">
                🤖 Trợ lý Bất Động Sản
            </div>
            """, unsafe_allow_html=True)
            
            # Khu vực hiển thị tin nhắn (Scrollable)
            messages_container = st.container(height=400)
            with messages_container:
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

            # Khu vực nhập liệu
            if prompt := st.chat_input("Nhập câu hỏi..."):
                # Hiển thị câu hỏi người dùng
                st.session_state.messages.append({"role": "user", "content": prompt})
                with messages_container:
                    with st.chat_message("user"):
                        st.markdown(prompt)

                # --- LOGIC RAG (TÌM KIẾM DỮ LIỆU) ---
                # 1. Chuẩn bị dữ liệu thống kê mặc định
                avg_all = df['price_billion'].mean()
                count_all = len(df)
                stats_text = f"Tổng quan toàn bộ Hà Đông: {count_all} tin đăng, giá TB {avg_all:.2f} tỷ."

                # 2. Tìm xem người dùng có hỏi về Phường cụ thể nào không
                ds_phuong = df['ward'].dropna().unique()
                for phuong in ds_phuong:
                    if phuong.lower() in prompt.lower():
                        df_loc = df[df['ward'] == phuong]
                        if not df_loc.empty:
                            loc_avg = df_loc['price_billion'].mean()
                            loc_count = len(df_loc)
                            stats_text = f"Khu vực {phuong}: {loc_count} tin, giá TB {loc_avg:.2f} tỷ."
                        break
                
                # --- GỌI GEMINI ---
                try:
                    # Dùng model flash cho nhanh
                    model = genai.GenerativeModel('gemini-2.5-flash') 
                    
                    full_prompt = f"""
                    Bạn là trợ lý ảo Bất động sản Hà Đông. 
                    Dữ liệu thực tế: {stats_text}
                    
                    Khách hàng hỏi: "{prompt}"
                    Hãy trả lời ngắn gọn, thân thiện, dựa trên số liệu trên.
                    """
                    
                    response = model.generate_content(full_prompt)
                    ai_reply = response.text
                    
                    # Hiển thị câu trả lời AI
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                    with messages_container:
                        with st.chat_message("assistant"):
                            st.markdown(ai_reply)
                            
                    st.rerun() # Cập nhật lại giao diện
                    
                except Exception as e:
                    st.error(f"Lỗi AI: {e}")

        # Áp dụng CSS Float cho container
        chat_container.float(chat_box_css)