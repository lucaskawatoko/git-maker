from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

FPS = 24


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/dejavu/DejaVuSansMono-Bold.ttf",
    )
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def save_gif(frames: list[Image.Image], output: str, fps: int, preview: bool) -> None:
    if not frames:
        raise SystemExit("Nenhum frame gerado.")
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    if preview:
        frames[0].save(output.replace(".gif", ".png"))
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=1000 // fps,
        loop=0,
        optimize=True,
        disposal=2,
    )
