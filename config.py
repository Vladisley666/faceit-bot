import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), 'secure', '.env')
load_dotenv(dotenv_path)

DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
FACEIT_API_KEY = os.getenv('FACEIT_API_KEY')
STEAM_API_KEY = os.getenv('STEAM_API_KEY')

MAIN_ADMIN_IDS = [932246143520362558]

DB_VERSION = 5

FACEIT_ROLES = {
    1: "Faceit Level 1", 2: "Faceit Level 2", 3: "Faceit Level 3",
    4: "Faceit Level 4", 5: "Faceit Level 5", 6: "Faceit Level 6",
    7: "Faceit Level 7", 8: "Faceit Level 8", 9: "Faceit Level 9", 10: "Faceit Level 10"
}

AVG_KILLS_ROLES = {
    "below_10": "AVG Kills < 10", "10_11": "AVG Kills 10-11",
    "11_12": "AVG Kills 11-12", "12_13": "AVG Kills 12-13",
    "13_14": "AVG Kills 13-14", "14_15": "AVG Kills 14-15",
    "15_16": "AVG Kills 15-16", "16_17": "AVG Kills 16-17",
    "17_18": "AVG Kills 17-18", "18_19": "AVG Kills 18-19",
    "19_20": "AVG Kills 19-20", "above_20": "AVG Kills 20+"
}

KD_ROLES = {
    "below_0.9": "K/D < 0.9", "0.9_1.0": "K/D 0.9-1.0",
    "1.0_1.1": "K/D 1.0-1.1", "1.1_1.2": "K/D 1.1-1.2",
    "1.2_1.3": "K/D 1.2-1.3", "1.3_1.4": "K/D 1.3-1.4",
    "1.4_1.5": "K/D 1.4-1.5", "1.5_1.6": "K/D 1.5-1.6",
    "1.6_1.7": "K/D 1.6-1.7", "1.7_1.8": "K/D 1.7-1.8",
    "1.8_1.9": "K/D 1.8-1.9", "1.9_2.0": "K/D 1.9-2.0", "above_2": "K/D 2.0+"
}

MAP_ROLES = {
    "Mirage": "Mirage Main", "Inferno": "Inferno Main", "Dust2": "Dust2 Main",
    "Nuke": "Nuke Main", "Overpass": "Overpass Main", "Ancient": "Ancient Main",
    "Anubis": "Anubis Main", "Vertigo": "Vertigo Main"
}

def get_all_bot_roles():
    roles = []
    roles.extend(FACEIT_ROLES.values())
    roles.extend(AVG_KILLS_ROLES.values())
    roles.extend(KD_ROLES.values())
    roles.extend(MAP_ROLES.values())
    roles.append("Verified")
    roles.append("Unverified")
    roles.append("🧭 Первопроходец")
    roles.append("⚙️ Трудоголик")
    roles.append("🤝 Командный игрок")
    roles.append("📡 Мастер связей")
    roles.append("🎯 Организатор")
    roles.append("💬 Душа компании")
    roles.append("🏆 Ветеран")
    roles.append("⭐ Коллекционер")
    return roles