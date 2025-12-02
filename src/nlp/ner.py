import re

try:
    from underthesea import ner
    HAS_UNDERTHESEA = True
except ImportError:
    HAS_UNDERTHESEA = False

def extract_location(text):
    """
    Tìm địa điểm dùng chiến lược Hybrid:
    1. Thử dùng Underthesea NER (Model AI) -> Có thêm bộ lọc ngữ cảnh
    2. Nếu thất bại, dùng Regex (Rule-based)
    """
    location = "Chưa xác định"
    found_by_model = False

    # --- BƯỚC 1: Model-based (Underthesea) ---
    if HAS_UNDERTHESEA:
        try:
            tags = ner(text)
            loc_parts = []
            
            # Cờ để theo dõi xem có đang trong chuỗi địa điểm bị cấm không
            is_ignoring = False
            
            for i, item in enumerate(tags):
                # item format: (word, pos, chunk, tag) hoặc (word, tag)
                word = item[0]
                tag = item[-1] 
                
                # Kiểm tra từ đứng trước (Look-behind)
                prev_word = tags[i-1][0].lower() if i > 0 else ""
                
                # Danh sách từ khóa báo hiệu ĐÂY LÀ NGƯỜI chứ không phải ĐỊA ĐIỂM
                # Ví dụ: hẹn VỚI Nam, gặp BÁC SĨ, cho MẸ...
                person_indicators = ['với', 'voi', 'gặp', 'gap', 'cho', 'tặng', 'của', 'cua', 'mời', 'moi']

                if tag in ['B-LOC', 'N-L']: # Bắt đầu một địa điểm
                    # Nếu từ trước đó là "với", "gặp"... -> Đánh dấu là bắt sai -> Bỏ qua
                    if prev_word in person_indicators:
                        is_ignoring = True
                        continue
                    else:
                        is_ignoring = False # Reset, đây là địa điểm xịn
                        loc_parts.append(word)
                
                elif tag == 'I-LOC': # Phần tiếp theo của địa điểm
                    if is_ignoring:
                        continue # Vẫn đang trong cụm bị cấm (VD: Tịt trong Hương Tịt)
                    else:
                        loc_parts.append(word)
                else:
                    is_ignoring = False # Gặp từ thường -> Reset cờ

            if loc_parts:
                location = " ".join(loc_parts)
                # Lọc thêm: Nếu địa điểm quá ngắn hoặc vô nghĩa
                if len(location) > 1:
                    found_by_model = True
                    
        except Exception as e:
            print(f"Lỗi NER: {e}")

    # --- BƯỚC 2: Rule-based (Regex Fallback) ---
    # Chỉ chạy nếu Model không tìm thấy hoặc Model tìm thấy nhưng bị bộ lọc loại bỏ
    if not found_by_model or location == "Chưa xác định":
        # Regex bắt sau từ: tại, ở, đi (đến)
        pattern = r'\b(?:tại|ở|tai|o|đến|den|tới|toi)\b\s+(.*?)(?=\s+\b(?:lúc|vào|hồi|ngày|sáng|trưa|chiều|tối|luc|vao|ngay|từ|tu|đến|tới)\b|$|[.,])'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            # Xóa cụm từ khóa địa điểm khỏi text gốc để tránh lặp
            text = text.replace(match.group(0), ' ') 
    
    # Nếu Model tìm thấy, xóa phần địa điểm khỏi text để làm sạch tên sự kiện
    if found_by_model:
        text = text.replace(location, '')

    return location, text