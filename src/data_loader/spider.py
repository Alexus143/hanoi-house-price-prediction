# src/data_loader/spider.py
import time
import random
import pandas as pd
from selenium.webdriver.common.by import By
import sys
import os

# Import modules từ project
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.config.crawler import BASE_URL
from src.config.path import RAW_CSV_PATH
from src.data_loader.browser import init_driver

# Ép Python xuất dữ liệu text ra terminal hoặc file log bằng chuẩn UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def safe_extract(parent_element, selectors, attribute=None):
    """
    Hàm rà quét an toàn: Thử lần lượt các CSS selector.
    Chống vỡ pipeline khi website thay đổi Class CSS.
    """
    for selector in selectors:
        try:
            el = parent_element.find_element(By.CSS_SELECTOR, selector)
            val = el.get_attribute(attribute) if attribute else el.text.strip()
            if val:
                return val
        except:
            continue
    return ""

def extract_card_data(card_element):
    """Hàm bóc tách thông tin từ 1 thẻ HTML sử dụng Wildcard và Fallback"""
    data = {}
    
    # 1. Định danh gốc & URL (Chìa khóa cho luồng Deep Enricher)
    data['prid'] = card_element.get_attribute('prid') or ""
    
    data['url'] = safe_extract(card_element, [
        'a.js__product-link-for-product-id', 
        'a[href*="/ban-"]', 
        'h3 a'
    ], attribute='href')

    # 2. Dữ liệu văn bản (Thử class chuẩn trước, sau đó fallback xuống wildcard)
    data['title'] = safe_extract(card_element, [
        '.js__card-title', 
        'span.pr-title', 
        '[class*="card-title"]', 
        'h3'
    ])
    
    data['description'] = safe_extract(card_element, [
        '.re__card-description', 
        '[class*="card-description"]'
    ])
    
    data['location'] = safe_extract(card_element, [
        '.re__card-location', 
        '[class*="card-location"]'
    ])

    # 3. Các thông số Cấu hình (Config Items)
    data['price'] = safe_extract(card_element, [
        '.re__card-config-price', 
        '[class*="config-price"]', 
        '[class*="price"]'
    ])
    
    data['area'] = safe_extract(card_element, [
        '.re__card-config-area', 
        '[class*="config-area"]', 
        '[class*="area"]'
    ])
    
    # Lấy số phòng ngủ / toilet từ aria-label, nếu không có thì lấy text
    data['bedrooms'] = safe_extract(card_element, [
        '.re__card-config-bedroom', 
        '[class*="config-bedroom"]',
        '[class*="bedroom"]'
    ], attribute='aria-label') or safe_extract(card_element, [
        '.re__card-config-bedroom',
        '[class*="bedroom"]'])

    data['bathrooms'] = safe_extract(card_element, [
        '.re__card-config-bathroom', 
        '[class*="config-bathroom"]',
        '[class*="bathroom"]'
    ], attribute='aria-label') or safe_extract(card_element, [
        '.re__card-config-bathroom',
        '[class*="bathroom"]'])

    # 4. Thời gian (Đổi định dạng scraped_date sang chuẩn SQL YYYY-MM-DD)
    data['scraped_date'] = time.strftime("%Y-%m-%d")
    
    data['published_date'] = safe_extract(card_element, [
        '.re__card-published-info-published-at', 
        '[class*="published-at"]', 
        '[class*="published-info"]'
    ], attribute='aria-label')

    return data

def run_crawler(pages=2, max_retries=3):
    """
    Hàm cào dữ liệu có tích hợp cơ chế Auto-Retry để vượt qua Cloudflare.
    """
    driver = init_driver()
    results = []
    
    try:
        for p in range(1, pages + 1):
            url = BASE_URL if p == 1 else f"{BASE_URL}/p{p}"
            print(f"\n[Spider] Đang cào trang {p}/{pages}: {url}")
            
            for attempt in range(1, max_retries + 1):
                try:
                    if attempt == 1:
                        driver.get(url)
                    else:
                        print(f"[Spider] 🔄 Đang thử tải lại lần {attempt}/{max_retries} cho trang {p}...")
                        driver.refresh()
                    
                    time.sleep(random.uniform(7, 10))
                    
                    # Tìm thẻ cha js__card (Cũng dùng fallback cho chắc chắn)
                    try:
                        cards = driver.find_elements(By.CSS_SELECTOR, '.js__card')
                    except:
                        cards = driver.find_elements(By.CSS_SELECTOR, '[class*="card-full"]')
                    
                    if len(cards) > 0:
                        print(f"[Spider] ✅ Thành công: Tìm thấy {len(cards)} tin đăng ở trang {p}.")
                        for card in cards:
                            data = extract_card_data(card)
                            # Đảm bảo bài đăng có Title và URL hợp lệ mới lưu
                            if data['title'] and data['url']:  
                                results.append(data)
                        break
                        
                    else:
                        print(f"[Spider] ⚠️ Không tìm thấy dữ liệu (Attempt {attempt}). Có thể bị chặn.")
                        if attempt == max_retries:
                            debug_path = os.path.join(os.path.dirname(__file__), f"debug_page_{p}.png")
                            driver.save_screenshot(debug_path)
                            print(f"[Spider] 📸 Đã lưu ảnh debug: {debug_path}")
                        else:
                            time.sleep(5)
                            
                except Exception as e:
                    print(f"[Spider] Lỗi tại trang {p} (Attempt {attempt}): {e}")
                    if attempt == max_retries:
                        break
                    time.sleep(3)
                    
    finally:
        try: 
            driver.quit()
        except Exception: 
            pass
        
    return results

def save_data(data):
    if not data:
        print("[Spider] Không có dữ liệu mới.")
        return

    df_new = pd.DataFrame(data)

    # Nếu file đã tồn tại, ta đọc lên và nối (concat) để KHỚP ĐÚNG TÊN CỘT
    if os.path.exists(RAW_CSV_PATH):
        print("[Spider] Đang gộp dữ liệu mới vào file cũ (Khớp theo tên cột)...")
        try:
            df_old = pd.read_csv(RAW_CSV_PATH, on_bad_lines='skip', engine='python')
            
            # pd.concat tự động so khớp tên cột. 
            # url của mẻ mới sẽ vào đúng cột url, data cũ không có url sẽ thành NaN
            df_combined = pd.concat([df_old, df_new], ignore_index=True)
            
            # Ghi đè lại toàn bộ file với cấu trúc cột đã được chuẩn hóa
            df_combined.to_csv(RAW_CSV_PATH, index=False, encoding='utf-8-sig')
            print(f"[Spider] Đã lưu {len(df_new)} dòng mới. Tổng: {len(df_combined)} dòng.")
        except Exception as e:
            print(f"[Spider] ❌ Lỗi khi gộp file: {e}")
    else:
        # Nếu chưa có file thì tạo mới bình thường
        df_new.to_csv(RAW_CSV_PATH, index=False, encoding='utf-8-sig')
        print(f"[Spider] Đã tạo file mới và lưu {len(df_new)} dòng.")

if __name__ == "__main__":
    data = run_crawler(pages=100)
    save_data(data)