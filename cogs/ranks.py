import discord
from discord.ext import commands
from discord import app_commands
import database as db
import utils


RANKS = [
    {"min": 0,          "max": 9_999,        "nazwa": "Żebrak",       "emoji": "🪨",  "kolor": 0x8B4513},
    {"min": 10_000,     "max": 49_999,       "nazwa": "Chłop",        "emoji": "👨‍🌾", "kolor": 0x6B8E23},
    {"min": 50_000,     "max": 124_999,      "nazwa": "Rzemieślnik",  "emoji": "⚒️",  "kolor": 0xCD853F},
    {"min": 125_000,    "max": 299_999,      "nazwa": "Mieszczanin",  "emoji": "🏘️",  "kolor": 0x4682B4},
    {"min": 300_000,    "max": 749_999,      "nazwa": "Gołota",       "emoji": "🗡️",  "kolor": 0x708090},
    {"min": 750_000,    "max": 1_499_999,    "nazwa": "Szlachcic",    "emoji": "🛡️",  "kolor": 0xC0C0C0},
    {"min": 1_500_000,  "max": 3_999_999,    "nazwa": "Rycerz",       "emoji": "⚔️",  "kolor": 0xFFD700},
    {"min": 4_000_000,  "max": 9_999_999,    "nazwa": "Możnowładca",  "emoji": "🏰",  "kolor": 0xFF8C00},
    {"min": 10_000_000, "max": 24_999_999,   "nazwa": "Hrabia",       "emoji": "🎖️",  "kolor": 0x9400D3},
    {"min": 25_000_000, "max": 74_999_999,   "nazwa": "Książę",       "emoji": "👑",  "kolor": 0x00CED1},
    {"min": 75_000_000, "max": float("inf"), "nazwa": "Król",         "emoji": "💎",  "kolor": 0xFF1493},
]


def get_rank(total: int):
    for rank in RANKS:
        if total >= rank["min"]:
            current = rank
    return current


def get_next_rank(total: int):
    for rank in RANKS:
        if total < rank["min"]:
            return rank
    return None


def rank_progress_bar(total: int, current: dict, next_rank: dict | None):
    if not next_rank:
        return "████████████████████ MAX"

    progress = (total - current["min"]) / (next_rank["min"] - current["min"])
    progress = max(0, min(progress, 1))

    filled = int(progress * 20)
    bar = "█" * filled + "░" * (20 - filled)

    return f"`{bar}` {int(progress * 100)}%"


class Ranks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # 👤 RANGA
    # =========================
    @app_commands.command(name="ranga", description="👑 Twoja ranga")
    async def rank(self, interaction: discord.Interaction, uzytkownik: discord.Member = None):

        target = uzytkownik or interaction.user

        data = await db.get_profile(target.id)

        crypto = data.get("crypto", 0)
        bank_crypto =
