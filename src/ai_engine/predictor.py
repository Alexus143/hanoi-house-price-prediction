# src/ai_engine/predictor.py
import pandas as pd
import pickle

class PricePredictor:
    def __init__(self, model_path):
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
            
    def predict_single(self, area, ward, model_columns):
    
        # 1. Tạo input dataframe
        input_data = pd.DataFrame({'area': [area], 'ward': [ward]})
        
        # 2. One-hot encoding & Align columns 
        input_encoded = pd.get_dummies(input_data, columns=['ward'])
        input_encoded = input_encoded.reindex(columns=model_columns, fill_value=0)
        
        # 3. Predict
        price_billion = self.model.predict(input_encoded)[0]
        return price_billion