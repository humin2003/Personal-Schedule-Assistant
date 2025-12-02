import re
from datetime import datetime, timedelta
import unicodedata

class NLPEngine:
    def __init__(self):
        self.stop_phrases = [
            "nhắc tôi", "nhắc nhở", "hãy nhắc", "nhắc", "đặt lịch", "tạo lịch", 
            "lên lịch", "note lại", "ghi chú", "có hẹn", "việc", "sự kiện",
            "nhac toi", "nhac nho", "hay nhac", "nhac", "dat lich", "tao lich",
            "len lich", "note lai", "ghi chu", "co hen", "viec", "su kien"
        ]

    def _normalize_text(self, text):
        text = unicodedata.normalize('NFC', text)
        return text.lower().strip()

    def _remove_stop_phrases(self, text):
        for phrase in self.stop_phrases:
            if text.startswith(phrase):
                text = text[len(phrase):].strip()
        # [SỬA] Chỉ xóa 'và' nếu nó nằm vô duyên ở đầu câu, còn ở giữa thì giữ lại
        text = re.sub(r'^(về|việc|là|rằng|và|vào)\s+', '', text)
        return text

    def _extract_location(self, text):
        location = "Chưa xác định"
        pattern = r'\b(?:tại|ở|tai|o)\b\s+(.*?)(?=\s+\b(?:lúc|vào|hồi|ngày|sáng|trưa|chiều|tối|luc|vao|ngay|từ|tu|đến|tới)\b|$|[.,])'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            text = text.replace(match.group(0), '')
        return location, text

    def _extract_time_str(self, text_segment):
        if not text_segment: return None, None
        pattern = r'(\d{1,2})(?:h|g|:| giờ)\s*(\d{1,2})?(?:\s*(?:phút|p))?'
        match = re.search(pattern, text_segment)
        if match:
            h = int(match.group(1))
            m = int(match.group(2)) if match.group(2) else 0
            return h, m
        return None, None

    def _extract_datetime(self, text):
        now = datetime.now()
        target_date = now.date()
        start_time = None
        end_time = None
        has_time = False
        is_pm_hint = False

        # --- 1. XỬ LÝ NGÀY (DATE) ---
        match_today = re.search(r'\b(hôm nay|hom nay|chiều nay|tối nay|trưa nay)\b', text)
        match_tomorrow = re.search(r'\b(ngày mai|ngay mai|sáng mai|trưa mai|chiều mai|tối mai)\b', text)
        match_after_tomorrow = re.search(r'\b(ngày kia|ngay kia|mốt)\b', text)

        if match_today:
            target_date = now.date()
            if any(x in match_today.group(0) for x in ['chiều', 'tối', 'pm']):
                is_pm_hint = True
            text = text.replace(match_today.group(0), '')
            
        elif match_tomorrow:
            target_date = now.date() + timedelta(days=1)
            if any(x in match_tomorrow.group(0) for x in ['chiều', 'tối', 'pm']):
                is_pm_hint = True
            text = text.replace(match_tomorrow.group(0), '')
            
        elif match_after_tomorrow:
            target_date = now.date() + timedelta(days=2)
            text = text.replace(match_after_tomorrow.group(0), '')
            
        else:
            weekdays_map = {
                r'(thứ|thu)\s*2|t2': 0, r'(thứ|thu)\s*3|t3': 1, r'(thứ|thu)\s*4|t4': 2,
                r'(thứ|thu)\s*5|t5': 3, r'(thứ|thu)\s*6|t6': 4, r'(thứ|thu)\s*7|t7': 5,
                r'chủ nhật|cn|chu nhat': 6
            }
            is_next_week = bool(re.search(r'tuần sau|tuan sau|tuần tới|\bthứ .+ tới', text))
            for pattern, w_idx in weekdays_map.items():
                if re.search(pattern, text):
                    days_ahead = w_idx - now.weekday()
                    if days_ahead <= 0: days_ahead += 7
                    if is_next_week: days_ahead += 7
                    target_date = now.date() + timedelta(days=days_ahead)
                    text = re.sub(pattern, '', text)
                    text = re.sub(r'tuần sau|tuan sau|tuần tới', '', text)
                    if is_next_week: text = re.sub(r'\btới\b', '', text) 
                    break
        
        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})(?:[/-](\d{4}))?', text)
        if date_match:
            try:
                d, m = int(date_match.group(1)), int(date_match.group(2))
                y = int(date_match.group(3)) if date_match.group(3) else now.year
                target_date = datetime(y, m, d).date()
                if target_date < now.date() and not date_match.group(3):
                    target_date = target_date.replace(year=y+1)
            except: pass
            text = text.replace(date_match.group(0), '')

        # --- 2. XỬ LÝ GIỜ (TỪ... ĐẾN...) ---
        range_match = re.search(r'(?:từ|tu)\s+((?:\d{1,2}[:hg]\d{0,2}|\d{1,2}\s*giờ).*?)\s+(?:đến|tới|den|toi)\s+((?:\d{1,2}[:hg]\d{0,2}|\d{1,2}\s*giờ).*?)(?=\s|$|[.,])', text, re.IGNORECASE)
        
        if range_match:
            h_start, m_start = self._extract_time_str(range_match.group(1))
            h_end, m_end = self._extract_time_str(range_match.group(2))
            
            if h_start is not None and h_end is not None:
                is_pm = bool(re.search(r'chiều|tối|pm|đêm', text)) or is_pm_hint
                if is_pm:
                    if h_start < 12: h_start += 12
                    if h_end < 12: h_end += 12
                elif h_end < h_start:
                    h_end += 12
                
                start_time = datetime(target_date.year, target_date.month, target_date.day, h_start, m_start)
                end_time = datetime(target_date.year, target_date.month, target_date.day, h_end, m_end)
                has_time = True
                text = text.replace(range_match.group(0), '')

        # --- 3. XỬ LÝ GIỜ ĐƠN ---
        if not has_time:
            h, m = self._extract_time_str(text)
            if h is not None:
                is_pm = bool(re.search(r'chiều|tối|đêm|pm', text)) or is_pm_hint
                if is_pm and h < 12: h += 12
                
                start_time = datetime(target_date.year, target_date.month, target_date.day, h, m)
                end_time = start_time + timedelta(minutes=60)
                has_time = True
                
                cleanup_pattern = r'\b(?:lúc|vào|hồi|từ|tu)\s*(\d{1,2}(?:h|g|:| giờ)\s*(?:\d{1,2})?)'
                match_cleanup = re.search(cleanup_pattern, text)
                if match_cleanup:
                     text = text.replace(match_cleanup.group(0), '')
                else:
                    text = re.sub(r'(\d{1,2})(?:h|g|:| giờ)\s*(\d{1,2})?', '', text, 1)

        if not start_time:
            start_time = datetime(target_date.year, target_date.month, target_date.day, 8, 0)
            end_time = start_time + timedelta(minutes=60)

        # [SỬA QUAN TRỌNG] Đã xóa chữ 'và' khỏi danh sách này để không bị mất tên
        text = re.sub(r'\b(vào|lúc|hồi|sáng|trưa|chiều|tối|ngày|tới|đến|từ)\b', '', text)
        return start_time, end_time, text, has_time

    def process(self, raw_text):
        original_text = raw_text
        clean_text = self._normalize_text(raw_text)
        
        location, clean_text = self._extract_location(clean_text)
        start_time, end_time, clean_text, has_time = self._extract_datetime(clean_text)
        clean_text = self._remove_stop_phrases(clean_text)
        
        event_name = re.sub(r'\s+', ' ', clean_text).strip(' ,.-')
        
        return {
            "event": event_name.capitalize() if event_name else "Sự kiện mới",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "location": location.title(),
            "reminder_minutes": 15,
            "original_text": original_text 
        }