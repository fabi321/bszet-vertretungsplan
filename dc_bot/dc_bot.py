from datetime import datetime
from os import getenv
import asyncio
from logging import info

import discord
from discord.errors import Forbidden
from discord.ext import tasks
from discord import app_commands
from util.DB import DB
from util import check_credentials


intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


DISCORD: str = "dc"


@tree.command(description="Verifiziere dass du die Zugangsdaten kennst")
@app_commands.describe(
    username="Nutzername für geschuetzt.bszet.de",
    password="Passwort für geschuetzt.bszet.de"
)
async def verify(interaction: discord.Interaction, username: str, password: str):
    allowed: bool
    if not interaction.guild:
        allowed = True
    else:
        bot_member: discord.Member = interaction.guild.get_member(client.user.id)
        allowed = interaction.channel.permissions_for(bot_member).send_messages
    if not allowed:
        await interaction.response.send_message(
            "Initialisieren fehlgeschlagen. Stelle sicher, dass der Bot im Channel schreiben darf."
            )
        return
    DB.add_user(interaction.channel_id, platform=DISCORD)
    if check_credentials(username, password):
        DB.trust_user(interaction.channel_id, platform=DISCORD)
        await interaction.response.send_message("Erfolgreich verifiziert. Du kannst nun eine Klasse mit /set_class setzen")
    else:
        await interaction.response.sent_message("Ungültige Zugangsdaten")


@tree.command(description="Setze eine Klasse, für die Vertretungen gesendet werden sollen")
@app_commands.choices(
    area=[
        app_commands.Choice(name="Berufschule für Informationstechnik", value="bs-it"),
        app_commands.Choice(name="Berufsschule für Elektrotechnik", value="bs-et"),
        app_commands.Choice(name="Berufliches Gymnasium", value="bgy"),
    ]
)
@app_commands.describe(
    area="Schulbereich",
    class_name="Klassenname"
)
async def set_class(interaction: discord.Interaction, area: app_commands.Choice[str], class_name: str):
    if not DB.is_trusted_user(interaction.channel_id, platform=DISCORD):
        await interaction.response.send_message("Bitte verifiziere dich erst mit /verify")
        return
    if not DB.check_if_class_exists(area.value, class_name):
        await interaction.response.send_message("Die Klasse wurde leider nicht für den Bereich gefunden.")
        return
    DB.add_user_to_class(interaction.channel_id, class_name, platform=DISCORD)
    DB.update_user(interaction.channel_id, is_zero=True, platform=DISCORD)
    await interaction.response.send_message(f"Erfolgreich Klasse {class_name} in Bereich {area.name} gesetzt.")
    await update_channel(interaction.channel_id)


@tree.command(description="Stoppe den bot in diesem Kanal")
async def stop(interaction: discord.Interaction):
    DB.delete_user(interaction.channel_id, platform=DISCORD)
    await interaction.response.send_message("Erfolgreich gestoppt")


async def get_channel(cid: int) -> discord.TextChannel | discord.DMChannel:
    if channel := client.get_channel(cid):
        return channel
    return await client.fetch_channel(cid)


async def update_channel(cid: int):
    info(f"Updating substitutions for discord channel {cid}")
    result: str = 'Aktuelle Vertretungen:\n\n'
    is_new: bool = False
    for substitution in DB.get_all_substitutions_for_user(cid, platform=DISCORD):
        line: str = datetime.fromtimestamp(substitution.day).strftime('%a, %d.%m')
        line += f', {substitution.lesson}: {substitution.teacher} {substitution.subject} {substitution.room}'
        if substitution.notes:
            line += f' ({substitution.notes})'
        if substitution.is_new:
            line = f'**{line}**'
            is_new = True
        result += line + '\n'
    if is_new:
        try:
            channel: discord.TextChannel | discord.DMChannel = await get_channel(cid)
            await channel.send(result)
            DB.update_user(cid, platform=DISCORD)
        except Forbidden:
            DB.delete_user(cid, platform=DISCORD)


@tasks.loop(minutes=1.0, reconnect=True)
async def update_channels():
    info("updating discord channels")
    for cid in DB.get_all_updated_users(DISCORD):
        await update_channel(cid)


@client.event
async def on_ready():
    await tree.sync()
    info("discord bot ready")
    update_channels.start()


async def main():
    await client.start(getenv('DISCORD_BOT_TOKEN'), reconnect=True)


if __name__ == "__main__":
    asyncio.run(main())
