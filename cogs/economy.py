import discord
from discord.ext import commands
from discord import app_commands
import random
import database as db
import utils


DAILY_AMOUNT = 500
DAILY_COOLDOWN = 86400
WORK_COOLDOWN = 3600
BEG_COOLDOWN = 300
CRIME_COOLDOWN = 7200
ROB_COOLDOWN = 3600

WORK_RESPONSES = [
    ("dostarczyłeś paczki jako kurier", (80, 250)),
    ("naprawiłeś kilka komputerów", (100, 300)),
    ("wysprzątałeś biuro", (60, 180)),
    ("pracowałeś jako barista", (90, 220)),
    ("programowałeś przez noc", (150, 400)),
    ("sprzedałeś używane rzeczy online", (70, 200)),
    ("naprawiłeś samochód sąsiada", (120, 350)),
    ("udzielałeś korepetycji", (100, 280)),
    ("grałeś na gitarze w parku", (50, 150)),
    ("zrobiłeś sesję zdjęciową", (130, 380)),
]

BEG_RESPONSES = [
    ("Miły przechodzień rzucił ci drobne", (1, 50)),
    ("Ktoś dał ci resztę z kawy", (5, 30)),
    ("Znalazłeś monetę na chodniku", (1, 20)),
    ("Pies przyniósł ci banknot w zębach", (10, 80)),
    ("Babcia z litości dała ci kilka groszy", (5, 40)),
]

CRIME_SUCCESS = [
    ("włamałeś się do bankomatu", (300, 900)),
    ("okradłeś sklep jubilerski", (400, 1200)),
    ("zhackowałeś kryptogiełdę", (500, 2000)),
    ("przemyciłeś towary przez granicę", (200, 700)),
    ("fałszowałeś dokumenty", (150, 600)),
]
CRIME_FAIL = [
    ("zostałeś złapany przez policję i zapłaciłeś grzywnę", (100, 400)),
    ("kamera nagrała twój napad i musiałeś uciec", (50, 200)),
    ("twój wspólnik doniósł na ciebie", (80, 300)),
    ("alarm się włączył i ledwo uciekłeś", (60, 250)),
]


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="balans", description="Sprawdź swój balans Crypto")
    @app_commands.describe(uzytkownik="Użytkownik (opcjonalnie)")
    async def balance(self, interaction: discord.Interaction, uzytkownik: discord.Member = None):
        target = uzytkownik or interaction.user
        user = await db.get_user(target.id)
        total = user["balance"] + user["bank"]

        embed = utils.make_embed(
            title=f"💰 Portfel — {target.display_name}",
            color=utils.INFO_COLOR,
        )
        embed.add_field(name="👜 Kieszeń", value=utils.format_currency(user["balance"]), inline=True)
        embed.add_field(name="🏦 Bank", value=utils.format_currency(user["bank"]), inline=True)
        embed.add_field(name="💎 Łącznie", value=utils.format_currency(total), inline=False)
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Odbierz dzienny bonus Crypto")
    async def daily(self, interaction: discord.Interaction):
        user = await db.get_user(interaction.user.id)
        remaining = utils.check_cooldown(user["last_daily"], DAILY_COOLDOWN)
        if remaining:
            await interaction.response.send_message(embed=utils.cooldown_embed("last_daily", remaining))
            return

        bonus = DAILY_AMOUNT + random.randint(0, 200)
        await db.update_balance(interaction.user.id, bonus)
        await db.update_cooldown(interaction.user.id, "last_daily")
        await db.log_transaction(interaction.user.id, bonus, "daily", "Dzienny bonus")

        embed = utils.make_embed(
            title="🎁 Dzienny Bonus!",
            description=f"Odebrałeś swój dzienny bonus!\n\n"
                        f"Otrzymujesz: {utils.format_currency(bonus)}\n"
                        f"Wróć jutro po kolejny bonus!",
            color=utils.WIN_COLOR,
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pracuj", description="Idź do pracy i zarób Crypto")
    async def work(self, interaction: discord.Interaction):
        user = await db.get_user(interaction.user.id)
        remaining = utils.check_cooldown(user["last_work"], WORK_COOLDOWN)
        if remaining:
            await interaction.response.send_message(embed=utils.cooldown_embed("last_work", remaining))
            return

        job, (min_pay, max_pay) = random.choice(WORK_RESPONSES)
        earned = random.randint(min_pay, max_pay)
        await db.update_balance(interaction.user.id, earned)
        await db.update_cooldown(interaction.user.id, "last_work")
        await db.log_transaction(interaction.user.id, earned, "work", job)

        embed = utils.make_embed(
            title="💼 Praca Wykonana!",
            description=f"Dzisiaj **{job}**.\n\n"
                        f"Zarobek: {utils.format_currency(earned)}\n"
                        f"Następna praca dostępna za **1 godzinę**.",
            color=utils.WIN_COLOR,
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="zebrz", description="Proś przechodniów o Crypto")
    async def beg(self, interaction: discord.Interaction):
        user = await db.get_user(interaction.user.id)
        remaining = utils.check_cooldown(user["last_beg"], BEG_COOLDOWN)
        if remaining:
            await interaction.response.send_message(embed=utils.cooldown_embed("last_beg", remaining))
            return

        desc, (min_pay, max_pay) = random.choice(BEG_RESPONSES)
        earned = random.randint(min_pay, max_pay)
        await db.update_balance(interaction.user.id, earned)
        await db.update_cooldown(interaction.user.id, "last_beg")

        embed = utils.make_embed(
            title="🙏 Żebranie",
            description=f"{desc}.\n\nOtrzymałeś: {utils.format_currency(earned)}",
            color=utils.NEUTRAL_COLOR,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="crime", description="Popełnij przestępstwo dla Crypto (ryzykowne!)")
    async def crime(self, interaction: discord.Interaction):
        user = await db.get_user(interaction.user.id)
        remaining = utils.check_cooldown(user["last_crime"], CRIME_COOLDOWN)
        if remaining:
            await interaction.response.send_message(embed=utils.cooldown_embed("last_crime", remaining))
            return

        await db.update_cooldown(interaction.user.id, "last_crime")
        success = random.random() < 0.60

        if success:
            desc, (min_pay, max_pay) = random.choice(CRIME_SUCCESS)
            earned = random.randint(min_pay, max_pay)
            await db.update_balance(interaction.user.id, earned)
            await db.log_transaction(interaction.user.id, earned, "crime", desc)
            embed = utils.make_embed(
                title="🦹 Przestępstwo Udane!",
                description=f"Udało się! {desc.capitalize()}.\n\n"
                            f"Łup: {utils.format_currency(earned)}",
                color=utils.WIN_COLOR,
            )
        else:
            desc, (min_fine, max_fine) = random.choice(CRIME_FAIL)
            fine = random.randint(min_fine, max_fine)
            user_data = await db.get_user(interaction.user.id)
            fine = min(fine, user_data["balance"])
            await db.update_balance(interaction.user.id, -fine)
            await db.log_transaction(interaction.user.id, -fine, "crime_fail", desc)
            embed = utils.make_embed(
                title="🚔 Złapany!",
                description=f"Pech! {desc.capitalize()}.\n\n"
                            f"Grzywna: {utils.format_currency(fine)}",
                color=utils.LOSE_COLOR,
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="okradnij", description="Spróbuj okraść innego użytkownika")
    @app_commands.describe(cel="Użytkownik, którego chcesz okraść")
    async def rob(self, interaction: discord.Interaction, cel: discord.Member):
        if cel.id == interaction.user.id:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", "Nie możesz okraść samego siebie!", utils.LOSE_COLOR)
            )
            return
        if cel.bot:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", "Nie możesz okraść bota!", utils.LOSE_COLOR)
            )
            return

        robber = await db.get_user(interaction.user.id)
        remaining = utils.check_cooldown(robber["last_rob"], ROB_COOLDOWN)
        if remaining:
            await interaction.response.send_message(embed=utils.cooldown_embed("last_rob", remaining))
            return

        target = await db.get_user(cel.id)
        await db.update_cooldown(interaction.user.id, "last_rob")

        if target["balance"] < 50:
            await interaction.response.send_message(
                embed=utils.make_embed(
                    "💸 Pusty portfel",
                    f"**{cel.display_name}** nie ma wystarczająco Crypto w kieszeni do kradzieży!\n"
                    f"*(Pieniądze w banku są bezpieczne)*",
                    utils.NEUTRAL_COLOR,
                )
            )
            return

        success = random.random() < 0.45
        if success:
            max_steal = int(target["balance"] * 0.30)
            stolen = random.randint(int(target["balance"] * 0.05), max(1, max_steal))
            await db.update_balance(cel.id, -stolen)
            await db.update_balance(interaction.user.id, stolen)
            await db.log_transaction(interaction.user.id, stolen, "rob", f"Okradziono {cel.id}")
            embed = utils.make_embed(
                title="🥷 Kradzież Udana!",
                description=f"Cicho podkradłeś się do **{cel.display_name}**!\n\n"
                            f"Skradzione: {utils.format_currency(stolen)}\n"
                            f"*(Pamiętaj: pieniądze w banku są bezpieczne!)*",
                color=utils.WIN_COLOR,
            )
        else:
            fine = random.randint(50, min(300, robber["balance"] if robber["balance"] > 0 else 1))
            await db.update_balance(interaction.user.id, -fine)
            embed = utils.make_embed(
                title="🚔 Złapany na Gorącym Uczynku!",
                description=f"**{cel.display_name}** złapał cię na kradzieży!\n\n"
                            f"Kara: {utils.format_currency(fine)}",
                color=utils.LOSE_COLOR,
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="wplac", description="Wpłać Crypto do banku")
    @app_commands.describe(kwota="Kwota do wpłacenia (lub 'all')")
    async def deposit(self, interaction: discord.Interaction, kwota: str):
        user = await db.get_user(interaction.user.id)
        if kwota.lower() in ("all", "wszystko"):
            amount = user["balance"]
        else:
            try:
                amount = int(kwota)
            except ValueError:
                await interaction.response.send_message(
                    embed=utils.make_embed("❌ Błąd", "Podaj prawidłową kwotę!", utils.LOSE_COLOR)
                )
                return

        if amount <= 0:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", "Kwota musi być większa od 0!", utils.LOSE_COLOR)
            )
            return
        if amount > user["balance"]:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Brak środków", f"Masz tylko {utils.format_currency(user['balance'])} w kieszeni!", utils.LOSE_COLOR)
            )
            return

        await db.update_balance(interaction.user.id, -amount)
        await db.update_bank(interaction.user.id, amount)

        embed = utils.make_embed(
            title="🏦 Wpłata do Banku",
            description=f"Wpłacono {utils.format_currency(amount)} do banku.\n"
                        f"Twoje pieniądze są teraz bezpieczne przed złodziejami!",
            color=utils.WIN_COLOR,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="wyplac", description="Wypłać Crypto z banku")
    @app_commands.describe(kwota="Kwota do wypłacenia (lub 'all')")
    async def withdraw(self, interaction: discord.Interaction, kwota: str):
        user = await db.get_user(interaction.user.id)
        if kwota.lower() in ("all", "wszystko"):
            amount = user["bank"]
        else:
            try:
                amount = int(kwota)
            except ValueError:
                await interaction.response.send_message(
                    embed=utils.make_embed("❌ Błąd", "Podaj prawidłową kwotę!", utils.LOSE_COLOR)
                )
                return

        if amount <= 0:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", "Kwota musi być większa od 0!", utils.LOSE_COLOR)
            )
            return
        if amount > user["bank"]:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Brak środków", f"Masz tylko {utils.format_currency(user['bank'])} w banku!", utils.LOSE_COLOR)
            )
            return

        await db.update_bank(interaction.user.id, -amount)
        await db.update_balance(interaction.user.id, amount)

        embed = utils.make_embed(
            title="🏦 Wypłata z Banku",
            description=f"Wypłacono {utils.format_currency(amount)} z banku do kieszeni.",
            color=utils.WIN_COLOR,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="przelej", description="Prześlij Crypto innemu użytkownikowi")
    @app_commands.describe(uzytkownik="Odbiorca", kwota="Kwota do przesłania")
    async def give(self, interaction: discord.Interaction, uzytkownik: discord.Member, kwota: int):
        if uzytkownik.id == interaction.user.id:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", "Nie możesz przelać Crypto samemu sobie!", utils.LOSE_COLOR)
            )
            return
        if uzytkownik.bot:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", "Nie możesz przelać Crypto botowi!", utils.LOSE_COLOR)
            )
            return
        if kwota <= 0:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", "Kwota musi być większa od 0!", utils.LOSE_COLOR)
            )
            return

        sender = await db.get_user(interaction.user.id)
        if kwota > sender["balance"]:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Brak środków", f"Masz tylko {utils.format_currency(sender['balance'])} w kieszeni!", utils.LOSE_COLOR)
            )
            return

        await db.update_balance(interaction.user.id, -kwota)
        await db.update_balance(uzytkownik.id, kwota)
        await db.log_transaction(interaction.user.id, -kwota, "transfer", f"Przelew do {uzytkownik.id}")
        await db.log_transaction(uzytkownik.id, kwota, "transfer", f"Przelew od {interaction.user.id}")

        embed = utils.make_embed(
            title="💸 Przelew Wykonany",
            description=f"{interaction.user.mention} przesłał {utils.format_currency(kwota)} do {uzytkownik.mention}!",
            color=utils.WIN_COLOR,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="top", description="Ranking najbogatszych użytkowników")
    @app_commands.describe(typ="Typ rankingu")
    @app_commands.choices(typ=[
        app_commands.Choice(name="💰 Bogactwo (domyślny)", value="bogactwo"),
        app_commands.Choice(name="🏆 Wygrane w grach", value="wygrane"),
    ])
    async def leaderboard(self, interaction: discord.Interaction, typ: str = "bogactwo"):
        await interaction.response.defer()

        medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7

        if typ == "bogactwo":
            top = await db.get_top_users(10)
            embed = utils.make_embed(
                title="🏆 Top 10 Najbogatszych — Crypto Casino",
                color=utils.JACKPOT_COLOR,
            )
            lines = []
            for i, u in enumerate(top):
                member = interaction.guild.get_member(u["user_id"])
                name = member.display_name if member else f"Gracz #{i+1}"
                total = u["balance"] + u["bank"]
                wins = u.get("total_wins", 0)
                games = u.get("total_games", 0)
                winrate = f"{int(wins/games*100)}%" if games > 0 else "—"
                lines.append(
                    f"{medals[i]} **{name}**\n"
                    f"╰ 💎 {total:,} Crypto  |  🎮 {games} gier  |  ✅ {winrate} wygranych"
                )
            embed.description = "\n\n".join(lines) if lines else "Brak danych."

        else:
            top = await db.get_top_winners(10)
            embed = utils.make_embed(
                title="🏆 Top 10 Graczy — Najwięcej Wygranych",
                color=utils.WIN_COLOR,
            )
            lines = []
            for i, u in enumerate(top):
                member = interaction.guild.get_member(u["user_id"])
                name = member.display_name if member else f"Gracz #{i+1}"
                wins = u["total_wins"]
                games = u["total_games"]
                biggest = u["biggest_win"]
                winrate = f"{int(wins/games*100)}%" if games > 0 else "—"
                lines.append(
                    f"{medals[i]} **{name}**\n"
                    f"╰ ✅ {wins} wygranych / {games} gier  |  🎯 {winrate}  |  🏅 Rekord: {biggest:,} 💎"
                )
            embed.description = "\n\n".join(lines) if lines else "Brak danych."

        embed.set_footer(text="Crypto Casino | /top wygrane — ranking graczy")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="statystyki", description="Wyświetl szczegółowe statystyki gier")
    @app_commands.describe(uzytkownik="Użytkownik (opcjonalnie)")
    async def stats(self, interaction: discord.Interaction, uzytkownik: discord.Member = None):
        target = uzytkownik or interaction.user
        stats = await db.get_game_stats(target.id)
        user = await db.get_user(target.id)

        total_games = stats["total_games"]
        total_wins = stats["total_wins"]
        total_losses = stats["total_losses"]
        winrate = f"{int(total_wins / total_games * 100)}%" if total_games > 0 else "—"

        embed = utils.make_embed(
            title=f"📊 Statystyki Gier — {target.display_name}",
            color=utils.INFO_COLOR,
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        embed.add_field(
            name="📈 Ogólne",
            value=(
                f"🎮 Wszystkich gier: **{total_games}**\n"
                f"✅ Wygranych: **{total_wins}**\n"
                f"❌ Przegranych: **{total_losses}**\n"
                f"🎯 Win-rate: **{winrate}**\n"
                f"🏅 Największa wygrana: **{stats['biggest_win']:,} 💎**\n"
                f"💸 Największa strata: **{stats['biggest_loss']:,} 💎**"
            ),
            inline=False,
        )

        def game_row(wins, losses, earned, lost):
            total = wins + losses
            wr = f"{int(wins/total*100)}%" if total > 0 else "—"
            net = earned - lost
            sign = "+" if net >= 0 else ""
            return (
                f"✅ {wins}W / ❌ {losses}L  |  🎯 {wr}\n"
                f"💎 Netto: **{sign}{net:,}**"
            )

        embed.add_field(
            name="🎡 Koło Fortuny (/spin)",
            value=game_row(stats["spin_wins"], stats["spin_losses"], stats["spin_earned"], stats["spin_lost"]),
            inline=True,
        )
        embed.add_field(
            name="🃏 Blackjack (/blackjack)",
            value=game_row(stats["blackjack_wins"], stats["blackjack_losses"], stats["blackjack_earned"], stats["blackjack_lost"]),
            inline=True,
        )
        embed.add_field(
            name="🎰 Automaty (/slots)",
            value=game_row(stats["slots_wins"], stats["slots_losses"], stats["slots_earned"], stats["slots_lost"]),
            inline=True,
        )
        embed.add_field(
            name="🪙 Coinflip (/coinflip)",
            value=f"✅ {stats['coinflip_wins']}W / ❌ {stats['coinflip_losses']}L",
            inline=True,
        )
        embed.add_field(
            name="🎡 Ruletka (/roulette)",
            value=f"✅ {stats['roulette_wins']}W / ❌ {stats['roulette_losses']}L",
            inline=True,
        )
        embed.add_field(
            name="💣 Miny (/mines)",
            value=f"✅ {stats['mines_wins']}W / ❌ {stats['mines_losses']}L",
            inline=True,
        )

        total = user["balance"] + user["bank"]
        embed.add_field(
            name="💰 Stan Konta",
            value=f"👜 Kieszeń: **{user['balance']:,} 💎**\n🏦 Bank: **{user['bank']:,} 💎**\n💎 Łącznie: **{total:,} 💎**",
            inline=False,
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="portfel", description="Alias do /balans")
    async def wallet(self, interaction: discord.Interaction):
        await self.balance.callback(self, interaction)


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
