from database.db_manager import c, conn
from datetime import datetime

def add_coins(user_id, amount):
    c.execute('INSERT INTO user_coins (user_id, coins) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET coins = coins + ?',
              (user_id, amount, amount))
    conn.commit()
    c.execute('UPDATE faceit_users SET coins = coins + ? WHERE discord_id = ?', (amount, user_id))
    conn.commit()

def get_coins(user_id):
    c.execute('SELECT coins FROM user_coins WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    if row:
        return row[0]
    c.execute('SELECT coins FROM faceit_users WHERE discord_id = ?', (user_id,))
    row = c.fetchone()
    if row and row[0]:
        add_coins(user_id, row[0])
        return row[0]
    return 0

def spend_coins(user_id, amount):
    coins = get_coins(user_id)
    if coins >= amount:
        c.execute('UPDATE user_coins SET coins = coins - ? WHERE user_id = ?', (amount, user_id))
        conn.commit()
        c.execute('UPDATE faceit_users SET coins = coins - ? WHERE discord_id = ?', (amount, user_id))
        conn.commit()
        return True
    return False

def add_owned_style(user_id, style_name):
    c.execute('INSERT OR IGNORE INTO owned_styles (user_id, style_name, purchased_at) VALUES (?, ?, ?)',
              (user_id, style_name, datetime.now().isoformat()))
    conn.commit()

def get_owned_styles(user_id):
    c.execute('SELECT style_name FROM owned_styles WHERE user_id = ?', (user_id,))
    return [row[0] for row in c.fetchall()]

def get_equipped_style(user_id):
    c.execute('SELECT style_name FROM user_style WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    return row[0] if row else None