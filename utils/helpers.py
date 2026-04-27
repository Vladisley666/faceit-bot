import secrets
import string
from datetime import datetime, timedelta
from functools import lru_cache
from database.db_manager import c, conn

def generate_verify_code():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

def save_verify_code(discord_id, faceit_nickname, steam_id):
    code = generate_verify_code()
    expires = datetime.now() + timedelta(minutes=10)
    c.execute('INSERT OR REPLACE INTO verification_codes (discord_id, code, faceit_nickname, steam_id, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?)',
              (discord_id, code, faceit_nickname, steam_id, datetime.now().isoformat(), expires.isoformat()))
    conn.commit()
    return code

def get_verify_code(discord_id):
    c.execute('SELECT code, faceit_nickname, steam_id, expires_at FROM verification_codes WHERE discord_id = ?', (discord_id,))
    row = c.fetchone()
    if row:
        return row[0], row[1], row[2], datetime.fromisoformat(row[3])
    return None, None, None, None

def delete_verify_code(discord_id):
    c.execute('DELETE FROM verification_codes WHERE discord_id = ?', (discord_id,))
    conn.commit()

def get_user_faceit(discord_id):
    c.execute('SELECT faceit_nickname, last_level, last_check FROM faceit_users WHERE discord_id = ?', (discord_id,))
    return c.fetchone()

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
    invalidate_players_cache()

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

def can_update(discord_id):
    c.execute('SELECT last_update FROM update_log WHERE discord_id = ?', (discord_id,))
    row = c.fetchone()
    if not row:
        return True
    last = datetime.fromisoformat(row[0])
    return datetime.now() - last > timedelta(minutes=15)

def save_update_time(discord_id):
    c.execute('INSERT OR REPLACE INTO update_log (discord_id, last_update) VALUES (?, ?)',
              (discord_id, datetime.now().isoformat()))
    conn.commit()

def is_data_stale(discord_id, hours=6):
    c.execute('SELECT last_check FROM faceit_users WHERE discord_id = ?', (discord_id,))
    row = c.fetchone()
    if not row:
        return True
    last = datetime.fromisoformat(row[0])
    return datetime.now() - last > timedelta(hours=hours)

@lru_cache(maxsize=128)
def get_all_players_cached():
    c.execute('SELECT discord_id, faceit_nickname, last_level FROM faceit_users WHERE status = "verified" ORDER BY last_level DESC, faceit_nickname ASC')
    return c.fetchall()

def invalidate_players_cache():
    get_all_players_cached.cache_clear()

def get_all_players():
    return get_all_players_cached()

def get_coins(user_id):
    from database.coins_styles import get_coins as _gc
    return _gc(user_id)

def add_coins(user_id, amount):
    from database.coins_styles import add_coins as _ac
    _ac(user_id, amount)

def spend_coins(user_id, amount):
    from database.coins_styles import spend_coins as _sc
    return _sc(user_id, amount)

def add_owned_style(user_id, style_name):
    from database.coins_styles import add_owned_style as _aos
    _aos(user_id, style_name)

def get_owned_styles(user_id):
    from database.coins_styles import get_owned_styles as _gos
    return _gos(user_id)

def get_equipped_style(user_id):
    from database.coins_styles import get_equipped_style as _ges
    return _ges(user_id)

def get_user_achievements(user_id):
    from database.achievements import get_user_achievements as _gua
    return _gua(user_id)

def update_achievement(user_id, achievement_name):
    from database.achievements import update_achievement as _ua
    return _ua(user_id, achievement_name)