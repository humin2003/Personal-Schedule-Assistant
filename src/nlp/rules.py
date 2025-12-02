import re

def extract_reminder(text):
    """
    Trích xuất thông tin nhắc trước bao lâu.
    Input: "... hãy nhắc tôi trước 30 phút ..."
    Output: (30, "text đã xóa cụm nhắc")
    """
    reminder_minutes = 15 # Mặc định
    
    # [FIX] Cập nhật Regex linh hoạt hơn:
    # 1. (?:hãy\s+)? -> Chấp nhận có chữ "hãy" hoặc không
    # 2. (?:nhắc|báo|gọi) -> Các từ khóa lệnh
    # 3. (?:\s+(?:tôi|mình|em|anh|chị|bạn|cho tôi))? -> Chấp nhận từ xưng hô ở giữa
    # 4. \s+(?:trước|sớm) -> Từ khóa thời gian
    
    pattern = r'(?:hãy\s+)?(?:nhắc|báo|gọi)(?:\s+(?:tôi|mình|em|anh|chị|bạn|cho tôi|cho mình))?\s+(?:trước|sớm)\s+(\d+)\s*(phút|p|tiếng|h|giờ)'
    
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        amount = int(match.group(1)) # Lấy số (VD: 25)
        unit = match.group(2).lower() # Lấy đơn vị (VD: phút)
        
        if unit in ['tiếng', 'h', 'giờ']:
            reminder_minutes = amount * 60
        else:
            reminder_minutes = amount
        
        # Xóa cụm này khỏi text để tên sự kiện sạch đẹp
        text = text.replace(match.group(0), '')
        
    return reminder_minutes, text