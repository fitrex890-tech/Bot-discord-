import discord
from discord.ext import commands
from discord import app_commands
import database as db
import utils


# =========================
# ADMIN CHECK
# =========================
def is_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            raise app_commands.CheckFailure("Brak uprawnień administratora.")
        return True
    return app_commands.check(predicate)


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =========================
    # ERROR HANDLER
    # =========================
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Brak Uprawnień", "Tylko administratorzy mogą używać tej komendy!", utils.LOSE_COLOR),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", str(error), utils.LOSE_COLOR),
                ephemeral=True,
            )

    # =========================
    # /dodaj — dodaj crypto
    # =========================
    @app_commands.command(name="dodaj", description="[ADMIN] Dodaj 💎 Crypto graczowi")
    @app_commands.describe(user="Gracz", kwota="Ilość do dodania")
    @is_admin()
    async def dodaj(self, interaction: discord.Interaction, user: discord.Member, kwota: int):
        if kwota <= 0:
            return await interaction.response.send_message("❌ Kwota musi być > 0", ephemeral=True)

        data_before = await db.get_profile(user.id)
        await db.update_crypto(user.id, kwota)
        await db.log_transaction(user.id, kwota, "admin_add", f"Dodano przez {interaction.user}")

        embed = utils.make_embed(
            title="✅ Dodano Crypto",
            description=(
                f"👤 Gracz: {user.mention}\n"
                f"➕ Dodano: **{kwota:,} 💎**\n"
                f"💰 Było: **{data_before['crypto']:,} 💎**\n"
                f"💎 Jest teraz: **{data_before['crypto'] + kwota:,} 💎**"
            ),
            color=utils.WIN_COLOR,
        )
        embed.set_footer(text=f"Admin: {interaction.user}")
        await interaction.response.send_message(embed=embed)

    # =========================
    # /usun — usuń crypto
    # =========================
    @app_commands.command(name="usun", description="[ADMIN] Usuń 💎 Crypto graczowi")
    @app_commands.describe(user="Gracz", kwota="Ilość do usunięcia")
    @is_admin()
    async def usun(self, interaction: discord.Interaction, user: discord.Member, kwota: int):
        if kwota <= 0:
            return await interaction.response.send_message("❌ Kwota musi być > 0", ephemeral=True)

        data_before = await db.get_profile(user.id)
        if data_before["crypto"] < kwota:
            return await interaction.response.send_message(
                embed=utils.make_embed(
                    "⚠️ Za Mało Środków",
                    f"{user.mention} ma tylko **{data_before['crypto']:,} 💎**, a chcesz usunąć **{kwota:,} 💎**.\n"
                    f"Usunięto dostępne środki: **{data_before['crypto']:,} 💎**.",
                    utils.NEUTRAL_COLOR,
                ),
                ephemeral=True,
            )

        await db.update_crypto(user.id, -kwota)
        await db.log_transaction(user.id, -kwota, "admin_remove", f"Usunięto przez {interaction.user}")

        embed = utils.make_embed(
            title="❌ Usunięto Crypto",
            description=(
                f"👤 Gracz: {user.mention}\n"
                f"➖ Usunięto: **{kwota:,} 💎**\n"
                f"💰 Było: **{data_before['crypto']:,} 💎**\n"
                f"💎 Jest teraz: **{data_before['crypto'] - kwota:,} 💎**"
            ),
            color=utils.LOSE_COLOR,
        )
        embed.set_footer(text=f"Admin: {interaction.user}")
        await interaction.response.send_message(embed=embed)

    # =========================
    # /set — ustaw balans
    # =========================
    @app_commands.command(name="set", description="[ADMIN] Ustaw dokładne saldo gracza")
    @app_commands.describe(user="Gracz", kwota="Nowe saldo")
    @is_admin()
    async def set_balance(self, interaction: discord.Interaction, user: discord.Member, kwota: int):
        if kwota < 0:
            return await interaction.response.send_message("❌ Saldo nie może być < 0", ephemeral=True)

        data = await db.get_profile(user.id)
        diff = kwota - data["crypto"]
        await db.update_crypto(user.id, diff)
        await db.log_transaction(user.id, diff, "admin_set", f"Ustawiono przez {interaction.user}")

        embed = utils.make_embed(
            title="⚙️ Ustawiono Saldo",
            description=(
                f"👤 Gracz: {user.mention}\n"
                f"💰 Było: **{data['crypto']:,} 💎**\n"
                f"💎 Teraz: **{kwota:,} 💎**\n"
                f"{'➕' if diff >= 0 else '➖'} Różnica: **{diff:+,} 💎**"
            ),
            color=utils.INFO_COLOR,
        )
        embed.set_footer(text=f"Admin: {interaction.user}")
        await interaction.response.send_message(embed=embed)

    # =========================
    # /reset — reset całego konta
    # =========================
    @app_commands.command(name="reset", description="[ADMIN] Zresetuj całe konto gracza do zera")
    @app_commands.describe(user="Gracz do zresetowania")
    @is_admin()
    async def reset(self, interaction: discord.Interaction, user: discord.Member):

        # Potwierdzenie przez View
        view = ConfirmResetView(interaction.user.id, user)
        await interaction.response.send_message(
            embed=utils.make_embed(
                "⚠️ Potwierdzenie",
                f"Czy na pewno chcesz **zresetować całe konto** {user.mention}?\n\n"
                f"Usunie: crypto, PLN, bank, wygrane.\n"
                f"**Ta akcja jest nieodwracalna!**",
                utils.NEUTRAL_COLOR,
            ),
            view=view,
            ephemeral=True,
        )

    # =========================
    # /addpln — dodaj PLN
    # =========================
    @app_commands.command(name="addpln", description="[ADMIN] Dodaj PLN graczowi")
    @app_commands.describe(user="Gracz", kwota="Ilość PLN")
    @is_admin()
    async def addpln(self, interaction: discord.Interaction, user: discord.Member, kwota: int):
        if kwota <= 0:
            return await interaction.response.send_message("❌ Kwota musi być > 0", ephemeral=True)

        await db.update_pln(user.id, kwota)
        await db.log_transaction(user.id, kwota, "admin_add_pln", f"Dodano PLN przez {interaction.user}")

        await interaction.response.send_message(
            embed=utils.make_embed(
                "✅ Dodano PLN",
                f"{user.mention} otrzymał **+{kwota:,} 🇵🇱 PLN**",
                utils.WIN_COLOR,
            )
        )

    # =========================
    # /info — info o graczu
    # =========================
    @app_commands.command(name="info", description="[ADMIN] Szczegółowe info o koncie gracza")
    @app_commands.describe(user="Gracz")
    @is_admin()
    async def info(self, interaction: discord.Interaction, user: discord.Member):
        data = await db.get_profile(user.id)
        transactions = await db.get_transactions(user.id, 5)

        total = data.get("crypto", 0) + data.get("pln", 0) + data.get("bank_crypto", 0) + data.get("bank_pln", 0)

        embed = utils.make_embed(
            title=f"🔍 Info — {user.display_name}",
            color=utils.INFO_COLOR,
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="💎 Crypto", value=f"{data.get('crypto', 0):,}", inline=True)
        embed.add_field(name="🇵🇱 PLN", value=f"{data.get('pln', 0):,}", inline=True)
        embed.add_field(name="🏦 Bank 💎", value=f"{data.get('bank_crypto', 0):,}", inline=True)
        embed.add_field(name="🏦 Bank PLN", value=f"{data.get('bank_pln', 0):,}", inline=True)
        embed.add_field(name="🏆 Wygrane", value=str(data.get("wins", 0)), inline=True)
        embed.add_field(name="📊 Łącznie", value=f"**{total:,}**", inline=True)

        if transactions:
            lines = []
            for t in transactions:
                sign = "+" if t["amount"] > 0 else ""
                date = t["created_at"][:10]
                note = f" ({t['note']})" if t.get("note") else ""
                lines.append(f"`{date}` {sign}{t['amount']:,} — `{t['type']}`{note}")
            embed.add_field(name="📜 Ostatnie transakcje", value="\n".join(lines), inline=False)

        embed.add_field(name="🆔 ID", value=str(user.id), inline=True)
        embed.add_field(name="📅 Konto od", value=data.get("created_at", "?")[:10], inline=True)

        await interaction.response.send_message(embed=embed)


# =========================
# CONFIRM RESET VIEW
# =========================
class ConfirmResetView(discord.ui.View):
    def __init__(self, admin_id: int, target: discord.Member):
        super().__init__(timeout=30)
        self.admin_id = admin_id
        self.target = target

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.admin_id

    @discord.ui.button(label="✅ Tak, resetuj", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = await db.get_profile(self.target.id)

        await db.update_crypto(self.target.id, -data.get("crypto", 0))
        await db.update_pln(self.target.id, -data.get("pln", 0))
        await db.update_bank_crypto(self.target.id, -data.get("bank_crypto", 0))
        await db.update_bank_pln(self.target.id, -data.get("bank_pln", 0))
        await db.log_transaction(self.target.id, 0, "admin_reset", f"Reset przez {interaction.user}")

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            embed=utils.make_embed(
                "🧨 Konto Zresetowane",
                f"Konto {self.target.mention} zostało zresetowane do zera.",
                utils.NEUTRAL_COLOR,
            ),
            view=self,
        )

    @discord.ui.button(label="❌ Anuluj", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            embed=utils.make_embed("✅ Anulowano", "Reset anulowany.", utils.NEUTRAL_COLOR),
            view=self,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
