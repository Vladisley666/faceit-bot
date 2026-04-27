from database.db_manager import c, conn
from datetime import datetime

def update_message_stats(user_id, channel_id):
    c.execute('''INSERT INTO message_stats (user_id, channel_id, message_count, last_message)
                 VALUES (?, ?, 1, ?)
                 ON CONFLICT(user_id) DO UPDATE SET
                 message_count = message_count + 1,
                 last_message = ?''',
              (user_id, channel_id, datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()

def get_message_stats(user_id):
    c.execute('SELECT message_count FROM message_stats WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    return row[0] if row else 0

def update_voice_stats(user_id, seconds):
    c.execute('UPDATE voice_stats SET total_seconds = total_seconds + ? WHERE user_id = ?', (seconds, user_id))
    conn.commit()