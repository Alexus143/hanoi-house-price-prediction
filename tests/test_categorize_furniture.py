import pytest
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.preprocessing.clean_phase2 import categorize_furniture

@pytest.mark.parametrize("input_text, expected", [
    # Nhóm: Không nội thất / Thô
    ("Bàn giao thô", "Không nội thất"),
    ("Nhà thô nguyên bản", "Không nội thất"),
    ("Không nội thất.", "Không nội thất"),
    
    # Nhóm: Nội thất đầy đủ (Dựa vào từ khóa khẳng định)
    ("Full nội thất cao cấp.", "Nội thất đầy đủ"),
    ("Để lại toàn bộ nội thất", "Nội thất đầy đủ"),
    ("Nhà đã có đủ nội thất về chỉ cần ở.", "Nội thất đầy đủ"),
    ("Đầy đủ trang thiết bị như điều hòa, tủ lạnh, giường", "Nội thất đầy đủ"),
    
    # Nhóm: Nội thất đầy đủ (Dựa vào liệt kê đồ đạc - Dù không có chữ 'Full')
    ("03 điều hòa, tivi, tủ lạnh, máy giặt, sofa", "Nội thất đầy đủ"),
    ("Tặng tivi, tủ lạnh, máy giặt cho khách thiện chí", "Nội thất đầy đủ"),
    
    # Nhóm: Nội thất cơ bản (Liền tường/CĐT)
    ("Cơ bản.", "Nội thất cơ bản"),
    ("Nội thất cơ bản chủ đầu tư.", "Nội thất cơ bản"),
    ("Nội thất gắn tường rồi.", "Nội thất cơ bản"),
    ("Sàn gỗ, tủ bếp trên dưới, nóng lạnh, điều hòa.", "Nội thất cơ bản"),
    
    # Nhóm: Mô tả mơ hồ nhưng tích cực
    ("Nội thất cao cấp nhập khẩu.", "Nội thất cơ bản"),
    ("Cực tây nội thất toàn đồ xịn.", "Nội thất cơ bản"),
    ("Đẹp.", "Nội thất cơ bản"),
    
    # Nhóm: Không xác định / Lỗi
    ("null", "Không xác định"),
    (None, "Không xác định"),
    ("THANG MÁY TUYỆT ĐẸP", "Không xác định"), # Không liên quan nội thất
    ("Pháp lý rõ ràng", "Không xác định"),
    ("View hồ rất đẹp", "Không xác định"),       # Nhiễu về tầm nhìn
    ("Nội thất đẹp", "Nội thất cơ bản"),         # Có chữ nội thất -> Chấp nhận
    ("Nhà mới hoàn thiện", "Nội thất cơ bản"),   # Có chữ nhà -> Chấp nhận
    ("Full nội thất mới đẹp", "Nội thất đầy đủ"), # Ưu tiên Full
])
def test_categorize_furniture(input_text, expected):
    assert categorize_furniture(input_text) == expected