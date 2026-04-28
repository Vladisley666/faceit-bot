import discord
from discord import app_commands
from discord.ext import commands
from utils.helpers import get_user_achievements
from database.users import is_banned

class AchievementsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="achievements", description="Показать список полученных достижений. Достижения даются за активность на сервере.")
    async def achievements(self, interaction: discord.Interaction):
        if is_banned(interaction.user.id):
            await interaction.response.send_message("🚫 Вы забанены", ephemeral=True)
            return

        achievements = get_user_achievements(interaction.user.id)

        if not achievements:
            await interaction.response.send_message("📋 У вас пока нет достижений. Участвуйте в жизни сервера!")
            return

        embed = discord.Embed(
            title=f"🏆 Достижения {interaction.user.display_name}",
            color=discord.Color.gold()
        )

        for name, desc in achievements:
            embed.add_field(name=name, value=desc, inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AchievementsCog(bot))