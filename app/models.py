# File: app/models.py
from app.db import get_db
from datetime import datetime
import json


class Conversation:
    @staticmethod
    def create(title="New Conversation"):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO conversations (title, created_at) VALUES (?, ?)',
            (title, datetime.now())
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def get(conversation_id):
        db = get_db()
        conversation = db.execute(
            'SELECT id, title, created_at FROM conversations WHERE id = ?',
            (conversation_id,)
        ).fetchone()

        return conversation

    @staticmethod
    def get_all():
        db = get_db()
        conversations = db.execute(
            'SELECT id, title, created_at FROM conversations ORDER BY created_at DESC'
        ).fetchall()

        return conversations

    @staticmethod
    def delete(conversation_id):
        db = get_db()
        db.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))
        db.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
        db.commit()


class Message:
    @staticmethod
    def create(conversation_id, role, content):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)',
            (conversation_id, role, content, datetime.now())
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def get_by_conversation(conversation_id):
        db = get_db()
        messages = db.execute(
            'SELECT id, role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at',
            (conversation_id,)
        ).fetchall()

        return messages
