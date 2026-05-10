import discord
from discord.ext import commands
from discord import app_commands
import database as db


# ==============================
# ADMIN CHECK
# ==============================
def is_admin():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator

    return app_commands.check(predicate)


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ==============================
    # ➕ DODAJ CRYPTO
    # ==============================
    @app_commands.command(name="dodaj", description="[ADMIN] Dodaj 💎 Crypto")
    @is_admin()
    async def dodaj(self, interaction: discord.Interaction, user: discord.Member, kwota: int):

        if kwota <= 0:
            return await interaction.response.send_message("❌ Kwota musi być > 0", ephemeral=True)

        await db.update_crypto(user.id, kwota)

        embed = discord.Embed(
            title="✅ Dodano Crypto",
            description=f"{user.mention} otrzymał **+{kwota} 💎**",
            color=0x2ECC71
        )

        await interaction.response.send_message(embed=embed)

    # ==============================
    # ➖ USUŃ CRYPTO
    # ==============================
    @app_commands.command(name="usun", description="[ADMIN] Usuń 💎 Crypto")
    @is_admin()
    async def usun(self, interaction: discord.Interaction, user: discord.Member, kwota: int):

        if kwota <= 0:
            return await interaction.response.send_message("❌ Kwota musi być > 0", ephemeral=True)

        await db.update_crypto(user.id, -kwota)

        embed = discord.Embed(
            title="❌ Usunięto Crypto",
            description=f"{user.mention} stracił **-{kwota} 💎**",
            color=0xE74C3C
        )

        await interaction.response.send_message(embed=embed)

    # ==============================
    # 💰 SET BALANCE
    # ==============================
    @app_commands.command(name="set", description="[ADMIN] Ustaw Crypto")
    @is_admin()
    async def set(self, interaction: discord.Interaction, user: discord.Member, kwota: int):

        if kwota < 0:
            return await interaction.response.send_message("❌ Nie może być < 0", ephemeral=True)

        data = await db.get_profile(user.id)
        current = data["crypto"]

        diff = kwota - current
        await db.update_crypto(user.id, diff)

        embed = discord.Embed(
            title="⚙️ Ustawiono balans",
            description=f"{user.mention} ma teraz **{kwota} 💎**",
            color=0xF1C40F
        )

        await interaction.response.send_message(embed=embed)

    # ==============================
    # 🧨 RESET USERA
    # ==============================
    @app_commands.command(name="reset", description="[ADMIN] Reset konta")
    @is_admin()
    async def reset(self, interaction: discord.Interaction, user: discord.Member):

        data = await db.get_profile(user.id)

        await db.update_crypto(user.id, -data["crypto"])
        await db.update_pln(user.id, -data["pln"])

        embed = discord.Embed(
            title="🧨 Reset konta",
            description=f"{user.mention} został zresetowany",
            color=0x95A5A6
        )

        await interaction.response.send_message(embed=embed)


# ==============================
# SETUP (RAILWAY FIX)
# ==============================
async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
