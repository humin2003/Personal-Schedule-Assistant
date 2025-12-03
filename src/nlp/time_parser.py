import re
from datetime import datetime, timedelta

def extract_datetime(text):
    text_lower = text.lower()
    now = datetime.now()
    target_date = now.date()
    start_time = None
    end_time = None
    has_time = False
    is_pm_hint = False
    is_all_day = False 

    # Từ khóa PM (bao gồm không dấu)
    pm_keywords = r'\b(chiều|chieu|tối|toi|đêm|dem|pm|p\.m\.?)\b'
    
    # --- 1. XỬ LÝ NGÀY (DATE) ---
    date_patterns = [
        (r'\b(hôm nay|hom nay|chiều nay|chieu nay|tối nay|toi nay|trưa nay|trua nay|sáng nay|sang nay)\b', 0),
        (r'\b(ngày mai|ngay mai|sáng mai|sang mai|trưa mai|trua mai|chiều mai|chieu mai|tối mai|toi mai)\b', 1),
        (r'\b(?:sáng|trưa|chiều|tối|đêm)?\s*(ngày kia|ngay kia|ngày mốt|ngay mot)\b', 2),
        (r'\b(thứ|thu)\s*2|t2\b', 0), (r'\b(thứ|thu)\s*3|t3\b', 1), 
        (r'\b(thứ|thu)\s*4|t4\b', 2), (r'\b(thứ|thu)\s*5|t5\b', 3),
        (r'\b(thứ|thu)\s*6|t6\b', 4), (r'\b(thứ|thu)\s*7|t7\b', 5), 
        (r'\b(chủ nhật|cn|chu nhat)\b', 6),
        (r'\b(tháng sau|thang sau)\b', 30)
    ]

    for pat, val in date_patterns:
        m = re.search(pat, text_lower)
        if m:
            if 't' in pat or 'cn' in pat: 
                current_weekday = now.weekday()
                days_ahead = val - current_weekday
                if days_ahead <= 0: days_ahead += 7
                if 'tuần sau' in text_lower or 'tuan sau' in text_lower or 'tuần tới' in text_lower: days_ahead += 7
                target_date = now.date() + timedelta(days=days_ahead)
            elif val == 30: 
                target_date = now.date() + timedelta(days=30)
            else:
                target_date = now.date() + timedelta(days=val)
            
            if re.search(pm_keywords, m.group(0)): is_pm_hint = True
            text = re.sub(re.escape(m.group(0)), '', text, flags=re.IGNORECASE)
            text_lower = text.lower()

    # --- 2. XỬ LÝ GIỜ (TIME) ---
    def normalize_hour(h, is_pm, ctx):
        if h == 12 and re.search(r'\b(đêm|dem)\b', ctx): return 0
        if is_pm and h < 12: return h + 12
        if not is_pm and h == 12: return 12
        return h

    # Regex phụ để bắt từ chỉ buổi đi kèm (VD: 6h30 "sáng")
    # Giúp xóa sạch cụm từ trong text gốc
    session_suffix = r'(?:\s*(?:sáng|trưa|chiều|tối|đêm|sang|trua|chieu|toi|dem))?'

    patterns = [
        # Giờ kém
        (r'(\d{1,2})\s*(?:giờ|gio|g|h)?\s*(?:kém|kem)\s*(\d{1,2})(?:\s*(?:phút|p|ph))?\b' + session_suffix, 'kem'),
        # Giờ rưỡi (Bắt trực tiếp để xóa chuẩn)
        (r'\b(\d{1,2})\s*(?:rưỡi|ruoi)\b' + session_suffix, 'half'),
        # Giờ đầy đủ (6 30 phút)
        (r'\b(\d{1,2})\s+(\d{1,2})\s*(?:phút|p|ph)\b' + session_suffix, 'full'),
        # Giờ chuẩn (6h30, 6:30) - Có thể kèm buổi
        (r'\b(\d{1,2})\s*(?:h|g|:|giờ|gio)\s*(\d{0,2})\b' + session_suffix, 'std'),
        # AM/PM
        (r'\b(\d{1,2})\s*(a\.?m\.?|p\.?m\.?)\b', 'ampm'),
        # Từ khóa (lúc 9, chuyến 9)
        (r'(?:lúc|vào|hồi|deadline)\s+(\d{1,2})\b' + session_suffix, 'key'),
        # Chuyến (giữ lại chữ chuyến cho event name)
        (r'(?<=chuyến)\s*(\d{1,2})(?:h|g|:|giờ)?\b' + session_suffix, 'chuyen_time')
    ]

    valid_match = None
    p_type = ""
    for pat, pt in patterns:
        m = re.search(pat, text_lower)
        if m:
            valid_match = m
            p_type = pt
            break
            
    if valid_match:
        try:
            h, m = 0, 0
            # Parse giờ tùy theo pattern
            if p_type == 'kem':
                h, m = int(valid_match.group(1)) - 1, 60 - int(valid_match.group(2))
            elif p_type == 'half':
                h, m = int(valid_match.group(1)), 30
            elif p_type == 'ampm':
                h = int(valid_match.group(1))
                if 'p' in valid_match.group(2).lower() and h < 12: h += 12
                if 'a' in valid_match.group(2).lower() and h == 12: h = 0
            elif p_type == 'chuyen_time':
                h = int(valid_match.group(1))
            else:
                h = int(valid_match.group(1))
                if valid_match.group(2): m = int(valid_match.group(2))

            # PM Logic
            is_pm = bool(re.search(pm_keywords, text_lower)) or is_pm_hint
            # Nếu trong chính cụm bắt được có từ chỉ buổi (VD: 5h "chiều") -> Ưu tiên nó
            if re.search(pm_keywords, valid_match.group(0)): is_pm = True
            
            if p_type != 'ampm': h = normalize_hour(h, is_pm, text_lower)

            start_time = datetime.combine(target_date, datetime.min.time().replace(hour=h%24, minute=m%60))
            end_time = start_time + timedelta(hours=1)
            has_time = True
            
            # Xóa cụm giờ đã bắt được khỏi text gốc
            text = re.sub(re.escape(valid_match.group(0)), '', text, flags=re.IGNORECASE)
        except: pass

    if not start_time:
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = start_time + timedelta(days=1)
        is_all_day = True

    # --- 3. CLEANUP (Dọn rác kỹ hơn) ---
    remove_list = r'\b(vào|lúc|hồi|ngày|tới|đến|từ|luc|vao|ngay|tu|den|toi|deadline|tuần sau|tuần tới)\b'
    text = re.sub(remove_list, '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(a\.?m\.?|p\.?m\.?)\b', '', text, flags=re.IGNORECASE)
    
    # Xóa các từ chỉ buổi nếu còn sót lại (đứng độc lập)
    text = re.sub(r'\b(sáng|trưa|chiều|tối|đêm|sang|trua|chieu|toi|dem)\s+(nay|mai|qua|kia|mốt|t\d|cn|chủ nhật|thứ)\b', '', text, flags=re.IGNORECASE)
    
    return start_time, end_time, text, has_time, is_all_day