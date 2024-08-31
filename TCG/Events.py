import discord
from discord.ext import commands
import mysql.connector
from .CardsMain import get_db_connection  # Assuming you have a get_db_connection method in CardsMain

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='myevents')
    async def my_events(self, ctx):
        """Check event participation."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("SELECT event_name, status FROM events WHERE user_id = (SELECT id FROM users WHERE discord_id = %s)", (ctx.author.id,))
            events = cursor.fetchall()
            
            if not events:
                await ctx.send(f"{ctx.author.mention}, you are not currently participating in any events.")
                return

            embed = discord.Embed(
                title=f"{ctx.author.name}'s Events",
                description="Here are your active events:",
                color=discord.Color.orange()
            )

            for event in events:
                embed.add_field(name=event['event_name'], value=f"Status: {event['status']}", inline=False)

            await ctx.send(embed=embed)

        except mysql.connector.Error as err:
            await ctx.send(f"Failed to retrieve your events due to a database error: {err}")
        
        finally:
            cursor.close()
            db.close()

    @commands.command(name='myachievements')
    async def my_achievements(self, ctx):
        """View earned achievements."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("SELECT achievement_name, date_earned FROM achievements WHERE user_id = (SELECT id FROM users WHERE discord_id = %s)", (ctx.author.id,))
            achievements = cursor.fetchall()

            if not achievements:
                await ctx.send(f"{ctx.author.mention}, you have not earned any achievements yet.")
                return

            embed = discord.Embed(
                title=f"{ctx.author.name}'s Achievements",
                description="Here are your earned achievements:",
                color=discord.Color.gold()
            )

            for achievement in achievements:
                embed.add_field(name=achievement['achievement_name'], value=f"Earned on: {achievement['date_earned']}", inline=False)

            await ctx.send(embed=embed)

        except mysql.connector.Error as err:
            await ctx.send(f"Failed to retrieve your achievements due to a database error: {err}")
        
        finally:
            cursor.close()
            db.close()

    @commands.command(name='joinevent')
    async def join_event(self, ctx, event_name: str):
        """Join an event."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("INSERT INTO events (user_id, event_name, status) VALUES ((SELECT id FROM users WHERE discord_id = %s), %s, 'active')", (ctx.author.id, event_name))
            db.commit()
            await ctx.send(f"{ctx.author.mention}, you have successfully joined the event: {event_name}.")

        except mysql.connector.Error as err:
            await ctx.send(f"Failed to join the event due to a database error: {err}")
        
        finally:
            cursor.close()
            db.close()

    @commands.command(name='invite')
    async def invite(self, ctx):
        """Send the community invite message."""
        embed = discord.Embed(
            title="✮* 𝒯𝒽𝑒 𝐸𝑒𝓋𝑒𝑒 𝒟𝑒𝓃  *✮",
            description=(
                "············· ── ⋆⋅☆⋅⋆ ── ·············\n\n"
                "Hiya Pals!\n"
                "Come join TED and be a part of our amazing community! We have a fun hangout space to make new friends, "
                "bully-free, and share laughter with one another! Can’t wait to have you join our family!\n\n"
                "············· ── ⋆⋅☆⋅⋆ ── ·············\n"
                "✧🍄˖°- S/V Sys Bots\n"
                "✧🍄˖°- Bots for all Pokemon Switch games\n"
                "✧🍄˖°- Variety of Giveaways\n"
                "✧🍄˖°- Plenty of Eevee emotes!\n"
                "✧🍄˖°- Active Staff!\n"
                "✧🍄˖°- Poketwo Events\n"
                "✧🍄˖°- Variety of giveaways that may include Nitro, Poketwo-themed events, S/V events, and more!\n"
                "············· ── ⋆⋅☆⋅⋆ ── ·············\n"
                "👇⬇️⬇️ • Join Now! • ⬇️⬇️👇\n"
                "🌲 [Join The Eevee Den](https://discord.gg/the-eevee-den-778557967682502676) 🌲"
            ),
            color=discord.Color.orange()
        )

        embed.set_image(url="https://media.discordapp.net/attachments/1112549567683121153/1172914921944649748/The_Eevee_Den.gif?ex=66d28865&is=66d136e5&hm=fad2f068abdfbf22207af816d8c33e711e1e798fd8d31f929e3ebe210c4b366e&=&width=550&height=550")

        await ctx.send(embed=embed)
        
    @commands.command(name='completeachievement')
    async def complete_achievement(self, ctx, achievement_name: str):
        """Manually complete an achievement (admin-only command)."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command.")
            return

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("INSERT INTO achievements (user_id, achievement_name) VALUES ((SELECT id FROM users WHERE discord_id = %s), %s)", (ctx.author.id, achievement_name))
            db.commit()
            await ctx.send(f"{ctx.author.mention} has earned the achievement: {achievement_name}.")

        except mysql.connector.Error as err:
            await ctx.send(f"Failed to record the achievement due to a database error: {err}")
        
        finally:
            cursor.close()
            db.close()

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(Events(bot))
