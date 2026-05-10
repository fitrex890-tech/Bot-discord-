import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import utils


class BotInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = datetime.utcnow()

    def get_uptime(self) -> str:
        """Oblicza uptime bota"""
        delta = datetime.utcnow() - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        else:
            return f"{minutes}m {seconds}s"

    @app_commands.command(name="botinfo", description="Informacje o bocie")
    async def botinfo(self, interaction: discord.Interaction):
        """Wyświetla informacje o bocie"""
        
        total_commands = len(self.bot.tree._get_all_commands())
        guild_count = len(self.bot.guilds)
        total_users = sum(guild.member_count for guild in self.bot.guilds)
        
        embed = utils.make_embed(
            title="🤖 Informacje o Bocie",
            description="",
            color=utils.INFO_COLOR,
        )
        
        embed.add_field(
            name="👨‍💻 Developer",
            value="**xrealfitrex**",
            inline=True,
        )
        
        embed.add_field(
            name="🏢 Serwer",
            value="**Zjednoczeni Ideą**",
            inline=True,
