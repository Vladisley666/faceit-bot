import sqlite3
from datetime import datetime
from config import DB_VERSION

conn = sqlite3.connect('faceit_users.db')
c = conn.cursor()

def get_db_version():
    c.execute('SELECT value FROM db_info WHERE key = "version"')
    row = c.fetchone()
    return int(row[0]) if row else 0

def set_db_version(version):
    c.execute('INSERT OR REPLACE INTO db_info (key, value) VALUES (?, ?)', ('version', str(version)))
    conn.commit()

def init_database():
    c.execute('CREATE TABLE IF NOT EXISTS db_info (key TEXT PRIMARY KEY, value TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS faceit_users (
        discord_id INTEGER PRIMARY KEY,
        faceit_nickname TEXT,
        steam_id TEXT,
        last_level INTEGER,
        last_avg REAL,
        last_kd REAL,
        last_map TEXT,
        win_percentage REAL,
        status TEXT DEFAULT 'new',
        last_check TIMESTAMP,
        last_seen TIMESTAMP,
        coins INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS verification_codes (
        discord_id INTEGER PRIMARY KEY,
        code TEXT,
        faceit_nickname TEXT,
        steam_id TEXT,
        created_at TIMESTAMP,
        expires_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS update_log (
        discord_id INTEGER PRIMARY KEY,
        last_update TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS banned_users (
        discord_id INTEGER PRIMARY KEY,
        faceit_nickname TEXT,
        banned_by INTEGER,
        ban_reason TEXT,
        ban_time TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS server_config (
        guild_id INTEGER PRIMARY KEY,
        team_channel_id INTEGER,
        verified_role_id INTEGER,
        unverified_role_id INTEGER,
        advertising_enabled INTEGER DEFAULT 1,
        created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS message_stats (
        user_id INTEGER PRIMARY KEY,
        channel_id INTEGER,
        message_count INTEGER DEFAULT 0,
        last_message TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS voice_stats (
        user_id INTEGER PRIMARY KEY,
        total_seconds INTEGER DEFAULT 0,
        last_join TIMESTAMP,
        current_channel_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creator_id INTEGER,
        guild_id INTEGER,
        channel_id INTEGER,
        event_time TIMESTAMP,
        maps TEXT,
        description TEXT,
        role TEXT,
        participants TEXT,
        confirmed TEXT,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS reliability_rating (
        user_id INTEGER PRIMARY KEY,
        rating INTEGER DEFAULT 1000,
        total_events INTEGER DEFAULT 0,
        attended INTEGER DEFAULT 0,
        late INTEGER DEFAULT 0,
        missed INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS achievements (
        user_id INTEGER PRIMARY KEY,
        pioneer INTEGER DEFAULT 0,
        hard_worker INTEGER DEFAULT 0,
        team_player INTEGER DEFAULT 0,
        connector INTEGER DEFAULT 0,
        leader INTEGER DEFAULT 0,
        social INTEGER DEFAULT 0,
        veteran INTEGER DEFAULT 0,
        collector INTEGER DEFAULT 0,
        last_weekly_reset TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS admin_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        action TEXT,
        target_id INTEGER,
        details TEXT,
        timestamp TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_coins (
        user_id INTEGER PRIMARY KEY,
        coins INTEGER DEFAULT 0,
        last_daily TIMESTAMP,
        last_weekly TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_style (
        user_id INTEGER PRIMARY KEY,
        style_name TEXT,
        style_data TEXT,
        equipped_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS owned_styles (
        user_id INTEGER,
        style_name TEXT,
        purchased_at TIMESTAMP,
        PRIMARY KEY (user_id, style_name)
    )''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_faceit_nickname ON faceit_users(faceit_nickname)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_status ON faceit_users(status)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_last_check ON faceit_users(last_check)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_events_time ON events(event_time)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_events_status ON events(status)')
    conn.commit()

def migrate_database():
    current = get_db_version()
    if current < DB_VERSION:
        print(f"🔄 Обновление БД {current} -> {DB_VERSION}")
        if current < 1:
            try: c.execute('ALTER TABLE verification_codes ADD COLUMN steam_id TEXT'); conn.commit()
            except: pass
        if current < 2:
            c.execute('CREATE INDEX IF NOT EXISTS idx_faceit_nickname ON faceit_users(faceit_nickname)')
            conn.commit()
        if current < 4:
            try: c.execute('ALTER TABLE faceit_users ADD COLUMN coins INTEGER DEFAULT 0'); conn.commit()
            except: pass
        if current < 5:
            try: c.execute('ALTER TABLE server_config ADD COLUMN advertising_enabled INTEGER DEFAULT 1'); conn.commit()
            except: pass
        set_db_version(DB_VERSION)

def ensure_database_schema():
    def add_column(table, column, col_type):
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            conn.commit()
        except: pass
    add_column('faceit_users', 'last_avg', 'REAL')
    add_column('faceit_users', 'last_kd', 'REAL')
    add_column('faceit_users', 'last_map', 'TEXT')
    add_column('faceit_users', 'win_percentage', 'REAL')
    add_column('faceit_users', 'last_seen', 'TIMESTAMP')
    add_column('faceit_users', 'steam_id', 'TEXT')
    add_column('verification_codes', 'steam_id', 'TEXT')
    add_column('server_config', 'advertising_enabled', 'INTEGER DEFAULT 1')
    print("✅ Схема БД проверена")