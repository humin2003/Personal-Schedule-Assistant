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

# --- CONFIG ---
st.set_page_config(page_title="Trợ lý Lịch trình AI", page_icon="📅", layout="wide")

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
                     notification.notify(title=f"🔔 Lời nhắc: {event_content}", message=f"Lúc {start_dt.strftime('%H:%M')} tại {loc}", app_name="Lời nhắc", timeout=10)
            conn.close()
        except Exception: pass
        time.sleep(60)

if 'scheduler_started' not in st.session_state:
    threading.Thread(target=run_scheduler, daemon=True).start()
    st.session_state['scheduler_started'] = True

# --- HEADER ---
st.title("📅 Trợ lý Quản lý Lịch trình Thông minh")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["➕ Thêm sự kiện", "🗓️ Xem Lịch Biểu", "⚙️ Quản lý & Xuất file"])

# --- TAB 1: THÊM SỰ KIỆN ---
with tab1:
    st.subheader("💬 Nhập liệu ngôn ngữ tự nhiên")
    st.caption("Ví dụ: 'Họp team lúc 9h đến 11h sáng mai ở phòng 302', 'Mai đi chơi cả ngày'")
    
    def handle_add_event():
        raw_text = st.session_state.input_main
        if raw_text.strip():
            try:
                data = nlp.process(raw_text)
                db.add_event(data)
                st.toast(f"✅ Đã thêm: {data['event']}", icon="🎉")
                st.session_state.input_main = ""
            except ValueError as e:
                st.toast(f"❌ Lỗi: {str(e)}", icon="⚠️")

    c1, c2 = st.columns([5, 1])
    with c1: st.text_input("Nhập câu lệnh tại đây:", key="input_main", placeholder="Gõ lệnh và nhấn Enter hoặc nút Thêm...")
    with c2: 
        st.write("")
        st.write("")
        st.button("✨ Thêm ngay", type="primary", on_click=handle_add_event, width='stretch')

    st.write("")
    st.markdown("##### 🕒 Sự kiện sắp tới")
    df_preview = db.get_all_events().head(5)
    if not df_preview.empty:
        st.dataframe(df_preview[['event_content', 'start_time', 'location']], hide_index=True, width='stretch')

# --- TAB 2: LỊCH BIỂU ---
with tab2:
    df_events = db.get_all_events()
    
    c_view, _ = st.columns([2, 5])
    with c_view:
        view_mode = st.radio("Chế độ xem:", ["Lịch đồ họa", "Danh sách"], horizontal=True, label_visibility="collapsed", index=0)

    if view_mode == "Lịch đồ họa":
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
        st.markdown("### 📝 Danh sách sự kiện")
        if df_events.empty:
            st.info("Chưa có sự kiện nào.")
        else:
            for _, row in df_events.iterrows():
                event_dt = pd.to_datetime(row['start_time'])
                is_all_day_db = bool(row.get('is_all_day', 0))
                time_display = "🟦 Cả ngày" if is_all_day_db else f"🕒 {event_dt.strftime('%H:%M')}"
                
                st.markdown(f"""
                <div style="background-color: #262730; padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #333; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 1.1em; font-weight: bold; color: #FFF; margin-bottom: 4px;">{row['event_content']}</div>
                        <div style="color: #AAA; font-size: 0.9em;">📍 {row['location']}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: #FF4B4B; font-weight: bold;">{event_dt.strftime('%d/%m/%Y')}</div>
                        <div style="color: #FFBD45; font-size: 0.9em;">{time_display}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# --- TAB 3: QUẢN LÝ ---
with tab3:
    st.subheader("🛠️ Công cụ quản lý")
    c_export, c_search = st.columns([1, 2])
    with c_export:
        all_events = db.get_all_events()
        if not all_events.empty:
            st.download_button("📥 Tải về Backup (.json)", data=all_events.to_json(orient='records', force_ascii=False, indent=2), file_name="schedule_backup.json", mime="application/json", width='stretch')
        else:
            st.button("📥 Tải về", disabled=True, width='stretch')
            
    with c_search: search_term = st.text_input("🔍 Tìm kiếm sự kiện:", label_visibility="collapsed", placeholder="Nhập từ khóa để lọc...")
    
    if search_term and not all_events.empty:
        all_events = all_events[all_events['event_content'].str.contains(search_term, case=False) | all_events['location'].str.contains(search_term, case=False)]

    if not all_events.empty:
        st.dataframe(all_events, hide_index=True, width='stretch', height=250)
    
    st.markdown("---")
    st.write("#### ✏️ Chỉnh sửa nhanh")
    event_id_input = st.number_input("Nhập ID sự kiện cần sửa:", min_value=0, step=1)
    
    if event_id_input > 0:
        evt = db.get_event_by_id(event_id_input)
        if evt is not None:
            with st.expander("Mở form chỉnh sửa", expanded=True):
                with st.form("edit_form"):
                    st.info(f"Đang sửa ID: {event_id_input}")
                    st.text_area("Câu lệnh gốc:", value=evt['original_text'], height=60, disabled=True)
                    
                    c_name, c_loc = st.columns(2)
                    new_content = c_name.text_input("Tên sự kiện", value=evt['event_content'])
                    new_loc = c_loc.text_input("Địa điểm", value=evt['location'])
                    
                    # Logic All Day
                    current_is_all_day = bool(evt.get('is_all_day', 0))
                    new_is_all_day = st.checkbox("Sự kiện diễn ra cả ngày?", value=current_is_all_day)

                    try:
                        # Lấy start_time và end_time hiện tại từ DB
                        cur_start = pd.to_datetime(evt['start_time'])
                        if evt['end_time']:
                            cur_end = pd.to_datetime(evt['end_time'])
                        else:
                            cur_end = cur_start + timedelta(hours=1)

                        # [FIX] Tách 2 ô nhập giờ: Bắt đầu & Kết thúc
                        c_date, c_start, c_end, c_rem = st.columns(4)
                        new_date = c_date.date_input("Ngày", value=cur_start.date())
                        new_start_time = c_start.time_input("Giờ bắt đầu", value=cur_start.time(), disabled=new_is_all_day)
                        new_end_time = c_end.time_input("Giờ kết thúc", value=cur_end.time(), disabled=new_is_all_day)
                        new_rem = c_rem.number_input("Nhắc trước (phút)", value=evt['reminder_minutes'])
                    except: pass
                    
                    if st.form_submit_button("💾 Lưu thay đổi", type="primary", width='stretch'):
                        # Logic lưu
                        if new_is_all_day:
                            final_start_dt = datetime.combine(new_date, datetime.min.time()) # 00:00
                            final_end_dt = final_start_dt + timedelta(days=1)
                        else:
                            final_start_dt = datetime.combine(new_date, new_start_time)
                            final_end_dt = datetime.combine(new_date, new_end_time)
                            
                            # Tự động sửa nếu Giờ kết thúc <= Giờ bắt đầu
                            if final_end_dt <= final_start_dt:
                                final_end_dt = final_start_dt + timedelta(hours=1)

                        db.update_event(event_id_input, new_content, new_loc, final_start_dt.isoformat(), final_end_dt.isoformat(), new_rem, new_is_all_day)
                        st.toast("Đã lưu thành công!")
                        time.sleep(1)
                        st.rerun()
                        
                    if st.form_submit_button("🗑️ Xóa sự kiện vĩnh viễn", type="secondary", width='stretch'):
                        db.delete_event(event_id_input)
                        st.toast("Đã xóa!")
                        time.sleep(1)
                        st.rerun()