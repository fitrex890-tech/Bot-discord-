import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import database as db
import utils


active_giveaways: dict[int, dict] = {}


class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id: int):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id

    @discord.ui.button(
        label="🎉 Weź Udział",
        style=discord.ButtonStyle.success,
        custom_id="giveaway_join",
    )
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        gw = active_giveaways.get(self.giveaway_id)
        if not gw:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", "To giveaway już się zakończyło!", utils.LOSE_COLOR),
                ephemeral=True,
            )
            return

        user_id = interaction.user.id
        if user_id in gw["participants"]:
            gw["participants"].discard(user_id)
            await interaction.response.send_message(
                embed=utils.make_embed(
                    "🚪 Wycofano Zgłoszenie",
                    "Wycofałeś się z giveaway. Możesz dołączyć ponownie klikając przycisk.",
                    utils.NEUTRAL_COLOR,
                ),
                ephemeral=True,
            )
        else:
            gw["participants"].add(user_id)
            await interaction.response.send_message(
                embed=utils.make_embed(
                    "✅ Dołączyłeś!",
                    f"Jesteś teraz w puli losowania!\n\n"
                    f"Nagroda: **{gw['amount']:,} 💎 Crypto**\n"
                    f"Uczestników: **{len(gw['participants'])}**\n\n"
                    f"*Kliknij ponownie aby się wycofać.*",
                    utils.WIN_COLOR,
                ),
                ephemeral=True,
            )

        await _update_giveaway_embed(interaction.message, gw)


async def _update_giveaway_embed(message: discord.Message, gw: dict) -> None:
    try:
        embed = _build_embed(gw)
        await message.edit(embed=embed)
    except Exception:
        pass


def _build_embed(gw: dict) -> discord.Embed:
    ends_ts = int(gw["ends_at"].timestamp())
    embed = discord.Embed(
        title="🎉 GIVEAWAY — Crypto Casino",
        description=(
            f"**{gw['opis']}**\n\n"
            f"💎 Nagroda: **{gw['amount']:,} Crypto**\n"
            f"👑 Fundator: {gw['host']}\n"
            f"⏰ Koniec: <t:{ends_ts}:R> (<t:{ends_ts}:T>)\n"
            f"👥 Uczestników: **{len(gw['participants'])}**\n\n"
            f"Kliknij **🎉 Weź Udział** aby dołączyć!"
        ),
        color=utils.JACKPOT_COLOR,
    )
    embed.set_footer(text="Kliknij ponownie przycisk, aby się wycofać")
    embed.timestamp = gw["ends_at"]
    return embed


class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="giveaway", description="[ADMIN] Rozpocznij giveaway Crypto")
    @app_commands.describe(
        kwota="Ilość Crypto do rozdania",
        minuty="Czas trwania w minutach",
        opis="Opis giveaway (opcjonalnie)",
    )
    async def giveaway(
        self,
        interaction: discord.Interaction,
        kwota: int,
        minuty: int,
        opis: str = "Wielki Giveaway Crypto!",
    ):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Brak Uprawnień", "Tylko administratorzy mogą tworzyć giveaway!", utils.LOSE_COLOR),
                ephemeral=True,
            )
            return

        if kwota < 100:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", "Minimalna nagroda to **100 💎 Crypto**!", utils.LOSE_COLOR),
                ephemeral=True,
            )
            return

        if minuty < 1 or minuty > 10080:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", "Czas musi być od **1 do 10080 minut** (7 dni)!", utils.LOSE_COLOR),
                ephemeral=True,
            )
            return

        import datetime
        ends_at = discord.utils.utcnow() + datetime.timedelta(minutes=minuty)

        gw_id = interaction.id
        gw = {
            "id": gw_id,
            "amount": kwota,
            "opis": opis,
            "host": interaction.user.mention,
            "host_id": interaction.user.id,
            "participants": set(),
            "ends_at": ends_at,
            "channel_id": interaction.channel_id,
            "message_id": None,
        }
        active_giveaways[gw_id] = gw

        view = GiveawayView(gw_id)
        embed = _build_embed(gw)

        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        gw["message_id"] = msg.id

        self.bot.loop.create_task(self._end_giveaway(gw_id, minuty * 60, msg, view))

    async def _end_giveaway(self, gw_id: int, delay: float, message: discord.Message, view: GiveawayView):
        await asyncio.sleep(delay)

        gw = active_giveaways.pop(gw_id, None)
        if not gw:
            return

        for item in view.children:
            item.disabled = True

        if not gw["participants"]:
            embed = discord.Embed(
                title="🎉 GIVEAWAY — Zakończony",
                description=(
                    f"**{gw['opis']}**\n\n"
                    f"💎 Nagroda: **{gw['amount']:,} Crypto**\n"
                    f"😔 Brak uczestników — nikt nie wygrał!"
                ),
                color=utils.NEUTRAL_COLOR,
            )
            embed.set_footer(text="Giveaway zakończony")
            try:
                await message.edit(embed=embed, view=view)
            except Exception:
                pass
            return

        winner_id = random.choice(list(gw["participants"]))
        await db.update_balance(winner_id, gw["amount"])
        await db.log_transaction(winner_id, gw["amount"], "giveaway", f"Wygrana giveaway: {gw['opis']}")

        embed = discord.Embed(
            title="🎉 GIVEAWAY — WYNIKI!",
            description=(
                f"**{gw['opis']}**\n\n"
                f"🏆 Zwycięzca: <@{winner_id}> 🎊\n"
                f"💎 Nagroda: **{gw['amount']:,} Crypto** — już na koncie!\n"
                f"👥 Uczestników: **{len(gw['participants'])}**\n"
                f"👑 Fundator: {gw['host']}"
            ),
            color=utils.WIN_COLOR,
        )
        embed.set_footer(text="Dziękujemy za udział!")

        try:
            await message.edit(embed=embed, view=view)
            await message.reply(
                content=f"🎊 Gratulacje <@{winner_id}>! Wygrałeś **{gw['amount']:,} 💎 Crypto** w giveaway **{gw['opis']}**! 🎉"
            )
        except Exception:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaway(bot))
