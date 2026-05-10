import discord
from discord.ext import commands
from discord import app_commands
import database as db


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # 👤 PROFIL
    # =========================
    @app_commands.command(name="profil", description="👤 Twój profil ekonomii")
    async def profil(self, interaction: discord.Interaction, user: discord.Member = None):

        user = user or interaction.user

        data = await db.get_profile(user.id)

        crypto = data.get("crypto", 0)
        pln = data.get("pln", 0)
        bank_crypto = data.get("bank_crypto", 0)
        bank_pln = data.get("bank_pln", 0)
        wins = data.get("wins", 0)

        embed = discord.Embed(
            title="👤 Profil gracza",
            color=0x00ffcc
        )

        embed.add_field(name="Użytkownik", value=user.mention, inline=False)
        embed.add_field(name="💎 Crypto", value=f"{crypto}", inline=True)
        embed.add_field(name="🇵🇱 PLN", value=f"{pln}", inline=True)
        embed.add_field(name="🏦 Bank Crypto", value=f"{bank_crypto}", inline=True)
        embed.add_field(name="🏦 Bank PLN", value=f"{bank_pln}", inline=True)
        embed.add_field(name="🏆 Wygrane", value=f"{wins}", inline=False)

        embed.set_thumbnail(url=user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    # =========================
    # 💸 PRZELEW
    # =========================
    @app_commands.command(name="przelej", description="💸 Przelej pieniądze")
    @app_commands.choices(currency=[
        app_commands.Choice(name="Crypto 💎", value="crypto"),
        app_commands.Choice(name="PLN 🇵🇱", value="pln")
    ])
    async def przelej(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        amount: int,
        currency: app_commands.Choice[str]
    ):

        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ Nie możesz przelać sobie.", ephemeral=True)

        if amount <= 0:
            return await interaction.response.send_message("❌ Zła kwota.", ephemeral=True)

        data = await db.get_profile(interaction.user.id)

        # CRYPTO
        if currency.value == "crypto":
            if data["crypto"] < amount:
                return await interaction.response.send_message("❌ Za mało 💎 Crypto.", ephemeral=True)

            await db.update_crypto(interaction.user.id, -amount)
            await db.update_crypto(user.id, amount)

            symbol = "💎 Crypto"

        # PLN
        else:
            if data["pln"] < amount:
                return await interaction.response.send_message("❌ Za mało 🇵🇱 PLN.", ephemeral=True)

            await db.update_pln(interaction.user.id, -amount)
            await db.update_pln(user.id, amount)

            symbol = "🇵🇱 PLN"

        await interaction.response.send_message(
            f"💸 **Przelew zakończony!**\n"
            f"👤 Do: {user.mention}\n"
            f"💰 Kwota: {amount} {symbol}"
        )

    # =========================
    # 💰 BALANS
    # =========================
    @app_commands.command(name="balans", description="💰 Sprawdź swoje saldo")
    async def balans(self, interaction: discord.Interaction, user: discord.Member = None):

        user = user or interaction.user

        data = await db.get_profile(user.id)

        await interaction.response.send_message(
            f"💰 **Saldo {user.mention}**\n"
            f"💎 Crypto: {data['crypto']}\n"
            f"🇵🇱 PLN: {data['pln']}\n"
            f"🏦 Bank Crypto: {data['bank_crypto']}\n"
            f"🏦 Bank PLN: {data['bank_pln']}"
        )

    # =========================
    # 🏦 DEPOZYT CRYPTO
    # =========================
    @app_commands.command(name="deposit", description="🏦 Wpłać do banku")
    @app_commands.describe(amount="Ilość")
    async def deposit(self, interaction: discord.Interaction, amount: int):

        if amount <= 0:
            return await interaction.response.send_message("❌ Zła kwota", ephemeral=True)

        data = await db.get_profile(interaction.user.id)

        if data["crypto"] < amount:
            return await interaction.response.send_message("❌ Za mało 💎", ephemeral=True)

        await db.update_crypto(interaction.user.id, -amount)
        await db.update_bank_crypto(interaction.user.id, amount)

        await interaction.response.send_message(f"🏦 Wpłacono {amount} 💎 do banku")

    # =========================
    # 🏦 WITHDRAW CRYPTO
    # =========================
    @app_commands.command(name="withdraw", description="🏦 Wypłać z banku")
    @app_commands.describe(amount="Ilość")
    async def withdraw(self, interaction: discord.Interaction, amount: int):

        if amount <= 0:
            return await interaction.response.send_message("❌ Zła kwota", ephemeral=True)

        data = await db.get_profile(interaction.user.id)

        if data["bank_crypto"] < amount:
            return await interaction.response.send_message("❌ Za mało w banku", ephemeral=True)

        await db.update_bank_crypto(interaction.user.id, -amount)
        await db.update_crypto(interaction.user.id, amount)

        await interaction.response.send_message(f"💸 Wypłacono {amount} 💎 z banku")


async def setup(bot):
    await bot.add_cog(Economy(bot))
