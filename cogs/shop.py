import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta

from utils.helpers import get_coins, spend_coins, add_coins, get_owned_styles, add_owned_style, get_equipped_style
from database.db_manager import c, conn
from database.users import get_user_faceit
from database.coins_styles import get_coins as db_get_coins, add_coins as db_add_coins, spend_coins as db_spend_coins

# ----------------------------------------------------------------------
# Функции трансформации текста (стили)
# ----------------------------------------------------------------------
def superscript(text):
    mapping = {
        'a': 'ᵃ', 'b': 'ᵇ', 'c': 'ᶜ', 'd': 'ᵈ', 'e': 'ᵉ', 'f': 'ᶠ', 'g': 'ᵍ',
        'h': 'ʰ', 'i': 'ⁱ', 'j': 'ʲ', 'k': 'ᵏ', 'l': 'ˡ', 'm': 'ᵐ', 'n': 'ⁿ',
        'o': 'ᵒ', 'p': 'ᵖ', 'q': 'ᑫ', 'r': 'ʳ', 's': 'ˢ', 't': 'ᵗ', 'u': 'ᵘ',
        'v': 'ᵛ', 'w': 'ʷ', 'x': 'ˣ', 'y': 'ʸ', 'z': 'ᶻ',
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵',
        '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
    }
    return ''.join(mapping.get(c.lower(), c) for c in text)

def subscript(text):
    mapping = {
        'a': 'ₐ', 'b': 'ᵦ', 'c': '꜀', 'd': 'ᵈ', 'e': 'ₑ', 'f': 'բ', 'g': '₉',
        'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ', 'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ',
        'o': 'ₒ', 'p': 'ₚ', 'q': '𐞥', 'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ', 'u': 'ᵤ',
        'v': 'ᵥ', 'w': 'w', 'x': 'ₓ', 'y': 'ᵧ', 'z': '₂',
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅',
        '6': '₆', '7': '₇', '8': '₈', '9': '₉'
    }
    return ''.join(mapping.get(c.lower(), c) for c in text)

def square_letters(text):
    mapping = {}
    for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz':
        mapping[ch] = f'🄰'  # упрощённо, для реальной работы замени на полный словарь
    return text

def circle_letters(text): return text
def double_letters(text): return text
def italic_letters(text): return text
def calligraphy_letters(text): return text
def gothic_letters(text): return text
def small_caps(text): return text
def strikethrough(text): return ''.join(c + '\u0336' for c in text)

FREE_STYLES = {
    "жирный": {"emoji": "🔤", "price": 0, "transform": lambda s: f"**{s}**", "description": "**Жирный текст**"},
    "курсив": {"emoji": "📝", "price": 0, "transform": lambda s: f"*{s}*", "description": "*Курсив*"},
    "подчёркнутый": {"emoji": "📏", "price": 0, "transform": lambda s: f"<u>{s}</u>", "description": "<u>Подчёркнутый</u>"},
    "моноширинный": {"emoji": "💻", "price": 0, "transform": lambda s: f"`{s}`", "description": "`Моноширинный`"}
}

STYLE_SHOP = {
    "зачёркнутый": {"emoji": "🚫", "price": 500, "transform": strikethrough, "description": "Перечёркнутый текст"},
    "верхний индекс": {"emoji": "⬆️", "price": 1000, "transform": superscript, "description": "Верхний индекс"},
    "нижний индекс": {"emoji": "⬇️", "price": 1000, "transform": subscript, "description": "Нижний индекс"},
    "квадратные": {"emoji": "⬛", "price": 1500, "transform": square_letters, "description": "Квадратные буквы"},
    "круглые": {"emoji": "⭕", "price": 1500, "transform": circle_letters, "description": "Буквы в кружках"},
    "маленькие капс": {"emoji": "🔠", "price": 1500, "transform": small_caps, "description": "Маленькие заглавные"},
    "двойные": {"emoji": "🔷", "price": 2000, "transform": double_letters, "description": "Двойные буквы"},
    "курсивные": {"emoji": "✍️", "price": 2000, "transform": italic_letters, "description": "Курсив"},
    "каллиграфия": {"emoji": "🖌️", "price": 2500, "transform": calligraphy_letters, "description": "Каллиграфия"},
    "готический": {"emoji": "🏰", "price": 2500, "transform": gothic_letters, "description": "Готический"}
}

class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="balance", description="Показать баланс монет (валюты для покупки стилей ника)")
    @app_commands.describe(user="Пользователь, чей баланс показать (по умолчанию свой)")
    async def balance(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        coins = get_coins(target.id)
        embed = discord.Embed(title=f"💰 Баланс {target.display_name}", description=f"**{coins}** монет", color=discord.Color.gold())
        owned = get_owned_styles(target.id)
        if owned:
            embed.add_field(name="🎨 Купленные стили", value=", ".join(owned[:5]), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Получить ежедневный бонус (100 монет). Можно раз в 24 часа.")
    async def daily(self, interaction: discord.Interaction):
        c.execute('SELECT last_daily FROM user_coins WHERE user_id = ?', (interaction.user.id,))
        result = c.fetchone()
        if result and result[0]:
            last_daily = datetime.fromisoformat(result[0])
            if datetime.now() - last_daily < timedelta(days=1):
                remaining = timedelta(days=1) - (datetime.now() - last_daily)
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                await interaction.response.send_message(f"⏰ Ежедневный бонус будет доступен через {hours}ч {minutes}мин", ephemeral=True)
                return
        add_coins(interaction.user.id, 100)
        c.execute('UPDATE user_coins SET last_daily = ? WHERE user_id = ?', (datetime.now().isoformat(), interaction.user.id))
        conn.commit()
        await interaction.response.send_message(f"💰 Вы получили **100** монет! Баланс: **{get_coins(interaction.user.id)}**", ephemeral=True)

    @app_commands.command(name="shop", description="Показать магазин стилей для ника. Стили меняют отображение ника на сервере.")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛒 Магазин стилей",
            description="Купи стиль для своего ника!\n\n**БЕСПЛАТНЫЕ СТИЛИ:**",
            color=discord.Color.blue()
        )
        for name, style in FREE_STYLES.items():
            embed.add_field(name=f"{style['emoji']} {name}", value=f"{style['description']}\n💰 Цена: **{style['price']}** монет", inline=True)
        embed.add_field(name="━" * 20, value="**ПЛАТНЫЕ СТИЛИ:**", inline=False)
        for name, style in STYLE_SHOP.items():
            embed.add_field(name=f"{style['emoji']} {name}", value=f"{style['description']}\n💰 Цена: **{style['price']}** монет", inline=True)
        embed.set_footer(text="Используй /buy_style <название> для покупки")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy_style", description="[ТОЛЬКО НА СЕРВЕРЕ] Купить стиль ника за монеты и сразу применить.")
    @app_commands.describe(style="Название стиля (из магазина)")
    async def buy_style(self, interaction: discord.Interaction, style: str):
        if not interaction.guild:
            await interaction.response.send_message("❌ Эту команду можно использовать только на сервере!", ephemeral=True)
            return

        if style in FREE_STYLES:
            style_data = FREE_STYLES[style]
        elif style in STYLE_SHOP:
            style_data = STYLE_SHOP[style]
        else:
            available = ", ".join(list(FREE_STYLES.keys()) + list(STYLE_SHOP.keys()))
            await interaction.response.send_message(f"❌ Неизвестный стиль. Доступные: {available}", ephemeral=True)
            return

        price = style_data["price"]
        owned = get_owned_styles(interaction.user.id)
        if style in owned:
            await interaction.response.send_message(f"❌ У вас уже есть стиль **{style}**!", ephemeral=True)
            return

        coins = get_coins(interaction.user.id)
        if price > 0 and coins < price:
            await interaction.response.send_message(f"❌ Недостаточно монет! Нужно {price}, у вас {coins}", ephemeral=True)
            return

        if price > 0:
            spend_coins(interaction.user.id, price)

        add_owned_style(interaction.user.id, style)

        user_data = get_user_faceit(interaction.user.id)
        if user_data and user_data[0]:
            base_nick = user_data[0]
        else:
            base_nick = interaction.user.display_name

        new_nick = style_data["transform"](base_nick)

        try:
            await interaction.user.edit(nick=new_nick)

            c.execute('''INSERT OR REPLACE INTO user_style (user_id, style_name, equipped_at)
                         VALUES (?, ?, ?)''',
                      (interaction.user.id, style, datetime.now().isoformat()))
            conn.commit()

            embed = discord.Embed(
                title="✅ Стиль куплен и применён!",
                description=f"{style_data['emoji']} **{style}**\n{style_data['description']}",
                color=discord.Color.green()
            )
            embed.add_field(name="Новый ник", value=new_nick, inline=False)
            if price > 0:
                embed.add_field(name="💰 Потрачено", value=f"{price} монет", inline=True)
                embed.add_field(name="📊 Остаток", value=f"{get_coins(interaction.user.id)} монет", inline=True)

            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ У меня нет прав менять ваш ник! Попросите администратора дать права `Управлять никнеймами`", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)

    @app_commands.command(name="styles", description="Показать список купленных стилей и текущий активный стиль.")
    async def styles(self, interaction: discord.Interaction):
        owned = get_owned_styles(interaction.user.id)
        current_style = get_equipped_style(interaction.user.id)

        embed = discord.Embed(
            title=f"🎨 Стили {interaction.user.display_name}",
            color=discord.Color.purple()
        )

        if current_style:
            embed.add_field(name="✅ Текущий стиль", value=current_style, inline=False)

        if owned:
            styles_text = "\n".join([f"• {s}" for s in owned])
            embed.add_field(name="📦 Купленные стили", value=styles_text, inline=False)
        else:
            embed.add_field(name="📦 Купленные стили", value="Нет купленных стилей", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="reset_nick", description="[ТОЛЬКО НА СЕРВЕРЕ] Сбросить стиль ника к исходному Faceit-нику.")
    async def reset_nick(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("❌ Эту команду можно использовать только на сервере!", ephemeral=True)
            return

        user_data = get_user_faceit(interaction.user.id)
        if user_data and user_data[0]:
            base_nick = user_data[0]
        else:
            base_nick = interaction.user.display_name

        try:
            await interaction.user.edit(nick=base_nick)
            c.execute('DELETE FROM user_style WHERE user_id = ?', (interaction.user.id,))
            conn.commit()
            await interaction.response.send_message(f"✅ Ник сброшен на **{base_nick}**", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ У меня нет прав менять ваш ник!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ShopCog(bot))