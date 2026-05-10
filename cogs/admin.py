import discord
from discord.ext import commands
from discord import app_commands
import database as db
import utils


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =========================================
    # DODAJ PIENIĄDZE
    # =========================================
    @app_commands.command(
        name="dodajpieniadze",
        description="[ADMIN] Dodaj pieniądze użytkownikowi"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        uzytkownik="Użytkownik",
        kwota="Kwota do dodania"
    )
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

        await db.update_balance(
            uzytkownik.id,
            kwota
        )

        await db.log_transaction(
            uzytkownik.id,
            kwota,
            "admin_add",
            f"Admin {interaction.user.id}"
        )

        await interaction.response.send_message(
            embed=utils.make_embed(
                "✅ Dodano Pieniądze",
                f"{uzytkownik.mention} otrzymał "
                f"{utils.format_currency(kwota)}.",
                utils.WIN_COLOR,
            )
        )

    # =========================================
    # USUŃ PIENIĄDZE
    # =========================================
    @app_commands.command(
        name="usunpieniadze",
        description="[ADMIN] Usuń pieniądze użytkownikowi"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        uzytkownik="Użytkownik",
        kwota="Kwota do usunięcia"
    )
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

        await db.update_balance(
            uzytkownik.id,
            -kwota
        )

        await db.log_transaction(
            uzytkownik.id,
            -kwota,
            "admin_remove",
            f"Admin {interaction.user.id}"
        )

        await interaction.response.send_message(
            embed=utils.make_embed(
                "✅ Usunięto Pieniądze",
                f"Usunięto {utils.format_currency(kwota)} "
                f"użytkownikowi {uzytkownik.mention}.",
                utils.WIN_COLOR,
            )
        )

    # =========================================
    # USTAW PIENIĄDZE
    # =========================================
    @app_commands.command(
        name="ustawpieniadze",
        description="[ADMIN] Ustaw balans użytkownika"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        uzytkownik="Użytkownik",
        kwota="Nowy balans"
    )
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

        await db.set_balance(
            uzytkownik.id,
            kwota
        )

        await interaction.response.send_message(
            embed=utils.make_embed(
                "✅ Ustawiono Balans",
                f"Balans {uzytkownik.mention} ustawiono na "
                f"{utils.format_currency(kwota)}.",
                utils.WIN_COLOR,
            )
        )

    # =========================================
    # RESET KONTA
    # =========================================
    @app_commands.command(
        name="resetuser",
        description="[ADMIN] Zresetuj konto użytkownika"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        uzytkownik="Użytkownik do zresetowania"
    )
    async def reset_user(
        self,
        interaction: discord.Interaction,
        uzytkownik: discord.Member
    ):

        await db.set_balance(
            uzytkownik.id,
            0
        )

        await db.set_bank(
            uzytkownik.id,
            0
        )

        await interaction.response.send_message(
            embed=utils.make_embed(
                "✅ Zresetowano Konto",
                f"Konto {uzytkownik.mention} zostało zresetowane.",
                utils.WIN_COLOR,
            )
        )

    # =========================================
    # BOT INFO
    # =========================================
    @app_commands.command(
        name="botinfo",
        description="Informacje o bocie"
    )
    async def bot_info(
        self,
        interaction: discord.Interaction
    ):

        embed = utils.make_embed(
            title="🤖 Crypto Casino Bot",
            description="Bot ekonomiczno-kasynowy z walutą Crypto 💎",
            color=utils.JACKPOT_COLOR,
        )

        embed.add_field(
            name="💰 Ekonomia",
            value=(
                "/balans • /daily • /pracuj • /żebrz\n"
                "/crime • /okradnij • /przelej"
            ),
            inline=False,
        )

        embed.add_field(
            name="🎰 Gry",
            value=(
                "/spin • /blackjack • /slots\n"
                "/coinflip • /roulette • /mines"
            ),
            inline=False,
        )

        embed.add_field(
            name="🛡️ Administracja",
            value=(
                "/dodajpieniadze\n"
                "/usunpieniadze\n"
                "/ustawpieniadze\n"
                "/resetuser"
            ),
            inline=False,
        )

        embed.add_field(
            name="📊 Limity",
            value=(
                f"Min Bet: {utils.format_currency(10)}\n"
                f"Max Bet: {utils.format_currency(50000)}"
            ),
            inline=True,
        )

        embed.add_field(
            name="🏦 Bank",
            value="Pieniądze w banku są bezpieczne przed kradzieżą.",
            inline=True,
        )

        embed.set_thumbnail(
            url=self.bot.user.display_avatar.url
        )

        embed.set_footer(
            text="Crypto Casino Bot"
        )

        await interaction.response.send_message(
            embed=embed
        )

    # =========================================
    # ERROR HANDLER
    # =========================================
    @dodaj_pieniadze.error
    @usun_pieniadze.error
    @ustaw_pieniadze.error
    @reset_user.error
    async def admin_error(
        self,
        interaction: discord.Interaction,
        error
    ):

        if isinstance(error, app_commands.MissingPermissions):

            await interaction.response.send_message(
                embed=utils.make_embed(
                    "❌ Brak Uprawnień",
                    "Musisz posiadać permisję Administrator.",
                    utils.LOSE_COLOR,
                ),
                ephemeral=True,
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
