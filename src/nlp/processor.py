from underthesea import word_tokenize
import re

class TextProcessor:
    def __init__(self):
        # Map các từ không dấu/viết tắt thông dụng sang có dấu
        self.accent_map = {
            r"\bt2\b": "thứ 2", r"\bt3\b": "thứ 3", r"\bt4\b": "thứ 4",
            r"\bt5\b": "thứ 5", r"\bt6\b": "thứ 6", r"\bt7\b": "thứ 7",
            r"\bcn\b": "chủ nhật", r"\bchunhat\b": "chủ nhật",
            r"\bhom qua\b": "hôm qua", r"\bhom nay\b": "hôm nay", 
            r"\bngay mai\b": "ngày mai", r"\bngay kia\b": "ngày kia",
            r"\btuan sau\b": "tuần sau", r"\btuan toi\b": "tuần tới",
            r"\bcuoi tuan\b": "cuối tuần",
            r"\bphut\b": "phút", r"\bgio\b": "giờ",
            r"\bsang\b": "sáng", r"\btrua\b": "trưa", 
            r"\bchieu\b": "chiều", r"\btoi\b": "tối",
            r"\bdem\b": "đêm"
        }

    def normalize(self, text):
        if not text:
            return ""
        
        # 1. Cơ bản: lowercase & strip
        text = " ".join(text.strip().split()).lower()
        
        # 2. Thay thế từ viết tắt/không dấu phổ biến (Keyword Mapping)
        for pattern, replacement in self.accent_map.items():
            text = re.sub(pattern, replacement, text)
            
        return text

    def segment(self, text):
        return word_tokenize(text, format="text")