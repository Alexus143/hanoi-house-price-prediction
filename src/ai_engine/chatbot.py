# src/ai_engine/chatbot.py
from google import genai

def generate_chatbot_response(prompt: str, df, chat_history: list, api_key: str) -> str:
    """
    Xử lý logic RAG, xây dựng Prompt và gọi API Gemini.
    Không chứa bất kỳ logic UI nào.
    """
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        raise ConnectionError(f"Lỗi khởi tạo AI Client: {e}")

    # --- LỚP RAG TIỀN XỬ LÝ ---
    stats_text = f"Tổng quan: {len(df)} tin, giá trung bình {df['price_billion'].mean():.2f} tỷ."
    
    # Tìm kiếm thông tin khu vực (Bỏ qua phân biệt hoa thường)
    prompt_lower = prompt.lower()
    ds_phuong = df['ward'].dropna().unique()
    for phuong in ds_phuong:
        if phuong.lower() in prompt_lower:
            df_loc = df[df['ward'] == phuong]
            if not df_loc.empty:
                stats_text += f"\n- Khu vực {phuong}: {len(df_loc)} tin, giá trung bình {df_loc['price_billion'].mean():.2f} tỷ. Diện tích trung bình {df_loc['area'].mean():.1f} m2."
            break # Tối ưu tốc độ, dừng khi tìm thấy 1 phường

    # --- XÂY DỰNG NGỮ CẢNH (MEMORY) ---
    # Lấy tối đa 5 tin nhắn gần nhất từ lịch sử được truyền vào
    recent_history = ""
    for msg in chat_history[-5:]: 
        role_name = "Khách hàng" if msg["role"] == "user" else "AI"
        recent_history += f"{role_name}: {msg['content']}\n"

    # --- GỌI GEMINI VỚI PROMPT CHUẨN KỸ SƯ AI ---
    system_instruction = f"""
    Bạn là AI tư vấn Bất động sản chuyên nghiệp tại Hà Đông. Dữ liệu thực tế hệ thống cung cấp:
    {stats_text}
    
    Lịch sử trò chuyện gần đây:
    {recent_history}
    
    Khách hàng hỏi: "{prompt}"
    
    Quy tắc:
    1. Dựa CHÍNH XÁC vào dữ liệu thực tế được cung cấp. Nếu không có số liệu, hãy nói rõ là hệ thống chưa có dữ liệu.
    2. Trả lời ngắn gọn, súc tích (dưới 4 câu), thân thiện.
    3. Gợi mở câu hỏi tiếp theo cho khách hàng (VD: Bạn có muốn biết giá chung cư ở đây không?).
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_instruction
        )
        return response.text
    except Exception as e:
        raise RuntimeError(f"Lỗi kết nối AI: {e}")