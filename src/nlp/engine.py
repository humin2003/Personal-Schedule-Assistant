from datetime import datetime, timedelta
import re
import unicodedata
from .processor import TextProcessor
from .ner import EntityExtractor
from .rules import RuleBasedExtractor
from .time_parser import TimeParser

def remove_accents(input_str):
    if not input_str: return ""
    s = unicodedata.normalize('NFD', str(input_str))
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')

class NLPEngine:
    def __init__(self):
        self.processor = TextProcessor()
        self.ner = EntityExtractor()
        self.rules = RuleBasedExtractor()
        self.timer = TimeParser()

    def process(self, raw_text): 
        clean_text = self.processor.normalize(raw_text)
        
        # 1. Trích xuất
        raw_location = self.ner.extract_location(clean_text)
        time_info = self.rules.extract(clean_text)
        
        # 2. Xử lý địa điểm
        final_location = ""
        if raw_location:
            collision = False
            if time_info['date_str'] and remove_accents(time_info['date_str']) in remove_accents(raw_location.lower()): collision = True
            if time_info['time_str'] and time_info['time_str'] in raw_location.lower(): collision = True
            
            time_keywords = ["tuần", "tháng", "năm", "hôm", "mai", "mốt", "lúc", "giờ"]
            if any(k in raw_location.lower() for k in time_keywords): collision = True

            if not collision:
                final_location = raw_location.title()

        # 3. Tính toán thời gian
        time_obj, time_error = self.timer.parse_time(
            time_info['time_str'], 
            time_info['session'], 
            time_info.get('special_type')
        )
        date_obj, is_valid_date = self.timer.parse_date(time_info['date_str'], time_info['day_month'])

        if time_error: raise ValueError(time_error)

        start_time_str = ""
        end_time_str = None
        all_day = False

        if time_obj:
            final_dt = date_obj.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
            start_time_str = final_dt.isoformat()
            end_time_str = None
        else:
            start_time_str = date_obj.strftime("%Y-%m-%d")
            all_day = True 

        # 4. XỬ LÝ TIÊU ĐỀ (CLEAN TITLE)
        title = raw_text
        items_to_remove = []
        
        # A. Địa điểm
        if final_location:
            items_to_remove.append(final_location)
            items_to_remove.append(remove_accents(final_location))
        
        # B. Thời gian
        if time_info['time_str']: items_to_remove.append(time_info['time_str'])
        if time_info['date_str']: items_to_remove.append(time_info['date_str'])

        # C. Nhắc nhở
        if time_info['reminder_str']: 
            items_to_remove.append(time_info['reminder_str'])
        
        # D. Buổi (Giữ lại nếu là hành động "Ăn trưa")
        session = time_info['session']
        if session:
            normalized_text = remove_accents(clean_text)
            normalized_session = remove_accents(session)
            is_activity = re.search(rf"\ban\s+{normalized_session}\b", normalized_text, re.IGNORECASE)
            if not is_activity:
                items_to_remove.append(session)

        items_to_remove.sort(key=len, reverse=True)

        for item in items_to_remove:
            if item:
                title = re.sub(re.escape(item), '', title, flags=re.IGNORECASE)
        
        # --- [CLEANUP LOGIC MỚI] ---
        
        # 1. Xóa Prefix
        start_prefixes = ["tôi muốn", "nhắc tôi", "nhớ là", "lên lịch", "ghi chú", "thêm sự kiện", "đặt lịch", "nhắc nhở"]
        lower_title = title.lower().strip()
        for p in start_prefixes:
            if lower_title.startswith(p):
                title = title[len(p):] 
                break

        connectors_pattern = r"\b(lúc|vào|tại|ở|trong|phút|phut|p|nay|hôm)\b"
        title = re.sub(connectors_pattern, " ", title, flags=re.IGNORECASE)

        # Nhóm 2: Từ nối chuyển động (đi, đến, về, qua)
        # Chỉ xóa nếu nó đứng lơ lửng (không phải đầu câu)
        move_connectors = r"(?<!^)\b(đi|đến|về|qua|)\b"
        title = re.sub(move_connectors, " ", title, flags=re.IGNORECASE)
        title = re.sub(r'\s+', ' ', title).strip().strip(",.-")
        if len(title) < 2: title = "Sự kiện mới"

        return {
            "event": title.capitalize(),
            "start_time": start_time_str,
            "end_time": end_time_str,   # Giờ đây nó sẽ là None (hoặc giá trị nếu sau này code thêm)
            "location": final_location,
            "reminder_minutes": time_info['reminder_minutes'], 
            "is_all_day": all_day,
            "original_text": raw_text
        }