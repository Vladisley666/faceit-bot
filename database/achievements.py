from database.db_manager import c, conn

def update_achievement(user_id, achievement_name):
    c.execute(f'SELECT {achievement_name} FROM achievements WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    if not row:
        c.execute('INSERT INTO achievements (user_id) VALUES (?)', (user_id,))
        conn.commit()
        c.execute(f'SELECT {achievement_name} FROM achievements WHERE user_id = ?', (user_id,))
        row = c.fetchone()
    if row and row[0] == 0:
        c.execute(f'UPDATE achievements SET {achievement_name} = 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        return True
    return False

def get_user_achievements(user_id):
    c.execute('SELECT pioneer, hard_worker, team_player, connector, leader, social, veteran, collector FROM achievements WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    if not row:
        return []
    achievements_map = {
        'pioneer': ('🧭 Первопроходец', 'Верификация в первые 3 дня'),
        'hard_worker': ('⚙️ Трудоголик', '20 матчей за неделю'),
        'team_player': ('🤝 Командный игрок', '10 матчей с разными игроками'),
        'connector': ('📡 Мастер связей', '20 успешных поисков тиммейтов'),
        'leader': ('🎯 Организатор', '50 созданных событий'),
        'social': ('💬 Душа компании', '500 сообщений в канале'),
        'veteran': ('🏆 Ветеран', '300 часов в голосовых каналах'),
        'collector': ('⭐ Коллекционер', 'Получить все достижения')
    }
    achievements = []
    for i, (key, (name, desc)) in enumerate(achievements_map.items()):
        if i < len(row) and row[i]:
            achievements.append((name, desc))
    return achievements