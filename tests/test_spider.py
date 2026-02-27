# tests/test_spider.py
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import urllib.parse
import os
import sys

# Lùi lại thư mục gốc để import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data_loader.spider import extract_card_data

@pytest.fixture(scope="module")
def driver():
    """Khởi tạo Headless Browser dùng chung cho tất cả Test Cases"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def load_mock_html(driver, html_content):
    """Hàm helper để load HTML giả lập vào trình duyệt cực nhanh"""
    html_data_uri = "data:text/html;charset=utf-8," + urllib.parse.quote(html_content)
    driver.get(html_data_uri)
    return driver.find_element(By.CSS_SELECTOR, '.js__card')

# ==========================================
# TEST CASE 1: ĐẦY ĐỦ THÔNG TIN (HAPPY PATH)
# ==========================================
def test_extract_full_data(driver):
    mock_html = """
    <div class="js__card" prid="111222">
        <a class="js__product-link-for-product-id" href="/ban-nha-chuan">Link</a>
        <h3 class="js__card-title">Nhà đẹp Hà Đông</h3>
        <span class="re__card-config-price">5 tỷ</span>
        <span class="re__card-config-area">50 m²</span>
        <span class="re__card-config-bedroom" aria-label="3 phòng ngủ"></span>
    </div>
    """
    card = load_mock_html(driver, mock_html)
    data = extract_card_data(card)
    
    assert data['prid'] == "111222"
    assert data['price'] == "5 tỷ"
    assert data['bedrooms'] == "3 phòng ngủ"
    assert data['title'] == "Nhà đẹp Hà Đông"

# ==========================================
# TEST CASE 2: THIẾU DỮ LIỆU (MISSING DATA)
# Đảm bảo bot không bị crash (văng lỗi Exception) khi bài đăng bị trống thông tin
# ==========================================
def test_extract_missing_data(driver):
    mock_html = """
    <div class="js__card" prid="333444">
        <a href="/ban-dat-trong">Link</a>
        <h3 class="js__card-title">Bán đất nền không có nhà</h3>
        </div>
    """
    card = load_mock_html(driver, mock_html)
    data = extract_card_data(card)
    
    assert data['prid'] == "333444"
    assert data['title'] == "Bán đất nền không có nhà"
    # Phải trả về chuỗi rỗng "" chứ không được báo lỗi hay trả về None
    assert data['price'] == "" 
    assert data['area'] == ""
    assert data['bedrooms'] == ""

# ==========================================
# TEST CASE 3: WEBSITE ĐỔI GIAO DIỆN (DEFENSIVE SCRAPING)
# Kiểm tra cơ chế Wildcard (Fallback) khi Batdongsan thay đổi tên Class CSS
# ==========================================
def test_extract_with_changed_css(driver):
    mock_html = """
    <div class="js__card" prid="555666">
        <a href="/ban-biet-thu-moi" class="new-link-style">Link</a>
        
        <div class="new-card-title-header">Biệt thự mới xây</div>
        
        <div class="super-new-price-layout">15 tỷ</div>
        <div class="layout-area-config">120 m²</div>
        <div class="bathroom-info-xyz" aria-label="4 WC"></div>
    </div>
    """
    card = load_mock_html(driver, mock_html)
    data = extract_card_data(card)
    
    assert data['prid'] == "555666"
    assert "ban-biet-thu-moi" in data['url'], "Lỗi fallback URL"
    assert data['title'] == "Biệt thự mới xây", "Lỗi fallback Title"
    assert data['price'] == "15 tỷ", "Lỗi fallback Price"
    assert data['area'] == "120 m²", "Lỗi fallback Area"
    assert data['bathrooms'] == "4 WC", "Lỗi fallback Bathrooms"