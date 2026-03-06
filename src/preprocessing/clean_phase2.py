import pandas as pd
import numpy as np
import os
import sys
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.postgres_manager import PostgresManager

def categorize_legal_status(status):
    if pd.isna(status): return "Không xác định"
    status = str(status).lower().strip()
    status = re.sub(r'[.\s]+$', '', status)
    so_do_kw = ['sổ', 'sđcc', 'sdcc', 'giấy chứng nhận']
    hop_dong_kw = ['hợp đồng', 'hđ', 'hd', 'giấy tay', 'đặt cọc', '50 năm']
    khac_kw = ['đang cập nhật', 'đang chờ sổ', 'sử dụng chung', 'dùng chung']
    if any(kw in status for kw in khac_kw): return "Khác"
    if any(kw in status for kw in so_do_kw): return "Sổ đỏ"
    if any(kw in status for kw in hop_dong_kw): return "Hợp đồng"
    return "Không xác định"

def categorize_furniture(text):
    if pd.isna(text) or str(text).lower() in ['null', 'nan', 'none', '']:
        return "Không xác định"
    
    t = str(text).lower().strip()

    # 0. Loại trừ các thông tin không liên quan đến nội thất (Noise)
    # Nếu chỉ có thông tin về thang máy, view, hướng mà không nhắc đến đồ đạc
    noise_kw = r'\b(thang máy|view|hướng|ban công|tiện ích|vị trí|pháp lý)\b'
    # Nếu chuỗi ngắn và chỉ chứa từ khóa nhiễu, trả về Không xác định
    if re.search(noise_kw, t) and not re.search(r'\b(nội thất|đồ|full|sổ|giường|tủ|bếp)\b', t):
        if len(t) < 30: # Chỉ áp dụng cho mô tả ngắn để tránh xóa nhầm mô tả dài có cả hai
            return "Không xác định"
    
    # 1. Nhóm Bàn giao thô / Không nội thất
    if re.search(r'\b(thô|không nội thất|nhà trống|bàn giao thô)\b', t):
        return "Không nội thất"
    
    # 2. Nhóm Nội thất đầy đủ (Full)
    # Nếu có từ khóa khẳng định Full hoặc liệt kê rất nhiều đồ rời (tivi, tủ lạnh, máy giặt, sofa)
    full_keywords = r'\b(full|đầy đủ|đủ nội thất|đủ đồ|để lại toàn bộ|hết nội thất|về ở ngay)\b'
    essential_items = ['tivi', 'tủ lạnh', 'máy giặt', 'sofa', 'bàn ăn']
    item_count = sum(1 for item in essential_items if item in t)
    
    if re.search(full_keywords, t) or item_count >= 2:
        return "Nội thất đầy đủ"
    
    # 3. Nhóm Nội thất cơ bản (Liền tường)
    basic_keywords = r'\b(cơ bản|liền tường|gắn tường|cđt|điều hòa|nóng lạnh|tủ bếp|sàn gỗ|trần thạch cao)\b'
    if re.search(basic_keywords, t) or len(t) > 50:
        return "Nội thất cơ bản"
        
    # 4. Nhóm tích cực (Chỉ khi có chữ 'nội thất' đi kèm hoặc không dính noise)
    if re.search(r'\b(đẹp|mới|cao cấp|xịn|nhập khẩu|hoàn thiện)\b', t):
        # Tránh trường hợp "Thang máy đẹp", "View đẹp"
        if re.search(noise_kw, t):
            return "Không xác định"
        else:
            return "Nội thất cơ bản"

    return "Không xác định"

if __name__ == "__main__":
    db = PostgresManager()
    table_name = "bds_hadong"
    df = db.load_dataframe("SELECT * FROM bds_hadong")
    if df is not None and not df.empty:
        df['legal_status'] = df['legal_status'].apply(categorize_legal_status)
        df['furniture'] = df['furniture'].apply(categorize_furniture)
        db.upsert_dataframe(
            df=df,
            table_name=table_name,
            unique_key="listing_id",
            exclude_cols=None
        )
        print("✅ Đã cập nhật cột legal_status và furniture thành công.")
    else:
        print("❌ Không có dữ liệu để xử lý hoặc kết nối DB thất bại.")