import discord
from discord.ext import commands
from .CardsMain import get_db_connection  # Assuming you have a get_db_connection method in CardsMain

class ActivityRewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Handle PokeTwo rewards
        if not message.author.bot:
            if "Congratulations" in message.content:  # Replace this condition based on how PokeTwo handles correct answers
                await self.award_poketwo_currency(message.author)

        # Handle MEE6 level-up rewards
        if message.author.bot and "leveled up" in message.content:  # MEE6 typically sends a message when someone levels up
            if message.mentions:
                user = message.mentions[0]
                level = int(message.content.split("level ")[-1].split()[0])  # Extract the level from the message
                await self.award_mee6_currency(user, level)

    async def award_poketwo_currency(self, user):
        """Award currency for answering a PokeTwo question correctly."""
        amount = 10  # Example currency amount for correct answer
        await self.add_currency(user.id, amount)
        await user.send(f"You have earned {amount} pack currency for answering a PokeTwo question correctly!")

    async def award_mee6_currency(self, user, level):
        """Award currency based on MEE6 level-up."""
        currency_award = level * 10  # Example: 10 currency per level
        await self.add_currency(user.id, currency_award)
        await user.send(f"You have earned {currency_award} pack currency for reaching level {level}!")

    async def add_currency(self, user_id, amount):
        """Add currency to a user's balance."""
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET currency = currency + %s WHERE discord_id = %s", (amount, user_id))
        db.commit()
        cursor.close()
        db.close()

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(ActivityRewards(bot))
