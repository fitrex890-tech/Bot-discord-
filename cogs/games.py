import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import database as db


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # 💼 WORK
    # =========================
    @app_commands.command(name="pracuj", description="💼 Idź do pracy i zarób")
    async def work(self, interaction: discord.Interaction):

        jobs = [
            "📦 Rozwoziłeś paczki",
            "🍔 Pracowałeś w fast foodzie",
            "🧑‍💻 Programowałeś systemy",
            "🚗 Jeździłeś Uberem",
            "🧹 Sprzątałeś biuro"
        ]

        job = random.choice(jobs)
        earn = random.randint(20, 150)

        await db.update_crypto(interaction.user.id, earn)

        embed = discord.Embed(
            title="💼 Praca wykonana!",
            description=f"{job}\n\n💰 Zarobek: **+{earn} 💎**",
            color=0x2ECC71
        )

        await interaction.response.send_message(embed=embed)

    # =========================
    # 🎁 DAILY
    # =========================
    @app_commands.command(name="daily", description="🎁 codzienna nagroda")
    async def daily(self, interaction: discord.Interaction):

        reward = random.randint(50, 200)
        await db.update_crypto(interaction.user.id, reward)

        embed = discord.Embed(
            title="🎁 Daily!",
            description=f"Odebrane!\n💰 +{reward} 💎",
            color=0xF1C40F
        )

        await interaction.response.send_message(embed=embed)

    # =========================
    # 🎰 SPIN (CASINO + LEVELS + GIF)
    # =========================
    @app_commands.command(name="spin", description="🎰 Koło fortuny")
    @app_commands.choices(level=[
        app_commands.Choice(name="Low 🟢", value="low"),
        app_commands.Choice(name="Medium 🟡", value="medium"),
        app_commands.Choice(name="Hard 🔴", value="hard"),
    ])
    async def spin(self, interaction: discord.Interaction, bet: int, level: app_commands.Choice[str]):

        if bet <= 0:
            return await interaction.response.send_message("❌ Zła kwota")

        data = await db.get_profile(interaction.user.id)

        if data["crypto"] < bet:
            return await interaction.response.send_message("❌ Za mało 💎")

        await db.update_crypto(interaction.user.id, -bet)

        # START EMBED (animacja)
        start = discord.Embed(
            title="🎰 Koło Fortuny",
            description="Kręcę kołem...",
            color=0xF1C40F
        )
        start.set_image(url="https://media.giphy.com/media/3o7aD2saalBwwftBIY/giphy.gif")

        await interaction.response.send_message(embed=start)
        msg = await interaction.original_response()

        await asyncio.sleep(3)

        wheel = [
            ("🟢", 0.5),
            ("🟢", 1),
            ("🟡", 1.5),
            ("🔵", 3),
            ("🟣", 6),
            ("⚪", 0),
        ]

        if level.value == "low":
            weights = [35, 30, 20, 10, 4, 1]
        elif level.value == "medium":
            weights = [25, 25, 25, 15, 8, 2]
        else:
            weights = [15, 20, 25, 20, 15, 5]

        color, mult = random.choices(wheel, weights=weights)[0]

        # =========================
        # RESULT
        # =========================
        if color == "⚪":
            embed = discord.Embed(
                title="💀 Przegrana!",
                description=f"Straciłeś **-{bet} 💎**",
                color=0x2C3E50
            )
        else:
            win = int(bet * mult)
            await db.update_crypto(interaction.user.id, win)

            embed = discord.Embed(
                title=f"{color} Wygrana!",
                description=f"Zarobek: **+{win} 💎**",
                color=0x2ECC71
            )

        embed.set_footer(text=f"Stawka: {bet} 💎 | Tryb: {level.value}")

        await msg.edit(embed=embed)

    # =========================
    # 🃏 BLACKJACK
    # =========================
    @app_commands.command(name="blackjack", description="🃏 Blackjack")
    async def blackjack(self, interaction: discord.Interaction, bet: int):

        if bet <= 0:
            return await interaction.response.send_message("❌ Zła kwota")

        data = await db.get_profile(interaction.user.id)

        if data["crypto"] < bet:
            return await interaction.response.send_message("❌ Za mało 💎")

        await db.update_crypto(interaction.user.id, -bet)

        player = random.randint(12, 23)
        dealer = random.randint(14, 24)

        if player > 21:
            player = 21
        if dealer > 21:
            dealer = 21

        if player > dealer:
            win = bet * 2
            await db.update_crypto(interaction.user.id, win)
            result = f"🎉 WYGRANA +{win} 💎"
            color = 0x2ECC71
        elif player == dealer:
            await db.update_crypto(interaction.user.id, bet)
            result = "🤝 REMIS"
            color = 0xF1C40F
        else:
            result = f"💀 PRZEGRANA -{bet} 💎"
            color = 0xE74C3C

        embed = discord.Embed(
            title="🃏 Blackjack",
            description=f"Ty: **{player}** | Dealer: **{dealer}**\n\n{result}",
            color=color
        )

        await interaction.response.send_message(embed=embed)

    # =========================
    # 💣 MINES
    # =========================
    @app_commands.command(name="mines", description="💣 Mines")
    async def mines(self, interaction: discord.Interaction, bet: int):

        if bet <= 0:
            return await interaction.response.send_message("❌ Zła kwota")

        data = await db.get_profile(interaction.user.id)

        if data["crypto"] < bet:
            return await interaction.response.send_message("❌ Za mało 💎")

        await db.update_crypto(interaction.user.id, -bet)

        field = random.choice(["💎", "💎", "💣", "💎", "💣"])

        if field == "💎":
            win = bet * 3
            await db.update_crypto(interaction.user.id, win)

            embed = discord.Embed(
                title="💎 SAFE!",
                description=f"Wygrana: **+{win} 💎**",
                color=0x2ECC71
            )
        else:
            embed = discord.Embed(
                title="💣 BOOM!",
                description=f"Strata: **-{bet} 💎**",
                color=0xE74C3C
            )

        await interaction.response.send_message(embed=embed)

    # =========================
    # 🪙 COINFLIP
    # =========================
    @app_commands.command(name="coinflip", description="🪙 orzeł/reszka")
    async def coinflip(self, interaction: discord.Interaction, bet: int):

        if bet <= 0:
            return await interaction.response.send_message("❌ Zła kwota")

        data = await db.get_profile(interaction.user.id)

        if data["crypto"] < bet:
            return await interaction.response.send_message("❌ Za mało 💎")

        await db.update_crypto(interaction.user.id, -bet)

        user = random.choice(["heads", "tails"])
        result = random.choice(["heads", "tails"])

        if user == result:
            win = bet * 2
            await db.update_crypto(interaction.user.id, win)

            embed = discord.Embed(
                title="🪙 WIN!",
                description=f"+{win} 💎",
                color=0x2ECC71
            )
        else:
            embed = discord.Embed(
                title="🪙 LOSS!",
                description=f"-{bet} 💎",
                color=0xE74C3C
            )

        await interaction.response.send_message(embed=embed)


# =========================
# SETUP (RAILWAY FIX)
# =========================
async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))
