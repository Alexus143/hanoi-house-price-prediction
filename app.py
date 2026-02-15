import streamlit as st
import pandas as pd
import sqlite3
import os
import joblib
from streamlit_float import *

# --- IMPORT MODULES CỦA BẠN ---
from src.chatbot import render_chatbot
from src.dashboard import render_dashboard
from src.prediction import render_prediction

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Bất Động Sản Hà Đông", layout="wide")
float_init() 

# --- CẤU HÌNH ĐƯỜNG DẪN ---
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, 'data', 'real_estate.db')
model_path = os.path.join(current_dir, 'data', 'house_price_model.pkl')

# --- HÀM LOAD DỮ LIỆU ---
@st.cache_data # Dùng cache để web chạy nhanh hơn, không load lại DB liên tục
def load_data():
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM listings", conn)
    conn.close()
    # Xử lý cột Ward luôn tại đây
    if 'ward' not in df.columns:
        df['ward'] = df['location'].apply(lambda x: x.split(',')[0].strip())
    return df

# --- HÀM LOAD MODEL ---
@st.cache_resource # Cache resource cho model nặng
def load_model():
    if not os.path.exists(model_path):
        return None, None
    artifact = joblib.load(model_path)
    return artifact['model'], artifact['model_columns']

# =========================================================
# GIAO DIỆN CHÍNH (MAIN APP)
# =========================================================
st.title("🏡 Hệ Thống Phân Tích & Định Giá BĐS Hà Đông")

df = load_data()

if df is None:
    st.error("❌ Chưa có dữ liệu. Vui lòng chạy Crawler!")
    st.stop()

# --- TẠO TABS ---
tab1, tab2 = st.tabs(["📊 Thống Kê Thị Trường", "🔮 AI Định Giá"])

with tab1:
    # Gọi hàm từ module dashboard
    render_dashboard(df)

with tab2:
    # Load model và gọi hàm từ module prediction
    model, model_columns = load_model()
    render_prediction(df, model, model_columns)

# =========================================================
# CHATBOT (MODULE RIÊNG)
# =========================================================
# Thay API KEY của bạn vào đây (hoặc dùng st.secrets)
API_KEY = "AIzaSyDZknlLHIsQeaO07uou-Sa_dkIMkupv9ao" 
render_chatbot(df, API_KEY)