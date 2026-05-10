import discord
from discord.ext import commands
from discord import app_commands
import utils


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="pomoc",
        description="Lista komend bota"
    )
    async def pomoc(self, interaction: discord.Interaction):

        embed = utils.make_embed(
            title="📖 Pomoc - Komendy",
            description="Lista wszystkich dostępnych komend",
            color=utils.JACKPOT_COLOR,
        )

        embed.add_field(
            name="💰 Ekonomia",
            value="/balans • /daily • /pracuj • /żebrz • /przelej",
            inline=False,
        )

        embed.add_field(
            name="🎰 Gry",
            value="/spin • /blackjack • /slots • /roulette",
            inline=False,
        )

        embed.add_field(
            name="🛡️ Admin",
            value="/dodajpieniadze • /usunpieniadze • /ustawpieniadze • /resetuser",
            inline=False,
        )

        embed.add_field(
            name="🤖 Bot",
            value="/botinfo • /pomoc",
            inline=False,
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
