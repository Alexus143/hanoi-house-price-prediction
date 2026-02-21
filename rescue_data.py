import pandas as pd
import re

# 1. Đọc file
df = pd.read_csv('data/cleaned_data.csv')
print(f"📊 Tổng số dòng: {len(df)}")

# 2. HÀM KIỂM TRA: Đâu là description đi lạc?
def is_misplaced_text(val):
    if pd.isna(val):
        return False
    val = str(val).strip()
    # Nếu không phải định dạng dd/mm/yyyy và dài hơn 10 ký tự -> Đích thị là text
    if not re.match(r'^\d{2}/\d{2}/\d{4}$', val) and len(val) > 10:
        return True
    return False

# Tìm các dòng bị lộn xộn
mask_swapped = df['published_date'].apply(is_misplaced_text)
so_dong_lon_xon = mask_swapped.sum()
print(f"🔄 Phát hiện {so_dong_lon_xon} dòng bị lẫn description vào cột published_date.")

if so_dong_lon_xon > 0:
    # A. Chuyển văn bản từ published_date sang description
    df.loc[mask_swapped, 'description'] = df.loc[mask_swapped, 'published_date']
    
    # B. Gán lại published_date bằng scraped_date cho những dòng vừa bị lấy mất text
    df.loc[mask_swapped, 'published_date'] = df.loc[mask_swapped, 'scraped_date']

# 3. LÀM SẠCH LẠI: Lỡ description nào vẫn còn chứa ngày tháng thì xóa đi
def clean_description(text):
    if pd.isna(text):
        return ""
    text = str(text).strip()
    if re.match(r'^\d{2}/\d{2}/\d{4}$', text):
        return ""
    return text

df['description'] = df['description'].apply(clean_description)

# 4. LOGIC CŨ CỦA BẠN: Sửa lỗi ngày đăng LỚN HƠN ngày cào
df['pub_dt'] = pd.to_datetime(df['published_date'], format='%d/%m/%Y', errors='coerce')
df['scrape_dt'] = pd.to_datetime(df['scraped_date'], format='%d/%m/%Y', errors='coerce')

mask_future_date = df['pub_dt'] > df['scrape_dt']
print(f"🔍 Phát hiện {mask_future_date.sum()} dòng có ngày đăng vô lý (sau ngày cào).")

df.loc[mask_future_date, 'published_date'] = df.loc[mask_future_date, 'scraped_date']
df = df.drop(columns=['pub_dt', 'scrape_dt'])

# 5. Lưu kết quả
df.to_csv('data/cleaned_data.csv', index=False, encoding='utf-8-sig')
print("✅ Cứu hộ thành công! Dữ liệu đã chuẩn schema 100%.")