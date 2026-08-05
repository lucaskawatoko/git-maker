from __future__ import annotations

import math

from PIL import Image, ImageDraw

from .render import FPS, load_font, save_gif_fixed

RAMP = " .:-=+*#%@"  # escuro → claro
DEFAULT_INK = (87, 96, 106, 255)  # #57606a (GitHub muted): legível em temas claro/escuro
PAD = 12
FONT_SIZE = 12
PRINT_SECONDS = 9.0
HOLD_SECONDS = 1.5


def _luminance(px: tuple) -> float:
    return 0.299 * px[0] + 0.587 * px[1] + 0.114 * px[2]


def _char_for(lum: float, lo: float, hi: float) -> str:
    t = (lum - lo) / (hi - lo) if hi > lo else 0.5
    idx = round(t * (len(RAMP) - 1))
    return RAMP[max(0, min(len(RAMP) - 1, idx))]


def mock_avatar(size: int = 200) -> Image.Image:
    """Gradiente sintético para testar/pré-visualizar sem rede."""
    img = Image.new("L", (size, size), 0)
    pix = img.load()
    for y in range(size):
        for x in range(size):
            pix[x, y] = int(255 * (x + y) / (2 * size))
    return img.convert("RGBA")


def to_grid(avatar: Image.Image, cols: int, char_w: float, char_h: float,
            crop: float = 0.9, bg_frac: float = 0.10) -> list[str]:
    """Converte a imagem em grade de caracteres, mantendo a proporção visual.

    Fotos de avatar costumam ter a figura escura no centro sobre fundo
    cinza-médio — o pior caso para uma rampa escuro→claro (o fundo vira ruído
    e a figura some com tinta clara). Então: cortamos as bordas (crop),
    estimamos o fundo pela borda da grade (mediana) e detectamos a polaridade
    (se o centro é mais escuro que o fundo, invertemos para a figura virar
    tinta pesada). Pixels próximos do fundo viram espaço (fundo transparente).
    """
    if crop and 0 < crop < 1:
        w, h = avatar.size
        s = int(min(w, h) * crop)
        left, top = (w - s) // 2, (h - s) // 2
        avatar = avatar.crop((left, top, left + s, top + s))

    rows = max(2, round(cols * char_w / char_h))
    img = avatar.resize((cols, rows), Image.LANCZOS).convert("RGB")
    pix = img.load()
    V = [[_luminance(pix[x, y]) for x in range(cols)] for y in range(rows)]

    b = max(2, rows // 8)
    border = [V[y][x] for y in range(rows) for x in range(cols)
              if y < b or y >= rows - b or x < 2 or x >= cols - 2]
    bg = sorted(border)[len(border) // 2]
    center = [V[y][x] for y in range(rows // 4, 3 * rows // 4)
              for x in range(cols // 4, 3 * cols // 4)]
    invert = sum(center) / len(center) < bg

    lo = min(min(r) for r in V)
    hi = max(max(r) for r in V)
    span = hi - lo or 1
    bg_dev = max(12.0, bg_frac * span)
    lo2, hi2 = (255 - hi, 255 - lo) if invert else (lo, hi)

    lines = []
    for y in range(rows):
        row = []
        for x in range(cols):
            v = V[y][x]
            if abs(v - bg) < bg_dev:
                row.append(" ")
            else:
                vv = 255 - v if invert else v
                row.append(_char_for(vv, lo2, hi2))
        lines.append("".join(row))
    return lines


def _compose(W: int, H: int, pad: int, char_w: float, char_h: int,
             row_imgs: list[Image.Image], cols: int, revealed: int) -> Image.Image:
    frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for r, strip in enumerate(row_imgs):
        start = r * cols
        if revealed <= start:
            break
        x = pad
        y = pad + r * char_h
        if revealed >= start + cols:
            frame.paste(strip, (x, y), strip)
        else:
            w = int((revealed - start) * char_w)
            region = strip.crop((0, 0, w, char_h))
            frame.paste(region, (x, y), region)
    return frame


def render_ascii(avatar: Image.Image, output: str, cols: int = 56,
                 ink: tuple = DEFAULT_INK, fps: int = FPS,
                 preview: bool = False) -> None:
    font = load_font(FONT_SIZE)
    ascent = font.getmetrics()[0]
    probe = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    char_w = probe.textlength("M", font=font)
    char_h = ascent
    grid = to_grid(avatar, cols, char_w, char_h)
    rows = len(grid)

    W = int(cols * char_w) + 2 * PAD
    H = rows * char_h + 2 * PAD

    row_imgs = []
    for row in grid:
        strip = Image.new("RGBA", (int(cols * char_w), char_h), (0, 0, 0, 0))
        ImageDraw.Draw(strip).text((0, 0), row, font=font, fill=ink)
        row_imgs.append(strip)

    total = cols * rows
    frames_print = int(fps * PRINT_SECONDS)
    cpf = max(1, total // frames_print)
    n_print = math.ceil(total / cpf)

    frames = []
    for k in range(n_print):
        revealed = min(total, (k + 1) * cpf)
        frames.append(_compose(W, H, PAD, char_w, char_h, row_imgs, cols, revealed))

    # último frame = foto completa; o hold é dado pela duration maior (sem
    # frames duplicados, que o Pillow mescla e corrompe no GIF transparente)
    frames[-1].info["duration"] = int(1000 * HOLD_SECONDS) + 1000 // fps

    save_gif_fixed(frames, output, fps, preview)
