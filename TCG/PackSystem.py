import discord
import random
import asyncio
from discord.ext import commands
from discord.ui import Button, View
from .EconomySystem import EconomySystem
from .CardsMain import get_db_connection

class PackSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    packs = {
        "moonbreon": {
            "price": 200,
            "cards": [
                {"name": "Energy", "hit_percentage": 55, "price": 5, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686610288185354/energy.png"},
                {"name": "Eevee", "hit_percentage": 42, "price": 10, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686626973253672/eevee.png"},
                {"name": "Umbreon V", "hit_percentage": 1, "price": 1000, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686674335465644/UmbreonV1.png"},
                {"name": "Umbreon VMax", "hit_percentage": 5, "price": 2000, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686754794541076/UmbreonVMAX0.2.png"},
                {"name": "Umbreon GX", "hit_percentage": 2, "price": 500, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686788793696296/UmbreonGX0.5.png"},
                {"name": "Umbreon GX", "hit_percentage": 1, "price": 150, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686817717485618/UmbreonGX0.15.png"},
                {"name": "Umbreon V", "hit_percentage": 0.5, "price": 150, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277688032526602464/UmbreonV0.15.png"},
                {"name": "Umbreon V", "hit_percentage": 0.25, "price": 150, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686871836725330/UmbreonV0.15_4k.png"},
                {"name": "Umbreon VMAX", "hit_percentage": 0.25, "price": 1000, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686909359095858/UmbreonVMAX0.1.png"},
                {"name": "Umbreon VMAX", "hit_percentage": 0.02, "price": 2000, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686909359095858/UmbreonVMAX0.1.png"},
                {"name": "Umbreon GX", "hit_percentage": 0.02, "price": 2000, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686947397111908/UmbreonGX0.02.png"},
                {"name": "Umbreon VMAX", "hit_percentage": 0.01, "price": 3000, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686966577659915/MoonbreonVMAX0.001.png"}
            ],
            "image": "https://media.discordapp.net/attachments/1277686502335447171/1277686582773813339/Crate.png"
        }
    }

    card_back_url = "https://media.discordapp.net/attachments/1277686502335447171/1277688692600737863/pokemoncard-back.png"

    @commands.command(name='buypack')
    async def buy_pack(self, ctx, pack_name: str):
        """Buy a pack of cards."""
        db = get_db_connection()
        cursor = db.cursor()

        if pack_name not in self.packs:
            await ctx.send(f"{ctx.author.mention}, that pack does not exist.")
            return

        pack_info = self.packs[pack_name]
        user_currency = await self.bot.get_cog("EconomySystem").get_currency(ctx.author.id)

        if user_currency >= pack_info["price"]:
            await self.bot.get_cog("EconomySystem").add_currency(ctx.author.id, -pack_info["price"])
            cursor.execute("INSERT INTO user_packs (user_id, pack_name) VALUES ((SELECT id FROM users WHERE discord_id = %s), %s)", (ctx.author.id, pack_name))
            db.commit()

            await ctx.send(f"{ctx.author.mention}, you bought a {pack_name} pack for {pack_info['price']} currency! Use `!openpack {pack_name}` to open it.")

        else:
            await ctx.send(f"{ctx.author.mention}, you don't have enough currency to buy this pack.")

        cursor.close()
        db.close()

    @commands.command(name='openpack')
    async def open_pack(self, ctx, pack_name: str):
        """Open a purchased pack and receive cards."""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM user_packs WHERE user_id = (SELECT id FROM users WHERE discord_id = %s) AND pack_name = %s", (ctx.author.id, pack_name))
        pack = cursor.fetchone()

        if not pack:
            await ctx.send(f"{ctx.author.mention}, you don't have any {pack_name} packs to open.")
            return

        pack_info = self.packs.get(pack_name)
        cards_obtained = self.draw_cards(pack_info["cards"])

        # Debug: Show the number of cards obtained
        print(f"Cards obtained: {len(cards_obtained)}")
        print(f"Cards obtained: {cards_obtained}")

        # Filter good and bad cards
        good_cards, bad_cards = self.filter_good_bad_cards(cards_obtained)

        # Debug: Show how many good and bad cards were filtered
        print(f"Good cards: {len(good_cards)}, Bad cards: {len(bad_cards)}")
        print(f"Good cards: {good_cards}")
        print(f"Bad cards: {bad_cards}")

        # Show pack opening animation first
        await self.show_pack_opening(ctx, pack_name)

        if not good_cards:
            print("No good cards were drawn!")

            # Sell bad cards and refund the user
            total_value = sum(card['price'] for card in bad_cards)
            await self.bot.get_cog("EconomySystem").add_currency(ctx.author.id, total_value)
            await ctx.send(f"{ctx.author.mention}, you didn't get any good cards in this pack, so we've refunded you {total_value} currency for the cards pulled.")
            
            # Reveal all bad cards as well before exiting
            for card in bad_cards:
                await self.reveal_card_suspense(ctx, card)

            cursor.close()
            db.close()
            return

        # Save all cards to the user's collection
        self.save_cards_to_collection(ctx.author.id, good_cards + bad_cards, pack_name, cursor)

        cursor.execute("DELETE FROM user_packs WHERE user_id = (SELECT id FROM users WHERE discord_id = %s) AND pack_name = %s LIMIT 1", (ctx.author.id, pack_name))
        db.commit()

        # Debug: Before revealing cards
        print("Starting to reveal cards...")

        # Simulate a scroll effect for the good cards
        await self.simulate_scroll(ctx, good_cards)

        cursor.close()
        db.close()

    async def simulate_scroll(self, ctx, good_cards):
        """Simulate a scrolling effect through the cards and land on one."""
        scroll_cycles = 10  # Number of times to scroll through the cards
        scroll_speed = 0.1  # Delay between scrolls

        # Select a random card from good cards or a random card from bad cards if no good cards
        card_to_land_on = random.choice(good_cards)

        # Simulate the scroll effect
        for _ in range(scroll_cycles):
            card = random.choice(good_cards)
            embed = discord.Embed(
                title=f"Scrolling...",
                description=f"🎴 {card['name']}",
                color=discord.Color.blue()
            )
            embed.set_image(url=card['image_url'])
            await ctx.send(embed=embed)
            await asyncio.sleep(scroll_speed)
        
        # Land on the final card
        await self.grand_reveal_card(ctx, card_to_land_on)

    def draw_cards(self, cards):
        """Draw cards from the pack based on hit percentage."""
        drawn_cards = []
        for card in cards:
            if random.randint(1, 100) <= card['hit_percentage']:
                drawn_cards.append(card)
        return drawn_cards

    def filter_good_bad_cards(self, cards):
        """Filter out good and bad cards based on hit percentage."""
        threshold = 10  # Hit percentage below this is considered good
        good_cards = [card for card in cards if card['hit_percentage'] <= threshold]
        bad_cards = [card for card in cards if card['hit_percentage'] > threshold]
        return good_cards, bad_cards

    def save_cards_to_collection(self, user_id, cards, pack_name, cursor):
        """Save cards to the user's collection in the cards table."""
        for card in cards:
            cursor.execute("""
                INSERT INTO cards (owner_id, card_name, image_url, set_name, market_price)
                VALUES ((SELECT id FROM users WHERE discord_id = %s), %s, %s, %s, %s)
            """, (user_id, card['name'], card['image_url'], pack_name, card['price']))
    
    async def reveal_card_suspense(self, ctx, card):
        """Reveal a card with a suspenseful delay."""
        embed = discord.Embed(title="Revealing your card...", color=discord.Color.blue())
        embed.set_image(url=self.card_back_url)

        try:
            message = await ctx.send(embed=embed)
            await asyncio.sleep(2)  # Pause for suspense

            embed = discord.Embed(
                title="It's coming...",
                color=discord.Color.orange()
            )
            await message.edit(embed=embed)

            await asyncio.sleep(1)  # Another short pause

            embed = discord.Embed(
                title=card['name'],
                description=f"Hit Percentage: {card['hit_percentage']}%\nValue: {card['price']} currency",
                color=discord.Color.gold() if card['hit_percentage'] <= 10 else discord.Color.blue()
            )
            embed.set_image(url=card['image_url'])
            await message.edit(embed=embed)

        except discord.HTTPException as e:
            print(f"Discord HTTPException: {e}")
        except Exception as e:
            print(f"Error in reveal_card_suspense: {e}")

    async def grand_reveal_card(self, ctx, card):
        """Showcase the rarest card with a special grand reveal."""
        await ctx.send("✨ **Get ready...** ✨")
        await asyncio.sleep(2)
        await ctx.send("🌟 **Here comes the rarest card in your pack!** 🌟")
        await asyncio.sleep(2)
        await self.reveal_rare_card(ctx, card)

    async def reveal_rare_card(self, ctx, card):
        """Reveal a rare card with a special effect."""

        # Step 1: Send the animation video to build hype
        animation_file_path = "C:/Users/AZA Custom Builds/Documents/GitHub/Packmon/rare_glow_sparkle_animation.png"  # Replace with the path to your animation file
        animation_file = discord.File(animation_file_path, filename="rare_glow_sparkle_animation.mp4")
        
        await ctx.send(file=animation_file)
        
        # Step 2: Add a short delay to ensure the animation plays before the card is revealed
        await asyncio.sleep(5)  # Adjust timing based on video length

        # Step 3: Reveal the rare card with the embed
        embed = discord.Embed(
            title=f"🌟 {card['name']} 🌟",
            description=f"Hit Percentage: {card['hit_percentage']}%\nValue: {card['price']} currency",
            color=discord.Color.gold()
        )
        embed.set_image(url=card['image_url'])
        embed.set_thumbnail(url="C:/Users/AZA Custom Builds/Documents/GitHub/Packmon/Images/Lightball.png")
        await ctx.send(embed=embed)
        
        # Step 4: Announce the rare card
        await self.announce_rare_card(ctx, card)

    async def announce_rare_card(self, ctx, card):
        """Announce a rare card pull in the channel."""
        announcement_message = await ctx.send(f"🎉 **{ctx.author.name} just pulled a super rare {card['name']} worth {card['price']} currency!** 🎉")
        await announcement_message.add_reaction("✨")
        await announcement_message.add_reaction("🎉")

    async def show_pack_opening(self, ctx, pack_name):
        """Simulate pack opening with a simple sequence."""
        pack_opening_images = [
            "https://media.discordapp.net/attachments/1277686502335447171/1278204323586637854/crate_fully_open.png?ex=66cff40a&is=66cea28a&hm=639c46900cda21e734d41393827b9085ef35dade5fa503ab3b90cf3194358b7f&=&format=webp&quality=lossless&width=422&height=364",
            "https://media.discordapp.net/attachments/1277686502335447171/1278204323800682599/crate_partially_open.png?ex=66cff40a&is=66cea28a&hm=7463c2b6ccf27f821d0a05ab857f80a5e83bb897b28758ff1ec90483afac074c&=&format=webp&quality=lossless&width=422&height=364",
            "https://media.discordapp.net/attachments/1277686502335447171/1278204323326857227/crate_closed.png?ex=66cff40a&is=66cea28a&hm=d132df7150d936f1c95443a64b1b989ea38b6d30923be2124b0e9ccfb75a5cd9&=&format=webp&quality=lossless&width=422&height=364"
        ]

        try:
            message = await ctx.send(embed=discord.Embed(title="Opening your pack..."))
            for image in pack_opening_images:
                embed = discord.Embed(title="Opening your pack...", color=discord.Color.blue())
                embed.set_image(url=image)
                await message.edit(embed=embed)
                await asyncio.sleep(0.5)  # Adjust timing for pack opening speed

            pack_image = self.packs[pack_name]["image"]
            embed = discord.Embed(title="Your pack is now open!", color=discord.Color.green())
            embed.set_image(url=pack_image)
            await message.edit(embed=embed)

        except discord.HTTPException as e:
            print(f"Discord HTTPException during pack opening: {e}")
        except Exception as e:
            print(f"Error in show_pack_opening: {e}")

    @commands.command(name='packs')
    async def view_packs(self, ctx):
        """View available packs in the store."""
        embed = discord.Embed(
            title="Available Packs",
            description="Here are the packs you can purchase:",
            color=discord.Color.blue()
        )

        for pack_name, pack_info in self.packs.items():
            embed.add_field(
                name=f"{pack_name.capitalize()} Pack",
                value=f"Price: {pack_info['price']} currency\nContains: {', '.join([card['name'] for card in pack_info['cards']])}",
                inline=False
            )
            embed.set_thumbnail(url=pack_info['image'])

        await ctx.send(embed=embed)

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(PackSystem(bot))
