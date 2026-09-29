from __future__ import annotations

import math

from PIL import Image, ImageDraw

from . import ascii_font
from .render import FPS, load_font, save_gif_fixed

CHAR = "▏"          # barrinha fina: traço contínuo e nítido
DEFAULT_INK = (201, 209, 217, 255)  # #c9d1d9 cinza claro: legível no tema escuro
DEFAULT_TEXT = "LUCAS KAWATOKO"
PAD = 20
FONT_SIZE = 12
PRINT_SECONDS = 6.0
HOLD_SECONDS = 1.5
SPACING = 1        # colunas vazias entre letras


def to_grid(text: str, pad_rows: int = 3) -> list[str]:
    """Monta o banner a partir da fonte ASCII 5×7 (`ascii_font`).

    Cada letra é um traço sólido desenhado à mão — não há rasterização, então
    as diagonais (A, W, K) não quebram. As letras de uma linha são separadas
    por `SPACING` colunas e as linhas de texto por `pad_rows` linhas vazias.
    """
    lines_text = [ln for ln in text.split("\n") if ln.strip()] or [text]
    rows: list[str | None] = []

    for i, ln in enumerate(lines_text):
        if i:
            rows.append(None)
        glyphs = [ascii_font.glyph(ch) for ch in ln]
        for y in range(ascii_font.HEIGHT):
            row = []
            for gi, g in enumerate(glyphs):
                if gi:
                    row.append(" " * SPACING)
                row.append("".join(CHAR if c == "1" else " " for c in g[y]))
            rows.append("".join(row))

    body = [r for r in rows if r is not None]
    width = max((len(r) for r in body), default=0)
    blank = " " * width
    out: list[str] = []
    for r in rows:
        if r is None:
            out.extend(blank for _ in range(pad_rows))
        else:
            out.append(r.ljust(width))
    return [blank] * pad_rows + out + [blank] * pad_rows


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


def render_ascii(text: str, output: str,
                 ink: tuple = DEFAULT_INK, fps: int = FPS,
                 preview: bool = False, pad_rows: int = 3) -> None:
    """Imprime `text` como banner ASCII, linha a linha, de cima para baixo."""
    font = load_font(FONT_SIZE)
    probe = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    char_w = float(probe.textlength(CHAR, font=font))
    char_h = max(1, probe.textbbox((0, 0), CHAR, font=font)[3] - 2)

    grid = to_grid(text, pad_rows=pad_rows)
    cols = max((len(r) for r in grid), default=1)
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

    frames[-1].info["duration"] = int(1000 * HOLD_SECONDS) + 1000 // fps

    save_gif_fixed(frames, output, fps, preview)
