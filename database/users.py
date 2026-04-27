from database.db_manager import c, conn
from datetime import datetime

def save_user_faceit(discord_id, nickname, level, avg_kills, kd, favorite_map, win_percentage, steam_id=None, coins=None):
    if coins is None:
        c.execute('SELECT coins FROM faceit_users WHERE discord_id = ?', (discord_id,))
        row = c.fetchone()
        coins = row[0] if row else 0
    c.execute('''INSERT OR REPLACE INTO faceit_users 
                 (discord_id, faceit_nickname, steam_id, last_level, last_avg, last_kd, last_map, win_percentage, status, last_check, last_seen, coins)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'verified', ?, ?, ?)''',
              (discord_id, nickname, steam_id, level, avg_kills, kd, favorite_map, win_percentage,
               datetime.now().isoformat(), datetime.now().isoformat(), coins))
    conn.commit()

def get_user_faceit(discord_id):
    c.execute('SELECT faceit_nickname, last_level, last_check FROM faceit_users WHERE discord_id = ?', (discord_id,))
    return c.fetchone()

def get_user_status(discord_id):
    c.execute('SELECT status, faceit_nickname FROM faceit_users WHERE discord_id = ?', (discord_id,))
    return c.fetchone()

def save_user_status(discord_id, status, nickname=None):
    if nickname:
        c.execute('INSERT OR REPLACE INTO faceit_users (discord_id, faceit_nickname, status, last_check) VALUES (?, ?, ?, ?)',
                  (discord_id, nickname, status, datetime.now().isoformat()))
    else:
        c.execute('INSERT OR REPLACE INTO faceit_users (discord_id, status, last_check) VALUES (?, ?, ?)',
                  (discord_id, status, datetime.now().isoformat()))
    conn.commit()

def ban_user(discord_id, faceit_nickname, banned_by, reason):
    c.execute('INSERT OR REPLACE INTO banned_users (discord_id, faceit_nickname, banned_by, ban_reason, ban_time) VALUES (?, ?, ?, ?, ?)',
              (discord_id, faceit_nickname, banned_by, reason, datetime.now().isoformat()))
    conn.commit()

def unban_user(discord_id):
    c.execute('DELETE FROM banned_users WHERE discord_id = ?', (discord_id,))
    conn.commit()

def is_banned(discord_id):
    c.execute('SELECT 1 FROM banned_users WHERE discord_id = ?', (discord_id,))
    return c.fetchone() is not None

def get_ban_info(discord_id):
    c.execute('SELECT faceit_nickname, ban_reason, ban_time FROM banned_users WHERE discord_id = ?', (discord_id,))
    return c.fetchone()

def get_all_bans():
    c.execute('SELECT discord_id, faceit_nickname, ban_reason, ban_time FROM banned_users ORDER BY ban_time DESC')
    return c.fetchall()