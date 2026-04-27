import discord
from discord.ext import commands
from database.db_manager import c, conn
from database.server_config import get_server_config
from database.achievements import update_achievement
from datetime import datetime

@commands.Cog.listener()
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    config = get_server_config(member.guild.id)
    if not config:
        return
    if after.channel and not before.channel:
        c.execute('INSERT INTO voice_stats (user_id, last_join, current_channel_id) VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET last_join=?, current_channel_id=?',
                  (member.id, datetime.now().isoformat(), after.channel.id, datetime.now().isoformat(), after.channel.id))
        conn.commit()
    elif before.channel and not after.channel:
        c.execute('SELECT last_join FROM voice_stats WHERE user_id = ?', (member.id,))
        row = c.fetchone()
        if row and row[0]:
            last_join = datetime.fromisoformat(row[0])
            seconds = int((datetime.now() - last_join).total_seconds())
            c.execute('UPDATE voice_stats SET total_seconds = total_seconds + ?, last_join = NULL, current_channel_id = NULL WHERE user_id = ?',
                      (seconds, member.id))
            conn.commit()
            c.execute('SELECT total_seconds FROM voice_stats WHERE user_id = ?', (member.id,))
            new_row = c.fetchone()
            if new_row and new_row[0] >= 1080000:  # 300 часов
                if update_achievement(member.id, 'veteran'):
                    role = discord.utils.get(member.guild.roles, name="🏆 Ветеран")
                    if role:
                        try:
                            await member.add_roles(role)
                        except:
                            pass

async def setup(bot):
    bot.add_listener(on_voice_state_update, name='on_voice_state_update')