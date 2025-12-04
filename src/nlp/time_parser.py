from datetime import datetime, timedelta
import re

class TimeParser:
    def __init__(self):
        pass

    # Hàm phân tích thời gian
    def parse_time(self, time_str, session=None, special_type=None):
        if not time_str: return None, None 
        
        now = datetime.now().replace(microsecond=0)
        hour, minute = 0, 0
        s_lower = time_str.lower().strip()

        try:
            # 1. XỬ LÝ ĐẶC BIỆT
            if special_type == "half":
                nums = re.findall(r"\d+", s_lower)
                if nums: hour, minute = int(nums[0]), 30
            elif special_type == "less":
                nums = re.findall(r"\d+", s_lower)
                if len(nums) >= 2:
                    t = datetime(2000, 1, 1, int(nums[0]), 0) - timedelta(minutes=int(nums[1]))
                    hour, minute = t.hour, t.minute
            else:
                # 2. XỬ LÝ CHUẨN
                s_clean = s_lower.replace("a.m", "am").replace("p.m", "pm")
                is_pm = "pm" in s_clean
                is_am = "am" in s_clean
                
                clean = re.sub(r"[^\d:]", "", s_clean.replace("h", ":").replace("g", ":").replace("giờ", ":"))
                
                if ':' in clean:
                    parts = clean.split(':')
                    hour = int(parts[0])
                    minute = int(parts[1]) if parts[1] else 0
                elif clean: 
                    hour = int(clean)
                    minute = 0
                
                if is_pm and hour < 12: hour += 12
                elif is_am and hour == 12: hour = 0
                elif not is_pm and not is_am and session:
                    ss = session.lower()
                    if ss in ['chiều', 'tối', 'chieu', 'toi']:
                        if hour < 12: hour += 12
                    elif ss in ['đêm', 'dem']:
                        if hour == 12: hour = 0
                        elif hour >= 6 and hour != 12: hour += 12
            
            if not (0 <= hour <= 23): return None, f"Giờ không hợp lệ: {hour}h"
            if not (0 <= minute <= 59): return None, f"Phút không hợp lệ: {minute}p"
            
            return now.replace(hour=hour, minute=minute, second=0), None

        except: return None, f"Lỗi đọc giờ: {time_str}"

    # Hàm phân tích ngày tháng
    def parse_date(self, date_str, day_month_tuple=None):
        today = datetime.now().replace(microsecond=0)
        if day_month_tuple:
            d, m = day_month_tuple
            year = today.year
            try:
                target = today.replace(year=year, month=m, day=d)
                if (today - target).days > 30: target = target.replace(year=year+1)
                return target, True
            except: return None, False

        if not date_str: return today, True
        s = date_str.lower()
        if "hôm nay" in s or "hom nay" in s: return today, True
        if "mai" in s: return today + timedelta(days=1), True
        if "mốt" in s or "kia" in s: return today + timedelta(days=2), True
        
        weekdays = {"hai": 0, "2": 0, "ba": 1, "3": 1, "tư": 2, "4": 2, "năm": 3, "5": 3, "sáu": 4, "6": 4, "bảy": 5, "7": 5, "chủ nhật": 6, "cn": 6, "t2": 0, "t3": 1, "t4": 2, "t5": 3, "t6": 4, "t7": 5}
        target_date = today
        found_weekday = False
        for key, val in weekdays.items():
            if re.search(rf"\b{key}\b", s) or (key.isdigit() and f"thứ {key}" in s):
                current_wd = today.weekday()
                days_diff = val - current_wd
                target_date = today + timedelta(days=days_diff)
                found_weekday = True
                break
        
        if found_weekday:
            if "tuần sau" in s or "tuần tới" in s or "tuan sau" in s: target_date += timedelta(days=7)
            else:
                if target_date < today: target_date += timedelta(days=7)
            return target_date, True
            
        if "cuối tuần" in s or "cuoi tuan" in s:
            days_until_sunday = 6 - today.weekday()
            target_date = today + timedelta(days=days_until_sunday)
            if "sau" in s or "tới" in s: target_date += timedelta(days=7)
            return target_date, True

        return today, True