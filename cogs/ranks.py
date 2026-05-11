import discord
from discord.ext import commands
from discord import app_commands
import database as db
import utils

# =========================
# RANGI
# =========================
RANKS = [
    {"min": 0,          "max": 9_999,       "nazwa": "Żebrak",       "emoji": "🪨", "kolor": 0x8B4513},
    {"min": 10_000,     "max": 49_999,      "nazwa": "Chłop",        "emoji": "👨‍🌾", "kolor": 0x6B8E23},
    {"min": 50_000,     "max": 124_999,     "nazwa": "Rzemieślnik",  "emoji": "⚒️",  "kolor": 0xCD853F},
    {"min": 125_000,    "max": 299_999,     "nazwa": "Mieszczanin",  "emoji": "🏘️",  "kolor": 0x4682B4},
    {"min": 300_000,    "max": 749_999,     "nazwa": "Gołota",       "emoji": "🗡️",  "kolor": 0x708090},
    {"min": 750_000,    "max": 1_499_999,   "nazwa": "Szlachcic",    "emoji": "🛡️",  "kolor": 0xC0C0C0},
    {"min": 1_500_000,  "max": 3_999_999,   "nazwa": "Rycerz",       "emoji": "⚔️",  "kolor": 0xFFD700},
    {"min": 4_000_000,  "max": 9_999_999,   "nazwa": "Możnowładca",  "emoji": "🏰",  "kolor": 0xFF8C00},
    {"min": 10_000_000, "max": 24_999_999,  "nazwa": "Hrabia",       "emoji": "🎖️",  "kolor": 0x9400D3},
    {"min": 25_000_000, "max": 74_999_999,  "nazwa": "Książę",       "emoji": "👑",  "kolor": 0x00CED1},
    {"min": 75_000_000, "max": float("inf"),"nazwa": "Król",         "emoji": "💎",  "kolor": 0xFF1493},
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


def progress_bar(total: int, current: dict, next_rank: dict | None) -> str:
    if not next_rank:
        return "█" * 20 + "  MAX 👑"
    progress = (total - current["min"]) / (next_rank["min"] - current["min"])
    progress = max(0.0, min(1.0, progress))
    filled = int(progress * 20)
    pct = int(progress * 100)
    return f"{'█' * filled}{'░' * (20 - filled)}  {pct}%"


# =========================
# RANK-UP CHECK
# Wywołuj po każdej zmianie salda jeśli chcesz powiadomień
# =========================
async def check_rank_up(member: discord.Member, old_total: int, new_total: int):
    """Wysyła DM jeśli gracz awansował na wyższą rangę."""
    old_rank = get_rank(old_total)
    new_rank = get_rank(new_total)
    if new_rank["nazwa"] != old_rank["nazwa"]:
        try:
            embed = utils.make_embed(
                title=f"🎉 Awans! {new_rank['emoji']} {new_rank['nazwa']}",
                description=(
                    f"Gratulacje **{member.display_name}**!\n\n"
                    f"Awansowałeś z **{old_rank['emoji']} {old_rank['nazwa']}** "
                    f"na **{new_rank['emoji']} {new_rank['nazwa']}**!\n\n"
                    f"Wymagany majątek: **{new_rank['min']:,} 💎**"
                ),
                color=new_rank["kolor"],
            )
            await member.send(embed=embed)
        except Exception:
            pass  # DM wyłączone


# =========================
# COG
# =========================
class Ranks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =========================
    # /ranga
    # =========================
    @app_commands.command(name="ranga", description="👑 Sprawdź swoją rangę ekonomiczną")
    @app_commands.describe(user="Użytkownik (opcjonalnie)")
    async def rank(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user
        data = await db.get_profile(user.id)

        total = data.get("crypto", 0) + data.get("bank_crypto", 0)
        current = get_rank(total)
        next_r = get_next_rank(total)

        embed = discord.Embed(
            title=f"{current['emoji']} {current['nazwa']}",
            description=f"Profil rankingowy gracza **{user.display_name}**",
            color=current["kolor"],
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        embed.add_field(name="💰 Majątek (portfel+bank)", value=f"**{total:,} 💎**", inline=True)
        embed.add_field(name="🏅 Ranga", value=f"{current['emoji']} **{current['nazwa']}**", inline=True)
        embed.add_field(name="🏆 Wygrane", value=str(data.get("wins", 0)), inline=True)

        if next_r:
            need = next_r["min"] - total
            embed.add_field(
                name=f"⬆️ Następna: {next_r['emoji']} {next_r['nazwa']}",
                value=(
                    f"`{progress_bar(total, current, next_r)}`\n"
                    f"Brakuje: **{need:,} 💎**"
                ),
                inline=False,
            )
        else:
            embed.add_field(name="👑 MAKSYMALNA RANGA", value="Osiągnąłeś szczyt bogactwa!", inline=False)

        embed.set_footer(text=f"Zakres rangi: {current['min']:,} — {'∞' if current['max'] == float('inf') else f\"{current['max']:,}\"} 💎")
        await interaction.response.send_message(embed=embed)

    # =========================
    # /rangi — lista wszystkich rang
    # =========================
    @app_commands.command(name="rangi", description="📜 Lista wszystkich rang")
    async def rank_list(self, interaction: discord.Interaction):
        data = await db.get_profile(interaction.user.id)
        total = data.get("crypto", 0) + data.get("bank_crypto", 0)
        current = get_rank(total)

        embed = discord.Embed(
            title="👑 System Rang — Crypto Casino",
            description="Im wyższy majątek (portfel + bank), tym wyższa ranga!\n",
            color=utils.JACKPOT_COLOR,
        )

        lines = []
        for r in RANKS:
            you = " ◄ **TY**" if r["nazwa"] == current["nazwa"] else ""
            if r["max"] == float("inf"):
                rng = f"{r['min']:,}+ 💎"
            else:
                rng = f"{r['min']:,} — {r['max']:,} 💎"
            lines.append(f"{r['emoji']} **{r['nazwa']}**{you}\n╰ {rng}")

        embed.description += "\n\n".join(lines)
        embed.set_footer(text=f"Twoja ranga: {current['emoji']} {current['nazwa']} • Majątek: {total:,} 💎")
        await interaction.response.send_message(embed=embed)

    # =========================
    # /top — ranking graczy
    # =========================
    @app_commands.command(name="top", description="🏆 Ranking najbogatszych graczy")
    async def top(self, interaction: discord.Interaction):
        await interaction.response.defer()

        rows = await db.get_leaderboard(10)
        if not rows:
            return await interaction.followup.send(
                embed=utils.make_embed("🏆 Ranking", "Brak danych!", utils.NEUTRAL_COLOR)
            )

        embed = discord.Embed(
            title="🏆 Top 10 — Ranking Ekonomiczny",
            color=utils.JACKPOT_COLOR,
        )

        medals = {0: "🥇", 1: "🥈", 2: "🥉"}
        lines = []

        for i, row in enumerate(rows):
            medal = medals.get(i, f"`#{i+1}`")
            try:
                member = interaction.guild.get_member(row["user_id"])
                name = member.display_name if member else f"Użytkownik #{row['user_id']}"
            except Exception:
                name = f"Użytkownik #{row['user_id']}"

            rank = get_rank(row["total"])
            # VIP — złoty kolor (tylko tekst, Discord nie obsługuje per-line kolorów)
            lines.append(
                f"{medal} **{name}** {rank['emoji']}\n"
                f"╰ 💎 {row['total']:,} • {rank['nazwa']}"
            )

        embed.description = "\n\n".join(lines)
        embed.set_footer(text="Majątek = portfel + bank 💎")
        await interaction.followup.send(embed=embed)

    # =========================
    # /top-rangi — ilu graczy na każdej randze
    # =========================
    @app_commands.command(name="toprangi", description="📊 Rozkład graczy według rang")
    async def top_ranks(self, interaction: discord.Interaction):
        await interaction.response.defer()

        rows = await db.get_leaderboard(1000)

        rank_counts: dict[str, int] = {r["nazwa"]: 0 for r in RANKS}
        for row in rows:
            r = get_rank(row["total"])
            rank_counts[r["nazwa"]] += 1

        embed = discord.Embed(
            title="📊 Rozkład Rang",
            description=f"Łącznie graczy: **{len(rows)}**\n",
            color=utils.INFO_COLOR,
        )

        for r in reversed(RANKS):
            count = rank_counts.get(r["nazwa"], 0)
            bar = "█" * min(count, 20) if count > 0 else "░"
            embed.add_field(
                name=f"{r['emoji']} {r['nazwa']}",
                value=f"`{bar}` **{count}** graczy",
                inline=False,
            )

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Ranks(bot))

