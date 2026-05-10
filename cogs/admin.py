import discord
from discord.ext import commands
from discord import app_commands
import database as db
import utils


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="przelej",
        description="Przelej Crypto innemu użytkownikowi"
    )
    @app_commands.describe(
        uzytkownik="Osoba która otrzyma pieniądze",
        kwota="Kwota przelewu"
    )
    async def transfer(
        self,
        interaction: discord.Interaction,
        uzytkownik: discord.Member,
        kwota: int
    ):

        # =========================
        # SPRAWDZENIA
        # =========================
        if uzytkownik.bot:
            return await interaction.response.send_message(
                embed=utils.make_embed(
                    "❌ Błąd",
                    "Nie możesz wysyłać pieniędzy botom.",
                    utils.LOSE_COLOR,
                ),
                ephemeral=True,
            )

        if kwota <= 0:
            return await interaction.response.send_message(
                embed=utils.make_embed(
                    "❌ Błąd",
                    "Kwota musi być większa od 0.",
                    utils.LOSE_COLOR,
                ),
                ephemeral=True,
            )

        # =========================
        # ADMIN BYPASS
        # =========================
        if interaction.user.guild_permissions.administrator:

            await db.update_balance(uzytkownik.id, kwota)

            await db.log_transaction(
                uzytkownik.id,
                kwota,
                "admin_transfer",
                f"Admin {interaction.user.id}"
            )

            return await interaction.response.send_message(
                embed=utils.make_embed(
                    "✅ Admin Transfer",
                    f"{interaction.user.mention} przekazał "
                    f"{utils.format_currency(kwota)} "
                    f"użytkownikowi {uzytkownik.mention}.",
                    utils.WIN_COLOR,
                )
            )

        # =========================
        # NORMALNY UŻYTKOWNIK
        # =========================
        balance = await db.get_balance(interaction.user.id)

        if balance < kwota:
            return await interaction.response.send_message(
                embed=utils.make_embed(
                    "❌ Brak Środków",
                    "Nie masz wystarczającej ilości Crypto.",
                    utils.LOSE_COLOR,
                ),
                ephemeral=True,
            )

        # Zabierz nadawcy
        await db.update_balance(interaction.user.id, -kwota)

        # Dodaj odbiorcy
        await db.update_balance(uzytkownik.id, kwota)

        # Logi
        await db.log_transaction(
            interaction.user.id,
            -kwota,
            "transfer_sent",
            f"Do {uzytkownik.id}"
        )

        await db.log_transaction(
            uzytkownik.id,
            kwota,
            "transfer_received",
            f"Od {interaction.user.id}"
        )

        await interaction.response.send_message(
            embed=utils.make_embed(
                "💸 Przelew Wysłany",
                f"Wysłano {utils.format_currency(kwota)} "
                f"do {uzytkownik.mention}.",
                utils.WIN_COLOR,
            )
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
