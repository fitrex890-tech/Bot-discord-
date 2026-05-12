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
        embed.set_thumbnail(url=interaction.client.user.display_avatar.url)

        embed.add_field(
            name="💰 Ekonomia",
            value=(
                "`/balans` — sprawdź saldo\n"
                "`/profil` — pełny profil ekonomiczny\n"
                "`/daily` — codzienna nagroda (24h cooldown)\n"
                "`/pracuj` — zarabiaj co 1h\n"
                "`/przelej` — przelej 💎/PLN innemu graczowi\n"
                "`/deposit` — wpłać do banku\n"
                "`/withdraw` — wypłać z banku\n"
                "`/historia` — historia transakcji"
            ),
            inline=False,
        )

        embed.add_field(
            name="🎰 Gry",
            value=(
                "`/spin` — koło fortuny (Low / Medium / Hard)\n"
                "`/slot` — slot machine z animacją bębnów\n"
                "`/blackjack` — blackjack z przyciskami Hit / Stand / Double\n"
                "`/coinflip` — orzeł czy reszka\n"
                "`/mines` — pole minowe (Łatwy / Normalny / Trudny)\n"
                "`/okradnij @gracz` — próba kradzieży (45% szans, cooldown 1h)"
            ),
            inline=False,
        )

        embed.add_field(
            name="🏪 Sklep & Przedmioty",
            value=(
                "`/sklep` — przeglądaj sklep z paginacją\n"
                "`/kup <id>` — kup przedmiot (np. `/kup shield`)\n"
                "`/ekwipunek` — posiadane przedmioty i czas wygaśnięcia\n"
                "`/kategorie` — sklep według kategorii\n"
                "`/odbierz` — odbierz zarobki z ⛏️ Kryptokoparki"
            ),
            inline=False,
        )

        embed.add_field(
            name="👑 Rangi",
            value=(
                "`/ranga` — sprawdź swoją rangę i postęp\n"
                "`/rangi` — lista wszystkich rang i wymagań\n"
                "`/top` — ranking Top 10 najbogatszych graczy\n"
                "`/toprangi` — rozkład graczy według rang"
            ),
            inline=False,
        )

        embed.add_field(
            name="🎉 Giveaway",
            value=(
                "`/giveaway` — stwórz giveaway `[ADMIN]`\n"
                "  Parametry: `kwota`, `czas` (np. `2h`, `1d`), `zwyciezcy`, `opis`\n"
                "`/reroll` — nowe losowanie zwycięzcy `[ADMIN]`"
            ),
            inline=False,
        )

        embed.add_field(
            name="🛡️ Admin",
            value=(
                "`/dodaj @gracz kwota` — dodaj 💎\n"
                "`/usun @gracz kwota` — usuń 💎\n"
                "`/set @gracz kwota` — ustaw dokładne saldo\n"
                "`/addpln @gracz kwota` — dodaj PLN\n"
                "`/reset @gracz` — zresetuj konto (wymaga potwierdzenia)\n"
                "`/info @gracz` — szczegółowe info o koncie"
            ),
            inline=False,
        )

        embed.add_field(
            name="🛒 ID przedmiotów sklepu",
            value=(
                "`vip` `lucky_charm` `shield` `work_boost`\n"
                "`daily_boost` `casino_pass` `robber_kit` `crypto_miner`"
            ),
            inline=False,
        )

        embed.set_footer(text="Crypto Casino Bot • Użyj / aby zobaczyć wszystkie komendy")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
