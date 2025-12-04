import re

class RuleBasedExtractor:
    def __init__(self):
        self.patterns = {
            # 1. Bắt Giờ
            "time_absolute": [
                r"\b(\d{1,2})\s*[:hg]\s*(\d{2})\b",
                r"\b(\d{1,2})\s*giờ\s*(\d{1,2})\b",
                r"\b(\d{1,2})\s*(?:h|g|giờ)?\s*kém\s*(\d{1,2})\b",
                r"\b(\d{1,2})\s*(?:h|g|giờ)?\s*rưỡi\b",
                r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.?|p\.m\.?)\b",
                r"\b(\d{1,2})\s*(h|g|giờ)\b"
            ],
            
            # 2. Bắt Ngày/Tháng
            "date_absolute": [
                r"\b(\d{1,2})\s*[/-]\s*(\d{1,2})\b",             
                r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})"      
            ],

            # 3. Bắt Thứ
            "weekday": [
                r"(?:thứ\s+(?:\d+|hai|ba|tư|năm|sáu|bảy)|chủ\s+nhật|cn|t\d)\s+tuần\s+(?:sau|tới|này|trước)",
                r"thứ\s+(\d+|hai|ba|tư|năm|sáu|bảy)",
                r"chủ\s+nhật",
                r"\b(t[2-7]|cn)\b"
            ],
            
            # 4. Ngày tương đối
            "date_relative": [
                r"\b(?:sáng|trưa|chiều|tối|đêm|khuya)\s+(?:mai|mốt|kia|hôm qua|qua)\b",
                r"\b(?:ngày|ngay)\s*(?:mai|kia|mốt|mot)\b",
                r"\b(?:hôm|hom)\s*(?:nay|qua|kia|sau)\b",
                r"(?<=\d)\s*(?:ngày|ngay)?\s*(mai|mốt|mot|kia)\b",
                r"(?<=[hg])\s*(?:ngày|ngay)?\s*(mai|mốt|mot|kia)\b",
                r"^\s*(mai|mốt|mot|kia)\b",
                r"\b(mai|mốt|mot|kia)\s+(?:lúc|vào)?\s*\d",
                r"\b(?:tuần|tuan)\s*(?:này|nay|sau|tới|toi)\b",
                r"\b(?:cuối tuần|cuoi tuan)\b",
            ],
            
            # 5. Buổi
            "session": [
                r"\b(sáng|trưa|chiều|tối|đêm|sang|trua|chieu|toi|dem)\b"
            ],

            # 6. Nhắc nhở
            "reminder": [
                r"\b(?:hãy\s+)?(?:nhắc|báo|hẹn|thông báo)\s*(?:nhở|tôi|mình|bạn|em|anh|chị|cho tôi|giùm)?\s*(?:trước|lại|thêm)?\s*(\d+)\s*(phút|p|h|giờ|tiếng)\b", 
            ]
        }

    # Hàm trích xuất thông tin theo quy tắc
    def extract(self, text):
        results = {
            "time_str": None, "date_str": None,
            "day_month": None, "session": None,
            "special_type": None,
            
            "reminder_minutes": 15,  
            "reminder_str": None    
        }
        
        for p in self.patterns["time_absolute"]:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                results["time_str"] = match.group(0)
                if "rưỡi" in results["time_str"]: results["special_type"] = "half"
                if "kém" in results["time_str"]: results["special_type"] = "less"
                break
        
        for p in self.patterns["date_absolute"]:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                results["day_month"] = (int(match.group(1)), int(match.group(2)))
                break

        if not results["day_month"]:
            for p in self.patterns["weekday"]:
                match = re.search(p, text, re.IGNORECASE)
                if match:
                    results["date_str"] = match.group(0)
                    break
        
            if not results["date_str"]:
                for p in self.patterns["date_relative"]:
                    match = re.search(p, text, re.IGNORECASE)
                    if match:
                        results["date_str"] = match.group(0)
                        break
        
        for p in self.patterns["session"]:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                results["session"] = match.group(0)
                break

        for p in self.patterns["reminder"]:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                results["reminder_str"] = match.group(0) # Lưu cụm từ bắt được (VD: "nhắc trước 30p")
                val = int(match.group(1))
                unit = match.group(2).lower()
                
                # Quy đổi ra phút
                if unit in ['h', 'giờ', 'tiếng']:
                    results["reminder_minutes"] = val * 60
                else:
                    results["reminder_minutes"] = val
                break
                
        return results