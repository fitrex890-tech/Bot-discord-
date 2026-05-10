import discord
from discord.ext import commands
from discord import app_commands
import database as db


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ======================
    # BALANS
    # ======================
    @app_commands.command(name="balans", description="Twoje saldo")
    async def balans(self, interaction: discord.Interaction):

        crypto = await db.get_crypto(interaction.user.id)
        pln = await db.get_pln(interaction.user.id)

        embed = discord.Embed(title="💰 Balans", color=0xFFD700)
        embed.add_field(name="💎 Crypto", value=f"{crypto:,}", inline=False)
        embed.add_field(name="🇵🇱 PLN", value=f"{pln:,} zł", inline=False)

        await interaction.response.send_message(embed=embed)

    # ======================
    # DAILY
    # ======================
    @app_commands.command(name="daily", description="Dzienna nagroda")
    async def daily(self, interaction: discord.Interaction):

        await db.update_crypto(interaction.user.id, 100)
        await db.update_pln(interaction.user.id, 50)

        await interaction.response.send_message(
            "🎁 Otrzymałeś 100 💎 i 50 zł"
        )

    # ======================
    # PRZELEW
    # ======================
    @app_commands.command(name="przelej", description="Przelej środki")
    @app_commands.choices(waluta=[
        app_commands.Choice(name="Crypto 💎", value="crypto"),
        app_commands.Choice(name="PLN 🇵🇱", value="pln")
    ])
    async def przelej(self, interaction, user: discord.Member, kwota: int, waluta: app_commands.Choice[str]):

        if kwota <= 0:
            return await interaction.response.send_message("❌ Zła kwota")

        if waluta.value == "crypto":
            await db.update_crypto(interaction.user.id, -kwota)
            await db.update_crypto(user.id, kwota)
        else:
            await db.update_pln(interaction.user.id, -kwota)
            await db.update_pln(user.id, kwota)

        await interaction.response.send_message(f"💸 Przelano {kwota} {waluta.name}")

async def setup(bot):
    await bot.add_cog(Economy(bot))
