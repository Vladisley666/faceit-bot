import discord
from discord.ext import commands
import asyncio
import sys
import os
from config import DISCORD_TOKEN
from database.db_manager import init_database, migrate_database, ensure_database_schema

print(f"🐍 Python {sys.version}")
if not DISCORD_TOKEN:
    print("❌ DISCORD_TOKEN не найден")
    sys.exit(1)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
intents.presences = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

init_database()
migrate_database()
ensure_database_schema()

async def load_extensions():
    await bot.load_extension("cogs.verification")
    await bot.load_extension("cogs.stats_commands")
    await bot.load_extension("cogs.lft")
    await bot.load_extension("cogs.shop")
    await bot.load_extension("cogs.achievements_cmd")
    await bot.load_extension("cogs.admin_tools")
    await bot.load_extension("cogs.advertising")
    await bot.load_extension("events.on_ready")
    await bot.load_extension("events.on_member_join")
    await bot.load_extension("events.on_guild_join_remove")
    await bot.load_extension("events.on_message")
    await bot.load_extension("events.on_voice_state")
    print("✅ Все модули загружены")

@bot.event
async def setup_hook():
    await load_extensions()
    await bot.tree.sync()
    print("✅ Слеш-команды синхронизированы")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)