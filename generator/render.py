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


def _to_palette_rgba(img: Image.Image) -> Image.Image:
    """Converte RGBA → P (255 cores + índice 255 = transparente) para GIF.

    Quantiza o RGB em 255 cores e usa o índice 255 como canal de transparência
    (pixels com alpha < 128 viram transparentes).
    """
    rgb = img.convert("RGB")
    pal = rgb.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    mask = img.getchannel("A").point(lambda a: 255 if a < 128 else 0)
    pal.paste(255, (0, 0, pal.width, pal.height), mask)
    pal.info["transparency"] = 255
    return pal


def save_gif(frames: list[Image.Image], output: str, fps: int, preview: bool,
             optimize: bool = True) -> None:
    if not frames:
        raise SystemExit("Nenhum frame gerado.")
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    if preview:
        frames[0].save(output.replace(".gif", ".png"))

    transparent = frames[0].mode == "RGBA"
    if transparent:
        frames = [_to_palette_rgba(f) for f in frames]
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


def save_gif_fixed(frames: list[Image.Image], output: str, fps: int,
                   preview: bool) -> None:
    """GIF transparente com paleta global fixa.

    Quantizar cada frame independente corrompe as cores quando a cor dominante
    muda entre frames (o índice da paleta global é reutilizado). Aqui coletamos
    todas as cores opacas de uma vez, montamos UMA paleta (índice 255 =
    transparente) e mapeamos todos os frames contra ela.
    """
    if not frames:
        raise SystemExit("Nenhum frame gerado.")
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    if preview:
        frames[0].save(output.replace(".gif", ".png"))

    colors: set = set()
    for f in frames:
        found = f.convert("RGB").getcolors(1000000)
        if found is not None:
            colors.update(c for _, c in found)
        else:
            colors.update(p for p in f.convert("RGB").get_flattened_data())

    if len(colors) > 254:
        return save_gif(frames, output, fps, preview, optimize=False)

    pal = [0] * 768
    for i, (r, g, b) in enumerate(sorted(colors)):
        pal[i * 3:i * 3 + 3] = (r, g, b)
    pal_img = Image.new("P", (1, 1))
    pal_img.putpalette(pal)

    w, h = frames[0].size
    out = []
    for f in frames:
        q = f.convert("RGB").quantize(palette=pal_img, dither=Image.Dither.NONE)
        mask = f.getchannel("A").point(lambda a: 255 if a < 128 else 0)
        q.paste(255, (0, 0, w, h), mask)
        q.info["transparency"] = 255
        out.append(q)

    out[0].save(output, save_all=True, append_images=out[1:],
                duration=[f.info.get("duration", 1000 // fps) for f in out],
                loop=0, optimize=False, disposal=2, transparency=255)
