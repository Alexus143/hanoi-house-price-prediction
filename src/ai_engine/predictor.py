# src/ai_engine/predictor.py
import pandas as pd

class PricePredictor:
    def __init__(self, model=None, model_columns=None):
        self.model = model
        self.model_columns = model_columns
            
    # CẬP NHẬT: Thêm tham số đầu vào
    def predict_single(self, area, bedrooms, bathrooms, ward, property_type):
        if self.model is None or self.model_columns is None:
            raise ValueError("Model hoặc Danh sách cột chưa được khởi tạo!")
    
        # 1. Tạo input dataframe với ĐẦY ĐỦ các cột mới
        input_data = pd.DataFrame({
            'area': [float(area)], 
            'bedrooms': [float(bedrooms)],
            'bathrooms': [float(bathrooms)],
            'ward': [ward],
            'property_type': [property_type]
        })
        
        # 2. One-hot encoding cho cả ward và property_type
        input_encoded = pd.get_dummies(input_data, columns=['ward', 'property_type'])
        
        # 3. Đồng bộ cột với mô hình đã huấn luyện
        input_encoded = input_encoded.reindex(columns=self.model_columns, fill_value=0)
        
        # 4. Predict
        price_billion = self.model.predict(input_encoded)[0]
        return price_billion