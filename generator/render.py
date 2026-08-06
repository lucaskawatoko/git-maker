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


def _to_palette_rgba(img: Image.Image, colors: int) -> Image.Image:
    """Converte RGBA → P (`colors` cores + índice 255 = transparente) para GIF.

    Quantiza o RGB em `colors` cores e usa o índice 255 como canal de
    transparência (pixels com alpha < 128 viram transparentes).
    """
    rgb = img.convert("RGB")
    pal = rgb.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    mask = img.getchannel("A").point(lambda a: 255 if a < 128 else 0)
    pal.paste(255, (0, 0, pal.width, pal.height), mask)
    pal.info["transparency"] = 255
    return pal


def save_gif(frames: list[Image.Image], output: str, fps: int, preview: bool,
             optimize: bool = True, colors: int = 255) -> None:
    if not frames:
        raise SystemExit("Nenhum frame gerado.")
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    if preview:
        png = output if output.endswith(".png") else output.replace(".gif", ".png")
        frames[0].save(png)
        if output.endswith(".png"):
            return

    transparent = frames[0].mode == "RGBA"
    if transparent:
        frames = [_to_palette_rgba(f, colors) for f in frames]
        transparency = frames[0].info.get("transparency")
    else:
        transparency = None

    save_kwargs = dict(
        save_all=True,
        append_images=frames[1:],
        duration=1000 // fps,
        loop=0,
        optimize=optimize,
        disposal=2,
    )
    if transparency is not None:
        save_kwargs["transparency"] = transparency
    frames[0].save(output, **save_kwargs)
