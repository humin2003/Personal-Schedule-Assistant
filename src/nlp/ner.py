import re

try:
    from underthesea import ner
    HAS_UNDERTHESEA = True
except ImportError:
    HAS_UNDERTHESEA = False

def extract_location(text):
    """
    Tìm địa điểm dùng chiến lược Hybrid:
    1. Thử dùng Underthesea NER (Model AI)
    2. Nếu thất bại, dùng Regex (Rule-based)
    """
    location = "Chưa xác định"
    found_by_model = False

    # --- BƯỚC 1: Model-based (Underthesea) ---
    if HAS_UNDERTHESEA:
        try:
            tags = ner(text)
            loc_parts = []
            
            # [FIX] Sửa đoạn này để tránh lỗi unpack
            for item in tags:
                # item có thể là (word, tag) hoặc (word, pos, chunk, tag)...
                # Ta luôn lấy phần tử đầu là từ, phần tử cuối cùng là nhãn NER
                word = item[0]
                tag = item[-1] 
                
                # B-LOC: Bắt đầu địa điểm, I-LOC: Bên trong địa điểm, N-L: Location (cũ)
                if tag in ['B-LOC', 'I-LOC', 'N-L']: 
                    loc_parts.append(word)
            
            if loc_parts:
                location = " ".join(loc_parts)
                found_by_model = True
        except Exception as e:
            print(f"Lỗi NER: {e}")

    # --- BƯỚC 2: Rule-based (Regex Fallback) ---
    if not found_by_model or location == "Chưa xác định":
        pattern = r'\b(?:tại|ở|tai|o)\b\s+(.*?)(?=\s+\b(?:lúc|vào|hồi|ngày|sáng|trưa|chiều|tối|luc|vao|ngay|từ|tu|đến|tới)\b|$|[.,])'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            text = text.replace(match.group(0), '') 
    
    if found_by_model:
        text = text.replace(location, '')

    return location, text