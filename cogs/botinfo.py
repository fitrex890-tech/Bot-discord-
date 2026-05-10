@app_commands.command(
    name="botinfo",
    description="Informacje o bocie"
)
async def bot_info(
    self,
    interaction: discord.Interaction
):

    embed = utils.make_embed(
        title="🤖 Crypto Casino Bot",
        description="Bot ekonomiczno-kasynowy z walutą Crypto 💎",
        color=utils.JACKPOT_COLOR,
    )

    # =========================
    # EKONOMIA
    # =========================
    embed.add_field(
        name="💰 Ekonomia",
        value=(
            "/balans • /daily • /pracuj • /żebrz\n"
            "/crime • /okradnij • /przelej\n"
            "/wpłać • /wypłać • /top"
        ),
        inline=False,
    )

    # =========================
    # GRY
    # =========================
    embed.add_field(
        name="🎰 Gry",
        value=(
            "/spin • /blackjack • /slots\n"
            "/coinflip • /roulette • /mines"
        ),
        inline=False,
    )

    # =========================
    # ADMIN
    # =========================
    embed.add_field(
        name="🛡️ Administracja",
        value=(
            "/dodajpieniadze\n"
            "/usunpieniadze\n"
            "/ustawpieniadze\n"
            "/resetuser"
        ),
        inline=False,
    )

    # =========================
    # INFO
    # =========================
    embed.add_field(
        name="📊 Info",
        value=(
            f"🌐 Serwery: **{len(self.bot.guilds)}**\n"
            f"👥 Użytkownicy: **{sum(g.member_count or 0 for g in self.bot.guilds):,}**\n"
            f"⚙️ Komendy: **{len(self.bot.tree.get_commands())}**"
        ),
        inline=False,
    )

    embed.add_field(
        name="🏦 Bank",
        value="Pieniądze w banku są bezpieczne przed kradzieżą.",
        inline=True,
    )

    embed.add_field(
        name="⚡ System",
        value="Economy + Casino + Admin Tools",
        inline=True,
    )

    embed.set_thumbnail(
        url=self.bot.user.display_avatar.url
    )

    embed.set_footer(
        text="Crypto Casino Bot • /botinfo"
    )

    await interaction.response.send_message(embed=embed)
