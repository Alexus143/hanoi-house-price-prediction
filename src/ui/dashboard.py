import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

def render_dashboard(df):
    """Hàm hiển thị Tab Thống kê"""
    # Thay vì 2 cột, giờ ta chia làm 3 cột bộ lọc
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        location_counts = df['ward'].value_counts()
        options_ward = ["Tất cả"] + location_counts.index.tolist()
        chon_phuong = st.selectbox("Chọn Phường/Xã:", options_ward, index=0, key="dash_phuong")

    with col_filter2:
        # CẬP NHẬT: Thêm bộ lọc Loại hình BĐS
        if 'property_type' in df.columns:
            type_counts = df['property_type'].value_counts()
            options_type = ["Tất cả"] + type_counts.index.tolist()
        else:
            options_type = ["Tất cả"]
        chon_loai = st.selectbox("Loại hình:", options_type, index=0, key="dash_loai")

    # Lọc dữ liệu theo phường và loại hình
    df_display = df.copy()
    if chon_phuong != "Tất cả":
        df_display = df_display[df_display['ward'] == chon_phuong]
    if chon_loai != "Tất cả" and 'property_type' in df_display.columns:
        df_display = df_display[df_display['property_type'] == chon_loai]

    with col_filter3:
        max_price_db = float(df_display['price_billion'].max()) if not df_display.empty else 10.0
        default_max = float(df_display['price_billion'].quantile(0.95)) if not df_display.empty else max_price_db
        price_range = st.slider("Khoảng giá (Tỷ):", 0.0, max_price_db, (0.0, default_max), key="dash_price")

    # Lọc lần cuối theo giá
    df_final = df_display[
        (df_display['price_billion'] >= price_range[0]) & 
        (df_display['price_billion'] <= price_range[1])
    ]

    st.markdown("---")

    # 3. Hiển thị KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Số lượng tin", f"{len(df_final)} tin")
    c2.metric("Giá trung bình", f"{df_final['price_billion'].mean():.2f} Tỷ")
    
    if len(df_final) > 0:
        avg_price_m2 = (df_final['price_billion'].sum() * 1000) / df_final['area'].sum()
        c3.metric("Đơn giá trung bình", f"{avg_price_m2:.1f} Triệu/m2")
        
        # 4. Biểu đồ
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.hist(df_final['price_billion'], bins=30, color='#2E86C1', edgecolor='white', alpha=0.8)
        ax.set_title(f"Phân bố giá tại {chon_phuong}")
        ax.set_xlabel("Giá (Tỷ VNĐ)")
        ax.set_ylabel("Số lượng")
        st.pyplot(fig)
        
        st.subheader("Dữ liệu chi tiết")
        st.dataframe(df_final[['title', 'price_billion', 'area', 'ward', 'published_date']].sort_values('price_billion'))
    else:
        c3.metric("Đơn giá trung bình", "0")
        st.warning("Không tìm thấy tin nào phù hợp với bộ lọc.")