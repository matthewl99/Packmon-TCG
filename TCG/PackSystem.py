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
        self.temporary_boosts = {}  # Store user-specific boosts

    packs = {
        "moonbreon": {
            "price": 200,
            "cards": [
                {"name": "Energy", "hit_percentage": 55, "price": 10, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686610288185354/energy.png?ex=66ce11e2&is=66ccc062&hm=088ac34ae3e9de494c94b75d45e3ba34feb18c3bde7409b7c8767336ef9542ea&=&format=webp&quality=lossless&width=281&height=394"},
                {"name": "Eevee", "hit_percentage": 42, "price": 20, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686626973253672/eevee.png?ex=66ce11e6&is=66ccc066&hm=8eae8212655a3fcea4f8e426d0e446e4176899501c7de982016e5757fe56507e&=&format=webp&quality=lossless&width=281&height=391"},
                {"name": "Umbreon V", "hit_percentage": 1, "price": 200, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686674335465644/UmbreonV1.png?ex=66ce11f1&is=66ccc071&hm=62d6b0b2b4aa33d1983a147c805f70a87f0fbb33b3d9d0974bf5966bcf18e996&=&format=webp&quality=lossless&width=281&height=391"},
                {"name": "Umbreon VMax", "hit_percentage": 0.2, "price": 500, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686754794541076/UmbreonVMAX0.2.png?ex=66ce1204&is=66ccc084&hm=6683428560fe68bd7c1ca93deef0d98f30ec24d31678bc328fd716b07277b5eb&=&format=webp&quality=lossless&width=281&height=391"},
                {"name": "Umbreon GX", "hit_percentage": 0.5, "price": 100, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686788793696296/UmbreonGX0.5.png?ex=66ce120c&is=66ccc08c&hm=7c2a00c8474654d1107ff7b9b4761136a0d4dcc931a54e5a3b9730df23d8a394&=&format=webp&quality=lossless&width=276&height=385"},
                {"name": "Umbreon GX", "hit_percentage": 0.15, "price": 150, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686817717485618/UmbreonGX0.15.png?ex=66ce1213&is=66ccc093&hm=d381f85a4a609896f5e9cbfe5585ed8bbb32eedb281351cb238d7726dd158537&=&format=webp&quality=lossless&width=281&height=392"},
                {"name": "Umbreon V", "hit_percentage": 0.15, "price": 150, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277688032526602464/UmbreonV0.15.png?ex=66ce1335&is=66ccc1b5&hm=86fb16d219c26689abcb848efe548d6925c6774943a624a8e16d5b5b680c9065&=&format=webp&quality=lossless&width=281&height=392"},
                {"name": "Umbreon V", "hit_percentage": 0.15, "price": 150, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686871836725330/UmbreonV0.15_4k.png?ex=66ce1220&is=66ccc0a0&hm=5214134d6b16c70c2ceeacf8931428731413927c11ed0ddb2da389e21f743d73&=&format=webp&quality=lossless&width=281&height=391"},
                {"name": "Umbreon VMAX", "hit_percentage": 0.1, "price": 300, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686909359095858/UmbreonVMAX0.1.png?ex=66ce1229&is=66ccc0a9&hm=5c7616ca23552983e99d71e9fc9f1b1b72871b9069ec6a214796ef5e762311a5&=&format=webp&quality=lossless&width=281&height=392"},
                {"name": "Umbreon VMAX", "hit_percentage": 0.02, "price": 1000, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686909359095858/UmbreonVMAX0.1.png?ex=66ce1229&is=66ccc0a9&hm=5c7616ca23552983e99d71e9fc9f1b1b72871b9069ec6a214796ef5e762311a5&=&format=webp&quality=lossless&width=281&height=392"},
                {"name": "Umbreon GX", "hit_percentage": 0.02, "price": 800, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686947397111908/UmbreonGX0.02.png?ex=66ce1232&is=66ccc0b2&hm=da5c4fb3ae559b27644f5af9079e70e93307c070877a6543e4a536de46633855&=&format=webp&quality=lossless&width=281&height=392"},
                {"name": "Umbreon VMAX", "hit_percentage": 0.01, "price": 1200, "image_url": "https://media.discordapp.net/attachments/1277686502335447171/1277686966577659915/MoonbreonVMAX0.001.png?ex=66ce1237&is=66ccc0b7&hm=a4de99911ef1ffef5e08207a8a76cf4f14314e62a2d1ec072c8e28d6ee15812d&=&format=webp&quality=lossless&width=281&height=391"}
            ],
            "image": "https://media.discordapp.net/attachments/1277686502335447171/1277686582773813339/Crate.png?ex=66ce11db&is=66ccc05b&hm=bbcb52f4c75f14960c0d8c727e8ea70f295e55b82eaef93c240e2207e10506fc&=&format=webp&quality=lossless&width=422&height=364"
        }
    }
    card_back_url = "https://media.discordapp.net/attachments/1277686502335447171/1277688692600737863/pokemoncard-back.png?ex=66ce13d2&is=66ccc252&hm=478eeec046e895cc547077436e85f575181e274d25e6215904dcd99118b86e6e&=&format=webp&quality=lossless&width=902&height=551"

    @commands.command(name='buypack')
    async def buy_pack(self, ctx, pack_name: str):
        """Buy a pack of cards."""
        if pack_name not in self.packs:
            await ctx.send(f"{ctx.author.mention}, that pack does not exist.")
            return

        pack_info = self.packs[pack_name]
        user_currency = await self.bot.get_cog("EconomySystem").get_currency(ctx.author.id)

        if user_currency >= pack_info["price"]:
            await self.bot.get_cog("EconomySystem").add_currency(ctx.author.id, -pack_info["price"])

            with get_db_connection() as db:
                with db.cursor() as cursor:
                    cursor.execute("INSERT INTO user_packs (user_id, pack_name, purchase_date) VALUES ((SELECT id FROM users WHERE discord_id = %s), %s, NOW())", (ctx.author.id, pack_name))
                    db.commit()

            await ctx.send(f"{ctx.author.mention}, you bought a {pack_name} pack for {pack_info['price']} currency! Use `!openpack {pack_name}` to open it.")
        else:
            await ctx.send(f"{ctx.author.mention}, you don't have enough currency to buy this pack.")

    @commands.command(name='openpack')
    async def open_pack(self, ctx, pack_name: str):
        """Open a purchased pack and receive a single card."""
        with get_db_connection() as db:
            with db.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM user_packs WHERE user_id = (SELECT id FROM users WHERE discord_id = %s) AND pack_name = %s", (ctx.author.id, pack_name))
                pack = cursor.fetchone()

                if not pack:
                    await ctx.send(f"{ctx.author.mention}, you don't have any {pack_name} packs to open.")
                    return

                pack_info = self.packs.get(pack_name)

                # Apply temporary boost if applicable
                if ctx.author.id in self.temporary_boosts:
                    card = self.draw_boosted_card(pack_info["cards"])
                    del self.temporary_boosts[ctx.author.id]  # Remove boost after use
                else:
                    card = self.draw_card(pack_info["cards"])

                # Save the card to the user's collection
                with db.cursor() as cursor:
                    self.save_card_to_collection(ctx.author.id, card, pack_name, cursor)
                    db.commit()

                # Delete the opened pack
                with db.cursor() as cursor:
                    cursor.execute("DELETE FROM user_packs WHERE id = %s", (pack["id"],))
                    db.commit()

        # Show the pack with a button to open it
        await self.show_pack_opening(ctx, card, pack_name)

    def draw_card(self, cards):
        """Draw a single card from the pack based on hit percentage."""
        return random.choices(cards, weights=[card['hit_percentage'] for card in cards], k=1)[0]

    def draw_boosted_card(self, cards):
        """Draw a single card with increased odds for rare cards."""
        adjusted_weights = [
            max(1, int(card['hit_percentage'] * 2)) if card['hit_percentage'] < 10 else card['hit_percentage']
            for card in cards
        ]
        return random.choices(cards, weights=adjusted_weights, k=1)[0]

    def save_card_to_collection(self, user_id, card, pack_name, cursor):
        """Save the card to the user's collection in the cards table."""
        cursor.execute("""
            INSERT INTO cards (owner_id, card_name, image_url, set_name, market_price)
            VALUES ((SELECT id FROM users WHERE discord_id = %s), %s, %s, %s, %s)
        """, (user_id, card['name'], card['image_url'], pack_name, card['price']))

    async def show_pack_opening(self, ctx, card, pack_name):
        """Simulate pack opening with a button to reveal the card."""
        pack_image = self.packs[pack_name]["image"]
        embed = discord.Embed(title="Your pack is ready to be opened!", color=discord.Color.green())
        embed.set_image(url=pack_image)
        message = await ctx.send(embed=embed)

        # Add a button for the user to reveal the card
        button = Button(label="Open Pack", style=discord.ButtonStyle.primary)

        async def button_callback(interaction):
            if interaction.user == ctx.author:
                # Show the back of the card first
                embed.title = "Revealing your card..."
                embed.set_image(url=self.card_back_url)
                await interaction.response.edit_message(embed=embed, view=None)
                await asyncio.sleep(2)

                # If the card is rare, play the special animation
                if card['hit_percentage'] <= 10:
                    await ctx.send(file=discord.File("C:/Users/AZA Custom Builds/Documents/GitHub/Packmon/rare_glow_sparkle_animation.mp4"))
                    await asyncio.sleep(2)

                # Reveal the actual card
                embed.title = f"🌟 {card['name']} 🌟"
                embed.description = f"Hit Percentage: {card['hit_percentage']}%\nValue: {card['price']} currency"
                embed.set_image(url=card['image_url'])
                await interaction.edit_original_response(embed=embed)
                await self.announce_rare_card(ctx, card)
            else:
                await interaction.response.send_message("This is not your pack to open!", ephemeral=True)

        button.callback = button_callback

        view = View()
        view.add_item(button)
        await message.edit(view=view)

    async def announce_rare_card(self, ctx, card):
        """Announce a rare card pull in the channel."""
        announcement_message = await ctx.send(f"🎉 **{ctx.author.name} just pulled a super rare {card['name']}!** 🎉")
        await announcement_message.add_reaction("✨")
        await announcement_message.add_reaction("🎉")

    @commands.command(name='boostodds')
    @commands.has_permissions(administrator=True)
    async def boost_odds(self, ctx, user: discord.Member):
        """Temporarily boost a user's odds for drawing a rare card (Admin only)."""
        self.temporary_boosts[user.id] = True
        await ctx.send(f"{user.mention}'s odds of pulling a rare card have been temporarily boosted!")

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(PackSystem(bot))
