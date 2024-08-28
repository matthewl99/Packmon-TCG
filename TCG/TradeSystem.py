import discord
import mysql.connector
from discord.ext import commands
from .CardsMain import get_db_connection  # Assuming you have a get_db_connection method in CardsMain

class TradeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='trade')
    async def trade(self, ctx, target_user: discord.Member, offer_card_id: int, request_card_id: int):
        """Initiate a trade with another user using card IDs."""
        if ctx.author == target_user:
            await ctx.send("You cannot trade with yourself!")
            return
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # Get the initiating user from the database
            cursor.execute("SELECT id FROM users WHERE discord_id = %s", (ctx.author.id,))
            from_user = cursor.fetchone()
            if not from_user:
                await ctx.send(f"{ctx.author.mention}, you are not registered in the database.")
                return

            # Get the target user from the database
            cursor.execute("SELECT id FROM users WHERE discord_id = %s", (target_user.id,))
            to_user = cursor.fetchone()
            if not to_user:
                await ctx.send(f"{target_user.mention} is not registered in the database.")
                return

            # Check ownership of the offer card
            cursor.execute("SELECT id, card_name FROM cards WHERE id = %s AND owner_id = %s", (offer_card_id, from_user['id']))
            offer_card = cursor.fetchone()
            if not offer_card:
                await ctx.send(f"{ctx.author.mention}, you do not own the card with ID: {offer_card_id}.")
                return

            # Check ownership of the request card
            cursor.execute("SELECT id, card_name FROM cards WHERE id = %s AND owner_id = %s", (request_card_id, to_user['id']))
            request_card = cursor.fetchone()
            if not request_card:
                await ctx.send(f"{target_user.mention} does not own the card with ID: {request_card_id}.")
                return

            # Insert the trade into the database
            cursor.execute(
                "INSERT INTO trades (from_user_id, to_user_id, offer_card_id, request_card_id, status) VALUES (%s, %s, %s, %s, %s)",
                (from_user['id'], to_user['id'], offer_card['id'], request_card['id'], 'pending')
            )
            db.commit()
            trade_id = cursor.lastrowid

            # Notify the target user
            embed = discord.Embed(
                title="Trade Proposal",
                description=f"{ctx.author.mention} is offering {offer_card['card_name']} (ID: {offer_card_id}) in exchange for {request_card['card_name']} (ID: {request_card_id}).",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Trade ID: {trade_id}")

            await ctx.send(f"{target_user.mention}, you have a new trade proposal!", embed=embed)

        except mysql.connector.Error as err:
            await ctx.send(f"Database error: {err}")
        
        finally:
            cursor.close()
            db.close()

    @commands.command(name='inventory')
    async def inventory(self, ctx):
        """Display the user's card inventory."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # Get all cards owned by the user
            cursor.execute("SELECT id, card_name, nickname FROM cards WHERE owner_id = (SELECT id FROM users WHERE discord_id = %s)", (ctx.author.id,))
            cards = cursor.fetchall()

            if not cards:
                await ctx.send(f"{ctx.author.mention}, you have no cards in your inventory.")
                return

            embed = discord.Embed(
                title=f"{ctx.author.name}'s Card Inventory",
                description="Here are your cards:",
                color=discord.Color.green()
            )

            for card in cards:
                display_name = f"{card['nickname']} (ID: {card['id']})" if card['nickname'] else f"{card['card_name']} (ID: {card['id']})"
                embed.add_field(
                    name=display_name,
                    value=f"ID: {card['id']}",
                    inline=False
                )

            await ctx.send(embed=embed)

        except mysql.connector.Error as err:
            await ctx.send(f"Failed to retrieve your inventory due to a database error: {err}")
        
        finally:
            cursor.close()
            db.close()

    @commands.command(name='setnickname')
    async def set_nickname(self, ctx, card_id: int, nickname: str):
        """Set a nickname for a specific card."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # Update the nickname for the specified card
            cursor.execute("UPDATE cards SET nickname = %s WHERE id = %s AND owner_id = (SELECT id FROM users WHERE discord_id = %s)", (nickname, card_id, ctx.author.id))
            db.commit()

            if cursor.rowcount == 0:
                await ctx.send(f"{ctx.author.mention}, you do not own a card with ID {card_id}.")
            else:
                await ctx.send(f"Nickname for card ID {card_id} has been set to '{nickname}'.")

        except mysql.connector.Error as err:
            await ctx.send(f"Failed to set the nickname due to a database error: {err}")
        
        finally:
            cursor.close()
            db.close()

    @commands.command(name='accepttrade')
    async def accept_trade(self, ctx, trade_id: int):
        """Accept a pending trade and log it, while canceling other pending trades involving the same cards."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # Fetch the user ID of the command issuer
            cursor.execute("SELECT id FROM users WHERE discord_id = %s", (ctx.author.id,))
            to_user = cursor.fetchone()
            
            if not to_user:
                await ctx.send(f"{ctx.author.mention}, you are not registered in the database.")
                return

            # Get the trade details from the database
            cursor.execute("SELECT * FROM trades WHERE id = %s AND to_user_id = %s AND status = 'pending'", (trade_id, to_user['id']))
            trade = cursor.fetchone()
            
            if not trade:
                await ctx.send(f"Trade ID {trade_id} is not valid or not pending for you.")
                return

            # Ensure both cards are still in their respective owners' inventories
            cursor.execute("SELECT id FROM cards WHERE id = %s AND owner_id = %s", (trade['offer_card_id'], trade['from_user_id']))
            offer_card = cursor.fetchone()
            
            cursor.execute("SELECT id FROM cards WHERE id = %s AND owner_id = %s", (trade['request_card_id'], trade['to_user_id']))
            request_card = cursor.fetchone()

            if not offer_card or not request_card:
                await ctx.send(f"Trade ID {trade_id} cannot be completed because one or more cards are no longer available.")
                
                # Cancel the trade since the cards are no longer available
                cursor.execute("UPDATE trades SET status = 'cancelled' WHERE id = %s", (trade_id,))
                db.commit()
                
                return

            # Swap ownership of the cards
            cursor.execute("UPDATE cards SET owner_id = %s WHERE id = %s", (trade['to_user_id'], trade['offer_card_id']))
            cursor.execute("UPDATE cards SET owner_id = %s WHERE id = %s", (trade['from_user_id'], trade['request_card_id']))

            # Update the trade status to 'accepted'
            cursor.execute("UPDATE trades SET status = 'accepted' WHERE id = %s", (trade_id,))
            db.commit()

            # Cancel all other pending trades involving the same cards
            cursor.execute("""
                UPDATE trades 
                SET status = 'cancelled' 
                WHERE (offer_card_id = %s OR request_card_id = %s OR offer_card_id = %s OR request_card_id = %s)
                AND status = 'pending' AND id != %s
            """, (trade['offer_card_id'], trade['offer_card_id'], trade['request_card_id'], trade['request_card_id'], trade_id))
            db.commit()

            # Log the trade in trade_logs
            cursor.execute(
                "INSERT INTO trade_logs (trade_id, from_user_id, to_user_id, offer_card_ids, request_card_ids) "
                "VALUES (%s, %s, %s, %s, %s)",
                (
                    trade_id,
                    trade['from_user_id'],
                    trade['to_user_id'],
                    str(trade['offer_card_id']),  # Convert to string for storage
                    str(trade['request_card_id'])  # Convert to string for storage
                )
            )
            db.commit()

            await ctx.send(f"Trade ID {trade_id} has been accepted and logged. The cards have been exchanged.")

        except mysql.connector.Error as err:
            await ctx.send(f"Failed to accept the trade due to a database error: {err}")
        
        finally:
            cursor.close()
            db.close()

    @commands.command(name='rejecttrade')
    async def reject_trade(self, ctx, trade_id: int):
        """Reject a pending trade."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # Check if the trade exists and is pending
            cursor.execute("SELECT * FROM trades WHERE id = %s AND to_user_id = %s AND status = 'pending'", (trade_id, ctx.author.id))
            trade = cursor.fetchone()
            if not trade:
                await ctx.send(f"Trade ID {trade_id} is not valid or not pending for you.")
                return

            # Update the trade status to rejected
            cursor.execute("UPDATE trades SET status = 'rejected' WHERE id = %s", (trade_id,))
            db.commit()

            await ctx.send(f"Trade ID {trade_id} has been rejected.")

        except mysql.connector.Error as err:
            await ctx.send(f"Failed to reject the trade due to a database error: {err}")
        
        finally:
            cursor.close()
            db.close()

    @commands.command(name='pendingtrades')
    async def pending_trades(self, ctx):
        """View all pending trades for the user."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # Get all pending trades for the user
            cursor.execute("SELECT * FROM trades WHERE to_user_id = (SELECT id FROM users WHERE discord_id = %s) AND status = 'pending'", (ctx.author.id,))
            trades = cursor.fetchall()

            if not trades:
                await ctx.send(f"{ctx.author.mention}, you have no pending trades.")
                return

            embed = discord.Embed(
                title="Pending Trades",
                description="Here are your pending trades:",
                color=discord.Color.gold()
            )

            for trade in trades:
                cursor.execute("SELECT card_name FROM cards WHERE id = %s", (trade['offer_card_id'],))
                offer_card = cursor.fetchone()['card_name']
                cursor.execute("SELECT card_name FROM cards WHERE id = %s", (trade['request_card_id'],))
                request_card = cursor.fetchone()['card_name']
                embed.add_field(
                    name=f"Trade ID: {trade['id']}",
                    value=f"Offered: **{offer_card}**\nRequested: **{request_card}**",
                    inline=False
                )
            print(f"Trades found: {trades}")
            await ctx.send(embed=embed)

        except mysql.connector.Error as err:
            await ctx.send(f"Failed to retrieve pending trades due to a database error: {err}")
        
        finally:
            cursor.close()
            db.close()


    @commands.command(name='canceltrade')
    async def cancel_trade(self, ctx, trade_id: int):
        """Cancel a pending trade that you initiated."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # Check if the trade exists and was initiated by the user
            cursor.execute("SELECT * FROM trades WHERE id = %s AND from_user_id = %s AND status = 'pending'", (trade_id, ctx.author.id))
            trade = cursor.fetchone()
            if not trade:
                await ctx.send(f"Trade ID {trade_id} is not valid or not pending for you.")
                return

            # Update the trade status to cancelled
            cursor.execute("UPDATE trades SET status = 'cancelled' WHERE id = %s", (trade_id,))
            db.commit()

            await ctx.send(f"Trade ID {trade_id} has been cancelled.")

        except mysql.connector.Error as err:
            await ctx.send(f"Failed to cancel the trade due to a database error: {err}")
        
        finally:
            cursor.close()
            db.close()

    @commands.command(name='tradehistory')
    async def trade_history(self, ctx):
        """Display the user's trade history."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # Get the trade history for the user
            cursor.execute(
                "SELECT * FROM trade_logs WHERE from_user_id = %s OR to_user_id = %s ORDER BY trade_date DESC",
                (ctx.author.id, ctx.author.id)
            )
            trades = cursor.fetchall()

            if not trades:
                await ctx.send(f"{ctx.author.mention}, you have no trade history.")
                return

            embed = discord.Embed(
                title=f"{ctx.author.name}'s Trade History",
                description="Here is your trade history:",
                color=discord.Color.teal()
            )

            for trade in trades:
                cursor.execute("SELECT card_name FROM cards WHERE id = %s", (trade['offer_card_ids'],))
                offer_card = cursor.fetchone()['card_name']
                cursor.execute("SELECT card_name FROM cards WHERE id = %s", (trade['request_card_ids'],))
                request_card = cursor.fetchone()['card_name']
                trade_date = trade['trade_date'].strftime('%B %d, %Y %H:%M:%S')

                embed.add_field(
                    name=f"Trade ID: {trade['trade_id']} ({trade_date})",
                    value=f"Offered: **{offer_card}**\nReceived: **{request_card}**",
                    inline=False
                )

            await ctx.send(embed=embed)

        except mysql.connector.Error as err:
            await ctx.send(f"Failed to retrieve your trade history due to a database error: {err}")
        
        finally:
            cursor.close()
            db.close()

@commands.command(name='multitrade')
async def multi_trade(self, ctx, target_user: discord.Member, offer_card_ids: str, request_card_ids: str):
    """Initiate a trade with another user involving multiple cards."""
    if ctx.author == target_user:
        await ctx.send("You cannot trade with yourself!")
        return
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Convert input strings to lists of IDs
        offer_card_ids = offer_card_ids.split(',')
        request_card_ids = request_card_ids.split(',')

        # Get the initiating user from the database
        cursor.execute("SELECT id FROM users WHERE discord_id = %s", (ctx.author.id,))
        from_user = cursor.fetchone()
        if not from_user:
            await ctx.send(f"{ctx.author.mention}, you are not registered in the database.")
            return

        # Get the target user from the database
        cursor.execute("SELECT id FROM users WHERE discord_id = %s", (target_user.id,))
        to_user = cursor.fetchone()
        if not to_user:
            await ctx.send(f"{target_user.mention} is not registered in the database.")
            return

        # Check ownership of the offer cards
        for card_id in offer_card_ids:
            cursor.execute("SELECT id FROM cards WHERE id = %s AND owner_id = %s", (card_id, from_user['id']))
            if not cursor.fetchone():
                await ctx.send(f"{ctx.author.mention}, you do not own card with ID: {card_id}.")
                return

        # Check ownership of the request cards
        for card_id in request_card_ids:
            cursor.execute("SELECT id FROM cards WHERE id = %s AND owner_id = %s", (card_id, to_user['id']))
            if not cursor.fetchone():
                await ctx.send(f"{target_user.mention} does not own card with ID: {card_id}.")
                return

        # Insert the trade into the database
        cursor.execute(
            "INSERT INTO trades (from_user_id, to_user_id, offer_card_ids, request_card_ids, status) VALUES (%s, %s, %s, %s, %s)",
            (from_user['id'], to_user['id'], ','.join(offer_card_ids), ','.join(request_card_ids), 'pending')
        )
        db.commit()
        trade_id = cursor.lastrowid

        # Notify the target user
        embed = discord.Embed(
            title="Multi-Card Trade Proposal",
            description=f"{ctx.author.mention} is offering cards with IDs: {', '.join(offer_card_ids)} in exchange for cards with IDs: {', '.join(request_card_ids)}.",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Trade ID: {trade_id}")

        await ctx.send(f"{target_user.mention}, you have a new trade proposal!", embed=embed)

    except mysql.connector.Error as err:
        await ctx.send(f"Database error: {err}")
    
    finally:
        cursor.close()
        db.close()

@commands.command(name='giftcard')
async def gift_card(self, ctx, target_user: discord.Member, card_id: int):
    """Gift a card to another user."""
    if ctx.author == target_user:
        await ctx.send("You cannot gift a card to yourself!")
        return
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Check if the user owns the card
        cursor.execute("SELECT id FROM cards WHERE id = %s AND owner_id = (SELECT id FROM users WHERE discord_id = %s)", (card_id, ctx.author.id))
        card = cursor.fetchone()
        if not card:
            await ctx.send(f"{ctx.author.mention}, you do not own the card with ID {card_id}.")
            return

        # Transfer the card to the target user
        cursor.execute("UPDATE cards SET owner_id = (SELECT id FROM users WHERE discord_id = %s) WHERE id = %s", (target_user.id, card_id))
        db.commit()

        await ctx.send(f"Card ID {card_id} has been gifted to {target_user.mention}.")
    
    except mysql.connector.Error as err:
        await ctx.send(f"Failed to gift the card due to a database error: {err}")
    
    finally:
        cursor.close()
        db.close()

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(TradeSystem(bot))
