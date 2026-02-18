# src/ai_engine/predictor.py
import pandas as pd

class PricePredictor:
    def __init__(self, model=None, model_columns=None):
        # Nhận trực tiếp model và columns từ app.py truyền sang
        self.model = model
        self.model_columns = model_columns
            
    def predict_single(self, area, ward):
        if self.model is None or self.model_columns is None:
            raise ValueError("Model hoặc Danh sách cột chưa được khởi tạo!")
    
        # 1. Tạo input dataframe
        # Đảm bảo area là kiểu số
        input_data = pd.DataFrame({'area': [float(area)], 'ward': [ward]})
        
        # 2. One-hot encoding
        input_encoded = pd.get_dummies(input_data, columns=['ward'])
        
        # 3. Đồng bộ cột (Sử dụng self.model_columns của class)
        input_encoded = input_encoded.reindex(columns=self.model_columns, fill_value=0)
        
        # 4. Predict
        price_billion = self.model.predict(input_encoded)[0]
        return price_billion