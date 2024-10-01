import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# Configure intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Required to read message content

# Initialize the bot with the desired prefix
bot = commands.Bot(command_prefix="!", intents=intents)

# IDs for the channels (replace with your actual values)
CHANNEL_ID = int(os.environ['CHANNEL_ID'])  # ID of the channel to send the initial message
RESULTS_CHANNEL_ID = int(os.environ['RESULTS_CHANNEL_ID'])  # ID of the channel to send results

# The six emojis to use
emoji_list = ['🏘️', '🏕️', '🏖️', '🏚️', '🏗️', '🪠']

# Dictionary to record user reactions
user_reactions = {}

# Personalized message
message_content = """This is for those who wish to be promoted in the gang or wish to have their captures logged for possible future promotions.
Although it is not required to submit your captures, please remember it is **one of the requirements to stay within the gang**.

**Those who do not have any captures at the end of each month beginning next month could be removed from the gang** unless they can prove they have been capturing territories.

Click the emoji corresponding to the territory every time you have claimed it:

🏘️ | Residential

🏕️ | Park

🏖️ | Beach

🏚️ | Slums

🏗️ | Industrial

🪠 | Sewers

**Anyone who declares false conquests will be kicked from the gang!**

To demonstrate conquests and when the bot is off use this: https://dyno.gg/form/95bdcbdd
"""

# Class for the emoji buttons view
class EmojiButtonView(discord.ui.View):
    def __init__(self, user, results_channel, rp_selection, timeout=60):
        super().__init__(timeout=timeout)
        self.user = user  # The user who can interact with this view
        self.user_selections = []
        self.results_channel = results_channel  # Channel to send results
        self.rp_selection = rp_selection  # 'RP1' or 'RP2'

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.user  # Only allow the specific user to interact

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
        # We no longer send a summary to the user here

    async def send_results(self, emoji_clicked):
        # Update the user reactions dictionary
        if self.user.name not in user_reactions:
            user_reactions[self.user.name] = []
        user_reactions[self.user.name].append((self.rp_selection, emoji_clicked))
        # Send the message to the results channel
        await self.results_channel.send(f"{self.user.name} selected {emoji_clicked} ({self.rp_selection})")

    # Create a button for each emoji
    @discord.ui.button(emoji='🏘️', style=discord.ButtonStyle.primary)
    async def emoji_button1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.button_callback(interaction, '🏘️')

    @discord.ui.button(emoji='🏕️', style=discord.ButtonStyle.primary)
    async def emoji_button2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.button_callback(interaction, '🏕️')

    @discord.ui.button(emoji='🏖️', style=discord.ButtonStyle.primary)
    async def emoji_button3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.button_callback(interaction, '🏖️')

    @discord.ui.button(emoji='🏚️', style=discord.ButtonStyle.primary)
    async def emoji_button4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.button_callback(interaction, '🏚️')

    @discord.ui.button(emoji='🏗️', style=discord.ButtonStyle.primary)
    async def emoji_button5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.button_callback(interaction, '🏗️')

    @discord.ui.button(emoji='🪠', style=discord.ButtonStyle.primary)
    async def emoji_button6(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.button_callback(interaction, '🪠')

    async def button_callback(self, interaction: discord.Interaction, emoji_clicked):
        if emoji_clicked not in self.user_selections:
            self.user_selections.append(emoji_clicked)
            # Send the message to the results channel
            await self.send_results(emoji_clicked)
        # Respond to the interaction to avoid errors
        await interaction.response.defer()

# Class for the number buttons view
class NumberButtonView(discord.ui.View):
    def __init__(self, results_channel):
        super().__init__(timeout=None)  # No timeout for this view
        self.results_channel = results_channel  # Channel to send results

    @discord.ui.button(label='RP1', style=discord.ButtonStyle.primary, custom_id='number_RP1')
    async def button1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.number_button_callback(interaction, 'RP1')

    @discord.ui.button(label='RP2', style=discord.ButtonStyle.primary, custom_id='number_RP2')
    async def button2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.number_button_callback(interaction, 'RP2')

    async def number_button_callback(self, interaction: discord.Interaction, rp_selection):
        # Send a private message to the user with the emoji buttons and the personalized message
        view = EmojiButtonView(interaction.user, self.results_channel, rp_selection)
        dm_message = await interaction.user.send(message_content, view=view)
        view.message = dm_message  # Save the message to be able to edit it

        # Respond to the interaction informing the user
        await interaction.response.send_message("I have sent you a private message with the options!", ephemeral=True)

# Event on_ready
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    # Retrieve the channels
    channel = bot.get_channel(CHANNEL_ID)
    results_channel = bot.get_channel(RESULTS_CHANNEL_ID)
    if channel is None or results_channel is None:
        print("Error: Check the channel IDs.")
        return
    # Send the message with the number buttons and the personalized message
    await channel.send(message_content, view=NumberButtonView(results_channel))
    print('Message with number buttons sent.')

# Command results
@bot.command(name='results')
async def results(ctx):
    # Create the results message
    results_message = "Reactions Results:\n"
    for user_name, selections in user_reactions.items():
        results_message += f"\n**{user_name}** selected the following emojis:\n"
        rp1_emojis = {}
        rp2_emojis = {}
        for rp_selection, emoji in selections:
            if rp_selection == 'RP1':
                if emoji not in rp1_emojis:
                    rp1_emojis[emoji] = 0
                rp1_emojis[emoji] += 1
            elif rp_selection == 'RP2':
                if emoji not in rp2_emojis:
                    rp2_emojis[emoji] = 0
                rp2_emojis[emoji] += 1
        if rp1_emojis:
            results_message += f"**RP1** selections:\n"
            for emoji, count in rp1_emojis.items():
                results_message += f"{emoji}: {count} times\n"
        if rp2_emojis:
            results_message += f"**RP2** selections:\n"
            for emoji, count in rp2_emojis.items():
                results_message += f"{emoji}: {count} times\n"

    if results_message == "Reactions Results:\n":
        results_message = "No reactions recorded yet."

    # Send the results in the channel where the command was invoked
    await ctx.send(results_message)

# Event on_message
@bot.event
async def on_message(message):
    # Handle messages and commands
    await bot.process_commands(message)

# Add the web server to keep the bot alive
app = Flask('')

@app.route('/')
def home():
    return "The bot is active!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Call keep_alive to start the web server
keep_alive()

# Run the bot
TOKEN = os.environ['TOKEN']  # Enter your bot's token in the environment variables
bot.run(TOKEN)
