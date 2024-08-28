import discord
from discord.ext import commands, tasks
import json
import asyncio
from itertools import cycle

intents = discord.Intents.default()
intents.members = True  # Ensure you have member intents enabled
intents.message_content = True  # Ensure message content intent is enabled
bot = commands.Bot(command_prefix='!', intents=intents)  # Use '!' as the command prefix

status = cycle(['Ripping Packs!', 'Unboxing legendaries!', 'Crazy Drops!'])

@bot.event
async def on_ready():
    change_status.start()
    if bot.user:
        print(f'Logged in as {bot.user.name}')

@bot.event
async def on_command(ctx):
    print(f"Command received: {ctx.command}")

@bot.event
async def on_command_error(ctx, error):
    print(f"Error occurred: {error}")

@tasks.loop(seconds=10)
async def change_status():
    await bot.change_presence(activity=discord.Game(next(status)))

async def load_extensions():
        ### TCG - Trading Cards ###

    try:
        await bot.load_extension('TCG.CardsMain')
        print('Loaded CardsMain successfully.')
    except Exception as e:
        print(f'Failed to load CardsMain: {e}')

    try:
        await bot.load_extension('TCG.TradeSystem')
        print('Loaded TradeSystem successfully.')
    except Exception as e:
        print(f'Failed to load TradeSystem: {e}')

    try:
        await bot.load_extension('TCG.ShowcaseSystem')
        print('Loaded ShowcaseSystem successfully.')
    except Exception as e:
        print(f'Failed to load ShowcaseSystem: {e}')

    try:
        await bot.load_extension('TCG.Leaderboard')
        print('Loaded Leaderboard successfully.')
    except Exception as e:
        print(f'Failed to load Leaderboard: {e}')

    try:
        await bot.load_extension('TCG.Events')
        print('Loaded Events successfully.')
    except Exception as e:
        print(f'Failed to load Events: {e}')

    try:
        await bot.load_extension('TCG.UserProfile')
        print('Loaded UserProfile successfully.')
    except Exception as e:
        print(f'Failed to load UserProfile: {e}')

    try:
        await bot.load_extension('TCG.ActivityRewards')
        print('Loaded ActivityRewards successfully.')
    except Exception as e:
        print(f'Failed to load ActivityRewards: {e}')

    try:
        await bot.load_extension('TCG.EconomySystem')
        print('Loaded EconomySystem successfully.')
    except Exception as e:
        print(f'Failed to load EconomySystem: {e}')

    try:
        await bot.load_extension('TCG.RewardSystem')
        print('Loaded RewardSystem successfully.')
    except Exception as e:
        print(f'Failed to load RewardSystem: {e}')

    try:
        await bot.load_extension('TCG.PackSystem')
        print('Loaded PackSystem successfully.')
    except Exception as e:
        print(f'Failed to load PackSystem: {e}')

async def main():
    async with bot:
        await load_extensions()
        await bot.start('MTI3NzQ1NTkyMDE1ODQ3NDI2MQ.Gybz7z.ISiKJnt_BmafQOkV-d82IkasYbw7RlPIxnUtwE')

if __name__ == "__main__":
    asyncio.run(main())
