import discord
import asyncio
import random
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from .CardsMain import get_db_connection

class RewardSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.random_drops.start()  # Start the random drops task

    @commands.command(name='daily')
    async def daily_reward(self, ctx):
        """Claim your daily reward."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # Check last claimed time
            cursor.execute("SELECT last_daily FROM users WHERE discord_id = %s", (ctx.author.id,))
            result = cursor.fetchone()
            now = datetime.utcnow()

            if result and result['last_daily']:
                last_claimed = result['last_daily']
                if now - last_claimed < timedelta(days=1):
                    await ctx.send(f"{ctx.author.mention}, you've already claimed your daily reward today.")
                    return

            # Update last claimed time and give reward
            cursor.execute("UPDATE users SET last_daily = %s, currency = currency + 50 WHERE discord_id = %s", (now, ctx.author.id))
            db.commit()
            await ctx.send(f"{ctx.author.mention}, you have claimed your daily reward of 50 pack currency!")

        finally:
            cursor.close()
            db.close()

    @commands.command(name='weekly')
    async def weekly_reward(self, ctx):
        """Claim your weekly reward."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # Check last claimed time
            cursor.execute("SELECT last_weekly FROM users WHERE discord_id = %s", (ctx.author.id,))
            result = cursor.fetchone()
            now = datetime.utcnow()

            if result and result['last_weekly']:
                last_claimed = result['last_weekly']
                if now - last_claimed < timedelta(weeks=1):
                    await ctx.send(f"{ctx.author.mention}, you've already claimed your weekly reward this week.")
                    return

            # Update last claimed time and give reward
            cursor.execute("UPDATE users SET last_weekly = %s, currency = currency + 250 WHERE discord_id = %s", (now, ctx.author.id))
            db.commit()
            await ctx.send(f"{ctx.author.mention}, you have claimed your weekly reward of 250 pack currency!")

        finally:
            cursor.close()
            db.close()

    @tasks.loop(hours=1)
    async def random_drops(self):
        """Drop random rewards in the specified channel."""
        await self.execute_random_drop(self.bot.get_channel(1277437238929522699))

    @commands.command(name='specialdrop')
    @commands.has_permissions(administrator=True)
    async def special_drop(self, ctx):
        """Admin command to execute a special random drop."""
        await self.execute_random_drop(ctx.channel)

    async def execute_random_drop(self, channel):
        """Handles the random drop logic, can be triggered by the bot or manually."""
        if channel:
            # Define potential rewards
            rewards = [
                {"type": "currency", "amount": 50, "message": "50 pack currency!"},
                {"type": "currency", "amount": 100, "message": "100 pack currency!"},
            ]
            reward = random.choice(rewards)

            message = await channel.send(f"A wild drop appears! React within 15 minutes to claim {reward['message']}")
            await message.add_reaction("🎁")
            
            claimed_users = set()

            def check(reaction, user):
                return (
                    user != self.bot.user 
                    and str(reaction.emoji) == "🎁" 
                    and reaction.message.id == message.id
                    and user.id not in claimed_users
                )

            try:
                end_time = datetime.utcnow() + timedelta(minutes=15)
                while datetime.utcnow() < end_time:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=(end_time - datetime.utcnow()).total_seconds(), check=check)

                    claimed_users.add(user.id)

                    if reward['type'] == 'currency':
                        db = get_db_connection()
                        cursor = db.cursor()
                        cursor.execute("UPDATE users SET currency = currency + %s WHERE discord_id = %s", (reward['amount'], user.id))
                        db.commit()
                        cursor.close()
                        db.close()
                        await channel.send(f"{user.mention} claimed the drop and received {reward['message']}")

                    elif reward['type'] == 'card':
                        db = get_db_connection()
                        cursor = db.cursor()
                        cursor.execute("INSERT INTO cards (owner_id, card_name) VALUES (%s, %s)", (user.id, reward["name"]))
                        db.commit()
                        cursor.close()
                        db.close()
                        await channel.send(f"{user.mention} claimed the drop and received {reward['message']}")

            except asyncio.TimeoutError:
                pass  # No further action needed on timeout

            await channel.send("The drop has expired.")

    @random_drops.before_loop
    async def before_random_drops(self):
        await self.bot.wait_until_ready()

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(RewardSystem(bot))
