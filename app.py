import google.generativeai as genai
import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import os
import joblib
from streamlit_float import * # Import thư viện float
from src.chatbot import render_chatbot 

# --- CẤU HÌNH TRANG & CSS ---
st.set_page_config(page_title="Bất Động Sản Hà Đông", layout="wide")

# Kích hoạt tính năng float
float_init()

# --- CSS TÙY CHỈNH CHO ĐẸP ---
st.markdown("""
<style>
    /* Làm đẹp cho container chat */
    div.st-emotion-cache-1jicfl2 {
        width: 100%;
        padding: 0px;
    }
    /* Tạo hiệu ứng bóng đổ cho hộp chat */
    .chat-container {
        border: 1px solid #ccc;
        border-radius: 10px 10px 0 0;
        background-color: white;
        box-shadow: 0px -5px 10px rgba(0,0,0,0.1);
        z-index: 9999;
    }
</style>
""", unsafe_allow_html=True)

# --- CẤU HÌNH ĐƯỜNG DẪN ---
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, 'data', 'real_estate.db')
model_path = os.path.join(current_dir, 'data', 'house_price_model.pkl')

# --- HÀM LOAD DỮ LIỆU ---
def load_data():
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM listings", conn)
    conn.close()
    return df

# --- HÀM LOAD MODEL AI ---
def load_model():
    if not os.path.exists(model_path):
        return None, None
    artifact = joblib.load(model_path)
    return artifact['model'], artifact['model_columns']

# --- GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="Bất Động Sản Hà Đông", layout="wide")
st.title("🏡 Hệ Thống Phân Tích & Định Giá BĐS Hà Đông")

df = load_data()

if df is None:
    st.error(f"❌ Không tìm thấy Database tại: {db_path}. Hãy chạy scraper và cleaner trước!")
    st.stop()

# Tách cột Phường nếu chưa có (Phòng hờ)
if 'ward' not in df.columns:
    df['ward'] = df['location'].apply(lambda x: x.split(',')[0].strip())

# TẠO 2 TAB CHỨC NĂNG
tab1, tab2 = st.tabs(["📊 Thống Kê Thị Trường", "🔮 AI Định Giá"])

# ==============================================================================
# TAB 1: THỐNG KÊ (DASHBOARD CŨ)
# ==============================================================================
with tab1:
    col_filter1, col_filter2 = st.columns(2)
    
    # 1. Bộ lọc Khu vực
    with col_filter1:
        location_counts = df['ward'].value_counts()
        options = ["Tất cả"] + location_counts.index.tolist()
        chon_phuong = st.selectbox("Chọn Phường/Xã:", options, index=0)

    # Lọc dữ liệu theo phường
    if chon_phuong != "Tất cả":
        df_display = df[df['ward'] == chon_phuong]
    else:
        df_display = df

    # 2. Bộ lọc Giá (Slider)
    with col_filter2:
        max_price_db = float(df_display['price_billion'].max())
        default_max = float(df_display['price_billion'].quantile(0.95)) # Mặc định loại bỏ top 5% giá ảo
        
        price_range = st.slider(
            "Khoảng giá mong muốn (Tỷ):",
            0.0, max_price_db, (0.0, default_max)
        )

    # Lọc dữ liệu theo giá
    df_final = df_display[
        (df_display['price_billion'] >= price_range[0]) & 
        (df_display['price_billion'] <= price_range[1])
    ]

    st.markdown("---")

    # 3. Hiển thị KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Số lượng tin", f"{len(df_final)} tin")
    c2.metric("Giá trung bình", f"{df_final['price_billion'].mean():.2f} Tỷ")
    if len(df_final) > 0:
        avg_price_m2 = (df_final['price_billion'].sum() * 1000) / df_final['area'].sum()
        c3.metric("Đơn giá trung bình", f"{avg_price_m2:.1f} Triệu/m2")
    else:
        c3.metric("Đơn giá trung bình", "0")

    # 4. Biểu đồ
    if len(df_final) > 0:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.hist(df_final['price_billion'], bins=30, color='#2E86C1', edgecolor='white', alpha=0.8)
        ax.set_title(f"Phân bố giá tại {chon_phuong}")
        ax.set_xlabel("Giá (Tỷ VNĐ)")
        ax.set_ylabel("Số lượng")
        st.pyplot(fig)
        
        st.subheader("Dữ liệu chi tiết")
        st.dataframe(df_final[['title', 'price_billion', 'area', 'ward', 'published_date']].sort_values('price_billion'))
    else:
        st.warning("Không tìm thấy tin nào phù hợp với bộ lọc.")

# ==============================================================================
# TAB 2: AI ĐỊNH GIÁ (CHỨC NĂNG MỚI)
# ==============================================================================
with tab2:
    model, model_columns = load_model()
    
    if model is None:
        st.warning("⚠️ Chưa có Model AI. Hãy chạy file `src/train_model.py` để huấn luyện!")
        st.info("Sau khi chạy xong, reload lại trang web này.")
    else:
        st.write("Nhập thông số căn nhà bạn muốn mua/bán, AI sẽ gợi ý mức giá hợp lý.")
        
        col_input1, col_input2 = st.columns(2)
        
        with col_input1:
            in_area = st.number_input("Diện tích (m2):", min_value=10.0, value=50.0, step=1.0)
            
        with col_input2:
            # Lấy danh sách phường từ model columns (để đảm bảo khớp dữ liệu)
            # Tên cột trong model có dạng "ward_Yên Nghĩa" -> Cắt bỏ "ward_"
            valid_wards = [c.replace("ward_", "") for c in model_columns if c.startswith("ward_")]
            in_ward = st.selectbox("Khu vực:", valid_wards)

        if st.button("🔮 Định giá ngay", type="primary"):
            # 1. Tạo input dataframe
            input_data = pd.DataFrame({'area': [in_area], 'ward': [in_ward]})
            
            # 2. One-hot encoding
            input_encoded = pd.get_dummies(input_data, columns=['ward'])
            
            # 3. Đồng bộ cột với model (Thêm cột thiếu, bỏ cột thừa)
            input_encoded = input_encoded.reindex(columns=model_columns, fill_value=0)
            
            # 4. Dự đoán
            pred_price = model.predict(input_encoded)[0]
            pred_m2 = (pred_price * 1000) / in_area
            
            # 5. Hiển thị kết quả
            st.success(f"💰 Mức giá khuyến nghị: **{pred_price:.2f} Tỷ**")
            st.caption(f"Tương đương: {pred_m2:.1f} Triệu/m2")
            
            # So sánh vui
            avg_area_price = df[df['ward'] == in_ward]['price_billion'].mean()
            if not pd.isna(avg_area_price):
                diff = pred_price - avg_area_price
                if diff > 0:
                    st.write(f"📈 Cao hơn trung bình khu vực {in_ward} khoảng {abs(diff):.2f} tỷ.")
                else:
                    st.write(f"📉 Thấp hơn trung bình khu vực {in_ward} khoảng {abs(diff):.2f} tỷ.")

# =========================================================
# GỌI CHATBOT TỪ MODULE RIÊNG
# =========================================================
# Lấy key từ secrets
api_key = st.secrets["GEMINI_API_KEY"]

# Truyền vào hàm
render_chatbot(df, api_key)