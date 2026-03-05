# 🏡 Hệ Thống Phân Tích & Định Giá Bất Động Sản Hà Đông

Dự án là một hệ thống dữ liệu end-to-end (ETL Pipeline & Machine Learning) tự động thu thập dữ liệu, làm sạch, lưu trữ và dự báo giá bất động sản tại quận Hà Đông theo thời gian thực. Hệ thống xử lý tập dữ liệu đầu vào với quy mô hàng ngàn mẫu bất động sản (khoảng 5100+ mẫu) cùng 12 đặc trưng, nhằm dự đoán giá trị thực tế (tính bằng tỷ VNĐ).

Hệ thống hiện được **triển khai trực tuyến (Cloud Native)** với Database vận hành trên nền tảng Supabase, giao diện phục vụ người dùng qua Streamlit Cloud, và lõi AI được nâng cấp mạnh mẽ sử dụng thuật toán **XGBoost**.

* **🌍 Truy cập ứng dụng tại:** [Hà Đông House Price Analytics](https://hanoi-house-price-prediction-cqga57xqgo22wq72uvsdcc.streamlit.app/)
* **💾 Cơ sở dữ liệu:** PostgreSQL (Lưu trữ trên **Supabase**)

## 🏗️ Kiến trúc Hệ thống & Luồng Dữ liệu

Dự án được thiết kế theo module hóa, tách biệt giữa các công đoạn xử lý dữ liệu (ETL) và luồng huấn luyện mô hình, hoạt động đồng bộ giữa Local (Automation) và Cloud (Supabase & Streamlit).

### A. Luồng 1: Fast Ingestion Pipeline (Quét bề mặt - Chạy hàng ngày)

* **`spider.py`**: Sử dụng Selenium để trích xuất nhanh thông tin cơ bản (Giá, Diện tích, Phường, URL) từ trang danh sách bất động sản. Dữ liệu thô liên tục được append vào `raw_data.csv` bằng `pd.concat` để đề phòng Schema Drift.
* **`cleaner.py`**:
* Áp dụng NLP và Regex để trích xuất tự động số phòng từ văn bản rác.
* Lọc Outlier (giá, diện tích) và điền khuyết bằng `KNNImputer`.
* **Định danh dữ liệu (Deduplication):** Băm ID (`listing_id`) bằng thuật toán MD5 dựa trên các đặc trưng vật lý để chống tình trạng tin rác, tin đăng lại.
* **Upsert vào Supabase:** Mở kết nối trực tiếp đến PostgreSQL trên Cloud để ghi dữ liệu, chuẩn bị cho luồng cào sâu.



### B. Luồng 2: Deep Enrich & AI Pipeline (Cào chi tiết & Học máy)

* **`detail_spider.py`**:
* Truy vấn Supabase lấy các bản ghi chưa hoàn thiện (`is_enriched = False`).
* Cào sâu vào từng URL để lấy 6 feature nâng cao: Mặt tiền, Đường vào, Số tầng, Hướng, Pháp lý, Nội thất.


* **`train_xgb.py` (Lõi AI nâng cấp)**:
* **Thuật toán XGBoost:** Chuyển đổi từ RandomForest sang `XGBoost` để nắm bắt tốt hơn các mối quan hệ phi tuyến phức tạp trong giá nhà, giảm thiểu overfitting.
* **Xử lý Target Variable:** Áp dụng phép biến đổi Logarit (`np.log1p`) lên biến mục tiêu (Giá - tỷ VNĐ) nhằm chuẩn hóa phân phối dữ liệu (giảm độ lệch Skewness), giúp mô hình dự đoán mượt mà hơn ở các phân khúc giá cao.
* **Tối ưu tự động (AutoML):** Tích hợp **Optuna** thay thế cho GridSearchCV, giúp tìm kiếm siêu tham số (Hyperparameters) tối ưu nhất trong không gian rộng với thời gian hội tụ nhanh hơn.
* **Cơ chế Champion-Challenger**: Hệ thống tự động so sánh MAE (Sai số tuyệt đối trung bình) của mô hình XGBoost mới với mô hình đang chạy. Chỉ đè file `xgb_house_price_model.pkl` lên Cloud khi mô hình mới thực sự thông minh hơn.



### C. Giao diện (Streamlit Cloud) & Dự đoán

* Ứng dụng cung cấp giao diện trực quan nhập các thông số vật lý của ngôi nhà.
* Lớp suy luận gọi mô hình XGBoost, tự động áp dụng hàm mũ (`np.expm1`) để chuyển đổi kết quả ngược lại từ dạng logarit về dạng tỷ VNĐ để hiển thị cho người dùng.
* Tích hợp chatbot tư vấn dùng Gemini API giải đáp các xu hướng bất động sản tại khu vực.

## 🛠️ Tech Stack

* **Ngôn ngữ:** Python 3.10+
* **Cơ sở dữ liệu (Online):** **Supabase (PostgreSQL)**
* **Triển khai (Deployment):** **Streamlit Cloud**
* **Thu thập & Xử lý Dữ liệu:** Selenium (Undetected Chromedriver), Pandas, Numpy, Regex, Hashlib.
* **Machine Learning:** **XGBoost**, Scikit-Learn, **Optuna** (Tối ưu Hyperparameter).
* **Tích hợp AI:** Gemini API.

## 📂 Cấu trúc Thư mục Nổi bật

```text
├── .env                              # Secret variables (DB_URL, GEMINI_API_KEY)
├── app.py                            # Streamlit App Entry Point
├── src/
│   ├── data_loader/                  # Chứa spider.py và detail_spider.py
│   ├── database/
│   │   └── postgres_manager.py       # Trình quản lý kết nối Supabase
│   ├── preprocessing/
│   │   └── cleaner.py                # Pipeline làm sạch và nội suy dữ liệu
│   └── ai_engine/
│       ├── train_xgb.py              # Script huấn luyện XGBoost + Optuna
│       ├── predictor.py              # Xử lý suy luận giá (áp dụng np.expm1)
│       └── chatbot.py                # Tích hợp LLM
├── models/
│   └── xgb_house_price_model.pkl     # File mô hình XGBoost (Theo dõi qua Git LFS)
├── automation/                       # Scripts chạy tự động trên Local Server
└── README.md

```

## ⚖️ Trade-offs & Quyết định Kỹ thuật

1. **Kiến trúc Hybrid (Local ETL - Cloud DB):** Do sử dụng Selenium đòi hỏi tài nguyên máy tính cụ thể và IP để vượt Cloudflare, công đoạn cào dữ liệu được thực hiện tại Local. Tuy nhiên, việc đẩy ngay dữ liệu sạch lên Supabase (Cloud) đảm bảo Web App luôn có dữ liệu realtime để query mà không bị gián đoạn.
2. **XGBoost + Target Log-Transformation (`np.log1p`):** Sự phân hóa giá bất động sản ở Hà Đông rất lớn (từ ngõ hẻm vài tỷ đến mặt phố hàng chục tỷ). Việc biến đổi logarit giúp mô hình XGBoost không bị thiên lệch bởi các căn nhà siêu đắt (Outliers tác động lên hàm mất mát), trả về dự báo có độ ổn định và phương sai tốt hơn.
3. **Thay thế GridSearchCV bằng Optuna:** Việc có 12 đặc trưng và mô hình Boosting phức tạp khiến GridSearch quá chậm. Optuna sử dụng phương pháp tìm kiếm dạng xác suất (Bayesian optimization) giúp giảm 70% thời gian tuning nhưng vẫn tìm ra bộ tham số xuất sắc.

## 🚀 Hướng Dẫn Cài Đặt & Vận Hành

### Bước 1: Khởi tạo

```bash
git clone https://github.com/HieuNT316/hanoi-house-price-prediction.git
cd hanoi-house-price-prediction
pip install -r requirements.txt

```

### Bước 2: Cấu hình Secret (Supabase & Gemini)

Tạo file `.env` (chạy local) hoặc cấu hình trong **Streamlit Cloud > Advanced Settings > Secrets**:

```toml
DB_HOST = "your-supabase-db-host"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "your-password"
DB_PORT = "5432"
GEMINI_API_KEY = "your-gemini-api-key"

```

### Bước 3: Vận hành Pipeline & Streamlit

* Chạy app trên trình duyệt:

```bash
streamlit run app.py

```

* Huấn luyện lại mô hình (Yêu cầu phải có dữ liệu trong Database):

```bash
python src/ai_engine/train_xgb.py

```