import re

try:
    from underthesea import ner
    HAS_UNDERTHESEA = True
except ImportError:
    HAS_UNDERTHESEA = False

# Danh sách từ cấm (Nếu địa điểm bắt đầu bằng từ này -> Loại bỏ)
BLOCK_LIST = ['ngủ', 'ăn', 'chơi', 'dạo', 'xem', 'date', 'học', 'làm', 'mua', 'gặp', 'book', 'check', 'đá', 'tập']

def is_valid_location(loc):
    if not loc or len(loc) < 2: return False
    first_word = loc.split()[0].lower()
    if first_word in BLOCK_LIST: return False
    # Không chứa số giờ (VD: 10h)
    if re.search(r'\d+h', loc): return False
    return True

def extract_location(text):
    location = "Chưa xác định"
    found_by_model = False

    # --- BƯỚC 1: Model-based ---
    if HAS_UNDERTHESEA:
        try:
            tags = ner(text)
            loc_parts = []
            is_ignoring = False
            for i, item in enumerate(tags):
                word = item[0]
                tag = item[-1]
                prev_word = tags[i-1][0].lower() if i > 0 else ""
                
                if prev_word in ['với', 'gặp', 'cho', 'tặng', 'mời']:
                    is_ignoring = True
                    continue
                if tag in ['B-LOC', 'N-L']:
                    is_ignoring = False
                    loc_parts.append(word)
                elif tag == 'I-LOC' and not is_ignoring:
                    loc_parts.append(word)
                else:
                    is_ignoring = False
            
            if loc_parts:
                candidate = " ".join(loc_parts)
                # [QUAN TRỌNG] Kiểm tra Block List cho cả kết quả Model
                if is_valid_location(candidate):
                    location = candidate
                    found_by_model = True
        except: pass

    # --- BƯỚC 2: Rule-based (Regex Fallback) ---
    if not found_by_model or location == "Chưa xác định":
        # Stop words: Thêm cả không dấu
        stop_words = r'lúc|vào|hồi|ngày|sáng|trưa|chiều|tối|chuyến|deadline|mua|ăn|xem|ngủ|làm|gặp|học|chơi|đá|tập|sang|trua|chieu|toi'
        
        pattern = fr'\b(?:tại|ở|tai|o|đến|den|tới|toi|về|ve|ra|trong|trên|đi|di|bay)\b\s+(.*?)(?=\s+\b(?:{stop_words})\b|$|[.,])'
        
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # Kiểm tra Block List và độ dài
            if is_valid_location(candidate) and len(candidate.split()) <= 6:
                location = candidate.title()
                text = text.replace(match.group(0), ' ')

    if found_by_model:
        text = text.replace(location, '')

    return location, text