import discord
from discord.ext import commands
from discord import app_commands
import utils


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="pomoc", description="📖 Lista wszystkich komend bota")
    async def pomoc(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="📖 Crypto Casino — Pomoc",
            description="Wszystkie dostępne komendy. Każda ma opis przy wpisaniu `/`.",
            color=utils.JACKPOT_COLOR,
        )

        embed.add_field(
            name="💰 Ekonomia",
            value=(
                "`/balans` — sprawdź saldo\n"
                "`/profil` — pełny profil\n"
                "`/daily` — codzienna nagroda\n"
                "`/pracuj` — zarabiaj co 1h\n"
                "`/przelej` — przelej 💎 innemu graczowi\n"
                "`/deposit` — wpłać do banku\n"
                "`/withdraw` — wypłać z banku\n"
                "`/historia` — historia transakcji"
            ),
            inline=False,
        )

        embed.add_field(
            name="🎰 Gry",
            value=(
                "`/spin` — koło fortuny (Low/Medium/Hard)\n"
                "`/slot` — slot machine z animacją\n"
                "`/blackjack` — blackjack z Hit/Stand/Double\n"
                "`/coinflip` — orzeł czy reszka\n"
                "`/mines` — pole minowe\n"
                "`/okradnij` — okradnij gracza (45% szans)"
            ),
            inline=False,
        )

        embed.add_field(
            name="🏪 Sklep",
            value=(
                "`/sklep` — przeglądaj sklep\n"
                "`/kup <id>` — kup przedmiot\n"
                "`/ekwipunek` — posiadane przedmioty\n"
                "`/kategorie` — sklep wg kategorii\n"
                "`/odbierz` — odbierz zarobki z koparki"
            ),
            inline=False,
        )

        embed.add_field(
            name="👑 Rangi",
            value=(
                "`/ranga` — sprawdź swoją rangę\n"
                "`/rangi` — lista rang i wymagań\n"
                "`/top` — ranking bogaczy\n"
                "`/toprangi` — rozkład graczy wg rang"
            ),
            inline=False,
        )

        embed.add_field(
            name="🎉 Giveaway",
            value=(
                "`/giveaway` — stwórz giveaway `[ADMIN]`\n"
                "`/reroll` — nowe losowanie `[ADMIN]`"
            ),
            inline=False,
        )

        embed.add_field(
            name="🛡️ Admin",
            value=(
                "`/dodaj` — dodaj 💎 graczowi\n"
                "`/usun` — usuń 💎 graczowi\n"
                "`/set` — ustaw balans\n"
                "`/reset` — zresetuj konto"
            ),
            inline=False,
        )

        embed.add_field(
            name="🤖 Bot",
            value="`/pomoc` — ta wiadomość",
            inline=False,
        )

        embed.set_footer(text="Crypto Casino Bot • Użyj / aby zobaczyć komendy")
        embed.set_thumbnail(url=interaction.client.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
