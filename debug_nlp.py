import sys
import os
import json

# Đoạn này quan trọng: Giúp Python tìm thấy folder 'src'
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.nlp import NLPEngine

def main():
    engine = NLPEngine()
    print("\n" + "="*40)
    print("TOOL TEST NLP (Gõ 'exit' để thoát)")
    print("="*40)

    while True:
        try:
            user_input = input("\n>> Nhập câu lệnh: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            
            if not user_input.strip():
                continue

            result = engine.process(user_input)

            # In kết quả JSON đẹp
            print("-" * 20)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        except Exception as e:
            print(f"Lỗi: {e}")

if __name__ == "__main__":
    main()