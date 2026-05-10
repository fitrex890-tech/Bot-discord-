import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio

import database as db


class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =========================
    # 💰 HELPERS
    # =========================
    async def check_balance(self, user_id, amount):
        bal = await db.get_crypto(user_id)
        return bal >= amount

    # =========================
    # 🎰 SLOTS
    # =========================
    @app_commands.command(name="slots")
    async def slots(self, interaction: discord.Interaction, bet: int):

        if bet <= 0:
            return await interaction.response.send_message("❌ zła stawka")

        if not await self.check_balance(interaction.user.id, bet):
            return await interaction.response.send_message("❌ brak środków")

        await db.update_crypto(interaction.user.id, -bet)

        embed = discord.Embed(title="🎰 Kręcenie...")
        embed.set_image(url="https://media.tenor.com/slot-spin.gif")

        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        await asyncio.sleep(2)

        symbols = ["🍒", "🍋", "🔔", "💎", "7️⃣"]

        win = random.randint(1, 100) <= 25

        if win:
            symbol = random.choice(symbols)
            result = [symbol, symbol, symbol]
            payout = bet * 5

            await db.update_crypto(interaction.user.id, payout)
            await db.add_win(interaction.user.id)

            outcome = f"🏆 WIN +{payout}"
        else:
            result = [random.choice(symbols) for _ in range(3)]
            outcome = "❌ LOSE"

        for _ in range(4):
            temp = [random.choice(symbols) for _ in range(3)]
            await msg.edit(content=f"🎰 {' | '.join(temp)}")
            await asyncio.sleep(0.5)

        await msg.edit(content=f"🎰 {' | '.join(result)}\n{outcome}")

    # =========================
    # 🃏 BLACKJACK
    # =========================
    def draw(self):
        return random.choice([2,3,4,5,6,7,8,9,10,10,10,11])

    def score(self, hand):
        return sum(hand)

    @app_commands.command(name="blackjack")
    async def blackjack(self, interaction: discord.Interaction, bet: int):

        if not await self.check_balance(interaction.user.id, bet):
            return await interaction.response.send_message("❌ brak środków")

        await db.update_crypto(interaction.user.id, -bet)

        player = [self.draw(), self.draw()]
        dealer = [self.draw(), self.draw()]

        while self.score(player) < 16:
            player.append(self.draw())

        while self.score(dealer) < 17:
            dealer.append(self.draw())

        p = self.score(player)
        d = self.score(dealer)

        if p > 21:
            result = "❌ Bust"
        elif d > 21 or p > d:
            payout = bet * 2
            await db.update_crypto(interaction.user.id, payout)
            await db.add_win(interaction.user.id)
            result = f"🏆 WIN +{payout}"
        elif p == d:
            await db.update_crypto(interaction.user.id, bet)
            result = "🤝 Return"
        else:
            result = "❌ Lose"

        await interaction.response.send_message(
            f"🃏 Ty: {player}={p}\nDealer: {dealer}={d}\n\n{result}"
        )

    # =========================
    # 🎡 ROULETTE
    # =========================
    @app_commands.command(name="roulette")
    async def roulette(self, interaction: discord.Interaction, bet: int, color: str):

        await db.update_crypto(interaction.user.id, -bet)

        colors = ["red", "black", "green"]
        result = random.choice(colors)

        win = (color == result)

        if win:
            payout = bet * (10 if result == "green" else 2)
            await db.update_crypto(interaction.user.id, payout)
            await db.add_win(interaction.user.id)
            outcome = f"🏆 WIN +{payout}"
        else:
            outcome = "❌ LOSE"

        await interaction.response.send_message(f"🎡 {result}\n{outcome}")

    # =========================
    # 💣 MINES
    # =========================
    @app_commands.command(name="mines")
    async def mines(self, interaction: discord.Interaction, bet: int):

        await db.update_crypto(interaction.user.id, -bet)

        grid = ["💣", "💎", "💎", "💎", "💣"]
        random.shuffle(grid)

        pick = random.choice(grid)

        if pick == "💎":
            payout = bet * 3
            await db.update_crypto(interaction.user.id, payout)
            await db.add_win(interaction.user.id)
            await interaction.response.send_message(f"💎 WIN +{payout}")
        else:
            await interaction.response.send_message("💥 BOOM")

    # =========================
    # 🏦 ROB
    # =========================
    @app_commands.command(name="rob")
    async def rob(self, interaction: discord.Interaction, user: discord.Member):

        if random.randint(1, 100) < 45:
            amount = random.randint(100, 500)

            await db.update_crypto(user.id, -amount)
            await db.update_crypto(interaction.user.id, amount)

            await interaction.response.send_message(f"🟢 +{amount} 💎")
        else:
            await interaction.response.send_message("🔴 failed")

    # =========================
    # 📈 INVEST
    # =========================
    prices = {}

    @app_commands.command(name="invest")
    async def invest(self, interaction: discord.Interaction):

        uid = interaction.user.id

        price = self.prices.get(uid, 100)
        change = random.randint(-40, 60)

        new_price = max(10, price + change)
        self.prices[uid] = new_price

        await interaction.response.send_message(
            f"📈 Cena: {new_price} 💎\n{'📈 UP' if change > 0 else '📉 DOWN'}"
        )

    # =========================
    # 👤 PROFILE
    # =========================
    @app_commands.command(name="profile")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):

        user = user or interaction.user

        crypto, pln, wins = await db.get_profile(user.id)

        embed = discord.Embed(title=f"👤 Profil {user.name}")

        embed.add_field(name="💎 Crypto", value=crypto, inline=False)
        embed.add_field(name="🇵🇱 PLN", value=f"{pln} zł", inline=False)
        embed.add_field(name="🏆 Wygrane", value=wins, inline=False)

        await interaction.response.send_message(embed=embed)

    # =========================
    # 🏆 LEADERBOARD
    # =========================
    @app_commands.command(name="leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):

        users = await db.get_all_users_crypto()

        top = sorted(users, key=lambda x: x["crypto"], reverse=True)[:10]

        text = ""
        for i, u in enumerate(top, 1):
            text += f"{i}. <@{u['id']}> - {u['crypto']} 💎\n"

        embed = discord.Embed(title="🏆 TOP GRACZE", description=text)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))
