import discord
from discord.ext import commands
from discord import app_commands
import database as db


def format_balance(amount: int, symbol: str) -> str:
    return f"**{amount:,}** {symbol}"


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # 👤 PROFIL
    # =========================
    @app_commands.command(name="profil", description="👤 Wyświetl swój profil ekonomiczny")
    async def profil(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user
        data = await db.get_profile(user.id)

        total = data["crypto"] + data["pln"] + data["bank_crypto"] + data["bank_pln"]

        embed = discord.Embed(
            title=f"👤 Profil — {user.display_name}",
            color=0x00D4FF
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="💎 Crypto", value=format_balance(data["crypto"], "💎"), inline=True)
        embed.add_field(name="🇵🇱 PLN", value=format_balance(data["pln"], "PLN"), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="🏦 Bank 💎", value=format_balance(data["bank_crypto"], "💎"), inline=True)
        embed.add_field(name="🏦 Bank PLN", value=format_balance(data["bank_pln"], "PLN"), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="📊 Łączna wartość", value=format_balance(total, "💎+PLN"), inline=False)
        embed.add_field(name="🏆 Wygrane", value=str(data["wins"]), inline=True)
        embed.set_footer(text=f"ID: {user.id}")

        await interaction.response.send_message(embed=embed)

    # =========================
    # 💰 BALANS
    # =========================
    @app_commands.command(name="balans", description="💰 Sprawdź saldo")
    async def balans(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user
        data = await db.get_profile(user.id)

        embed = discord.Embed(
            title=f"💰 Saldo — {user.display_name}",
            color=0xF1C40F
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="💎 Crypto", value=format_balance(data["crypto"], "💎"), inline=True)
        embed.add_field(name="🇵🇱 PLN", value=format_balance(data["pln"], "PLN"), inline=True)
        embed.add_field(name="🏦 Bank 💎", value=format_balance(data["bank_crypto"], "💎"), inline=True)
        embed.add_field(name="🏦 Bank PLN", value=format_balance(data["bank_pln"], "PLN"), inline=True)

        await interaction.response.send_message(embed=embed)

    # =========================
    # 💸 PRZELEW
    # =========================
    @app_commands.command(name="przelej", description="💸 Przelej pieniądze innemu użytkownikowi")
    @app_commands.choices(currency=[
        app_commands.Choice(name="Crypto 💎", value="crypto"),
        app_commands.Choice(name="PLN 🇵🇱", value="pln")
    ])
    async def przelej(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        amount: int,
        currency: app_commands.Choice[str]
    ):
        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ Nie możesz przelać pieniędzy samemu sobie.", ephemeral=True)

        if user.bot:
            return await interaction.response.send_message("❌ Nie możesz przelać pieniędzy botowi.", ephemeral=True)

        if amount <= 0:
            return await interaction.response.send_message("❌ Kwota musi być większa niż 0.", ephemeral=True)

        data = await db.get_profile(interaction.user.id)

        if currency.value == "crypto":
            if data["crypto"] < amount:
                return await interaction.response.send_message(
                    f"❌ Nie masz wystarczająco 💎. Masz: **{data['crypto']:,}**", ephemeral=True
                )
            await db.update_crypto(interaction.user.id, -amount)
            await db.update_crypto(user.id, amount)
            symbol = "💎"
        else:
            if data["pln"] < amount:
                return await interaction.response.send_message(
                    f"❌ Nie masz wystarczająco PLN. Masz: **{data['pln']:,}**", ephemeral=True
                )
            await db.update_pln(interaction.user.id, -amount)
            await db.update_pln(user.id, amount)
            symbol = "🇵🇱 PLN"

        await db.log_transaction(interaction.user.id, -amount, f"transfer_out_{currency.value}")
        await db.log_transaction(user.id, amount, f"transfer_in_{currency.value}")

        embed = discord.Embed(
            title="💸 Przelew zakończony!",
            description=(
                f"{interaction.user.mention} wysłał do {user.mention}\n"
                f"💰 **{amount:,}** {symbol}"
            ),
            color=0x2ECC71
        )
        embed.set_footer(text="Transakcja zarejestrowana")

        await interaction.response.send_message(embed=embed)

    # =========================
    # 🏦 DEPOSIT
    # =========================
    @app_commands.command(name="deposit", description="🏦 Wpłać środki do banku")
    @app_commands.choices(currency=[
        app_commands.Choice(name="Crypto 💎", value="crypto"),
        app_commands.Choice(name="PLN 🇵🇱", value="pln")
    ])
    async def deposit(self, interaction: discord.Interaction, amount: int, currency: app_commands.Choice[str]):
        if amount <= 0:
            return await interaction.response.send_message("❌ Kwota musi być większa niż 0.", ephemeral=True)

        data = await db.get_profile(interaction.user.id)

        if currency.value == "crypto":
            if data["crypto"] < amount:
                return await interaction.response.send_message(
                    f"❌ Nie masz wystarczająco 💎. Masz: **{data['crypto']:,}**", ephemeral=True
                )
            await db.update_crypto(interaction.user.id, -amount)
            await db.update_bank_crypto(interaction.user.id, amount)
            symbol = "💎"
        else:
            if data["pln"] < amount:
                return await interaction.response.send_message(
                    f"❌ Nie masz wystarczająco PLN. Masz: **{data['pln']:,}**", ephemeral=True
                )
            await db.update_pln(interaction.user.id, -amount)
            await db.update_bank_pln(interaction.user.id, amount)
            symbol = "🇵🇱 PLN"

        await db.log_transaction(interaction.user.id, amount, f"deposit_{currency.value}")

        embed = discord.Embed(
            title="🏦 Wpłata zakończona!",
            description=f"Wpłacono **{amount:,}** {symbol} do banku.\n🔒 Środki w banku są bezpieczne przed kradzieżą.",
            color=0x3498DB
        )
        await interaction.response.send_message(embed=embed)

    # =========================
    # 💳 WITHDRAW
    # =========================
    @app_commands.command(name="withdraw", description="🏦 Wypłać środki z banku")
    @app_commands.choices(currency=[
        app_commands.Choice(name="Crypto 💎", value="crypto"),
        app_commands.Choice(name="PLN 🇵🇱", value="pln")
    ])
    async def withdraw(self, interaction: discord.Interaction, amount: int, currency: app_commands.Choice[str]):
        if amount <= 0:
            return await interaction.response.send_message("❌ Kwota musi być większa niż 0.", ephemeral=True)

        data = await db.get_profile(interaction.user.id)

        if currency.value == "crypto":
            if data["bank_crypto"] < amount:
                return await interaction.response.send_message(
                    f"❌ Nie masz wystarczająco w banku. Masz: **{data['bank_crypto']:,} 💎**", ephemeral=True
                )
            await db.update_bank_crypto(interaction.user.id, -amount)
            await db.update_crypto(interaction.user.id, amount)
            symbol = "💎"
        else:
            if data["bank_pln"] < amount:
                return await interaction.response.send_message(
                    f"❌ Nie masz wystarczająco w banku. Masz: **{data['bank_pln']:,} PLN**", ephemeral=True
                )
            await db.update_bank_pln(interaction.user.id, -amount)
            await db.update_pln(interaction.user.id, amount)
            symbol = "🇵🇱 PLN"

        await db.log_transaction(interaction.user.id, amount, f"withdraw_{currency.value}")

        embed = discord.Embed(
            title="💸 Wypłata zakończona!",
            description=f"Wypłacono **{amount:,}** {symbol} z banku.",
            color=0xE67E22
        )
        await interaction.response.send_message(embed=embed)

    # =========================
    # 🏆 LEADERBOARD
    # =========================
    @app_commands.command(name="top", description="🏆 Ranking najbogatszych graczy")
    async def top(self, interaction: discord.Interaction):
        await interaction.response.defer()

        rows = await db.get_leaderboard(10)

        embed = discord.Embed(
            title="🏆 Ranking Ekonomiczny",
            description="Top 10 najbogatszych graczy na serwerze",
            color=0xF1C40F
        )

        medals = ["🥇", "🥈", "🥉"]

        for i, row in enumerate(rows):
            medal = medals[i] if i < 3 else f"`{i+1}.`"
            try:
                member = interaction.guild.get_member(row["user_id"])
                name = member.display_name if member else f"Użytkownik #{row['user_id']}"
            except Exception:
                name = f"Użytkownik #{row['user_id']}"

            total = row["total"]
            embed.add_field(
                name=f"{medal} {name}",
                value=f"💰 **{total:,}** łącznie",
                inline=False
            )

        if not rows:
            embed.description = "Brak danych. Nikt jeszcze nie zarobił żadnych środków!"

        await interaction.followup.send(embed=embed)

    # =========================
    # 📜 HISTORIA
    # =========================
    @app_commands.command(name="historia", description="📜 Historia ostatnich transakcji")
    async def historia(self, interaction: discord.Interaction):
        transactions = await db.get_transactions(interaction.user.id, 10)

        embed = discord.Embed(
            title="📜 Historia transakcji",
            color=0x9B59B6
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        if not transactions:
            embed.description = "Brak transakcji do wyświetlenia."
        else:
            lines = []
            for t in transactions:
                sign = "+" if t["amount"] > 0 else ""
                date = t["created_at"][:10]
                lines.append(f"`{date}` | `{t['type']}` | **{sign}{t['amount']:,}**")
            embed.description = "\n".join(lines)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Economy(bot))
