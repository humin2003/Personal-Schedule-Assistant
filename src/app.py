import streamlit as st
import pandas as pd
import sys
import os
import time
import threading
import sqlite3
from datetime import datetime, timedelta

# --- IMPORT THƯ VIỆN CALENDAR ---
from streamlit_calendar import calendar

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

from src.nlp_engine import NLPEngine
from src.database import DatabaseManager

# --- CONFIG ---
st.set_page_config(page_title="Trợ lý Lịch trình AI", page_icon="📅", layout="wide")

# Khởi tạo object (chỉ 1 lần để tối ưu)
if 'db' not in st.session_state:
    st.session_state.db = DatabaseManager()
if 'nlp' not in st.session_state:
    st.session_state.nlp = NLPEngine()

db = st.session_state.db
nlp = st.session_state.nlp

# --- BACKGROUND THREAD ---
# Sửa lại trong app.py
def run_scheduler():
    while True:
        try:
            # Tạo connection thủ công mỗi lần quét để tránh lỗi "SQLite objects created in a thread..."
            # Quan trọng: Phải import sqlite3 và trỏ đúng đường dẫn file db
            conn = sqlite3.connect('data/schedule.db') 
            cursor = conn.cursor()
            
            # Query lấy các sự kiện sắp diễn ra trong 1 phút tới
            now = datetime.now()
            next_minute = now + timedelta(minutes=1)
            
            # Logic này đơn giản hơn dataframe nhiều
            cursor.execute("SELECT event_content, start_time, location, reminder_minutes FROM events")
            rows = cursor.fetchall()
            
            for row in rows:
                event_content, start_str, loc, rem_min = row
                start_dt = datetime.fromisoformat(start_str)
                rem_time = start_dt - timedelta(minutes=rem_min)
                
                # Nếu thời gian hiện tại trùng khớp thời gian nhắc (trong khoảng 60s)
                if rem_time <= now <= rem_time + timedelta(seconds=59):
                     notification.notify(
                        title=f"🔔 Sắp diễn ra: {event_content}",
                        message=f"Lúc {start_dt.strftime('%H:%M')} tại {loc}",
                        timeout=10
                    )
            conn.close()
        except Exception as e:
            print(f"Lỗi Scheduler: {e}")
        
        time.sleep(60)

if 'scheduler_started' not in st.session_state:
    threading.Thread(target=run_scheduler, daemon=True).start()
    st.session_state['scheduler_started'] = True

# --- GIAO DIỆN CHÍNH ---
st.title("📅 Trợ lý Quản lý Lịch trình Thông minh")

tab1, tab2, tab3 = st.tabs(["➕ Thêm sự kiện", "🗓️ Xem Lịch Tháng", "⚙️ Quản lý & Danh sách"])

# --- TAB 1: NHẬP LIỆU (ĐÃ SỬA LỖI STATE) ---
with tab1:
    st.subheader("Nhập liệu ngôn ngữ tự nhiên")

    # [FIX] Hàm Callback: Chạy xử lý TRƯỚC khi giao diện render lại
    def handle_add_event():
        # Lấy text từ session_state thông qua key
        raw_text = st.session_state.input_main
        
        if raw_text.strip():
            # Xử lý NLP & DB
            data = nlp.process(raw_text)
            db.add_event(data)
            
            # Thông báo
            st.toast(f"✅ Đã thêm: {data['event']}", icon="🎉")
            
            # Xóa trắng ô nhập liệu (An toàn tuyệt đối ở đây)
            st.session_state.input_main = ""

    col_input, col_btn = st.columns([5, 1])
    with col_input:
        # Key="input_main" để liên kết với session_state
        st.text_input(
            "Ví dụ: 'Họp team tại phòng 302 lúc 9h sáng mai'", 
            key="input_main"
        )
    with col_btn:
        st.write("") 
        st.write("") 
        # Gắn hàm handle_add_event vào nút bấm
        st.button("Thêm ngay", type="primary", on_click=handle_add_event)

    st.divider()
    st.caption("Sự kiện sắp tới:")
    df_preview = db.get_all_events().head(5)
    st.dataframe(df_preview[['event_content', 'start_time', 'location']], hide_index=True)

# --- TAB 2: LỊCH THÁNG ---
# --- TAB 2: LỊCH THÁNG (ĐÃ NÂNG CẤP GIAO DIỆN) ---
# --- TAB 2: LỊCH THÁNG (FIX LỖI HIỂN THỊ & CHIỀU CAO) ---
# --- TAB 2: LỊCH BIỂU (PHIÊN BẢN MODERN DARK UI) ---
# --- TAB 2: LỊCH BIỂU (PHIÊN BẢN FIX FINAL - ỔN ĐỊNH NHẤT) ---
with tab2:
    df_events = db.get_all_events()
    
    if df_events.empty:
        st.info("📭 Chưa có sự kiện nào. Hãy qua tab 'Thêm sự kiện' để tạo mới!")
    else:
        # Move radio ra giữa
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            view_mode = st.radio("Chế độ xem:", ["📅 Lịch biểu", "📝 Danh sách chi tiết"], horizontal=True, label_visibility="collapsed")
        
        if view_mode == "📅 Lịch biểu":
            calendar_events = []
            
            def clean_title(text):
                if not text: return "Sự kiện"
                text = text.replace("'", "").replace('"', "").strip()
                return text[0].upper() + text[1:]

            for _, row in df_events.iterrows():
                try:
                    # start
                    event_dt = pd.to_datetime(row['start_time'])
                    iso_start = event_dt.strftime("%Y-%m-%dT%H:%M:%S")
                    
                    # end - LẤY TỪ DB
                    if row['end_time']:
                        end_dt = pd.to_datetime(row['end_time'])
                    else:
                        # Fallback nếu dữ liệu cũ không có end_time
                        end_dt = event_dt + timedelta(minutes=60)
                        
                    iso_end = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
                    

                    is_past = event_dt < datetime.now()
                    color = "#495057" if is_past else "#3a86ff" 
                    
                    calendar_events.append({
                        "title": clean_title(row['event_content']),
                        "start": iso_start,
                        "end": iso_end,
                        "backgroundColor": color,
                        "borderColor": color,
                        "allDay": False
                    })
                except:
                    continue

            # --- CẤU HÌNH FULLCALENDAR ---
            calendar_options = {
                "headerToolbar": {
                    "left": "prev,next today",
                    "center": "title",
                    "right": "dayGridMonth,timeGridWeek,listWeek"
                },
                "initialView": "dayGridMonth",
                
                # [QUAN TRỌNG NHẤT] Thêm dòng này để biến "Dấu chấm" thành "Khối màu"
                "eventDisplay": "block",
                
                "height": "auto", 
                "slotMinTime": "00:00:00",
                "slotMaxTime": "23:00:00",
                "allDaySlot": False,
                "slotEventOverlap": False,
                
                "buttonText": {
                    "today": "Hôm nay", "month": "Tháng", "week": "Tuần", "list": "Danh sách"
                },
                "slotLabelFormat": {
                    "hour": "2-digit", "minute": "2-digit", "hour12": False, "meridiem": False
                },
                "eventTimeFormat": {
                    "hour": "2-digit", "minute": "2-digit", "hour12": False
                }
            }
            
            # CSS DARK MODE (Đã chỉnh lại để không bị mất màu)
            custom_css = """
                .fc {
                    background-color: #0E1117; 
                    font-family: sans-serif;
                }
                .fc-col-header-cell-cushion {
                    color: #E0E0E0 !important;
                    font-size: 1.1em;
                    font-weight: 600;
                    padding: 10px 0 !important;
                }
                .fc-daygrid-day-number {
                    color: #E0E0E0 !important;
                    font-weight: 500;
                    padding: 8px !important;
                }
                /* Kẻ bảng màu xám nhẹ để thấy rõ ô */
                .fc-theme-standard td, .fc-theme-standard th {
                    border-color: #303030 !important;
                }
                .fc-event {
                    border-radius: 4px !important;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.4);
                    border: none !important;
                    margin: 2px !important;
                    cursor: pointer;
                }
                .fc-toolbar-title {
                    color: white !important;
                    text-transform: capitalize !important;
                }
                .fc-button {
                    background-color: #262730 !important;
                    border: 1px solid #4a4a4a !important;
                    color: white !important;
                    text-transform: capitalize !important;
                }
                .fc-button-active {
                    background-color: #FF4B4B !important;
                    border-color: #FF4B4B !important;
                }
            """

            # Bỏ st.container bao ngoài -> Để Calendar tự do bung lụa
            calendar(
                events=calendar_events, 
                options=calendar_options, 
                custom_css=custom_css,
                key="final_calendar_v3" # Key mới để reset lại từ đầu
            )

        else:
            # --- CHẾ ĐỘ DANH SÁCH ---
            st.markdown("### 📝 Chi tiết lịch trình")
            for _, row in df_events.iterrows():
                event_dt = pd.to_datetime(row['start_time'])
                clean_content = row['event_content'].replace("'", "").replace('"', "").strip()
                clean_content = clean_content[0].upper() + clean_content[1:] if clean_content else ""
                
                st.markdown(f"""
                <div style="background-color: #262730; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #FF4B4B;">
                    <div style="display: flex; justify-content: space-between;">
                        <strong style="color: white; font-size: 1.1em;">{clean_content}</strong>
                        <span style="color: #FFBD45; font-weight: bold;">{event_dt.strftime('%H:%M')}</span>
                    </div>
                    <div style="color: #A0A0A0; font-size: 0.9em; margin-top: 4px;">
                        📅 {event_dt.strftime('%d/%m/%Y')} &nbsp; | &nbsp; 📍 {row['location']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

# --- TAB 3: QUẢN LÝ & DANH SÁCH ---
with tab3:
    st.subheader("Danh sách chi tiết & Chỉnh sửa")
    
    search_term = st.text_input("🔍 Tìm kiếm sự kiện:", placeholder="Nhập từ khóa...")
    df = db.get_all_events()
    if search_term:
        df = df[df['event_content'].str.contains(search_term, case=False) | df['location'].str.contains(search_term, case=False)]

    st.dataframe(
        df,
        column_config={
            "id": "ID",
            "event_content": "Sự kiện",
            "start_time": "Thời gian",
            "location": "Địa điểm",
            "reminder_minutes": "Nhắc trước (phút)"
        },
        hide_index=True,
        height=300
    )

    st.divider()
    st.warning("⚠️ Khu vực chỉnh sửa (Nhập ID)")
    
    col_select, col_action = st.columns([1, 2])
    with col_select:
        event_id_input = st.number_input("ID sự kiện:", min_value=0, step=1)
        
    if event_id_input > 0:
        event_data = db.get_event_by_id(event_id_input)
        if event_data is not None:
            with st.form("edit_form"):
                st.write(f"Đang sửa: **{event_data['event_content']}**")
                
                new_content = st.text_input("Tên sự kiện", value=event_data['event_content'])
                new_location = st.text_input("Địa điểm", value=event_data['location'])
                
                try:
                    current_time = pd.to_datetime(event_data['start_time'])
                    new_date = st.date_input("Ngày", value=current_time.date())
                    new_time = st.time_input("Giờ", value=current_time.time())
                except:
                    pass
                
                new_reminder = st.number_input("Nhắc trước (phút)", value=event_data['reminder_minutes'])
                
                c1, c2 = st.columns(2)
                with c1:
                    btn_update = st.form_submit_button("💾 Lưu", type="primary")
                with c2:
                    btn_delete = st.form_submit_button("🗑️ Xóa", type="secondary")
                
                if btn_update:
                    final_dt = datetime.combine(new_date, new_time)
                    db.update_event(event_id_input, new_content, new_location, final_dt.isoformat(), new_reminder)
                    st.toast("Đã cập nhật!")
                    time.sleep(1)
                    st.rerun()
                    
                if btn_delete:
                    db.delete_event(event_id_input)
                    st.toast("Đã xóa!")
                    time.sleep(1)
                    st.rerun()
        else:
            st.error("Không tìm thấy ID này!")
