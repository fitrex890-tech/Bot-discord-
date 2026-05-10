import discord
from discord.ext import commands
from discord import app_commands
import database as db
import utils


RANKS = [
    {"min": 0,          "max": 9_999,        "nazwa": "Żebrak",       "emoji": "🪨",  "kolor": 0x8B4513},
    {"min": 10_000,     "max": 49_999,        "nazwa": "Chłop",        "emoji": "👨‍🌾", "kolor": 0x6B8E23},
    {"min": 50_000,     "max": 124_999,       "nazwa": "Rzemieślnik",  "emoji": "⚒️",  "kolor": 0xCD853F},
    {"min": 125_000,    "max": 299_999,       "nazwa": "Mieszczanin",  "emoji": "🏘️",  "kolor": 0x4682B4},
    {"min": 300_000,    "max": 749_999,       "nazwa": "Gołota",       "emoji": "🗡️",  "kolor": 0x708090},
    {"min": 750_000,    "max": 1_499_999,     "nazwa": "Szlachcic",    "emoji": "🛡️",  "kolor": 0xC0C0C0},
    {"min": 1_500_000,  "max": 3_999_999,     "nazwa": "Rycerz",       "emoji": "⚔️",  "kolor": 0xFFD700},
    {"min": 4_000_000,  "max": 9_999_999,     "nazwa": "Możnowładca",  "emoji": "🏰",  "kolor": 0xFF8C00},
    {"min": 10_000_000, "max": 24_999_999,    "nazwa": "Hrabia",       "emoji": "🎖️",  "kolor": 0x9400D3},
    {"min": 25_000_000, "max": 74_999_999,    "nazwa": "Książę",       "emoji": "👑",  "kolor": 0x00CED1},
    {"min": 75_000_000, "max": float("inf"),  "nazwa": "Król",         "emoji": "💎",  "kolor": 0xFF1493},
]


def get_rank(total: int) -> dict:
    for rank in reversed(RANKS):
        if total >= rank["min"]:
            return rank
    return RANKS[0]


def get_next_rank(total: int) -> dict | None:
    for rank in RANKS:
        if total < rank["min"]:
            return rank
    return None


def rank_progress_bar(total: int, current: dict, next_rank: dict | None) -> str:
    if next_rank is None:
        return "█████████████████████ MAX"
    progress = (total - current["min"]) / (next_rank["min"] - current["min"])
    progress = min(max(progress, 0), 1)
    filled = int(progress * 20)
    bar = "█" * filled + "░" * (20 - filled)
    pct = int(progress * 100)
    return f"`{bar}` {pct}%"


class Ranks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ranga", description="Sprawdź swoją rangę społeczną")
    @app_commands.describe(uzytkownik="Użytkownik (opcjonalnie)")
    async def rank(self, interaction: discord.Interaction, uzytkownik: discord.Member = None):
        target = uzytkownik or interaction.user
        user = await db.get_user(target.id)
        total = user["balance"] + user["bank"]

        current = get_rank(total)
        next_r = get_next_rank(total)
        bar = rank_progress_bar(total, current, next_r)

        embed = discord.Embed(
            title=f"{current['emoji']} {current['nazwa']} — {target.display_name}",
            color=current["kolor"],
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        embed.add_field(name="💰 Majątek", value=f"**{total:,} 💎 Crypto**", inline=True)
        embed.add_field(name="🏅 Aktualna Ranga", value=f"{current['emoji']} **{current['nazwa']}**", inline=True)

        if next_r:
            brakuje = next_r["min"] - total
            embed.add_field(
                name=f"⬆️ Następna: {next_r['emoji']} {next_r['nazwa']}",
                value=f"Brakuje: **{brakuje:,} 💎**\n{bar}",
                inline=False,
            )
        else:
            embed.add_field(
                name="👑 Szczyt Hierarchii!",
                value="Osiągnąłeś najwyższą rangę — **Król**!\n`████████████████████` MAX",
                inline=False,
            )

        embed.set_footer(text="Crypto Casino | /rangi — pełna lista rang")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rangi", description="Lista wszystkich rang i wymagań")
    async def rank_list(self, interaction: discord.Interaction):
        user = await db.get_user(interaction.user.id)
        total = user["balance"] + user["bank"]
        current = get_rank(total)

        embed = discord.Embed(
            title="👑 System Rang — Crypto Casino",
            description="Twój majątek = kieszeń + bank. Im więcej masz, tym wyższa ranga!\n\n",
            color=utils.JACKPOT_COLOR,
        )

        lines = []
        for rank in RANKS:
            is_current = rank["nazwa"] == current["nazwa"]
            marker = " ◄ **TY**" if is_current else ""
            if rank["max"] == float("inf"):
                prog = f"{rank['min']:,}+"
            else:
                prog = f"{rank['min']:,} – {rank['max']:,}"
            lines.append(
                f"{rank['emoji']} **{rank['nazwa']}**{marker}\n"
                f"╰ 💎 {prog} Crypto"
            )

        embed.description += "\n\n".join(lines)
        embed.set_footer(text="Użyj /ranga aby zobaczyć swój postęp")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Ranks(bot))
