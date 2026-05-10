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

        total_commands = len(list(self.bot.tree.walk_commands()))
        guild_count = len(self.bot.guilds)
        total_users = sum(g.member_count or 0 for g in self.bot.guilds)

        embed = utils.make_embed(
            title="🤖 Crypto Casino Bot",
            description="Bot ekonomiczno-kasynowy z walutą Crypto 💎",
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
            value="/dodajpieniadze • /usunpieniadze • /ustawpieniadze",
            inline=False,
        )

        embed.add_field(
            name="📊 Info",
            value=(
                f"🌐 Serwery: **{guild_count}**\n"
                f"👥 Użytkownicy: **{total_users:,}**\n"
                f"⚙️ Komendy: **{total_commands}**"
            ),
            inline=False,
        )

        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(BotInfo(bot))
