# tests/test_cleaner.py
import pytest
import pandas as pd
import numpy as np
import os
import sys

# Đưa src vào path để import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.preprocessing.cleaner import (
    extract_ward, 
    clean_price, 
    determine_property_type, 
    extract_room_number
)

# ==========================================
# TEST 1: LÀM SẠCH VỊ TRÍ (WARD)
# ==========================================
def test_extract_ward():
    # Trường hợp 1: Chuỗi chuẩn có dấu phẩy
    assert extract_ward("Phường Vạn Phúc, Quận Hà Đông, Hà Nội") == "Phường Vạn Phúc"
    # Trường hợp 2: Chuỗi chỉ có tên phường
    assert extract_ward("Yên Nghĩa") == "Yên Nghĩa"
    # Trường hợp 3: Dữ liệu bị NaN
    assert extract_ward(np.nan) == "Khác"

# ==========================================
# TEST 2: LÀM SẠCH VÀ QUY ĐỔI GIÁ (TỶ VNĐ)
# ==========================================
def test_clean_price():
    # Quy đổi "Tỷ"
    assert clean_price("5.5 tỷ") == 5.5
    assert clean_price("10 Tỷ") == 10.0
    
    # Quy đổi "Triệu" về "Tỷ"
    assert clean_price("850 triệu") == 0.85
    assert clean_price("500 Triệu") == 0.5
    
    # Xử lý giá trị rỗng/lỗi
    assert clean_price(np.nan) is None
    assert clean_price("Thỏa thuận") is None

# ==========================================
# TEST 3: PHÂN LOẠI BẤT ĐỘNG SẢN BẰNG NLP (NLP CLASSIFIER)
# ==========================================
def test_determine_property_type():
    # Test Đất nền
    row_dat = {'title': 'Bán lô đất phân lô khu DV', 'description': 'mặt tiền 5m'}
    assert determine_property_type(row_dat) == 'Đất nền'
    
    # Test Chung cư
    row_cc = {'title': 'Bán gấp', 'description': 'căn hộ góc 3PN The Pride'}
    assert determine_property_type(row_cc) == 'Chung cư'
    
    # Test Nhà riêng (Từ khóa tường minh)
    row_nha = {'title': 'Bán biệt thự Văn Quán', 'description': 'nội thất xịn'}
    assert determine_property_type(row_nha) == 'Nhà riêng'
    
    # Test Fallback (Không có từ khóa nào -> Mặc định là Nhà riêng)
    row_empty = {'title': 'Cần bán gấp', 'description': 'Liên hệ chính chủ'}
    assert determine_property_type(row_empty) == 'Nhà riêng'

# ==========================================
# TEST 4: TRÍCH XUẤT SỐ PHÒNG BẰNG REGEX (ROOM EXTRACTOR)
# ==========================================
def test_extract_room_number():
    keywords = ['pn', 'ngủ', 'phòng ngủ']
    
    # Trường hợp 1: Có sẵn dữ liệu cào được chuẩn
    row_clean = {'bedrooms': '4 phòng ngủ', 'property_type': 'Nhà riêng'}
    assert extract_room_number(row_clean, 'bedrooms', keywords) == 4.0
    
    # Trường hợp 2: Đất nền -> Tự động ép về 0 phòng ngủ (Không cần đọc text)
    row_dat = {'title': 'Có 3 pn trên đất', 'property_type': 'Đất nền'}
    assert extract_room_number(row_dat, 'bedrooms', keywords) == 0.0
    
    # Trường hợp 3: Bị thiếu dữ liệu cào, phải bới trong Title bằng Regex
    row_missing = {
        'bedrooms': np.nan, 
        'title': 'Bán nhà 5 tầng có 6 phòng ngủ đẹp', 
        'property_type': 'Nhà riêng'
    }
    assert extract_room_number(row_missing, 'bedrooms', keywords) == 6.0
    
    # Trường hợp 4: Không tìm thấy gì cả -> Trả về NaN để KNN Imputer lo
    row_hopeless = {
        'bedrooms': '', 
        'title': 'Bán nhà mặt phố', 
        'description': 'nhà xây thô chưa chia phòng',
        'property_type': 'Nhà riêng'
    }
    assert np.isnan(extract_room_number(row_hopeless, 'bedrooms', keywords))

# ==========================================
# TEST 5: KIỂM THỬ THUẬT TOÁN HASH MD5 VÀ DROP DUPLICATE
# ==========================================
def test_md5_deduplication():
    import hashlib
    
    # Tạo 2 bài đăng của cò mồi: Khác Title, khác URL, khác Ngày đăng
    # NHƯNG bản chất căn nhà (diện tích, giá, phòng...) là giống hệt nhau
    data = [
        {
            'url': '/link-1', 'title': 'Hạ chào bán gấp nhà Văn Quán', 
            'area': 50, 'ward': 'Văn Quán', 'property_type': 'Nhà riêng', 
            'price_billion': 6.5, 'bedrooms': 4, 'bathrooms': 3
        },
        {
            'url': '/link-2', 'title': 'Chính chủ cần bán nhà Văn Quán', 
            'area': 50, 'ward': 'Văn Quán', 'property_type': 'Nhà riêng', 
            'price_billion': 6.5, 'bedrooms': 4, 'bathrooms': 3
        }
    ]
    df = pd.DataFrame(data)
    
    # Chạy thuật toán băm MD5 kẹp 6 biến như trong cleaner.py
    df['listing_id'] = df.apply(
        lambda row: hashlib.md5(
            f"{row['area']}_{row['ward']}_{row['property_type']}_{row['price_billion']}_{row['bedrooms']}_{row['bathrooms']}".encode('utf-8')
        ).hexdigest(), 
        axis=1
    )
    
    # 1. Khẳng định 2 bài đăng này sinh ra CÙNG MỘT MÃ MD5
    assert df.loc[0, 'listing_id'] == df.loc[1, 'listing_id'], "Thuật toán MD5 không nhận diện được cò mồi spam"
    
    # 2. Khẳng định lệnh drop_duplicates sẽ dọn dẹp sạch sẽ
    df_clean = df.drop_duplicates(subset=['listing_id'], keep='last')
    assert len(df_clean) == 1, "Lỗi: Không loại bỏ được tin trùng lặp"
    assert df_clean.iloc[0]['url'] == '/link-2', "Lỗi: keep='last' không hoạt động đúng"

# ==========================================
# TEST 6: KIỂM THỬ LOGIC LỌC OUTLIERS (BOUNDING BOX & UNIT PRICE)
# ==========================================
def test_outlier_filtering_logic():
    # Mô phỏng lại lõi logic lọc của hàm process_and_save
    data = [
        {'title': 'Nhà chuẩn', 'price_billion': 5.0, 'area': 50.0}, # Hợp lệ (100tr/m2)
        {'title': 'Giá siêu đắt', 'price_billion': 60.0, 'area': 50.0}, # Bị loại do Giá > 50 tỷ (Bounding box)
        {'title': 'Diện tích lỗ hổng', 'price_billion': 2.0, 'area': 10.0}, # Bị loại do Diện tích < 15 m2 (Bounding box)
        {'title': 'Đơn giá ảo', 'price_billion': 2.0, 'area': 500.0}, # Bị loại do Đơn giá = 4tr/m2 < 15tr (Unit Price check)
        {'title': 'Mặt phố VIP ảo', 'price_billion': 40.0, 'area': 20.0}, # Bị loại do Đơn giá = 2 tỷ/m2 > 350tr (Unit Price check)
    ]
    df = pd.DataFrame(data)
    
    # 1. Bounding Box Filter
    df_clean = df[
        df['price_billion'].between(0.5, 50) & 
        df['area'].between(15, 500)
    ]
    
    # 2. Unit Price Filter
    df_clean['unit_price'] = (df_clean['price_billion'] * 1000) / df_clean['area']
    df_clean = df_clean[df_clean['unit_price'].between(15, 350)]
    
    assert len(df_clean) == 1, "Logic lọc Outlier không loại bỏ được các điểm dị biệt"
    assert df_clean.iloc[0]['title'] == 'Nhà chuẩn'

# ==========================================
# TEST 7: KIỂM THỬ LOGIC NGÀY THÁNG (TIME TRAVEL BUG)
# ==========================================
def test_datetime_logic_correction():
    # Cò mồi đôi khi "lách luật" bằng cách hẹn giờ đăng tin ảo trong tương lai.
    # Logic phải ép ngày đăng (published_date) KHÔNG ĐƯỢC lớn hơn ngày cào (scraped_date)
    data = [
        {'scraped_date': '2023-10-20', 'published_date': '2023-10-15'}, # Bình thường
        {'scraped_date': '2023-10-20', 'published_date': '2023-10-25'}, # Lỗi: Ngày đăng nằm ở tương lai!
    ]
    df = pd.DataFrame(data)
    
    df['pub_dt'] = pd.to_datetime(df['published_date'], format='%Y-%m-%d', errors='coerce')
    df['scrape_dt'] = pd.to_datetime(df['scraped_date'], format='%Y-%m-%d', errors='coerce')
    
    # Logic sửa lỗi
    mask_future = df['pub_dt'] > df['scrape_dt']
    df.loc[mask_future, 'published_date'] = df.loc[mask_future, 'scraped_date']
    
    assert df.iloc[0]['published_date'] == '2023-10-15', "Lỗi: Làm hỏng ngày tháng hợp lệ"
    assert df.iloc[1]['published_date'] == '2023-10-20', "Lỗi: Không ép được ngày tương lai về ngày cào hiện tại"