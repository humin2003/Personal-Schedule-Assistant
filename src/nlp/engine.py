import re
from datetime import datetime
from . import processor, rules, ner, time_parser

class NLPEngine:
    def __init__(self):
        pass

    def process(self, raw_text):
        original_text = raw_text
        
        # 1. Trích xuất nhắc nhở
        reminder_minutes, clean_text = rules.extract_reminder(raw_text)
        
        # 2. Tiền xử lý
        clean_text = processor.normalize_text(clean_text)
        
        # 3. Time Parser chạy TRƯỚC (Để lọc giờ)
        start_time, end_time, clean_text, has_time, is_all_day = time_parser.extract_datetime(clean_text)
        
        # 4. NER chạy SAU (Với bộ lọc thông minh hơn)
        location, clean_text = ner.extract_location(clean_text)
        
        # 5. Dọn dẹp tên sự kiện
        clean_text = processor.remove_stop_phrases(clean_text)
        event_name = re.sub(r'\s+', ' ', clean_text).strip(' ,.-')
        if not event_name: event_name = "Sự kiện mới"

        # Validation
        if end_time and end_time <= start_time:
            end_time = start_time.replace(hour=(start_time.hour + 1) % 24)
            if end_time < start_time: end_time = end_time.replace(day=start_time.day + 1)

        return {
            "event": event_name.capitalize(),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "location": location.title(),
            "reminder_minutes": reminder_minutes,
            "original_text": original_text,
            "is_all_day": is_all_day
        }