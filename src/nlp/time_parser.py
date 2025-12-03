import re
from datetime import datetime, timedelta

def parse_sub_time(time_str):
    """Hàm phụ trợ: Chuyển chuỗi giờ (9h, 9:30, 9) thành (hour, minute)"""
    if not time_str: return 0, 0
    time_str = time_str.lower().replace('h', ':').replace('g', ':').replace('giờ', ':')
    if ':' in time_str:
        parts = time_str.split(':')
        try:
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 and parts[1] else 0
        except ValueError:
            return 0, 0
    else:
        try:
            h = int(time_str)
            m = 0
        except ValueError:
            return 0, 0
    return h, m

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
            # Xóa cụm ngày đã bắt được
            text = re.sub(re.escape(m.group(0)), '', text, flags=re.IGNORECASE)
            text_lower = text.lower()

    # --- 2. XỬ LÝ THỜI GIAN TƯƠNG ĐỐI (Relative Time) ---
    delta_pattern = r'\b(?:trong|sau|tầm|khoảng)\s+(\d+)\s*(phút|p|tiếng|h|giờ)(?:\s*nữa)?\b'
    delta_match = re.search(delta_pattern, text_lower)
    
    if delta_match:
        try:
            amount = int(delta_match.group(1))
            unit = delta_match.group(2)
            
            if unit in ['tiếng', 'h', 'giờ']:
                add_time = timedelta(hours=amount)
            else: # phút, p
                add_time = timedelta(minutes=amount)
                
            start_time = now + add_time
            start_time = start_time.replace(second=0, microsecond=0)
            target_date = start_time.date()
            
            # [SỬA LẠI DÒNG NÀY]
            # CŨ: end_time = start_time + timedelta(hours=1)
            # MỚI: Không gán giờ kết thúc, để nó là None
            end_time = None 
            
            has_time = True
            text = re.sub(re.escape(delta_match.group(0)), '', text, flags=re.IGNORECASE)
        except: pass

    # --- 3. XỬ LÝ KHOẢNG GIỜ (TIME RANGE) ---
    # Ví dụ: "từ 9h đến 11h"
    if not start_time:
        range_pattern = r'\b(?:từ\s+)?(\d{1,2}(?:h|:|g|giờ)?(?:\d{2})?)\s*(?:đến|-|tới)\s*(\d{1,2}(?:h|:|g|giờ)?(?:\d{2})?)\b'
        range_match = re.search(range_pattern, text_lower)
        
        if range_match:
            try:
                t1_str = range_match.group(1)
                t2_str = range_match.group(2)
                
                h1, m1 = parse_sub_time(t1_str)
                h2, m2 = parse_sub_time(t2_str)

                is_pm = bool(re.search(pm_keywords, text_lower)) or is_pm_hint
                if is_pm and h1 < 12: h1 += 12
                if is_pm and h2 < 12: h2 += 12
                if h2 < h1 and h2 < 12: h2 += 12

                start_time = datetime.combine(target_date, datetime.min.time().replace(hour=h1%24, minute=m1%60))
                end_time = datetime.combine(target_date, datetime.min.time().replace(hour=h2%24, minute=m2%60))
                
                has_time = True
                text = re.sub(re.escape(range_match.group(0)), '', text, flags=re.IGNORECASE)
            except: pass

    # --- 4. XỬ LÝ GIỜ ĐƠN (SINGLE TIME) ---
    if not start_time:
        def normalize_hour(h, is_pm, ctx):
            if h == 12 and re.search(r'\b(đêm|dem)\b', ctx): return 0
            if is_pm and h < 12: return h + 12
            if not is_pm and h == 12: return 12
            return h

        session_suffix = r'(?:\s*(?:sáng|trưa|chiều|tối|đêm|sang|trua|chieu|toi|dem))?'

        patterns = [
            (r'(\d{1,2})\s*(?:giờ|gio|g|h)?\s*(?:kém|kem)\s*(\d{1,2})(?:\s*(?:phút|p|ph))?\b' + session_suffix, 'kem'),
            (r'\b(\d{1,2})\s*(?:rưỡi|ruoi)\b' + session_suffix, 'half'),
            (r'\b(\d{1,2})\s+(\d{1,2})\s*(?:phút|p|ph)\b' + session_suffix, 'full'),
            (r'\b(\d{1,2})\s*(?:h|g|:|giờ|gio)\s*(\d{0,2})\b' + session_suffix, 'std'),
            (r'\b(\d{1,2})\s*(a\.?m\.?|p\.?m\.?)\b', 'ampm'),
            (r'(?:lúc|vào|hồi|deadline)\s+(\d{1,2})\b' + session_suffix, 'key'),
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

                is_pm = bool(re.search(pm_keywords, text_lower)) or is_pm_hint
                if re.search(pm_keywords, valid_match.group(0)): is_pm = True
                
                if p_type != 'ampm': h = normalize_hour(h, is_pm, text_lower)

                start_time = datetime.combine(target_date, datetime.min.time().replace(hour=h%24, minute=m%60))
                end_time = None
                has_time = True
                
                text = re.sub(re.escape(valid_match.group(0)), '', text, flags=re.IGNORECASE)
            except: pass

    # --- 5. CLEANUP & FALLBACK ---
    if not start_time:
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = start_time + timedelta(days=1)
        is_all_day = True

    remove_list = r'\b(vào|lúc|hồi|ngày|tới|đến|từ|luc|vao|ngay|tu|den|toi|deadline|tuần sau|tuần tới)\b'
    text = re.sub(remove_list, '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(a\.?m\.?|p\.?m\.?)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(sáng|trưa|chiều|tối|đêm|sang|trua|chieu|toi|dem)\s+(nay|mai|qua|kia|mốt|t\d|cn|chủ nhật|thứ)\b', '', text, flags=re.IGNORECASE)
    
    return start_time, end_time, text, has_time, is_all_day