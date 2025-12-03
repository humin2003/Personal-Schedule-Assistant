# File: run.py
import sys
import os
from streamlit.web import cli as stcli

def resolve_path(path):
    if getattr(sys, "frozen", False):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)

if __name__ == '__main__':
    # Trỏ đúng vào file app.py trong thư mục src
    app_path = resolve_path(os.path.join("src", "app.py"))
    
    # Giả lập lệnh chạy: streamlit run src/app.py
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())