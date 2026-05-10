import discord
from discord.ext import commands
from discord import app_commands
import database as db
import utils


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_admin():
        async def predicate(interaction: discord.Interaction):
            return interaction.user.guild_permissions.administrator
        return app_commands.check(predicate)

    @app_commands.command(name="addmoney", description="[ADMIN] Dodaj Crypto użytkownikowi")
    @app_commands.describe(uzytkownik="Użytkownik", kwota="Kwota do dodania")
    @is_admin()
    async def add_money(self, interaction: discord.Interaction, uzytkownik: discord.Member, kwota: int):
        await db.update_balance(uzytkownik.id, kwota)
        await db.log_transaction(uzytkownik.id, kwota, "admin_add", f"Admin {interaction.user.id}")
        await interaction.response.send_message(
            embed=utils.make_embed(
                "✅ Dodano Środki",
                f"Dodano {utils.format_currency(kwota)} do konta {uzytkownik.mention}.",
                utils.WIN_COLOR,
            )
        )

    @app_commands.command(name="removemoney", description="[ADMIN] Usuń Crypto od użytkownika")
    @app_commands.describe(uzytkownik="Użytkownik", kwota="Kwota do usunięcia")
    @is_admin()
    async def remove_money(self, interaction: discord.Interaction, uzytkownik: discord.Member, kwota: int):
        await db.update_balance(uzytkownik.id, -kwota)
        await db.log_transaction(uzytkownik.id, -kwota, "admin_remove", f"Admin {interaction.user.id}")
        await interaction.response.send_message(
            embed=utils.make_embed(
                "✅ Usunięto Środki",
                f"Usunięto {utils.format_currency(kwota)} z konta {uzytkownik.mention}.",
                utils.WIN_COLOR,
            )
        )

    @app_commands.command(name="setmoney", description="[ADMIN] Ustaw balans użytkownika")
    @app_commands.describe(uzytkownik="Użytkownik", kwota="Nowy balans")
    @is_admin()
    async def set_money(self, interaction: discord.Interaction, uzytkownik: discord.Member, kwota: int):
        await db.set_balance(uzytkownik.id, kwota)
        await interaction.response.send_message(
            embed=utils.make_embed(
                "✅ Ustawiono Balans",
                f"Balans {uzytkownik.mention} ustawiony na {utils.format_currency(kwota)}.",
                utils.WIN_COLOR,
            )
        )

    @app_commands.command(name="resetuser", description="[ADMIN] Zresetuj konto użytkownika")
    @app_commands.describe(uzytkownik="Użytkownik do zresetowania")
    @is_admin()
    async def reset_user(self, interaction: discord.Interaction, uzytkownik: discord.Member):
        await db.set_balance(uzytkownik.id, 0)
        await db.set_bank(uzytkownik.id, 0)
        await interaction.response.send_message(
            embed=utils.make_embed(
                "✅ Zresetowano Konto",
                f"Konto {uzytkownik.mention} zostało zresetowane do 0.",
                utils.WIN_COLOR,
            )
        )

    @app_commands.command(name="botinfo", description="Informacje o bocie")
    async def bot_info(self, interaction: discord.Interaction):
        embed = utils.make_embed(
            title="🤖 Crypto Casino Bot",
            description="Bot ekonomiczno-kasynowy z walutą **Crypto** 💎",
            color=utils.JACKPOT_COLOR,
        )
        embed.add_field(
            name="💰 Ekonomia",
            value="/balans • /daily • /pracuj • /żebrz • /crime\n/okradnij • /wpłać • /wypłać • /przelej • /top",
            inline=False,
        )
        embed.add_field(
            name="🎰 Gry",
            value="/spin • /blackjack • /slots • /coinflip • /roulette • /mines",
            inline=False,
        )
        embed.add_field(
            name="📊 Limity",
            value=f"Min stawka: **{utils.format_currency(10)}**\nMaks stawka: **{utils.format_currency(50000)}**",
            inline=True,
        )
        embed.add_field(
            name="🏦 Bank",
            value="Pieniądze w banku są bezpieczne przed kradzieżą!",
            inline=True,
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @add_money.error
    @remove_money.error
    @set_money.error
    @reset_user.error
    async def admin_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Brak Uprawnień", "Tylko administratorzy mogą używać tej komendy!", utils.LOSE_COLOR),
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
