
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("acisstant.db")

class ChatDB:
    def __init__(self, db_path: str = "data/chats.db"):
        self.db_path = Path(__file__).parent.parent / db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self):
        try:
            return sqlite3.connect(str(self.db_path))
        except Exception as e:
            logger.error(f"[DB] Failed to connect to database: {e}")
            raise

    def init_db(self):
        try:
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
            logger.info("[DB] Database initialized.")
        except Exception as e:
            logger.error(f"[DB] Failed to initialize database: {e}")
            raise

    def create_chat(self, chat_id: str, title: str) -> None:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO chats (id, title) VALUES (?, ?)",
                    (chat_id, title)
                )
                conn.commit()
            logger.info(f"[DB] Chat created: {chat_id} ('{title}')")
        except Exception as e:
            logger.error(f"[DB] Failed to create chat: {e}")
            raise

    def get_chats(self) -> List[Dict[str, Any]]:
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM chats ORDER BY updated_at DESC")
                result = [dict(row) for row in cursor.fetchall()]
            logger.info(f"[DB] Retrieved {len(result)} chats.")
            return result
        except Exception as e:
            logger.error(f"[DB] Failed to get chats: {e}")
            raise

    def add_message(self, chat_id: str, role: str, content: str) -> None:
        try:
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
            logger.info(f"[DB] Message added to chat {chat_id} (role: {role})")
        except Exception as e:
            logger.error(f"[DB] Failed to add message: {e}")
            raise

    def get_messages(self, chat_id: str) -> List[Dict[str, str]]:
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY timestamp ASC",
                    (chat_id,)
                )
                result = [dict(row) for row in cursor.fetchall()]
            logger.info(f"[DB] Retrieved {len(result)} messages for chat {chat_id}.")
            return result
        except Exception as e:
            logger.error(f"[DB] Failed to get messages for chat {chat_id}: {e}")
            raise

    def update_chat_title(self, chat_id: str, new_title: str) -> None:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE chats SET title = ? WHERE id = ?",
                    (new_title, chat_id)
                )
                conn.commit()
            logger.info(f"[DB] Chat {chat_id} renamed to '{new_title}'")
        except Exception as e:
            logger.error(f"[DB] Failed to update chat title: {e}")
            raise

    def delete_chat(self, chat_id: str) -> None:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
                cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
                conn.commit()
            logger.info(f"[DB] Chat {chat_id} deleted.")
        except Exception as e:
            logger.error(f"[DB] Failed to delete chat {chat_id}: {e}")
            raise

    def compress_messages(self, chat_id: str, count: int, summary: str) -> None:
        """Delete the oldest `count` messages and insert a compressed summary."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM messages WHERE chat_id = ? ORDER BY timestamp ASC LIMIT ?",
                    (chat_id, count)
                )
                ids_to_delete = [row[0] for row in cursor.fetchall()]
                if ids_to_delete:
                    placeholders = ",".join("?" * len(ids_to_delete))
                    cursor.execute(
                        f"DELETE FROM messages WHERE id IN ({placeholders})",
                        ids_to_delete
                    )
                    cursor.execute(
                        "INSERT INTO messages (chat_id, role, content, timestamp) VALUES (?, 'system', ?, datetime('now', '-1 hour'))",
                        (chat_id, summary)
                    )
                conn.commit()
            logger.info(f"[DB] Compressed {len(ids_to_delete)} messages for chat {chat_id}.")
        except Exception as e:
            logger.error(f"[DB] Failed to compress messages for chat {chat_id}: {e}")
            raise

    def purge_oldest_messages(self, chat_id: str, count: int) -> None:
        """Delete the oldest `count` messages from a chat."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM messages WHERE chat_id = ? ORDER BY timestamp ASC LIMIT ?",
                    (chat_id, count)
                )
                ids_to_delete = [row[0] for row in cursor.fetchall()]
                if ids_to_delete:
                    placeholders = ",".join("?" * len(ids_to_delete))
                    cursor.execute(
                        f"DELETE FROM messages WHERE id IN ({placeholders})",
                        ids_to_delete
                    )
                conn.commit()
            logger.info(f"[DB] Purged {len(ids_to_delete)} messages for chat {chat_id}.")
        except Exception as e:
            logger.error(f"[DB] Failed to purge messages for chat {chat_id}: {e}")
            raise
