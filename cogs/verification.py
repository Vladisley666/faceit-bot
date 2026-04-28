import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio

from utils.permissions import in_dm_only, in_guild_only
from utils.faceit_api import get_faceit_data, get_player_detailed_stats
from utils.steam_api import check_steam_summary
from utils.helpers import (
    get_user_faceit, get_user_status, save_user_status,
    get_verify_code, save_verify_code, delete_verify_code,
    save_user_faceit, invalidate_players_cache, get_coins,
    can_update, save_update_time, is_data_stale
)
from database.db_manager import c, conn
from database.users import is_banned
from utils.role_colors import get_role_color
from config import FACEIT_ROLES, AVG_KILLS_ROLES, KD_ROLES, MAP_ROLES

# ----------------------------------------------------------------------
# Функция обновления ролей пользователя (полная версия)
# ----------------------------------------------------------------------
async def update_user_role(member, faceit_nickname):
    await asyncio.sleep(2)
    if not faceit_nickname:
        return False, "❌ Ник не указан"

    data, error = await get_faceit_data(faceit_nickname)
    if error:
        return False, error
    if not data or 'games' not in data or 'cs2' not in data['games']:
        return False, "❌ Нет CS2 профиля"

    player_level = data['games']['cs2']['skill_level']
    steam_id = data.get('games', {}).get('cs2', {}).get('steam_id')

    stats, stats_error = await get_player_detailed_stats(faceit_nickname)
    if stats_error:
        stats = {"avg_kills": 0, "kd": 0, "win_percentage": 0, "favorite_map": "Неизвестно", "matches_count": 0}

    all_role_names = (list(FACEIT_ROLES.values()) +
                      list(AVG_KILLS_ROLES.values()) +
                      list(KD_ROLES.values()) +
                      list(MAP_ROLES.values()))

    # Удаляем старые роли бота
    for old_role in member.roles:
        if old_role.name in all_role_names:
            try:
                await member.remove_roles(old_role)
            except:
                pass

    roles_added = []

    # Уровень
    level_role_name = FACEIT_ROLES.get(player_level)
    if level_role_name:
        level_role = discord.utils.get(member.guild.roles, name=level_role_name)
        if not level_role:
            try:
                level_role = await member.guild.create_role(
                    name=level_role_name,
                    color=discord.Color(get_role_color("level", player_level)),
                    reason="Авто"
                )
            except:
                pass
        if level_role:
            try:
                await member.add_roles(level_role)
                roles_added.append(f"Уровень {player_level}")
            except:
                pass

    # AVG Kills
    if stats and stats.get('matches_count', 0) > 0:
        avg_kills = stats['avg_kills']
        if avg_kills < 10:
            avg_role_key = "below_10"
        elif avg_kills < 11:
            avg_role_key = "10_11"
        elif avg_kills < 12:
            avg_role_key = "11_12"
        elif avg_kills < 13:
            avg_role_key = "12_13"
        elif avg_kills < 14:
            avg_role_key = "13_14"
        elif avg_kills < 15:
            avg_role_key = "14_15"
        elif avg_kills < 16:
            avg_role_key = "15_16"
        elif avg_kills < 17:
            avg_role_key = "16_17"
        elif avg_kills < 18:
            avg_role_key = "17_18"
        elif avg_kills < 19:
            avg_role_key = "18_19"
        elif avg_kills < 20:
            avg_role_key = "19_20"
        else:
            avg_role_key = "above_20"

        avg_role_name = AVG_KILLS_ROLES[avg_role_key]
        avg_role = discord.utils.get(member.guild.roles, name=avg_role_name)
        if not avg_role:
            try:
                avg_role = await member.guild.create_role(
                    name=avg_role_name,
                    color=discord.Color(get_role_color("avg", avg_kills)),
                    reason="Авто"
                )
            except:
                pass
        if avg_role:
            try:
                await member.add_roles(avg_role)
                roles_added.append(avg_role_name)
            except:
                pass

        # K/D
        kd = stats['kd']
        if kd < 0.9:
            kd_role_key = "below_0.9"
        elif kd < 1.0:
            kd_role_key = "0.9_1.0"
        elif kd < 1.1:
            kd_role_key = "1.0_1.1"
        elif kd < 1.2:
            kd_role_key = "1.1_1.2"
        elif kd < 1.3:
            kd_role_key = "1.2_1.3"
        elif kd < 1.4:
            kd_role_key = "1.3_1.4"
        elif kd < 1.5:
            kd_role_key = "1.4_1.5"
        elif kd < 1.6:
            kd_role_key = "1.5_1.6"
        elif kd < 1.7:
            kd_role_key = "1.6_1.7"
        elif kd < 1.8:
            kd_role_key = "1.7_1.8"
        elif kd < 1.9:
            kd_role_key = "1.8_1.9"
        elif kd < 2.0:
            kd_role_key = "1.9_2.0"
        else:
            kd_role_key = "above_2"

        kd_role_name = KD_ROLES[kd_role_key]
        kd_role = discord.utils.get(member.guild.roles, name=kd_role_name)
        if not kd_role:
            try:
                kd_role = await member.guild.create_role(
                    name=kd_role_name,
                    color=discord.Color(get_role_color("kd", kd)),
                    reason="Авто"
                )
            except:
                pass
        if kd_role:
            try:
                await member.add_roles(kd_role)
                roles_added.append(kd_role_name)
            except:
                pass

        # Карта
        favorite_map = stats.get('favorite_map', 'Unknown')
        if favorite_map in MAP_ROLES:
            map_role_name = MAP_ROLES[favorite_map]
            map_role = discord.utils.get(member.guild.roles, name=map_role_name)
            if not map_role:
                try:
                    map_role = await member.guild.create_role(
                        name=map_role_name,
                        color=discord.Color(get_role_color("map", 0)),
                        reason="Авто"
                    )
                except:
                    pass
            if map_role:
                try:
                    await member.add_roles(map_role)
                    roles_added.append(map_role_name)
                except:
                    pass

    # Сохраняем в БД
    save_user_faceit(
        member.id,
        faceit_nickname,
        player_level,
        stats.get('avg_kills', 0),
        stats.get('kd', 0),
        stats.get('favorite_map', 'Unknown'),
        stats.get('win_percentage', 0),
        steam_id,
        get_coins(member.id)
    )
    invalidate_players_cache()

    stats_info = f"📊 AVG: {stats.get('avg_kills',0)} | K/D: {stats.get('kd',0)} | Win: {stats.get('win_percentage',0)}% | 🗺️ {stats.get('favorite_map','Unknown')}"
    player_url = f"https://www.faceit.com/en/players/{faceit_nickname}"
    return True, (player_level, roles_added, stats_info, data.get('player_id'), player_url)

# ----------------------------------------------------------------------
# Синхронизация пользователя по всем серверам
# ----------------------------------------------------------------------
async def sync_user_across_servers(bot, user_id: int, faceit_nickname: str):
    from database.server_config import get_server_config
    print(f"\n🔄 Синхронизация {user_id} ({faceit_nickname})...")
    for guild in bot.guilds:
        member = guild.get_member(user_id)
        if member:
            success, result = await update_user_role(member, faceit_nickname)
            if success:
                config = get_server_config(guild.id)
                if config:
                    verified_role = guild.get_role(config[1])
                    unverified_role = guild.get_role(config[2])
                    if verified_role and verified_role not in member.roles:
                        try:
                            await member.add_roles(verified_role)
                        except:
                            pass
                    if unverified_role and unverified_role in member.roles:
                        try:
                            await member.remove_roles(unverified_role)
                        except:
                            pass
            else:
                print(f"   ❌ Ошибка на {guild.name}: {result}")

# ----------------------------------------------------------------------
# Ког верификации
# ----------------------------------------------------------------------
class VerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="verify", description="[ТОЛЬКО ЛС] Привязать Faceit профиль к Discord аккаунту")
    @app_commands.describe(
        faceit_nick="Твой никнейм на Faceit",
        steam_id="Твой Steam ID (17 цифр, из ссылки профиля)"
    )
    @in_dm_only()
    async def slash_verify(self, interaction: discord.Interaction, faceit_nick: str, steam_id: str):
        if is_banned(interaction.user.id):
            await interaction.response.send_message("🚫 Вы забанены", ephemeral=True)
            return

        await interaction.response.defer()

        user_data = get_user_faceit(interaction.user.id)
        if user_data and user_data[0]:
            await interaction.followup.send(f"✅ Ты уже верифицирован как **{user_data[0]}**")
            return

        data, error = await get_faceit_data(faceit_nick)
        if error:
            await interaction.followup.send(error)
            return

        c.execute('SELECT discord_id FROM faceit_users WHERE faceit_nickname = ?', (faceit_nick,))
        existing = c.fetchone()
        if existing and existing[0] != interaction.user.id:
            await interaction.followup.send(f"❌ Профиль **{faceit_nick}** уже привязан к другому Discord аккаунту")
            return

        if not steam_id.isdigit() or len(steam_id) != 17:
            await interaction.followup.send("❌ Неверный Steam ID. Должно быть 17 цифр")
            return

        success, check_error = await check_steam_summary(steam_id, "")
        if not success and "не найден" in check_error:
            await interaction.followup.send(f"❌ Steam профиль с ID `{steam_id}` не найден.")
            return

        code = save_verify_code(interaction.user.id, faceit_nick, steam_id)

        embed = discord.Embed(
            title="🔐 Подтверждение владения профилем",
            description=f"**{faceit_nick}**, нужно подтвердить:",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📝 Инструкция:",
            value=f"1️⃣ Зайди в [Steam профиль](https://steamcommunity.com/profiles/{steam_id}/edit)\n"
                  f"2️⃣ В поле **Real Name** вставь код:\n```{code}```\n"
                  f"3️⃣ Сохрани\n4️⃣ Напиши `/confirm {code}`\n\n"
                  f"⏱️ Код действителен 10 минут",
            inline=False
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="confirm", description="[ТОЛЬКО ЛС] Подтвердить код из Steam (после /verify)")
    @app_commands.describe(code="Код из поля Real Name вашего Steam профиля")
    @in_dm_only()
    async def slash_confirm(self, interaction: discord.Interaction, code: str):
        if is_banned(interaction.user.id):
            await interaction.response.send_message("🚫 Вы забанены", ephemeral=True)
            return

        await interaction.response.defer()

        saved_code, faceit_nick, steam_id, expires_at = get_verify_code(interaction.user.id)
        if not saved_code:
            await interaction.followup.send("❌ Нет активного кода. Используй `/verify ник steam_id`")
            return
        if code != saved_code:
            await interaction.followup.send("❌ Неверный код")
            return
        if datetime.now() > expires_at:
            delete_verify_code(interaction.user.id)
            await interaction.followup.send("❌ Код истёк. Используй `/verify` снова")
            return

        await interaction.followup.send(f"🔍 Проверяю Steam профиль `{steam_id}`...")
        success, error = await check_steam_summary(steam_id, code)

        if not success:
            await interaction.followup.send(f"❌ {error}")
            return

        delete_verify_code(interaction.user.id)
        await interaction.followup.send(f"✅ Код подтверждён! Выдаю роли...")

        await sync_user_across_servers(self.bot, interaction.user.id, faceit_nick)

        embed = discord.Embed(
            title="✅ Верификация успешна!",
            description=f"Профиль **{faceit_nick}** подтверждён и привязан",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="refresh", description="[ТОЛЬКО НА СЕРВЕРЕ] Обновить статистику Faceit и выдать актуальные роли")
    @app_commands.describe(nickname="Никнейм на Faceit (оставьте пустым, чтобы использовать сохранённый)")
    @in_guild_only()
    async def slash_refresh(self, interaction: discord.Interaction, nickname: str = None):
        if is_banned(interaction.user.id):
            await interaction.response.send_message("🚫 Вы забанены", ephemeral=True)
            return

        await interaction.response.defer()

        old_data = get_user_faceit(interaction.user.id)
        old_nick = old_data[0] if old_data else None

        if not nickname:
            if old_nick:
                nickname = old_nick
            else:
                await interaction.followup.send("❌ У тебя нет привязанного профиля. Используй `/verify` в ЛС")
                return

        if old_nick and old_nick.lower() != nickname.lower():
            await interaction.followup.send(
                f"🔄 Смена профиля с **{old_nick}** на **{nickname}**\n"
                f"Напиши в ЛС `/verify {nickname} steam_id` и пройди верификацию."
            )
            return

        await interaction.followup.send(f"🔄 Обновляю статистику для **{nickname}**...")
        success, result = await update_user_role(interaction.user, nickname)
        if not success:
            await interaction.followup.send(result)
            return

        player_level, roles_added, stats_info, player_id, player_url = result
        embed = discord.Embed(
            title="✅ Статистика обновлена!",
            description=f"Профиль **{nickname}**",
            color=discord.Color.blue(),
            url=player_url
        )
        embed.add_field(name="🎮 Уровень", value=f"**{player_level}**", inline=True)
        embed.add_field(name="📊 Статистика", value=stats_info, inline=False)
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(VerificationCog(bot))