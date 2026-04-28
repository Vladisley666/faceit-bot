import discord
from discord import app_commands
from discord.ext import commands
from utils.permissions import in_guild_only
from utils.faceit_api import get_faceit_data, get_player_detailed_stats
from utils.helpers import get_all_players, get_user_faceit
from database.db_manager import c
from database.users import is_banned

class PlayerSelect(discord.ui.Select):
    def __init__(self, players):
        options = []
        for discord_id, nickname, level in players[:25]:
            options.append(
                discord.SelectOption(
                    label=f"{nickname} (Level {level})",
                    value=str(discord_id),
                    description=f"ID: {discord_id}"
                )
            )
        super().__init__(
            placeholder="👥 Выбери игрока для просмотра статистики...",
            min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        discord_id = int(self.values[0])
        c.execute('SELECT faceit_nickname FROM faceit_users WHERE discord_id = ?', (discord_id,))
        result = c.fetchone()
        if not result:
            await interaction.followup.send("❌ Игрок не найден", ephemeral=True)
            return
        nickname = result[0]
        stats, error = await get_player_detailed_stats(nickname)
        if error:
            await interaction.followup.send(error, ephemeral=True)
            return
        embed = discord.Embed(
            title=f"📊 Статистика Faceit: {nickname}",
            url=f"https://www.faceit.com/en/players/{nickname}",
            color=discord.Color.blue()
        )
        embed.add_field(name="🎮 Уровень", value=f"**{stats['level']}**", inline=True)
        embed.add_field(name="📈 ELO", value=f"**{stats['elo']}**", inline=True)
        embed.add_field(name="📊 Win %", value=f"**{stats['win_percentage']}%**", inline=True)
        embed.add_field(name="⚔️ AVG Kills", value=f"**{stats['avg_kills']}**", inline=True)
        embed.add_field(name="📊 K/D", value=f"**{stats['kd']}**", inline=True)
        embed.add_field(name="🗺️ Любимая карта", value=f"**{stats['favorite_map']}**", inline=True)
        embed.set_footer(text=f"ID: {stats['player_id']}")
        await interaction.followup.send(embed=embed)
        try:
            await interaction.delete_original_response()
        except:
            pass

class PlayerView(discord.ui.View):
    def __init__(self, players):
        super().__init__()
        self.add_item(PlayerSelect(players))

class StatsCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="info", description="Показать подробную статистику любого игрока (работает везде)")
    @app_commands.describe(nickname="Никнейм на Faceit")
    async def slash_info(self, interaction: discord.Interaction, nickname: str):
        if is_banned(interaction.user.id):
            await interaction.response.send_message("🚫 Вы забанены", ephemeral=True)
            return
        await interaction.response.defer()
        stats, error = await get_player_detailed_stats(nickname)
        if error:
            await interaction.followup.send(error)
            return
        embed = discord.Embed(
            title=f"📊 Статистика Faceit: {nickname}",
            url=f"https://www.faceit.com/en/players/{nickname}",
            color=discord.Color.blue()
        )
        embed.add_field(name="🎮 Уровень", value=f"**{stats['level']}**", inline=True)
        embed.add_field(name="📈 ELO", value=f"**{stats['elo']}**", inline=True)
        embed.add_field(name="📊 Win %", value=f"**{stats['win_percentage']}%**", inline=True)
        embed.add_field(name="⚔️ AVG Kills", value=f"**{stats['avg_kills']}**", inline=True)
        embed.add_field(name="📊 K/D", value=f"**{stats['kd']}**", inline=True)
        embed.add_field(name="🗺️ Любимая карта", value=f"**{stats['favorite_map']}**", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="faceit", description="Показать базовую информацию (уровень, ELO) игрока Faceit")
    @app_commands.describe(nickname="Никнейм на Faceit")
    async def slash_faceit(self, interaction: discord.Interaction, nickname: str):
        if is_banned(interaction.user.id):
            await interaction.response.send_message("🚫 Вы забанены", ephemeral=True)
            return
        await interaction.response.defer()
        data, error = await get_faceit_data(nickname)
        if error:
            await interaction.followup.send(error)
            return
        try:
            country = data.get('country', 'N/A')
            level = data['games']['cs2']['skill_level']
            elo = data['games']['cs2']['faceit_elo']
            embed = discord.Embed(
                title=f"🎮 Faceit: {nickname}",
                url=f"https://www.faceit.com/en/players/{nickname}",
                color=discord.Color.purple()
            )
            embed.add_field(name="Уровень", value=f"**{level}**", inline=True)
            embed.add_field(name="ELO", value=f"**{elo}**", inline=True)
            embed.add_field(name="Страна", value=f":flag_{country.lower()}:" if country != 'N/A' else "N/A", inline=True)
            await interaction.followup.send(embed=embed)
        except KeyError:
            await interaction.followup.send("❌ Ошибка в данных Faceit (возможно нет CS2 профиля)")

    @app_commands.command(name="stats", description="Показать детальную статистику игрока. Без ника — выбор из списка верифицированных")
    @app_commands.describe(nickname="Никнейм на Faceit (необязательно)")
    async def slash_stats(self, interaction: discord.Interaction, nickname: str = None):
        if is_banned(interaction.user.id):
            await interaction.response.send_message("🚫 Вы забанены", ephemeral=True)
            return
        if nickname:
            await interaction.response.defer()
            stats, error = await get_player_detailed_stats(nickname)
            if error:
                await interaction.followup.send(error)
                return
            embed = discord.Embed(
                title=f"📊 Статистика Faceit: {nickname}",
                url=f"https://www.faceit.com/en/players/{nickname}",
                color=discord.Color.purple()
            )
            embed.add_field(name="🎮 Уровень", value=f"**{stats['level']}**", inline=True)
            embed.add_field(name="📈 ELO", value=f"**{stats['elo']}**", inline=True)
            embed.add_field(name="📊 Win %", value=f"**{stats['win_percentage']}%**", inline=True)
            embed.add_field(name="⚔️ AVG Kills", value=f"**{stats['avg_kills']}**", inline=True)
            embed.add_field(name="📊 K/D", value=f"**{stats['kd']}**", inline=True)
            embed.add_field(name="🗺️ Любимая карта", value=f"**{stats['favorite_map']}**", inline=True)
            await interaction.followup.send(embed=embed)
            return
        players = get_all_players()
        if not players:
            await interaction.response.send_message("📋 Нет верифицированных игроков")
            return
        embed = discord.Embed(
            title="👥 Выбери игрока",
            description="Нажми на меню ниже",
            color=discord.Color.green()
        )
        embed.add_field(name="Всего игроков", value=str(len(players)), inline=True)
        view = PlayerView(players)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="myroles", description="[ТОЛЬКО НА СЕРВЕРЕ] Показать все ваши роли на этом сервере")
    @in_guild_only()
    async def slash_myroles(self, interaction: discord.Interaction):
        if is_banned(interaction.user.id):
            await interaction.response.send_message("🚫 Вы забанены", ephemeral=True)
            return
        roles = [role.mention for role in interaction.user.roles if role.name != "@everyone"]
        if roles:
            await interaction.response.send_message(f"📋 **Твои роли:**\n" + "\n".join(roles))
        else:
            await interaction.response.send_message("📋 У тебя нет ролей на этом сервере.")

    @app_commands.command(name="help", description="Показать список всех команд бота")
    async def slash_help(self, interaction: discord.Interaction):
        is_admin = interaction.user.guild_permissions.administrator if interaction.guild else False
        embed = discord.Embed(
            title="📚 **FACEIT RANK BOT - ПОМОЩЬ**",
            description="Бот для автоматической выдачи ролей по Faceit статистике",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="👤 **ДЛЯ ВСЕХ**",
            value=(
                "`/verify ник steam_id` — начать верификацию (только в ЛС)\n"
                "`/confirm код` — подтвердить код из Steam\n"
                "`/refresh [ник]` — обновить статистику (только на сервере)\n"
                "`/info ник` — статистика любого игрока\n"
                "`/faceit ник` — базовая информация\n"
                "`/stats [ник]` — статистика или выбор из списка\n"
                "`/myroles` — показать твои роли\n"
                "`/balance` — показать баланс монет\n"
                "`/daily` — получить ежедневный бонус\n"
                "`/shop` — магазин стилей\n"
                "`/buy_style название` — купить стиль\n"
                "`/styles` — показать купленные стили\n"
                "`/reset_nick` — сбросить ник\n"
                "`/lft время карты [описание] [роль]` — создать событие\n"
                "`/rating [пользователь]` — показать рейтинг надежности\n"
                "`/achievements` — показать полученные достижения"
            ),
            inline=False
        )
        if is_admin:
            embed.add_field(
                name="🛠️ **АДМИН КОМАНДЫ**",
                value=(
                    "`/setup_channel` — настроить канал (в ЛС)\n"
                    "`/check_bot_position` — проверить позицию бота\n"
                    "`/fix_bot_role` — поднять роль бота\n"
                    "`/force_unverified` — выдать Unverified всем\n"
                    "`/cleanup_old_roles` — удалить пустые роли\n"
                    "`/force_delete_all_roles` — удалить ВСЕ роли бота\n"
                    "`/remove_all_bot_roles_from_users` — снять роли с участников\n"
                    "`/check_configs` — показать все настроенные каналы\n"
                    "`/check_server` — проверить настройки сервера по ID\n"
                    "`/sync_roles` — синхронизировать роли карт на всех серверах\n"
                    "`/sync_achievement_roles` — создать все роли достижений на всех серверах\n"
                    "`/sync_all_roles` — создать ВСЕ роли бота на всех серверах\n"
                    "`/advertising_on` — включить рекламу на сервере\n"
                    "`/advertising_off` — отключить рекламу на сервере\n"
                    "`/logs` — показать логи действий\n"
                    "`/ban` — забанить\n"
                    "`/unban` — разбанить\n"
                    "`/banlist` — список банов"
                ),
                inline=False
            )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(StatsCommandsCog(bot))