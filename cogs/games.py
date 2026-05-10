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
    last = await db.get_cooldown(user_id, field)
    if not last:
        return None
    last_dt = datetime.fromisoformat(last)
    diff = (last_dt + timedelta(seconds=cooldown_seconds)) - datetime.utcnow()
    remaining = int(diff.total_seconds())
    return remaining if remaining > 0 else None


# =========================
# WHEEL CONFIG
# Każdy level ma inne segmenty z wagami (weight = szansa)
# Odpowiada dokładnie wizualnemu kołu z aplikacji
# =========================
WHEEL = {
    "low": [
        {"mult": 0.00, "color": "⬜", "label": "0.00x", "weight": 10},
        {"mult": 1.20, "color": "🔵", "label": "1.20x", "weight": 45},
        {"mult": 1.20, "color": "🔵", "label": "1.20x", "weight": 45},
        {"mult": 1.50, "color": "🟢", "label": "1.50x", "weight": 30},
        {"mult": 1.50, "color": "🟢", "label": "1.50x", "weight": 30},
        {"mult": 0.00, "color": "⬜", "label": "0.00x", "weight": 10},
        {"mult": 1.20, "color": "🔵", "label": "1.20x", "weight": 45},
        {"mult": 1.50, "color": "🟢", "label": "1.50x", "weight": 30},
        {"mult": 0.00, "color": "⬜", "label": "0.00x", "weight": 8},
        {"mult": 1.20, "color": "🔵", "label": "1.20x", "weight": 45},
    ],
    "medium": [
        {"mult": 0.00, "color": "⬜", "label": "0.00x", "weight": 15},
        {"mult": 1.50, "color": "🟢", "label": "1.50x", "weight": 25},
        {"mult": 1.90, "color": "🟠", "label": "1.90x", "weight": 20},
        {"mult": 2.00, "color": "🔵", "label": "2.00x", "weight": 15},
        {"mult": 0.00, "color": "⬜", "label": "0.00x", "weight": 15},
        {"mult": 3.00, "color": "🟣", "label": "3.00x", "weight": 8},
        {"mult": 1.50, "color": "🟢", "label": "1.50x", "weight": 25},
        {"mult": 1.90, "color": "🟠", "label": "1.90x", "weight": 20},
        {"mult": 0.00, "color": "⬜", "label": "0.00x", "weight": 15},
        {"mult": 2.00, "color": "🔵", "label": "2.00x", "weight": 15},
    ],
    "hard": [
        {"mult": 0.00, "color": "⬜", "label": "0.00x",  "weight": 35},
        {"mult": 2.00, "color": "🔵", "label": "2.00x",  "weight": 20},
        {"mult": 0.00, "color": "⬜", "label": "0.00x",  "weight": 35},
        {"mult": 3.00, "color": "🟣", "label": "3.00x",  "weight": 12},
        {"mult": 0.00, "color": "⬜", "label": "0.00x",  "weight": 35},
        {"mult": 5.00, "color": "🟡", "label": "5.00x",  "weight": 6},
        {"mult": 0.00, "color": "⬜", "label": "0.00x",  "weight": 35},
        {"mult": 10.0, "color": "🔴", "label": "10.0x",  "weight": 2},
        {"mult": 0.00, "color": "⬜", "label": "0.00x",  "weight": 35},
        {"mult": 3.00, "color": "🟣", "label": "3.00x",  "weight": 12},
    ],
}


def pick_weighted(segments: list) -> dict:
    total = sum(s["weight"] for s in segments)
    r = random.uniform(0, total)
    for seg in segments:
        r -= seg["weight"]
        if r <= 0:
            return seg
    return segments[-1]


# =========================
# SLOT CONFIG
# =========================
SLOT_SYMBOLS = [
    {"symbol": "💎", "mult": 10, "label": "JACKPOT 💎"},
    {"symbol": "7️⃣",  "mult": 5,  "label": "Siódemki! 7️⃣"},
    {"symbol": "⭐",  "mult": 4,  "label": "Gwiazdy! ⭐"},
    {"symbol": "🍒",  "mult": 3,  "label": "Wiśnie! 🍒"},
    {"symbol": "🔔",  "mult": 3,  "label": "Dzwonki! 🔔"},
    {"symbol": "🍋",  "mult": 2,  "label": "Cytryny! 🍋"},
    {"symbol": "🃏",  "mult": 0,  "label": "Brak"},
    {"symbol": "🃏",  "mult": 0,  "label": "Brak"},
    {"symbol": "🃏",  "mult": 0,  "label": "Brak"},
    {"symbol": "🃏",  "mult": 0,  "label": "Brak"},
]

SPIN_GIF = "https://media.giphy.com/media/3o7aD2saalBwwftBIY/giphy.gif"
SLOT_GIF = "https://media.giphy.com/media/l0ExbnCiJMFjpvqaQ/giphy.gif"


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
    return CARD_VALUES[card[:-1]]


def hand_value(hand: list) -> int:
    total = sum(card_value(c) for c in hand)
    aces = sum(1 for c in hand if c[:-1] == "A")
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def hand_str(hand: list) -> str:
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
            description=f"{job_name}\n\n💰 Zarobek: **+{earn:,} 💎**",
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
    # 🎰 SPIN — koło z wagami + animacja
    # =========================
    @app_commands.command(name="spin", description="🎰 Koło fortuny z animacją")
    @app_commands.choices(level=[
        app_commands.Choice(name="Low 🟢 — duża szansa, mały zysk (max x1.5)",   value="low"),
        app_commands.Choice(name="Medium 🟡 — średnia szansa, średni zysk (max x3.0)", value="medium"),
        app_commands.Choice(name="Hard 🔴 — mała szansa, wielki zysk (max x10.0)", value="hard"),
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

        legend_lines = {
            "low":    "⬜ 0.00x — Przegrana\n🔵 1.20x\n🟢 1.50x",
            "medium": "⬜ 0.00x — Przegrana\n🟢 1.50x\n🟠 1.90x\n🔵 2.00x\n🟣 3.00x",
            "hard":   "⬜ 0.00x — Przegrana\n🔵 2.00x\n🟣 3.00x\n🟡 5.00x\n🔴 10.0x",
        }

        # ─ Animacja krok 1 ─
        start_embed = discord.Embed(
            title="🎰 Koło Fortuny — kręcę...",
            description=f"💰 Stawka: **{bet:,} 💎** | Tryb: **{level.name}**\n\n```\n{legend_lines[level.value]}\n```",
            color=0xF1C40F
        )
        start_embed.set_image(url=SPIN_GIF)
        await interaction.response.send_message(embed=start_embed)
        msg = await interaction.original_response()

        # ─ Animacja krok 2 — suspens ─
        await asyncio.sleep(2)
        suspense_embed = discord.Embed(
            title="🎰 Koło zwalnia...",
            description="⏳ Zatrzymuje się...",
            color=0xF59E0B
        )
        suspense_embed.set_image(url=SPIN_GIF)
        await msg.edit(embed=suspense_embed)
        await asyncio.sleep(2)

        # ─ Losowanie wyważone ─
        segments = WHEEL[level.value]
        seg = pick_weighted(segments)

        if seg["mult"] == 0.0:
            await db.log_transaction(interaction.user.id, -bet, f"spin_loss_{level.value}")
            result_embed = discord.Embed(
                title="⬜ Przegrana! (0.00x)",
                description=f"Pech! Straciłeś **{bet:,} 💎**",
                color=0x374151
            )
        else:
            win = int(bet * seg["mult"])
            profit = win - bet
            await db.update_crypto(interaction.user.id, win)
            await db.log_transaction(interaction.user.id, profit, f"spin_win_{level.value}")

            if seg["mult"] >= 5.0:
                title = f"🎊 MEGA WYGRANA! ({seg['label']})"
                color = 0xF59E0B
            elif seg["mult"] >= 3.0:
                title = f"🎉 Duża wygrana! ({seg['label']})"
                color = 0xA855F7
            else:
                title = f"{seg['color']} Wygrana! ({seg['label']})"
                color = 0x2ECC71

            profit_str = f"+{profit:,}" if profit >= 0 else f"{profit:,}"
            result_embed = discord.Embed(
                title=title,
                description=f"Wygrałeś **{win:,} 💎**\nZysk: **{profit_str} 💎**",
                color=color
            )

        result_embed.set_footer(text=f"Stawka: {bet:,} 💎 | Tryb: {level.name}")
        await msg.edit(embed=result_embed)

    # =========================
    # 🎰 SLOT MACHINE
    # =========================
    @app_commands.command(name="slot", description="🎰 Slot machine — 3 bębny, szansa na JACKPOT!")
    async def slot(self, interaction: discord.Interaction, bet: int):
        if bet <= 0:
            return await interaction.response.send_message("❌ Stawka musi być większa niż 0.", ephemeral=True)

        data = await db.get_profile(interaction.user.id)
        if data["crypto"] < bet:
            return await interaction.response.send_message(
                f"❌ Za mało 💎. Masz: **{data['crypto']:,}**", ephemeral=True
            )

        await db.update_crypto(interaction.user.id, -bet)

        # ─ Start ─
        start_embed = discord.Embed(
            title="🎰 Slot Machine",
            description="```\n| 🎰 | 🎰 | 🎰 |\n```\nKręcę bębny...",
            color=0xA855F7
        )
        start_embed.set_image(url=SLOT_GIF)
        await interaction.response.send_message(embed=start_embed)
        msg = await interaction.original_response()

        await asyncio.sleep(1.5)

        # ─ Bęben 1 ─
        r1 = random.choice(SLOT_SYMBOLS)
        await msg.edit(embed=discord.Embed(
            title="🎰 Slot Machine",
            description=f"```\n| {r1['symbol']} | 🎰 | 🎰 |\n```",
            color=0xA855F7
        ))
        await asyncio.sleep(1.0)

        # ─ Bęben 2 ─
        r2 = random.choice(SLOT_SYMBOLS)
        await msg.edit(embed=discord.Embed(
            title="🎰 Slot Machine",
            description=f"```\n| {r1['symbol']} | {r2['symbol']} | 🎰 |\n```",
            color=0xA855F7
        ))
        await asyncio.sleep(1.0)

        # ─ Bęben 3 ─
        r3 = random.choice(SLOT_SYMBOLS)
        symbols_str = f"| {r1['symbol']} | {r2['symbol']} | {r3['symbol']} |"

        # ─ Oblicz wynik ─
        win = 0
        result_label = ""

        if r1["symbol"] == r2["symbol"] == r3["symbol"]:
            if r1["mult"] > 0:
                win = int(bet * r1["mult"])
                result_label = f"🎊 **{r1['label']}** x{r1['mult']} → **+{win:,} 💎**"
            else:
                result_label = f"💀 Trzy 🃏 — Przegrana! **-{bet:,} 💎**"
        elif r1["symbol"] == r2["symbol"] or r2["symbol"] == r3["symbol"] or r1["symbol"] == r3["symbol"]:
            matched = r1 if r1["symbol"] == r2["symbol"] else (r2 if r2["symbol"] == r3["symbol"] else r1)
            if matched["mult"] > 0:
                half_mult = matched["mult"] * 0.5
                win = int(bet * half_mult)
                result_label = f"✅ Dwie takie same! x{half_mult:.1f} → **+{win:,} 💎**" if win > 0 else f"💀 Przegrana! **-{bet:,} 💎**"
            else:
                result_label = f"💀 Przegrana! **-{bet:,} 💎**"
        else:
            result_label = f"💀 Nic nie trafiłeś! **-{bet:,} 💎**"

        profit = win - bet

        if win > 0:
            await db.update_crypto(interaction.user.id, win)
            await db.log_transaction(interaction.user.id, profit, "slot_win")
            color = 0xF59E0B if win >= bet * 5 else 0x2ECC71
        else:
            await db.log_transaction(interaction.user.id, -bet, "slot_loss")
            color = 0xE74C3C

        payout_table = "\n".join(
            f"{s['symbol']} x3 = **x{s['mult']}**"
            for s in SLOT_SYMBOLS
            if s["mult"] > 0 and s["symbol"] != "🃏"
        )

        result_embed = discord.Embed(title="🎰 Slot Machine — Wynik", color=color)
        result_embed.add_field(name="Bębny", value=f"```\n{symbols_str}\n```", inline=False)
        result_embed.add_field(name="Wynik", value=result_label, inline=False)
        result_embed.add_field(name="📊 Tabela wypłat", value=payout_table, inline=False)
        result_embed.set_footer(text=f"Stawka: {bet:,} 💎 | x2 takie same = połowa mnożnika")
        await msg.edit(embed=result_embed)

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

        if player_val == 21 and dealer_val == 21:
            await db.update_crypto(interaction.user.id, bet)
            result, color = "🤝 REMIS — oboje macie Blackjacka!", 0xF1C40F
        elif player_val == 21:
            win = int(bet * 2.5)
            await db.update_crypto(interaction.user.id, win)
            await db.increment_wins(interaction.user.id)
            result, color = f"🎉 BLACKJACK! +{win:,} 💎", 0x2ECC71
        elif dealer_val == 21:
            result, color = f"💀 Dealer ma Blackjacka! -{bet:,} 💎", 0xE74C3C
        else:
            while dealer_val < 17:
                dealer_hand.append(deck.pop())
                dealer_val = hand_value(dealer_hand)

            if player_val > 21:
                result, color = f"💀 BUST! -{bet:,} 💎", 0xE74C3C
            elif dealer_val > 21 or player_val > dealer_val:
                win = bet * 2
                await db.update_crypto(interaction.user.id, win)
                await db.increment_wins(interaction.user.id)
                await db.log_transaction(interaction.user.id, win - bet, "blackjack_win")
                result, color = f"🎉 WYGRANA! +{win:,} 💎", 0x2ECC71
            elif player_val == dealer_val:
                await db.update_crypto(interaction.user.id, bet)
                result, color = "🤝 REMIS — stawka zwrócona", 0xF1C40F
            else:
                await db.log_transaction(interaction.user.id, -bet, "blackjack_loss")
                result, color = f"💀 PRZEGRANA! -{bet:,} 💎", 0xE74C3C

        embed = discord.Embed(title="🃏 Blackjack", color=color)
        embed.add_field(name=f"Twoja ręka ({player_val})", value=hand_str(player_hand), inline=False)
        embed.add_field(name=f"Ręka dealera ({dealer_val})", value=hand_str(dealer_hand), inline=False)
        embed.add_field(name="Wynik", value=result, inline=False)
        embed.set_footer(text=f"Stawka: {bet:,} 💎")
        await interaction.response.send_message(embed=embed)

    # =========================
    # 💣 MINES
    # =========================
    @app_commands.command(name="mines", description="💣 Pole minowe — trafisz na diament?")
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="Łatwy — 2 miny / 5 pól (x3.0)", value="easy"),
        app_commands.Choice(name="Normalny — 3 miny / 6 pól (x5.0)", value="normal"),
        app_commands.Choice(name="Trudny — 5 min / 7 pól (x8.0)", value="hard"),
    ])
    async def mines(self, interaction: discord.Interaction, bet: int, difficulty: app_commands.Choice[str]):
        if bet <= 0:
            return await interaction.response.send_message("❌ Stawka musi być większa niż 0.", ephemeral=True)

        data = await db.get_profile(interaction.user.id)
        if data["crypto"] < bet:
            return await interaction.response.send_message(
                f"❌ Za mało 💎. Masz: **{data['crypto']:,}**", ephemeral=True
            )

        await db.update_crypto(interaction.user.id, -bet)

        cfg = {"easy": (5, 2, 3.0), "normal": (6, 3, 5.0), "hard": (7, 5, 8.0)}[difficulty.value]
        total, mines_count, mult = cfg
        field = ["💣"] * mines_count + ["💎"] * (total - mines_count)
        random.shuffle(field)
        picked = random.choice(field)

        if picked == "💎":
            win = int(bet * mult)
            await db.update_crypto(interaction.user.id, win)
            await db.log_transaction(interaction.user.id, win - bet, "mines_win")
            embed = discord.Embed(
                title="💎 SAFE! Trafiłeś diamenta!",
                description=f"Wygrana: **+{win:,} 💎** (x{mult})",
                color=0x2ECC71
            )
        else:
            await db.log_transaction(interaction.user.id, -bet, "mines_loss")
            embed = discord.Embed(
                title="💣 BOOM! Trafiłeś na minę!",
                description=f"Strata: **-{bet:,} 💎**",
                color=0xE74C3C
            )

        embed.set_footer(text=f"Stawka: {bet:,} 💎 | {mines_count} miny / {total} pól | x{mult}")
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
    # 🔫 ROB
    # =========================
    @app_commands.command(name="okradnij", description="🔫 Spróbuj okraść kogoś (ryzykowne!)")
    async def rob(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ Nie możesz okraść samego siebie.", ephemeral=True)
        if user.bot:
            return await interaction.response.send_message("❌ Botów nie da się okraść.", ephemeral=True)

        remaining = await check_cooldown(interaction.user.id, "last_rob", 3600)
        if remaining:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏳ Jesteś obserwowany!",
                    description=f"Czekaj **{seconds_to_str(remaining)}** zanim spróbujesz ponownie.",
                    color=0xE74C3C
                ), ephemeral=True
            )

        victim_data = await db.get_profile(user.id)
        robber_data = await db.get_profile(interaction.user.id)

        if victim_data["crypto"] < 50:
            return await interaction.response.send_message(
                f"❌ {user.display_name} ma za mało 💎 (minimum 50 💎).", ephemeral=True
            )

        await db.set_cooldown(interaction.user.id, "last_rob")

        if random.random() < 0.45:
            max_steal = min(victim_data["crypto"] // 3, 500)
            stolen = random.randint(10, max(10, max_steal))
            await db.update_crypto(user.id, -stolen)
            await db.update_crypto(interaction.user.id, stolen)
            await db.log_transaction(interaction.user.id, stolen, "rob_success")
            await db.log_transaction(user.id, -stolen, "robbed")
            embed = discord.Embed(
                title="🔫 Udany skok!",
                description=f"Okradłeś {user.mention}!\n💰 Zdobyłeś **{stolen:,} 💎**",
                color=0x2ECC71
            )
        else:
            fine = random.randint(20, min(100, max(20, robber_data["crypto"])))
            if robber_data["crypto"] >= fine:
                await db.update_crypto(interaction.user.id, -fine)
                await db.log_transaction(interaction.user.id, -fine, "rob_caught")
            else:
                fine = 0
            embed = discord.Embed(
                title="🚔 Złapany!",
                description=f"Próba okradzenia {user.mention} się nie powiodła!\n💸 Kara: **{fine:,} 💎**",
                color=0xE74C3C
            )

        embed.set_footer(text="Cooldown: 1 godzina")
        await interaction.response.send_message(embed=embed)


# =========================
# SETUP
# =========================
async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))

