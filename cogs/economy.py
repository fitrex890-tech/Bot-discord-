import discord
from discord.ext import commands
from discord import app_commands
import random
import database as db


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ======================
    # BALANS
    # ======================
    @app_commands.command(name="balans")
    async def balans(self, interaction: discord.Interaction):

        c, p, bc, bp = await db.get_wallet(interaction.user.id)

        embed = discord.Embed(title="💰 Economy")

        embed.add_field(name="💎 Crypto", value=c, inline=False)
        embed.add_field(name="🇵🇱 PLN", value=f"{p} zł", inline=False)
        embed.add_field(name="🏦 Bank Crypto", value=bc, inline=False)
        embed.add_field(name="🏦 Bank PLN", value=f"{bp} zł", inline=False)

        await interaction.response.send_message(embed=embed)

    # ======================
    # DAILY
    # ======================
    @app_commands.command(name="daily")
    async def daily(self, interaction: discord.Interaction):

        await db.update_crypto(interaction.user.id, 150)
        await db.update_pln(interaction.user.id, 75)

        await interaction.response.send_message("🎁 +150 💎 +75 zł")

    # ======================
    # DEPOSIT
    # ======================
    @app_commands.command(name="deposit")
    @app_commands.choices(currency=[
        app_commands.Choice(name="Crypto", value="crypto"),
        app_commands.Choice(name="PLN", value="pln")
    ])
    async def deposit(self, interaction, amount: int, currency: app_commands.Choice[str]):

        await db.deposit(interaction.user.id, amount, currency.value)
        await interaction.response.send_message(f"🏦 Zdeponowano {amount} {currency.name}")

    # ======================
    # WITHDRAW
    # ======================
    @app_commands.command(name="withdraw")
    @app_commands.choices(currency=[
        app_commands.Choice(name="Crypto", value="crypto"),
        app_commands.Choice(name="PLN", value="pln")
    ])
    async def withdraw(self, interaction, amount: int, currency: app_commands.Choice[str]):

        await db.withdraw(interaction.user.id, amount, currency.value)
        await interaction.response.send_message(f"💰 Wypłacono {amount} {currency.name}")

    # ======================
    # TRANSFER
    # ======================
    @app_commands.command(name="przelej")
    @app_commands.choices(currency=[
        app_commands.Choice(name="Crypto", value="crypto"),
        app_commands.Choice(name="PLN", value="pln")
    ])
    async def transfer(self, interaction, user: discord.Member, amount: int, currency: app_commands.Choice[str]):

        if currency.value == "crypto":
            await db.update_crypto(interaction.user.id, -amount)
            await db.update_crypto(user.id, amount)
        else:
            await db.update_pln(interaction.user.id, -amount)
            await db.update_pln(user.id, amount)

        await interaction.response.send_message("💸 Przelano")

    # ======================
    # STEAL (KRADZIEŻ Z WALIZKI)
    # ======================
    @app_commands.command(name="kradnij")
    async def steal(self, interaction: discord.Interaction, user: discord.Member):

        if random.randint(1, 100) < 50:
            amount = random.randint(50, 200)

            await db.update_crypto(user.id, -amount)
            await db.update_crypto(interaction.user.id, amount)

            await interaction.response.send_message(f"🟢 Ukradłeś {amount} 💎")
        else:
            await interaction.response.send_message("🔴 Kradzież nieudana")

async def setup(bot):
    await bot.add_cog(Economy(bot))
