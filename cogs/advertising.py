import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from config import MAIN_ADMIN_IDS
from database.server_config import get_server_config, save_server_config
from database.admin_logs import log_admin_action

async def ad_timeout(bot, user_id):
    await asyncio.sleep(300)
    if hasattr(bot, 'advertising_running'):
        bot.advertising_running = False
    if hasattr(bot, 'waiting_for_ad') and bot.waiting_for_ad:
        bot.waiting_for_ad = False
        user = bot.get_user(user_id)
        if user:
            try:
                await user.send("⏱️ Время ожидания рекламы истекло.")
            except:
                pass

class AdvertisingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="advertising_on", description="[АДМИН] Включить приём рекламы на этом сервере (реклама будет отправляться в настроенный канал)")
    @app_commands.default_permissions(administrator=True)
    async def advertising_on(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Только для админов!", ephemeral=True)
            return
        config = get_server_config(interaction.guild.id)
        if not config or not config[0]:
            await interaction.response.send_message("❌ Сначала настрой канал командой `/setup_channel`", ephemeral=True)
            return
        save_server_config(interaction.guild.id, config[0], config[1], config[2], 1)
        await interaction.response.send_message("✅ Реклама включена на этом сервере!", ephemeral=True)
        log_admin_action(interaction.user.id, "advertising_on", None, interaction.guild.name)

    @app_commands.command(name="advertising_off", description="[АДМИН] Отключить приём рекламы на этом сервере")
    @app_commands.default_permissions(administrator=True)
    async def advertising_off(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Только для админов!", ephemeral=True)
            return
        config = get_server_config(interaction.guild.id)
        if not config or not config[0]:
            await interaction.response.send_message("❌ Канал не настроен", ephemeral=True)
            return
        save_server_config(interaction.guild.id, config[0], config[1], config[2], 0)
        await interaction.response.send_message("✅ Реклама отключена на этом сервере!", ephemeral=True)
        log_admin_action(interaction.user.id, "advertising_off", None, interaction.guild.name)

    @app_commands.command(name="advertising", description="[ГЛАВНЫЙ АДМИН] Запустить режим рассылки рекламы")
    async def slash_advertising(self, interaction: discord.Interaction):
        if interaction.user.id not in MAIN_ADMIN_IDS:
            await interaction.response.send_message("❌ Нет прав. Команда доступна только создателю бота.", ephemeral=True)
            return
        if hasattr(self.bot, 'advertising_running') and self.bot.advertising_running:
            await interaction.response.send_message("❌ Реклама уже запущена", ephemeral=True)
            return

        self.bot.advertising_running = True
        self.bot.ad_admin_id = interaction.user.id
        self.bot.waiting_for_ad = True
        embed = discord.Embed(
            title="📢 Режим рекламы активирован",
            description="Отправь мне сообщение с рекламой!\n⏱️ 5 минут.",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.bot.ad_timer = asyncio.create_task(ad_timeout(self.bot, interaction.user.id))

async def setup(bot):
    await bot.add_cog(AdvertisingCog(bot))