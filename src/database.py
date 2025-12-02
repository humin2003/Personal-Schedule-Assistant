import sqlite3
import pandas as pd
import os

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(base_dir, 'data', 'schedule.db')
        else:
            self.db_path = db_path 
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        # Thêm cột end_time
        query = """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_content TEXT,
            original_text TEXT,
            location TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,  -- <--- THÊM DÒNG NÀY
            reminder_minutes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        with self.get_connection() as conn:
            conn.execute(query)

    def add_event(self, data: dict):
        # Insert cả end_time
        query = """
        INSERT INTO events (event_content, original_text, location, start_time, end_time, reminder_minutes)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        with self.get_connection() as conn:
            conn.execute(query, (
                data.get('event'), 
                data.get('original_text'),
                data.get('location'),
                data.get('start_time'),
                data.get('end_time'), # <--- THÊM DÒNG NÀY
                data.get('reminder_minutes', 0)
            ))
            conn.commit()
    
    def get_all_events(self):
        # Select thêm end_time
        query = "SELECT id, event_content, start_time, end_time, location, reminder_minutes FROM events ORDER BY start_time ASC"
        conn = self.get_connection()
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def delete_event(self, event_id):
        query = "DELETE FROM events WHERE id = ?"
        with self.get_connection() as conn:
            conn.execute(query, (event_id,))
            conn.commit()

    # --- HÀM MỚI: CẬP NHẬT SỰ KIỆN ---
    def update_event(self, event_id, content, location, time, reminder):
        query = """
        UPDATE events 
        SET event_content = ?, location = ?, start_time = ?, reminder_minutes = ?
        WHERE id = ?
        """
        with self.get_connection() as conn:
            conn.execute(query, (content, location, time, reminder, event_id))
            conn.commit()
    
    # --- HÀM MỚI: LẤY 1 SỰ KIỆN ĐỂ SỬA ---
    def get_event_by_id(self, event_id):
        query = "SELECT * FROM events WHERE id = ?"
        conn = self.get_connection()
        df = pd.read_sql_query(query, conn, params=(event_id,))
        conn.close()
        return df.iloc[0] if not df.empty else None