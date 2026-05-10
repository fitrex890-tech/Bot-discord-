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
    @app_commands.command(name="pracuj", description="💼 Idź do pracy")
    async def work(self, interaction: discord.Interaction):

        jobs = [
            "📦 Rozwoziłeś paczki",
            "🍔 Fast food worker",
            "🧑‍💻 Programista",
            "🚗 Uber driver",
            "🧹 Sprzątanie biura"
        ]

        job = random.choice(jobs)
        earn = random.randint(20, 150)

        await db.update_crypto(interaction.user.id, earn)

        await interaction.response.send_message(
            f"💼 {job}\n💰 +{earn} 💎"
        )

    # =========================
    # 🎁 DAILY
    # =========================
    @app_commands.command(name="daily", description="🎁 nagroda dzienna")
    async def daily(self, interaction: discord.Interaction):

        reward = random.randint(50, 200)

        await db.update_crypto(interaction.user.id, reward)

        await interaction.response.send_message(
            f"🎁 Daily!\n💰 +{reward} 💎"
        )

    # =========================
    # 🎰 SPIN (FIXED)
    # =========================
    @app_commands.command(name="spin", description="🎰 Koło fortuny")
    async def spin(self, interaction: discord.Interaction, bet: int):

        if bet <= 0:
            return await interaction.response.send_message("❌ Zła kwota")

        data = await db.get_profile(interaction.user.id)
        if data["crypto"] < bet:
            return await interaction.response.send_message("❌ Za mało 💎")

        await db.update_crypto(interaction.user.id, -bet)

        embed = discord.Embed(title="🎰 Kręcę kołem...")
        embed.set_image(url="https://media.giphy.com/media/3o7aD2saalBwwftBIY/giphy.gif")

        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        await asyncio.sleep(3)

        wheel = [
            ("🟢", 0.5),
            ("🟢", 1),
            ("🟡", 1.5),
            ("🔵", 3),
            ("🟣", 6),
            ("💀", 0),
        ]

        weights = [30, 25, 20, 15, 7, 3]

        color, mult = random.choices(wheel, weights=weights)[0]

        if color == "💀":
            await msg.edit(content=f"💀 PRZEGRANA -{bet} 💎")
            return

        win = int(bet * mult)
        await db.update_crypto(interaction.user.id, win)

        await msg.edit(
            content=f"{color} WYGRANA!\n💰 +{win} 💎"
        )

    # =========================
    # 🃏 BLACKJACK
    # =========================
    @app_commands.command(name="blackjack", description="🃏 blackjack")
    async def blackjack(self, interaction: discord.Interaction, bet: int):

        if bet <=
