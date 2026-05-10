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

        await interaction.response.send_message(
            f"💼 **Praca wykonana!**\n{job}\n💰 +{earn} 💎"
        )

    # =========================
    # 🎁 DAILY
    # =========================
    @app_commands.command(name="daily", description="🎁 codzienna nagroda")
    async def daily(self, interaction: discord.Interaction):

        reward = random.randint(50, 200)

        await db.update_crypto(interaction.user.id, reward)

        await interaction.response.send_message(
            f"🎁 Daily odebrane!\n💰 +{reward} 💎"
        )

    # =========================
    # 🎰 SPIN (KOŁO FORTUNY - FIX)
    # =========================
    @app_commands.command(name="spin", description="🎰 Koło fortuny")
    @app_commands.choices(level=[
        app_commands.Choice(name="Low 🟢", value="low"),
        app_commands.Choice(name="Medium 🟡", value="medium"),
        app_commands.Choice(name="Hard 🔥", value="hard"),
    ])
    async def spin(
        self,
        interaction: discord.Interaction,
        bet: int,
        level: app_commands.Choice[str]
    ):

        if bet <= 0:
            return await interaction.response.send_message("❌ Zła kwota")

        data = await db.get_profile(interaction.user.id)
        if data["crypto"] < bet:
            return await interaction.response.send_message("❌ Za mało 💎")

        await db.update_crypto(interaction.user.id, -bet)

        embed = discord.Embed(
            title="🎰 Koło fortuny się kręci...",
            description=f"Poziom: **{level.name}**\nStawka: **{bet} 💎**"
        )
        embed.set_image(url="https://media.tenor.com/your_spin.gif")

        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        await asyncio.sleep(3)

        # =========================
        # LEVEL SYSTEM
        # =========================
        if level.value == "low":
            options = [
                ("🟢", 1, "https://media.tenor.com/green.gif"),
                ("🟡", 1.5, "https://media.tenor.com/yellow.gif"),
                ("⚪", 0, "https://media.tenor.com/fail.gif"),
            ]
            weights = [50, 35, 15]

        elif level.value == "medium":
            options = [
                ("🟢", 1.2, "https://media.tenor.com/green.gif"),
                ("🔵", 2.5, "https://media.tenor.com/blue.gif"),
                ("⚪", 0, "https://media.tenor.com/fail.gif"),
            ]
            weights = [40, 40, 20]

        else:  # hard
            options = [
                ("🔵", 3, "https://media.tenor.com/blue.gif"),
                ("🟣", 6, "https://media.tenor.com/purple.gif"),
                ("⚪", 0, "https://media.tenor.com/fail.gif"),
            ]
            weights = [45, 30, 25]

        color, mult, gif = random.choices(options, weights=weights)[0]

        # =========================
        # LOSE
        # =========================
        if color == "⚪":
            await msg.edit(
                embed=discord.Embed(
                    title="💀 PRZEGRANA",
                    description=f"-{bet} 💎",
                    color=0xFFFFFF
                ).set_image(url=gif)
            )
            return

        # =========================
        # WIN
        # =========================
        win = int(bet * mult)
        await db.update_crypto(interaction.user.id, win)

        await msg.edit(
            embed=discord.Embed(
                title=f"{color} WYGRANA!",
                description=f"+{win} 💎\nMnożnik: x{mult}",
                color=0x00FF00
            ).set_image(url=gif)
        )

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

        player = random.randint(14, 23)
        dealer = random.randint(16, 24)

        if player > 21:
            player = 21
        if dealer > 21:
            dealer = 21

        if player > dealer:
            win = bet * 2
            await db.update_crypto(interaction.user.id, win)
            result = f"🎉 WYGRANA +{win} 💎"
        elif player == dealer:
            await db.update_crypto(interaction.user.id, bet)
            result = "🤝 REMIS"
        else:
            result = f"💀 PRZEGRANA -{bet} 💎"

        await interaction.response.send_message(
            f"🃏 TY: {player} | DEALER: {dealer}\n{result}"
        )

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

        result = random.choice(["💎", "💎", "💣", "💎", "💣"])

        if result == "💎":
            win = bet * 3
            await db.update_crypto(interaction.user.id, win)
            await interaction.response.send_message(f"💎 SAFE +{win} 💎")
        else:
            await interaction.response.send_message(f"💣 BOOM -{bet} 💎")

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
            await interaction.response.send_message(f"🪙 WIN +{win} 💎")
        else:
            await interaction.response.send_message(f"🪙 LOSS -{bet} 💎")


# =========================
# SETUP (RAILWAY FIX)
# =========================
async def setup(bot):
    await bot.add_cog(Games(bot))
