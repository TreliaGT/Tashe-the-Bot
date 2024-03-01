#A bot that helps with DND
import discord
import requests
import random
import datetime
from discord.ext import commands
from discord.ext import tasks

#Init the bot with intents
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
ITEM_API = "https://api.open5e.com/v1/magicitems/?desc=&desc__icontains=&desc__iexact=&desc__in=&document__slug=&document__slug__iexact=&document__slug__in=&document__slug__not_in=&format=json&name=&name__iexact=&rarity=&rarity__icontains=common&rarity__iexact=&requires_attunement=&requires_attunement__iexact=&slug=&slug__iexact=&slug__in=&type=&type__icontains=&type__iexact="
TOKEN = ""
HUB_ID = 0

user_inventory = {}

#Went entering the server
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    # Check if the reaction is on the correct message
    if reaction.message.author == bot.user:
        # Check if the reaction is one of the options (1, 2, 3)
        if reaction.emoji in ['1️⃣', '2️⃣', '3️⃣']:
            # Fetch data from API
            response = requests.get(ITEM_API)
            items_data = response.json()['results']

            # Get the corresponding item based on the reaction
            item_index = int(reaction.emoji[0]) - 1
            selected_item = items_data[item_index]

            # Give the item to the user
            user_id = str(user.id)
            user_inventory[user_id] = selected_item['name']

            # Send a message to the user about obtaining the item
            await user.send(f"You obtained: {selected_item['name']}")

            # Remove the reaction to prevent further selection
            await reaction.message.clear_reaction(reaction.emoji)


@bot.command(name='inventory')
async def show_inventory(ctx):
    # Fetch data from API
    response = requests.get(ITEM_API)
    items_data = response.json()['results']

    # Randomly select three items
    random_items = random.sample(items_data, 3)

    # Create embed
    embed = discord.Embed(title="Tashe's Inventory for Today", color=0xffd700)
    embed.add_field(name="Please note:", value="You can only have one item at a time, so please choose wisely.")

    # Add random items to embed
    for idx, item in enumerate(random_items):
        embed.add_field(name=f"Option {idx+1}: {item['name']}", value=f"Type: {item['type']}\n[More Info]({item['document__url']})", inline=False)

    # Send embed to Discord
    message = await ctx.send(embed=embed)

    # Add reactions to the message
    emojis = ['1️⃣', '2️⃣', '3️⃣']
    for emoji in emojis:
        await message.add_reaction(emoji)


@bot.command(name='roll')
async def roll(ctx, dice: str):
    try:
        num, die = map(int, dice.split('d'))
        if num <= 0 or die not in [4, 6, 8, 10, 12, 20, 100]:
            raise ValueError
        rolls = [random.randint(1, die) for _ in range(num)]
        total = sum(rolls)
        await ctx.send(f'Rolling {num}d{die}... Result: {rolls}. Total: {total}')
    except ValueError:
        await ctx.send('Invalid dice format! Please use the format XdY where X is the number of dice and Y is the number of sides (4, 6, 8, 10, 12, 20, or 100).')

@bot.command(name='list_items')
async def list_user_items(ctx):
    if not user_inventory:
        await ctx.send("No users have items in their inventory.")
        return

    inventory_list = ""
    for user_id, item in user_inventory.items():
        user = await bot.fetch_user(int(user_id))
        inventory_list += f"{user.name}: {item}\n"

    await ctx.send(f"Inventory List:\n{inventory_list}")



@tasks.loop(hours=24)  # This will run the function once every 24 hours
async def daily_task():
    # Get the channel where you want to execute the command
    channel = bot.get_channel(HUB_ID)  # Replace YOUR_CHANNEL_ID with the ID of your desired channel
    
    # Your code for the daily task goes here
    await show_inventory(channel)  # Call the show_inventory function and pass the channel object

@daily_task.before_loop
async def before_daily_task():
    await bot.wait_until_ready()  # Wait until the bot is ready

    # Calculate the time until the next 7:30 AM
    now = datetime.datetime.now()
    desired_time = now.replace(hour=10, minute=30, second=0, microsecond=0)
    if now > desired_time:
        desired_time += datetime.timedelta(days=1)  # If it's past 7:30 AM today, schedule for tomorrow
    delta = desired_time - now

    # Sleep until 7:30 AM
    await asyncio.sleep(delta.total_seconds())

bot.run(TOKEN)
