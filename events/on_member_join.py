import discord
from discord.ext import commands
from database.users import is_banned, get_user_faceit, save_user_status
from database.server_config import get_server_config

async def sync_user_across_servers(guild, user_id, faceit_nickname):
    from cogs.verification import update_user_role
    member = guild.get_member(user_id)
    if member:
        await update_user_role(member, faceit_nickname)

@commands.Cog.listener()
async def on_member_join(member):
    if is_banned(member.id):
        try:
            await member.send("🚫 Вы забанены на этом сервере.")
        except:
            pass
        return

    config = get_server_config(member.guild.id)
    if config:
        unverified_role = member.guild.get_role(config[2])
        if unverified_role and not member.bot:
            try:
                await member.add_roles(unverified_role)
            except:
                pass

    user_data = get_user_faceit(member.id)
    if user_data and user_data[0]:
        await sync_user_across_servers(member.guild, member.id, user_data[0])
    else:
        try:
            embed = discord.Embed(
                title="👋 Добро пожаловать!",
                description=(
                    "**Я — Faceit Rank Bot** 🤖\n\n"
                    "Чтобы получить доступ к каналу для поиска тиммейтов:\n\n"
                    "1️⃣ Напиши мне **в ЛС**: `/verify твой_ник твой_steam_id`\n"
                    "2️⃣ Вставь полученный код в **Real Name** Steam профиля\n"
                    "3️⃣ Напиши `/confirm код`\n\n"
                    "📝 Пример: `/verify moneself 76561198000000000`"
                ),
                color=discord.Color.green()
            )
            await member.send(embed=embed)
            save_user_status(member.id, "waiting_for_nick")
        except:
            pass

async def setup(bot):
    bot.add_listener(on_member_join, name='on_member_join')