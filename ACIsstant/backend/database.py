import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

class ChatDB:
    def __init__(self, db_path: str = "data/chats.db"):
        self.db_path = Path(__file__).parent.parent / db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(str(self.db_path))

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Chats Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Messages Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats (id)
                )
            ''')
            conn.commit()

    def create_chat(self, chat_id: str, title: str) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chats (id, title) VALUES (?, ?)",
                (chat_id, title)
            )
            conn.commit()

    def get_chats(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chats ORDER BY updated_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def add_message(self, chat_id: str, role: str, content: str) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
                (chat_id, role, content)
            )
            # Update chat's updated_at
            cursor.execute(
                "UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (chat_id,)
            )
            conn.commit()

    def get_messages(self, chat_id: str) -> List[Dict[str, str]]:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY timestamp ASC",
                (chat_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def update_chat_title(self, chat_id: str, new_title: str) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE chats SET title = ? WHERE id = ?",
                (new_title, chat_id)
            )
            conn.commit()

    def delete_chat(self, chat_id: str) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
            conn.commit()
