import sys
import os
import csv
from datetime import datetime

# --- SETUP ĐƯỜNG DẪN ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from src.nlp.engine import NLPEngine

def normalize_str(s):
    """
    Chuẩn hóa chuỗi để so sánh:
    - Chuyển về chữ thường
    - Xóa khoảng trắng thừa
    - Coi 'none', 'chưa xác định', 'null' là rỗng ("")
    """
    if not s: return ""
    s = str(s).strip().lower()
    if s in ['none', 'chưa xác định', 'null', 'nan']:
        return ""
    return s

def run_test():
    print("🚀 Đang khởi động bộ test TOÀN DIỆN (Smart Matching)...")
    
    engine = NLPEngine()
    
    # Đảm bảo đường dẫn file đúng
    input_file = os.path.join(current_dir, 'tests', 'test_cases_2.csv')
    output_file = os.path.join(current_dir, 'tests', 'test_report_full2.csv')
    
    results = []
    correct_count = 0
    total_count = 0

    try:
        with open(input_file, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            # Header in ra màn hình
            print(f"{'ID':<4} {'STATUS':<7} {'TIME (Exp/Act)':<16} {'LOC (Exp/Act)':<25} {'EVENT'}")
            print("-" * 100)

            for row in reader:
                total_count += 1
                text = row['text']
                
                # --- 1. LẤY KẾT QUẢ MONG ĐỢI ---
                exp_time = row.get('expected_time', '')
                exp_loc_raw = row.get('expected_location', '')
                exp_evt_raw = row.get('expected_title', '')

                # --- 2. CHẠY NLP ENGINE ---
                try:
                    output = engine.process(text)
                    
                    # a. Time
                    actual_time_str = output.get('start_time', '')
                    if actual_time_str:
                        dt = datetime.fromisoformat(actual_time_str)
                        act_time = dt.strftime("%H:%M")
                    else:
                        act_time = "None"

                    # b. Location & Event
                    act_loc_raw = output.get('location', '')
                    act_evt_raw = output.get('event', '')

                except Exception as e:
                    act_time = "ERROR"
                    act_loc_raw = "ERROR"
                    act_evt_raw = "ERROR"

                # --- 3. SO SÁNH THÔNG MINH (SMART MATCH) ---
                
                # Check Time (Tuyệt đối)
                check_time = (exp_time == act_time)
                
                # Check Location (Đã chuẩn hóa None/Chưa xác định)
                n_exp_loc = normalize_str(exp_loc_raw)
                n_act_loc = normalize_str(act_loc_raw)
                check_loc = (n_exp_loc == n_act_loc) or (n_exp_loc in n_act_loc) or (n_act_loc in n_exp_loc)

                # Check Event (Tương đối - Chứa trong nhau là được)
                n_exp_evt = normalize_str(exp_evt_raw)
                n_act_evt = normalize_str(act_evt_raw)
                # Logic: Nếu chuỗi mong đợi nằm trong chuỗi thực tế (hoặc ngược lại) -> PASS
                check_evt = (n_exp_evt == n_act_evt) or (n_exp_evt in n_act_evt) or (n_act_evt in n_exp_evt)

                # --- 4. KẾT LUẬN ---
                if check_time and check_loc and check_evt:
                    status = "PASS"
                    correct_count += 1
                    icon = "✅"
                else:
                    status = "FAIL"
                    icon = "❌"

                # In ra màn hình console (Cắt ngắn bớt nếu dài quá để dễ nhìn)
                disp_time = f"{exp_time}/{act_time}"
                
                # Hiển thị location ngắn gọn
                l_e = exp_loc_raw if exp_loc_raw != 'None' else '-'
                l_a = act_loc_raw if act_loc_raw != 'Chưa xác định' else '-'
                disp_loc = f"{l_e}/{l_a}"[:24]
                
                print(f"{icon} {row['id']:<4} {status:<7} {disp_time:<16} {disp_loc:<25} {n_act_evt}")

                results.append({
                    "ID": row['id'],
                    "Input": text,
                    "Exp Time": exp_time, "Act Time": act_time,
                    "Exp Loc": exp_loc_raw, "Act Loc": act_loc_raw,
                    "Exp Event": exp_evt_raw, "Act Event": act_evt_raw,
                    "Result": status
                })

    except FileNotFoundError:
        print(f"❌ Lỗi: Không tìm thấy file csv test tại {input_file}")
        return

    # --- TỔNG KẾT ---
    accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
    print("="*60)
    print(f"🎯 KẾT QUẢ CUỐI CÙNG: {correct_count}/{total_count} passed")
    print(f"🏆 ĐỘ CHÍNH XÁC: {accuracy:.2f}%")
    print("="*60)
    
    # Xuất file báo cáo
    with open(output_file, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
        writer.writerow({})
        writer.writerow({"Input": f"ACCURACY: {accuracy:.2f}%"})

    print(f"📄 Xem báo cáo chi tiết tại: {output_file}")

if __name__ == "__main__":
    run_test()