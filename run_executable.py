import streamlit.web.cli as stcli
import os, sys

def resolve_path(path):
    """Hàm này giúp tìm đường dẫn file khi đã đóng gói vào .exe"""
    if getattr(sys, 'frozen', False):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)

if __name__ == "__main__":
    # Trỏ đúng vào file app.py trong thư mục src
    app_path = resolve_path(os.path.join("src", "app.py"))
    
    # Giả lập lệnh: streamlit run src/app.py --global.developmentMode=false
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
    ]
    
    sys.exit(stcli.main())