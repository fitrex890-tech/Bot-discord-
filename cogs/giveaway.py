import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
from datetime import timedelta
import database as db
import utils

# Aktywne giveawaye: gw_id -> dict
active_giveaways: dict[int, dict] = {}


# =========================
# HELPERS
# =========================
def parse_time(time_str: str) -> int | None:
    """
    Parsuje czas w formacie: '10m', '2h', '1d', '1d12h', '90m', '2h30m'.
    Zwraca sekundy lub None jeśli błędny format.
    """
    time_str = time_str.lower().strip()
    total = 0
    current = ""
    for ch in time_str:
        if ch.isdigit():
            current += ch
        elif ch == "d" and current:
            total += int(current) * 86400
            current = ""
        elif ch == "h" and current:
            total += int(current) * 3600
            current = ""
        elif ch == "m" and current:
            total += int(current) * 60
            current = ""
        else:
            return None
    return total if total > 0 else None


def format_duration(seconds: int) -> str:
    d = seconds // 86400
    h = (seconds % 86400) // 3600
    m = (seconds % 3600) // 60
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    return " ".join(parts) or "< 1m"


def _build_embed(gw: dict) -> discord.Embed:
    ends_ts = int(gw["ends_at"].timestamp())
    winners_txt = f"{gw['winners']} zwycięzc{'ę' if gw['winners'] == 1 else 'ów'}"

    embed = discord.Embed(
        title="🎉 GIVEAWAY — Crypto Casino",
        description=(
            f"## {gw['opis']}\n\n"
            f"💎 **Nagroda:** {gw['amount']:,} Crypto\n"
            f"🏆 **Zwycięzców:** {winners_txt}\n"
            f"👑 **Fundator:** {gw['host']}\n"
            f"⏰ **Koniec:** <t:{ends_ts}:R> (<t:{ends_ts}:F>)\n"
            f"👥 **Uczestników:** {len(gw['participants'])}\n\n"
            f"Kliknij **🎉 Weź Udział** aby dołączyć!"
        ),
        color=utils.JACKPOT_COLOR,
    )
    embed.set_footer(text="Kliknij ponownie aby się wycofać")
    embed.timestamp = gw["ends_at"]
    return embed


async def _update_embed(message: discord.Message, gw: dict):
    try:
        await message.edit(embed=_build_embed(gw))
    except Exception:
        pass


# =========================
# VIEW — przycisk dołączania
# =========================
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
            return await interaction.response.send_message(
                embed=utils.make_embed("❌ Zakończone", "To giveaway już się zakończyło!", utils.LOSE_COLOR),
                ephemeral=True,
            )

        uid = interaction.user.id
        if uid in gw["participants"]:
            gw["participants"].discard(uid)
            await interaction.response.send_message(
                embed=utils.make_embed(
                    "🚪 Wycofano",
                    "Wycofałeś się z giveaway.\n*Kliknij ponownie aby wrócić.*",
                    utils.NEUTRAL_COLOR,
                ),
                ephemeral=True,
            )
        else:
            gw["participants"].add(uid)
            await interaction.response.send_message(
                embed=utils.make_embed(
                    "✅ Dołączyłeś!",
                    f"Jesteś w puli losowania!\n\n"
                    f"💎 Nagroda: **{gw['amount']:,} Crypto**\n"
                    f"🏆 Zwycięzców: **{gw['winners']}**\n"
                    f"👥 Uczestników: **{len(gw['participants'])}**\n\n"
                    f"*Kliknij ponownie aby się wycofać.*",
                    utils.WIN_COLOR,
                ),
                ephemeral=True,
            )

        await _update_embed(interaction.message, gw)


# =========================
# COG
# =========================
class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =========================
    # /giveaway
    # =========================
    @app_commands.command(name="giveaway", description="[ADMIN] Rozpocznij giveaway Crypto")
    @app_commands.describe(
        kwota="Ilość Crypto do rozdania",
        czas="Czas trwania: np. '30m', '2h', '1d', '1d12h'",
        zwyciezcy="Liczba zwycięzców (domyślnie 1)",
        opis="Opis giveaway",
    )
    async def giveaway(
        self,
        interaction: discord.Interaction,
        kwota: int,
        czas: str,
        zwyciezcy: int = 1,
        opis: str = "Wielki Giveaway Crypto!",
    ):
        # Uprawnienia
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                embed=utils.make_embed("❌ Brak Uprawnień", "Tylko administratorzy mogą tworzyć giveaway!", utils.LOSE_COLOR),
                ephemeral=True,
            )

        # Walidacja kwoty
        if kwota < 100:
            return await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", "Minimalna nagroda to **100 💎**!", utils.LOSE_COLOR),
                ephemeral=True,
            )

        # Walidacja czasu
        seconds = parse_time(czas)
        if not seconds or seconds < 60 or seconds > 7 * 86400:
            return await interaction.response.send_message(
                embed=utils.make_embed(
                    "❌ Błędny czas",
                    "Podaj czas w formacie: `30m`, `2h`, `1d`, `1d12h`.\n"
                    "Minimum: **1m** | Maksimum: **7d**",
                    utils.LOSE_COLOR,
                ),
                ephemeral=True,
            )

        # Walidacja zwycięzców
        if zwyciezcy < 1 or zwyciezcy > 20:
            return await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", "Liczba zwycięzców: od **1** do **20**.", utils.LOSE_COLOR),
                ephemeral=True,
            )

        import discord.utils as dutils
        ends_at = dutils.utcnow() + timedelta(seconds=seconds)

        gw_id = interaction.id
        gw = {
            "id": gw_id,
            "amount": kwota,
            "opis": opis,
            "host": interaction.user.mention,
            "host_id": interaction.user.id,
            "participants": set(),
            "ends_at": ends_at,
            "winners": zwyciezcy,
            "channel_id": interaction.channel_id,
            "message_id": None,
            "duration_str": format_duration(seconds),
        }
        active_giveaways[gw_id] = gw

        view = GiveawayView(gw_id)
        await interaction.response.send_message(embed=_build_embed(gw), view=view)
        msg = await interaction.original_response()
        gw["message_id"] = msg.id

        self.bot.loop.create_task(self._end_giveaway(gw_id, seconds, msg, view))

    # =========================
    # /reroll — nowe losowanie
    # =========================
    @app_commands.command(name="reroll", description="[ADMIN] Losuj nowego zwycięzcę ostatniego giveaway")
    @app_commands.describe(message_id="ID wiadomości giveaway")
    async def reroll(self, interaction: discord.Interaction, message_id: str):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                embed=utils.make_embed("❌ Brak Uprawnień", "Tylko administratorzy!", utils.LOSE_COLOR),
                ephemeral=True,
            )

        # Szukaj zakończonego giveaway po message_id w historii (uproszczone)
        await interaction.response.send_message(
            embed=utils.make_embed(
                "🔄 Reroll",
                f"Nowe losowanie dla wiadomości `{message_id}`.\n"
                f"*Aby to działało w pełni, zachowaj listę uczestników w bazie danych.*",
                utils.INFO_COLOR,
            )
        )

    # =========================
    # Kończenie giveaway
    # =========================
    async def _end_giveaway(self, gw_id: int, delay: float, message: discord.Message, view: GiveawayView):
        await asyncio.sleep(delay)

        gw = active_giveaways.pop(gw_id, None)
        if not gw:
            return

        # Wyłącz przycisk
        for item in view.children:
            item.disabled = True

        participants = list(gw["participants"])

        # Brak uczestników
        if not participants:
            embed = discord.Embed(
                title="🎉 GIVEAWAY — Zakończony",
                description=(
                    f"## {gw['opis']}\n\n"
                    f"😔 Nikt nie dołączył — brak zwycięzców."
                ),
                color=utils.NEUTRAL_COLOR,
            )
            embed.set_footer(text="Giveaway zakończony")
            try:
                await message.edit(embed=embed, view=view)
            except Exception:
                pass
            return

        # Losowanie (max tylu zwycięzców ilu uczestników)
        count = min(gw["winners"], len(participants))
        winners = random.sample(participants, count)

        # Wypłata i DM dla każdego zwycięzcy
        reward_each = gw["amount"] // count
        dm_errors = []

        for w_id in winners:
            await db.update_balance(w_id, reward_each)
            await db.log_transaction(
                w_id, reward_each, "giveaway",
                f"Wygrana giveaway: {gw['opis']}"
            )
            # DM do zwycięzcy
            try:
                user_obj = message.guild.get_member(w_id)
                if user_obj:
                    dm_embed = utils.make_embed(
                        title="🎉 Wygrałeś Giveaway!",
                        description=(
                            f"Wygrałeś **{reward_each:,} 💎 Crypto** w giveaway:\n"
                            f"**{gw['opis']}**\n\n"
                            f"Nagroda jest już na Twoim koncie! 🥳"
                        ),
                        color=utils.WIN_COLOR,
                    )
                    await user_obj.send(embed=dm_embed)
            except Exception:
                dm_errors.append(w_id)

        # Buduj embed wyników
        winners_mentions = "\n".join(f"🏆 <@{w}>" for w in winners)
        dm_note = "\n⚠️ *Nie udało się wysłać DM do niektórych zwycięzców.*" if dm_errors else ""

        embed = discord.Embed(
            title="🎉 GIVEAWAY — WYNIKI!",
            description=(
                f"## {gw['opis']}\n\n"
                f"{winners_mentions}\n\n"
                f"💎 **Nagroda na osobę:** {reward_each:,} Crypto\n"
                f"👥 **Uczestników:** {len(participants)}\n"
                f"👑 **Fundator:** {gw['host']}"
                f"{dm_note}"
            ),
            color=utils.WIN_COLOR,
        )
        embed.set_footer(text="Dziękujemy za udział!")

        try:
            await message.edit(embed=embed, view=view)
            winners_ping = " ".join(f"<@{w}>" for w in winners)
            await message.reply(
                content=f"🎊 Gratulacje {winners_ping}! "
                        f"Wygraliście **{reward_each:,} 💎 Crypto** w giveaway **{gw['opis']}**! 🎉"
            )
        except Exception:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaway(bot))

