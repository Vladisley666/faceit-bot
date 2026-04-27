import discord
from discord.ext import commands
from config import get_all_bot_roles, FACEIT_ROLES, AVG_KILLS_ROLES, KD_ROLES, MAP_ROLES
from database.server_config import delete_server_config

async def create_all_roles(guild):
    created = []
    existed = []
    for role_name in ["Verified", "Unverified"]:
        existing = discord.utils.get(guild.roles, name=role_name)
        if existing:
            existed.append(role_name)
        else:
            color = discord.Color.green() if role_name == "Verified" else discord.Color.red()
            try:
                await guild.create_role(name=role_name, color=color, reason="Авто")
                created.append(role_name)
            except:
                pass
    all_roles = {}
    all_roles.update(FACEIT_ROLES)
    all_roles.update(AVG_KILLS_ROLES)
    all_roles.update(KD_ROLES)
    all_roles.update(MAP_ROLES)
    for name in all_roles.values():
        if not discord.utils.get(guild.roles, name=name):
            try:
                await guild.create_role(name=name, reason="Авто")
                created.append(name)
            except:
                pass
    return created, existed

@commands.Cog.listener()
async def on_guild_join(guild):
    print(f"➕ Бот добавлен на сервер {guild.name}")
    created, existed = await create_all_roles(guild)
    print(f"Создано ролей: {len(created)}")
    bot_member = guild.get_member(guild.me.id)
    if bot_member:
        bot_role = bot_member.top_role
        verified = discord.utils.get(guild.roles, name="Verified")
        unverified = discord.utils.get(guild.roles, name="Unverified")
        target_pos = 0
        if verified and verified.position > target_pos:
            target_pos = verified.position
        if unverified and unverified.position > target_pos:
            target_pos = unverified.position
        if target_pos and bot_role.position <= target_pos:
            try:
                await bot_role.edit(position=target_pos + 1)
            except:
                pass
    unverified_role = discord.utils.get(guild.roles, name="Unverified")
    if unverified_role:
        for member in guild.members:
            if not member.bot and not member.guild_permissions.administrator:
                try:
                    await member.add_roles(unverified_role)
                except:
                    pass

@commands.Cog.listener()
async def on_guild_remove(guild):
    print(f"➖ Бот удалён с {guild.name}")
    delete_server_config(guild.id)
    bot_roles = get_all_bot_roles()
    for role in guild.roles:
        if role.name in bot_roles:
            try:
                await role.delete()
            except:
                pass

async def setup(bot):
    bot.add_listener(on_guild_join, name='on_guild_join')
    bot.add_listener(on_guild_remove, name='on_guild_remove')