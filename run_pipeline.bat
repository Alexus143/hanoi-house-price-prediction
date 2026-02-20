@echo off
:: Thay đổi đường dẫn này thành thư mục chứa project thực tế trên máy bạn
cd /d "D:\Python\realtime_estimate_tracker"

:: Nếu bạn dùng môi trường ảo (venv/conda), hãy bỏ comment dòng dưới và sửa đường dẫn
call venv_bds\Scripts\activate

echo [1/3] Dang cao du lieu...
python -m src.data_loader.spider

echo [2/3] Dang lam sach du lieu...
python -m src.preprocessing.cleaner

echo [3/3] Dang huan luyen AI...
python -m src.ai_engine.train_model

echo [4/4] Dang dong bo len GitHub...
git add data/*
git commit -m "Auto-update data and model from Local Edge Node"
git push origin main