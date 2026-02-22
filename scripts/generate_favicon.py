"""Generate favicon files from the Acoruss logo."""

from PIL import Image
import os

src = os.path.join(os.path.dirname(__file__), "..", "src", "static", "images", "logos", "dark-rounded-bg.png")
out_dir = os.path.join(os.path.dirname(__file__), "..", "src", "static", "images")

img = Image.open(src)

# Generate favicon.ico (multi-size)
sizes = [(16, 16), (32, 32), (48, 48)]
icons = []
for size in sizes:
    icon = img.copy()
    icon.thumbnail(size, Image.LANCZOS)
    icons.append(icon)
icons[0].save(
    os.path.join(out_dir, "favicon.ico"),
    format="ICO",
    sizes=[(s.width, s.height) for s in icons],
    append_images=icons[1:],
)

# Generate apple-touch-icon (180x180)
apple = img.copy()
apple.thumbnail((180, 180), Image.LANCZOS)
apple.save(os.path.join(out_dir, "apple-touch-icon.png"), format="PNG")

# Generate favicon-32x32.png
f32 = img.copy()
f32.thumbnail((32, 32), Image.LANCZOS)
f32.save(os.path.join(out_dir, "favicon-32x32.png"), format="PNG")

# Generate favicon-16x16.png
f16 = img.copy()
f16.thumbnail((16, 16), Image.LANCZOS)
f16.save(os.path.join(out_dir, "favicon-16x16.png"), format="PNG")

print("Favicons generated successfully")
