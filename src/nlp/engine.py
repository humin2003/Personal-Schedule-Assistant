# src/nlp/engine.py
import re
from datetime import datetime
from . import processor, rules, ner, time_parser

class NLPEngine:
    def __init__(self):
        pass

    def process(self, raw_text):
        original_text = raw_text
        
        # [Component 3] Trích xuất nhắc nhở (Rule-based)
        reminder_minutes, clean_text = rules.extract_reminder(raw_text)
        
        # [Component 1] Tiền xử lý
        clean_text = processor.normalize_text(clean_text)
        
        # [Component 4] Phân tích thời gian
        start_time, end_time, clean_text, has_time, is_all_day = time_parser.extract_datetime(clean_text)
        
        # [Component 2] Trích xuất địa điểm (NER)
        location, clean_text = ner.extract_location(clean_text)
        
        # Xử lý tên sự kiện
        clean_text = processor.remove_stop_phrases(clean_text)
        event_name = re.sub(r'\s+', ' ', clean_text).strip(' ,.-')
        if not event_name: event_name = "Sự kiện mới"

        # --- [COMPONENT 5] VALIDATION & HỢP NHẤT ---
        # 1. Kiểm tra logic thời gian
        now = datetime.now()

        # Fix lỗi End Time <= Start Time
        if end_time and end_time <= start_time:
            # Tự động đẩy End Time lên 1 tiếng
            end_time = start_time.replace(hour=(start_time.hour + 1) % 24)
            if end_time < start_time: # Qua ngày hôm sau
                 end_time = end_time.replace(day=start_time.day + 1)

        return {
            "event": event_name.capitalize(),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "location": location.title(),
            "reminder_minutes": reminder_minutes,
            "original_text": original_text,
            "is_all_day": is_all_day
        }