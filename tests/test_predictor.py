# tests/test_predictor.py
import pytest
import pandas as pd
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.ai_engine.predictor import PricePredictor

# ==========================================
# TEST 1: CHUẨN BỊ DỮ LIỆU ĐẦU VÀO (FEATURE ALIGNMENT)
# ==========================================
@patch('src.ai_engine.predictor.joblib.load')
@patch('os.path.exists', return_value=True)
def test_predict_single_feature_alignment(mock_exists, mock_load):
    # 1. Arrange: Giả lập Model đã train xong với 8 features
    mock_model = MagicMock()
    mock_model.predict.return_value = [0.15] # Giả lập AI dự đoán đơn giá = 0.15 Tỷ/m2
    
    mock_load.return_value = {
        'model': mock_model,
        'features': ['area', 'frontage', 'ward_Văn Quán', 'ward_Hà Cầu', 'direction_Đông', 'furniture_Full'],
        'mae': 0.8
    }

    predictor = PricePredictor("fake/path.pkl")

    # 2. Action: Người dùng UI nhập các thông số
    total_price, unit_price, mae = predictor.predict_single(
        area=50, bedrooms=3, bathrooms=2, 
        ward='Văn Quán', property_type='Nhà riêng',
        frontage=5.0, road_width=3.0, floors=4,
        direction='Đông', legal_status='Sổ đỏ', furniture='Không xác định'
    )

    # 3. Assert: Kiểm tra thuật toán quy đổi Giá
    assert unit_price == 0.15, "Lỗi: Lấy sai đơn giá từ model"
    assert total_price == 50 * 0.15, "Lỗi: Tính sai Tổng giá (Đơn giá * Diện tích)"

    # 4. Assert: Kiểm tra DataFrame truyền vào Model có đúng không
    # Gọi args của hàm predict để xem DataFrame truyền vào là gì
    df_input = mock_model.predict.call_args[0][0]
    
    # Kiểm tra Numerical
    assert df_input.loc[0, 'area'] == 50
    assert df_input.loc[0, 'frontage'] == 5.0
    
    # Kiểm tra One-hot mapping: Chọn Văn Quán thì cột ward_Văn Quán phải = 1, ward_Hà Cầu phải = 0
    assert df_input.loc[0, 'ward_Văn Quán'] == 1
    assert df_input.loc[0, 'ward_Hà Cầu'] == 0
    assert df_input.loc[0, 'direction_Đông'] == 1
    
    # Chọn Nội thất = Không xác định (Không có trong lúc train) thì cột furniture_Full phải = 0
    assert df_input.loc[0, 'furniture_Full'] == 0

# ==========================================
# TEST 2: MODEL CHƯA SẴN SÀNG
# ==========================================
@patch('os.path.exists', return_value=False) # Giả lập file pkl không tồn tại
def test_predictor_not_ready(mock_exists):
    predictor = PricePredictor("fake/path.pkl")
    assert not predictor.is_ready()
    
    with pytest.raises(ValueError, match="Model chưa sẵn sàng!"):
        predictor.predict_single(50, 2, 2, 'A', 'B', 4, 3, 3, 'C', 'D', 'E')