import discord
from discord.ext import commands
import mysql.connector
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from moviepy.editor import ImageSequenceClip, CompositeVideoClip, ColorClip
import numpy as np
import os

# Create a light rays effect
def add_light_rays(image, intensity=1.0):
    rays = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(rays)
    width, height = image.size
    
    for _ in range(8):  # Create 8 rays
        x1 = np.random.randint(0, width)
        y1 = np.random.randint(0, height)
        x2 = np.random.randint(0, width)
        y2 = np.random.randint(0, height)
        line_width = np.random.randint(10, 20)
        draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, int(255 * intensity)), width=line_width)
        
    rays = rays.filter(ImageFilter.GaussianBlur(radius=15))
    return Image.alpha_composite(image, rays)

# Subtle pulsing glow
def add_pulsing_glow(image, frame, total_frames):
    glow_intensity = 1.0 + 0.5 * np.sin(2 * np.pi * frame / total_frames)
    glow = image.filter(ImageFilter.GaussianBlur(radius=10))
    enhancer = ImageEnhance.Brightness(glow)
    glow = enhancer.enhance(glow_intensity)
    return glow

# Function to add animated particles around the card
def add_particles(image, frame, total_frames):
    particles = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(particles)
    width, height = image.size

    for _ in range(20):  # More particles
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)
        size = np.random.randint(3, 8)
        alpha = int(255 * np.abs(np.sin(np.pi * frame / total_frames)))
        draw.ellipse((x, y, x + size, y + size), fill=(255, 255, 255, alpha))
    
    return Image.alpha_composite(image, particles)

# Function to create the advanced animation
def create_advanced_animation(card_image_path, output_path, frames=60):
    card = Image.open(card_image_path).convert("RGBA")
    card = card.resize((600, 800))  # Resize for better detail

    frames_dir = "advanced_animation_frames"
    os.makedirs(frames_dir, exist_ok=True)

    frame_images = []

    for i in range(frames):
        base_image = card.copy()
        
        # Apply light rays effect
        light_rays_image = add_light_rays(base_image, intensity=0.7 + 0.3 * np.sin(2 * np.pi * i / frames))
        
        # Apply pulsing glow
        glowing_image = add_pulsing_glow(light_rays_image, i, frames)
        
        # Apply particles
        sparkling_image = add_particles(glowing_image, i, frames)

        # Save the frame
        frame_path = os.path.join(frames_dir, f"frame_{i:02d}.png")
        sparkling_image.save(frame_path)
        frame_images.append(frame_path)

    # Create the animation using MoviePy
    clip = ImageSequenceClip(frame_images, fps=30)
    
    # Add a final reveal flash
    final_flash = ColorClip(size=card.size, color=(255, 255, 255), duration=0.2).set_opacity(0.8)
    final_clip = CompositeVideoClip([clip, final_flash.set_start(clip.duration - 0.2)])

    final_clip.write_videofile(output_path, codec="libx264", fps=30)

    # Clean up frame images
    for frame_image in frame_images:
        os.remove(frame_image)

    print(f"Advanced animation saved to {output_path}")

# Example usage
card_image_path = "C:/Users/AZA Custom Builds/Documents\GitHub/Packmon/Images/Moonbreon/MoonbreonVMAX0.001.png"  # Replace with your thumbnail image path
output_path = "rare_glow_sparkle_animation.mp4"  # Output animation file
create_advanced_animation(card_image_path, output_path)

print("Crate opening sequence images generated successfully!")

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

    @commands.command(name='addcard')
    @commands.has_permissions(administrator=True)
    async def addcard(self, ctx):
        """Guided input for adding a card."""
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        card_details = {}

        # Step 1: Ask for the category
        await ctx.send("Please enter the card category (e.g., Marvel, Sports):")
        try:
            category_msg = await self.bot.wait_for('message', check=check, timeout=60)
            card_details['category'] = category_msg.content
        except:
            await ctx.send("You took too long to respond! Please start over.")
            return
        
        # Step 2: Ask for the card name
        await ctx.send("Please enter the card name:")
        try:
            card_name_msg = await self.bot.wait_for('message', check=check, timeout=60)
            card_details['card_name'] = card_name_msg.content
        except:
            await ctx.send("You took too long to respond! Please start over.")
            return

        # Step 3: Ask for the set name
        await ctx.send("Please enter the set name:")
        try:
            set_name_msg = await self.bot.wait_for('message', check=check, timeout=60)
            card_details['set_name'] = set_name_msg.content
        except:
            await ctx.send("You took too long to respond! Please start over.")
            return
        
        # Step 4: Ask for the character/player name
        await ctx.send("Please enter the character or player name:")
        try:
            character_msg = await self.bot.wait_for('message', check=check, timeout=60)
            card_details['character'] = character_msg.content
        except:
            await ctx.send("You took too long to respond! Please start over.")
            return
        
        # Step 5: Ask for the serial number
        await ctx.send("Please enter the serial number (or type 'N/A' if none):")
        try:
            serial_number_msg = await self.bot.wait_for('message', check=check, timeout=60)
            card_details['serial_number'] = serial_number_msg.content
        except:
            await ctx.send("You took too long to respond! Please start over.")
            return
        
        # Step 6: Ask for the rarity
        await ctx.send("Please enter the rarity (e.g., Level 5, Ultra Rare):")
        try:
            rarity_msg = await self.bot.wait_for('message', check=check, timeout=60)
            card_details['rarity'] = rarity_msg.content
        except:
            await ctx.send("You took too long to respond! Please start over.")
            return
        
        # Step 7: Ask for the market price
        await ctx.send("Please enter the market price (e.g., 5.00):")
        try:
            market_price_msg = await self.bot.wait_for('message', check=check, timeout=60)
            card_details['market_price'] = market_price_msg.content
        except:
            await ctx.send("You took too long to respond! Please start over.")
            return
        
        # Step 8: Ask for the image URL
        await ctx.send("Please enter the image URL:")
        try:
            image_url_msg = await self.bot.wait_for('message', check=check, timeout=60)
            card_details['image_url'] = image_url_msg.content
        except:
            await ctx.send("You took too long to respond! Please start over.")
            return
        
        # Insert card details into the database
        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)

            # Ensure the user exists in the database
            cursor.execute("SELECT id FROM users WHERE discord_id = %s", (ctx.author.id,))
            user = cursor.fetchone()
            if not user:
                # Insert the user if they don't exist
                cursor.execute("INSERT INTO users (discord_id, username) VALUES (%s, %s)", (ctx.author.id, ctx.author.name))
                db.commit()
                user_id = cursor.lastrowid
            else:
                user_id = user["id"]

            # Insert the card into the database
            cursor.execute("""
                INSERT INTO cards (owner_id, category, card_name, set_name, character_name, serial_number, rarity, market_price, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                str(card_details['category']),
                str(card_details['card_name']),
                str(card_details['set_name']),
                str(card_details['character']),
                str(card_details['serial_number']) if card_details['serial_number'].lower() != 'n/a' else None,
                str(card_details['rarity']),
                float(card_details['market_price']) if card_details['market_price'].replace('.', '', 1).isdigit() else 0.0,
                str(card_details['image_url'])
            ))
            db.commit()

            await ctx.send(f"Card '{card_details['card_name']}' added to your collection!")

        except mysql.connector.Error as err:
            await ctx.send(f"Failed to add card due to a database error: {err}")
        
        finally:
            cursor.close()
            db.close()

        # Create the embed after inserting the card
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

        # Set the thumbnail to the image URL provided
        embed.set_thumbnail(url=card_details['image_url'])
        
        # Set the large image in the embed
        embed.set_image(url=card_details['image_url'])
        
        # Footer with a category-specific message
        embed.set_footer(text=f"{theme['footer']} - Card added on {ctx.message.created_at.strftime('%B %d, %Y')}")
        
        # Send the embed to the channel
        await ctx.send(embed=embed)

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(CardsMain(bot))
