import discord
from discord.ext import commands
from .CardsMain import get_db_connection  # Assuming get_db_connection is in CardsMain

class EconomySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='balance')
    async def balance(self, ctx):
        """Check your currency balance."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT currency FROM users WHERE discord_id = %s", (ctx.author.id,))
            result = cursor.fetchone()

            if result:
                balance = result['currency']
                await ctx.send(f"{ctx.author.mention}, you have {balance} pack currency.")
            else:
                await ctx.send(f"{ctx.author.mention}, you do not have a registered account.")
        
        finally:
            cursor.close()
            db.close()

    @commands.command(name='givecurrency')
    @commands.has_permissions(administrator=True)
    async def give_currency(self, ctx, target_user: discord.Member, amount: int):
        """Give a user a specified amount of currency (Admin only)."""
        db = get_db_connection()
        cursor = db.cursor()

        try:
            cursor.execute("UPDATE users SET currency = currency + %s WHERE discord_id = %s", (amount, target_user.id))
            db.commit()
            await ctx.send(f"{target_user.mention} has been awarded {amount} pack currency!")
        
        finally:
            cursor.close()
            db.close()

    @commands.command(name='marketplace')
    async def marketplace(self, ctx, action: str, card_id: int = None, price: int = None):
        """List, buy, or sell cards on the marketplace."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        try:
            if action == "list":
                # List a card for sale
                cursor.execute("INSERT INTO marketplace (card_id, seller_id, price) VALUES (%s, %s, %s)", (card_id, ctx.author.id, price))
                db.commit()
                await ctx.send(f"Card {card_id} listed for {price} pack currency!")

            elif action == "buy":
                # Buy a card from the marketplace
                cursor.execute("SELECT * FROM marketplace WHERE card_id = %s", (card_id,))
                listing = cursor.fetchone()

                if listing:
                    buyer_currency = await self.get_currency(ctx.author.id)
                    if buyer_currency >= listing['price']:
                        # Transfer currency and card
                        await self.add_currency(ctx.author.id, -listing['price'])
                        await self.add_currency(listing['seller_id'], listing['price'])
                        cursor.execute("UPDATE cards SET owner_id = %s WHERE id = %s", (ctx.author.id, card_id))
                        cursor.execute("DELETE FROM marketplace WHERE card_id = %s", (card_id,))
                        db.commit()
                        await ctx.send(f"You bought card {card_id} for {listing['price']} pack currency!")
                    else:
                        await ctx.send(f"You don't have enough currency to buy this card.")
                else:
                    await ctx.send(f"This card is not available on the marketplace.")

            elif action == "remove":
                # Remove a listing from the marketplace
                cursor.execute("DELETE FROM marketplace WHERE card_id = %s AND seller_id = %s", (card_id, ctx.author.id))
                db.commit()
                await ctx.send(f"Your listing for card {card_id} has been removed.")

            else:
                await ctx.send("Invalid marketplace action. Use 'list', 'buy', or 'remove'.")
        
        finally:
            cursor.close()
            db.close()

    @commands.command(name='market')
    async def market(self, ctx):
        """View all cards currently listed on the marketplace."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT m.card_id, c.card_name, m.price, u.discord_id FROM marketplace m JOIN cards c ON m.card_id = c.id JOIN users u ON m.seller_id = u.id")
            listings = cursor.fetchall()

            if listings:
                embed = discord.Embed(
                    title="Marketplace Listings",
                    description="Here are the cards currently for sale:",
                    color=discord.Color.green()
                )

                for listing in listings:
                    user = self.bot.get_user(listing['discord_id'])
                    embed.add_field(
                        name=f"Card ID: {listing['card_id']} - {listing['card_name']}",
                        value=f"Price: {listing['price']} currency | Seller: {user.display_name if user else 'Unknown'}",
                        inline=False
                    )
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("The marketplace is currently empty.")
        
        finally:
            cursor.close()
            db.close()

    async def get_currency(self, user_id):
        """Get the current currency balance for a user."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT currency FROM users WHERE discord_id = %s", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        db.close()
        return result['currency'] if result else 0

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
    await bot.add_cog(EconomySystem(bot))
