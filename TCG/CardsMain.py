import discord
from discord.ext import commands
import mysql.connector

def get_db_connection():
    """Establish a connection to the database."""
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username if it's different
        password="",  # Replace with your MySQL password if you have one
        database="discord_bot"  # Replace with the name of your database
    )

class CardsMain(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Check pending trades and clean up invalid ones on bot startup."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # Get all pending trades
            cursor.execute("SELECT * FROM trades WHERE status = 'pending'")
            pending_trades = cursor.fetchall()

            for trade in pending_trades:
                # Check if the offer card is still with the original owner
                cursor.execute("SELECT id FROM cards WHERE id = %s AND owner_id = %s", (trade['offer_card_id'], trade['from_user_id']))
                offer_card = cursor.fetchone()

                # Check if the request card is still with the original owner
                cursor.execute("SELECT id FROM cards WHERE id = %s AND owner_id = %s", (trade['request_card_id'], trade['to_user_id']))
                request_card = cursor.fetchone()

                # If either card is missing, cancel the trade
                if not offer_card or not request_card:
                    cursor.execute("UPDATE trades SET status = 'cancelled' WHERE id = %s", (trade['id'],))
                    db.commit()
                    print(f"Trade ID {trade['id']} was cancelled because the cards are no longer in the users' inventories.")

        except mysql.connector.Error as err:
            print(f"Failed to clean up pending trades due to a database error: {err}")
        
        finally:
            cursor.close()
            db.close()

    @commands.command(name='signup')
    async def register(self, ctx):
        """Registers a new user into the database."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # Check if the user is already registered
            cursor.execute("SELECT id FROM users WHERE discord_id = %s", (ctx.author.id,))
            user = cursor.fetchone()

            if user:
                await ctx.send(f"{ctx.author.mention}, you are already registered!")
            else:
                # Insert the user into the database
                cursor.execute("INSERT INTO users (discord_id, username) VALUES (%s, %s)", (ctx.author.id, ctx.author.name))
                db.commit()
                await ctx.send(f"{ctx.author.mention}, you have been successfully registered!")
        
        except Exception as e:
            await ctx.send(f"An error occurred while registering: {e}")
        
        finally:
            cursor.close()
            db.close()

        @commands.command(name='setalerts')
        async def set_alerts(self, ctx, alert_type: str, enable: bool):
            """Set user alerts for various events."""
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)

            try:
                cursor.execute("INSERT INTO alerts (user_id, alert_type, enabled) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE enabled = %s",
                            (ctx.author.id, alert_type, enable, enable))
                db.commit()
                status = "enabled" if enable else "disabled"
                await ctx.send(f"Alerts for {alert_type} have been {status}.")
            
            except mysql.connector.Error as err:
                await ctx.send(f"Failed to set alerts due to a database error: {err}")
            
            finally:
                cursor.close()
                db.close()

        async def notify_user(self, user_id, message):
            """Send a DM or channel message to notify users of an event."""
            user = await self.bot.fetch_user(user_id)
            if user is not None:
                await user.send(message)

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(CardsMain(bot))
