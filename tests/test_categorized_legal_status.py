import pytest
import pandas as pd
import re
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.preprocessing.clean_phase2 import categorize_legal_status

@pytest.mark.parametrize("input_val, expected", [
    # Nhóm Sổ đỏ: Cơ bản & Viết tắt
    ("Sổ đỏ chính chủ", "Sổ đỏ"),
    ("SĐCC phân lô", "Sổ đỏ"),
    ("sdcc vuông đét.", "Sổ đỏ"),  # Test xóa dấu chấm cuối
    ("Có Giấy chứng nhận quyền sử dụng đất", "Sổ đỏ"),
    ("Sổ hồng riêng", "Sổ đỏ"),
    
    # Nhóm Hợp đồng: Viết tắt & Loại hình
    ("Hợp đồng mua bán", "Hợp đồng"),
    ("HĐMB chung cư", "Hợp đồng"),
    ("Giấy tay công chứng", "Hợp đồng"),
    ("Hợp đồng 50 năm", "Hợp đồng"),
    ("Đã đặt cọc 100tr", "Hợp đồng"),
    ("hd mua ban", "Hợp đồng"), # Test từ viết tắt không dấu
    
    # Nhóm Khác: Các trường hợp đặc biệt & Độ ưu tiên
    ("Đang chờ sổ", "Khác"),       # Có chữ 'sổ' nhưng phải ưu tiên nhóm 'Khác'
    ("Sổ đỏ (sử dụng chung)", "Khác"), # Có chữ 'chung'
    ("Đang cập nhật", "Khác"),
    
    # Nhóm Không xác định/Nhiễu
    (None, "Không xác định"),
    (pd.NA, "Không xác định"),
    ("Pháp lý rõ ràng", "Không xác định"), # Không chứa keyword nào
    ("Chính chủ bán", "Không xác định"),
    
    # Test xóa dấu chấm cuối câu phức tạp
    ("Sổ đỏ sẵn sàng.....", "Sổ đỏ"),
    ("Hợp đồng đặt cọc. ", "Hợp đồng"),
])
def test_categorize_legal_status(input_val, expected):
    assert categorize_legal_status(input_val) == expected