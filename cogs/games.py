import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from datetime import datetime, timedelta
import database as db


# =========================
# HELPERS
# =========================
def seconds_to_str(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    parts = []
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    if s: parts.append(f"{s}s")
    return " ".join(parts) or "0s"


async def check_cooldown(user_id: int, field: str, cooldown_seconds: int) -> int | None:
    """Zwraca pozostały czas w sekundach lub None jeśli cooldown minął."""
    last = await db.get_cooldown(user_id, field)
    if not last:
        return None
    last_dt = datetime.fromisoformat(last)
    diff = (last_dt + timedelta(seconds=cooldown_seconds)) - datetime.utcnow()
    remaining = int(diff.total_seconds())
    return remaining if remaining > 0 else None


# =========================
# BLACKJACK LOGIC
# =========================
CARD_VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
    "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11
}
SUITS = ["♠", "♥", "♦", "♣"]
RANKS = list(CARD_VALUES.keys())


def new_deck():
    deck = [f"{r}{s}" for r in RANKS for s in SUITS]
    random.shuffle(deck)
    return deck


def card_value(card: str) -> int:
    rank = card[:-1]
    return CARD_VALUES[rank]


def hand_value(hand: list[str]) -> int:
    total = sum(card_value(c) for c in hand)
    aces = sum(1 for c in hand if c[:-1] == "A")
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def hand_str(hand: list[str]) -> str:
    return " ".join(f"`{c}`" for c in hand)


# =========================
# GAMES COG
# =========================
class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # 💼 PRACA
    # =========================
    @app_commands.command(name="pracuj", description="💼 Idź do pracy i zarób (cooldown: 1h)")
    async def work(self, interaction: discord.Interaction):
        remaining = await check_cooldown(interaction.user.id, "last_work", 3600)
        if remaining:
            embed = discord.Embed(
                title="⏳ Jesteś zmęczony!",
                description=f"Wróć do pracy za **{seconds_to_str(remaining)}**.",
                color=0xE74C3C
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        jobs = [
            ("📦 Rozwoziłeś paczki", 20, 80),
            ("🍔 Pracowałeś w fast foodzie", 15, 60),
            ("🧑‍💻 Programowałeś systemy", 50, 150),
            ("🚗 Jeździłeś Uberem", 30, 100),
            ("🧹 Sprzątałeś biuro", 10, 50),
            ("🏗️ Pracowałeś na budowie", 40, 120),
            ("📊 Robiłeś analizy finansowe", 60, 180),
            ("🎨 Projektowałeś grafiki", 35, 110),
        ]

        job_name, min_earn, max_earn = random.choice(jobs)
        earn = random.randint(min_earn, max_earn)

        await db.update_crypto(interaction.user.id, earn)
        await db.set_cooldown(interaction.user.id, "last_work")
        await db.log_transaction(interaction.user.id, earn, "work")

        embed = discord.Embed(
            title="💼 Praca wykonana!",
            description=f"{job_name}\n\n💰 Zarobek: **+{earn} 💎**",
            color=0x2ECC71
        )
        embed.set_footer(text="Możesz pracować ponownie za 1 godzinę")
        await interaction.response.send_message(embed=embed)

    # =========================
    # 🎁 DAILY
    # =========================
    @app_commands.command(name="daily", description="🎁 Codzienna nagroda (cooldown: 24h)")
    async def daily(self, interaction: discord.Interaction):
        remaining = await check_cooldown(interaction.user.id, "last_daily", 86400)
        if remaining:
            embed = discord.Embed(
                title="⏳ Już odebrałeś nagrodę!",
                description=f"Wróć za **{seconds_to_str(remaining)}**.",
                color=0xE74C3C
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        reward_crypto = random.randint(50, 200)
        reward_pln = random.randint(10, 50)

        await db.update_crypto(interaction.user.id, reward_crypto)
        await db.update_pln(interaction.user.id, reward_pln)
        await db.set_cooldown(interaction.user.id, "last_daily")
        await db.log_transaction(interaction.user.id, reward_crypto, "daily_crypto")
        await db.log_transaction(interaction.user.id, reward_pln, "daily_pln")

        embed = discord.Embed(
            title="🎁 Daily odebrane!",
            description=f"💎 **+{reward_crypto}** Crypto\n🇵🇱 **+{reward_pln}** PLN",
            color=0xF1C40F
        )
        embed.set_footer(text="Wróć jutro po kolejną nagrodę!")
        await interaction.response.send_message(embed=embed)

    # =========================
    # 🎰 SPIN
    # =========================
    @app_commands.command(name="spin", description="🎰 Koło fortuny")
    @app_commands.choices(level=[
        app_commands.Choice(name="Low 🟢 (bezpieczniejszy)", value="low"),
        app_commands.Choice(name="Medium 🟡 (wyważony)", value="medium"),
        app_commands.Choice(name="Hard 🔴 (ryzykowny)", value="hard"),
    ])
    async def spin(self, interaction: discord.Interaction, bet: int, level: app_commands.Choice[str]):
        if bet <= 0:
            return await interaction.response.send_message("❌ Stawka musi być większa niż 0.", ephemeral=True)

        data = await db.get_profile(interaction.user.id)
        if data["crypto"] < bet:
            return await interaction.response.send_message(
                f"❌ Za mało 💎. Masz: **{data['crypto']:,}**", ephemeral=True
            )

        await db.update_crypto(interaction.user.id, -bet)

        start = discord.Embed(
            title="🎰 Koło Fortuny",
            description=f"Kręcę kołem...\n\n💰 Stawka: **{bet:,} 💎** | Tryb: **{level.name}**",
            color=0xF1C40F
        )
        start.set_image(url="https://media.giphy.com/media/3o7aD2saalBwwftBIY/giphy.gif")
        await interaction.response.send_message(embed=start)
        msg = await interaction.original_response()

        await asyncio.sleep(3)

        wheel = [
            ("🟢", 0.5, "x0.5"),
            ("🟢", 1.0, "x1.0"),
            ("🟡", 1.5, "x1.5"),
            ("🔵", 3.0, "x3.0"),
            ("🟣", 6.0, "x6.0"),
            ("⚪", 0.0, "Brak"),
        ]

        weights_map = {
            "low":    [35, 30, 20, 10, 4, 1],
            "medium": [25, 25, 25, 15, 8, 2],
            "hard":   [15, 20, 25, 20, 15, 5],
        }
        weights = weights_map[level.value]
        color, mult, mult_label = random.choices(wheel, weights=weights)[0]

        if color == "⚪":
            embed = discord.Embed(
                title="💀 Przegrana!",
                description=f"Pech! Straciłeś **{bet:,} 💎**",
                color=0x2C3E50
            )
        else:
            win = int(bet * mult)
            await db.update_crypto(interaction.user.id, win)
            await db.log_transaction(interaction.user.id, win - bet, "spin")

            profit = win - bet
            profit_str = f"+{profit:,}" if profit >= 0 else f"{profit:,}"

            embed = discord.Embed(
                title=f"{color} Wygrana! ({mult_label})",
                description=f"Wygrałeś **{win:,} 💎**\nZysk: **{profit_str} 💎**",
                color=0x2ECC71
            )

        embed.set_footer(text=f"Stawka: {bet:,} 💎 | Tryb: {level.value}")
        await msg.edit(embed=embed)

    # =========================
    # 🃏 BLACKJACK
    # =========================
    @app_commands.command(name="blackjack", description="🃏 Zagraj w Blackjacka (prawdziwe karty!)")
    async def blackjack(self, interaction: discord.Interaction, bet: int):
        if bet <= 0:
            return await interaction.response.send_message("❌ Stawka musi być większa niż 0.", ephemeral=True)

        data = await db.get_profile(interaction.user.id)
        if data["crypto"] < bet:
            return await interaction.response.send_message(
                f"❌ Za mało 💎. Masz: **{data['crypto']:,}**", ephemeral=True
            )

        await db.update_crypto(interaction.user.id, -bet)

        deck = new_deck()
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]

        player_val = hand_value(player_hand)
        dealer_val = hand_value(dealer_hand)

        # Sprawdź blackjack
        player_bj = player_val == 21
        dealer_bj = dealer_val == 21

        if player_bj and dealer_bj:
            await db.update_crypto(interaction.user.id, bet)
            result = "🤝 REMIS — oboje macie Blackjacka!"
            color = 0xF1C40F
        elif player_bj:
            win = int(bet * 2.5)
            await db.update_crypto(interaction.user.id, win)
            await db.increment_wins(interaction.user.id)
            result = f"🎉 BLACKJACK! Wygrywasz **+{win:,} 💎**"
            color = 0x2ECC71
        elif dealer_bj:
            result = f"💀 Dealer ma Blackjacka! Tracisz **-{bet:,} 💎**"
            color = 0xE74C3C
        else:
            # Dealer dobiera do 17
            while dealer_val < 17:
                dealer_hand.append(deck.pop())
                dealer_val = hand_value(dealer_hand)

            if player_val > 21:
                result = f"💀 BUST! Przekroczyłeś 21. Tracisz **-{bet:,} 💎**"
                color = 0xE74C3C
            elif dealer_val > 21 or player_val > dealer_val:
                win = bet * 2
                await db.update_crypto(interaction.user.id, win)
                await db.increment_wins(interaction.user.id)
                await db.log_transaction(interaction.user.id, win - bet, "blackjack_win")
                result = f"🎉 WYGRANA! **+{win:,} 💎**"
                color = 0x2ECC71
            elif player_val == dealer_val:
                await db.update_crypto(interaction.user.id, bet)
                result = "🤝 REMIS — stawka zwrócona"
                color = 0xF1C40F
            else:
                await db.log_transaction(interaction.user.id, -bet, "blackjack_loss")
                result = f"💀 PRZEGRANA! Dealer wygrywa. **-{bet:,} 💎**"
                color = 0xE74C3C

        embed = discord.Embed(title="🃏 Blackjack", color=color)
        embed.add_field(
            name=f"Twoja ręka ({player_val})",
            value=hand_str(player_hand),
            inline=False
        )
        embed.add_field(
            name=f"Ręka dealera ({dealer_val})",
            value=hand_str(dealer_hand),
            inline=False
        )
        embed.add_field(name="Wynik", value=result, inline=False)
        embed.set_footer(text=f"Stawka: {bet:,} 💎")

        await interaction.response.send_message(embed=embed)

    # =========================
    # 💣 MINES
    # =========================
    @app_commands.command(name="mines", description="💣 Pole minowe — trafisz na diament?")
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="Łatwy (3 miny / 5 pól)", value="easy"),
        app_commands.Choice(name="Normalny (5 min / 8 pól)", value="normal"),
        app_commands.Choice(name="Trudny (7 min / 10 pól)", value="hard"),
    ])
    async def mines(self, interaction: discord.Interaction, bet: int, difficulty: app_commands.Choice[str] = None):
        if bet <= 0:
            return await interaction.response.send_message("❌ Stawka musi być większa niż 0.", ephemeral=True)

        data = await db.get_profile(interaction.user.id)
        if data["crypto"] < bet:
            return await interaction.response.send_message(
                f"❌ Za mało 💎. Masz: **{data['crypto']:,}**", ephemeral=True
            )

        await db.update_crypto(interaction.user.id, -bet)

        settings = {
            "easy":   {"fields": 5,  "mines": 3, "multiplier": 3.0},
            "normal": {"fields": 8,  "mines": 5, "multiplier": 5.0},
            "hard":   {"fields": 10, "mines": 7, "multiplier": 8.0},
        }
        diff_key = difficulty.value if difficulty else "easy"
        cfg = settings[diff_key]

        field = ["💣"] * cfg["mines"] + ["💎"] * (cfg["fields"] - cfg["mines"])
        random.shuffle(field)
        picked = random.choice(field)

        if picked == "💎":
            win = int(bet * cfg["multiplier"])
            await db.update_crypto(interaction.user.id, win)
            await db.log_transaction(interaction.user.id, win - bet, "mines_win")
            embed = discord.Embed(
                title="💎 SAFE! Trafiłeś diamenta!",
                description=f"Wygrana: **+{win:,} 💎** (x{cfg['multiplier']})",
                color=0x2ECC71
            )
        else:
            await db.log_transaction(interaction.user.id, -bet, "mines_loss")
            embed = discord.Embed(
                title="💣 BOOM! Trafiłeś na minę!",
                description=f"Strata: **-{bet:,} 💎**",
                color=0xE74C3C
            )

        embed.set_footer(text=f"Stawka: {bet:,} 💎 | Trudność: {diff_key}")
        await interaction.response.send_message(embed=embed)

    # =========================
    # 🪙 COINFLIP
    # =========================
    @app_commands.command(name="coinflip", description="🪙 Orzeł czy reszka")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Orzeł 🦅", value="heads"),
        app_commands.Choice(name="Reszka 🔵", value="tails"),
    ])
    async def coinflip(self, interaction: discord.Interaction, bet: int, choice: app_commands.Choice[str]):
        if bet <= 0:
            return await interaction.response.send_message("❌ Stawka musi być większa niż 0.", ephemeral=True)

        data = await db.get_profile(interaction.user.id)
        if data["crypto"] < bet:
            return await interaction.response.send_message(
                f"❌ Za mało 💎. Masz: **{data['crypto']:,}**", ephemeral=True
            )

        await db.update_crypto(interaction.user.id, -bet)

        result = random.choice(["heads", "tails"])
        result_label = "Orzeł 🦅" if result == "heads" else "Reszka 🔵"

        if choice.value == result:
            win = bet * 2
            await db.update_crypto(interaction.user.id, win)
            await db.increment_wins(interaction.user.id)
            await db.log_transaction(interaction.user.id, win - bet, "coinflip_win")
            embed = discord.Embed(
                title=f"🪙 {result_label} — WYGRANA!",
                description=f"Trafiłeś! **+{win:,} 💎**",
                color=0x2ECC71
            )
        else:
            await db.log_transaction(interaction.user.id, -bet, "coinflip_loss")
            embed = discord.Embed(
                title=f"🪙 {result_label} — PRZEGRANA!",
                description=f"Nie tym razem! **-{bet:,} 💎**",
                color=0xE74C3C
            )

        embed.set_footer(text=f"Twój wybór: {choice.name} | Wynik: {result_label} | Stawka: {bet:,} 💎")
        await interaction.response.send_message(embed=embed)

    # =========================
    # 🔫 ROB (okradnij)
    # =========================
    @app_commands.command(name="okradnij", description="🔫 Spróbuj okraść kogoś (ryzykowne!)")
    async def rob(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ Nie możesz okraść samego siebie.", ephemeral=True)
        if user.bot:
            return await interaction.response.send_message("❌ Botów nie da się okraść.", ephemeral=True)

        remaining = await check_cooldown(interaction.user.id, "last_rob", 3600)
        if remaining:
            embed = discord.Embed(
                title="⏳ Jesteś obserwowany!",
                description=f"Czekaj **{seconds_to_str(remaining)}** zanim spróbujesz ponownie.",
                color=0xE74C3C
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        victim_data = await db.get_profile(user.id)
        robber_data = await db.get_profile(interaction.user.id)

        if victim_data["crypto"] < 50:
            return await interaction.response.send_message(
                f"❌ {user.display_name} ma za mało 💎 żeby go okraść (minimum 50 💎).", ephemeral=True
            )

        await db.set_cooldown(interaction.user.id, "last_rob")

        success = random.random() < 0.45  # 45% szans na sukces

        if success:
            max_steal = min(victim_data["crypto"] // 3, 500)
            stolen = random.randint(10, max(10, max_steal))

            await db.update_crypto(user.id, -stolen)
            await db.update_crypto(interaction.user.id, stolen)
            await db.log_transaction(interaction.user.id, stolen, "rob_success")
            await db.log_transaction(user.id, -stolen, "robbed")

            embed = discord.Embed(
                title="🔫 Udany skok!",
                description=(
                    f"Okradłeś {user.mention}!\n"
                    f"💰 Zdobyłeś **{stolen:,} 💎**"
                ),
                color=0x2ECC71
            )
        else:
            # Kara za nieudany napad — tracisz losową kwotę
            fine = random.randint(20, min(100, robber_data["crypto"])) if robber_data["crypto"] >= 20 else 0
            if fine > 0:
                await db.update_crypto(interaction.user.id, -fine)
                await db.log_transaction(interaction.user.id, -fine, "rob_caught")

            embed = discord.Embed(
                title="🚔 Złapany!",
                description=(
                    f"Próba okradzenia {user.mention} się nie powiodła!\n"
                    f"💸 Zapłaciłeś karę: **{fine:,} 💎**"
                ),
                color=0xE74C3C
            )

        embed.set_footer(text="Cooldown: 1 godzina")
        await interaction.response.send_message(embed=embed)


# =========================
# SETUP
# =========================
async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))
