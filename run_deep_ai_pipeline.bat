@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

cd /d "D:\Python\realtime_estimate_tracker"
call venv_bds\Scripts\activate

echo [%date% %time%] BAT DAU LUONG DEEP & AI >> logs\deep_pipeline.log

:: Đi cào mặt tiền, đường vào...
python -m src.data_loader.detail_spider >> logs\deep_pipeline.log 2>&1

:: Train lại AI với 6 feature mới
python -m src.ai_engine.train_model >> logs\deep_pipeline.log 2>&1

:: Đẩy Model AI (qua Git LFS) lên Git
git add .gitattributes models/*
git commit -m "Auto-update AI Model: %date% %time%" >> logs\deep_pipeline.log 2>&1
git push origin main >> logs\deep_pipeline.log 2>&1

echo [%date% %time%] HOAN THANH LUONG DEEP & AI >> logs\deep_pipeline.log