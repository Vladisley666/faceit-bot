from discord import app_commands

def in_dm_only():
    async def predicate(interaction):
        if interaction.guild:
            await interaction.response.send_message("❌ Эту команду можно использовать только в ЛС!", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

def in_guild_only():
    async def predicate(interaction):
        if not interaction.guild:
            await interaction.response.send_message("❌ Эту команду можно использовать только на сервере!", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)