import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import json
import asyncio

from utils.permissions import in_guild_only
from database.db_manager import c, conn
from database.users import is_banned
from database.server_config import get_server_config

class LftCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="lft", description="Создать событие для поиска тиммейтов")
    @app_commands.describe(
        time="Время (например: 20:00)",
        maps="Карты через запятую (например: Mirage,Inferno)",
        description="Описание (например: нужен эйм)",
        role="Требуемая роль (эймер, саппорт и т.д.)"
    )
    async def slash_lft(self, interaction: discord.Interaction, time: str, maps: str, description: str = "", role: str = ""):
        if is_banned(interaction.user.id):
            await interaction.response.send_message("🚫 Вы забанены", ephemeral=True)
            return

        if not interaction.guild:
            await interaction.response.send_message("❌ Эту команду можно использовать только на сервере!", ephemeral=True)
            return

        config = get_server_config(interaction.guild.id)
        if not config or not config[0]:
            await interaction.response.send_message(
                "❌ На этом сервере не настроен канал для тиммейтов! Администратор должен использовать `/setup_channel`",
                ephemeral=True)
            return

        try:
            hour, minute = map(int, time.split(':'))
            event_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            if event_time < datetime.now():
                event_time += timedelta(days=1)
            if (event_time - datetime.now()).total_seconds() < 600:
                await interaction.response.send_message("❌ Время должно быть минимум через 10 минут!", ephemeral=True)
                return
        except:
            await interaction.response.send_message("❌ Неверный формат времени! Используй HH:MM", ephemeral=True)
            return

        c.execute('''INSERT INTO events (creator_id, guild_id, channel_id, event_time, maps, description, role, participants, confirmed, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (interaction.user.id, interaction.guild.id, config[0], event_time.isoformat(),
                   maps, description, role, json.dumps([]), json.dumps([]), datetime.now().isoformat()))
        conn.commit()
        event_id = c.lastrowid

        embed = discord.Embed(
            title=f"🎮 Поиск тиммейтов | {time}",
            description=description if description else "Нет описания",
            color=discord.Color.green(),
            timestamp=event_time
        )
        embed.add_field(name="🗺️ Карты", value=maps, inline=True)
        if role:
            embed.add_field(name="🎭 Требуется роль", value=role, inline=True)
        embed.add_field(name="👥 Участники", value="Пока никого", inline=False)
        embed.set_footer(text=f"Создал: {interaction.user.display_name} | ID: {event_id}")

        class EventButtons(discord.ui.View):
            def __init__(self, event_id, creator_id):
                super().__init__(timeout=None)
                self.event_id = event_id
                self.creator_id = creator_id

            @discord.ui.button(label="✅ Пойду", style=discord.ButtonStyle.success)
            async def join_button(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id == self.creator_id:
                    await button_interaction.response.send_message("❌ Вы создатель события!", ephemeral=True)
                    return

                c.execute('SELECT participants FROM events WHERE id = ?', (self.event_id,))
                result = c.fetchone()
                if result:
                    participants = json.loads(result[0])
                    if button_interaction.user.id not in participants:
                        participants.append(button_interaction.user.id)
                        c.execute('UPDATE events SET participants = ? WHERE id = ?', (json.dumps(participants), self.event_id))
                        conn.commit()

                        new_embed = button_interaction.message.embeds[0]
                        new_embed.set_field_at(2, name="👥 Участники", value=f"{len(participants)} человек", inline=False)
                        await button_interaction.response.edit_message(embed=new_embed, view=self)

                        creator = await self.bot.fetch_user(self.creator_id)
                        if creator:
                            try:
                                await creator.send(f"✅ {button_interaction.user.display_name} присоединился к вашему событию!")
                            except:
                                pass
                    else:
                        await button_interaction.response.send_message("❌ Вы уже в списке!", ephemeral=True)

            @discord.ui.button(label="❌ Не пойду", style=discord.ButtonStyle.danger)
            async def leave_button(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                c.execute('SELECT participants FROM events WHERE id = ?', (self.event_id,))
                result = c.fetchone()
                if result:
                    participants = json.loads(result[0])
                    if button_interaction.user.id in participants:
                        participants.remove(button_interaction.user.id)
                        c.execute('UPDATE events SET participants = ? WHERE id = ?', (json.dumps(participants), self.event_id))
                        conn.commit()

                        new_embed = button_interaction.message.embeds[0]
                        new_embed.set_field_at(2, name="👥 Участники", value=f"{len(participants)} человек", inline=False)
                        await button_interaction.response.edit_message(embed=new_embed, view=self)
                    else:
                        await button_interaction.response.send_message("❌ Вас нет в списке!", ephemeral=True)

        view = EventButtons(event_id, interaction.user.id)
        channel = interaction.guild.get_channel(config[0])
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Событие создано!", ephemeral=True)

        async def event_timer():
            await asyncio.sleep((event_time - datetime.now()).total_seconds() - 300)
            c.execute('SELECT participants FROM events WHERE id = ?', (event_id,))
            result = c.fetchone()
            if result:
                participants = json.loads(result[0])
                if len(participants) < 2:
                    await channel.send("❌ Событие отменено: недостаточно участников (минимум 2)")
                    c.execute('UPDATE events SET status = "cancelled" WHERE id = ?', (event_id,))
                    conn.commit()
                    return

                for user_id in participants:
                    user = await self.bot.fetch_user(user_id)
                    if user:
                        try:
                            await user.send(f"🔔 Напоминание: ваше событие начнётся через 5 минут!\n{embed.url}")
                        except:
                            pass

                await channel.send(f"🔔 **{len(participants)}** участников! Событие начнётся через 5 минут!")

                await asyncio.sleep(240)
                for user_id in participants:
                    user = await self.bot.fetch_user(user_id)
                    if user:
                        try:
                            await user.send(f"⚠️ Событие начнётся через 1 минуту!")
                        except:
                            pass

                await asyncio.sleep(60)
                for user_id in participants:
                    c.execute('''INSERT INTO reliability_rating (user_id, rating, total_events, attended)
                                 VALUES (?, 1000, 1, 1)
                                 ON CONFLICT(user_id) DO UPDATE SET
                                 rating = rating + 50,
                                 total_events = total_events + 1,
                                 attended = attended + 1''', (user_id,))
                    conn.commit()

        asyncio.create_task(event_timer())

    @app_commands.command(name="rating", description="Показать рейтинг надежности игрока")
    @app_commands.describe(user="Пользователь (опционально)")
    async def slash_rating(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user

        c.execute('SELECT rating, total_events, attended, late, missed FROM reliability_rating WHERE user_id = ?', (target.id,))
        result = c.fetchone()

        if not result:
            await interaction.response.send_message(f"📊 У {target.display_name} пока нет рейтинга (нужно участвовать в событиях)")
            return

        rating, total, attended, late, missed = result

        if rating >= 1500:
            color = discord.Color.gold()
            rank = "👑 Легенда"
        elif rating >= 1200:
            color = discord.Color.green()
            rank = "⭐ Надёжный"
        elif rating >= 900:
            color = discord.Color.blue()
            rank = "👍 Хороший"
        elif rating >= 700:
            color = discord.Color.orange()
            rank = "⚠️ Средний"
        else:
            color = discord.Color.red()
            rank = "❌ Ненадёжный"

        embed = discord.Embed(
            title=f"📊 Рейтинг надёжности: {target.display_name}",
            description=f"**Ранг:** {rank}",
            color=color
        )
        embed.add_field(name="🎯 Рейтинг", value=f"**{rating}**", inline=True)
        embed.add_field(name="📅 Всего событий", value=str(total), inline=True)
        embed.add_field(name="✅ Пришёл", value=str(attended), inline=True)
        embed.add_field(name="⏰ Опоздал", value=str(late), inline=True)
        embed.add_field(name="❌ Пропустил", value=str(missed), inline=True)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(LftCog(bot))