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
    # 💰 helper: check balance
    # =========================
    async def check_balance(self, user_id, amount):
        bal = await db.get_crypto(user_id)
        return bal >= amount

    # =========================
    # 🎰 SLOTS (BET + PAYOUT)
    # =========================
    @app_commands.command(name="slots", description="🎰 Sloty")
    async def slots(self, interaction: discord.Interaction, bet: int):

        if bet <= 0:
            return await interaction.response.send_message("❌ zła stawka")

        if not await self.check_balance(interaction.user.id, bet):
            return await interaction.response.send_message("❌ brak środków")

        await db.update_crypto(interaction.user.id, -bet)

        symbols = ["🍒", "🍋", "🔔", "💎", "7️⃣"]

        embed = discord.Embed(title="🎰 Kręcenie...")
        embed.set_image(url="https://media.tenor.com/slot-spin.gif")

        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        await asyncio.sleep(2)

        win_chance = 25

        if random.randint(1, 100) <= win_chance:
            symbol = random.choice(symbols)
            result = [symbol, symbol, symbol]

            payout = bet * 5
            await db.update_crypto(interaction.user.id, payout)

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
    # 🃏 BLACKJACK (BET SYSTEM)
    # =========================
    def draw(self):
        return random.choice([2,3,4,5,6,7,8,9,10,10,10,11])

    def score(self, hand):
        return sum(hand)

    @app_commands.command(name="blackjack", description="🃏 Blackjack")
    async def blackjack(self, interaction: discord.Interaction, bet: int):

        if bet <= 0:
            return await interaction.response
