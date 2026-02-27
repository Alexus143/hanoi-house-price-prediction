# tests/test_detail_spider.py
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import urllib.parse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data_loader.detail_spider import extract_specifications

@pytest.fixture(scope="module")
def driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

# ==========================================
# TEST 1: TRÍCH XUẤT KEY-VALUE THÀNH CÔNG
# ==========================================
def test_extract_specifications_happy_path(driver):
    # Giả lập HTML trang chi tiết của Batdongsan
    mock_html = """
    <div class="pr-specs-item">
        <span class="title">Mặt tiền</span>
        <span class="value">5 m</span>
    </div>
    <div class="pr-specs-item">
        <span class="title">Đường vào</span>
        <span class="value">12.5 m</span>
    </div>
    <div class="pr-specs-item">
        <span class="title">Hướng nhà</span>
        <span class="value">Đông-Nam</span>
    </div>
    """
    html_data_uri = "data:text/html;charset=utf-8," + urllib.parse.quote(mock_html)
    driver.get(html_data_uri)

    data = extract_specifications(driver)
    
    # Assert ánh xạ đúng từ điển
    assert data['frontage'] == '5 m', "Lỗi lấy Mặt tiền"
    assert data['road_width'] == '12.5 m', "Lỗi lấy Đường vào"
    assert data['direction'] == 'Đông-Nam', "Lỗi lấy Hướng nhà"
    # Assert các trường không có trong HTML phải trả về None
    assert data['floors'] is None, "Lỗi: Số tầng không có nhưng lại sinh ra data"
    assert data['legal_status'] is None

# ==========================================
# TEST 2: HTML BỊ XỘC XỆCH
# ==========================================
def test_extract_specifications_messy_html(driver):
    # Dùng thẻ <div> bọc lại để mô phỏng việc xuống dòng thực tế trên web
    mock_html = """
    <div class="specs-content-item">
        <div>Số tầng</div>
        <div>4 tầng</div>
    </div>
    <div class="specs-content-item">
        <div>Pháp lý</div>
        <div>Sổ đỏ/ Sổ hồng</div>
    </div>
    """
    html_data_uri = "data:text/html;charset=utf-8," + urllib.parse.quote(mock_html)
    driver.get(html_data_uri)

    data = extract_specifications(driver)
    
    assert data['floors'] == '4 tầng', "Lỗi: Không parse được text gộp Số tầng"
    assert data['legal_status'] == 'Sổ đỏ/ Sổ hồng', "Lỗi: Không parse được text gộp Pháp lý"

# ==========================================
# TEST 3: BÀI ĐĂNG HOÀN TOÀN TRỐNG THÔNG SỐ (NO SPECS)
# ==========================================
def test_extract_empty_specs(driver):
    # Bài đăng rác, không có bất kỳ thẻ cấu hình nào
    mock_html = """
    <div class="description">
        Nhà đẹp bán gấp, liên hệ chính chủ.
    </div>
    """
    html_data_uri = "data:text/html;charset=utf-8," + urllib.parse.quote(mock_html)
    driver.get(html_data_uri)

    data = extract_specifications(driver)
    
    # Phải trả về một dictionary với tất cả các value = None, bot không được crash
    for key, value in data.items():
        assert value is None, f"Lỗi: Cột {key} phải là None vì HTML trống"

# ==========================================
# TEST 4: CHỈ CÓ 1 VÀI THÔNG SỐ (PARTIAL DATA)
# ==========================================
def test_extract_partial_specs(driver):
    mock_html = """
    <div class="pr-specs-item">
        <span class="title">Nội thất</span>
        <span class="value">Cơ bản</span>
    </div>
    """
    html_data_uri = "data:text/html;charset=utf-8," + urllib.parse.quote(mock_html)
    driver.get(html_data_uri)

    data = extract_specifications(driver)
    
    assert data['furniture'] == 'Cơ bản', "Lỗi: Lấy thiếu Nội thất"
    assert data['frontage'] is None, "Lỗi: Mặt tiền phải là None"
    assert data['road_width'] is None, "Lỗi: Đường vào phải là None"