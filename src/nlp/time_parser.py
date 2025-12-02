import re
from datetime import datetime, timedelta

def _extract_time_str(text_segment):
    if not text_segment: return None, None
    pattern = r'(\d{1,2})\s*(?:giờ|gio|g|h|:|phút|p|ph|\.|-)\s*(\d{1,2})?(?:\s*(?:phút|p|ph))?'
    match = re.search(pattern, text_segment, re.IGNORECASE)
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
    is_pm_hint = False
    is_all_day = False # [MỚI] Biến cờ đánh dấu cả ngày

    lower_text = text.lower()
    
    # 1. XỬ LÝ NGÀY
    match_today = re.search(r'\b(hôm nay|hom nay|chiều nay|tối nay|trưa nay|sáng nay)\b', lower_text)
    if match_today:
        target_date = now.date()
        if any(x in match_today.group(0) for x in ['chiều', 'tối', 'pm']): is_pm_hint = True
        text = text.replace(match_today.group(0), '')

    match_tomorrow = re.search(r'\b(ngày mai|ngay mai|sáng mai|trưa mai|chiều mai|tối mai)\b', lower_text)
    if match_tomorrow:
        target_date = now.date() + timedelta(days=1)
        if any(x in match_tomorrow.group(0) for x in ['chiều', 'tối', 'pm']): is_pm_hint = True
        text = text.replace(match_tomorrow.group(0), '')

    date_match = re.search(r'(\d{1,2})[/-](\d{1,2})(?:[/-](\d{4}))?', text)
    if date_match:
        try:
            d, m = int(date_match.group(1)), int(date_match.group(2))
            y = int(date_match.group(3)) if date_match.group(3) else now.year
            target_date = datetime(y, m, d).date()
            if target_date < now.date() and not date_match.group(3): target_date = target_date.replace(year=y+1)
        except ValueError: raise ValueError(f"Ngày {date_match.group(0)} sai!")
        text = text.replace(date_match.group(0), '')

    weekdays_map = {r'(thứ|thu)\s*2|t2': 0, r'(thứ|thu)\s*3|t3': 1, r'(thứ|thu)\s*4|t4': 2, r'(thứ|thu)\s*5|t5': 3, r'(thứ|thu)\s*6|t6': 4, r'(thứ|thu)\s*7|t7': 5, r'chủ nhật|cn|chu nhat': 6}
    for pattern, w_idx in weekdays_map.items():
        if re.search(pattern, lower_text):
            is_next = bool(re.search(r'tuần sau|tuan sau|tuần tới', lower_text))
            diff = w_idx - now.weekday()
            target_date = now.date() + timedelta(days=diff + 7) if is_next else now.date() + timedelta(days=(diff+7 if diff<=0 else diff))
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            text = re.sub(r'tuần sau|tuan sau|tuần tới', '', text, flags=re.IGNORECASE)
            break

    # 2. XỬ LÝ GIỜ
    range_match = re.search(r'(?:từ|tu|lúc|vào|ngay|hồi)?\s*((?:\d{1,2}[:hjg\.-]|\d{1,2}\s*(?:giờ|gio|g|h)).*?)\s+(?:đến|tới|den|toi|-)\s+((?:\d{1,2}[:hjg\.-]|\d{1,2}\s*(?:giờ|gio|g|h)).*?)(?=\s|$|[.,])', text, re.IGNORECASE)
    if range_match:
        h_s, m_s = _extract_time_str(range_match.group(1))
        h_e, m_e = _extract_time_str(range_match.group(2))
        if h_s is not None and h_e is not None:
            if not (0<=h_s<=23 and 0<=m_s<=59 and 0<=h_e<=23 and 0<=m_e<=59): raise ValueError("Giờ sai!")
            is_pm = bool(re.search(r'chiều|tối|pm|đêm', text, re.IGNORECASE)) or is_pm_hint
            if is_pm and h_s < 12: h_s += 12
            if is_pm and h_e < 12: h_e += 12
            elif h_e < h_s: h_e += 12 
            start_time = datetime.combine(target_date, datetime.min.time().replace(hour=h_s, minute=m_s))
            end_time = datetime.combine(target_date, datetime.min.time().replace(hour=h_e, minute=m_e))
            has_time = True
            text = text.replace(range_match.group(0), '')

    if not has_time:
        match = re.search(r'(?:lúc|vào|hồi|từ|tu|ngay)?\s*(\d{1,2})\s*(?:giờ|gio|phút|p|ph|[:\.-]|g|h)\s*(\d{1,2})?(?:\s*(?:phút|p|ph))?', text, re.IGNORECASE)
        if match:
            h = int(match.group(1))
            m = int(match.group(2)) if match.group(2) else 0
            if 0<=h<=23 and 0<=m<=59:
                is_pm = bool(re.search(r'chiều|tối|đêm|pm', text, re.IGNORECASE)) or is_pm_hint
                if is_pm and h < 12: h += 12
                start_time = datetime.combine(target_date, datetime.min.time().replace(hour=h, minute=m))
                end_time = start_time + timedelta(minutes=60)
                has_time = True
                text = text.replace(match.group(0), '')

    # [MỚI] LOGIC ALL DAY
    # Nếu chạy hết các bước trên mà start_time vẫn là None -> Tức là không có giờ cụ thể
    if not start_time:
        start_time = datetime.combine(target_date, datetime.min.time()) # 00:00:00
        end_time = start_time + timedelta(days=1) # Hết ngày
        is_all_day = True # Bật cờ All Day

    text = re.sub(r'\b(vào|lúc|hồi|sáng|trưa|chiều|tối|ngày|tới|đến|từ)\b', '', text, flags=re.IGNORECASE)
    
    # [MỚI] Trả về thêm biến is_all_day
    return start_time, end_time, text, has_time, is_all_day