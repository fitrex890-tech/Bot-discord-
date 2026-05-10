import discord
from discord.ext import commands
from discord import app_commands
import utils


class BotInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="botinfo",
        description="Informacje o bocie"
    )
    async def botinfo(self, interaction: discord.Interaction):

        embed = utils.make_embed(
            title="🎰 Hazard Bot",
            description="Bot ekonomiczno-kasynowy",
            color=utils.JACKPOT_COLOR,
        )

        embed.add_field(
            name="🤖 Nazwa",
            value="Hazard Bot",
            inline=True,
        )

        embed.add_field(
            name="👤 Stworzony przez",
            value="xrealfitrex",
            inline=True,
        )

        embed.add_field(
            name="🏠 Serwer",
            value="Zjednoczeni ideą",
            inline=False,
        )

        embed.add_field(
            name="📊 Statystyki",
            value=(
                f"🌐 Serwery: **{len(self.bot.guilds)}**\n"
                f"👥 Użytkownicy: **{sum(g.member_count or 0 for g in self.bot.guilds):,}**"
            ),
            inline=False,
        )

        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(BotInfo(bot))
