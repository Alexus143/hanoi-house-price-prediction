import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import sys
import time
import pandas as pd
import os 

BASE_URL = 'https://batdongsan.com.vn/nha-dat-ban-ha-dong'

# --- CẤU HÌNH CHẾ ĐỘ CHẠY ---
# Đặt là False khi chạy trên máy tính của bạn để xem trình duyệt
# Đặt là True khi đẩy lên GitHub Actions
CHAY_NGAM = True  

def init_driver():
    chrome_options = Options()
    
    # 1. Thêm User-Agent (CỰC KỲ QUAN TRỌNG)
    # Giả mạo đây là trình duyệt Chrome thật trên Windows 10
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # 2. Các tùy chọn chống phát hiện Bot
    chrome_options.add_argument("--disable-blink-features=AutomationControlled") # Ẩn dòng "Chrome is being controlled by automated software"
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # 3. Cấu hình Chạy Ngầm (Headless)
    if CHAY_NGAM:
        chrome_options.add_argument("--headless=new") # Dùng chế độ new headless ổn định hơn
        chrome_options.add_argument("--window-size=1920,1080") # Bắt buộc set size nếu không web sẽ bị vỡ layout
    
    # Khởi tạo Driver
    driver = webdriver.Chrome(options=chrome_options)
    
    # Mẹo nhỏ: Xóa thuộc tính navigator.webdriver để tránh bị phát hiện
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def crawls(pages):
    driver = init_driver() 
    #driver.maximize_window() # Mở rộng cửa sổ trình duyệt để tránh bị ẩn phần tử
    res = []
    try:
        for p in range(1, pages + 1): # Duyệt qua các trang
            if p == 1:
                url = BASE_URL
            else:
                url = f"{BASE_URL}/p{p}"
            driver.get(url)
            time.sleep(5)  # Chờ trang load hoàn toàn
            lst_bds = driver.find_elements(By.CSS_SELECTOR, '.js__card')
            for bds in lst_bds:
                title = bds.find_element(By.CSS_SELECTOR, '.js__card-title').text
                #print(title)
                price = bds.find_element(By.CSS_SELECTOR, '.re__card-config-price').text
                area = bds.find_element(By.CSS_SELECTOR, '.re__card-config-area').text
                #bedroom = bds.find_element(By.CSS_SELECTOR, '.re__card-config-bedroom').text
                #toilet = bds.find_element(By.CSS_SELECTOR, '.re__card-config-toilet').text
                location = bds.find_element(By.CSS_SELECTOR, '.re__card-location').text
                date = bds.find_element(By.CSS_SELECTOR, '.re__card-published-info-published-at').get_attribute('aria-label')
                res.append({
                    'title': title,
                    'price': price,
                    'area': area,
                    #'bedroom': bedroom,
                    #'toilet': toilet,
                    'location': location,
                    'scraped_date': time.strftime("%d/%m/%Y"),
                    'published_date': date
                })
    except Exception as e:
        print(f"Lỗi khi crawl dữ liệu: {e}")
    finally:
        driver.quit()

    return res

def save_to_csv(data, filename, header_mode=True):
    df = pd.DataFrame(data)
    df.to_csv(filename, mode='a', index=False, header=header_mode, encoding='utf-8-sig')
    print(f"Dữ liệu đã được lưu vào {filename}")

if __name__ == "__main__":
    df = crawls(pages=100)

    current_dir = os.path.dirname(os.path.abspath(__file__)) # Đang ở trong src/
    project_root = os.path.dirname(current_dir)              # Lùi ra ngoài 1 cấp (Root)
    data_dir = os.path.join(project_root, 'data')            # Trỏ vào thư mục data

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Đã tạo mới thư mục: {data_dir}")

    #Định nghĩa đường dẫn file cuối cùng
    csv_path = os.path.join(data_dir, 'batdongsan_data.csv')

    header_mode = not os.path.exists(csv_path)
    save_to_csv(df, csv_path, header_mode)
    print(f"Đã cập nhật thêm {len(df)} dòng mới vào {csv_path}")

    