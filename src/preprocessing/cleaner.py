# src/preprocessing/cleaner.py
import pandas as pd
import sqlite3
import os
import numpy as np
import sys
import re
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src import config

# --- HÀM LẤY PHƯỜNG TỪ ĐỊA CHỈ ---
def extract_ward(location_str):
    """Input: "Yên Nghĩa, Hà Đông" -> Output: "Yên Nghĩa" """
    if pd.isna(location_str): return "Khác"
    parts = location_str.split(',') 
    if len(parts) > 1:
        return parts[0].strip()
    return location_str.strip()

def clean_price(price_str):
    """Chuyển đổi giá sang số thực (Tỷ VNĐ)"""
    if pd.isna(price_str): return None
    price_str = str(price_str).lower().replace(',', '.') 
    if "tỷ" in price_str:
        return float(price_str.replace("tỷ", "").strip())
    elif "triệu" in price_str:
        return float(price_str.replace("triệu", "").strip()) / 1000
    return None

def is_misplaced_text(val):
    """Nhận diện description đi lạc vào published_date"""
    if pd.isna(val): return False
    val = str(val).strip()
    # Nếu không phải dd/mm/yyyy và dài hơn 10 ký tự -> Text đi lạc
    if not re.match(r'^\d{2}/\d{2}/\d{4}$', val) and len(val) > 10:
        return True
    return False

def clean_description(text):
    """Xóa các ngày tháng rác bị rơi vào cột description"""
    if pd.isna(text): return ""
    text = str(text).strip()
    if re.match(r'^\d{2}/\d{2}/\d{4}$', text):
        return ""
    return text

def process_and_save():
    if not os.path.exists(config.RAW_CSV_PATH):
        print(f"Không tìm thấy file tại: {config.RAW_CSV_PATH}")
        return

    column_names = ['title', 'price', 'area', 'location', 'scraped_date', 'published_date', 'description']
    print(f"Đang đọc dữ liệu thô...")

    try:
        df = pd.read_csv(
            config.RAW_CSV_PATH, header=None, names=column_names, 
            skiprows=1, on_bad_lines='skip', engine='python'
        )
        # Xóa dòng header rác bị lặp
        df = df[df['title'] != 'title']
        print(f"Tổng số dòng thô: {len(df)}")
    except Exception as e:
        print(f"Lỗi đọc CSV: {e}")
        return

    # --- 1. LÀM SẠCH CƠ BẢN ---
    df['price_billion'] = df['price'].apply(clean_price)
    df['area'] = df['area'].astype(str).str.extract(r'(\d+\.?\d*)').astype(float)
    df['ward'] = df['location'].apply(extract_ward)
    df.replace(r'^\s*$', np.nan, regex=True, inplace=True)

    # --- 2. SELF-HEALING: SỬA LỖI LỘN XỘN CỘT ---
    if 'published_date' in df.columns:
        mask_swapped = df['published_date'].apply(is_misplaced_text)
        if mask_swapped.sum() > 0:
            print(f"🔄 Đang phục hồi {mask_swapped.sum()} dòng bị lẫn text vào published_date...")
            # Chuyển text về đúng chỗ
            df.loc[mask_swapped, 'description'] = df.loc[mask_swapped, 'published_date']
            # Dùng scraped_date trám vào chỗ trống
            df.loc[mask_swapped, 'published_date'] = df.loc[mask_swapped, 'scraped_date']

    if 'description' in df.columns:
        df['description'] = df['description'].apply(clean_description)

    # --- 3. XỬ LÝ NGÀY THÁNG (LOGIC NGHIỆP VỤ) ---
    today_str = datetime.now().strftime("%d/%m/%Y")
    
    # Đảm bảo scraped_date không bị rỗng
    if 'scraped_date' not in df.columns:
        df['scraped_date'] = today_str
    else:
        df['scraped_date'] = df['scraped_date'].fillna(today_str)

    # Đảm bảo published_date không bị rỗng (Trám bằng scraped_date)
    if 'published_date' not in df.columns:
        df['published_date'] = df['scraped_date']
    else:
        df['published_date'] = df['published_date'].fillna(df['scraped_date'])

    # Kiểm tra tính logic: published_date không được LỚN HƠN scraped_date
    df['pub_dt'] = pd.to_datetime(df['published_date'], format='%d/%m/%Y', errors='coerce')
    df['scrape_dt'] = pd.to_datetime(df['scraped_date'], format='%d/%m/%Y', errors='coerce')
    
    mask_future_date = df['pub_dt'] > df['scrape_dt']
    anomalies = mask_future_date.sum()
    if anomalies > 0:
        print(f"⚠️ Phát hiện {anomalies} ngày đăng vô lý. Đang đồng bộ hóa...")
        df.loc[mask_future_date, 'published_date'] = df.loc[mask_future_date, 'scraped_date']
    
    df = df.drop(columns=['pub_dt', 'scrape_dt'])

    # --- 4. LỌC BỎ DỮ LIỆU THIẾU & TRÙNG LẶP ---
    required_features = ['title', 'price_billion', 'area', 'location']
    df_clean = df.dropna(subset=required_features, how='any')
    
    df_clean = df_clean.drop_duplicates(
        subset=['title', 'price_billion', 'area', 'published_date'], 
        keep='last'
    )
    print(f"✅ Kết quả: Giữ lại {len(df_clean)}/{len(df)} tin hợp lệ.")

    # --- 5. LƯU KẾT QUẢ ---
    conn = sqlite3.connect(config.DB_PATH)
    df_clean.to_sql('listings', conn, if_exists='replace', index=False)
    conn.close()
    
    df_clean.to_csv(config.CLEANED_DATA_PATH, index=False, encoding='utf-8-sig')
    print("💾 Đã cập nhật Database và CSV thành công!")

if __name__ == "__main__":
    process_and_save()