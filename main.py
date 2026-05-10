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
    raise ValueError("Brak tokenu bota! Ustaw zmienną środowiskową DISCORD_TOKEN.")

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
]



@bot.event
async def on_ready():
    await db.init_db()
    print(f"✅ Bot uruchomiony jako: {bot.user} (ID: {bot.user.id})")
    print(f"📡 Połączono z {len(bot.guilds)} serwerami")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Zsynchronizowano {len(synced)} komend slash")
    except Exception as e:
        print(f"❌ Błąd synchronizacji komend: {e}")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="💎 Crypto Casino | /botinfo",
        )
    )


@bot.event
async def on_guild_join(guild: discord.Guild):
    print(f"➕ Dołączono do serwera: {guild.name} (ID: {guild.id})")


@bot.event
async def on_application_command_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.errors.CommandOnCooldown):
        await interaction.response.send_message(
            embed=utils.make_embed(
                "⏳ Cooldown",
                f"Ta komenda jest na cooldownie. Spróbuj za **{error.retry_after:.1f}s**.",
                utils.LOSE_COLOR,
            ),
            ephemeral=True,
        )
    elif isinstance(error, discord.app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            embed=utils.make_embed("❌ Brak Uprawnień", "Nie masz uprawnień do tej komendy!", utils.LOSE_COLOR),
            ephemeral=True,
        )
    else:
        print(f"❌ Błąd komendy: {error}")
        try:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", "Wystąpił nieoczekiwany błąd. Spróbuj ponownie.", utils.LOSE_COLOR),
                ephemeral=True,
            )
        except Exception:
            pass


async def main():
    async with bot:
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                print(f"✅ Załadowano: {cog}")
            except Exception as e:
                print(f"❌ Błąd ładowania {cog}: {e}")
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
