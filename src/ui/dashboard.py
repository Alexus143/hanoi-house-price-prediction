# src/ui/dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

def render_dashboard(df):
    """Hàm hiển thị Tab Thống kê với biểu đồ tương tác Plotly"""
    st.subheader("📈 Phân tích Thị trường Bất Động Sản")
    
    # 1. TẠO BỘ LỌC (FILTERS)
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        location_counts = df['ward'].value_counts()
        options_ward = ["Tất cả"] + location_counts.index.tolist()
        chon_phuong = st.selectbox("📍 Chọn Phường/Xã:", options_ward, index=0, key="dash_phuong")

    with col_filter2:
        if 'property_type' in df.columns:
            type_counts = df['property_type'].dropna().value_counts()
            options_type = ["Tất cả"] + type_counts.index.tolist()
        else:
            options_type = ["Tất cả"]
        chon_loai = st.selectbox("🏢 Loại hình:", options_type, index=0, key="dash_loai")

    # Xử lý lọc cấp 1 (Theo Phường và Loại hình)
    df_display = df.copy()
    if chon_phuong != "Tất cả":
        df_display = df_display[df_display['ward'] == chon_phuong]
    if chon_loai != "Tất cả" and 'property_type' in df_display.columns:
        df_display = df_display[df_display['property_type'] == chon_loai]

    with col_filter3:
        # Xử lý an toàn khi df_display rỗng
        if df_display.empty or df_display['price_billion'].isna().all():
            st.warning("Không có dữ liệu cho khu vực/loại hình này.")
            return
            
        max_price_db = float(df_display['price_billion'].max())
        if max_price_db <= 0: max_price_db = 1.0 
        
        default_max = float(df_display['price_billion'].quantile(0.95))
        price_range = st.slider("💰 Khoảng giá (Tỷ VNĐ):", 0.0, max_price_db, (0.0, default_max), step=0.5, key="dash_price")

    # Xử lý lọc cấp 2 (Theo Khoảng giá)
    df_final = df_display[
        (df_display['price_billion'] >= price_range[0]) & 
        (df_display['price_billion'] <= price_range[1])
    ].copy()

    st.markdown("---")

    # 2. HIỂN THỊ KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng số lượng tin", f"{len(df_final)} tin")
    
    if len(df_final) > 0:
        c2.metric("Giá trung bình", f"{df_final['price_billion'].mean():.2f} Tỷ VNĐ")
        avg_price_m2 = (df_final['price_billion'].sum() * 1000) / df_final['area'].sum()
        c3.metric("Đơn giá trung bình", f"{avg_price_m2:.1f} Triệu/m2")
        
        # 3. HỆ THỐNG BIỂU ĐỒ TRỰC QUAN HÓA
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Hàng biểu đồ 1
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Biểu đồ Line: Biến động đơn giá theo thời gian
            if 'scraped_date' in df_final.columns and 'price_billion' in df_final.columns and 'area' in df_final.columns:
                
                # Tính toán cột đơn giá (Triệu VNĐ / m2)
                # Sử dụng np.where để tránh lỗi ZeroDivisionError nếu area = 0
                df_final['price_per_m2'] = np.where(
                    df_final['area'] > 0, 
                    (df_final['price_billion'] * 1000) / df_final['area'], 
                    np.nan
                )
                
                # Xử lý ngày tháng
                df_final['scraped_date_clean'] = pd.to_datetime(df_final['scraped_date'], errors='coerce')
                
                # Loại bỏ các dòng thiếu ngày tháng hoặc thiếu đơn giá
                df_time = df_final.dropna(subset=['scraped_date_clean', 'price_per_m2'])
                
                if not df_time.empty:
                    # Nhóm dữ liệu theo ngày và tính trung bình đơn giá
                    df_trend = df_time.groupby(df_time['scraped_date_clean'].dt.date)['price_per_m2'].mean().reset_index()
                    df_trend = df_trend.rename(columns={'scraped_date_clean': 'Ngày', 'price_per_m2': 'Đơn giá TB (Triệu/m²)'})
                    df_trend = df_trend.sort_values('Ngày')

                    fig_trend = px.line(
                        df_trend, 
                        x="Ngày", 
                        y="Đơn giá TB (Triệu/m²)", 
                        title=f"Biến động đơn giá trung bình theo thời gian tại {chon_phuong}",
                        markers=True,
                        color_discrete_sequence=['#E74C3C']
                    )
                    st.plotly_chart(fig_trend, width='stretch')
                else:
                    st.info("Không có dữ liệu hợp lệ để vẽ biểu đồ biến động đơn giá.")
            else:
                st.warning("Dữ liệu thiếu cột 'price_billion' hoặc 'area' để tính đơn giá.")
            
        with chart_col2:
            # Biểu đồ Scatter: Tương quan Diện tích - Giá tiền
            fig_scatter = px.scatter(
                df_final, 
                x="area", 
                y="price_billion", 
                color="property_type" if 'property_type' in df_final.columns else None,
                title="Tương quan giữa Diện tích và Mức giá",
                labels={
                    "area": "Diện tích (m2)", 
                    "price_billion": "Giá (Tỷ VNĐ)", 
                    "property_type": "Loại hình"
                },
                opacity=0.7
            )
            st.plotly_chart(fig_scatter, width='stretch')

        # Hàng biểu đồ 2
        st.markdown("<br>", unsafe_allow_html=True)
        chart_col3, chart_col4 = st.columns(2)

        with chart_col3:
            # Biểu đồ Boxplot: Phân bố giá theo loại hình
            if 'property_type' in df_final.columns:
                fig_box = px.box(
                    df_final, 
                    x="property_type", 
                    y="price_billion", 
                    color="property_type",
                    title="Phân bố khoảng giá theo Loại hình",
                    labels={
                        "property_type": "Loại hình", 
                        "price_billion": "Giá (Tỷ VNĐ)"
                    }
                )
                st.plotly_chart(fig_box, width='stretch')

        with chart_col4:
            # Tính toán đơn giá/m2 cho biểu đồ Bar
            df_final['price_per_m2'] = (df_final['price_billion'] * 1000) / df_final['area']
            
            if chon_phuong == "Tất cả":
                # Đơn giá trung bình theo Phường
                df_ward_price = df_final.groupby('ward')['price_per_m2'].mean().reset_index()
                df_ward_price = df_ward_price.sort_values('price_per_m2', ascending=False).head(15) # Lấy top 15 để biểu đồ không bị rối
                
                fig_bar = px.bar(
                    df_ward_price, 
                    x="ward", 
                    y="price_per_m2", 
                    title="Đơn giá trung bình (Triệu/m2) theo Phường",
                    labels={"ward": "Phường/Xã", "price_per_m2": "Đơn giá (Triệu/m2)"},
                    color="price_per_m2",
                    color_continuous_scale="Blues"
                )
                st.plotly_chart(fig_bar, width='stretch')
            else:
                # Đơn giá trung bình theo Loại hình (khi đã lọc 1 phường cụ thể)
                if 'property_type' in df_final.columns:
                    df_type_price = df_final.groupby('property_type')['price_per_m2'].mean().reset_index()
                    df_type_price = df_type_price.sort_values('price_per_m2', ascending=False)
                    
                    fig_bar = px.bar(
                        df_type_price, 
                        x="property_type", 
                        y="price_per_m2", 
                        title=f"Đơn giá trung bình (Triệu/m2) theo Loại hình",
                        labels={"property_type": "Loại hình", "price_per_m2": "Đơn giá (Triệu/m2)"},
                        color="price_per_m2",
                        color_continuous_scale="Blues"
                    )
                    st.plotly_chart(fig_bar, width='stretch')
    else:
        st.info("💡 Không tìm thấy tin bất động sản nào phù hợp với bộ lọc hiện tại.")