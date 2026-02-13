import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import json
import pandas as pd
import os 

BASE_URL = 'https://batdongsan.com.vn/nha-dat-ban-ha-dong'
# Một số trang web sẽ chặn bot nên cần header để giả như người dùng
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
}

def crawls(pages):
    driver = uc.Chrome(use_subprocess=True, version_main=139) # chọn phiên bản Chrome phù hợp với máy, ví dụ 139, use_subprocess=True để bot chạy như một tiến trình con
    driver.maximize_window() # Mở rộng cửa sổ trình duyệt để tránh bị ẩn phần tử
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
    file_path = 'realtime_estimate_tracker/data/batdongsan_data.csv'
    header_mode = not os.path.exists(file_path)
    save_to_csv(df, file_path, header_mode)
    print(f"Đã cập nhật thêm {len(df)} dòng mới vào {file_path}")

    