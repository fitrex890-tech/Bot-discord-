import discord
from discord.ext import commands
from discord import app_commands
import random
import database as db


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="coinflip", description="Orzeł czy reszka")
    async def coinflip(self, interaction: discord.Interaction):

        result = random.choice(["Orzeł", "Reszka"])
        await interaction.response.send_message(f"🪙 Wypadło: {result}")

async def setup(bot):
    await bot.add_cog(Games(bot))
