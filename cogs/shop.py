import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import database as db
import utils

# =========================
# PRZEDMIOTY SKLEPU
# =========================
SHOP_ITEMS = {
    "vip": {
        "id": "vip",
        "nazwa": "👑 VIP Status",
        "opis": "Zwiększa dzienny bonus o +300 💎 i daje złoty kolor w /top.",
        "cena": 5000,
        "emoji": "👑",
        "efekt": "daily_bonus +300",
        "czas_trwania": None,
        "kategoria": "status",
    },
    "lucky_charm": {
        "id": "lucky_charm",
        "nazwa": "🍀 Szczęśliwy Talizman",
        "opis": "Zwiększa szansę wygranej w /spin i /slot o +5% przez 24h.",
        "cena": 2000,
        "emoji": "🍀",
        "efekt": "luck +5%",
        "czas_trwania": "24h",
        "kategoria": "boosters",
    },
    "shield": {
        "id": "shield",
        "nazwa": "🛡️ Tarcza Bankowa",
        "opis": "Chroni kieszeń przed /okradnij przez 12h. Złodziej dostaje karę bez efektu.",
        "cena": 1500,
        "emoji": "🛡️",
        "efekt": "rob_immunity 12h",
        "czas_trwania": "12h",
        "kategoria": "ochrona",
    },
    "work_boost": {
        "id": "work_boost",
        "nazwa": "⚡ Turbo Praca",
        "opis": "Podwaja zarobki z /pracuj przez 6h.",
        "cena": 1200,
        "emoji": "⚡",
        "efekt": "work x2",
        "czas_trwania": "6h",
        "kategoria": "boosters",
    },
    "daily_boost": {
        "id": "daily_boost",
        "nazwa": "🎁 Mega Dzienny",
        "opis": "Następny /daily daje 3x normalną kwotę (jednorazowe).",
        "cena": 3000,
        "emoji": "🎁",
        "efekt": "next_daily x3",
        "czas_trwania": "jednorazowe",
        "kategoria": "boosters",
    },
    "casino_pass": {
        "id": "casino_pass",
        "nazwa": "🎰 Karnet Kasyna",
        "opis": "Zwiększa max stawkę do 100 000 💎 i dodaje +3% szans przez 12h.",
        "cena": 4000,
        "emoji": "🎰",
        "efekt": "max_bet 100000 + luck +3%",
        "czas_trwania": "12h",
        "kategoria": "boosters",
    },
    "robber_kit": {
        "id": "robber_kit",
        "nazwa": "🥷 Zestaw Złodzieja",
        "opis": "Zwiększa szansę /okradnij z 45% do 70% przez 6h.",
        "cena": 2500,
        "emoji": "🥷",
        "efekt": "rob_boost 70%",
        "czas_trwania": "6h",
        "kategoria": "przestepstwo",
    },
    "crypto_miner": {
        "id": "crypto_miner",
        "nazwa": "⛏️ Kryptokoparki",
        "opis": "Pasywnie generuje 50 💎 co godzinę przez 8h. Użyj /odbierz aby zebrać.",
        "cena": 3500,
        "emoji": "⛏️",
        "efekt": "passive 50/h",
        "czas_trwania": "8h",
        "kategoria": "pasywne",
    },
}

KATEGORIE = {
    "🚀 Boostery":      ["lucky_charm", "work_boost", "daily_boost", "casino_pass"],
    "🛡️ Ochrona":      ["shield"],
    "🥷 Przestępstwo": ["robber_kit"],
    "⛏️ Pasywne":      ["crypto_miner"],
    "👑 Status":        ["vip"],
}


# =========================
# HELPER — sprawdź efekty
# =========================
async def get_luck_bonus(user_id: int) -> float:
    """Zwraca sumę bonusów szczęścia (lucky_charm +0.05, casino_pass +0.03)."""
    bonus = 0.0
    if await db.has_active_item(user_id, "lucky_charm"):
        bonus += 0.05
    if await db.has_active_item(user_id, "casino_pass"):
        bonus += 0.03
    return bonus


async def get_work_multiplier(user_id: int) -> float:
    """Zwraca mnożnik zarobków z /pracuj."""
    if await db.has_active_item(user_id, "work_boost"):
        return 2.0
    return 1.0


async def get_rob_chance(user_id: int) -> float:
    """Zwraca szansę kradzieży."""
    if await db.has_active_item(user_id, "robber_kit"):
        return 0.70
    return 0.45


async def is_shielded(user_id: int) -> bool:
    """Sprawdź czy cel ma tarczę."""
    return await db.has_active_item(user_id, "shield")


async def get_daily_multiplier(user_id: int) -> float:
    """Sprawdź czy dzienny ma boost x3 (jednorazowy)."""
    if await db.has_active_item(user_id, "daily_boost"):
        await db.deactivate_item(user_id, "daily_boost")
        return 3.0
    if await db.has_active_item(user_id, "vip"):
        return 1.0  # VIP dodaje flat +300, nie mnożnik
    return 1.0


async def get_vip_daily_bonus(user_id: int) -> int:
    """VIP daje +300 do daily."""
    if await db.has_active_item(user_id, "vip"):
        return 300
    return 0


async def collect_miner(user_id: int) -> int:
    """
    Oblicz ile 💎 zebrała koparka od ostatniego odbioru.
    Uproszczona wersja: 50/h przez max 8h.
    """
    items = await db.get_inventory(user_id)
    miner = next((i for i in items if i["item_id"] == "crypto_miner" and i["active"]), None)
    if not miner:
        return 0

    bought_at = datetime.fromisoformat(miner["bought_at"])
    now = datetime.utcnow()
    hours = min((now - bought_at).total_seconds() / 3600, 8.0)
    earned = int(hours * 50)
    return max(0, earned)


# =========================
# VIEW — paginacja sklepu
# =========================
class ShopView(discord.ui.View):
    def __init__(self, user_id: int, page: int = 0):
        super().__init__(timeout=90)
        self.user_id = user_id
        self.page = page
        self.all_items = list(SHOP_ITEMS.values())
        self.per_page = 4
        self.max_page = (len(self.all_items) - 1) // self.per_page
        self._refresh_buttons()

    def _refresh_buttons(self):
        for child in self.children:
            if hasattr(child, "custom_id"):
                if child.custom_id == "shop_prev":
                    child.disabled = self.page == 0
                elif child.custom_id == "shop_next":
                    child.disabled = self.page >= self.max_page

    async def make_embed(self, user_id: int) -> discord.Embed:
        data = await db.get_user(user_id)
        balance = data["balance"]

        start = self.page * self.per_page
        items = self.all_items[start:start + self.per_page]

        embed = discord.Embed(
            title="🏪 Sklep Crypto Casino",
            description=(
                f"💎 Twój balans: **{balance:,} Crypto**\n"
                f"Kup komendą `/kup <id>` • Sprawdź `/ekwipunek`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=utils.JACKPOT_COLOR,
        )

        for item in items:
            can = "✅" if balance >= item["cena"] else "❌"
            czas = f" • ⏳ {item['czas_trwania']}" if item["czas_trwania"] else " • ♾️ Trwałe"
            embed.add_field(
                name=f"{item['emoji']} {item['nazwa']}  {can}",
                value=(
                    f"📋 {item['opis']}\n"
                    f"💰 **{item['cena']:,} 💎**{czas}\n"
                    f"🔑 ID: `{item['id']}`"
                ),
                inline=False,
            )

        embed.set_footer(
            text=f"Strona {self.page + 1}/{self.max_page + 1} • ✅ stać cię • ❌ za drogo"
        )
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ To nie twój sklep!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary, custom_id="shop_prev")
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        self._refresh_buttons()
        await interaction.response.edit_message(embed=await self.make_embed(interaction.user.id), view=self)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary, custom_id="shop_next")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        self._refresh_buttons()
        await interaction.response.edit_message(embed=await self.make_embed(interaction.user.id), view=self)

    @discord.ui.button(label="🔄 Odśwież", style=discord.ButtonStyle.primary, custom_id="shop_refresh")
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=await self.make_embed(interaction.user.id), view=self)


# =========================
# COG
# =========================
class Shop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =========================
    # /sklep
    # =========================
    @app_commands.command(name="sklep", description="🏪 Otwórz sklep Crypto Casino")
    async def shop(self, interaction: discord.Interaction):
        view = ShopView(interaction.user.id)
        embed = await view.make_embed(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    # =========================
    # /kup
    # =========================
    @app_commands.command(name="kup", description="💳 Kup przedmiot ze sklepu")
    @app_commands.describe(przedmiot="ID przedmiotu (np. vip, shield, lucky_charm)")
    async def buy(self, interaction: discord.Interaction, przedmiot: str):
        item_id = przedmiot.lower().strip()

        if item_id not in SHOP_ITEMS:
            ids = "  ".join(f"`{k}`" for k in SHOP_ITEMS)
            return await interaction.response.send_message(
                embed=utils.make_embed(
                    "❌ Nieznany Przedmiot",
                    f"Nie ma przedmiotu `{item_id}`.\n\n**Dostępne ID:**\n{ids}",
                    utils.LOSE_COLOR,
                ),
                ephemeral=True,
            )

        item = SHOP_ITEMS[item_id]
        user = await db.get_user(interaction.user.id)

        # Sprawdź środki
        if user["balance"] < item["cena"]:
            brakuje = item["cena"] - user["balance"]
            return await interaction.response.send_message(
                embed=utils.make_embed(
                    "❌ Brak Środków",
                    f"Potrzebujesz **{item['cena']:,} 💎**\n"
                    f"Masz: **{user['balance']:,} 💎**\n"
                    f"Brakuje: **{brakuje:,} 💎**",
                    utils.LOSE_COLOR,
                ),
                ephemeral=True,
            )

        # Sprawdź czy już posiada aktywny
        if await db.has_active_item(interaction.user.id, item_id):
            return await interaction.response.send_message(
                embed=utils.make_embed(
                    "⚠️ Już Posiadasz",
                    f"Masz już aktywny **{item['nazwa']}**!\n"
                    f"Sprawdź `/ekwipunek` aby zobaczyć czas wygaśnięcia.",
                    utils.NEUTRAL_COLOR,
                ),
                ephemeral=True,
            )

        # Kup
        await db.update_balance(interaction.user.id, -item["cena"])
        await db.add_to_inventory(interaction.user.id, item_id, item["czas_trwania"])
        await db.log_transaction(
            interaction.user.id, -item["cena"], "shop_buy",
            f"Zakup: {item['nazwa']}"
        )

        nowy_bal = user["balance"] - item["cena"]
        embed = utils.make_embed(
            title=f"{item['emoji']} Zakup Udany!",
            description=(
                f"Kupiłeś **{item['nazwa']}**!\n\n"
                f"📋 {item['opis']}\n\n"
                f"💰 Zapłacono: **{item['cena']:,} 💎**\n"
                f"💎 Pozostało: **{nowy_bal:,} 💎**"
            ),
            color=utils.WIN_COLOR,
        )
        if item["czas_trwania"] and item["czas_trwania"] != "jednorazowe":
            embed.add_field(name="⏳ Czas", value=f"Aktywny przez: **{item['czas_trwania']}**", inline=True)
        elif item["czas_trwania"] == "jednorazowe":
            embed.add_field(name="⚡ Jednorazowe", value="Efekt aktywuje się automatycznie przy następnym użyciu.", inline=False)
        else:
            embed.add_field(name="♾️ Trwały", value="Ten przedmiot nigdy nie wygasa.", inline=True)

        embed.add_field(name="📦", value="Sprawdź `/ekwipunek`", inline=True)
        await interaction.response.send_message(embed=embed)

    # =========================
    # /ekwipunek
    # =========================
    @app_commands.command(name="ekwipunek", description="🎒 Sprawdź posiadane przedmioty")
    @app_commands.describe(uzytkownik="Użytkownik (opcjonalnie)")
    async def inventory(self, interaction: discord.Interaction, uzytkownik: discord.Member = None):
        target = uzytkownik or interaction.user
        owned = await db.get_inventory(target.id)

        embed = utils.make_embed(
            title=f"🎒 Ekwipunek — {target.display_name}",
            color=utils.INFO_COLOR,
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        if not owned:
            embed.description = "Brak przedmiotów!\n\nKup coś w `/sklep` 🏪"
            return await interaction.response.send_message(embed=embed)

        active = [i for i in owned if i["active"]]
        expired = [i for i in owned if not i["active"]]

        if active:
            lines = []
            for i in active:
                item_data = SHOP_ITEMS.get(i["item_id"])
                if not item_data:
                    continue
                if i["expires_at"]:
                    exp_ts = int(datetime.fromisoformat(i["expires_at"]).timestamp())
                    czas = f"Wygasa <t:{exp_ts}:R>"
                else:
                    czas = "♾️ Trwały"
                lines.append(
                    f"{item_data['emoji']} **{item_data['nazwa']}**\n"
                    f"╰ {item_data['opis'][:70]}\n"
                    f"╰ ⏳ {czas}"
                )
            embed.add_field(
                name=f"✅ Aktywne ({len(active)})",
                value="\n\n".join(lines) or "Brak",
                inline=False,
            )

        if expired:
            names = []
            for i in expired[-5:]:
                d = SHOP_ITEMS.get(i["item_id"])
                if d:
                    names.append(f"{d['emoji']} ~~{d['nazwa']}~~")
            if names:
                embed.add_field(
                    name=f"❌ Wygasłe (ostatnie {len(names)})",
                    value="\n".join(names),
                    inline=False,
                )

        embed.set_footer(text="/sklep • /kup <id> • /odbierz")
        await interaction.response.send_message(embed=embed)

    # =========================
    # /odbierz — koparka
    # =========================
    @app_commands.command(name="odbierz", description="⛏️ Odbierz zarobki z kryptokoparki")
    async def collect(self, interaction: discord.Interaction):
        if not await db.has_active_item(interaction.user.id, "crypto_miner"):
            return await interaction.response.send_message(
                embed=utils.make_embed(
                    "❌ Brak Koparki",
                    "Nie masz aktywnej **⛏️ Kryptokoparki**!\n"
                    "Kup ją w `/sklep` za **3 500 💎**.",
                    utils.LOSE_COLOR,
                ),
                ephemeral=True,
            )

        earned = await collect_miner(interaction.user.id)
        if earned <= 0:
            return await interaction.response.send_message(
                embed=utils.make_embed(
                    "⛏️ Nic do zebrania",
                    "Koparka pracuje! Wróć za chwilę — generuje **50 💎/h**.",
                    utils.NEUTRAL_COLOR,
                ),
                ephemeral=True,
            )

        await db.update_crypto(interaction.user.id, earned)
        await db.log_transaction(interaction.user.id, earned, "miner", "Zarobek z kryptokoparki")

        await interaction.response.send_message(
            embed=utils.make_embed(
                "⛏️ Odebrano zarobki!",
                f"Twoja koparka zarobiła **+{earned:,} 💎**!\n\n"
                f"Koparka generuje **50 💎/h** przez 8h od zakupu.",
                utils.WIN_COLOR,
            )
        )

    # =========================
    # /kategorie — lista po kategorii
    # =========================
    @app_commands.command(name="kategorie", description="📦 Przeglądaj sklep według kategorii")
    async def categories(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📦 Kategorie Sklepu",
            description="Wszystkie przedmioty pogrupowane według typu.",
            color=utils.INFO_COLOR,
        )
        for kat_name, item_ids in KATEGORIE.items():
            lines = []
            for iid in item_ids:
                item = SHOP_ITEMS.get(iid)
                if item:
                    lines.append(f"{item['emoji']} **{item['nazwa']}** — {item['cena']:,} 💎 • `{iid}`")
            embed.add_field(name=kat_name, value="\n".join(lines) or "Brak", inline=False)
        embed.set_footer(text="/sklep • /kup <id>")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Shop(bot))

