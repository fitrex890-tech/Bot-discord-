import discord
from discord.ext import commands
from discord import app_commands
import database as db
import utils


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ==============================
    # ADMIN CHECK (POPRAWNY)
    # ==============================
    def is_admin():
        async def predicate(interaction: discord.Interaction):
            return interaction.user.guild_permissions.administrator

        return app_commands.check(predicate)

    # ==============================
    # DODAJ PIENIĄDZE
    # ==============================
    @app_commands.command(
        name="dodajpieniadze",
        description="[ADMIN] Dodaj pieniądze użytkownikowi"
    )
    @is_admin()
    async def dodaj_pieniadze(
        self,
        interaction: discord.Interaction,
        uzytkownik: discord.Member,
        kwota: int
    ):

        if kwota <= 0:
            return await interaction.response.send_message(
                embed=utils.make_embed(
                    "❌ Błąd",
                    "Kwota musi być większa od 0.",
                    utils.LOSE_COLOR,
                ),
                ephemeral=True,
            )

        await db.update_balance(uzytkownik.id, kwota)

        await db.log_transaction(
            uzytkownik.id,
            kwota,
            "admin_add",
            f"Admin {interaction.user.id}"
        )

        await interaction.response.send_message(
            embed=utils.make_embed(
                "✅ Dodano Pieniądze",
                f"{uzytkownik.mention} otrzymał {utils.format_currency(kwota)}.",
                utils.WIN_COLOR,
            )
        )

    # ==============================
    # USUŃ PIENIĄDZE
    # ==============================
    @app_commands.command(
        name="usunpieniadze",
        description="[ADMIN] Usuń pieniądze użytkownikowi"
    )
    @is_admin()
    async def usun_pieniadze(
        self,
        interaction: discord.Interaction,
        uzytkownik: discord.Member,
        kwota: int
    ):

        if kwota <= 0:
            return await interaction.response.send_message(
                embed=utils.make_embed(
                    "❌ Błąd",
                    "Kwota musi być większa od 0.",
                    utils.LOSE_COLOR,
                ),
                ephemeral=True,
            )

        await db.update_balance(uzytkownik.id, -kwota)

        await db.log_transaction(
            uzytkownik.id,
            -kwota,
            "admin_remove",
            f"Admin {interaction.user.id}"
        )

        await interaction.response.send_message(
            embed=utils.make_embed(
                "✅ Usunięto Pieniądze",
                f"Usunięto {utils.format_currency(kwota)} od {uzytkownik.mention}.",
                utils.WIN_COLOR,
            )
        )

    # ==============================
    # USTAW BALANS
    # ==============================
    @app_commands.command(
        name="ustawpieniadze",
        description="[ADMIN] Ustaw balans użytkownika"
    )
    @is_admin()
    async def ustaw_pieniadze(
        self,
        interaction: discord.Interaction,
        uzytkownik: discord.Member,
        kwota: int
    ):

        if kwota < 0:
            return await interaction.response.send_message(
                embed=utils.make_embed(
                    "❌ Błąd",
                    "Balans nie może być ujemny.",
                    utils.LOSE_COLOR,
                ),
                ephemeral=True,
            )

        await db.set_balance(uzytkownik.id, kwota)

        await interaction.response.send_message(
            embed=utils.make_embed(
                "✅ Ustawiono Balans",
                f"{uzytkownik.mention} ma teraz {utils.format_currency(kwota)}.",
                utils.WIN_COLOR,
            )
        )

    # ==============================
    # RESET USERA
    # ==============================
    @app_commands.command(
        name="resetuser",
        description="[ADMIN] Reset konta użytkownika"
    )
    @is_admin()
    async def reset_user(
        self,
        interaction: discord.Interaction,
        uzytkownik: discord.Member
    ):

        await db.set_balance(uzytkownik.id, 0)
        await db.set_bank(uzytkownik.id, 0)

        await interaction.response.send_message(
            embed=utils.make_embed(
                "✅ Reset",
                f"Konto {uzytkownik.mention} zostało zresetowane.",
                utils.WIN_COLOR,
            )
        )

    # ==============================
    # ERROR HANDLER
    # ==============================
    @dodaj_pieniadze.error
    @usun_pieniadze.error
    @ustaw_pieniadze.error
    @reset_user.error
    async def admin_error(self, interaction: discord.Interaction, error):

        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                embed=utils.make_embed(
                    "❌ Brak uprawnień",
                    "Musisz być administratorem.",
                    utils.LOSE_COLOR,
                ),
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
