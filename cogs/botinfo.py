import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import utils


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = datetime.utcnow()

   .start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
"

    @app_commands.command(name="botinfo", description="Informacje o bocie")
    async def botinfo(self, interaction: discord.Interaction):
        """Wyświetla informacje o bocie"""
        
        # Pobierz liczbę komend
        total_commands = len(self.bot.tree._get_all_commands())
        
        # Pobierz liczbę serwerów
        guild_count = len(self.bot.guilds)
        
        # Oblicz użytkowników
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
            inline=True,
        )
        
        embed.add_field(
            name="⏱️ Uptime",
            value=f"**{self.get_uptime()}**",
            inline=True,
        )
        
        embed.add_field(
            name="📊 Statystyki",
            value=(
                f"🖥️ Serwery: **{guild_count}**\n"
                f"👥 Użytkownicy: **{total_users:,}**\n"
                f"⚙️ Komendy: **{total_commands}**"
            ),
            inline=False,
        )
        
        embed.add_field(
            name="🎮 Funkcje",
            value=(
                "💰 System ekonomii\n"
                "🎰 Mini-gry kasynowe\n"
                "🏆 Ranking graczy\n"
                "👑 System rang\n"
                "🎁 Giveaway'e\n"
 name="💻 Technologia",
            value="**discord.py** • **SQLite** • **Python 3.10+**",
            inline=False,
        )
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Crypto Casino Bot | /botinfo")
        
        await interaction.response.send_message(embed=embed)


async def setup(bot:.py do `COGS` w `main.py`**.
3. Włącz bota i przetestuj komendę `/botinfo`!

### Daj znać, czy mogę coś poprawić! ✅
