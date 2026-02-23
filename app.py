# app.py
import streamlit as st
import pandas as pd
import os
from streamlit_float import *

# --- IMPORT MODULES CỦA BẠN ---
from src.ai_engine.chatbot import render_chatbot
from src.ui.dashboard import render_dashboard
from src.ui.prediction import render_prediction
from src.database.postgres_manager import PostgresManager # Import module kết nối DB mới

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Bất Động Sản Hà Đông", layout="wide", page_icon="🏠")
float_init() 

# --- HÀM LOAD DỮ LIỆU TỪ POSTGRESQL ---
@st.cache_data(ttl=3600) # Cache dữ liệu 1 tiếng để web chạy nhanh, không query DB liên tục
def load_data():
    try:
        db = PostgresManager()
        # Query toàn bộ bảng listings
        query = "SELECT * FROM listings"
        df = db.load_dataframe(query)
        
        # Nếu DB chưa có dữ liệu, trả về None
        if df is None or df.empty:
            return None
            
        return df
    except Exception as e:
        st.error(f"❌ Lỗi kết nối Database: {e}")
        return None

# =========================================================
# GIAO DIỆN CHÍNH (MAIN APP)
# =========================================================
st.title("🏡 Hệ Thống Phân Tích & Định Giá BĐS Hà Đông")

# 1. Load dữ liệu tổng từ DB
df = load_data()

if df is None:
    st.error("❌ Chưa có dữ liệu hoặc không thể kết nối PostgreSQL. Vui lòng kiểm tra Database và chạy luồng ETL (cleaner.py) trước!")
    st.stop()

# 2. Render Tabs
tab1, tab2 = st.tabs(["📊 Thống Kê Thị Trường", "🔮 AI Định Giá"])

with tab1:
    # Truyền df vào dashboard (Giữ nguyên logic của bạn)
    render_dashboard(df)

with tab2:
    # Gọi AI UI cực kỳ gọn gàng, không cần truyền model hay columns nữa
    render_prediction(df)

# =========================================================
# CHATBOT (MODULE RIÊNG)
# =========================================================
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    render_chatbot(df, API_KEY)
except Exception as e:
    st.warning("⚠️ Chưa cấu hình GEMINI_API_KEY trong file `.streamlit/secrets.toml`. Chatbot hiện đang bị vô hiệu hóa.")