# tests/test_train_model.py
import pytest
import pandas as pd
import numpy as np
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.ai_engine.train_model import preprocess_features, train_and_evaluate

# ==========================================
# TEST 1: TIỀN XỬ LÝ & LÀM SẠCH FEATURE MỚI
# ==========================================
def test_preprocess_features():
    # Giả lập dữ liệu thô y hệt cào từ Batdongsan về
    mock_df = pd.DataFrame({
        'price_billion': [5.0, 10.0, 3.0],
        'area': [50.0, 100.0, 30.0],
        'ward': ['Văn Quán', 'Hà Cầu', 'La Khê'],
        'property_type': ['Nhà riêng', 'Biệt thự', 'Đất nền'],
        'bedrooms': [3, 4, 0],
        'bathrooms': [2, 3, 0],
        'frontage': ['5 m', None, '10.5m'], # Test Regex móc số và điền None
        'road_width': ['Ngõ 3m', '10 m', np.nan],
        'floors': ['Xây 4 tầng', '5', None],
        'direction': ['Đông', None, 'Tây'],
        'legal_status': ['Sổ đỏ', 'Sổ hồng', None],
        'furniture': ['Cơ bản', None, 'Full']
    })

    X, y = preprocess_features(mock_df)

    # 1. Test biến mục tiêu (Đơn giá)
    assert 'unit_price' in y.columns
    assert y.loc[0, 'unit_price'] == 0.1 # 5 tỷ / 50m2 = 0.1 tỷ/m2
    
    # 2. Test Regex bóc tách số
    assert X.loc[0, 'frontage'] == 5.0
    assert X.loc[2, 'frontage'] == 10.5
    assert X.loc[0, 'road_width'] == 3.0 # Lấy được số 3 từ "Ngõ 3m"
    assert X.loc[0, 'floors'] == 4.0 # Lấy được số 4 từ "Xây 4 tầng"

    # 3. Test điền Missing Data (FillNA)
    # Hàng 1 (index 1) frontage bị None, phải được điền bằng Median của [5.0, 10.5] là 7.75
    assert X.loc[1, 'frontage'] == 7.75 
    
    # 4. Test điền "Không xác định" cho Categorical và Dummy Variable Trap
    # Hàng 1 (index 1) direction bị None, quy về 'Không xác định'.
    # Vì drop_first=True đã xóa cột 'Không xác định', nên các cột còn lại (Đông, Tây) của hàng này phải đều bằng 0 (hoặc False)
    assert 'direction_Đông' in X.columns
    assert 'direction_Tây' in X.columns
    # Cả Đông và Tây đều False -> Ngầm hiểu là "Không xác định"
    assert X.loc[1, 'direction_Đông'] == False
    assert X.loc[1, 'direction_Tây'] == False

# ==========================================
# TEST 2: HUẤN LUYỆN MODEL (MOCK TRAINING)
# ==========================================
def test_train_and_evaluate():
    # Tạo một mini-dataset đã qua tiền xử lý (Sạch)
    X = pd.DataFrame({
        'area': [50, 60, 70, 80],
        'bedrooms': [2, 3, 3, 4],
        'ward_Hà Cầu': [1, 0, 1, 0]
    })
    y = pd.DataFrame({
        'price_billion': [5, 6, 7, 8],
        'unit_price': [0.1, 0.1, 0.1, 0.1] # Giả sử đơn giá bằng nhau hết
    })

    # Chạy hàm train
    model, mae, features = train_and_evaluate(X, y)

    # Assert model được tạo thành công và MAE được tính ra
    assert model is not None, "Lỗi: Không trả về model"
    assert isinstance(mae, float), "Lỗi: MAE không phải là số"
    assert len(features) == 3, "Lỗi: Đánh mất số lượng features"