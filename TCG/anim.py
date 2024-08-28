from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import os

# Load the base crate image
crate_image_path = "https://media.discordapp.net/attachments/1277686502335447171/1277686582773813339/Crate.png"  # Update with the path to your crate image
crate = Image.open(crate_image_path)

# Create a directory to save the generated images
output_dir = "crate_opening_sequence"
os.makedirs(output_dir, exist_ok=True)

# Create variations of the crate image
# Step 1: The crate closed (original image)
crate_closed = crate.copy()
crate_closed.save(os.path.join(output_dir, "crate_closed.png"))

# Step 2: Slightly open the crate (simulate by adding a small light glow)
def add_glow(image, intensity=1.0):
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(intensity)
    return image

crate_partially_open = crate.copy()
glow = Image.new("RGBA", crate.size, (255, 255, 0, 0))  # Light yellow glow
glow = add_glow(glow, intensity=2.0)
crate_partially_open = Image.blend(crate_partially_open, glow, alpha=0.3)
crate_partially_open.save(os.path.join(output_dir, "crate_partially_open.png"))

# Step 3: Fully open crate (increase the glow intensity)
crate_fully_open = crate.copy()
glow = Image.new("RGBA", crate.size, (255, 255, 0, 0))  # Brighter glow
glow = add_glow(glow, intensity=3.0)
crate_fully_open = Image.blend(crate_fully_open, glow, alpha=0.6)
crate_fully_open.save(os.path.join(output_dir, "crate_fully_open.png"))

print("Crate opening sequence images generated successfully!")