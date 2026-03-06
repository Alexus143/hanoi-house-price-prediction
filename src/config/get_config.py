import streamlit as st
import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

def get_config(key):
    # Thử lấy từ Secrets của Streamlit trước (Ưu tiên Cloud)
    if key in st.secrets:
        return st.secrets[key]
    # Nếu không thấy, thử lấy từ biến môi trường hệ thống hoặc .env
    pwd = os.getenv(key)
    if not pwd:
        try:
            from google.colab import userdata
            pwd = userdata.get(key)
        except:
            print(f"Cảnh báo: Không tìm thấy {key}!")
    return pwd