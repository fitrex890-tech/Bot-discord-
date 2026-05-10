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
    raise ValueError("Brak tokenu bota! Ustaw DISCORD_TOKEN.")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None,
)

COGS = [
    "cogs.economy",
    "cogs.games",
    "cogs.admin",
    "cogs.shop",
    "cogs.ranks",
    "cogs.giveaway",
    "cogs.botinfo",
]


# ==============================
# ERROR HANDLING SLASH
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
                    "Wystąpił błąd.",
                    utils.LOSE_COLOR,
                ),
                ephemeral=True,
            )
        except Exception:
            pass


# ==============================
# LOAD COGS + SYNC (POPRAWIONE)
# ==============================
async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Załadowano: {cog}")
        except Exception as e:
            print(f"❌ Błąd ładowania {cog}: {e}")


# ==============================
# START
# ==============================
async def main():
    async with bot:
        await db.init_db()

        await load_cogs()

        # 🔥 WAŻNE: sync PO załadowaniu cogów
        try:
            synced = await bot.tree.sync()
            print(f"🔄 Zsynchronizowano {len(synced)} komend slash")
        except Exception as e:
            print(f"❌ Błąd sync: {e}")

        await bot.start(TOKEN)


# ==============================
# READY EVENT
# ==============================
@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user} (ID: {bot.user.id})")
    print(f"📡 Serwery: {len(bot.guilds)}")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="💎 Crypto Casino | /botinfo",
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
