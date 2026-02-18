# src/config.py
import os

# --- CẤU HÌNH CRAWLER ---
BASE_URL = 'https://batdongsan.com.vn/nha-dat-ban-ha-dong'
IS_GITHUB_ACTION = os.getenv("GITHUB_ACTIONS") == "true"

# --- CẤU HÌNH ĐƯỜNG DẪN ---
# Lấy đường dẫn gốc của project
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(ROOT_DIR, 'data')

# File paths
RAW_CSV_PATH = os.path.join(DATA_DIR, 'batdongsan_data.csv')
CLEANED_DATA_PATH = os.path.join(DATA_DIR, 'cleaned_data.csv')
MODEL_PATH = os.path.join(DATA_DIR, 'house_price_model.pkl')

# Đảm bảo thư mục data tồn tại
os.makedirs(DATA_DIR, exist_ok=True)