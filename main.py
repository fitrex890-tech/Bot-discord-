import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
import database as db
import utils

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("Brak tokenu DISCORD_TOKEN!")

# ==============================
# INTENTS
# ==============================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# ==============================
# BOT
# ==============================
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None,
    application_id=1502958498890256504  # <- TWOJE ID
)

# ==============================
# COGS
# ==============================
COGS = [
    "cogs.economy",
    "cogs.games",
    "cogs.admin",
    "cogs.shop",
    "cogs.ranks",
    "cogs.giveaway",
    "cogs.botinfo",
    "cogs.help",
]

# ==============================
# LOAD COGS
# ==============================
async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Załadowano: {cog}")
        except Exception as e:
            print(f"❌ Błąd ładowania {cog}: {e}")

# ==============================
# ON READY
# ==============================
@bot.event
async def on_ready():
    await db.init_db()

    print(f"✅ Bot uruchomiony jako: {bot.user}")
    print(f"📡 Serwery: {len(bot.guilds)}")

    try:
        synced = await bot.tree.sync()
        print(f"🔄 Zsynchronizowano {len(synced)} komend slash")
    except Exception as e:
        print(f"❌ Błąd sync: {e}")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="💎 Crypto Casino | /pomoc",
        )
    )

# ==============================
# ERROR HANDLER SLASH
# ==============================
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):

    if isinstance(error, discord.app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            embed=utils.make_embed(
                "⏳ Cooldown",
                f"Poczekaj {error.retry_after:.1f}s",
                utils.LOSE_COLOR,
            ),
            ephemeral=True,
        )

    elif isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message(
            embed=utils.make_embed(
                "❌ Brak uprawnień",
                "Nie masz uprawnień do tej komendy!",
                utils.LOSE_COLOR,
            ),
            ephemeral=True,
        )

    else:
        print(f"❌ Błąd komendy: {error}")
        try:
            await interaction.response.send_message(
                embed=utils.make_embed(
                    "❌ Błąd",
                    "Wystąpił nieoczekiwany błąd.",
                    utils.LOSE_COLOR,
                ),
                ephemeral=True,
            )
        except Exception:
            pass

# ==============================
# MAIN START
# ==============================
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    asyncio.run(main())
