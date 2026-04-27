import aiohttp
import asyncio
from config import FACEIT_API_KEY

async def get_faceit_data(nickname, retries=3):
    nickname = nickname.strip()
    headers = {"Authorization": f"Bearer {FACEIT_API_KEY}", "Accept": "application/json"}
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://open.faceit.com/data/v4/players?nickname={nickname}&game=cs2"
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        return await resp.json(), None
                    elif resp.status == 404:
                        alt_url = f"https://open.faceit.com/data/v4/players?nickname={nickname}"
                        async with session.get(alt_url, headers=headers) as alt_resp:
                            if alt_resp.status == 200:
                                return await alt_resp.json(), None
                            else:
                                return None, f"❌ Игрок {nickname} не найден"
                    else:
                        return None, f"❌ Ошибка Faceit API: {resp.status}"
        except asyncio.TimeoutError:
            if attempt < retries - 1:
                await asyncio.sleep(3)
                continue
            return None, "❌ Таймаут"
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(3)
                continue
            return None, f"❌ Ошибка: {e}"
    return None, "❌ Не удалось подключиться"

async def get_player_detailed_stats(nickname):
    data, error = await get_faceit_data(nickname)
    if error:
        return None, error
    player_id = data['player_id']
    player_level = data['games']['cs2']['skill_level']
    player_elo = data['games']['cs2']['faceit_elo']
    headers = {"Authorization": f"Bearer {FACEIT_API_KEY}", "Accept": "application/json"}
    async with aiohttp.ClientSession() as session:
        stats_url = f"https://open.faceit.com/data/v4/players/{player_id}/stats/cs2"
        async with session.get(stats_url, headers=headers) as stats_resp:
            if stats_resp.status != 200:
                return None, "❌ Не удалось получить статистику"
            stats_data = await stats_resp.json()
            map_stats_all = {}
            for segment in stats_data.get('segments', []):
                if segment.get('type') == 'Map':
                    map_name = segment.get('label', 'Unknown')
                    matches = int(segment.get('stats', {}).get('Matches', 0))
                    if map_name != 'Unknown' and matches > 0:
                        map_stats_all[map_name] = matches
            favorite_map = max(map_stats_all.items(), key=lambda x: x[1])[0] if map_stats_all else "Нет данных"
            history_url = f"https://open.faceit.com/data/v4/players/{player_id}/history?game=cs2&limit=30"
            async with session.get(history_url, headers=headers) as history_resp:
                if history_resp.status != 200:
                    return {
                        "nickname": nickname, "level": player_level, "elo": player_elo, "player_id": player_id,
                        "avg_kills": 0, "kd": 0, "win_percentage": 0, "favorite_map": favorite_map, "matches_count": 0
                    }, None
                history_data = await history_resp.json()
                total_kills = total_deaths = matches_count = wins = 0
                for match in history_data.get('items', []):
                    match_stats_url = f"https://open.faceit.com/data/v4/matches/{match['match_id']}/stats"
                    async with session.get(match_stats_url, headers=headers) as match_resp:
                        if match_resp.status == 200:
                            match_data = await match_resp.json()
                            for round_data in match_data.get('rounds', []):
                                for team in round_data.get('teams', []):
                                    for player_stat in team.get('players', []):
                                        if player_stat['player_id'] == player_id:
                                            kills = int(player_stat['player_stats'].get('Kills', 0))
                                            deaths = int(player_stat['player_stats'].get('Deaths', 0))
                                            total_kills += kills
                                            total_deaths += deaths
                                            matches_count += 1
                                            result = player_stat['player_stats'].get('Result')
                                            if result is not None and str(result) in ["1","True","Yes"]:
                                                wins += 1
                                            else:
                                                winner = player_stat['player_stats'].get('Winner')
                                                if winner is not None and str(winner) in ["1","True","Yes"]:
                                                    wins += 1
                                            break
                avg_kills = round(total_kills / matches_count, 1) if matches_count else 0
                kd = round(total_kills / total_deaths, 2) if total_deaths else 0
                win_percentage = round((wins / matches_count) * 100, 1) if matches_count else 0
                return {
                    "nickname": nickname, "level": player_level, "elo": player_elo, "player_id": player_id,
                    "avg_kills": avg_kills, "kd": kd, "win_percentage": win_percentage,
                    "favorite_map": favorite_map, "matches_count": matches_count,
                    "total_kills": total_kills, "total_deaths": total_deaths, "wins": wins
                }, None