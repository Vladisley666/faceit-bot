import discord
from discord.ext import commands
from database.server_config import get_server_config
from config import MAIN_ADMIN_IDS
from utils.helpers import get_user_status, save_user_status

@commands.Cog.listener()
async def on_message(message):
    if message.author.bot:
        return
    if isinstance(message.channel, discord.DMChannel):
        # Рассылка рекламы (для админов)
        if hasattr(message.author, 'waiting_for_ad') and message.author.waiting_for_ad and message.author.id in MAIN_ADMIN_IDS:
            await message.channel.send("📨 Рассылка...")
            for guild in message.author.bot.guilds:
                config = get_server_config(guild.id)
                if config and config[0] and (len(config) > 3 and config[3]):
                    channel = guild.get_channel(config[0])
                    if channel:
                        try:
                            await channel.send(content=message.content)
                        except:
                            pass
            await message.channel.send("✅ Рассылка завершена")
            return

        status, saved_nick = get_user_status(message.author.id)
        if status == "waiting_for_nick":
            nickname = message.content.strip()
            await message.channel.send(f"🔍 Проверяю {nickname}...")
            for guild in message.author.bot.guilds:
                member = guild.get_member(message.author.id)
                if member:
                    from cogs.verification import update_user_role
                    success, result = await update_user_role(member, nickname)
                    if success:
                        await message.channel.send(f"✅ Верификация успешна!")
                        save_user_status(message.author.id, "verified", nickname)
                    else:
                        await message.channel.send(result)
                    break
            else:
                await message.channel.send("❌ Ты не на сервере!")
        else:
            await message.channel.send("👋 Привет! Используй `/verify ник steam_id` в ЛС")

async def setup(bot):
    bot.add_listener(on_message, name='on_message')