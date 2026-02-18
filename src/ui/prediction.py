# src/prediction.py
import streamlit as st
import pandas as pd
from src import config
from src.ai_engine.predictor import PricePredictor

def render_prediction(df, model, model_columns):
    """
    Hàm hiển thị Tab AI Định giá
    df: Dataframe gốc (để so sánh giá)
    model: Model đã load
    model_columns: Danh sách cột của model
    """
    if model is None:
        st.warning("Chưa có Model AI. Hãy chạy file `src/ai_engine/train_model.py` để huấn luyện!")
        st.info("Sau khi chạy xong, reload lại trang web này.")
        return

    st.write("Nhập thông số căn nhà bạn muốn mua/bán, AI sẽ gợi ý mức giá hợp lý.")
    
    col_input1, col_input2 = st.columns(2)
    
    with col_input1:
        in_area = st.number_input("Diện tích (m2):", min_value=10.0, value=50.0, step=1.0, key="pred_area")
        
    with col_input2:
        # Lấy danh sách phường từ model columns để đảm bảo khớp dữ liệu
        valid_wards = [c.replace("ward_", "") for c in model_columns if c.startswith("ward_")]
        in_ward = st.selectbox("Khu vực:", valid_wards, key="pred_ward")

    if st.button("🔮 Định giá ngay", type="primary"):
        
        # 4. Dự đoán
        try:
            predictor = PricePredictor(model=model, model_columns=model_columns)
            
            # Gọi hàm dự đoán (chỉ cần area và ward)
            pred_price = predictor.predict_single(in_area, in_ward)
            pred_m2 = (pred_price * 1000) / in_area
            
            # 5. Hiển thị kết quả
            st.success(f"💰 Mức giá khuyến nghị: **{pred_price:.2f} Tỷ**")
            st.caption(f"Tương đương: {pred_m2:.1f} Triệu/m2")
            
            # So sánh với trung bình khu vực
            avg_area_price = df[df['ward'] == in_ward]['price_billion'].mean()
            if not pd.isna(avg_area_price):
                diff = pred_price - avg_area_price
                if diff > 0:
                    st.write(f"📈 Cao hơn trung bình khu vực {in_ward} khoảng {abs(diff):.2f} tỷ.")
                else:
                    st.write(f"📉 Thấp hơn trung bình khu vực {in_ward} khoảng {abs(diff):.2f} tỷ.")
        except Exception as e:
            st.error(f"Lỗi khi dự đoán: {e}")