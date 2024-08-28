import discord
from discord.ext import commands
from .CardsMain import get_db_connection  # Assuming get_db_connection is in CardsMain

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def calculate_leaderboard_by_value(self):
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            query = """
            SELECT u.username, SUM(c.market_price) as total_value
            FROM users u
            JOIN cards c ON u.id = c.owner_id
            GROUP BY u.id
            ORDER BY total_value DESC
            LIMIT 10
            """
            cursor.execute(query)
            leaderboard = cursor.fetchall()

            return leaderboard

        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            return None

        finally:
            cursor.close()
            db.close()

    def calculate_leaderboard_by_count(self):
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            query = """
            SELECT u.username, COUNT(c.id) as total_cards
            FROM users u
            JOIN cards c ON u.id = c.owner_id
            GROUP BY u.id
            ORDER BY total_cards DESC
            LIMIT 10
            """
            cursor.execute(query)
            leaderboard = cursor.fetchall()

            return leaderboard

        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            return None

        finally:
            cursor.close()
            db.close()

    @commands.command(name='leaderboard')
    async def leaderboard(self, ctx, metric: str = "value"):
        """Display the leaderboard based on total collection value or number of cards."""
        if metric == "value":
            leaderboard = self.calculate_leaderboard_by_value()
            title = "Top 10 Collectors by Collection Value"
            unit = "$"
        elif metric == "count":
            leaderboard = self.calculate_leaderboard_by_count()
            title = "Top 10 Collectors by Number of Cards"
            unit = " cards"
        else:
            await ctx.send(f"Invalid metric: {metric}. Use 'value' or 'count'.")
            return

        if not leaderboard:
            await ctx.send("No leaderboard data available.")
            return

        embed = discord.Embed(
            title=title,
            color=discord.Color.gold()
        )

        for idx, entry in enumerate(leaderboard, start=1):
            embed.add_field(
                name=f"{idx}. {entry['username']}",
                value=f"{entry['total_value'] if metric == 'value' else entry['total_cards']}{unit}",
                inline=False
            )

        await ctx.send(embed=embed)

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(Leaderboard(bot))