@app_commands.command(name="przelej")
@app_commands.choices(currency=[
    app_commands.Choice(name="Crypto 💎", value="crypto"),
    app_commands.Choice(name="PLN 🇵🇱", value="pln")
])
async def transfer(
    self,
    interaction: discord.Interaction,
    user: discord.Member,
    amount: int,
    currency: app_commands.Choice[str]
):

    if user.id == interaction.user.id:
        return await interaction.response.send_message("❌ Nie możesz przelać sobie")

    if amount <= 0:
        return await interaction.response.send_message("❌ Zła kwota")

    # 🔒 CHECK SALDA
    crypto, pln, _, _ = await db.get_wallet(interaction.user.id)

    if currency.value == "crypto" and crypto < amount:
        return await interaction.response.send_message("❌ Za mało 💎")

    if currency.value == "pln" and pln < amount:
        return await interaction.response.send_message("❌ Za mało zł")

    # 💸 TRANSFER
    if currency.value == "crypto":
        await db.update_crypto(interaction.user.id, -amount)
        await db.update_crypto(user.id, amount)
    else:
        await db.update_pln(interaction.user.id, -amount)
        await db.update_pln(user.id, amount)

    await interaction.response.send_message(
        f"💸 Przelano **{amount} {currency.name}** do {user.mention}"
    )
