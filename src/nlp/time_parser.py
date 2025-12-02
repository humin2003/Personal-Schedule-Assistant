import re
from datetime import datetime, timedelta

def _extract_time_str(text_segment):
    """
    Hàm phụ trợ: Tính toán giờ/phút từ chuỗi đã bắt được.
    """
    if not text_segment: return None, None
    
    # 1. Xử lý GIỜ KÉM (VD: 8h kém 15, 8 giờ kém 15)
    kem_match = re.search(r'(\d{1,2})\s*(?:giờ|gio|g|h)?\s*(?:kém|kem)\s*(\d{1,2})', text_segment, re.IGNORECASE)
    if kem_match:
        h = int(kem_match.group(1)) - 1
        m = 60 - int(kem_match.group(2))
        if m < 0: m += 60; h -= 1
        if h < 0: h += 24 
        return h, m

    # 2. Xử lý GIỜ THƯỜNG
    match = re.search(r'(\d{1,2})\s*(?:giờ|gio|g|h|:|phút|p|ph|\.|-)?\s*(\d{1,2})?', text_segment, re.IGNORECASE)
    if match:
        h = int(match.group(1))
        m = int(match.group(2)) if match.group(2) else 0
        return h, m
    
    return None, None

def extract_datetime(text):
    now = datetime.now()
    target_date = now.date()
    start_time = None
    end_time = None
    has_time = False
    
    # Cờ ngữ cảnh
    is_pm_hint = False
    is_all_day = False 

    # --- TIỀN XỬ LÝ ---
    text = text.lower()
    # [Fix Case 20] 6 rưỡi -> 6 30 phút
    text = re.sub(r'\b(rưỡi|ruoi)\b', ' 30 phút', text)

    # Từ khóa buổi
    pm_keywords = r'\b(chiều|chieu|tối|toi|đêm|dem|pm|p\.m\.?)\b'
    
    # --- 1. XỬ LÝ NGÀY (DATE) ---
    
    # a. HÔM NAY
    match_today = re.search(r'\b(hôm nay|hom nay|chiều nay|chieu nay|tối nay|toi nay|trưa nay|trua nay|sáng nay|sang nay)\b', text)
    if match_today:
        target_date = now.date()
        if re.search(pm_keywords, match_today.group(0)): is_pm_hint = True
        text = text.replace(match_today.group(0), '')

    # b. NGÀY MAI
    match_tomorrow = re.search(r'\b(ngày mai|ngay mai|sáng mai|sang mai|trưa mai|trua mai|chiều mai|chieu mai|tối mai|toi mai)\b', text)
    if match_tomorrow:
        target_date = now.date() + timedelta(days=1)
        if re.search(pm_keywords, match_tomorrow.group(0)): is_pm_hint = True
        text = text.replace(match_tomorrow.group(0), '')

    # c. [MỚI] NGÀY KIA / NGÀY MỐT (Thêm 2 ngày)
    # Regex bắt: ngày kia, ngày mốt (có thể kèm sáng/chiều/tối)
    match_day_after = re.search(r'\b(?:sáng|trưa|chiều|tối|đêm)?\s*(ngày kia|ngay kia|ngày mốt|ngay mot)\b', text)
    if match_day_after:
        target_date = now.date() + timedelta(days=2)
        # Nếu cụm từ có chứa chiều/tối -> Bật gợi ý PM
        if re.search(pm_keywords, match_day_after.group(0)): is_pm_hint = True
        text = text.replace(match_day_after.group(0), '')

    # d. NGÀY CỤ THỂ (dd/mm/yyyy)
    date_match = re.search(r'(\d{1,2})[/-](\d{1,2})(?:[/-](\d{4}))?', text)
    if date_match:
        try:
            d, m = int(date_match.group(1)), int(date_match.group(2))
            y = int(date_match.group(3)) if date_match.group(3) else now.year
            target_date = datetime(y, m, d).date()
            if target_date < now.date() and not date_match.group(3): target_date = target_date.replace(year=y+1)
        except: pass
        text = text.replace(date_match.group(0), '')

    # e. THỨ TRONG TUẦN
    weekdays_map = {r'(thứ|thu)\s*2|t2': 0, r'(thứ|thu)\s*3|t3': 1, r'(thứ|thu)\s*4|t4': 2, r'(thứ|thu)\s*5|t5': 3, r'(thứ|thu)\s*6|t6': 4, r'(thứ|thu)\s*7|t7': 5, r'chủ nhật|cn|chu nhat': 6}
    for pattern, w_idx in weekdays_map.items():
        if re.search(pattern, text):
            is_next = bool(re.search(r'tuần sau|tuan sau|tuần tới|tuan toi', text))
            diff = w_idx - now.weekday()
            days_add = diff + 7 if is_next else (diff + 7 if diff <= 0 else diff)
            target_date = now.date() + timedelta(days=days_add)
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            text = re.sub(r'tuần sau|tuan sau|tuần tới|tuan toi', '', text, flags=re.IGNORECASE)
            break

    # --- 2. XỬ LÝ GIỜ (TIME) ---
    
    def check_is_pm(context_text):
        return bool(re.search(pm_keywords, context_text)) or is_pm_hint

    def normalize_hour(h, is_pm, context_text=""):
        if h == 12:
            if re.search(r'đêm|dem', context_text): return 0
            if is_pm: return 12
            return 12
        if is_pm and h < 12: return h + 12
        return h

    # Case A: Khoảng giờ
    range_match = re.search(r'(?:từ|tu|lúc|vào|ngay|hồi)?\s*\b((?:\d{1,2}[:hjg\.-]|\d{1,2}\s*(?:giờ|gio|g|h)|kém).*?)\s+(?:đến|tới|den|toi|-)\s+\b((?:\d{1,2}[:hjg\.-]|\d{1,2}\s*(?:giờ|gio|g|h)|kém).*?)(?=\s|$|[.,])', text, re.IGNORECASE)
    if range_match:
        h_s, m_s = _extract_time_str(range_match.group(1))
        h_e, m_e = _extract_time_str(range_match.group(2))
        if h_s is not None and h_e is not None:
            if (0<=h_s<=23 and 0<=m_s<=59 and 0<=h_e<=23 and 0<=m_e<=59):
                is_pm = check_is_pm(text)
                h_s = normalize_hour(h_s, is_pm, text)
                h_e_temp = normalize_hour(h_e, is_pm, text)
                if h_e_temp < h_s: h_e_temp += 12
                
                start_time = datetime.combine(target_date, datetime.min.time().replace(hour=h_s, minute=m_s))
                end_time = datetime.combine(target_date, datetime.min.time().replace(hour=h_e_temp, minute=m_e))
                has_time = True
                text = text.replace(range_match.group(0), '')

    # Case B: Giờ đơn lẻ
    if not has_time:
        valid_match = None
        matched_pattern = ""
        ampm_str = ""

        patterns = [
            # 1. Giờ kém (Ưu tiên số 1)
            (r'(\d{1,2})\s*(?:giờ|gio|g|h)?\s*(?:kém|kem)\s*(\d{1,2})(?:\s*(?:phút|p|ph))?\b', 'kem'),

            # 2. Giờ + Phút có đơn vị
            (r'\b(\d{1,2})\s+(\d{1,2})\s*(?:phút|p|ph)\b', 'full_unit'),
            
            # 3. Giờ + Unit
            (r'\b(\d{1,2})\s*(?:h|g|:|giờ|gio)\s*(\d{0,2})\b', 'std_unit'),
            
            # 4. Giờ + AM/PM
            (r'\b(\d{1,2})\s*(a\.?m\.?|p\.?m\.?)\b', 'ampm'),
            
            # 5. Từ khóa + Số
            (r'(?:lúc|vào|hồi|deadline|chuyến)\s+(\d{1,2})\b', 'keyword_only'),
        ]

        for pat, p_type in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                valid_match = m
                matched_pattern = p_type
                break
        
        if valid_match:
            h, m = 0, 0
            
            if matched_pattern == 'kem':
                h = int(valid_match.group(1)) - 1
                m = 60 - int(valid_match.group(2))
                if m < 0: m += 60; h -= 1
            elif matched_pattern == 'ampm':
                h = int(valid_match.group(1))
                ampm_str = valid_match.group(2)
            elif matched_pattern == 'keyword_only':
                h = int(valid_match.group(1))
            else: 
                h = int(valid_match.group(1))
                m = int(valid_match.group(2)) if valid_match.group(2) else 0

            # --- Logic chuẩn hóa giờ (12h -> 24h) ---
            if 0 <= h <= 23 and 0 <= m <= 59:
                is_pm = check_is_pm(text)
                
                if matched_pattern == 'ampm' and ampm_str:
                    if 'p' in ampm_str.lower() and h < 12: h += 12
                    if 'a' in ampm_str.lower() and h == 12: h = 0
                else:
                    h = normalize_hour(h, is_pm, text)

                start_time = datetime.combine(target_date, datetime.min.time().replace(hour=h, minute=m))
                end_time = start_time + timedelta(minutes=60)
                has_time = True
                text = text.replace(valid_match.group(0), '')

    # --- 3. XỬ LÝ ALL DAY ---
    if not start_time:
        start_time = datetime.combine(target_date, datetime.min.time()) 
        end_time = start_time + timedelta(days=1)
        is_all_day = True 

    text = re.sub(r'\b(vào|lúc|hồi|sáng|trưa|chiều|tối|ngày|tới|đến|từ)\b', '', text, flags=re.IGNORECASE)
    
    return start_time, end_time, text, has_time, is_all_day