# src/database/postgres_manager.py
from sqlalchemy import create_engine, text
import pandas as pd
import sys
import os

# Import modules từ project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config.database import POSTGRES_URI

# Ép Python xuất dữ liệu text ra terminal hoặc file log bằng chuẩn UTF-8
sys.stdout.reconfigure(encoding='utf-8')

class PostgresManager:
    def __init__(self):
        """Khởi tạo kết nối tới PostgreSQL sử dụng SQLAlchemy Engine"""
        try:
            self.engine = create_engine(POSTGRES_URI)
            # THÊM ĐOẠN NÀY: Ép SQLAlchemy ping thử vào DB ngay lập tức
            with self.engine.connect() as conn:
                pass
            print("✅ Đã kết nối thành công tới PostgreSQL.")
        except Exception as e:
            print(f"❌ Lỗi kết nối Database: {e}")
            self.engine = None

    def save_dataframe(self, df: pd.DataFrame, table_name: str, if_exists: str = 'replace'):
        """Lưu Pandas DataFrame trực tiếp vào PostgreSQL."""
        if self.engine is None: return
        try:
            df.to_sql(table_name, con=self.engine, if_exists=if_exists, index=False)
            print(f"💾 Đã lưu {len(df)} bản ghi vào '{table_name}'.")
        except Exception as e:
            print(f"❌ Lỗi khi lưu dữ liệu: {e}")

    def load_dataframe(self, query: str) -> pd.DataFrame:
        """Đọc dữ liệu từ PostgreSQL trả về Pandas DataFrame"""
        if self.engine is None:
            raise ConnectionError("Không có kết nối DB.")
        return pd.read_sql(query, con=self.engine)
    
    def ensure_primary_key(self, table_name: str, column_name: str = "listing_id"):
        """
        Kiểm tra và tự động ép kiểu PRIMARY KEY cho bảng.
        Chỉ cần gọi hàm này 1 lần duy nhất lúc khởi tạo pipeline.
        """
        if self.engine is None: return
        
        check_pk_query = f"""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = '{table_name}' AND constraint_type = 'PRIMARY KEY';
        """
        
        add_pk_query = f"""
            ALTER TABLE "{table_name}" 
            ADD PRIMARY KEY ("{column_name}");
        """
        
        try:
            with self.engine.begin() as conn:
                result = conn.execute(text(check_pk_query)).fetchone()
                if not result:
                    conn.execute(text(add_pk_query))
                    print(f"🔑 Đã thiết lập thành công PRIMARY KEY cho cột '{column_name}' trong bảng '{table_name}'.")
                else:
                    print(f"✅ Bảng '{table_name}' đã có PRIMARY KEY. Bỏ qua.")
        except Exception as e:
            print(f"❌ Lỗi khi thiết lập PK: {e}")
            print("⚠️ Lưu ý: Nếu bảng đang có dữ liệu trùng lặp (duplicate listing_id), PostgreSQL sẽ từ chối tạo PK. Hãy xóa trắng DB và chạy lại.")
    
    # ==========================================
    # HỖ TRỢ LUỒNG 1: SPIDER.PY & CLEANER.PY
    # ==========================================
    def upsert_dataframe(self, df: pd.DataFrame, table_name: str, unique_key: str, exclude_cols: list = None):
        """
        Logic Upsert thông minh:
        - Insert nếu chưa tồn tại (Dựa vào MD5 unique_key).
        - Update nếu đã tồn tại, NHƯNG bảo vệ các cột được cấu hình trong exclude_cols (như is_enriched, frontage...).
        """
        if df.empty or self.engine is None: return
        if exclude_cols is None: exclude_cols = []
        
        # Đảm bảo có cột cờ hiệu cho các bản ghi mới
        if 'is_enriched' not in df.columns:
            df['is_enriched'] = False

        temp_table = f"temp_{table_name}"
        
        with self.engine.begin() as conn:
            # 1. Đẩy dữ liệu mới vào Bảng Tạm
            df.to_sql(temp_table, con=conn, index=False, if_exists='replace')
            
            # 2. Tạo danh sách các cột CẦN UPDATE
            columns_str = ", ".join([f'"{col}"' for col in df.columns])
            update_cols = [
                f'"{col}" = EXCLUDED."{col}"' 
                for col in df.columns 
                if col != unique_key and col not in exclude_cols
            ]
            
            # Nếu không có cột nào để update thì chỉ cần DO NOTHING
            conflict_action = f"DO UPDATE SET {', '.join(update_cols)}" if update_cols else "DO NOTHING"
            
            # 3. Câu lệnh chuẩn PostgreSQL (Yêu cầu unique_key phải là Primary Key trong DB)
            upsert_query = f"""
                INSERT INTO "{table_name}" ({columns_str})
                SELECT {columns_str} FROM "{temp_table}"
                ON CONFLICT ("{unique_key}") 
                {conflict_action};
            """
            
            conn.execute(text(upsert_query))
            conn.execute(text(f'DROP TABLE "{temp_table}";'))
            print(f"🔄 Upsert thành công {len(df)} bản ghi vào '{table_name}'.")

    # ==========================================
    # HỖ TRỢ LUỒNG 2: DETAIL_SPIDER.PY
    # ==========================================
    def get_unenriched_listings(self, table_name: str, limit: int = 50) -> list:
        """Truy xuất các URL chưa được cào chi tiết."""
        if self.engine is None: return []
        
        query = f"""
            SELECT listing_id, url 
            FROM "{table_name}" 
            WHERE is_enriched = FALSE OR is_enriched IS NULL 
            LIMIT {limit};
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            # Trả về list chứa các dictionary để detail_spider dễ xử lý
            return [dict(row._mapping) for row in result]

    def update_listing_details(self, table_name: str, enriched_data: dict):
        """
        Cập nhật các feature chi tiết (mặt tiền, đường vào...) 
        và lật cờ is_enriched = TRUE.
        """
        if self.engine is None: return
        
        # Tách listing_id ra khỏi data dictionary
        listing_id = enriched_data.pop('listing_id', None)
        if not listing_id: return
        
        # Tự động bật cờ đã cào chi tiết
        enriched_data['is_enriched'] = True 
        
        # Xây dựng câu lệnh SET động dựa trên dictionary gửi vào
        set_clauses = [f'"{key}" = :{key}' for key in enriched_data.keys()]
        set_str = ", ".join(set_clauses)
        
        query = f"""
            UPDATE "{table_name}"
            SET {set_str}
            WHERE listing_id = :listing_id;
        """
        
        # Kẹp listing_id lại vào dictionary để mapping params an toàn chống SQL Injection
        enriched_data['listing_id'] = listing_id 
        
        with self.engine.begin() as conn:
            conn.execute(text(query), enriched_data)