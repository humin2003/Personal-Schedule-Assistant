import re
from . import processor, rules, ner, time_parser

class NLPEngine:
    def __init__(self):
        pass

    def process(self, raw_text):
        original_text = raw_text
        reminder_minutes, clean_text = rules.extract_reminder(raw_text)
        clean_text = processor.normalize_text(clean_text)
        
        # [MỚI] Hứng thêm biến is_all_day
        start_time, end_time, clean_text, has_time, is_all_day = time_parser.extract_datetime(clean_text)
        
        location, clean_text = ner.extract_location(clean_text)
        clean_text = processor.remove_stop_phrases(clean_text)
        event_name = re.sub(r'\s+', ' ', clean_text).strip(' ,.-')
        
        return {
            "event": event_name.capitalize() if event_name else "Sự kiện mới",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "location": location.title(),
            "reminder_minutes": reminder_minutes,
            "original_text": original_text,
            "is_all_day": is_all_day # [MỚI] Thêm vào kết quả trả về
        }