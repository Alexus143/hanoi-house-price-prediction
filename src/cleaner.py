import pandas as pd
import sqlite3
import os
import numpy as np
from datetime import datetime

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
    # --- XỬ LÝ ĐƯỜNG DẪN THÔNG MINH (QUAN TRỌNG) ---
    # Lấy vị trí của file cleaner.py đang chạy (trong thư mục src)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Lùi lại 1 cấp để ra thư mục dự án (realtime_estimate_tracker)
    project_root = os.path.dirname(current_dir)
    
    # Tạo đường dẫn chuẩn tới file CSV và DB trong thư mục data
    csv_path = os.path.join(project_root, 'data', 'batdongsan_data.csv')
    db_path = os.path.join(project_root, 'data', 'real_estate.db')

    # Kiểm tra file tồn tại
    if not os.path.exists(csv_path):
        print(f"❌ Không tìm thấy file tại: {csv_path}")
        print("Hãy kiểm tra lại tên file trong thư mục data!")
        return

    column_names = [
        'title', 'price', 'area', 'location', 'scraped_date', 'published_date'
    ]
    print(f"Đang đọc dữ liệu từ: {csv_path}")

    try:
        # --- SỬA ĐOẠN NÀY ---
        df = pd.read_csv(
            csv_path,
            header=None,              # không dùng dòng đầu làm header
            names=column_names,    # Nhưng GHI ĐÈ tên cột bằng danh sách mới (đủ 6 cột)
            skiprows=1,              # Bỏ qua dòng đầu tiên (header cũ)
            on_bad_lines='skip',   # Bỏ qua các dòng lỗi quá nặng
            engine='python'        # Dùng engine python mạnh hơn
        )
        # --------------------
        
        print(f"Đã đọc xong! Tổng số dòng thô: {len(df)}")
        
        # Kiểm tra xem cột scraped_date có dữ liệu không
        print("Mẫu dữ liệu scraped_date:", df['scraped_date'].unique()[:5])

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

    print(f"📊 Kết quả: Giữ lại {len(df_clean)}/{len(df)} tin.")

    # --- LỌC TRÙNG LẶP ---
    df_clean = df_clean.drop_duplicates(
        subset=['title', 'price_billion', 'area', 'published_date'], 
        keep='last'
    )

    # --- LƯU DATABASE ---
    conn = sqlite3.connect(db_path)
    df_clean.to_sql('listings', conn, if_exists='replace', index=False)
    conn.close()
    
    print(f"✅ Đã lưu dữ liệu sạch vào: {db_path}")

if __name__ == "__main__":
    process_and_save()