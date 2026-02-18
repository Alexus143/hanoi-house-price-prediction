import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import sys
import time
import pandas as pd
import os 
import random
import subprocess  
import re  
import platform       

BASE_URL = 'https://batdongsan.com.vn/nha-dat-ban-ha-dong'

# --- CẤU HÌNH CHẾ ĐỘ CHẠY ---
# Đặt là False khi chạy trên máy tính của bạn để xem trình duyệt
# Đặt là True khi đẩy lên GitHub Actions
CHAY_NGAM = True 

def get_chrome_version():
    """
    Hàm tự động dò tìm phiên bản Chrome trên cả Windows và Linux
    Trả về số phiên bản chính (Ví dụ: 139)
    """
    system_name = platform.system()
    version = None

    try:
        if system_name == "Windows":
            # Cách 1: Thử truy vấn Registry (Nhanh và chuẩn nhất trên Windows)
            try:
                # Lệnh cmd để đọc Registry key nơi Chrome lưu version
                process = subprocess.Popen(
                    ['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', '/v', 'version'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
                )
                output, _ = process.communicate()
                output = output.decode()
                # Parse kết quả: ... version REG_SZ 139.0.xxxx ...
                match = re.search(r'version\s+REG_SZ\s+(\d+)', output)
                if match:
                    version = int(match.group(1))
            except:
                pass

        elif system_name == "Linux":
            # Cách 2: Chạy lệnh terminal trên Linux (cho GitHub Actions)
            try:
                cmd_list = ['google-chrome', 'google-chrome-stable', 'chromium-browser', 'chromium']
                for cmd in cmd_list:
                    try:
                        result = subprocess.run([cmd, '--version'], capture_output=True, text=True)
                        if result.returncode == 0:
                            output = result.stdout.strip()
                            # Output dạng: "Google Chrome 144.0.7559.0"
                            match = re.search(r'(\d+)\.\d+\.\d+\.\d+', output)
                            if match:
                                version = int(match.group(1))
                                break
                    except FileNotFoundError:
                        continue
            except:
                pass
                
    except Exception as e:
        print(f"⚠️ Không dò được version Chrome: {e}")

    if version:
        print(f"🖥️ Phát hiện Chrome ({system_name}): Version {version}")
    else:
        print(f"⚠️ Không tìm thấy Chrome trên {system_name}. Sẽ để thư viện tự quyết định.")
        
    return version

def init_driver():
    chrome_options = uc.ChromeOptions()
    
    #Các tùy chọn chống phát hiện Bot
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    target_version = get_chrome_version()  # Tự động lấy version Chrome đang cài trên máy

    # Khởi tạo Driver
    driver = uc.Chrome(options=chrome_options, 
                       headless=CHAY_NGAM, 
                       version_main=target_version,
                       use_subprocess=True)
    
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
            try:
                driver.get(url) # Lúc này nó sẽ vào đúng trang web chứ không bị lỗi DNS nữa
            except Exception as e:
                print(f"Lỗi load trang: {e}")
                continue
            # Random delay để giống người thật hơn (từ 3 đến 6 giây)
            time.sleep(random.uniform(3, 6))
            lst_bds = driver.find_elements(By.CSS_SELECTOR, '.js__card')
            for bds in lst_bds:
                try:
                    # Lấy các thông tin cơ bản (Dùng try-except cho từng trường để tránh lỗi vặt)
                    try: title = bds.find_element(By.CSS_SELECTOR, '.js__card-title').text
                    except: title = ""
                    
                    try: price = bds.find_element(By.CSS_SELECTOR, '.re__card-config-price').text
                    except: price = ""
                    
                    try: area = bds.find_element(By.CSS_SELECTOR, '.re__card-config-area').text
                    except: area = ""
                    
                    try: location = bds.find_element(By.CSS_SELECTOR, '.re__card-location').text
                    except: location = ""
                    
                    try: date = bds.find_element(By.CSS_SELECTOR, '.re__card-published-info-published-at').get_attribute('aria-label')
                    except: date = ""
                    
                    # LẤY MÔ TẢ (DESCRIPTION)
                    try: description = bds.find_element(By.CSS_SELECTOR, '.re__card-description').text
                    except: description = ""

                    # Chỉ lấy tin có tiêu đề
                    if title:
                        res.append({
                            'title': title,
                            'price': price,
                            'area': area,
                            'location': location,
                            'scraped_date': time.strftime("%d/%m/%Y"),
                            'published_date': date,
                            'description': description
                        })
                except Exception as e:
                    continue
    except Exception as e:
        print(f"Lỗi khi crawl dữ liệu: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass # Nếu driver đã chết thì bỏ qua

    return res

def save_to_csv(data, filename, header_mode=True):
    if not data:
        print("Không cào được dữ liệu nào!")
        return
    
    df = pd.DataFrame(data)

    df.to_csv(filename, mode='a', index=False, header=header_mode, encoding='utf-8-sig')
    print(f"Dữ liệu đã được lưu vào {filename}")

if __name__ == "__main__":
    df = crawls(pages=2)

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

    