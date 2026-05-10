import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import database as db
import utils


MIN_BET = 10
MAX_BET = 50000

SPIN_LEVELS = {
    "low": {
        "label": "Niskie Ryzyko",
        "emoji": "🟢",
        "segments": [
            ("PRZEGRANA", 0, 0.40),
            ("x0.5", 0.5, 0.20),
            ("x1.5", 1.5, 0.20),
            ("x2", 2.0, 0.12),
            ("x3", 3.0, 0.06),
            ("x5", 5.0, 0.02),
        ],
    },
    "medium": {
        "label": "Średnie Ryzyko",
        "emoji": "🟡",
        "segments": [
            ("PRZEGRANA", 0, 0.35),
            ("x0.5", 0.5, 0.15),
            ("x1.5", 1.5, 0.18),
            ("x2", 2.0, 0.15),
            ("x3.5", 3.5, 0.10),
            ("x6", 6.0, 0.05),
            ("x10", 10.0, 0.02),
        ],
    },
    "high": {
        "label": "Wysokie Ryzyko",
        "emoji": "🔴",
        "segments": [
            ("PRZEGRANA", 0, 0.55),
            ("x0.5", 0.5, 0.10),
            ("x2", 2.0, 0.15),
            ("x5", 5.0, 0.10),
            ("x10", 10.0, 0.06),
            ("x20", 20.0, 0.03),
            ("x50 JACKPOT", 50.0, 0.01),
        ],
    },
}

SLOT_SYMBOLS = [
    ("🍒", 2.0, 0.25),
    ("🍋", 2.5, 0.20),
    ("🍊", 3.0, 0.18),
    ("🍇", 4.0, 0.15),
    ("🔔", 5.0, 0.10),
    ("💎", 8.0, 0.07),
    ("7️⃣", 15.0, 0.04),
    ("🃏", 25.0, 0.01),
]

SLOT_SPINNING_FRAMES = [
    ["❓", "❓", "❓"],
    ["🎰", "❓", "❓"],
    ["🎰", "🎰", "❓"],
]

ROULETTE_NUMBERS = list(range(0, 37))
ROULETTE_RED = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
ROULETTE_BLACK = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}


def spin_weighted(segments):
    labels = [s[0] for s in segments]
    multipliers = [s[1] for s in segments]
    weights = [s[2] for s in segments]
    idx = random.choices(range(len(segments)), weights=weights, k=1)[0]
    return labels[idx], multipliers[idx]


def spin_slots():
    symbols = [s[0] for s in SLOT_SYMBOLS]
    weights = [s[2] for s in SLOT_SYMBOLS]
    reels = random.choices(symbols, weights=weights, k=3)
    if reels[0] == reels[1] == reels[2]:
        mult = next(s[1] for s in SLOT_SYMBOLS if s[0] == reels[0])
        return reels, mult, True
    elif reels[0] == reels[1] or reels[1] == reels[2]:
        return reels, 1.5, False
    return reels, 0, False


def validate_bet(amount: int, balance: int):
    if amount < MIN_BET:
        return f"Minimalna stawka to {utils.format_currency(MIN_BET)}!"
    if amount > MAX_BET:
        return f"Maksymalna stawka to {utils.format_currency(MAX_BET)}!"
    if amount > balance:
        return f"Masz tylko {utils.format_currency(balance)} w kieszeni!"
    return None


class BlackjackView(discord.ui.View):
    def __init__(self, player_hand, dealer_hand, deck, bet, user_id):
        super().__init__(timeout=60)
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.deck = deck
        self.bet = bet
        self.user_id = user_id
        self.finished = False

    def make_embed(self, title="🃏 Blackjack", reveal_dealer=False, extra=""):
        player_val = utils.hand_value(self.player_hand)
        dealer_visible = self.dealer_hand if reveal_dealer else [self.dealer_hand[0], "🂠"]
        dealer_val = utils.hand_value(self.dealer_hand) if reveal_dealer else utils.get_card_value(self.dealer_hand[0])

        color = utils.INFO_COLOR
        if reveal_dealer:
            pv = utils.hand_value(self.player_hand)
            dv = utils.hand_value(self.dealer_hand)
            if pv > 21:
                color = utils.LOSE_COLOR
            elif dv > 21 or pv > dv:
                color = utils.WIN_COLOR
            elif pv == dv:
                color = utils.NEUTRAL_COLOR
            else:
                color = utils.LOSE_COLOR

        embed = discord.Embed(title=title, color=color)
        embed.add_field(
            name=f"🎴 Twoje Karty (Wartość: {player_val})",
            value=utils.format_hand(self.player_hand),
            inline=False,
        )
        embed.add_field(
            name=f"🏠 Krupier (Wartość: {'?' if not reveal_dealer else dealer_val})",
            value=utils.format_hand(dealer_visible),
            inline=False,
        )
        embed.add_field(name="💰 Stawka", value=utils.format_currency(self.bet), inline=True)
        if extra:
            embed.add_field(name="📢 Wynik", value=extra, inline=False)
        embed.set_thumbnail(url=utils.CARD_GIFS["deal"])
        embed.timestamp = __import__("datetime").datetime.utcnow()
        return embed

    async def end_game(self, interaction, reason=""):
        self.finished = True
        for item in self.children:
            item.disabled = True

        player_val = utils.hand_value(self.player_hand)
        dealer_val = utils.hand_value(self.dealer_hand)

        if player_val > 21:
            result = "przegrana"
            payout = -self.bet
            msg = f"💥 Przekroczyłeś 21! Przegrałeś {utils.format_currency(self.bet)}."
            gif = utils.CARD_GIFS["bust"]
            won = False
        elif dealer_val > 21 or player_val > dealer_val:
            if player_val == 21 and len(self.player_hand) == 2:
                result = "blackjack"
                payout = int(self.bet * 1.5)
                msg = f"🎉 BLACKJACK! Wygrałeś {utils.format_currency(payout)}!"
                gif = utils.CARD_GIFS["blackjack"]
            else:
                result = "wygrana"
                payout = self.bet
                msg = f"🏆 Wygrałeś {utils.format_currency(payout)}!"
                gif = utils.CARD_GIFS["win"]
            won = True
        elif player_val == dealer_val:
            result = "remis"
            payout = 0
            msg = "🤝 Remis! Odzyskujesz swoją stawkę."
            gif = utils.CARD_GIFS["deal"]
            won = True
        else:
            result = "przegrana"
            payout = -self.bet
            msg = f"😔 Przegrałeś {utils.format_currency(self.bet)}."
            gif = utils.CARD_GIFS["lose"]
            won = False

        await db.update_balance(self.user_id, payout)
        await db.log_transaction(self.user_id, payout, "blackjack", result)
        await db.record_game(self.user_id, "blackjack", won, payout)

        embed = self.make_embed(reveal_dealer=True, extra=msg)
        embed.set_image(url=gif)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🃏 Dobierz", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("To nie twoja gra!", ephemeral=True)
            return
        self.player_hand.append(self.deck.pop())
        if utils.hand_value(self.player_hand) > 21:
            await self.end_game(interaction, "bust")
        else:
            await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="✋ Stój", style=discord.ButtonStyle.secondary)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("To nie twoja gra!", ephemeral=True)
            return
        while utils.hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.pop())
        await self.end_game(interaction)

    @discord.ui.button(label="✖️ Double Down", style=discord.ButtonStyle.danger)
    async def double_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("To nie twoja gra!", ephemeral=True)
            return
        user = await db.get_user(self.user_id)
        if user["balance"] < self.bet:
            await interaction.response.send_message(
                "Nie masz wystarczająco Crypto na double down!", ephemeral=True
            )
            return
        await db.update_balance(self.user_id, -self.bet)
        self.bet *= 2
        self.player_hand.append(self.deck.pop())
        while utils.hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.pop())
        await self.end_game(interaction, "double")

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="spin", description="Zakręć kołem fortuny!")
    @app_commands.describe(
        kwota="Kwota do postawienia",
        ryzyko="Poziom ryzyka: low, medium, high",
    )
    @app_commands.choices(
        ryzyko=[
            app_commands.Choice(name="🟢 Niskie (low)", value="low"),
            app_commands.Choice(name="🟡 Średnie (medium)", value="medium"),
            app_commands.Choice(name="🔴 Wysokie (high)", value="high"),
        ]
    )
    async def spin(self, interaction: discord.Interaction, kwota: int, ryzyko: str = "medium"):
        user = await db.get_user(interaction.user.id)
        err = validate_bet(kwota, user["balance"])
        if err:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", err, utils.LOSE_COLOR), ephemeral=True
            )
            return

        level = SPIN_LEVELS[ryzyko]
        await db.update_balance(interaction.user.id, -kwota)

        spin_embed = utils.make_embed(
            title="🎡 Koło Fortuny — Kręci się...",
            description=f"**{level['emoji']} Poziom:** {level['label']}\n"
                        f"**💰 Stawka:** {utils.format_currency(kwota)}\n\n"
                        f"🎡 ✨ *Koło się kręci... trzymaj kciuki!* ✨ 🎡",
            color=utils.JACKPOT_COLOR,
            gif_url=utils.SPIN_GIFS["spinning"],
        )
        spin_embed.set_footer(text="Koło fortuny Crypto Casino")
        await interaction.response.send_message(embed=spin_embed)
        await asyncio.sleep(3)

        label, multiplier = spin_weighted(level["segments"])
        winnings = int(kwota * multiplier)
        net = winnings - kwota

        if multiplier == 0:
            color = utils.LOSE_COLOR
            gif = utils.SPIN_GIFS["lose"]
            result_text = f"💔 **PRZEGRANA!**\nKoło zatrzymało się na: **{label}**\nStrata: {utils.format_currency(kwota)}"
            won = False
        elif multiplier >= 20:
            color = utils.JACKPOT_COLOR
            gif = utils.SPIN_GIFS["jackpot"]
            result_text = f"🏆 **JACKPOT!!!**\nKoło zatrzymało się na: **{label}**\n\nWygrana: {utils.format_currency(winnings)}\nZysk netto: **+{utils.format_currency(net)}**"
            await db.update_balance(interaction.user.id, winnings)
            won = True
        elif multiplier >= 3:
            color = utils.WIN_COLOR
            gif = utils.SPIN_GIFS["win_big"]
            result_text = f"🎉 **DUŻA WYGRANA!**\nKoło zatrzymało się na: **{label}**\n\nWygrana: {utils.format_currency(winnings)}\nZysk netto: **+{utils.format_currency(net)}**"
            await db.update_balance(interaction.user.id, winnings)
            won = True
        else:
            color = utils.WIN_COLOR if net >= 0 else utils.LOSE_COLOR
            gif = utils.SPIN_GIFS["win_small"]
            sign = "+" if net >= 0 else ""
            result_text = f"✅ **WYGRANA!**\nKoło zatrzymało się na: **{label}**\n\nWygrana: {utils.format_currency(winnings)}\nZysk netto: **{sign}{utils.format_currency(net)}**"
            await db.update_balance(interaction.user.id, winnings)
            won = net >= 0

        await db.log_transaction(interaction.user.id, net, "spin", f"Spin {ryzyko}: {label}")
        await db.record_game(interaction.user.id, "spin", won, net)

        result_embed = utils.make_embed(
            title="🎡 Wynik Koła Fortuny",
            description=result_text,
            color=color,
            gif_url=gif,
        )
        result_embed.add_field(name="🎰 Poziom Ryzyka", value=f"{level['emoji']} {level['label']}", inline=True)
        result_embed.add_field(name="💎 Mnożnik", value=f"**x{multiplier}**", inline=True)

        user_after = await db.get_user(interaction.user.id)
        result_embed.add_field(
            name="💰 Stan konta", value=utils.format_currency(user_after["balance"]), inline=True
        )
        result_embed.set_footer(text="Crypto Casino | /spin aby zagrać ponownie")

        await interaction.edit_original_response(embed=result_embed)

    @app_commands.command(name="blackjack", description="Zagraj w Blackjacka!")
    @app_commands.describe(kwota="Kwota do postawienia")
    async def blackjack(self, interaction: discord.Interaction, kwota: int):
        user = await db.get_user(interaction.user.id)
        err = validate_bet(kwota, user["balance"])
        if err:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", err, utils.LOSE_COLOR), ephemeral=True
            )
            return

        await db.update_balance(interaction.user.id, -kwota)

        deal_embed = utils.make_embed(
            title="🃏 Blackjack — Rozdawanie Kart...",
            description="*Krupier tasuje i rozdaje karty...*",
            color=utils.INFO_COLOR,
            gif_url=utils.CARD_GIFS["deal"],
        )
        await interaction.response.send_message(embed=deal_embed)
        await asyncio.sleep(2)

        deck = utils.new_deck()
        player = [deck.pop(), deck.pop()]
        dealer = [deck.pop(), deck.pop()]

        view = BlackjackView(player, dealer, deck, kwota, interaction.user.id)

        if utils.hand_value(player) == 21:
            payout = int(kwota * 1.5)
            await db.update_balance(interaction.user.id, kwota + payout)
            await db.log_transaction(interaction.user.id, payout, "blackjack", "blackjack")
            await db.record_game(interaction.user.id, "blackjack", True, payout)
            bj_embed = utils.make_embed(
                title="🃏 BLACKJACK!",
                description=f"🎉 Niesamowite! Dostałeś Blackjacka przy rozdaniu!\n\n"
                            f"Twoje karty: {utils.format_hand(player)} (21)\n"
                            f"Wygrana: {utils.format_currency(payout)}",
                color=utils.JACKPOT_COLOR,
                gif_url=utils.CARD_GIFS["blackjack"],
            )
            await interaction.edit_original_response(embed=bj_embed, view=None)
            return

        game_embed = view.make_embed()
        await interaction.edit_original_response(embed=game_embed, view=view)

    @app_commands.command(name="slots", description="Zagraj w automaty!")
    @app_commands.describe(kwota="Kwota do postawienia")
    async def slots(self, interaction: discord.Interaction, kwota: int):
        user = await db.get_user(interaction.user.id)
        err = validate_bet(kwota, user["balance"])
        if err:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", err, utils.LOSE_COLOR), ephemeral=True
            )
            return

        await db.update_balance(interaction.user.id, -kwota)

        spin_embed = utils.make_embed(
            title="🎰 Automaty — Kręcę...",
            description="```\n[ ❓ | ❓ | ❓ ]\n```\n*Kręcę bębny...*",
            color=utils.JACKPOT_COLOR,
            gif_url=utils.SLOT_GIFS["spinning"],
        )
        await interaction.response.send_message(embed=spin_embed)

        for frame in SLOT_SPINNING_FRAMES:
            await asyncio.sleep(0.8)
            frame_display = " | ".join(frame)
            frame_embed = utils.make_embed(
                title="🎰 Automaty — Kręcę...",
                description=f"```\n[ {frame_display} ]\n```\n*Kręcę bębny...*",
                color=utils.JACKPOT_COLOR,
                gif_url=utils.SLOT_GIFS["spinning"],
            )
            await interaction.edit_original_response(embed=frame_embed)

        await asyncio.sleep(1)
        reels, multiplier, is_jackpot = spin_slots()
        reels_display = " | ".join(reels)

        winnings = int(kwota * multiplier) if multiplier > 0 else 0
        net = winnings - kwota
        won = winnings > 0

        if is_jackpot and multiplier >= 15:
            color = utils.JACKPOT_COLOR
            gif = utils.SLOT_GIFS["win"]
            msg = f"🏆 **JACKPOT!!!** Trzy {reels[0]} na raz!\nWygrana: {utils.format_currency(winnings)}"
        elif multiplier > 0:
            color = utils.WIN_COLOR if net >= 0 else utils.NEUTRAL_COLOR
            gif = utils.SLOT_GIFS["win"]
            msg = f"✅ **Wygrana!** Mnożnik: **x{multiplier}**\nWygrana: {utils.format_currency(winnings)}"
        else:
            color = utils.LOSE_COLOR
            gif = utils.SLOT_GIFS["lose"]
            msg = f"💔 **Przegrana!**\nStrata: {utils.format_currency(kwota)}"

        if winnings > 0:
            await db.update_balance(interaction.user.id, winnings)

        await db.log_transaction(interaction.user.id, net, "slots", f"Slots: {reels_display}")
        await db.record_game(interaction.user.id, "slots", won, net)

        result_embed = utils.make_embed(
            title="🎰 Wynik Automatów",
            description=f"```\n[ {reels_display} ]\n```\n{msg}",
            color=color,
            gif_url=gif,
        )
        result_embed.add_field(name="💰 Stawka", value=utils.format_currency(kwota), inline=True)
        result_embed.add_field(name="💎 Mnożnik", value=f"x{multiplier}", inline=True)
        sign = "+" if net >= 0 else ""
        result_embed.add_field(name="📊 Bilans", value=f"{sign}{utils.format_currency(net)}", inline=True)

        await interaction.edit_original_response(embed=result_embed)

    @app_commands.command(name="coinflip", description="Rzuć monetą!")
    @app_commands.describe(kwota="Kwota do postawienia", wybor="Orzeł lub Reszka")
    @app_commands.choices(
        wybor=[
            app_commands.Choice(name="🦅 Orzeł", value="orzel"),
            app_commands.Choice(name="🌟 Reszka", value="reszka"),
        ]
    )
    async def coinflip(self, interaction: discord.Interaction, kwota: int, wybor: str):
        user = await db.get_user(interaction.user.id)
        err = validate_bet(kwota, user["balance"])
        if err:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", err, utils.LOSE_COLOR), ephemeral=True
            )
            return

        await db.update_balance(interaction.user.id, -kwota)

        flip_embed = utils.make_embed(
            title="🪙 Rzut Monetą",
            description=f"Twój wybór: **{'🦅 Orzeł' if wybor == 'orzel' else '🌟 Reszka'}**\n\n*Rzucam monetą...*",
            color=utils.INFO_COLOR,
        )
        await interaction.response.send_message(embed=flip_embed)
        await asyncio.sleep(1.5)

        result = random.choice(["orzel", "reszka"])
        won = result == wybor
        result_label = "🦅 Orzeł" if result == "orzel" else "🌟 Reszka"

        if won:
            await db.update_balance(interaction.user.id, kwota * 2)
            await db.log_transaction(interaction.user.id, kwota, "coinflip", "wygrana")
            await db.record_game_no_stats(interaction.user.id, "coinflip", True, kwota)
            embed = utils.make_embed(
                title="🪙 Rzut Monetą — Wygrana!",
                description=f"Wypadło: **{result_label}**\n\n"
                            f"✅ Trafiłeś! Wygrałeś {utils.format_currency(kwota)}!",
                color=utils.WIN_COLOR,
            )
        else:
            await db.log_transaction(interaction.user.id, -kwota, "coinflip", "przegrana")
            await db.record_game_no_stats(interaction.user.id, "coinflip", False, -kwota)
            embed = utils.make_embed(
                title="🪙 Rzut Monetą — Przegrana",
                description=f"Wypadło: **{result_label}**\n\n"
                            f"💔 Pudło! Przegrałeś {utils.format_currency(kwota)}.",
                color=utils.LOSE_COLOR,
            )

        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="roulette", description="Zagraj w ruletkę!")
    @app_commands.describe(kwota="Kwota do postawienia", zaklad="Twój zakład")
    @app_commands.choices(
        zaklad=[
            app_commands.Choice(name="🔴 Czerwony (x2)", value="czerwony"),
            app_commands.Choice(name="⚫ Czarny (x2)", value="czarny"),
            app_commands.Choice(name="🟢 Zero (x14)", value="zero"),
            app_commands.Choice(name="🔢 Parzyste (x2)", value="parzyste"),
            app_commands.Choice(name="🔢 Nieparzyste (x2)", value="nieparzyste"),
            app_commands.Choice(name="📉 1-18 (x2)", value="niskie"),
            app_commands.Choice(name="📈 19-36 (x2)", value="wysokie"),
        ]
    )
    async def roulette(self, interaction: discord.Interaction, kwota: int, zaklad: str):
        user = await db.get_user(interaction.user.id)
        err = validate_bet(kwota, user["balance"])
        if err:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", err, utils.LOSE_COLOR), ephemeral=True
            )
            return

        await db.update_balance(interaction.user.id, -kwota)

        spin_embed = utils.make_embed(
            title="🎡 Ruletka — Kółko się Kręci...",
            description=f"**Twój zakład:** {zaklad.upper()}\n**Stawka:** {utils.format_currency(kwota)}\n\n*Kulka wiruje...*",
            color=utils.INFO_COLOR,
            gif_url=utils.ROULETTE_GIFS["spinning"],
        )
        await interaction.response.send_message(embed=spin_embed)
        await asyncio.sleep(3)

        number = random.choice(ROULETTE_NUMBERS)
        color_str = "🟢 Zielony (0)" if number == 0 else ("🔴 Czerwony" if number in ROULETTE_RED else "⚫ Czarny")

        won = False
        multiplier = 2
        if zaklad == "czerwony" and number in ROULETTE_RED:
            won = True
        elif zaklad == "czarny" and number in ROULETTE_BLACK:
            won = True
        elif zaklad == "zero" and number == 0:
            won, multiplier = True, 14
        elif zaklad == "parzyste" and number != 0 and number % 2 == 0:
            won = True
        elif zaklad == "nieparzyste" and number % 2 == 1:
            won = True
        elif zaklad == "niskie" and 1 <= number <= 18:
            won = True
        elif zaklad == "wysokie" and 19 <= number <= 36:
            won = True

        if won:
            payout = kwota * multiplier
            net = payout - kwota
            await db.update_balance(interaction.user.id, payout)
            await db.log_transaction(interaction.user.id, net, "roulette", f"wygrana {zaklad}")
            await db.record_game_no_stats(interaction.user.id, "roulette", True, net)
            embed = utils.make_embed(
                title="🎡 Ruletka — Wygrana!",
                description=f"Kulka zatrzymała się na: **{number}** ({color_str})\n\n"
                            f"✅ Wygrałeś! Wygrana: {utils.format_currency(payout)}",
                color=utils.WIN_COLOR,
                gif_url=utils.ROULETTE_GIFS["win"],
            )
        else:
            await db.log_transaction(interaction.user.id, -kwota, "roulette", f"przegrana {zaklad}")
            await db.record_game_no_stats(interaction.user.id, "roulette", False, -kwota)
            embed = utils.make_embed(
                title="🎡 Ruletka — Przegrana",
                description=f"Kulka zatrzymała się na: **{number}** ({color_str})\n\n"
                            f"💔 Przegrałeś {utils.format_currency(kwota)}.",
                color=utils.LOSE_COLOR,
                gif_url=utils.ROULETTE_GIFS["lose"],
            )

        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="mines", description="Zagraj w Miny — znajdź gwiazdy, unikaj min!")
    @app_commands.describe(kwota="Kwota do postawienia", miny="Liczba min (1-20)")
    async def mines(self, interaction: discord.Interaction, kwota: int, miny: int = 5):
        user = await db.get_user(interaction.user.id)
        err = validate_bet(kwota, user["balance"])
        if err:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", err, utils.LOSE_COLOR), ephemeral=True
            )
            return
        if not (1 <= miny <= 20):
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", "Liczba min musi być między 1 a 20!", utils.LOSE_COLOR), ephemeral=True
            )
            return

        await db.update_balance(interaction.user.id, -kwota)

        grid_size = 25
        mine_positions = set(random.sample(range(grid_size), miny))
        revealed = set()
        current_multiplier = 1.0
        stars_per_reveal = round(1 + miny / (grid_size - miny), 2)

        view = MinesView(
            mine_positions=mine_positions,
            revealed=revealed,
            bet=kwota,
            user_id=interaction.user.id,
            multiplier=current_multiplier,
            stars_per_reveal=stars_per_reveal,
            grid_size=grid_size,
        )
        embed = view.make_embed()
        await interaction.response.send_message(embed=embed, view=view)


class MinesView(discord.ui.View):
    def __init__(self, mine_positions, revealed, bet, user_id, multiplier, stars_per_reveal, grid_size=25):
        super().__init__(timeout=120)
        self.mine_positions = mine_positions
        self.revealed = revealed
        self.bet = bet
        self.user_id = user_id
        self.multiplier = multiplier
        self.stars_per_reveal = stars_per_reveal
        self.grid_size = grid_size
        self.finished = False
        self.safe_found = 0
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        unrevealed = [i for i in range(self.grid_size) if i not in self.revealed]
        sample = unrevealed[:20] if len(unrevealed) > 20 else unrevealed
        random.shuffle(sample)
        for pos in sample[:20]:
            btn = discord.ui.Button(
                label="?",
                style=discord.ButtonStyle.secondary,
                custom_id=f"mine_{pos}",
                row=pos // 5 if pos // 5 < 4 else 3,
            )
            btn.callback = self._make_callback(pos)
            self.add_item(btn)
        cashout_btn = discord.ui.Button(
            label=f"💰 Wypłać (x{self.multiplier:.2f})",
            style=discord.ButtonStyle.success,
            custom_id="cashout",
            row=4,
        )
        cashout_btn.callback = self.cashout_callback
        self.add_item(cashout_btn)

    def _make_callback(self, pos):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("To nie twoja gra!", ephemeral=True)
                return
            if pos in self.mine_positions:
                self.finished = True
                for item in self.children:
                    item.disabled = True
                await db.log_transaction(self.user_id, -self.bet, "mines", "trafiono minę")
                await db.record_game_no_stats(self.user_id, "mines", False, -self.bet)
                embed = utils.make_embed(
                    title="💣 BOOM! Trafiłeś w Minę!",
                    description=f"Wybuchło! Straciłeś {utils.format_currency(self.bet)}.\n"
                                f"Odkryto {self.safe_found} bezpiecznych pól.",
                    color=utils.LOSE_COLOR,
                )
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                self.revealed.add(pos)
                self.safe_found += 1
                self.multiplier = round(self.multiplier + self.stars_per_reveal, 2)
                self._build_buttons()
                embed = self.make_embed()
                await interaction.response.edit_message(embed=embed, view=self)
        return callback

    async def cashout_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("To nie twoja gra!", ephemeral=True)
            return
        self.finished = True
        payout = int(self.bet * self.multiplier)
        net = payout - self.bet
        await db.update_balance(self.user_id, payout)
        await db.log_transaction(self.user_id, net, "mines", f"cashout x{self.multiplier}")
        await db.record_game_no_stats(self.user_id, "mines", True, net)
        for item in self.children:
            item.disabled = True
        embed = utils.make_embed(
            title="💰 Wypłata z Gry Miny!",
            description=f"Odkryto {self.safe_found} bezpiecznych pól!\n"
                        f"Mnożnik: **x{self.multiplier}**\n"
                        f"Wypłata: {utils.format_currency(payout)}\n"
                        f"Zysk: +{utils.format_currency(net)}",
            color=utils.WIN_COLOR,
        )
        await interaction.response.edit_message(embed=embed, view=self)

    def make_embed(self):
        current_payout = int(self.bet * self.multiplier)
        embed = discord.Embed(
            title="💣 Miny — Znajdź Gwiazdy!",
            description=f"Odkryte pola: **{self.safe_found}**\n"
                        f"Aktualny mnożnik: **x{self.multiplier:.2f}**\n"
                        f"Potencjalna wypłata: {utils.format_currency(current_payout)}\n\n"
                        f"*Kliknij pole aby odkryć. Unikaj min! 💣*",
            color=utils.INFO_COLOR,
        )
        embed.add_field(name="💰 Stawka", value=utils.format_currency(self.bet), inline=True)
        embed.add_field(name="💣 Miny", value=f"{len(self.mine_positions)}", inline=True)
        embed.timestamp = __import__("datetime").datetime.utcnow()
        return embed

    async def on_timeout(self):
        if not self.finished:
            await db.log_transaction(self.user_id, -self.bet, "mines", "timeout")
            await db.record_game_no_stats(self.user_id, "mines", False, -self.bet)
        for item in self.children:
            item.disabled = True


async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))
