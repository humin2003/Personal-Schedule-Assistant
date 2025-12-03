from underthesea import ner
import re
import unicodedata

def remove_accents(input_str):
    if not input_str: return ""
    s = unicodedata.normalize('NFD', str(input_str))
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')

class EntityExtractor:
    def __init__(self):
        # 1. TIỀN TỐ ĐỊA ĐIỂM
        self.place_prefixes = [
            "sân", "san", "rạp", "rap", "phòng", "phong", 
            "nhà hàng", "nha hang", "khách sạn", "khach san",
            "công ty", "cong ty", "trường", "truong", 
            "bệnh viện", "benh vien", "quán", "quan", 
            "siêu thị", "sieu thi", "chợ", "hồ", "ho", 
            "công viên", "cong vien", "toà", "toa",
            "chung cư", "chung cu", "shop", "cửa hàng",
            "trung tâm", "trung tam", "nhà sách", "nha sach", 
            "sân bay", "san bay", "bến", "ben", "biển", "bien"
            
        ]

        # 2. ĐỊA DANH PHỔ BIẾN
        self.common_locations = [
            "fpt software", "đại học fpt", "sân bay tân sơn nhất", "tân sơn nhất",
            "sân bay nội bài", "nội bài", "hà nội", "hồ chí minh", "sài gòn",
            "đà nẵng", "vũng tàu", "đà lạt", "nha trang", "phú quốc",
            "highland", "starbucks", "cali", "aeon", "bigc", "lotte", 
            "vincom", "landmark", "bitexco", "hồ gươm", "bờ hồ", "đồng xuân", "bến thành", 
            "thư viện", "cho Dong Xuan"
        ]

        # 3. TỪ CHẶN
        self.stop_words_pattern = r"(?:lúc|vào|ngày|hôm|sáng|trưa|chiều|tối|đêm|mua|bán|xem|ăn|uống|thăm|học|chơi|ngủ|làm|về|đi|để|gặp|với|chuyến|$)"

    def extract_location(self, text):
        if not text: return None
        
        # Chiến thuật 1: Prefix
        rule_prefix = self._extract_by_prefix(text)
        if rule_prefix: return rule_prefix.title()

        # Chiến thuật 2: Common Location (Check cả không dấu)
        text_no_accent = remove_accents(text).lower()
        for loc in self.common_locations:
            loc_no_accent = remove_accents(loc).lower()
            if re.search(rf"\b{loc}\b", text, re.IGNORECASE) or \
               re.search(rf"\b{loc_no_accent}\b", text_no_accent):
                return loc.title()

        # Chiến thuật 3: Preposition
        rule_prep = self._extract_by_preposition(text)
        if rule_prep: return rule_prep.title()
        
        # Chiến thuật 4: AI Fallback
        ai_loc = self._extract_by_ai(text)
        if ai_loc: return ai_loc

        return None

    def _extract_by_prefix(self, text):
        prefixes = "|".join(self.place_prefixes)
        pattern = rf"\b({prefixes})(?:\s+(.*?))?(?=\s+{self.stop_words_pattern}|\s*$)"
        
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            prefix = match.group(1)
            content = match.group(2)
            
            if content and re.match(rf"^{self.stop_words_pattern}", content, re.IGNORECASE):
                content = None

            if content: full_loc = f"{prefix} {content}"
            else: full_loc = prefix 
                
            if self._is_valid(full_loc): return full_loc
        return None
    
    def _extract_by_preposition(self, text):
        preps = r"(?:tại|ở|đến|về|qua|tai|o|den|ve|qua|trong|ngoài)" 
        pattern = rf"\b{preps}\s+(.*?)(?=\s+{self.stop_words_pattern}|\s*$)"
        
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            loc = match.group(1).strip()
            if self._is_valid(loc): return loc
        return None
    
    def _extract_by_ai(self, text):
        try:
            tokens = ner(text)
            locations = []
            current = []
            for token in tokens:
                if len(token) == 4: word, pos, chunk, tag = token
                else: word, pos, tag = token
                if tag == 'B-LOC':
                    if current: locations.append(" ".join(current))
                    current = [word]
                elif tag == 'I-LOC': current.append(word)
                else:
                    if current:
                        locations.append(" ".join(current))
                        current = []
            if current: locations.append(" ".join(current))
            valid_locs = [l for l in locations if self._is_valid(l)]
            return valid_locs[0] if valid_locs else None
        except: return None

    def _is_valid(self, loc):
        if not loc: return False
        if len(loc.split()) > 10: return False 
        loc_lower = loc.lower().strip()
        loc_no_accent = remove_accents(loc_lower)
        
        forbidden_single_words = [
            "ngủ", "chơi", "làm", "học", "xem", "ăn", "uống", "hẹn", "book", "mua", "bán", "đi", "về", "ghé", 
            "quê", "đồ", "quà", "rau", "củ", "thịt", "cơm", "bài", "tết"
        ]
        
        forbidden_phrases = ["rau cu", "rau củ", "do nau an", "đồ nấu ăn", "qua tet", "do an", "đồ ăn"]

        if loc_lower in forbidden_single_words: return False
        if loc_no_accent in forbidden_single_words: return False
        if loc_lower in forbidden_phrases: return False
        if loc_no_accent in forbidden_phrases: return False
        
        # [FIX QUAN TRỌNG] Thêm phiên bản không dấu cho phép đứng một mình
        allow_standalone = [
            "chợ", "siêu thị", "nhà sách", "sân bay", "trường", "công viên", "bệnh viện", "rạp", "thư viện", "công ty", "shop", "hồ",
            "cho", "sieu thi", "nha sach", "san bay", "truong", "cong vien", "benh vien", "rap", "thu vien", "cong ty", "ho"
        ]
        
        is_prefix_word = (loc_lower in self.place_prefixes)
        # Kiểm tra cả có dấu và không dấu trong danh sách cho phép
        if is_prefix_word:
             if (loc_lower not in allow_standalone) and (loc_no_accent not in allow_standalone):
                return False

        if re.search(r"\b(hôm|nay|mai|mốt|giờ|phút)\b", loc_lower): return False
        return True