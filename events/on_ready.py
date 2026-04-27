import discord
from discord.ext import commands
import asyncio
from database.db_manager import get_db_version

_bot = None

async def auto_refresh_loop():
    await _bot.wait_until_ready()
    await asyncio.sleep(3600)  # 1 час
    while not _bot.is_closed():
        try:
            print("\n🔄 ЕЖЕДНЕВНОЕ АВТООБНОВЛЕНИЕ")
            # Здесь можно добавить логику обновления, если нужно
            print("✅ Обновление завершено")
        except Exception as e:
            print(f"❌ Ошибка автообновления: {e}")
        await asyncio.sleep(24 * 3600)  # 24 часа

@commands.Cog.listener()
async def on_ready():
    global _bot
    print(f'\n✅ Бот {_bot.user} запущен!')
    print(f'📊 Серверов: {len(_bot.guilds)}')
    print(f'📁 База данных: версия {get_db_version()}')
    if not hasattr(_bot, 'refresh_task'):
        _bot.refresh_task = asyncio.create_task(auto_refresh_loop())

async def setup(bot):
    global _bot
    _bot = bot
    bot.add_listener(on_ready, name='on_ready')