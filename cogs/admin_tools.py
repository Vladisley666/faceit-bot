import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from utils.permissions import in_dm_only
from database.server_config import get_server_config, save_server_config, delete_server_config
from database.admin_logs import log_admin_action
from database.users import ban_user, unban_user, is_banned, get_all_bans
from config import MAIN_ADMIN_IDS, get_all_bot_roles
from database.db_manager import c, conn
from utils.role_colors import get_role_color
from config import FACEIT_ROLES, AVG_KILLS_ROLES, KD_ROLES, MAP_ROLES

class AdminToolsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ------------------------------------------------------------
    # ОСНОВНЫЕ КОМАНДЫ
    # ------------------------------------------------------------
    @app_commands.command(name="ban", description="Забанить пользователя (только для админов)")
    @app_commands.describe(member="Пользователь для бана", reason="Причина бана")
    async def slash_ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Не указана"):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Нет прав", ephemeral=True)
            return
        c.execute('SELECT faceit_nickname FROM faceit_users WHERE discord_id = ?', (member.id,))
        row = c.fetchone()
        faceit_nickname = row[0] if row else "Не верифицирован"
        ban_user(member.id, faceit_nickname, interaction.user.id, reason)
        all_roles = get_all_bot_roles()
        for role in member.roles:
            if role.name in all_roles:
                try:
                    await member.remove_roles(role)
                except:
                    pass
        embed = discord.Embed(title="🚫 Пользователь забанен", color=discord.Color.red())
        embed.add_field(name="Пользователь", value=member.mention, inline=True)
        embed.add_field(name="Faceit ник", value=faceit_nickname, inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        await interaction.response.send_message(embed=embed)
        log_admin_action(interaction.user.id, "ban", member.id, reason)

    @app_commands.command(name="unban", description="Разбанить пользователя (только для админов)")
    @app_commands.describe(discord_id="ID пользователя для разбана")
    async def slash_unban(self, interaction: discord.Interaction, discord_id: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Нет прав", ephemeral=True)
            return
        try:
            user_id = int(discord_id)
        except ValueError:
            await interaction.response.send_message("❌ Некорректный ID", ephemeral=True)
            return
        if not is_banned(user_id):
            await interaction.response.send_message("❌ Пользователь не в бане", ephemeral=True)
            return
        unban_user(user_id)
        await interaction.response.send_message(f"✅ Пользователь с ID {user_id} разбанен")
        log_admin_action(interaction.user.id, "unban", user_id, "")

    @app_commands.command(name="banlist", description="Показать список забаненных")
    async def slash_banlist(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Нет прав", ephemeral=True)
            return
        bans = get_all_bans()
        if not bans:
            await interaction.response.send_message("📋 Бан-лист пуст")
            return
        embed = discord.Embed(title="📋 Бан-лист", color=discord.Color.orange())
        ban_text = ""
        for discord_id, nickname, reason, ban_time in bans[:10]:
            ban_time_obj = datetime.fromisoformat(ban_time)
            ban_text += f"• <@{discord_id}> | {nickname} | {ban_time_obj.strftime('%d.%m.%Y')}\n"
        embed.add_field(name="Забаненные", value=ban_text, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="logs", description="[АДМИН] Показать логи действий")
    @app_commands.describe(user="Показать логи только для этого админа", limit="Количество записей (до 50)")
    async def slash_logs(self, interaction: discord.Interaction, user: discord.User = None, limit: int = 10):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Только для админов!", ephemeral=True)
            return
        if limit > 50:
            limit = 50
        if user:
            c.execute('''SELECT admin_id, action, target_id, details, timestamp 
                         FROM admin_logs 
                         WHERE admin_id = ? 
                         ORDER BY timestamp DESC 
                         LIMIT ?''', (user.id, limit))
        else:
            c.execute('''SELECT admin_id, action, target_id, details, timestamp 
                         FROM admin_logs 
                         ORDER BY timestamp DESC 
                         LIMIT ?''', (limit,))
        logs = c.fetchall()
        if not logs:
            await interaction.response.send_message("📋 Логов не найдено")
            return
        embed = discord.Embed(title="📋 Логи действий админов", color=discord.Color.blue())
        for admin_id, action, target_id, details, timestamp in logs:
            admin = await self.bot.fetch_user(admin_id)
            admin_name = admin.display_name if admin else str(admin_id)
            target = f" | <@{target_id}>" if target_id else ""
            embed.add_field(
                name=f"{timestamp.split('T')[0]} {timestamp.split('T')[1][:8]}",
                value=f"**{admin_name}** → {action}{target}\n{details[:50] if details else ''}",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    # ------------------------------------------------------------
    # НОВАЯ КОМАНДА /stop
    # ------------------------------------------------------------
    @app_commands.command(name="stop", description="[АДМИН] Остановить бота")
    async def slash_stop(self, interaction: discord.Interaction):
        if interaction.user.id not in MAIN_ADMIN_IDS:
            await interaction.response.send_message("❌ Нет прав", ephemeral=True)
            return
        await interaction.response.send_message("🛑 Бот отключается...", ephemeral=True)
        await self.bot.close()

    # ------------------------------------------------------------
    # ЗАГЛУШКИ ДЛЯ ОСТАЛЬНЫХ АДМИН-КОМАНД (можно потом дописать)
    # ------------------------------------------------------------
    @app_commands.command(name="setup_channel", description="Настроить канал для тиммейтов (только в ЛС)")
    @in_dm_only()
    async def setup_channel(self, interaction: discord.Interaction):
        await interaction.response.send_message("Команда в разработке. Используйте старую версию бота для настройки.", ephemeral=True)

    @app_commands.command(name="check_bot_position", description="Проверить позицию роли бота")
    async def check_bot_position(self, interaction: discord.Interaction):
        await interaction.response.send_message("Команда в разработке.", ephemeral=True)

    @app_commands.command(name="fix_bot_role", description="Поднять роль бота")
    async def fix_bot_role(self, interaction: discord.Interaction):
        await interaction.response.send_message("Команда в разработке.", ephemeral=True)

    @app_commands.command(name="force_unverified", description="Выдать Unverified всем")
    async def force_unverified(self, interaction: discord.Interaction):
        await interaction.response.send_message("Команда в разработке.", ephemeral=True)

    @app_commands.command(name="cleanup_old_roles", description="Удалить пустые роли бота")
    async def cleanup_old_roles(self, interaction: discord.Interaction):
        await interaction.response.send_message("Команда в разработке.", ephemeral=True)

    @app_commands.command(name="force_delete_all_roles", description="Удалить ВСЕ роли бота")
    async def force_delete_all_roles(self, interaction: discord.Interaction):
        await interaction.response.send_message("Команда в разработке.", ephemeral=True)

    @app_commands.command(name="remove_all_bot_roles_from_users", description="Снять все роли бота с участников")
    async def remove_all_bot_roles_from_users(self, interaction: discord.Interaction):
        await interaction.response.send_message("Команда в разработке.", ephemeral=True)

    @app_commands.command(name="check_configs", description="Показать все настроенные каналы")
    async def check_configs(self, interaction: discord.Interaction):
        await interaction.response.send_message("Команда в разработке.", ephemeral=True)

    @app_commands.command(name="check_server", description="Проверить настройки сервера по ID")
    async def check_server(self, interaction: discord.Interaction, guild_id: str):
        await interaction.response.send_message("Команда в разработке.", ephemeral=True)

    @app_commands.command(name="sync_roles", description="Синхронизировать роли карт на всех серверах")
    async def sync_roles(self, interaction: discord.Interaction):
        await interaction.response.send_message("Команда в разработке.", ephemeral=True)

    @app_commands.command(name="sync_achievement_roles", description="Создать роли достижений на всех серверах")
    async def sync_achievement_roles(self, interaction: discord.Interaction):
        await interaction.response.send_message("Команда в разработке.", ephemeral=True)

    @app_commands.command(name="sync_all_roles", description="Создать ВСЕ роли бота на всех серверах")
    async def sync_all_roles(self, interaction: discord.Interaction):
        await interaction.response.send_message("Команда в разработке.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminToolsCog(bot))