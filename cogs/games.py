import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from datetime import datetime, timedelta
import database as db

# Importujemy efekty sklepu
from shop import (
    get_luck_bonus,
    get_work_multiplier,
    get_rob_chance,
    is_shielded,
    get_daily_multiplier,
    get_vip_daily_bonus,
)


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

LEGEND = {
    "low":    "⬜ 0.00x  |  🔵 1.20x  |  🟢 1.50x",
    "medium": "⬜ 0.00x  |  🟢 1.50x  |  🟠 1.90x  |  🔵 2.00x  |  🟣 3.00x",
    "hard":   "⬜ 0.00x  |  🔵 2.00x  |  🟣 3.00x  |  🟡 5.00x  |  🔴 10.0x",
}


def pick_weighted(segments: list, luck_bonus: float = 0.0) -> dict:
    """
    Losuje segment z wagami.
    luck_bonus (np. 0.05 z lucky_charm) zmniejsza wagę segmentów 0.00x
    i proporcjonalnie zwiększa wagę wygrywających.
    """
    segs = []
    for s in segments:
        w = s["weight"]
        if s["mult"] == 0.0 and luck_bonus > 0:
            # Redukuj szansę przegranej
            w = max(1, w * (1.0 - luck_bonus * 3))
        elif s["mult"] > 0 and luck_bonus > 0:
            # Zwiększ szansę wygranej
            w = w * (1.0 + luck_bonus)
        segs.append({**s, "weight": w})

    total = sum(s["weight"] for s in segs)
    r = random.uniform(0, total)
    for seg in segs:
        r -= seg["weight"]
        if r <= 0:
            return seg
    return segs[-1]


def make_wheel_bar(segments: list, highlighted: int) -> str:
    pointer_line = "".join("▼" if i == highlighted else "　" for i in range(len(segments)))
    wheel_line = "".join(s["color"] for s in segments)
    return f"`{pointer_line}`\n{wheel_line}"


# =========================
# SLOT CONFIG
# =========================
SLOT_SYMBOLS = [
    {"symbol": "💎", "mult": 10, "label": "JACKPOT 💎"},
    {"symbol": "7️⃣",  "mult": 5,  "label": "Siódemki 7️⃣"},
    {"symbol": "⭐",  "mult": 4,  "label": "Gwiazdy ⭐"},
    {"symbol": "🍒",  "mult": 3,  "label": "Wiśnie 🍒"},
    {"symbol": "🔔",  "mult": 3,  "label": "Dzwonki 🔔"},
    {"symbol": "🍋",  "mult": 2,  "label": "Cytryny 🍋"},
    {"symbol": "🃏",  "mult": 0,  "label": "Brak"},
    {"symbol": "🃏",  "mult": 0,  "label": "Brak"},
    {"symbol": "🃏",  "mult": 0,  "label": "Brak"},
    {"symbol": "🃏",  "mult": 0,  "label": "Brak"},
]
SLOT_SPIN_SYMS = ["💎", "7️⃣", "⭐", "🍒", "🔔", "🍋", "🃏"]


def pick_slot_symbol(luck_bonus: float = 0.0) -> dict:
    """Losuje symbol slota z uwzględnieniem luck_bonus."""
    symbols = []
    for s in SLOT_SYMBOLS:
        w = 1.0
        if s["mult"] == 0 and luck_bonus > 0:
            w = max(0.1, 1.0 - luck_bonus * 2)
        elif s["mult"] > 0 and luck_bonus > 0:
            w = 1.0 + luck_bonus * s["mult"] * 0.1
        symbols.append((s, w))
    total = sum(w for _, w in symbols)
    r = random.uniform(0, total)
    for s, w in symbols:
        r -= w
        if r <= 0:
            return s
    return symbols[-1][0]


def slot_embed(a, b, c, title="🎰 Slot Machine", color=0xA855F7, result="", bet=0, bonus_txt=""):
    e = discord.Embed(title=title, color=color)
    e.add_field(
        name="Bębny",
        value=f"```\n╔═══╦═══╦═══╗\n║ {a} ║ {b} ║ {c} ║\n╚═══╩═══╩═══╝\n```",
        inline=False
    )
    if result:
        e.add_field(name="Wynik", value=result, inline=False)
    footer = f"Stawka: {bet:,} 💎"
    if bonus_txt:
        footer += f"  {bonus_txt}"
    if bet:
        e.set_footer(text=footer)
    return e


# =========================
# BLACKJACK HELPERS
# =========================
CARD_VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
    "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11
}
SUITS = ["♠", "♥", "♦", "♣"]
BJ_RANKS = list(CARD_VALUES.keys())


def new_deck():
    deck = [f"{r}{s}" for r in BJ_RANKS for s in SUITS]
    random.shuffle(deck)
    return deck


def card_value(card: str) -> int:
    for r in sorted(CARD_VALUES.keys(), key=len, reverse=True):
        if card.startswith(r):
            return CARD_VALUES[r]
    return 0


def hand_value(hand: list) -> int:
    total = sum(card_value(c) for c in hand)
    aces = sum(1 for c in hand if c.startswith("A"))
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def hand_str(hand: list) -> str:
    return "  ".join(f"`{c}`" for c in hand)


def build_bj_embed(player_hand, dealer_hand, player_val, dealer_val,
                   bet, status="playing", result_text="", color=0x00D4FF,
                   show_dealer_full=False, items_txt=""):
    embed = discord.Embed(title="🃏 Blackjack", color=color)

    if show_dealer_full:
        d_display = hand_str(dealer_hand)
        d_score = str(dealer_val)
    else:
        d_display = f"`{dealer_hand[0]}`  🂠"
        d_score = "?"

    embed.add_field(name=f"🏦 Dealer  [{d_score}]", value=d_display, inline=False)
    embed.add_field(name=f"👤 Twoja ręka  [{player_val}]", value=hand_str(player_hand), inline=False)

    if status == "playing":
        embed.add_field(
            name="Akcje",
            value="🃏 **Hit** — dobierz kartę\n🛑 **Stand** — zatrzymaj się\n✌️ **Double** — podwój stawkę i dobierz 1 kartę",
            inline=False
        )

    if result_text:
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value=result_text, inline=False)

    footer = f"Stawka: {bet:,} 💎"
    if items_txt:
        footer += f"  {items_txt}"
    embed.set_footer(text=footer)
    return embed


# =========================
# BLACKJACK VIEW
# =========================
class BlackjackView(discord.ui.View):
    def __init__(self, user_id: int, bet: int, deck: list,
                 player_hand: list, dealer_hand: list, items_txt: str = ""):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.bet = bet
        self.deck = deck
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.doubled = False
        self.items_txt = items_txt

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ To nie twoja gra!", ephemeral=True)
            return False
        return True

    def disable_all(self):
        for child in self.children:
            child.disabled = True

    async def end_game(self, interaction: discord.Interaction):
        self.disable_all()
        player_val = hand_value(self.player_hand)

        while hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.pop())
        dealer_val = hand_value(self.dealer_hand)

        actual_bet = self.bet * 2 if self.doubled else self.bet

        if player_val > 21:
            result = f"💀 **BUST!** Przekroczyłeś 21.\n**-{actual_bet:,} 💎**"
            color = 0xE74C3C
            await db.log_transaction(self.user_id, -actual_bet, "bj_bust")
        elif dealer_val > 21 or player_val > dealer_val:
            win = actual_bet * 2
            await db.update_crypto(self.user_id, win)
            await db.increment_wins(self.user_id)
            await db.log_transaction(self.user_id, actual_bet, "bj_win")
            result = f"🎉 **WYGRANA!** Dealer: {dealer_val}\n**+{win:,} 💎**"
            color = 0x2ECC71
        elif player_val == dealer_val:
            await db.update_crypto(self.user_id, actual_bet)
            result = f"🤝 **REMIS!** Obaj macie {player_val}.\nStawka zwrócona."
            color = 0xF1C40F
        else:
            await db.log_transaction(self.user_id, -actual_bet, "bj_loss")
            result = f"💀 **PRZEGRANA!** Dealer: {dealer_val} > Ty: {player_val}\n**-{actual_bet:,} 💎**"
            color = 0xE74C3C

        embed = build_bj_embed(
            self.player_hand, self.dealer_hand,
            player_val, dealer_val, actual_bet,
            status="done", result_text=result, color=color,
            show_dealer_full=True, items_txt=self.items_txt
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🃏 Hit", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player_hand.append(self.deck.pop())
        player_val = hand_value(self.player_hand)
        if player_val >= 21:
            await self.end_game(interaction)
            return
        embed = build_bj_embed(
            self.player_hand, self.dealer_hand,
            player_val, hand_value(self.dealer_hand),
            self.bet, items_txt=self.items_txt
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🛑 Stand", style=discord.ButtonStyle.danger)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.end_game(interaction)

    @discord.ui.button(label="✌️ Double", style=discord.ButtonStyle.secondary)
    async def double_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = await db.get_profile(self.user_id)
        if data["crypto"] < self.bet:
            await interaction.response.send_message(
                f"❌ Potrzebujesz **{self.bet:,} 💎** więcej na double.", ephemeral=True
            )
            return
        await db.update_crypto(self.user_id, -self.bet)
        self.doubled = True
        button.disabled = True
        self.player_hand.append(self.deck.pop())
        await self.end_game(interaction)

    async def on_timeout(self):
        self.disable_all()


# =========================
# SPIN AGAIN VIEW
# =========================
class SpinAgainView(discord.ui.View):
    def __init__(self, user_id: int, bet: int, level: str):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.bet = bet
        self.level = level

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ To nie twoja gra!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🎰 Zagraj ponownie", style=discord.ButtonStyle.primary)
    async def play_again(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = await db.get_profile(self.user_id)
        if data["crypto"] < self.bet:
            return await interaction.response.send_message(
                f"❌ Za mało 💎! Masz: **{data['crypto']:,}**", ephemeral=True
            )
        await db.update_crypto(self.user_id, -self.bet)
        button.disabled = True
        await interaction.response.edit_message(view=self)
        await run_spin(interaction, self.user_id, self.bet, self.level, followup=True)


# =========================
# SLOT AGAIN VIEW
# =========================
class SlotAgainView(discord.ui.View):
    def __init__(self, user_id: int, bet: int):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.bet = bet

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ To nie twoja gra!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🎰 Zagraj ponownie", style=discord.ButtonStyle.primary)
    async def play_again(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = await db.get_profile(self.user_id)
        if data["crypto"] < self.bet:
            return await interaction.response.send_message(
                f"❌ Za mało 💎! Masz: **{data['crypto']:,}**", ephemeral=True
            )
        button.disabled = True
        await interaction.response.edit_message(view=self)
        await run_slot(interaction, self.user_id, self.bet, followup=True)


# =========================
# ACTIVE ITEMS SUMMARY
# Zwraca krótki tekst do footera np. "🍀 +5% | 🎰 max 100k"
# =========================
async def active_items_txt(user_id: int) -> str:
    parts = []
    luck = await get_luck_bonus(user_id)
    if luck > 0:
        parts.append(f"🍀 +{int(luck*100)}% luck")
    if await db.has_active_item(user_id, "casino_pass"):
        parts.append("🎰 Karnet")
    if await db.has_active_item(user_id, "work_boost"):
        parts.append("⚡ Turbo")
    if await db.has_active_item(user_id, "shield"):
        parts.append("🛡️ Tarcza")
    if await db.has_active_item(user_id, "vip"):
        parts.append("👑 VIP")
    return "  ".join(parts)


# =========================
# SPIN ANIMATION
# =========================
async def run_spin(interaction, user_id: int, bet: int, level: str, followup=False):
    luck = await get_luck_bonus(user_id)
    segments = WHEEL[level]
    seg = pick_weighted(segments, luck_bonus=luck)
    target_idx = segments.index(seg)
    n = len(segments)

    bonus_txt = f"🍀 +{int(luck*100)}% luck" if luck > 0 else ""

    def frame_embed(pointer: int, title="🎰 Koło Fortuny — kręci się..."):
        e = discord.Embed(title=title, color=0xF1C40F)
        e.add_field(name="Koło", value=make_wheel_bar(segments, pointer), inline=False)
        e.add_field(name="Legenda", value=LEGEND[level], inline=False)
        footer = f"Stawka: {bet:,} 💎 | Tryb: {level.upper()}"
        if bonus_txt:
            footer += f" | {bonus_txt}"
        e.set_footer(text=footer)
        return e

    start_embed = frame_embed(0)
    if followup:
        msg = await interaction.followup.send(embed=start_embed)
    else:
        await interaction.response.send_message(embed=start_embed)
        msg = await interaction.original_response()

    # Animacja
    total_frames = 20
    pointer = 0
    for frame_i in range(total_frames):
        t = frame_i / total_frames
        if t < 0.5:
            delay, step = 0.08, 2
        elif t < 0.75:
            delay, step = 0.15, 1
        else:
            delay, step = 0.28, 1

        remaining = total_frames - frame_i
        if remaining <= n:
            dist = (target_idx - pointer) % n
            if dist == 0 and remaining > 1:
                dist = n
            step = max(1, round(dist / remaining))

        pointer = (pointer + step) % n
        await msg.edit(embed=frame_embed(pointer))
        await asyncio.sleep(delay)

    await msg.edit(embed=frame_embed(target_idx, title="🎰 Koło zatrzymało się!"))
    await asyncio.sleep(0.5)

    # Wynik
    if seg["mult"] == 0.0:
        await db.log_transaction(user_id, -bet, f"spin_loss_{level}")
        result_embed = discord.Embed(
            title="⬜ Przegrana! (0.00x)",
            description=f"Pech! Straciłeś **{bet:,} 💎**",
            color=0x4B5563
        )
    else:
        win = int(bet * seg["mult"])
        profit = win - bet
        await db.update_crypto(user_id, win)
        await db.log_transaction(user_id, profit, f"spin_win_{level}")

        if seg["mult"] >= 5.0:
            title, color = f"🎊 MEGA WYGRANA! ({seg['label']})", 0xF59E0B
        elif seg["mult"] >= 3.0:
            title, color = f"🎉 Duża wygrana! ({seg['label']})", 0xA855F7
        else:
            title, color = f"{seg['color']} Wygrana! ({seg['label']})", 0x2ECC71

        profit_str = f"+{profit:,}" if profit >= 0 else f"{profit:,}"
        result_embed = discord.Embed(
            title=title,
            description=f"Wygrałeś **{win:,} 💎**\nZysk: **{profit_str} 💎**",
            color=color
        )

    result_embed.add_field(name="Koło", value=make_wheel_bar(segments, target_idx), inline=False)
    result_embed.add_field(name="Legenda", value=LEGEND[level], inline=False)
    footer = f"Stawka: {bet:,} 💎 | Tryb: {level.upper()}"
    if bonus_txt:
        footer += f" | {bonus_txt}"
    result_embed.set_footer(text=footer)

    again_view = SpinAgainView(user_id, bet, level)
    await msg.edit(embed=result_embed, view=again_view)


# =========================
# SLOT ANIMATION
# =========================
async def run_slot(interaction, user_id: int, bet: int, followup=False):
    await db.update_crypto(user_id, -bet)

    luck = await get_luck_bonus(user_id)
    bonus_txt = f"🍀 +{int(luck*100)}% luck" if luck > 0 else ""

    r1 = pick_slot_symbol(luck)
    r2 = pick_slot_symbol(luck)
    r3 = pick_slot_symbol(luck)

    start = slot_embed("🎰", "🎰", "🎰", bet=bet, bonus_txt=bonus_txt)
    if followup:
        msg = await interaction.followup.send(embed=start)
    else:
        await interaction.response.send_message(embed=start)
        msg = await interaction.original_response()

    # Bęben 1
    for _ in range(7):
        await msg.edit(embed=slot_embed(random.choice(SLOT_SPIN_SYMS), "🎰", "🎰", bet=bet))
        await asyncio.sleep(0.1)
    await msg.edit(embed=slot_embed(r1["symbol"], "🎰", "🎰", bet=bet))
    await asyncio.sleep(0.5)

    # Bęben 2
    for _ in range(7):
        await msg.edit(embed=slot_embed(r1["symbol"], random.choice(SLOT_SPIN_SYMS), "🎰", bet=bet))
        await asyncio.sleep(0.1)
    await msg.edit(embed=slot_embed(r1["symbol"], r2["symbol"], "🎰", bet=bet))
    await asyncio.sleep(0.5)

    # Bęben 3
    for _ in range(7):
        await msg.edit(embed=slot_embed(r1["symbol"], r2["symbol"], random.choice(SLOT_SPIN_SYMS), bet=bet))
        await asyncio.sleep(0.1)
    await msg.edit(embed=slot_embed(r1["symbol"], r2["symbol"], r3["symbol"], bet=bet))
    await asyncio.sleep(0.6)

    # Oblicz wynik
    win = 0
    result_text = ""

    if r1["symbol"] == r2["symbol"] == r3["symbol"]:
        if r1["mult"] > 0:
            win = int(bet * r1["mult"])
            result_text = f"🎊 **{r1['label']}** × {r1['mult']} → **+{win:,} 💎**"
        else:
            result_text = f"💀 Trzy 🃏 — Brak wygranej. **-{bet:,} 💎**"
    elif r1["symbol"] == r2["symbol"] or r2["symbol"] == r3["symbol"] or r1["symbol"] == r3["symbol"]:
        matched = r1 if r1["symbol"] == r2["symbol"] else (r2 if r2["symbol"] == r3["symbol"] else r1)
        if matched["mult"] > 0:
            half = matched["mult"] * 0.5
            win = int(bet * half)
            result_text = f"✅ Dwie takie same! × {half:.1f} → **+{win:,} 💎**" if win > 0 else f"💀 Brak wygranej. **-{bet:,} 💎**"
        else:
            result_text = f"💀 Brak wygranej. **-{bet:,} 💎**"
    else:
        result_text = f"💀 Nic nie trafiłeś! **-{bet:,} 💎**"

    profit = win - bet
    if win > 0:
        await db.update_crypto(user_id, win)
        await db.log_transaction(user_id, profit, "slot_win")
        color = 0xF59E0B if win >= bet * 5 else 0x2ECC71
    else:
        await db.log_transaction(user_id, -bet, "slot_loss")
        color = 0xE74C3C

    payout = " | ".join(
        f"{s['symbol']}×3={s['mult']}x"
        for s in SLOT_SYMBOLS if s["mult"] > 0 and s["symbol"] != "🃏"
    )

    final = slot_embed(
        r1["symbol"], r2["symbol"], r3["symbol"],
        title="🎰 Slot Machine — Wynik", color=color,
        result=result_text, bet=bet, bonus_txt=bonus_txt
    )
    final.add_field(name="📊 Wypłaty (×3)", value=payout, inline=False)
    final.set_footer(text=f"Stawka: {bet:,} 💎 | ×2 takie same = ½ mnożnika" + (f" | {bonus_txt}" if bonus_txt else ""))

    again_view = SlotAgainView(user_id, bet)
    await msg.edit(embed=final, view=again_view)


# =========================
# GAMES COG
# =========================
class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # 💼 PRACUJ — work_boost x2
    # =========================
    @app_commands.command(name="pracuj", description="💼 Idź do pracy i zarób (cooldown: 1h)")
    async def work(self, interaction: discord.Interaction):
        remaining = await check_cooldown(interaction.user.id, "last_work", 3600)
        if remaining:
            return await interaction.response.send_message(embed=discord.Embed(
                title="⏳ Jesteś zmęczony!",
                description=f"Wróć za **{seconds_to_str(remaining)}**.",
                color=0xE74C3C
            ), ephemeral=True)

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
        job_name, lo, hi = random.choice(jobs)
        base_earn = random.randint(lo, hi)

        # ⚡ work_boost — podwaja zarobki
        multiplier = await get_work_multiplier(interaction.user.id)
        earn = int(base_earn * multiplier)

        await db.update_crypto(interaction.user.id, earn)
        await db.set_cooldown(interaction.user.id, "last_work")
        await db.log_transaction(interaction.user.id, earn, "work")

        embed = discord.Embed(
            title="💼 Praca wykonana!",
            description=f"{job_name}\n\n💰 **+{earn:,} 💎**",
            color=0x2ECC71
        )
        if multiplier > 1:
            embed.add_field(
                name="⚡ Turbo Praca aktywna!",
                value=f"Bazowo: {base_earn:,} 💎 × {multiplier:.0f} = **{earn:,} 💎**",
                inline=False
            )
        embed.set_footer(text="Cooldown: 1 godzina")
        await interaction.response.send_message(embed=embed)

    # =========================
    # 🎁 DAILY — daily_boost x3, VIP +300
    # =========================
    @app_commands.command(name="daily", description="🎁 Codzienna nagroda (cooldown: 24h)")
    async def daily(self, interaction: discord.Interaction):
        remaining = await check_cooldown(interaction.user.id, "last_daily", 86400)
        if remaining:
            return await interaction.response.send_message(embed=discord.Embed(
                title="⏳ Już odebrałeś!",
                description=f"Wróć za **{seconds_to_str(remaining)}**.",
                color=0xE74C3C
            ), ephemeral=True)

        base_crypto = random.randint(50, 200)
        base_pln = random.randint(10, 50)

        # 🎁 daily_boost x3 (jednorazowy) — zużywa przedmiot
        multiplier = await get_daily_multiplier(interaction.user.id)
        rc = int(base_crypto * multiplier)
        rp = int(base_pln * multiplier)

        # 👑 VIP +300 flat
        vip_bonus = await get_vip_daily_bonus(interaction.user.id)
        rc += vip_bonus

        await db.update_crypto(interaction.user.id, rc)
        await db.update_pln(interaction.user.id, rp)
        await db.set_cooldown(interaction.user.id, "last_daily")
        await db.log_transaction(interaction.user.id, rc, "daily_crypto")
        await db.log_transaction(interaction.user.id, rp, "daily_pln")

        embed = discord.Embed(
            title="🎁 Daily odebrane!",
            description=f"💎 **+{rc:,}** Crypto\n🇵🇱 **+{rp:,} PLN**",
            color=0xF1C40F
        )
        if multiplier > 1:
            embed.add_field(name="🎁 Mega Dzienny!", value=f"Bonus ×{multiplier:.0f} zastosowany!", inline=False)
        if vip_bonus > 0:
            embed.add_field(name="👑 VIP Bonus", value=f"+{vip_bonus} 💎 extra!", inline=False)
        embed.set_footer(text="Wróć jutro!")
        await interaction.response.send_message(embed=embed)

    # =========================
    # 🎰 SPIN — lucky_charm / casino_pass
    # =========================
    @app_commands.command(name="spin", description="🎰 Koło fortuny z animacją")
    @app_commands.choices(level=[
        app_commands.Choice(name="Low 🟢 — duża szansa, max x1.5",    value="low"),
        app_commands.Choice(name="Medium 🟡 — średnia szansa, max x3.0", value="medium"),
        app_commands.Choice(name="Hard 🔴 — mała szansa, max x10.0",   value="hard"),
    ])
    async def spin(self, interaction: discord.Interaction, bet: int, level: app_commands.Choice[str]):
        if bet <= 0:
            return await interaction.response.send_message("❌ Stawka > 0.", ephemeral=True)

        data = await db.get_profile(interaction.user.id)

        # 🎰 casino_pass — max stawka 100 000
        max_bet = 100_000 if await db.has_active_item(interaction.user.id, "casino_pass") else 10_000
        if bet > max_bet:
            return await interaction.response.send_message(
                f"❌ Maksymalna stawka: **{max_bet:,} 💎**.", ephemeral=True
            )
        if data["crypto"] < bet:
            return await interaction.response.send_message(
                f"❌ Za mało 💎. Masz: **{data['crypto']:,}**", ephemeral=True
            )

        await db.update_crypto(interaction.user.id, -bet)
        await run_spin(interaction, interaction.user.id, bet, level.value)

    # =========================
    # 🎰 SLOT — lucky_charm / casino_pass
    # =========================
    @app_commands.command(name="slot", description="🎰 Slot machine — 3 bębny z animacją!")
    async def slot(self, interaction: discord.Interaction, bet: int):
        if bet <= 0:
            return await interaction.response.send_message("❌ Stawka > 0.", ephemeral=True)

        data = await db.get_profile(interaction.user.id)

        max_bet = 100_000 if await db.has_active_item(interaction.user.id, "casino_pass") else 10_000
        if bet > max_bet:
            return await interaction.response.send_message(
                f"❌ Maksymalna stawka: **{max_bet:,} 💎**.", ephemeral=True
            )
        if data["crypto"] < bet:
            return await interaction.response.send_message(
                f"❌ Za mało 💎. Masz: **{data['crypto']:,}**", ephemeral=True
            )

        await run_slot(interaction, interaction.user.id, bet)

    # =========================
    # 🃏 BLACKJACK
    # =========================
    @app_commands.command(name="blackjack", description="🃏 Blackjack z przyciskami Hit / Stand / Double!")
    async def blackjack(self, interaction: discord.Interaction, bet: int):
        if bet <= 0:
            return await interaction.response.send_message("❌ Stawka > 0.", ephemeral=True)

        data = await db.get_profile(interaction.user.id)
        max_bet = 100_000 if await db.has_active_item(interaction.user.id, "casino_pass") else 10_000
        if bet > max_bet:
            return await interaction.response.send_message(
                f"❌ Maksymalna stawka: **{max_bet:,} 💎**.", ephemeral=True
            )
        if data["crypto"] < bet:
            return await interaction.response.send_message(
                f"❌ Za mało 💎. Masz: **{data['crypto']:,}**", ephemeral=True
            )

        await db.update_crypto(interaction.user.id, -bet)

        items_txt = await active_items_txt(interaction.user.id)
        deck = new_deck()
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
        pv = hand_value(player_hand)
        dv = hand_value(dealer_hand)

        if pv == 21 and dv == 21:
            await db.update_crypto(interaction.user.id, bet)
            return await interaction.response.send_message(embed=build_bj_embed(
                player_hand, dealer_hand, pv, dv, bet, "done",
                "🤝 Remis — oboje macie Blackjacka!", 0xF1C40F, True, items_txt))
        if pv == 21:
            win = int(bet * 2.5)
            await db.update_crypto(interaction.user.id, win)
            await db.increment_wins(interaction.user.id)
            return await interaction.response.send_message(embed=build_bj_embed(
                player_hand, dealer_hand, pv, dv, bet, "done",
                f"🎉 BLACKJACK! **+{win:,} 💎**", 0x2ECC71, True, items_txt))
        if dv == 21:
            return await interaction.response.send_message(embed=build_bj_embed(
                player_hand, dealer_hand, pv, dv, bet, "done",
                f"💀 Dealer ma Blackjacka! **-{bet:,} 💎**", 0xE74C3C, True, items_txt))

        view = BlackjackView(interaction.user.id, bet, deck, player_hand, dealer_hand, items_txt)
        await interaction.response.send_message(
            embed=build_bj_embed(player_hand, dealer_hand, pv, dv, bet, items_txt=items_txt),
            view=view
        )

    # =========================
    # 💣 MINES
    # =========================
    @app_commands.command(name="mines", description="💣 Pole minowe")
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="Łatwy — 2/5 pól (x3.0)", value="easy"),
        app_commands.Choice(name="Normalny — 3/6 pól (x5.0)", value="normal"),
        app_commands.Choice(name="Trudny — 5/7 pól (x8.0)", value="hard"),
    ])
    async def mines(self, interaction: discord.Interaction, bet: int, difficulty: app_commands.Choice[str]):
        if bet <= 0:
            return await interaction.response.send_message("❌ Stawka > 0.", ephemeral=True)
        data = await db.get_profile(interaction.user.id)
        if data["crypto"] < bet:
            return await interaction.response.send_message(
                f"❌ Za mało 💎. Masz: **{data['crypto']:,}**", ephemeral=True
            )
        await db.update_crypto(interaction.user.id, -bet)

        total, mines_count, mult = {"easy": (5,2,3.0), "normal": (6,3,5.0), "hard": (7,5,8.0)}[difficulty.value]
        field = ["💣"] * mines_count + ["💎"] * (total - mines_count)
        random.shuffle(field)
        picked = random.choice(field)

        if picked == "💎":
            win = int(bet * mult)
            await db.update_crypto(interaction.user.id, win)
            await db.log_transaction(interaction.user.id, win - bet, "mines_win")
            embed = discord.Embed(title="💎 SAFE!", description=f"**+{win:,} 💎** (×{mult})", color=0x2ECC71)
        else:
            await db.log_transaction(interaction.user.id, -bet, "mines_loss")
            embed = discord.Embed(title="💣 BOOM!", description=f"**-{bet:,} 💎**", color=0xE74C3C)

        embed.set_footer(text=f"Stawka: {bet:,} 💎 | {mines_count}/{total} pól | ×{mult}")
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
            return await interaction.response.send_message("❌ Stawka > 0.", ephemeral=True)
        data = await db.get_profile(interaction.user.id)
        if data["crypto"] < bet:
            return await interaction.response.send_message(
                f"❌ Za mało 💎. Masz: **{data['crypto']:,}**", ephemeral=True
            )
        await db.update_crypto(interaction.user.id, -bet)
        result = random.choice(["heads", "tails"])
        label = "Orzeł 🦅" if result == "heads" else "Reszka 🔵"

        if choice.value == result:
            win = bet * 2
            await db.update_crypto(interaction.user.id, win)
            await db.increment_wins(interaction.user.id)
            await db.log_transaction(interaction.user.id, win - bet, "coinflip_win")
            embed = discord.Embed(title=f"🪙 {label} — WYGRANA!", description=f"**+{win:,} 💎**", color=0x2ECC71)
        else:
            await db.log_transaction(interaction.user.id, -bet, "coinflip_loss")
            embed = discord.Embed(title=f"🪙 {label} — PRZEGRANA!", description=f"**-{bet:,} 💎**", color=0xE74C3C)

        embed.set_footer(text=f"Twój wybór: {choice.name} | Wynik: {label}")
        await interaction.response.send_message(embed=embed)

    # =========================
    # 🔫 OKRADNIJ — shield blokuje, robber_kit 70%
    # =========================
    @app_commands.command(name="okradnij", description="🔫 Spróbuj okraść kogoś!")
    async def rob(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.user.id or user.bot:
            return await interaction.response.send_message("❌ Nieprawidłowy cel.", ephemeral=True)

        remaining = await check_cooldown(interaction.user.id, "last_rob", 3600)
        if remaining:
            return await interaction.response.send_message(embed=discord.Embed(
                title="⏳ Obserwowany!",
                description=f"Czekaj **{seconds_to_str(remaining)}**.",
                color=0xE74C3C
            ), ephemeral=True)

        # 🛡️ Sprawdź czy cel ma tarczę
        if await is_shielded(user.id):
            await db.set_cooldown(interaction.user.id, "last_rob")
            embed = discord.Embed(
                title="🛡️ Tarcza Bankowa!",
                description=(
                    f"{user.mention} ma aktywną **🛡️ Tarczę Bankową**!\n"
                    f"Nie możesz go okraść. Twój cooldown został naliczony."
                ),
                color=0x3498DB
            )
            embed.set_footer(text="Cooldown: 1h")
            return await interaction.response.send_message(embed=embed)

        victim = await db.get_profile(user.id)
        robber = await db.get_profile(interaction.user.id)

        if victim["crypto"] < 50:
            return await interaction.response.send_message(
                f"❌ {user.display_name} ma za mało 💎 (min. 50).", ephemeral=True
            )

        await db.set_cooldown(interaction.user.id, "last_rob")

        # 🥷 robber_kit — 70% zamiast 45%
        chance = await get_rob_chance(interaction.user.id)
        kit_active = await db.has_active_item(interaction.user.id, "robber_kit")

        if random.random() < chance:
            stolen = random.randint(10, max(10, min(victim["crypto"] // 3, 500)))
            await db.update_crypto(user.id, -stolen)
            await db.update_crypto(interaction.user.id, stolen)
            await db.log_transaction(interaction.user.id, stolen, "rob_success")
            await db.log_transaction(user.id, -stolen, "robbed")
            embed = discord.Embed(
                title="🔫 Udany skok!",
                description=f"Okradłeś {user.mention}!\n**+{stolen:,} 💎**",
                color=0x2ECC71
            )
            if kit_active:
                embed.add_field(name="🥷 Zestaw Złodzieja", value=f"Szansa: **{int(chance*100)}%**", inline=False)
        else:
            fine = random.randint(20, min(100, max(20, robber["crypto"])))
            if robber["crypto"] >= fine:
                await db.update_crypto(interaction.user.id, -fine)
                await db.log_transaction(interaction.user.id, -fine, "rob_caught")
            else:
                fine = 0
            embed = discord.Embed(
                title="🚔 Złapany!",
                description=f"Nieudany napad na {user.mention}!\nKara: **{fine:,} 💎**",
                color=0xE74C3C
            )
            if kit_active:
                embed.add_field(name="🥷 Zestaw Złodzieja", value=f"Nawet z {int(chance*100)}% szansą się nie udało!", inline=False)

        embed.set_footer(text="Cooldown: 1h")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))

