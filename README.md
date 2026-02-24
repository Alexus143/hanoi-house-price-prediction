# 🏡 Hệ Thống Phân Tích & Định Giá Bất Động Sản Hà Đông

Dự án là một hệ thống dữ liệu end-to-end (ETL Pipeline & Machine Learning) nhằm mục đích thu thập, làm sạch, phân tích và dự đoán giá bất động sản tại khu vực Hà Đông. Hệ thống sử dụng **PostgreSQL** làm cơ sở dữ liệu trung tâm, tích hợp cơ chế tự động hóa qua **Windows Task Scheduler**, và cung cấp giao diện tương tác trực quan qua Streamlit kết hợp với Trợ lý AI Gemini.

## 🏗️ Kiến trúc Hệ thống & Luồng Dữ liệu

Dự án được phân tách thành các module độc lập, quản lý luồng dữ liệu chuyên nghiệp:

1. **Data Extraction (Thu thập):** Cào dữ liệu tự động định kỳ bằng Selenium (headless) và lưu thô thành CSV.
2. **Preprocessing & ETL (Tiền xử lý):** Module `cleaner.py` làm sạch văn bản, áp dụng các quy tắc nghiệp vụ khắt khe, tạo định danh duy nhất (MD5 Hash) và đồng bộ vào PostgreSQL qua cơ chế **Upsert**.
3. **AI Engine (Định giá & Huấn luyện):** Module `train_model.py` load dữ liệu từ Database, tự động tinh chỉnh siêu tham số (Hyperparameter Tuning) và đánh giá mô hình bằng kỹ thuật Champion-Challenger.
4. **User Interface (Giao diện):** Streamlit App (`app.py`) truy xuất dữ liệu từ PostgreSQL có sử dụng bộ nhớ đệm (Cache), hiển thị biểu đồ phân tích và tích hợp Chatbot AI tư vấn.

## 🛠️ Tech Stack

* **Ngôn ngữ:** Python 3.x
* **Cơ sở dữ liệu (Database):** PostgreSQL (Giao tiếp qua `PostgresManager` & `psycopg2`)
* **Xử lý Dữ liệu (Data Manipulation):** Pandas, Numpy, Regex, Hashlib
* **Machine Learning:** Scikit-Learn (`RandomForestRegressor`, `GridSearchCV`)
* **Giao diện Web (UI):** Streamlit, Streamlit-Float
* **Tích hợp AI:** Gemini API (Chatbot tư vấn)
* **Tự động hóa (Automation):** Windows Task Scheduler

## 📂 Cấu trúc Thư mục

```text
├── app.py                            # Khởi chạy giao diện Streamlit UI & cấu hình Cache
├── src/
│   ├── config/
│   │   ├── crawler.py                # Tham số cho Spider/Crawler
│   │   ├── database.py               # Cấu hình kết nối PostgreSQL
│   │   └── path.py                   # Quản lý đường dẫn file tập trung
│   ├── data_loader/
│   │   ├── browser.py                # Khởi tạo Selenium Driver
│   │   └── spider.py                 # Crawler bóc tách dữ liệu
│   ├── database/
│   │   └── postgres_manager.py       # Tương tác DB, xử lý Upsert dữ liệu
│   ├── preprocessing/
│   │   └── cleaner.py                # Pipeline ETL, làm sạch dữ liệu & Regex
│   ├── ai_engine/
│   │   ├── train_model.py            # Huấn luyện mô hình, Champion-Challenger evaluation
│   │   ├── predictor.py              # Xử lý luồng dự đoán giá
│   │   └── chatbot.py                # Render Chatbot với Gemini API
│   └── ui/
│       ├── dashboard.py              # Giao diện biểu đồ thống kê
│       └── prediction.py             # Giao diện nhập liệu định giá
├── data/                             # Chứa dữ liệu thô (.csv) và file mô hình (.pkl)
├── requirements.txt
└── README.md

```

## 🧠 Core Modules & Nghiệp Vụ Xử Lý

### 1. Module `cleaner.py` (ETL & NLP)

* **Quy tắc Nghiệp vụ Bắt buộc:** Hệ thống tự động phân loại bất động sản. Nếu `property_type` là "Đất nền", thuật toán ép buộc gán số lượng phòng ngủ/phòng tắm bằng `0` để không gây nhiễu cho mô hình.
* **Trích xuất Đặc trưng (Feature Extraction):** Sử dụng Regex để đọc hiểu "ngôn ngữ môi giới" (vd: "3pn", "2wc") từ tiêu đề và mô tả nếu dữ liệu cào bị thiếu.
* **Cơ chế Upsert Thông minh:** Tạo mã `listing_id` duy nhất bằng thuật toán mã hóa `hashlib.md5` dựa trên tiêu đề, diện tích và ngày đăng. Chỉ cập nhật (Upsert) dữ liệu vào PostgreSQL nếu có thay đổi, tránh duplicate hoàn toàn.

### 2. Module `train_model.py` (AI Engine)

* **Thuật toán:** Sử dụng `RandomForestRegressor` kết hợp `GridSearchCV` (với K-Fold CV = 3) để tự động tìm ra các siêu tham số (`n_estimators`, `max_depth`, `min_samples_split`) tối ưu nhất.
* **Cơ chế Champion - Challenger:** Mỗi khi hệ thống chạy lại pipeline huấn luyện, mô hình mới (Challenger) sẽ được so sánh độ sai số MAE (Mean Absolute Error) với mô hình hiện tại đang dùng (Champion). File `house_price_model.pkl` **chỉ bị ghi đè** nếu Challenger chiến thắng (MAE thấp hơn).

### 3. Tối ưu Hiệu năng UI (`app.py`)

* Sử dụng decorator `@st.cache_data(ttl=3600)` để lưu bộ nhớ đệm kết quả Query từ PostgreSQL trong 1 giờ. Đảm bảo Dashboard load tức thì mà không gây nghẽn kết nối Database.

## 🚀 Hướng Dẫn Cài Đặt & Vận Hành

### Bước 1: Khởi tạo Môi trường

```bash
git clone https://github.com/Alexus143/hanoi-house-price-prediction.git
cd hanoi-house-price-prediction
pip install -r requirements.txt

```

### Bước 2: Cấu hình PostgreSQL & API Key

1. **Database:** Mở file `src/config/database.py` và cập nhật thông số kết nối PostgreSQL (Host, Port, User, Password, DB Name). Mọi truy vấn DB trong dự án bắt buộc phải thông qua lớp `PostgresManager`.
2. **Gemini API:** Tạo thư mục `.streamlit` ở thư mục gốc, tạo file `secrets.toml` và cấu hình key để kích hoạt AI Chatbot:

```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "your-google-gemini-api-key"

```

### Bước 3: Chạy Streamlit UI

```bash
streamlit run app.py

```

### Bước 4: Triển khai Tự Động Hóa (Windows Task Scheduler)

Dự án sử dụng **Task Scheduler** để chạy luồng thu thập và cập nhật mô hình tự động hàng ngày (không dùng GitHub Actions):

1. Mở **Task Scheduler** trên máy chủ/máy trạm Windows.
2. Tạo **Basic Task** và thiết lập Trigger chạy hàng ngày (vd: 12:00 AM).
3. Tại tab **Action**, chọn *Start a program*.
4. Chỉ định file thực thi `.bat` (hoặc `.vbs` để chạy ngầm) chứa chuỗi lệnh ETL:
* Chạy `src/data_loader/spider.py`
* Chạy `src/preprocessing/cleaner.py` (Làm sạch & Upsert DB)
* Chạy `src/ai_engine/train_model.py` (Retrain model)