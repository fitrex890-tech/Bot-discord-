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
    @app_commands.command(name="profil", description="👤 Twój profil")
    async def profil(self, interaction: discord.Interaction, user: discord.Member = None):

        user = user or interaction.user
        data = await db.get_profile(user.id)

        embed = discord.Embed(
            title="👤 Profil ekonomii",
            color=0x00D4FF
        )

        embed.set_thumbnail(url=user.display_avatar.url)

        embed.add_field(name="💎 Crypto", value=data["crypto"], inline=True)
        embed.add_field(name="🇵🇱 PLN", value=data["pln"], inline=True)
        embed.add_field(name="🏦 Bank 💎", value=data["bank_crypto"], inline=True)
        embed.add_field(name="🏦 Bank PLN", value=data["bank_pln"], inline=True)
        embed.add_field(name="🏆 Wygrane", value=data["wins"], inline=False)

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
            return await interaction.response.send_message("❌ Nie możesz przelać sobie", ephemeral=True)

        if amount <= 0:
            return await interaction.response.send_message("❌ Zła kwota", ephemeral=True)

        data = await db.get_profile(interaction.user.id)

        if currency.value == "crypto":
            if data["crypto"] < amount:
                return await interaction.response.send_message("❌ Za mało 💎", ephemeral=True)

            await db.update_crypto(interaction.user.id, -amount)
            await db.update_crypto(user.id, amount)

            symbol = "💎"

        else:
            if data["pln"] < amount:
                return await interaction.response.send_message("❌ Za mało PLN", ephemeral=True)

            await db.update_pln(interaction.user.id, -amount)
            await db.update_pln(user.id, amount)

            symbol = "🇵🇱"

        embed = discord.Embed(
            title="💸 Przelew zakończony",
            description=f"{interaction.user.mention} → {user.mention}\n💰 {amount} {symbol}",
            color=0x2ECC71
        )

        await interaction.response.send_message(embed=embed)

    # =========================
    # 💰 BALANS
    # =========================
    @app_commands.command(name="balans", description="💰 saldo")
    async def balans(self, interaction: discord.Interaction, user: discord.Member = None):

        user = user or interaction.user
        data = await db.get_profile(user.id)

        embed = discord.Embed(
            title=f"💰 Balans {user.display_name}",
            color=0xF1C40F
        )

        embed.add_field(name="💎 Crypto", value=data["crypto"], inline=True)
        embed.add_field(name="🇵🇱 PLN", value=data["pln"], inline=True)
        embed.add_field(name="🏦 Bank 💎", value=data["bank_crypto"], inline=True)
        embed.add_field(name="🏦 Bank PLN", value=data["bank_pln"], inline=True)

        await interaction.response.send_message(embed=embed)

    # =========================
    # 🏦 DEPOSIT (CRYPTO + PLN FIX)
    # =========================
    @app_commands.command(name="deposit", description="🏦 wpłać do banku")
    @app_commands.choices(currency=[
        app_commands.Choice(name="Crypto 💎", value="crypto"),
        app_commands.Choice(name="PLN 🇵🇱", value="pln")
    ])
    async def deposit(self, interaction: discord.Interaction, amount: int, currency: app_commands.Choice[str]):

        if amount <= 0:
            return await interaction.response.send_message("❌ Zła kwota", ephemeral=True)

        data = await db.get_profile(interaction.user.id)

        if currency.value == "crypto":
            if data["crypto"] < amount:
                return await interaction.response.send_message("❌ Za mało 💎", ephemeral=True)

            await db.update_crypto(interaction.user.id, -amount)
            await db.update_bank_crypto(interaction.user.id, amount)

        else:
            if data["pln"] < amount:
                return await interaction.response.send_message("❌ Za mało PLN", ephemeral=True)

            await db.update_pln(interaction.user.id, -amount)
            await db.update_bank_pln(interaction.user.id, amount)

        embed = discord.Embed(
            title="🏦 Wpłata zakończona",
            description=f"💰 +{amount} {currency.value.upper()}",
            color=0x3498DB
        )

        await interaction.response.send_message(embed=embed)

    # =========================
    # 🏦 WITHDRAW FIX
    # =========================
    @app_commands.command(name="withdraw", description="🏦 wypłać z banku")
    @app_commands.choices(currency=[
        app_commands.Choice(name="Crypto 💎", value="crypto"),
        app_commands.Choice(name="PLN 🇵🇱", value="pln")
    ])
    async def withdraw(self, interaction: discord.Interaction, amount: int, currency: app_commands.Choice[str]):

        if amount <= 0:
            return await interaction.response.send_message("❌ Zła kwota", ephemeral=True)

        data = await db.get_profile(interaction.user.id)

        if currency.value == "crypto":
            if data["bank_crypto"] < amount:
                return await interaction.response.send_message("❌ Za mało w banku", ephemeral=True)

            await db.update_bank_crypto(interaction.user.id, -amount)
            await db.update_crypto(interaction.user.id, amount)

        else:
            if data["bank_pln"] < amount:
                return await interaction.response.send_message("❌ Za mało w banku", ephemeral=True)

            await db.update_bank_pln(interaction.user.id, -amount)
            await db.update_pln(interaction.user.id, amount)

        embed = discord.Embed(
            title="💸 Wypłata zakończona",
            description=f"💰 +{amount} {currency.value.upper()}",
            color=0xE67E22
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Economy(bot))
