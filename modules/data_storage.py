import sqlite3
import datetime
from flask import g, current_app

class ConversationLogger:
    def __init__(self, db_connection="conversations.db"):
        self.db_connection = db_connection

    def get_db(self):
        """Get a database connection within the app context."""
        if not hasattr(g, '_database'):
            g._database = sqlite3.connect(self.db_connection)
        return g._database

    def close_db(self):
        """Close the database connection."""
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()
            delattr(g, '_database')

    def create_tables(self):
        """Create necessary tables if they don't exist."""
        with current_app.app_context():  # Ensure app context
            db = self.get_db()
            cursor = db.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calls (
                    call_id TEXT PRIMARY KEY,
                    caller TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration INTEGER
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    call_id TEXT,
                    sender TEXT,
                    content TEXT,
                    timestamp TIMESTAMP,
                    FOREIGN KEY (call_id) REFERENCES calls (call_id)
                )
            ''')
            db.commit()

    def log_call_start(self, call_id, caller):
        with current_app.app_context():
            db = self.get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO calls (call_id, caller, start_time) VALUES (?, ?, ?)",
                (call_id, caller, datetime.datetime.now())
            )
            db.commit()

    def log_call_end(self, call_id):
        with current_app.app_context():
            db = self.get_db()
            cursor = db.cursor()
            end_time = datetime.datetime.now()
            cursor.execute("SELECT start_time FROM calls WHERE call_id = ?", (call_id,))
            result = cursor.fetchone()
            if result:
                start_time = datetime.datetime.fromisoformat(result[0])
                duration = (end_time - start_time).total_seconds()
                cursor.execute(
                    "UPDATE calls SET end_time = ?, duration = ? WHERE call_id = ?",
                    (end_time, duration, call_id)
                )
                db.commit()

    def log_message(self, call_id, sender, content):
        with current_app.app_context():
            db = self.get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO messages (call_id, sender, content, timestamp) VALUES (?, ?, ?, ?)",
                (call_id, sender, content, datetime.datetime.now())
            )
            db.commit()