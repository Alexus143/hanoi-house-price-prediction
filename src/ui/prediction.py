# src/ui/prediction.py
import streamlit as st
import pandas as pd
from src import config
from src.ai_engine.predictor import PricePredictor

def render_prediction(df, model, model_columns):
    if model is None:
        st.warning("Chưa có Model AI. Hãy chạy file `src/ai_engine/train_model.py` để huấn luyện!")
        st.info("Sau khi chạy xong, reload lại trang web này.")
        return

    st.write("Nhập thông số căn nhà bạn muốn mua/bán, AI sẽ gợi ý mức giá hợp lý.")
    
    # Chia làm 2 cột cho đẹp mắt
    col_input1, col_input2 = st.columns(2)
    
    with col_input1:
        in_area = st.number_input("Diện tích (m2):", min_value=10.0, value=50.0, step=1.0, key="pred_area")
        in_bedrooms = st.number_input("Số phòng ngủ:", min_value=0, value=2, step=1, key="pred_bed")
        in_bathrooms = st.number_input("Số phòng tắm/WC:", min_value=0, value=2, step=1, key="pred_bath")
        
    with col_input2:
        # Tự động lấy danh sách khu vực và loại hình từ cấu trúc model
        valid_wards = [c.replace("ward_", "") for c in model_columns if c.startswith("ward_")]
        in_ward = st.selectbox("Khu vực:", valid_wards, key="pred_ward")
        
        valid_types = [c.replace("property_type_", "") for c in model_columns if c.startswith("property_type_")]
        if not valid_types: 
            valid_types = ['Chung cư', 'Nhà riêng', 'Đất nền']
        in_type = st.selectbox("Loại hình BĐS:", valid_types, key="pred_type")

    if st.button("🔮 Định giá ngay", type="primary"):
        try:
            predictor = PricePredictor(model=model, model_columns=model_columns)
            
            # CẬP NHẬT: Truyền đủ 5 tham số vào hàm dự đoán
            pred_price = predictor.predict_single(in_area, in_bedrooms, in_bathrooms, in_ward, in_type)
            pred_m2 = (pred_price * 1000) / in_area
            
            st.success(f"💰 Mức giá khuyến nghị: **{pred_price:.2f} Tỷ**")
            st.caption(f"Tương đương: {pred_m2:.1f} Triệu/m2")
            
            # So sánh với trung bình khu vực (Optional)
            avg_area_price = df[df['ward'] == in_ward]['price_billion'].mean()
            if not pd.isna(avg_area_price):
                diff = pred_price - avg_area_price
                if diff > 0:
                    st.info(f"📈 Cao hơn mức trung bình của {in_ward} khoảng {diff:.2f} Tỷ")
                else:
                    st.info(f"📉 Thấp hơn mức trung bình của {in_ward} khoảng {abs(diff):.2f} Tỷ")
                    
        except Exception as e:
            st.error(f"Lỗi khi dự đoán: {e}")