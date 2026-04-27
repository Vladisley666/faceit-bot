from database.db_manager import c, conn
import json
from datetime import datetime

def create_event(creator_id, guild_id, channel_id, event_time, maps, description, role):
    c.execute('''INSERT INTO events (creator_id, guild_id, channel_id, event_time, maps, description, role, participants, confirmed, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (creator_id, guild_id, channel_id, event_time.isoformat(), maps, description, role,
               json.dumps([]), json.dumps([]), datetime.now().isoformat()))
    conn.commit()
    return c.lastrowid

def add_participant(event_id, user_id):
    c.execute('SELECT participants FROM events WHERE id = ?', (event_id,))
    row = c.fetchone()
    if row:
        participants = json.loads(row[0])
        if user_id not in participants:
            participants.append(user_id)
            c.execute('UPDATE events SET participants = ? WHERE id = ?', (json.dumps(participants), event_id))
            conn.commit()
            return True
    return False

def remove_participant(event_id, user_id):
    c.execute('SELECT participants FROM events WHERE id = ?', (event_id,))
    row = c.fetchone()
    if row:
        participants = json.loads(row[0])
        if user_id in participants:
            participants.remove(user_id)
            c.execute('UPDATE events SET participants = ? WHERE id = ?', (json.dumps(participants), event_id))
            conn.commit()
            return True
    return False