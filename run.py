# File: run.py
import sys
import os
from streamlit.web import cli as stcli


def resolve_path(path):
    # Hàm này giúp tìm file khi đã đóng gói vào exe (sys._MEIPASS)
    if getattr(sys, "frozen", False):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)

if __name__ == '__main__':
    # 1. Cấu hình biến môi trường để Streamlit không cảnh báo lung tung
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "false"
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"

    # 2. Xác định đường dẫn file app.py
    app_path = resolve_path(os.path.join("src", "app.py"))
    
    # 3. Giả lập lệnh chạy
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
    ]
    
    # 4. Khởi chạy
    sys.exit(stcli.main())