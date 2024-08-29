import discord
import mysql.connector
from discord.ext import commands
from discord.ui import Button, View
from .CardsMain import get_db_connection
import asyncio
from PIL import Image
import requests
from io import BytesIO

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

    @commands.command(name='addcard')
    @commands.has_permissions(administrator=True)
    async def addcard(self, ctx):
        """Guided input for adding a card with a merged front and back image."""
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        card_details = {}

        async def prompt_for_input(prompt):
            """Prompt the user for input and delete the message after processing."""
            await ctx.send(prompt, delete_after=60)
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                await msg.delete()
                return msg.content
            except asyncio.TimeoutError:
                await ctx.send("You took too long to respond! Please start over.", delete_after=10)
                return None

        # Step 1: Ask for the card category
        card_details['category'] = await prompt_for_input("Please enter the card category (e.g., Marvel, Sports):")
        if card_details['category'] is None: return

        # Step 2: Ask for the card name
        card_details['card_name'] = await prompt_for_input("Please enter the card number/name:")
        if card_details['card_name'] is None: return

        # Step 3: Ask for the set name
        card_details['set_name'] = await prompt_for_input("Please enter the set name:")
        if card_details['set_name'] is None: return

        # Step 4: Ask for the character/player name
        card_details['character'] = await prompt_for_input("Please enter the character or player name:")
        if card_details['character'] is None: return

        # Step 5: Ask for the serial number
        card_details['serial_number'] = await prompt_for_input("Please enter the serial number (or type 'N/A' if none):")
        if card_details['serial_number'] is None: return

        # Step 6: Ask for the rarity
        card_details['rarity'] = await prompt_for_input("Please enter the rarity (e.g., Level 5, Ultra Rare):")
        if card_details['rarity'] is None: return

        # Step 7: Ask for the market price
        card_details['market_price'] = await prompt_for_input("Please enter the market price (e.g., 5.00):")
        if card_details['market_price'] is None: return

        # Step 8: Ask for the front image URL
        card_details['front_image_url'] = await prompt_for_input("Please enter the front image URL:")
        if card_details['front_image_url'] is None: return

        # Step 9: Ask for the back image URL
        card_details['back_image_url'] = await prompt_for_input("Please enter the back image URL:")
        if card_details['back_image_url'] is None: return
        
        # Download the images
        try:
            response_front = requests.get(card_details['front_image_url'])
            response_back = requests.get(card_details['back_image_url'])

            img_front = Image.open(BytesIO(response_front.content))
            img_back = Image.open(BytesIO(response_back.content))

            # Combine the images side by side
            total_width = img_front.width + img_back.width
            max_height = max(img_front.height, img_back.height)

            combined_img = Image.new('RGB', (total_width, max_height))
            combined_img.paste(img_front, (0, 0))
            combined_img.paste(img_back, (img_front.width, 0))

            # Save the combined image to a BytesIO object
            combined_image_io = BytesIO()
            combined_img.save(combined_image_io, format='PNG')
            combined_image_io.seek(0)

            # Create a discord.File object from the combined image
            file = discord.File(fp=combined_image_io, filename="combined_card.png")
        except Exception as e:
            await ctx.send(f"Failed to process images: {e}", delete_after=10)
            return

        # Create the embed
        theme = self.get_theme(card_details['category'])
        
        embed = discord.Embed(
            title=f"{theme['icon']} {card_details['card_name']}", 
            description=f"Set: {card_details['set_name']}", 
            color=theme['color']
        )
        
        embed.add_field(name="**Category**", value=f"{card_details['category']}", inline=True)
        embed.add_field(name="**Character**", value=f"{card_details['character']}", inline=True)
        embed.add_field(name="**Serial Number**", value=f"{card_details['serial_number']}", inline=True)
        embed.add_field(name="⭐ **Rarity**", value=f"*{card_details['rarity']}*", inline=True)
        embed.add_field(name="💲 **Market Price**", value=f"${card_details['market_price']}", inline=True)

        # Set the combined image in the embed
        embed.set_image(url="attachment://combined_card.png")
        
        # Footer with a category-specific message
        embed.set_footer(text=f"{theme['footer']} - Card added on {ctx.message.created_at.strftime('%B %d, %Y')}")
        
        # Send the embed to the channel
        await ctx.send(embed=embed, file=file)

    def get_theme(self, category):
        """Get the theme details based on the category."""
        themes = {
            "Marvel": {"icon": "🦸‍♂️", "color": discord.Color.red(), "footer": "Marvel Collection"},
            "Sports": {"icon": "🏀", "color": discord.Color.blurple(), "footer": "Sports Collection"},
            # Add more themes as needed
        }
        return themes.get(category, {"icon": "🎴", "color": discord.Color.blue(), "footer": "Card Collection"})

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(ShowcaseSystem(bot))