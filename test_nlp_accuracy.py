import sys
import os
import csv
from datetime import datetime

# --- [FIX 1] SETUP ĐƯỜNG DẪN ĐỂ IMPORT ĐƯỢC SRC TỪ ROOT ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import engine của BẠN (đã chia module)
from src.nlp.engine import NLPEngine

def run_test():
    print("🚀 Đang khởi động bộ test NLP...")
    
    # Khởi tạo Engine của bạn
    engine = NLPEngine()
    
    # Đường dẫn file csv (Tạo folder tests và file csv trước nhé)
    input_file = os.path.join(current_dir, 'tests', 'test_cases_2.csv')
    output_file = os.path.join(current_dir, 'tests', 'test_report_final2.csv')
    
    results = []
    correct_count = 0
    total_count = 0

    try:
        with open(input_file, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            print(f"{'ID':<5} {'EXPECTED':<10} {'ACTUAL':<10} {'STATUS':<10} {'INPUT'}")
            print("-" * 80)

            for row in reader:
                total_count += 1
                text = row['text']
                expected = row['expected_time'] # Giờ mong muốn (VD: 09:00)
                
                # --- [FIX 2] GỌI HÀM CỦA BẠN (process thay vì process_text) ---
                try:
                    output = engine.process(text) # <--- Sửa chỗ này
                    
                    # Lấy giờ thực tế từ kết quả
                    actual_time_str = output.get('start_time', '')
                    actual_hour_minute = "None"
                    
                    if actual_time_str:
                        dt = datetime.fromisoformat(actual_time_str)
                        actual_hour_minute = dt.strftime("%H:%M")
                except Exception as e:
                    actual_hour_minute = "ERROR"

                # --- SO SÁNH ---
                if expected == actual_hour_minute:
                    status = "PASS"
                    correct_count += 1
                else:
                    status = "FAIL"

                # In ra màn hình console cho đẹp
                icon = "✅" if status == "PASS" else "❌"
                print(f"{icon} {row['id']:<5} {expected:<10} {actual_hour_minute:<10} {text}")

                # Lưu kết quả
                results.append({
                    "ID": row['id'],
                    "Câu lệnh (Input)": text,
                    "Mong đợi": expected,
                    "Thực tế": actual_hour_minute,
                    "Kết quả": status
                })

    except FileNotFoundError:
        print(f"❌ Lỗi: Không tìm thấy file '{input_file}'. Hãy tạo file này trước!")
        return

    # --- TÍNH ĐIỂM ---
    accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
    
    print(f"\n==============================")
    print(f"TỔNG SỐ TEST: {total_count}")
    print(f"SỐ CÂU ĐÚNG: {correct_count}")
    print(f"ĐỘ CHÍNH XÁC: {accuracy:.2f}%")
    print(f"==============================")

    # Xuất báo cáo CSV
    with open(output_file, mode='w', newline='', encoding='utf-8-sig') as f:
        fieldnames = ["ID", "Câu lệnh (Input)", "Mong đợi", "Thực tế", "Kết quả"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
        writer.writerow({})
        writer.writerow({"Câu lệnh (Input)": f"ĐỘ CHÍNH XÁC: {accuracy:.2f}%"})

    print(f"📄 Đã xuất file báo cáo tại: {output_file}")

if __name__ == "__main__":
    run_test()