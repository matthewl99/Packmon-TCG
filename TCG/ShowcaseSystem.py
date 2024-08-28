import discord
import mysql.connector
from discord.ext import commands
from discord.ui import Button, View
from .CardsMain import get_db_connection

class ShowcaseSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='showcase')
    async def showcase(self, ctx, target_user: discord.User = None):
        """Display a user's showcase with customizations."""
        target_user = target_user or ctx.author  # Default to the command user if no target user is specified
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            # Retrieve the target user's customizations
            cursor.execute("SELECT * FROM showcase_customizations WHERE user_id = (SELECT id FROM users WHERE discord_id = %s)", (target_user.id,))
            customization = cursor.fetchone()

            if not customization:
                await ctx.send(f"{target_user.mention} hasn't customized their showcase yet.")
                return

            # Fetch the target user's showcased cards
            cursor.execute("SELECT card_name, rarity, market_price, image_url FROM cards WHERE owner_id = (SELECT id FROM users WHERE discord_id = %s) AND showcase = TRUE", (target_user.id,))
            cards = cursor.fetchall()

            if not cards:
                await ctx.send(f"{target_user.mention} doesn't have any cards in their showcase.")
                return

            # Pagination variables
            cards_per_page = 1
            total_pages = (len(cards) + cards_per_page - 1) // cards_per_page

            # Show the first page
            await self.show_page(ctx, cards, 0, total_pages, customization, target_user)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
        
        finally:
            cursor.close()
            db.close()

    async def show_page(self, ctx, cards, page, total_pages, customization, target_user):
        """Display a specific page of the user's showcased cards."""
        start = page * 1
        end = start + 1

        embed = discord.Embed(
            title=customization.get('title', f"{target_user.name}'s Showcase"),
            description=f"Showing card {page + 1} of {total_pages}",
            color=discord.Color.from_str(customization['theme_color']) if customization['theme_color'] else discord.Color.blue(),
        )

        if customization['background_url']:
            embed.set_image(url=customization['background_url'])

        for card in cards[start:end]:
            rarity = card.get('rarity', 'Unknown')
            market_price = float(card.get('market_price', 0))

            embed.add_field(
                name=card['card_name'],
                value=f"Rarity: {rarity} | Value: ${market_price:.2f}",
                inline=False
            )
            
            # Display the card image
            if card['image_url']:
                embed.set_image(url=card['image_url'])

        embed.set_footer(text=f"Page {page + 1}/{total_pages} | Showcase customized by {target_user.name}")

        # Creating navigation buttons
        buttons = View()

        if page > 0:
            buttons.add_item(Button(label="Previous", style=discord.ButtonStyle.primary, custom_id="prev_card"))
        
        if page < total_pages - 1:
            buttons.add_item(Button(label="Next", style=discord.ButtonStyle.primary, custom_id="next_card"))

        message = await ctx.send(embed=embed, view=buttons)

        # Button click handling
        async def button_callback(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This button is not for you!", ephemeral=True)
                return

            if interaction.custom_id == "next_card":
                await self.show_page(ctx, cards, page + 1, total_pages, customization, target_user)
            elif interaction.custom_id == "prev_card":
                await self.show_page(ctx, cards, page - 1, total_pages, customization, target_user)

            await message.delete()  # Clean up the old message with buttons

        for button in buttons.children:
            button.callback = button_callback

    # Other commands remain the same

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(ShowcaseSystem(bot))