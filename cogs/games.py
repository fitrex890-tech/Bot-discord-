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
            return await interaction.response
