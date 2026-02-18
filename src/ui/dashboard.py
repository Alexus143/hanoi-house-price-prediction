import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

def render_dashboard(df):
    """
    Hàm hiển thị Tab Thống kê
    df: Dataframe chứa dữ liệu bất động sản
    """
    col_filter1, col_filter2 = st.columns(2)
    
    # 1. Bộ lọc Khu vực
    with col_filter1:
        location_counts = df['ward'].value_counts()
        options = ["Tất cả"] + location_counts.index.tolist()
        chon_phuong = st.selectbox("Chọn Phường/Xã:", options, index=0, key="dash_phuong")

    # Lọc dữ liệu theo phường
    if chon_phuong != "Tất cả":
        df_display = df[df['ward'] == chon_phuong]
    else:
        df_display = df

    # 2. Bộ lọc Giá (Slider)
    with col_filter2:
        max_price_db = float(df_display['price_billion'].max()) if not df_display.empty else 10.0
        # Mặc định loại bỏ top 5% giá ảo để slider đỡ bị dài quá
        default_max = float(df_display['price_billion'].quantile(0.95)) if not df_display.empty else max_price_db
        
        price_range = st.slider(
            "Khoảng giá mong muốn (Tỷ):",
            0.0, max_price_db, (0.0, default_max),
            key="dash_price"
        )

    # Lọc dữ liệu theo giá
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