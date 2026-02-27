@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

cd /d "D:\Python\realtime_estimate_tracker"
call venv_bds\Scripts\activate

echo [%date% %time%] BAT DAU LUONG FAST >> logs\fast_pipeline.log

python -m src.data_loader.spider >> logs\fast_pipeline.log 2>&1
python -m src.preprocessing.cleaner >> logs\fast_pipeline.log 2>&1

:: Chỉ đẩy Data CSV lên Git
git add data/*
git commit -m "Auto-update Raw Data: %date% %time%" >> logs\fast_pipeline.log 2>&1
git push origin main >> logs\fast_pipeline.log 2>&1

echo [%date% %time%] HOAN THANH LUONG FAST >> logs\fast_pipeline.log