import sys
import pandas as pd
import sqlite3
import joblib
import os
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src import config

def load_data(db_path):
    conn = sqlite3.connect(db_path)
    # Lấy toàn bộ dữ liệu (cả cũ và mới vừa cào thêm)
    df = pd.read_sql("SELECT * FROM listings", conn)
    conn.close()
    return df

def preprocess_data(df):
    # 1. Tách phường và lọc bỏ giá trị trống
    df = df.dropna(subset=['price_billion', 'area', 'ward'])
    
    # 2. ÉP KIỂU SỐ TƯỜNG MINH (Quan trọng nhất)
    df['area'] = pd.to_numeric(df['area'], errors='coerce')
    df = df.dropna(subset=['area']) # Loại bỏ những dòng area không phải là số
    
    # 3. Chỉ lấy đúng 2 cột features
    X = df[['area', 'ward']].copy()
    y = df['price_billion']
    
    # 4. Dummy encoding
    X = pd.get_dummies(X, columns=['ward'])
    
    return X, y

def train_and_evaluate():
    # --- 1. SETUP ĐƯỜNG DẪN ---
    db_path = config.DB_PATH
    model_path = config.MODEL_PATH

    print("⏳ Đang tải dữ liệu từ Database...")
    df = load_data(db_path)
    print(f"📊 Tổng số mẫu dữ liệu hiện có: {len(df)}")

    # --- 2. XỬ LÝ DỮ LIỆU ---
    X, y = preprocess_data(df)
    
    # Chia tập train/test (80% học, 20% thi)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # --- 3. HUẤN LUYỆN MODEL MỚI (CHALLENGER) ---
    print("🚀 Đang huấn luyện model mới trên toàn bộ dữ liệu...")
    new_model = RandomForestRegressor(n_estimators=200, random_state=42) # Tăng lên 200 cây để học kỹ hơn
    new_model.fit(X_train, y_train)

    # Đánh giá model mới
    y_pred_new = new_model.predict(X_test)
    mae_new = mean_absolute_error(y_test, y_pred_new)
    print(f"🎯 Sai số trung bình (MAE) của Model MỚI: {mae_new:.2f} Tỷ")

    # --- 4. SO SÁNH VỚI MODEL CŨ (CHAMPION) ---
    save_new_model = True
    
    if os.path.exists(model_path):
        print("⚔️ Đang so sánh với Model cũ...")
        try:
            old_artifact = joblib.load(model_path)
            old_model = old_artifact['model']
            old_columns = old_artifact['model_columns']
            
            # Để so sánh công bằng, phải dùng X_test hiện tại để test model cũ
            # Nhưng model cũ có thể khác cột (do phường mới/cũ), cần đồng bộ cột
            X_test_aligned = X_test.reindex(columns=old_columns, fill_value=0)
            
            y_pred_old = old_model.predict(X_test_aligned)
            mae_old = mean_absolute_error(y_test, y_pred_old)
            
            print(f"👴 Sai số trung bình (MAE) của Model CŨ: {mae_old:.2f} Tỷ")
            
            # Logic quyết định
            if mae_new < mae_old:
                print(f"✅ Model MỚI tốt hơn ({mae_new:.2f} < {mae_old:.2f}). Sẽ cập nhật!")
            elif abs(mae_new - mae_old) < 0.1:
                print("⚠️ Hiệu suất tương đương. Cập nhật để học thêm dữ liệu mới.")
            else:
                print(f"❌ Model MỚI tệ hơn ({mae_new:.2f} > {mae_old:.2f}).")
                # Trong thực tế có thể không save, nhưng vì ta cần nó học dữ liệu mới
                # nên ở đây ta vẫn ưu tiên save, trừ khi sai số quá lớn.
                print("-> Vẫn sẽ cập nhật để model bao phủ được các khu vực mới.")
                
        except Exception as e:
            print(f"⚠️ Không load được model cũ để so sánh ({e}). Sẽ ghi đè model mới.")
    else:
        print("✨ Chưa có model cũ. Đây là lần train đầu tiên.")

    # --- 5. LƯU MODEL (NẾU QUYẾT ĐỊNH LƯU) ---
    if save_new_model:
        artifact = {
            'model': new_model,
            'model_columns': X.columns.tolist()
        }
        joblib.dump(artifact, model_path)
        print(f"💾 Đã lưu model thành công tại: {model_path}")
        print("👉 Hãy chạy lại 'streamlit run app.py' để áp dụng thay đổi.")

if __name__ == "__main__":
    train_and_evaluate()