@echo off
setlocal
:: Thay đổi bảng mã của cmd sang UTF-8
chcp 65001 >nul
:: Ép Python sử dụng UTF-8 khi in dữ liệu ra file log
set PYTHONIOENCODING=utf-8
:: Chạy ở chế độ non-interactive (run ẩn) nên không cho Git hỏi username/password qua prompt.
set GIT_TERMINAL_PROMPT=0

cd /d "D:\Python\realtime_estimate_tracker"
call venv_bds\Scripts\activate

:: Tạo thư mục log nếu chưa có
if not exist logs mkdir logs

:: Ghi timestamp bắt đầu
echo ========================================= >> logs\fast_pipeline.log
echo [%date% %time%] BAT DAU LUONG FAST (QUET BE MAT) >> logs\fast_pipeline.log

:: === BƯỚC 1: CRAWL BỀ MẶT ===
echo [%date% %time%] [1/3] Dang cao du lieu be mat... >> logs\fast_pipeline.log
python -m src.data_loader.spider >> logs\fast_pipeline.log 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] LOI: Spider that bai. Dung pipeline. >> logs\fast_pipeline.log
    goto :error
)

:: === BƯỚC 2: CLEAN & UPSERT DATABASE ===
echo [%date% %time%] [2/3] Dang lam sach va day vao PostgreSQL... >> logs\fast_pipeline.log
python -m src.preprocessing.cleaner >> logs\fast_pipeline.log 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] LOI: Cleaner that bai. Dung pipeline. >> logs\fast_pipeline.log
    goto :error
)

:: === BƯỚC 3: GIT PUSH ===
echo [%date% %time%] [3/3] Dang dong bo Data len GitHub... >> logs\fast_pipeline.log
git add data/* logs/*
if %errorlevel% neq 0 (
    echo [%date% %time%] LOI: git add that bai. >> logs\fast_pipeline.log
    goto :error
)

git diff --cached --quiet
if %errorlevel% equ 0 (
    echo [%date% %time%] Khong co thay doi moi de commit/push. >> logs\fast_pipeline.log
    goto :success
)

git commit -m "Auto-update Fast Pipeline: %date% %time%" >> logs\fast_pipeline.log 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] LOI: git commit that bai. >> logs\fast_pipeline.log
    goto :error
)

git push origin main >> logs\fast_pipeline.log 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] LOI: git push that bai. >> logs\fast_pipeline.log
    goto :error
)

:success
echo [%date% %time%] HOAN THANH LUONG FAST >> logs\fast_pipeline.log
goto :eof

:error
echo [%date% %time%] LUONG FAST BI DUNG DO LOI >> logs\fast_pipeline.log
exit /b 1