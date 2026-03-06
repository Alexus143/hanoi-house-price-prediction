import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

import os
from dotenv import load_dotenv

# Load .env nếu chạy ở Local
load_dotenv()

def get_config(key):
    # 1. Thử lấy từ biến môi trường (Ưu tiên số 1: Local .env hoặc System Env)
    val = os.getenv(key)
    if val:
        return val

    # 2. Thử lấy từ Streamlit Secrets (Chỉ chạy khi đang trong môi trường Streamlit)
    try:
        import streamlit as st
        # Kiểm tra xem st.secrets có dữ liệu không để tránh lỗi NotFoundError
        if key in st.secrets:
            return st.secrets[key]
    except (ImportError, Exception):
        # Nếu không có streamlit hoặc lỗi secrets, bỏ qua và đi tiếp
        pass

    # 3. Thử lấy từ Google Colab Userdata (Chỉ chạy khi trên Colab)
    try:
        from google.colab import userdata
        val = userdata.get(key)
        if val:
            return val
    except (ImportError, ModuleNotFoundError, Exception):
        pass

    print(f"⚠️ Cảnh báo: Không tìm thấy cấu hình cho '{key}'")
    return None