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
        query = """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_content TEXT,
            original_text TEXT,
            location TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            reminder_minutes INTEGER DEFAULT 0,
            is_all_day INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        with self.get_connection() as conn:
            conn.execute(query)
            try: conn.execute("ALTER TABLE events ADD COLUMN is_all_day INTEGER DEFAULT 0")
            except: pass

    def add_event(self, data: dict):
        query = """
        INSERT INTO events (event_content, original_text, location, start_time, end_time, reminder_minutes, is_all_day)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        is_all_day_int = 1 if data.get('is_all_day') else 0
        with self.get_connection() as conn:
            conn.execute(query, (
                data.get('event'), data.get('original_text'), data.get('location'),
                data.get('start_time'), data.get('end_time'),
                data.get('reminder_minutes', 0), is_all_day_int
            ))
            conn.commit()
    
    def get_all_events(self):
        query = "SELECT id, event_content, start_time, end_time, location, reminder_minutes, is_all_day, original_text FROM events ORDER BY start_time ASC"
        conn = self.get_connection()
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def delete_event(self, event_id):
        query = "DELETE FROM events WHERE id = ?"
        with self.get_connection() as conn:
            conn.execute(query, (event_id,))
            conn.commit()

    # [CẬP NHẬT] Hàm update nhận thêm end_time
    def update_event(self, event_id, content, location, start_time, end_time, reminder, is_all_day):
        query = """
        UPDATE events 
        SET event_content = ?, location = ?, start_time = ?, end_time = ?, reminder_minutes = ?, is_all_day = ?
        WHERE id = ?
        """
        is_all_day_int = 1 if is_all_day else 0
        with self.get_connection() as conn:
            conn.execute(query, (content, location, start_time, end_time, reminder, is_all_day_int, event_id))
            conn.commit()
    
    def get_event_by_id(self, event_id):
        query = "SELECT * FROM events WHERE id = ?"
        conn = self.get_connection()
        df = pd.read_sql_query(query, conn, params=(event_id,))
        conn.close()
        return df.iloc[0] if not df.empty else None