# tests/test_prediction_ui.py
import pytest
import pandas as pd
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.ui.prediction import render_prediction

# ==========================================
# TEST 1: LUỒNG UI BÌNH THƯỜNG (HAPPY PATH)
# ==========================================
@patch('src.ui.prediction.get_predictor')
@patch('streamlit.button', return_value=True) # Giả lập người dùng BẤM NÚT "Định giá ngay"
@patch('streamlit.selectbox')
@patch('streamlit.number_input')
@patch('streamlit.success')
def test_render_prediction_success(mock_success, mock_num, mock_select, mock_button, mock_get_predictor):
    # 1. Arrange: Giả lập Model và Data DB
    mock_predictor = MagicMock()
    mock_predictor.is_ready.return_value = True
    mock_predictor.mae = 0.5
    mock_predictor.predict_single.return_value = (5.5, 0.11, 0.5) # Trả về Tổng giá, Đơn giá, MAE
    mock_get_predictor.return_value = mock_predictor

    # Giả lập input từ DB để UI render danh sách
    mock_df = pd.DataFrame({
        'ward': ['Văn Quán', 'Hà Cầu'],
        'property_type': ['Nhà riêng', 'Chung cư'],
        'direction': ['Đông', 'Tây'],
        'price_billion': [5.0, 6.0]
    })

    # 2. Action: Chạy hàm Render UI
    render_prediction(mock_df)

    # 3. Assert: Kiểm tra xem hàm dự đoán của AI có được gọi khi bấm nút không
    mock_predictor.predict_single.assert_called_once()
    
    # Kiểm tra xem có hiển thị thông báo Success màu xanh lên màn hình không
    mock_success.assert_called()
    # Kiểm tra nội dung thông báo có chứa giá 5.5 Tỷ không
    success_message = mock_success.call_args[0][0]
    assert "5.50 Tỷ" in success_message

# ==========================================
# TEST 2: HIỂN THỊ CẢNH BÁO KHI THIẾU MODEL
# ==========================================
@patch('src.ui.prediction.get_predictor')
@patch('streamlit.warning')
def test_render_prediction_no_model(mock_warning, mock_get_predictor):
    mock_predictor = MagicMock()
    mock_predictor.is_ready.return_value = False # Giả lập chưa có model
    mock_get_predictor.return_value = mock_predictor

    render_prediction(pd.DataFrame())

    # Nếu chưa có model, phải in ra Warning và dừng lại
    mock_warning.assert_called_once()
    warning_msg = mock_warning.call_args[0][0]
    assert "Chưa có Model AI" in warning_msg