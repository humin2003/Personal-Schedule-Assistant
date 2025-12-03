import streamlit as st
import pandas as pd
import sys
import os
import time
import threading
import sqlite3
import json
from datetime import datetime, timedelta
from streamlit_calendar import calendar
import streamlit.components.v1 as components # [MỚI] Thêm thư viện này để hiển thị HTML

# --- CONFIG ---
st.set_page_config(page_title="Trợ lý Lịch trình AI", layout="wide")

# Thử import notification
try:
    from plyer import notification
    HAS_NOTI = True
except ImportError:
    HAS_NOTI = False

# --- SETUP PATH ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# --- [QUAN TRỌNG] IMPORT MODULES ---
from src.nlp import NLPEngine
from src.database import DatabaseManager

# --- INIT STATE ---
if 'db' not in st.session_state: st.session_state.db = DatabaseManager()
if 'nlp' not in st.session_state: st.session_state.nlp = NLPEngine()

# [MỚI] Biến để lưu trạng thái chờ xác nhận
if 'confirm_mode' not in st.session_state: st.session_state.confirm_mode = False
if 'pending_event_data' not in st.session_state: st.session_state.pending_event_data = None

db = st.session_state.db
nlp = st.session_state.nlp

# --- BACKGROUND THREAD ---
def run_scheduler():
    while True:
        try:
            conn = sqlite3.connect('data/schedule.db')
            cursor = conn.cursor()
            now = datetime.now()
            cursor.execute("SELECT event_content, start_time, location, reminder_minutes, is_all_day FROM events")
            rows = cursor.fetchall()
            for row in rows:
                event_content, start_str, loc, rem_min, is_all_day = row
                if is_all_day: continue 
                
                start_dt = datetime.fromisoformat(start_str)
                rem_time = start_dt - timedelta(minutes=rem_min)
                if rem_time <= now <= rem_time + timedelta(seconds=59):
                     notification.notify(title=f"Lời nhắc: {event_content}", message=f"Lúc {start_dt.strftime('%H:%M')} tại {loc}", app_name="Lời nhắc", timeout=10)
            conn.close()
        except Exception: pass
        time.sleep(60)

if 'scheduler_started' not in st.session_state:
    threading.Thread(target=run_scheduler, daemon=True).start()
    st.session_state['scheduler_started'] = True

# --- HEADER ---
st.title("Trợ lý Quản lý Lịch trình Thông minh")
st.markdown("---")

# [CẬP NHẬT] Thêm Tab 4 vào danh sách
tab1, tab2, tab3, tab4 = st.tabs(["➕ Thêm sự kiện", "Xem Lịch Biểu", "Quản lý & Xuất file", "📊 Báo cáo Kiểm thử"])

# --- TAB 1: THÊM SỰ KIỆN ---
with tab1:
    st.subheader("Nhập liệu ngôn ngữ tự nhiên")
    st.caption("Ví dụ: 'Họp team lúc 9h đến 11h sáng mai ở phòng 302', 'Mai đi chơi cả ngày'")
    
    def handle_add_event():
        raw_text = st.session_state.input_main
        if raw_text.strip():
            try:
                # 1. Xử lý NLP
                data = nlp.process(raw_text)
                
                # 2. Kiểm tra quá khứ
                start_dt = datetime.fromisoformat(data['start_time'])
                now = datetime.now()
                
                # Logic: Nếu không phải cả ngày VÀ ở quá khứ -> BẬT CHẾ ĐỘ XÁC NHẬN
                if not data.get('is_all_day') and start_dt < now:
                    st.session_state.confirm_mode = True        # Bật cờ xác nhận
                    st.session_state.pending_event_data = data  # Lưu tạm dữ liệu
                    st.session_state.input_main = ""            # Xóa ô nhập cho gọn
                    
                else:
                    # Nếu là tương lai -> Thêm luôn như bình thường
                    db.add_event(data)
                    st.toast(f"Đã thêm: {data['event']}")
                    st.session_state.input_main = ""
                    st.session_state.confirm_mode = False # Reset cờ
                    
            except ValueError as e:
                st.toast(f"Lỗi: {str(e)}")

    c1, c2 = st.columns([5, 1])
    with c1: st.text_input("Nhập câu lệnh tại đây:", key="input_main", placeholder="Gõ lệnh và nhấn Enter hoặc nút Thêm...")
    with c2: 
        st.write("")
        st.write("")
        st.button("Thêm ngay", type="primary", on_click=handle_add_event, width='stretch')

    # --- [MỚI] GIAO DIỆN XÁC NHẬN (Hiện ra khi cần confirm) ---
    if st.session_state.confirm_mode and st.session_state.pending_event_data:
        pending_data = st.session_state.pending_event_data
        start_time_str = datetime.fromisoformat(pending_data['start_time']).strftime('%H:%M %d/%m/%Y')
        
        # Hiện khung cảnh báo màu vàng
        with st.container(border=True):
            st.warning(f"**Xác nhận:** Sự kiện **'{pending_data['event']}'** diễn ra lúc **{start_time_str}** (Quá khứ).")
            st.write("Bạn có chắc chắn muốn thêm không?")
            
            col_yes, col_no = st.columns(2)
            
            # Nút ĐỒNG Ý
            if col_yes.button("Có", width='stretch'):
                db.add_event(pending_data) # Thêm vào DB từ biến tạm
                st.toast(f"Đã thêm sự kiện: {pending_data['event']}",)
                time.sleep(1)
                
                # Reset trạng thái
                st.session_state.confirm_mode = False
                st.session_state.pending_event_data = None
                st.rerun() # Chạy lại để ẩn khung xác nhận
            
            # Nút HỦY
            if col_no.button("Không, hủy bỏ", width='stretch'):
                st.toast("Đã hủy thao tác!")
                time.sleep(1)
                
                # Reset trạng thái
                st.session_state.confirm_mode = False
                st.session_state.pending_event_data = None
                st.rerun()
        
        
    st.write("")
    st.markdown("##### Sự kiện sắp tới")
    df_preview = db.get_all_events().head(5)
    if not df_preview.empty:
        st.dataframe(df_preview[['event_content', 'start_time', 'location']], hide_index=True, width='stretch')

# --- TAB 2: LỊCH BIỂU ---
with tab2:
    df_events = db.get_all_events()
    
    c_view, _ = st.columns([2, 5])
    with c_view:
        view_mode = st.radio("Chế độ xem:", ["Lịch biểu", "Danh sách"], horizontal=True, label_visibility="collapsed", index=0)

    if view_mode == "Lịch biểu":
        calendar_events = []
        for _, row in df_events.iterrows():
            try:
                event_dt = pd.to_datetime(row['start_time'])
                iso_start = event_dt.strftime("%Y-%m-%dT%H:%M:%S")
                # Xử lý end_time
                if row['end_time']:
                    end_dt = pd.to_datetime(row['end_time'])
                else:
                    end_dt = event_dt + timedelta(minutes=60)
                iso_end = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
                
                is_past = event_dt < datetime.now()
                color = "#6c757d" if is_past else "#3a86ff"
                is_all_day_db = bool(row.get('is_all_day', 0))
                title_text = row['event_content'].strip().capitalize()
                
                calendar_events.append({
                    "title": title_text,
                    "start": iso_start,
                    "end": iso_end,
                    "backgroundColor": color,
                    "borderColor": color,
                    "allDay": is_all_day_db
                })
            except: continue

        calendar_options = {
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,listWeek"
            },
            "buttonText": {
                "today": "Hôm nay",
                "dayGridMonth": "Tháng",
                "timeGridWeek": "Tuần",
                "listWeek": "Danh sách"
            },
            "initialView": "dayGridMonth",
            "eventDisplay": "block",
            "height": 700,
            "slotMinTime": "06:00:00",
            "slotMaxTime": "24:00:00",
            "allDaySlot": True,
            "navLinks": True,
            
            # [FIX] Đổi tên All Day và Format 24h
            "allDayText": "All Day",
            "slotLabelFormat": {
                "hour": "2-digit", "minute": "2-digit", "hour12": False, "meridiem": False
            },
            "eventTimeFormat": {
                "hour": "2-digit", "minute": "2-digit", "hour12": False
            }
        }

        custom_css = """
            .fc {
                font-family: 'Segoe UI', sans-serif;
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            .fc-scrollgrid {
                border: 1px solid #444 !important;
                border-radius: 12px !important;
                overflow: hidden;
            }
            .fc-theme-standard td, .fc-theme-standard th {
                border-color: #383838 !important;
            }
            .fc-col-header-cell {
                background-color: #2D2D2D;
                padding: 12px 0 !important;
            }
            .fc-col-header-cell-cushion {
                color: #FF4B4B !important;
                font-weight: 700;
                text-transform: uppercase;
                font-size: 0.9rem;
            }
            .fc-button {
                background-color: #2D2D2D !important;
                border: 1px solid #444 !important;
                text-transform: capitalize !important;
                font-weight: 600 !important;
                border-radius: 8px !important;
                padding: 6px 16px !important;
                box-shadow: none !important;
            }
            .fc-button:hover { background-color: #3E3E3E !important; }
            .fc-button-active {
                background-color: #FF4B4B !important;
                border-color: #FF4B4B !important;
                color: white !important;
            }
            .fc-toolbar-title { font-size: 1.5rem !important; font-weight: 700; color: white; }
            .fc-day-today { background-color: rgba(255, 75, 75, 0.08) !important; }
            .fc-event {
                border-radius: 4px !important;
                padding: 2px 4px;
                font-size: 0.85rem;
                border: none !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
        """

        calendar(events=calendar_events, options=calendar_options, custom_css=custom_css, key="cal_v_final")

    else:
        st.markdown("### Danh sách sự kiện")
        if df_events.empty:
            st.info("Chưa có sự kiện nào.")
        else:
            for _, row in df_events.iterrows():
                event_dt = pd.to_datetime(row['start_time'])
                is_all_day_db = bool(row.get('is_all_day', 0))
                time_display = "🟦 Cả ngày" if is_all_day_db else f"{event_dt.strftime('%H:%M')}"
                
                st.markdown(f"""
                <div style="background-color: #262730; padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #333; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 1.1em; font-weight: bold; color: #FFF; margin-bottom: 4px;">{row['event_content']}</div>
                        <div style="color: #AAA; font-size: 0.9em;"> Địa điểm: {row['location']}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: #FF4B4B; font-weight: bold;">{event_dt.strftime('%d/%m/%Y')}</div>
                        <div style="color: #FFBD45; font-size: 0.9em;">{time_display}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# --- TAB 3: QUẢN LÝ & IMPORT/EXPORT ---
with tab3:
    st.subheader("Công cụ quản lý dữ liệu")
    
    col_backup, col_restore = st.columns(2)
    
    # --- 1. XUẤT DỮ LIỆU ---
    with col_backup:
        st.markdown("#### Sao lưu dữ liệu")
        st.caption("Xuất toàn bộ lịch trình ra file JSON.")
        
        all_events = db.get_all_events()
        if not all_events.empty:
            json_str = all_events.to_json(orient='records', force_ascii=False, indent=2)
            st.download_button("Tải file Backup (.json)", json_str, "schedule_backup.json", "application/json", width='stretch')
        else:
            st.info("Chưa có dữ liệu.")

    # --- 2. NHẬP DỮ LIỆU (RESTORE - FIX) ---
    with col_restore:
        st.markdown("#### Khôi phục dữ liệu")
        st.caption("Nhập file JSON để thêm lại sự kiện.")
        
        uploaded_file = st.file_uploader("Chọn file .json", type=['json'], label_visibility="collapsed")
        
        if uploaded_file is not None:
            if st.button("Bắt đầu Import", type="primary", width='stretch'):
                try:
                    df_new = pd.read_json(uploaded_file)
                    
                    if df_new.empty:
                        st.warning("File rỗng!")
                    else:
                        success_count = 0
                        for _, row in df_new.iterrows():
                            # [FIX 1] Xử lý lỗi Timestamp
                            s_time = row.get('start_time')
                            e_time = row.get('end_time')
                            if isinstance(s_time, pd.Timestamp): s_time = s_time.isoformat()
                            if isinstance(e_time, pd.Timestamp): e_time = e_time.isoformat()

                            # [FIX 2] Xử lý original_text bị mất hoặc thành số 0
                            raw_text = row.get('original_text', '')
                            # Nếu là số 0 hoặc NaN -> chuyển thành chuỗi rỗng
                            if pd.isna(raw_text) or str(raw_text) == '0': 
                                raw_text = ""
                            else:
                                raw_text = str(raw_text)

                            # Mapping dữ liệu
                            event_data = {
                                "event": row.get('event_content', 'Sự kiện Import'),
                                "start_time": s_time,
                                "end_time": e_time,
                                "location": row.get('location', ''),
                                "reminder_minutes": row.get('reminder_minutes', 0),
                                "is_all_day": row.get('is_all_day', 0),
                                "original_text": raw_text # <-- Đã xử lý sạch
                            }
                            db.add_event(event_data)
                            success_count += 1
                        
                        st.success(f"✅ Đã khôi phục {success_count} sự kiện!")
                        time.sleep(1.5)
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    st.markdown("---")
    # --- 3. BẢNG DỮ LIỆU & TÌM KIẾM (Đã nâng cấp) ---
    st.markdown("### Dữ liệu hiện tại")
    
    # [MỚI] Thanh tìm kiếm
    c_search, c_total = st.columns([4, 1])
    with c_search:
        search_term = st.text_input("Tìm kiếm nhanh:", placeholder="Nhập tên sự kiện, hoặc địa điểm", label_visibility="collapsed")
    
    # Lấy dữ liệu
    all_events = db.get_all_events()
    
    # [LOGIC LỌC]
    if search_term:
        # Chuyển từ khóa về chữ thường để tìm không phân biệt hoa/thường
        term_lower = search_term.lower()
        
        # Lọc trên các cột quan trọng
        filtered_df = all_events[
            all_events['original_text'].str.lower().str.contains(term_lower, na=False)
        ]
    else:
        filtered_df = all_events

    # --- 3. BẢNG DỮ LIỆU ---
    st.dataframe(filtered_df, width='stretch', height=300, hide_index=True)

    # --- 4. FORM SỬA (Logic cũ giữ nguyên hoặc copy lại nếu cần) ---
    st.write("#### Chỉnh sửa theo ID")
    event_id_input = st.number_input("Nhập ID sự kiện:", min_value=0, step=1)
    if event_id_input > 0:
        evt = db.get_event_by_id(event_id_input)
        if evt is not None:
            with st.expander(f"Sửa ID: {event_id_input}", expanded=True):
                with st.form("edit_form"):
                    # Hiển thị text gốc
                    st.text_area("Câu lệnh gốc:", value=evt['original_text'], disabled=True)
                    
                    c1, c2 = st.columns(2)
                    new_content = c1.text_input("Tên sự kiện", value=evt['event_content'])
                    new_loc = c2.text_input("Địa điểm", value=evt['location'])
                    
                    is_all_day = st.checkbox("Cả ngày?", value=bool(evt.get('is_all_day', 0)))
                    
                    # Xử lý datetime để hiển thị lên form
                    try:
                        cur_start = pd.to_datetime(evt['start_time'])
                        cur_end = pd.to_datetime(evt['end_time']) if evt['end_time'] else cur_start + timedelta(hours=1)
                        
                        d_col, t1_col, t2_col, rem_col = st.columns(4)
                        new_date = d_col.date_input("Ngày", value=cur_start.date())
                        new_start = t1_col.time_input("Bắt đầu", value=cur_start.time(), disabled=is_all_day)
                        new_end = t2_col.time_input("Kết thúc", value=cur_end.time(), disabled=is_all_day)
                        new_rem = rem_col.number_input("Nhắc trước (phút)", value=evt['reminder_minutes'])
                    except: pass

                    if st.form_submit_button("Lưu thay đổi", type="primary", width='stretch'):
                        # Logic lưu thời gian
                        if is_all_day:
                            s_dt = datetime.combine(new_date, datetime.min.time())
                            e_dt = s_dt + timedelta(days=1)
                        else:
                            s_dt = datetime.combine(new_date, new_start)
                            e_dt = datetime.combine(new_date, new_end)
                            if e_dt <= s_dt: e_dt = s_dt + timedelta(hours=1)
                        
                        db.update_event(event_id_input, new_content, new_loc, s_dt.isoformat(), e_dt.isoformat(), new_rem, is_all_day)
                        st.toast("Đã lưu!")
                        time.sleep(1)
                        st.rerun()

                    if st.form_submit_button("Xóa", type="secondary", width='stretch'):
                        db.delete_event(event_id_input)
                        st.toast("Đã xóa!")
                        time.sleep(1)
                        st.rerun()

# --- TAB 4: BÁO CÁO KIỂM THỬ (DASHBOARD) ---
with tab4:
    st.header("📊 NLP Accuracy Dashboard")
    st.caption("Tải lên file `test_report.csv` để xem kết quả kiểm thử.")
    
    uploaded_report = st.file_uploader("Chọn file CSV:", type=['csv'], label_visibility="collapsed")
    json_data = "[]" 

    if uploaded_report is not None:
        try:
            # 1. Đọc file thông minh (tự nhận diện dấu phẩy/chấm phẩy)
            df_report = pd.read_csv(uploaded_report, encoding='utf-8-sig', sep=None, engine='python')
            
            # Chuẩn hóa tên cột (về chữ thường, xóa khoảng trắng)
            df_report.columns = df_report.columns.str.strip()
            # Mapping tên cột linh hoạt
            cols = {c.lower(): c for c in df_report.columns}
            
            # Tìm cột ID (ưu tiên 'id', 'ID')
            id_col = cols.get('id')
            
            if id_col is None:
                st.error(f"❌ Không tìm thấy cột ID. Các cột có trong file: {list(df_report.columns)}")
            else:
                st.success(f"Đã tải: {uploaded_report.name} ({len(df_report)} dòng)")
                
                mapped_data = []
                for _, row in df_report.iterrows():
                    row_id = row[id_col]
                    
                    # Bỏ qua dòng tổng kết
                    if pd.isna(row_id) or str(row_id).strip().upper().startswith('ACCURACY'): continue
                    
                    # Helper tìm giá trị từ nhiều tên cột khác nhau (Tiếng Anh/Việt)
                    def get_val(keys):
                        for k in keys:
                            if k.lower() in cols: return row[cols[k.lower()]]
                        return ""

                    mapped_data.append({
                        "id": row_id,
                        "text": get_val(['Input', 'Câu lệnh (Input)', 'text']),
                        "expected_time": get_val(['Exp Time', 'Expected Time', 'Mong đợi', 'expected_time']),
                        "actual_time": get_val(['Act Time', 'Actual Time', 'Thực tế', 'actual_time']),
                        "expected_loc": get_val(['Exp Loc', 'Expected Loc', 'Expected Location', 'expected_location']),
                        "actual_loc": get_val(['Act Loc', 'Actual Loc', 'Actual Location', 'actual_location']),
                        "expected_title": get_val(['Exp Event', 'Expected Event', 'Expected Title', 'expected_title']),
                        "actual_title": get_val(['Act Event', 'Actual Event', 'Actual Title', 'actual_title']),
                        "status": get_val(['Result', 'Kết quả', 'status']) or 'FAIL',
                        "error": "" 
                    })
                
                json_data = json.dumps(mapped_data, ensure_ascii=False)
                
        except Exception as e:
            st.error(f"❌ Lỗi đọc file: {e}")

    # Nội dung HTML Dashboard
    html_template = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ background-color: #ffffff; font-family: 'Segoe UI', sans-serif; }}
            .card {{ border: none; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-radius: 12px; margin-bottom: 20px; }}
            .status-pass {{ color: #198754; font-weight: bold; background: #d1e7dd; padding: 4px 8px; border-radius: 6px; }}
            .status-fail {{ color: #dc3545; font-weight: bold; background: #f8d7da; padding: 4px 8px; border-radius: 6px; }}
            .metric-value {{ font-size: 2.5rem; font-weight: 700; color: #333; }}
            .text-muted-small {{ font-size: 0.85em; color: #6c757d; display: block; margin-top: 2px; }}
        </style>
    </head>
    <body>
    <div class="container-fluid py-4">
        <div class="row mb-4">
            <div class="col-md-3"><div class="card p-3 text-center border-start border-5 border-primary"><div class="metric-value" id="totalCases">0</div><div class="text-muted">Tổng Test Case</div></div></div>
            <div class="col-md-3"><div class="card p-3 text-center border-start border-5 border-success"><div class="metric-value text-success" id="totalPass">0</div><div class="text-muted">Pass</div></div></div>
            <div class="col-md-3"><div class="card p-3 text-center border-start border-5 border-danger"><div class="metric-value text-danger" id="totalFail">0</div><div class="text-muted">Fail</div></div></div>
            <div class="col-md-3"><div class="card p-3 text-center border-start border-5 border-warning"><div class="metric-value text-warning" id="accuracy">0%</div><div class="text-muted">Độ Chính Xác</div></div></div>
        </div>
        <div class="row mb-4">
            <div class="col-md-8"><div class="card p-4"><h5 class="mb-4"><i class="fas fa-chart-pie me-2"></i>Biểu đồ</h5><div style="height: 300px;"><canvas id="resultChart"></canvas></div></div></div>
            <div class="col-md-4"><div class="card p-4 h-100"><h5 class="mb-4"><i class="fas fa-filter me-2"></i>Bộ lọc</h5><div class="d-grid gap-3"><button class="btn btn-outline-primary" onclick="filterData('ALL')">Tất cả</button><button class="btn btn-outline-success" onclick="filterData('PASS')">Pass</button><button class="btn btn-outline-danger" onclick="filterData('FAIL')">Fail</button></div></div></div>
        </div>
        <div class="card">
            <div class="card-header bg-white py-3"><h5><i class="fas fa-table me-2"></i>Chi tiết</h5></div>
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light">
                        <tr>
                            <th>ID</th><th style="width:25%">Input</th>
                            <th>Time <span style="font-size:0.8em; font-weight:normal">(Exp / Act)</span></th>
                            <th>Loc <span style="font-size:0.8em; font-weight:normal">(Exp / Act)</span></th>
                            <th>Event <span style="font-size:0.8em; font-weight:normal">(Exp / Act)</span></th>
                            <th>Result</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody"></tbody>
                </table>
            </div>
        </div>
    </div>
    <script>
        const testData = {json_data};
        let currentData = testData;
        let chartInstance = null;
        function init() {{ calcMetrics(); renderTable(testData); if(testData.length>0) renderChart(); }}
        function calcMetrics() {{
            const total=testData.length; const pass=testData.filter(d=>d.status==='PASS').length;
            document.getElementById('totalCases').innerText=total; document.getElementById('totalPass').innerText=pass;
            document.getElementById('totalFail').innerText=total-pass;
            document.getElementById('accuracy').innerText=total>0?((pass/total)*100).toFixed(2)+'%':'0%';
        }}
        function renderTable(data) {{
            const tb=document.getElementById('tableBody'); tb.innerHTML='';
            data.forEach(r=>{{
                const cls=r.status==='PASS'?'status-pass':'status-fail';
                // Highlight nếu sai
                const timeCls = r.expected_time !== r.actual_time ? 'text-danger fw-bold' : '';
                const locCls = r.expected_loc !== r.actual_loc ? 'text-danger fw-bold' : '';
                const titleCls = r.expected_title !== r.actual_title ? 'text-danger fw-bold' : '';
                
                tb.innerHTML+=`<tr>
                    <td class="fw-bold">#${{r.id}}</td><td>${{r.text}}</td>
                    <td>${{r.expected_time}}<span class="text-muted-small ${{timeCls}}">${{r.actual_time}}</span></td>
                    <td>${{r.expected_loc}}<span class="text-muted-small ${{locCls}}">${{r.actual_loc}}</span></td>
                    <td>${{r.expected_title}}<span class="text-muted-small ${{titleCls}}">${{r.actual_title}}</span></td>
                    <td><span class="${{cls}}">${{r.status}}</span></td>
                </tr>`;
            }});
        }}
        function renderChart() {{
            const ctx=document.getElementById('resultChart').getContext('2d');
            const pass=testData.filter(d=>d.status==='PASS').length;
            if(chartInstance) chartInstance.destroy();
            chartInstance=new Chart(ctx,{{type:'doughnut',data:{{labels:['Pass','Fail'],datasets:[{{data:[pass,testData.length-pass],backgroundColor:['#198754','#dc3545'],borderWidth:0}}]}},options:{{responsive:true,maintainAspectRatio:false,cutout:'70%'}}}});
        }}
        function filterData(t) {{ currentData=t==='ALL'?testData:testData.filter(d=>d.status===t); renderTable(currentData); }}
        init();
    </script>
    </body>
    </html>
    """
    components.html(html_template, height=800, scrolling=True)