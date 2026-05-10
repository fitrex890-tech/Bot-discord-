import discord
from datetime import datetime, timedelta
from typing import Optional

CRYPTO_EMOJI = "💎"
WIN_COLOR = 0x00FF7F
LOSE_COLOR = 0xFF4444
JACKPOT_COLOR = 0xFFD700
INFO_COLOR = 0x5865F2
NEUTRAL_COLOR = 0x2B2D31


SPIN_GIFS = {
    "spinning": "https://media.tenor.com/YYHCYnRDWFMAAAAC/wheel-of-fortune-spin.gif",
    "win_big": "https://media.tenor.com/Lb01bXiD9CUAAAAC/jackpot-winner.gif",
    "win_small": "https://media.tenor.com/1Cj30j8CQPUAAAAC/winner-spinning.gif",
    "lose": "https://media.tenor.com/X0N-T2Bg-xMAAAAC/spin-wheel.gif",
    "jackpot": "https://media.tenor.com/IhBjAXNr_v4AAAAC/jackpot-slot-machine.gif",
}

SLOT_GIFS = {
    "spinning": "https://media.tenor.com/lM-CDNJPgP8AAAAC/slots-casino.gif",
    "win": "https://media.tenor.com/sbZCLSGFMrUAAAAC/jackpot-casino.gif",
    "lose": "https://media.tenor.com/X6j8lRvxTkUAAAAC/slot-machine-cartoon.gif",
}

CARD_GIFS = {
    "deal": "https://media.tenor.com/1WBbMl97_0EAAAAC/cards-casino.gif",
    "win": "https://media.tenor.com/DzV7lhHkq5MAAAAC/blackjack-casino.gif",
    "lose": "https://media.tenor.com/0rdWiA8IiJoAAAAC/card-game-casino.gif",
    "bust": "https://media.tenor.com/XHpEzDsHzCwAAAAC/bust-blackjack.gif",
    "blackjack": "https://media.tenor.com/DzV7lhHkq5MAAAAC/blackjack-casino.gif",
}

ROULETTE_GIFS = {
    "spinning": "https://media.tenor.com/QHKlbYqMawoAAAAC/roulette-casino.gif",
    "win": "https://media.tenor.com/2VMhNHHCBDQAAAAC/roulette-winner.gif",
    "lose": "https://media.tenor.com/QHKlbYqMawoAAAAC/roulette-casino.gif",
}


CARD_SUITS = {"♠️": "pik", "♥️": "kier", "♦️": "karo", "♣️": "trefl"}
CARD_VALUES = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

CARD_EMOJIS = {
    "A♠️": "🂡", "2♠️": "🂢", "3♠️": "🂣", "4♠️": "🂤", "5♠️": "🂥",
    "6♠️": "🂦", "7♠️": "🂧", "8♠️": "🂨", "9♠️": "🂩", "10♠️": "🂪",
    "J♠️": "🂫", "Q♠️": "🂭", "K♠️": "🂮",
    "A♥️": "🂱", "2♥️": "🂲", "3♥️": "🂳", "4♥️": "🂴", "5♥️": "🂵",
    "6♥️": "🂶", "7♥️": "🂷", "8♥️": "🂸", "9♥️": "🂹", "10♥️": "🂺",
    "J♥️": "🂻", "Q♥️": "🂽", "K♥️": "🂾",
}


def format_currency(amount: int) -> str:
    return f"**{amount:,} {CRYPTO_EMOJI} Crypto**"


def make_embed(
    title: str,
    description: str = "",
    color: int = INFO_COLOR,
    gif_url: Optional[str] = None,
    thumbnail_url: Optional[str] = None,
    footer: Optional[str] = None,
) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    if gif_url:
        embed.set_image(url=gif_url)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    if footer:
        embed.set_footer(text=footer)
    embed.timestamp = datetime.utcnow()
    return embed


def check_cooldown(last_time_str: Optional[str], cooldown_seconds: int) -> Optional[int]:
    if not last_time_str:
        return None
    last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
    diff = (datetime.utcnow() - last_time).total_seconds()
    remaining = cooldown_seconds - diff
    if remaining > 0:
        return int(remaining)
    return None


def seconds_to_str(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m}m {s}s"
    else:
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h}h {m}m {s}s"


def get_card_value(card: str) -> int:
    val = card[:-2]
    if val in ("J", "Q", "K"):
        return 10
    if val == "A":
        return 11
    return int(val)


def hand_value(hand: list) -> int:
    total = sum(get_card_value(c) for c in hand)
    aces = sum(1 for c in hand if c.startswith("A"))
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def format_hand(hand: list) -> str:
    return "  ".join(hand)


import random


def new_deck() -> list:
    suits = list(CARD_SUITS.keys())
    deck = [f"{v}{s}" for s in suits for v in CARD_VALUES]
    random.shuffle(deck)
    return deck


def cooldown_embed(field: str, remaining: int) -> discord.Embed:
    names = {
        "last_daily": "Dzienny bonus",
        "last_work": "Praca",
        "last_beg": "Żebranie",
        "last_crime": "Przestępstwo",
        "last_rob": "Kradzież",
    }
    label = names.get(field, field)
    return make_embed(
        title="⏳ Cooldown!",
        description=f"**{label}** będzie dostępne za **{seconds_to_str(remaining)}**.",
        color=LOSE_COLOR,
    )
