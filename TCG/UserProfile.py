import discord
from discord.ext import commands
import mysql.connector
from .CardsMain import get_db_connection  # Assuming get_db_connection is in CardsMain

class UserProfile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='profile')
    async def profile(self, ctx, target_user: discord.Member = None):
        """Display the user's profile including achievements and badges."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        target_user = target_user or ctx.author

        try:
            # Fetch the profile data
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = (SELECT id FROM users WHERE discord_id = %s)", (target_user.id,))
            profile = cursor.fetchone()

            if not profile:
                await ctx.send(f"{target_user.mention} does not have a profile set up.")
                return

            embed = discord.Embed(
                title=f"{target_user.name}'s Profile",
                description="Here is an overview of your achievements and collection stats:",
                color=discord.Color.blue()
            )

            embed.add_field(name="Total Cards", value=profile['total_cards'], inline=True)
            embed.add_field(name="Total Collection Value", value=f"${profile['total_value']}", inline=True)
            embed.add_field(name="Badges", value=profile['badges'], inline=False)
            embed.add_field(name="Achievements", value=profile['achievements'], inline=False)

            await ctx.send(embed=embed)

        except mysql.connector.Error as err:
            await ctx.send(f"Failed to retrieve the profile due to a database error: {err}")
        
        finally:
            cursor.close()
            db.close()

    @commands.command(name='updateprofile')
    async def update_profile(self, ctx):
        """Update the user's profile statistics."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # Calculate total cards and total value for the user
            cursor.execute("SELECT COUNT(*) AS total_cards, SUM(market_price) AS total_value FROM cards WHERE owner_id = (SELECT id FROM users WHERE discord_id = %s)", (ctx.author.id,))
            stats = cursor.fetchone()

            # Check if user already has a profile
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = (SELECT id FROM users WHERE discord_id = %s)", (ctx.author.id,))
            profile = cursor.fetchone()

            if profile:
                # Update the profile
                cursor.execute(
                    "UPDATE user_profiles SET total_cards = %s, total_value = %s WHERE user_id = %s",
                    (stats['total_cards'], stats['total_value'], profile['user_id'])
                )
            else:
                # Create a new profile
                cursor.execute(
                    "INSERT INTO user_profiles (user_id, total_cards, total_value) VALUES ((SELECT id FROM users WHERE discord_id = %s), %s, %s)",
                    (ctx.author.id, stats['total_cards'], stats['total_value'])
                )
            db.commit()

            await ctx.send(f"{ctx.author.mention}, your profile has been updated.")

        except mysql.connector.Error as err:
            await ctx.send(f"Failed to update your profile due to a database error: {err}")
        
        finally:
            cursor.close()
            db.close()

    @commands.command(name='addbadge')
    async def add_badge(self, ctx, badge_name: str):
        """Add a badge to the user's profile."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # Fetch the user's current badges
            cursor.execute("SELECT badges FROM user_profiles WHERE user_id = (SELECT id FROM users WHERE discord_id = %s)", (ctx.author.id,))
            profile = cursor.fetchone()

            if profile:
                current_badges = profile['badges'].split(', ') if profile['badges'] else []
                if badge_name in current_badges:
                    await ctx.send(f"{ctx.author.mention}, you already have the '{badge_name}' badge.")
                    return

                current_badges.append(badge_name)
                updated_badges = ', '.join(current_badges)

                # Update the badges in the profile
                cursor.execute(
                    "UPDATE user_profiles SET badges = %s WHERE user_id = (SELECT id FROM users WHERE discord_id = %s)",
                    (updated_badges, ctx.author.id)
                )
                db.commit()

                await ctx.send(f"{ctx.author.mention}, the '{badge_name}' badge has been added to your profile.")
            else:
                await ctx.send(f"{ctx.author.mention}, you do not have a profile set up yet. Please update your profile first using `!updateprofile`.")

        except mysql.connector.Error as err:
            await ctx.send(f"Failed to add the badge due to a database error: {err}")
        
        finally:
            cursor.close()
            db.close()

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(UserProfile(bot))
