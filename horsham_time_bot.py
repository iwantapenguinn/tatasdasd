import os
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones

import discord
from discord import app_commands

# Every real-world timezone, sorted alphabetically (e.g. Africa/Abidjan ... Pacific/Wallis)
ZONES = sorted(
    z for z in available_timezones()
    if "/" in z and not z.startswith(("Etc/", "posix/", "right/"))
)
PER_PAGE = 20
DEFAULT_ZONE = "Australia/Melbourne"  # Horsham, Victoria

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def fmt(zone: str) -> str:
    now = datetime.now(ZoneInfo(zone))
    return f"`{zone}` — **{now:%I:%M %p}** {now:%a %d %b} ({now:%Z})"


class TimePages(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.page = 0
        self.max_page = (len(ZONES) - 1) // PER_PAGE

    def embed(self) -> discord.Embed:
        start = self.page * PER_PAGE
        lines = [fmt(z) for z in ZONES[start:start + PER_PAGE]]
        e = discord.Embed(title="🌍 Time around the world (A–Z)", description="\n".join(lines))
        e.set_footer(text=f"Page {self.page + 1}/{self.max_page + 1} • {len(ZONES)} zones")
        return e

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = (self.page - 1) % (self.max_page + 1)
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = (self.page + 1) % (self.max_page + 1)
        await interaction.response.edit_message(embed=self.embed(), view=self)


@tree.command(name="alltimes", description="Show the time in every timezone, alphabetically")
async def alltimes(interaction: discord.Interaction):
    view = TimePages()
    await interaction.response.send_message(embed=view.embed(), view=view)


async def zone_autocomplete(interaction: discord.Interaction, current: str):
    matches = [z for z in ZONES if current.lower() in z.lower()][:25]
    return [app_commands.Choice(name=z, value=z) for z in matches]


@tree.command(name="time", description="Show the time in one place (defaults to Horsham, Victoria)")
@app_commands.describe(zone="Timezone, e.g. Europe/London")
@app_commands.autocomplete(zone=zone_autocomplete)
async def time_command(interaction: discord.Interaction, zone: str = DEFAULT_ZONE):
    if zone not in ZONES:
        await interaction.response.send_message("Unknown timezone — pick one from the list.", ephemeral=True)
        return
    await interaction.response.send_message(fmt(zone))


@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user} — {len(ZONES)} zones loaded")


client.run(os.environ["DISCORD_TOKEN"])
