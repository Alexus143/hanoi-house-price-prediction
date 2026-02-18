import pandas as pd
import sqlite3
import os
import numpy as np
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src import config

# --- HÀM LẤY PHƯỜNG TỪ ĐỊA CHỈ ---
def extract_ward(location_str):
    """
    Input: "Yên Nghĩa, Hà Đông"
    Output: "Yên Nghĩa"
    """
    if pd.isna(location_str): return "Khác"
    # Tách bằng dấu phẩy, lấy phần đầu tiên
    parts = location_str.split(',') 
    if len(parts) > 1:
        return parts[0].strip() # Lấy phần trước dấu phẩy
    return location_str.strip()

def clean_price(price_str):
    """Chuyển đổi giá sang số thực (Tỷ VNĐ)"""
    if pd.isna(price_str): return None
    price_str = str(price_str).lower()
    # Ví dụ: "8,6 tỷ" -> "8.6 tỷ" để Python hiểu được
    price_str = price_str.replace(',', '.') 

    if "tỷ" in price_str:
        return float(price_str.replace("tỷ", "").strip())
    elif "triệu" in price_str:
        return float(price_str.replace("triệu", "").strip()) / 1000
        
    return None

def process_and_save():

    # Kiểm tra file tồn tại
    if not os.path.exists(config.RAW_CSV_PATH):
        print(f"Không tìm thấy file tại: {config.RAW_CSV_PATH}")
        print("Hãy kiểm tra lại tên file trong thư mục data!")
        return

    column_names = [
        'title', 'price', 'area', 'location', 'scraped_date', 'published_date', 'description'
    ]
    print(f"Đang đọc dữ liệu từ: {config.RAW_CSV_PATH}")

    try:
        # --- SỬA ĐOẠN NÀY ---
        df = pd.read_csv(
            config.RAW_CSV_PATH,
            header=None,              # không dùng dòng đầu làm header
            names=column_names,    # Nhưng GHI ĐÈ tên cột bằng danh sách mới (đủ 6 cột)
            skiprows=1,              # Bỏ qua dòng đầu tiên (header cũ)
            on_bad_lines='skip',   # Bỏ qua các dòng lỗi quá nặng
            engine='python'        # Dùng engine python mạnh hơn
        )
        # --------------------
        # --- LỌC RÁC HEADER ---
        # Vì file CSV được append liên tục, có thể header bị lặp lại ở giữa file
        # Cần xóa các dòng mà 'title' lại bằng chính chữ 'title'
        df = df[df['title'] != 'title']
        print(f"Đã đọc xong! Tổng số dòng thô: {len(df)}")

    except Exception as e:
        print(f"Lỗi đọc CSV: {e}")
        return

    # --- LÀM SẠCH DỮ LIỆU ---
    df['price_billion'] = df['price'].apply(clean_price)
    df['area'] = df['area'].astype(str).str.extract(r'(\d+\.?\d*)').astype(float)

    # --- TẠO CỘT PHƯỜNG ---
    df['ward'] = df['location'].apply(extract_ward)
    
    # Coi chuỗi rỗng là NaN
    df.replace(r'^\s*$', np.nan, regex=True, inplace=True)

    # --- XỬ LÝ NGÀY THÁNG (FIX LỖI THIẾU SCRAPED_DATE) ---
    # Nếu chưa cào scraped_date, ta lấy ngày hôm nay để điền vào
    today_str = datetime.now().strftime("%d/%m/%Y")
    
    # Nếu cột published_date bị thiếu, điền ngày hôm nay vào
    if 'published_date' in df.columns:
        df['published_date'] = df['published_date'].fillna(today_str)
    else:
        # Trường hợp file csv chưa có cột này luôn (do code cũ)
        df['published_date'] = today_str

    # --- LỌC BỎ DỮ LIỆU THIẾU ---
    # Chỉ bắt buộc có: Tiêu đề, Giá, Diện tích, Địa điểm
    required_features = ['title', 'price_billion', 'area', 'location']
    
    # Xóa các dòng thiếu 1 trong các thông tin trên
    df_clean = df.dropna(subset=required_features, how='any')

    print(f"Kết quả: Giữ lại {len(df_clean)}/{len(df)} tin.")

    # --- LỌC TRÙNG LẶP ---
    df_clean = df_clean.drop_duplicates(
        subset=['title', 'price_billion', 'area', 'published_date'], 
        keep='last'
    )

    # --- LƯU DATABASE ---
    conn = sqlite3.connect(config.DB_PATH)
    df_clean.to_sql('listings', conn, if_exists='replace', index=False)
    conn.close()
    
    print(f"Đã lưu dữ liệu sạch vào: {config.DB_PATH}")

    df_clean.to_csv(config.CLEANED_DATA_PATH, index=False, encoding='utf-8-sig')
    print(f"Đã lưu dữ liệu sạch vào: {config.CLEANED_DATA_PATH}")

if __name__ == "__main__":
    process_and_save()