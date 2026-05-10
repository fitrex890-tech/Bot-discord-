import discord
from discord.ext import commands
from discord import app_commands
import database as db
import utils

SHOP_ITEMS = {
    "vip": {
        "id": "vip",
        "nazwa": "👑 VIP Status",
        "opis": "Zwiększa dzienny bonus o +300 Crypto i daje złoty kolor nazwy w /top.",
        "cena": 5000,
        "emoji": "👑",
        "efekt": "daily_bonus +300",
        "czas_trwania": None,
    },
    "lucky_charm": {
        "id": "lucky_charm",
        "nazwa": "🍀 Szczęśliwy Talizman",
        "opis": "Zwiększa szansę na wygraną w /spin i /slots o 5% przez 24 godziny.",
        "cena": 2000,
        "emoji": "🍀",
        "efekt": "luck +5%",
        "czas_trwania": "24h",
    },
    "shield": {
        "id": "shield",
        "nazwa": "🛡️ Tarcza Bankowa",
        "opis": "Chroni całą kieszeń przed kradzieżą przez 12 godzin.",
        "cena": 1500,
        "emoji": "🛡️",
        "efekt": "rob_immunity 12h",
        "czas_trwania": "12h",
    },
    "work_boost": {
        "id": "work_boost",
        "nazwa": "⚡ Turbo Praca",
        "opis": "Podwaja zarobki z /pracuj przez 6 godzin.",
        "cena": 1200,
        "emoji": "⚡",
        "efekt": "work_boost x2",
        "czas_trwania": "6h",
    },
    "daily_boost": {
        "id": "daily_boost",
        "nazwa": "🎁 Mega Dzienny",
        "opis": "Następny /daily daje 3x normalną kwotę (jednorazowe).",
        "cena": 3000,
        "emoji": "🎁",
        "efekt": "next_daily x3",
        "czas_trwania": "jednorazowe",
    },
    "casino_pass": {
        "id": "casino_pass",
        "nazwa": "🎰 Karnet Kasyna",
        "opis": "Zwiększa maksymalną stawkę do 100,000 Crypto przez 12 godzin.",
        "cena": 4000,
        "emoji": "🎰",
        "efekt": "max_bet 100000",
        "czas_trwania": "12h",
    },
    "robber_kit": {
        "id": "robber_kit",
        "nazwa": "🥷 Zestaw Złodzieja",
        "opis": "Zwiększa szansę powodzenia /okradnij do 70% przez 6 godzin.",
        "cena": 2500,
        "emoji": "🥷",
        "efekt": "rob_boost 70%",
        "czas_trwania": "6h",
    },
    "crypto_miner": {
        "id": "crypto_miner",
        "nazwa": "⛏️ Kryptokoparki",
        "opis": "Pasywnie generuje 50 Crypto co godzinę przez 8 godzin.",
        "cena": 3500,
        "emoji": "⛏️",
        "efekt": "passive 50/h",
        "czas_trwania": "8h",
    },
}

CATEGORIES = {
    "boosters": ["lucky_charm", "work_boost", "daily_boost", "casino_pass"],
    "ochrona": ["shield"],
    "przestepstwo": ["robber_kit"],
    "pasywne": ["crypto_miner"],
    "status": ["vip"],
}


class ShopView(discord.ui.View):
    def __init__(self, user_id: int, page: int = 0):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.page = page
        self.items_per_page = 4
        self.all_items = list(SHOP_ITEMS.values())
        self.max_pages = (len(self.all_items) - 1) // self.items_per_page
        self._update_buttons()

    def _update_buttons(self):
        for item in self.children:
            if hasattr(item, "custom_id"):
                if item.custom_id == "prev":
                    item.disabled = self.page == 0
                elif item.custom_id == "next":
                    item.disabled = self.page >= self.max_pages

    def make_embed(self, user_balance: int) -> discord.Embed:
        start = self.page * self.items_per_page
        end = start + self.items_per_page
        page_items = self.all_items[start:end]

        embed = discord.Embed(
            title="🏪 Sklep Crypto Casino",
            description=(
                f"💎 Twój balans: **{user_balance:,} Crypto**\n"
                f"Użyj `/kup <id_przedmiotu>` aby kupić.\n"
                f"Sprawdź posiadane przedmioty: `/ekwipunek`\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=utils.JACKPOT_COLOR,
        )

        for item in page_items:
            can_afford = "✅" if user_balance >= item["cena"] else "❌"
            czas = f" ⏳ {item['czas_trwania']}" if item["czas_trwania"] else ""
            embed.add_field(
                name=f"{item['emoji']} {item['nazwa']}  {can_afford}",
                value=(
                    f"📋 {item['opis']}\n"
                    f"💰 Cena: **{item['cena']:,} Crypto**{czas}\n"
                    f"🔑 ID: `{item['id']}`"
                ),
                inline=False,
            )

        embed.set_footer(
            text=f"Strona {self.page + 1}/{self.max_pages + 1} | ✅ = stać cię, ❌ = za drogo"
        )
        return embed

    @discord.ui.button(label="◀️ Poprzednia", style=discord.ButtonStyle.secondary, custom_id="prev")
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("To nie twój sklep!", ephemeral=True)
            return
        self.page -= 1
        self._update_buttons()
        user = await db.get_user(interaction.user.id)
        await interaction.response.edit_message(embed=self.make_embed(user["balance"]), view=self)

    @discord.ui.button(label="Następna ▶️", style=discord.ButtonStyle.secondary, custom_id="next")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("To nie twój sklep!", ephemeral=True)
            return
        self.page += 1
        self._update_buttons()
        user = await db.get_user(interaction.user.id)
        await interaction.response.edit_message(embed=self.make_embed(user["balance"]), view=self)


class Shop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="sklep", description="Otwórz sklep Crypto Casino")
    async def shop(self, interaction: discord.Interaction):
        user = await db.get_user(interaction.user.id)
        view = ShopView(interaction.user.id)
        embed = view.make_embed(user["balance"])
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="kup", description="Kup przedmiot ze sklepu")
    @app_commands.describe(przedmiot="ID przedmiotu (np. vip, shield, lucky_charm)")
    async def buy(self, interaction: discord.Interaction, przedmiot: str):
        item_id = przedmiot.lower().strip()
        if item_id not in SHOP_ITEMS:
            ids = ", ".join(f"`{k}`" for k in SHOP_ITEMS)
            await interaction.response.send_message(
                embed=utils.make_embed(
                    "❌ Nieznany Przedmiot",
                    f"Nie znaleziono przedmiotu `{item_id}`.\n\nDostępne ID: {ids}",
                    utils.LOSE_COLOR,
                ),
                ephemeral=True,
            )
            return

        item = SHOP_ITEMS[item_id]
        user = await db.get_user(interaction.user.id)

        if user["balance"] < item["cena"]:
            brakuje = item["cena"] - user["balance"]
            await interaction.response.send_message(
                embed=utils.make_embed(
                    "❌ Brak Środków",
                    f"Nie masz wystarczająco Crypto!\n\n"
                    f"Cena: **{item['cena']:,} 💎**\n"
                    f"Masz: **{user['balance']:,} 💎**\n"
                    f"Brakuje: **{brakuje:,} 💎**",
                    utils.LOSE_COLOR,
                ),
                ephemeral=True,
            )
            return

        owned = await db.get_inventory(interaction.user.id)
        already_own = any(i["item_id"] == item_id and i["active"] for i in owned)
        if already_own:
            await interaction.response.send_message(
                embed=utils.make_embed(
                    "⚠️ Już Posiadasz",
                    f"Masz już aktywny przedmiot **{item['nazwa']}**!\n"
                    f"Sprawdź `/ekwipunek` aby zobaczyć czas wygaśnięcia.",
                    utils.NEUTRAL_COLOR,
                ),
                ephemeral=True,
            )
            return

        await db.update_balance(interaction.user.id, -item["cena"])
        await db.add_to_inventory(interaction.user.id, item_id, item["czas_trwania"])
        await db.log_transaction(interaction.user.id, -item["cena"], "shop", f"Kupiono: {item['nazwa']}")

        embed = utils.make_embed(
            title=f"{item['emoji']} Zakup Udany!",
            description=(
                f"Kupiłeś **{item['nazwa']}**!\n\n"
                f"📋 {item['opis']}\n\n"
                f"💰 Zapłacono: **{item['cena']:,} 💎**\n"
                f"💎 Pozostało: **{user['balance'] - item['cena']:,} 💎**"
            ),
            color=utils.WIN_COLOR,
        )
        if item["czas_trwania"]:
            embed.add_field(
                name="⏳ Czas Trwania",
                value=f"Przedmiot aktywny przez: **{item['czas_trwania']}**",
                inline=False,
            )
        embed.add_field(
            name="📦 Ekwipunek",
            value="Użyj `/ekwipunek` aby zobaczyć wszystkie posiadane przedmioty.",
            inline=False,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ekwipunek", description="Sprawdź posiadane przedmioty")
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
            embed.description = (
                "Brak przedmiotów w ekwipunku!\n\n"
                "Odwiedź `/sklep` aby kupić bonusy i ulepszenia."
            )
            await interaction.response.send_message(embed=embed)
            return

        active_items = [i for i in owned if i["active"]]
        expired_items = [i for i in owned if not i["active"]]

        if active_items:
            lines = []
            for i in active_items:
                item_data = SHOP_ITEMS.get(i["item_id"])
                if not item_data:
                    continue
                expires = f"Wygasa: **{i['expires_at'][:16].replace('T', ' ')}**" if i["expires_at"] else "**Trwałe**"
                lines.append(
                    f"{item_data['emoji']} **{item_data['nazwa']}**\n"
                    f"╰ {item_data['opis'][:60]}...\n"
                    f"╰ ⏳ {expires}"
                )
            embed.add_field(
                name=f"✅ Aktywne ({len(active_items)})",
                value="\n\n".join(lines),
                inline=False,
            )

        if expired_items:
            expired_names = []
            for i in expired_items[-5:]:
                item_data = SHOP_ITEMS.get(i["item_id"])
                if item_data:
                    expired_names.append(f"{item_data['emoji']} {item_data['nazwa']}")
            embed.add_field(
                name=f"❌ Wygasłe (ostatnie {min(5, len(expired_items))})",
                value="\n".join(expired_names) if expired_names else "Brak",
                inline=False,
            )

        embed.set_footer(text="Kup więcej przedmiotów: /sklep")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="uzyjprzedmiot", description="Aktywuj przedmiot jednorazowy z ekwipunku")
    @app_commands.describe(przedmiot="ID przedmiotu do użycia")
    async def use_item(self, interaction: discord.Interaction, przedmiot: str):
        item_id = przedmiot.lower().strip()
        owned = await db.get_inventory(interaction.user.id)
        active = next((i for i in owned if i["item_id"] == item_id and i["active"]), None)

        if not active:
            await interaction.response.send_message(
                embed=utils.make_embed(
                    "❌ Nie Posiadasz",
                    f"Nie masz aktywnego przedmiotu `{item_id}`.\n"
                    f"Sprawdź `/ekwipunek` lub kup w `/sklep`.",
                    utils.LOSE_COLOR,
                ),
                ephemeral=True,
            )
            return

        item_data = SHOP_ITEMS.get(item_id)
        if not item_data:
            await interaction.response.send_message(
                embed=utils.make_embed("❌ Błąd", "Nieznany przedmiot.", utils.LOSE_COLOR),
                ephemeral=True,
            )
            return

        embed = utils.make_embed(
            title=f"{item_data['emoji']} Przedmiot Aktywny!",
            description=(
                f"**{item_data['nazwa']}** jest aktywny!\n\n"
                f"📋 Efekt: {item_data['opis']}\n\n"
                f"*Efekty przedmiotów są automatycznie uwzględniane w grach i komendach.*"
            ),
            color=utils.WIN_COLOR,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Shop(bot))
