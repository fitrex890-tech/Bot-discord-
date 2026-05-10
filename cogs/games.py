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
    # 💼 WORK (ZARABIANIE)
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
            f"💼 **Praca wykonana!**\n"
            f"{job}\n\n"
            f"💰 Zarobek: **+{earn} 💎 Crypto**"
        )

    # =========================
    # 🎁 DAILY
    # =========================
    @app_commands.command(name="daily", description="🎁 codzienna nagroda")
    async def daily(self, interaction: discord.Interaction):

        reward = random.randint(50, 200)

        await db.update_crypto(interaction.user.id, reward)

        await interaction.response.send_message(
            f"🎁 **Daily odebrane!**\n"
            f"💰 +{reward} 💎 Crypto"
        )

    # =========================
    # 🎰 SPIN (GIF + KOŁO)
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

        msg = await interaction.response.send_message(embed=embed)
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
            await msg.edit_original_response(
                content=f"💀 KOŁO: pech!\n❌ Strata: -{bet} 💎",
                embed=None
            )
            return

        win = int(bet * mult)
        await db.update_crypto(interaction.user.id, win)

        await msg.edit_original_response(
            content=(
                f"{color} KOŁO: wynik!\n"
                f"💰 Wygrana: +{win} 💎\n"
                f"📊 Stawka: {bet}"
            ),
            embed=None
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
            reward = bet * 2
            await db.update_crypto(interaction.user.id, reward)

            result = f"🎉 WYGRANA!\n💰 +{reward} 💎\n📊 Lepsza ręka"
        elif player == dealer:
            await db.update_crypto(interaction.user.id, bet)
            result = "🤝 REMIS – zwrot betu"
        else:
            result = f"💀 PRZEGRANA -{bet} 💎\nDealer wygrał"

        await interaction.response.send_message(
            f"🃏 TY: {player} | DEALER: {dealer}\n\n{result}"
        )

    # =========================
    # 💣
