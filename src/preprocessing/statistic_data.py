import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.postgres_manager import PostgresManager
def load_data_from_db():
    print("🔄 Đang lấy dữ liệu từ PostgreSQL...")
    db = PostgresManager()
    query = """
        SELECT price_billion, area, ward, property_type, bedrooms, bathrooms,
               frontage, road_width, direction, floors, legal_status, furniture
        FROM bds_hadong 
        WHERE price_billion IS NOT NULL AND area IS NOT NULL
    """
    df = db.load_dataframe(query)
    print(f"✅ Đã tải {len(df)} bản ghi để phân tích thống kê.")
    return df

def analyze_statistics(df):
    print("📊 Phân tích thống kê cơ bản về dữ liệu...")
    
    # Thống kê mô tả cho các cột số
    numeric_cols = ['price_billion', 'area', 'frontage', 'road_width', 'floors']
    print("\n--- Thống kê mô tả cho các cột số ---")
    print(df[numeric_cols].describe())
    
    # Phân phối giá theo loại bất động sản
    plt.figure(figsize=(10, 6))
    df.boxplot(column='price_billion', by='property_type')
    plt.title('Phân phối giá theo loại bất động sản')
    plt.suptitle('')
    plt.xlabel('Loại bất động sản')
    plt.ylabel('Giá (Tỷ VNĐ)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
    # Tỷ lệ phân bổ theo phường
    plt.figure(figsize=(10, 6))
    df['ward'].value_counts().plot(kind='bar')
    plt.title('Số lượng bất động sản theo phường')
    plt.xlabel('Phường')
    plt.ylabel('Số lượng')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    df = load_data_from_db()
    analyze_statistics(df)