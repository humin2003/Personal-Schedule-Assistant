import re
import unicodedata

STOP_PHRASES = [
    "nhắc tôi", "nhắc nhở", "hãy nhắc", "nhắc", "đặt lịch", "tạo lịch", 
    "lên lịch", "note lại", "ghi chú", "có hẹn", "việc", "sự kiện",
    "nhac toi", "nhac nho", "hay nhac", "nhac", "dat lich", "tao lich",
    "len lich", "note lai", "ghi chu", "co hen", "viec", "su kien"
]

def normalize_text(text):
    """Chuyển về dạng chuẩn NFC và chữ thường."""
    text = unicodedata.normalize('NFC', text)
    return text.strip()

def remove_stop_phrases(text):
    """Loại bỏ các từ khóa ra lệnh ở đầu câu."""
    lower_text = text.lower()
    for phrase in STOP_PHRASES:
        if lower_text.startswith(phrase):
            text = text[len(phrase):].strip()
            lower_text = text.lower()
    
    # Xóa từ đệm vô nghĩa ở đầu câu
    text = re.sub(r'^(về|việc|là|rằng|và|vào)\s+', '', text, flags=re.IGNORECASE)
    return text