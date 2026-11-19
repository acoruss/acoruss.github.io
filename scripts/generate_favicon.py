"""Generate square icons and a social preview from the supplied logo suite."""

from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "public" / "images"
BACKGROUND = "#1A1612"


def main() -> None:
    with Image.open(OUT_DIR / "logos" / "icon-brown.png") as source:
        mark = source.convert("RGBA")

    def square_icon(size: int) -> Image.Image:
        canvas = Image.new("RGBA", (size, size), BACKGROUND)
        fitted = ImageOps.contain(mark, (size * 3 // 4, size * 3 // 4), Image.Resampling.LANCZOS)
        canvas.alpha_composite(fitted, ((size - fitted.width) // 2, (size - fitted.height) // 2))
        return canvas

    square_icon(48).save(OUT_DIR / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    for size in (16, 32):
        square_icon(size).save(OUT_DIR / f"favicon-{size}x{size}.png", optimize=True)
    square_icon(180).convert("RGB").save(OUT_DIR / "apple-touch-icon.png", optimize=True)

    preview = Image.new("RGBA", (1200, 630), BACKGROUND)
    with Image.open(OUT_DIR / "logos" / "primary-light.png") as source:
        logo = ImageOps.contain(source.convert("RGBA"), (900, 300), Image.Resampling.LANCZOS)
    preview.alpha_composite(logo, ((preview.width - logo.width) // 2, (preview.height - logo.height) // 2))
    preview.convert("RGB").save(OUT_DIR / "social-preview.png", optimize=True)


if __name__ == "__main__":
    main()
