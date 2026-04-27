from database.db_manager import c, conn
from datetime import datetime

def save_server_config(guild_id, team_channel_id, verified_role_id, unverified_role_id, advertising_enabled=1):
    c.execute('''INSERT OR REPLACE INTO server_config 
                 (guild_id, team_channel_id, verified_role_id, unverified_role_id, advertising_enabled, created_at)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (guild_id, team_channel_id, verified_role_id, unverified_role_id, advertising_enabled, datetime.now().isoformat()))
    conn.commit()

def get_server_config(guild_id):
    c.execute('SELECT team_channel_id, verified_role_id, unverified_role_id, advertising_enabled FROM server_config WHERE guild_id = ?', (guild_id,))
    row = c.fetchone()
    if row:
        return row[0], row[1], row[2], row[3] if len(row) > 3 else 1
    return None

def delete_server_config(guild_id):
    c.execute('DELETE FROM server_config WHERE guild_id = ?', (guild_id,))
    conn.commit()