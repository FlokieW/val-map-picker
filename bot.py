import discord
import random
from discord.ext import commands
import os
from dotenv import load_dotenv
from discord import app_commands

# Load environment variables
load_dotenv()

# Fetch the token from the environment variable
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Setup intents (ensure you enable the privileged intents in the Discord developer portal)
intents = discord.Intents.default()

# Define the bot and prefix
bot = commands.Bot(command_prefix='!', intents=intents)

# Define the maps list
maps = ["Ascent", "Bind", "Breeze", "Icebox", "Lotus", "Split", "Sunset"]

# Define the MapBanView class
class MapBanView(discord.ui.View):
    def __init__(self, user, enemy_captain):
        super().__init__(timeout=None)
        self.user = user
        self.enemy_captain = enemy_captain
        self.next_turn = self.user if random.choice([True, False]) else self.enemy_captain
        self.banned_maps = []

        self.select = discord.ui.Select(
            placeholder="Select a map to ban...",
            options=[discord.SelectOption(label=map_name) for map_name in maps],
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.next_turn:
            await interaction.response.send_message(f"It's {self.next_turn.mention}'s turn to ban a map!", ephemeral=True)
            return False
        return True

    def get_maps_list(self):
        maps_list = []
        for map_name in maps:
            if map_name in self.banned_maps:
                maps_list.append(f"> {map_name} <:util_Cross_Box:1180190758075125940>")
            else:
                maps_list.append(f"> {map_name}")
        return "\n".join(maps_list)

    async def select_callback(self, interaction: discord.Interaction):
        selected_map = self.select.values[0]
        self.banned_maps.append(selected_map)
        self.select.options = [option for option in self.select.options if option.label != selected_map]
        self.next_turn = self.user if self.next_turn == self.enemy_captain else self.enemy_captain

        if len(self.banned_maps) == len(maps) - 1:
            remaining_map = [map_name for map_name in maps if map_name not in self.banned_maps][0]
            await interaction.response.edit_message(content=f"Banning Complete! The selected map is: **{remaining_map}**\n\n**Maps:**\n{self.get_maps_list()}", view=None)
        else:
            await interaction.response.edit_message(content=f"{interaction.user.mention} banned **{selected_map}**. It's now {self.next_turn.mention}'s turn to ban a map.\n\n**Maps:**\n{self.get_maps_list()}", view=self)

# Define the command for map picking
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        await bot.tree.sync()  # Sync commands globally
        print(f'Synced global commands.')
    except Exception as e:
        print(f'Error syncing commands: {e}')

@bot.tree.command(name="map_pick", description="Starts a pick and ban phase for Valorant maps.")
@app_commands.describe(enemy_captain="The captain of the enemy team.")
async def map_pick(interaction: discord.Interaction, enemy_captain: discord.Member):
    user = interaction.user

    if user == enemy_captain:
        await interaction.response.send_message("You cannot pick and ban maps against yourself!", ephemeral=True)
        return

    view = MapBanView(user, enemy_captain)
    await interaction.response.send_message(
        f"{user.mention} and {enemy_captain.mention} are starting the map pick and ban phase. The first turn goes to {view.next_turn.mention}. Use the select menu below to ban maps.\n\n**Maps:**\n{view.get_maps_list()}",
        view=view
    )

# Run the bot
bot.run(DISCORD_TOKEN)