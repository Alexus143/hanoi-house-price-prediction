# tests/test_postgres_manager.py
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.postgres_manager import PostgresManager

# ==========================================
# TEST 1: KIỂM TRA LOGIC UPSERT & EXCLUDE COLS
# ==========================================
# Dùng @patch để làm giả hàm create_engine, không cho nó kết nối DB thật
@patch('src.database.postgres_manager.create_engine')
def test_upsert_dataframe_exclude_cols(mock_create_engine):
    # 1. Arrange: Chuẩn bị môi trường Mock
    db = PostgresManager()
    mock_conn = MagicMock() # Tạo một kết nối giả
    db.engine.begin.return_value.__enter__.return_value = mock_conn

    # Tạo DataFrame giả lập từ Luồng 1 (Không có mặt tiền)
    df = pd.DataFrame({
        'listing_id': ['md5_test_123'],
        'price_billion': [5.5],
        'frontage': [None] # Giá trị này có thể ghi đè mất data của Luồng 2 nếu UPSERT sai
    })

    # 2. Action: Thực hiện Upsert với lệnh cấm đè 'frontage'
    db.upsert_dataframe(df, 'listings', 'listing_id', exclude_cols=['frontage'])

    # 3. Assert: Phân tích CÂU LỆNH SQL ĐỘNG
    execute_calls = mock_conn.execute.call_args_list
    
    # Duyệt qua toàn bộ các lệnh SQL đã được gọi để tìm lệnh UPSERT
    upsert_query = ""
    for call in execute_calls:
        query_text = str(call[0][0]) # Ép kiểu query object thành string
        if "ON CONFLICT" in query_text:
            upsert_query = query_text
            break
            
    assert upsert_query != "", "Lỗi: Hệ thống không sinh ra câu lệnh UPSERT nào!"
    assert 'ON CONFLICT ("listing_id")' in upsert_query, "Lỗi: Thiếu logic ON CONFLICT"
    assert '"price_billion" = EXCLUDED."price_billion"' in upsert_query, "Lỗi: Không update các cột thông thường"
    assert '"frontage" = EXCLUDED."frontage"' not in upsert_query, "Nguy hiểm: Cột frontage bị ghi đè!"

# ==========================================
# TEST 2: KIỂM TRA LOGIC UPDATE TỪ DETAIL SPIDER
# ==========================================
@patch('src.database.postgres_manager.create_engine')
def test_update_listing_details(mock_create_engine):
    db = PostgresManager()
    mock_conn = MagicMock()
    db.engine.begin.return_value.__enter__.return_value = mock_conn

    # Data thu được từ Luồng 2
    enriched_data = {
        'listing_id': 'md5_test_999',
        'frontage': '5m',
        'road_width': '10m'
    }

    db.update_listing_details('listings', enriched_data)

    execute_calls = mock_conn.execute.call_args_list
    update_query = execute_calls[0][0][0].text
    params = execute_calls[0][0][1] # Lấy dictionary chứa tham số truyền vào SQL

    # Kiểm tra cấu trúc câu lệnh UPDATE an toàn (Parameterized Query)
    assert 'UPDATE "listings"' in update_query
    assert '"frontage" = :frontage' in update_query, "Lỗi: Cấu trúc mapping tham số frontage bị sai"
    assert '"road_width" = :road_width' in update_query
    assert 'WHERE listing_id = :listing_id' in update_query
    
    # Kiểm tra cờ is_enriched đã được tự động lật lên True chưa
    assert params['is_enriched'] is True, "Lỗi: Quên lật cờ is_enriched = True sau khi update"
    assert params['listing_id'] == 'md5_test_999'

# ==========================================
# TEST 4: TỰ ĐỘNG THIẾT LẬP PRIMARY KEY
# ==========================================
@patch('src.database.postgres_manager.create_engine')
def test_ensure_primary_key(mock_create_engine):
    db = PostgresManager()
    mock_conn = MagicMock()
    db.engine.begin.return_value.__enter__.return_value = mock_conn
    
    # Giả lập DB trả về rỗng (nghĩa là chưa có Primary Key)
    mock_conn.execute.return_value.fetchone.return_value = None
    
    # Gọi hàm (giả sử bạn đã thêm hàm này vào PostgresManager như hướng dẫn trước)
    if hasattr(db, 'ensure_primary_key'):
        db.ensure_primary_key('listings', 'listing_id')
        
        execute_calls = mock_conn.execute.call_args_list
        assert len(execute_calls) >= 2, "Phải có lệnh SELECT check và lệnh ALTER TABLE"
        
        alter_query = str(execute_calls[1][0][0])
        assert 'ALTER TABLE "listings"' in alter_query
        assert 'ADD PRIMARY KEY ("listing_id")' in alter_query

# ==========================================
# TEST 5: MẤT KẾT NỐI DB (DB OFFLINE)
# ==========================================
def test_db_connection_failure():
    # Cố tình truyền URI sai để ép lỗi kết nối
    with patch('src.database.postgres_manager.POSTGRES_URI', 'postgresql://wrong:pass@localhost/fake'):
        # Thay vì crash cả pipeline, hệ thống phải gán engine = None một cách an toàn
        db = PostgresManager()
        
        # Gọi upsert khi không có engine
        df = pd.DataFrame({'listing_id': ['123']})
        # Hàm phải return ngay lập tức, không raise Exception làm chết chương trình
        db.upsert_dataframe(df, 'listings', 'listing_id')