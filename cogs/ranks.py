import discord
from discord.ext import commands
from discord import app_commands
import database as db
import utils


# =========================
# 👑 RANK SYSTEM
# =========================
RANKS = [
    {"min": 0, "max": 9_999, "nazwa": "Żebrak", "emoji": "🪨", "kolor": 0x8B4513},
    {"min": 10_000, "max": 49_999, "nazwa": "Chłop", "emoji": "👨‍🌾", "kolor": 0x6B8E23},
    {"min": 50_000, "max": 124_999, "nazwa": "Rzemieślnik", "emoji": "⚒️", "kolor": 0xCD853F},
    {"min": 125_000, "max": 299_999, "nazwa": "Mieszczanin", "emoji": "🏘️", "kolor": 0x4682B4},
    {"min": 300_000, "max": 749_999, "nazwa": "Gołota", "emoji": "🗡️", "kolor": 0x708090},
    {"min": 750_000, "max": 1_499_999, "nazwa": "Szlachcic", "emoji": "🛡️", "kolor": 0xC0C0C0},
    {"min": 1_500_000, "max": 3_999_999, "nazwa": "Rycerz", "emoji": "⚔️", "kolor": 0xFFD700},
    {"min": 4_000_000, "max": 9_999_999, "nazwa": "Możnowładca", "emoji": "🏰", "kolor": 0xFF8C00},
    {"min": 10_000_000, "max": 24_999_999, "nazwa": "Hrabia", "emoji": "🎖️", "kolor": 0x9400D3},
    {"min": 25_000_000, "max": 74_999_999, "nazwa": "Książę", "emoji": "👑", "kolor": 0x00CED1},
    {"min": 75_000_000, "max": float("inf"), "nazwa": "Król", "emoji": "💎", "kolor": 0xFF1493},
]


def get_rank(total: int):
    for rank in reversed(RANKS):
        if total >= rank["min"]:
            return rank
    return RANKS[0]


def get_next_rank(total: int):
    for rank in RANKS:
        if total < rank["min"]:
            return rank
    return None


def bar(total: int, current: dict, next_rank: dict | None):
    if not next_rank:
        return "████████████████████ MAX"

    progress = (total - current["min"]) / (next_rank["min"] - current["min"])
    progress = max(0, min(1, progress))

    filled = int(progress * 20)
    return "█" * filled + "░" * (20 - filled)


class Ranks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =========================
    # 👤 /ranga
    # =========================
    @app_commands.command(name="ranga", description="👑 Sprawdź swoją rangę")
    async def rank(self, interaction: discord.Interaction, user: discord.Member = None):

        user = user or interaction.user
        data = await db.get_profile(user.id)

        total = data["crypto"] + data["bank_crypto"]

        current = get_rank(total)
        next_r = get_next_rank(total)

        embed = discord.Embed(
            title=f"{current['emoji']} {current['nazwa']} — {user.display_name}",
            color=current["kolor"]
        )

        embed.set_thumbnail(url=user.display_avatar.url)

        embed.add_field(
            name="💰 Majątek",
            value=f"**{total:,} 💎**",
            inline=True
        )

        embed.add_field(
            name="🏅 Ranga",
            value=f"{current['emoji']} {current['nazwa']}",
            inline=True
        )

        if next_r:
            need = next_r["min"] - total

            embed.add_field(
                name=f"⬆️ Następna: {next_r['emoji']} {next_r['nazwa']}",
                value=f"Brakuje: **{need:,} 💎**\n`{bar(total, current, next_r)}`",
                inline=False
            )
        else:
            embed.add_field(
                name="👑 MAX RANGA",
                value="Masz najwyższą rangę!",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    # =========================
    # 📜 /rangi
    # =========================
    @app_commands.command(name="rangi", description="📜 Lista rang")
    async def rank_list(self, interaction: discord.Interaction):

        data = await db.get_profile(interaction.user.id)
        total = data["crypto"] + data["bank_crypto"]
        current = get_rank(total)

        embed = discord.Embed(
            title="👑 System Rang",
            description="Im więcej masz 💎 tym wyższa ranga!\n\n",
            color=utils.JACKPOT_COLOR if hasattr(utils, "JACKPOT_COLOR") else 0xFFD700
        )

        text = ""
        for r in RANKS:
            mark = " ◄ TY" if r["nazwa"] == current["nazwa"] else ""

            if r["max"] == float("inf"):
                rng = f"{r['min']:,}+"
            else:
                rng = f"{r['min']:,} - {r['max']:,}"

            text += f"{r['emoji']} **{r['nazwa']}**{mark}\n╰ 💎 {rng}\n\n"

        embed.description += text
        await interaction.response.send_message(embed=embed)


# =========================
# SETUP (RAILWAY FIX)
# =========================
async def setup(bot: commands.Bot):
    await bot.add_cog(Ranks(bot))
