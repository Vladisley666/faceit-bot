import aiohttp
from config import STEAM_API_KEY

async def check_steam_summary(steam_id, expected_code):
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steam_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    return False, "Не удалось подключиться к Steam API"
                data = await resp.json()
                players = data.get('response', {}).get('players', [])
                if not players:
                    return False, "Steam профиль не найден"
                player = players[0]
                realname = player.get('realname', '')
                if expected_code and expected_code in realname:
                    return True, None
                elif not expected_code:
                    return True, None
                else:
                    return False, f"Код `{expected_code}` не найден в поле Real Name. Сейчас там: **{realname if realname else 'пусто'}**"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"