# src/ui/prediction.py
import streamlit as st
import pandas as pd
import os
from src.ai_engine.predictor import PricePredictor
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config.path import MODEL_PATH, XGB_MODEL_PATH

@st.cache_resource
def get_predictor():
    return PricePredictor(XGB_MODEL_PATH)

def render_prediction(df):
    predictor = get_predictor()

    if not predictor.is_ready():
        st.warning("Chưa có Model AI. Hãy chạy file `src/ai_engine/train_model.py` để huấn luyện!")
        return

    st.write("Nhập thông số căn nhà bạn muốn mua/bán, AI sẽ gợi ý mức giá hợp lý.")
    st.caption(f"Hệ thống đang sử dụng mô hình XGBoost (Sai số chuẩn MAE: **{predictor.mae:.2f} Tỷ VNĐ**)")
    
    # --- Trích xuất danh mục động từ Database để nạp vào SelectBox ---
    valid_wards = sorted(df['ward'].dropna().unique().tolist())
    valid_types = sorted(df['property_type'].dropna().unique().tolist())
    
    # Bổ sung các list danh mục mới (Lọc N/A và thêm mác mặc định)
    valid_directions = ['Không xác định'] + sorted([str(x) for x in df.get('direction', pd.Series()).dropna().unique() if str(x) != 'Không xác định'])
    valid_legals = ['Không xác định'] + sorted([str(x) for x in df.get('legal_status', pd.Series()).dropna().unique() if str(x) != 'Không xác định'])
    valid_furnitures = ['Không xác định'] + sorted([str(x) for x in df.get('furniture', pd.Series()).dropna().unique() if str(x) != 'Không xác định'])

    # --- UI BỐ CỤC ---
    st.markdown("### 1. Thông tin cơ bản")
    col1, col2 = st.columns(2)
    with col1:
        in_type = st.selectbox("Loại hình BĐS:", valid_types, key="pred_type")
        in_ward = st.selectbox("Khu vực:", valid_wards, key="pred_ward")
        in_area = st.number_input("Diện tích (m2):", min_value=10.0, value=50.0, step=1.0, key="pred_area")
    with col2:
        is_land = (in_type == 'Đất nền')
        in_bedrooms = st.number_input("Số phòng ngủ:", value=0 if is_land else 2, min_value=0, step=1, disabled=is_land)
        in_bathrooms = st.number_input("Số phòng tắm/WC:", value=0 if is_land else 2, min_value=0, step=1, disabled=is_land)
        in_floors = st.number_input("Số tầng:", value=0 if is_land else 3, min_value=0, step=1, disabled=is_land)

    # Dùng Expander để giấu đi thông tin nâng cao, làm UI bớt rườm rà
    with st.expander("2. Thông số thặng dư (Nâng cao) - Giúp AI định giá chuẩn hơn", expanded=True):
        col3, col4 = st.columns(2)
        with col3:
            in_frontage = st.number_input("Mặt tiền (m):", min_value=1.0, value=4.0, step=0.5, help="Chiều rộng mặt trước nhà")
            in_road_width = st.number_input("Đường vào (m):", min_value=1.0, value=3.0, step=0.5, help="Khoảng cách đường ngõ trước nhà")
        with col4:
            in_direction = st.selectbox("Hướng nhà:", valid_directions)
            in_legal = st.selectbox("Pháp lý:", valid_legals)
            in_furniture = st.selectbox("Nội thất:", valid_furnitures)

    if st.button("Định giá ngay", type="primary", use_container_width=True):
        try:
            # Truyền TẤT CẢ biến vào Predictor
            pred_price, pred_unit_price, mae = predictor.predict_single(
                area=in_area, bedrooms=in_bedrooms, bathrooms=in_bathrooms, 
                ward=in_ward, property_type=in_type,
                frontage=in_frontage, road_width=in_road_width, floors=in_floors,
                direction=in_direction, legal_status=in_legal, furniture=in_furniture
            )
            
            pred_m2_display = pred_unit_price * 1000
            
            st.success(f"Mức giá khuyến nghị: **{pred_price:.2f} Tỷ VNĐ**")
            st.caption(f"Đơn giá tương đương: **{pred_m2_display:.1f} Triệu/m2**")
            
            # Tính năng so sánh trung bình khu vực
            avg_area_price = df[(df['ward'] == in_ward) & (df['property_type'] == in_type)]['price_billion'].mean()
            if pd.notna(avg_area_price):
                diff = pred_price - avg_area_price
                if diff > 0:
                    st.info(f"Cao hơn mức trung bình của {in_type} tại {in_ward} khoảng {diff:.2f} Tỷ")
                elif diff < 0:
                    st.info(f"Thấp hơn mức trung bình của {in_type} tại {in_ward} khoảng {abs(diff):.2f} Tỷ")
                    
        except Exception as e:
            st.error(f"Lỗi khi dự đoán: {e}")