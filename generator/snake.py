#!/usr/bin/env python3
"""Estilo Snake: a cobra (auto-play com BFS) percorre a arena comendo os
dados do usuário. Cada item é um alimento com seu nome; a pontuação soma o
`count` de cada item (estrelas, contribuições ou seguidores)."""

from __future__ import annotations

import random
from collections import deque

from PIL import Image, ImageDraw

from .render import load_font, save_gif
from .render_context import RenderContext

CELL = 25
COLS, ROWS = 24, 14
GRID_X, GRID_Y = 50, 46
WIDTH = COLS * CELL + 2 * GRID_X
HEIGHT = ROWS * CELL + GRID_Y + 34

PLAY_ROW0 = 3  # linhas 0-2 são a faixa do HUD; a cobra/comida só jogam a partir daqui

INTRO = 10
OUTRO = 6
FPS = 24
MAX_STEPS = 80
MAX_TOTAL = 900
MAX_ITEMS = 25  # limita a quantidade de alimentos para manter o GIF leve

SMOOTH = 2          # sub-frames por passo de simulação (movimento interpolado)
POPUP_FRAMES = 12   # vida do popup "+N" em sub-frames
MAX_RENDER_FRAMES = 1500  # teto de frames renderizados (proteção de memória)

HUD_LABELS = {"repos": "REPOS", "commits": "CONTRIB", "followers": "SEGUIDORES"}
MAX_NAME = 14

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _in_bounds(cell: tuple[int, int]) -> bool:
    r, c = cell
    return PLAY_ROW0 <= r < ROWS and 0 <= c < COLS


def find_path(body: list[tuple[int, int]], goal: tuple[int, int],
              growing: bool = False) -> list[tuple[int, int]] | None:
    head = body[0]
    if head == goal:
        return []
    # Enquanto a cobra está crescendo a cauda não sai na jogada: trata-a como
    # ocupada para não planejar caminho que atravesse a própria cauda parada.
    occupied = set(body) if growing else set(body[:-1])
    prev: dict[tuple[int, int], tuple[int, int]] = {}
    q = deque([head])
    seen = {head}
    while q:
        cur = q.popleft()
        for dr, dc in DIRS:
            nxt = (cur[0] + dr, cur[1] + dc)
            if nxt in seen or nxt in occupied or not _in_bounds(nxt):
                continue
            seen.add(nxt)
            prev[nxt] = cur
            if nxt == goal:
                path = []
                node = goal
                while node != head:
                    path.append(node)
                    node = prev[node]
                path.reverse()
                return path
            q.append(nxt)
    return None


def _fallback_move(body: list[tuple[int, int]],
                   growing: bool = False) -> tuple[int, int]:
    head = body[0]
    occupied = set(body) if growing else set(body[:-1])
    for dr, dc in DIRS:
        nxt = (head[0] + dr, head[1] + dc)
        if _in_bounds(nxt) and nxt not in occupied:
            return nxt
    return head


def _spawn_food(rng: random.Random, occupied: set,
                exclude: tuple[int, int] | None = None) -> tuple[int, int]:
    for _ in range(500):
        cell = (rng.randrange(PLAY_ROW0, ROWS), rng.randrange(COLS))
        if cell not in occupied and cell != exclude:
            return cell
    raise SystemExit("Sem espaço livre para a cobra.")


def simulate(items: list[dict], rng: random.Random) -> list[dict]:
    head = (7, 7)
    body = [(7, 7), (6, 7), (5, 7), (4, 7)]
    pending = 0
    idx = 0
    eaten = 0
    score = 0
    food = _spawn_food(rng, set(body))
    states = []

    for _ in range(INTRO):
        states.append(dict(body=list(body), food=food, idx=idx, eaten=eaten,
                           score=score, done=False))

    stuck = 0
    while idx < len(items) and len(states) < MAX_TOTAL:
        goal = food
        growing = pending > 0
        path = find_path(body, goal, growing)
        step = path[0] if path else _fallback_move(body, growing)
        body.insert(0, step)
        if pending:
            pending -= 1
        else:
            body.pop()

        gain = 0
        if step == goal:
            gain = items[idx]["count"]
            eaten += 1
            score += gain
            idx += 1
            pending += 1  # cresce a cada comida
            stuck = 0
            if idx < len(items):
                food = _spawn_food(rng, set(body), exclude=goal)
        else:
            stuck += 1
            if stuck >= MAX_STEPS:
                food = _spawn_food(rng, set(body), exclude=food)
                stuck = 0

        state = dict(body=list(body), food=food, idx=idx, eaten=eaten,
                     score=score, done=idx >= len(items))
        if gain:
            state["eat"] = {"gain": gain, "cell": goal}
        states.append(state)

    last = states[-1]
    last["done"] = True
    last["finished"] = last["idx"] >= len(items)

    for _ in range(OUTRO):
        states.append(states[-1])
    return states


def _build_background(pal) -> Image.Image:
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Apenas a borda da arena (fundo 100% transparente)
    x0, y0 = GRID_X - 8, GRID_Y - 8
    x1, y1 = GRID_X + COLS * CELL + 8, GRID_Y + ROWS * CELL + 8
    draw.rounded_rectangle((x0, y0, x1, y1), radius=12,
                           outline=(150, 160, 180, 255), width=1)
    return img


def _cell_rect(cell: tuple[float, float]) -> tuple[int, int, int, int]:
    r, c = cell
    x = GRID_X + c * CELL + 1
    y = GRID_Y + r * CELL + 1
    return (int(round(x)), int(round(y)),
            int(round(x + CELL - 2)), int(round(y + CELL - 2)))


def _interp_cell(a: tuple[float, float], b: tuple[float, float],
                 t: float) -> tuple[float, float]:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _interp_body(a: list[tuple[int, int]], b: list[tuple[int, int]],
                 t: float) -> list[tuple[float, float]]:
    """Interpola o corpo entre dois estados consecutivos.

    Cada segmento segue o da frente (`b[i] == a[i-1]`); quando a cobra cresce
    (ou encolhe de volta) a cauda extra é segurada/convergida para não "piscar".
    """
    n = min(len(a), len(b))
    out = [_interp_cell(a[i], b[i], t) for i in range(n)]
    if len(b) > len(a):
        out.append(b[-1])
    elif len(b) < len(a):
        tail = b[-1]
        for i in range(n, len(a)):
            out.append(_interp_cell(a[i], tail, t))
    return out


def _draw_food(draw: ImageDraw.ImageDraw, overlay: Image.Image, pal,
               food: tuple[float, float], name: str, font,
               avatar_img: Image.Image | None = None, level: int = 1) -> None:
    r, c = food
    cx = GRID_X + c * CELL + CELL // 2
    cy = GRID_Y + r * CELL + CELL // 2
    half = 6 + min(4, max(1, level))  # nível 1-4 escala o tamanho da comida
    if avatar_img is not None:
        d = 2 * half + 2
        x0, y0 = cx - d // 2, cy - d // 2
        img = avatar_img.resize((d, d), Image.LANCZOS)
        mask = Image.new("L", (d, d), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, d - 1, d - 1), fill=255)
        overlay.paste(img, (int(x0), int(y0)), mask)
        draw.ellipse((x0 - 1, y0 - 1, x0 + d, y0 + d),
                     outline=(255, 255, 255, 160), width=1)
    else:
        draw.ellipse((cx - half, cy - half, cx + half, cy + half),
                     fill=pal["warn"] + (255,), outline=(255, 255, 255, 180))
        draw.ellipse((cx - half + 2, cy - half + 2, cx - half + 5, cy - half + 5),
                     fill=(255, 255, 255, 220))

    label = name if len(name) <= MAX_NAME else name[: MAX_NAME - 1] + "…"
    tw = draw.textlength(label, font=font)
    lx = max(GRID_X + 2, min(cx - tw / 2, GRID_X + COLS * CELL - tw - 2))
    ly = max(GRID_Y - 16, min(cy - CELL, GRID_Y + ROWS * CELL - 16))
    draw.text((int(lx), int(ly)), label, font=font, fill=pal["primary"] + (255,))


def _draw_snake(draw: ImageDraw.ImageDraw, overlay: Image.Image, pal,
                body: list[tuple[float, float]],
                avatar: Image.Image | None = None) -> None:
    for i in range(len(body) - 1, 0, -1):
        draw.rounded_rectangle(_cell_rect(body[i]), radius=6,
                               fill=pal["primary"] + (255,))
    x, y, x2, y2 = _cell_rect(body[0])
    if avatar is not None:
        w = x2 - x + 1
        img = avatar.resize((w, w), Image.LANCZOS)
        mask = Image.new("L", (w, w), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, w - 1), radius=6, fill=255)
        overlay.paste(img, (x, y), mask)
    else:
        draw.rounded_rectangle(_cell_rect(body[0]), radius=6,
                               fill=pal["secondary"] + (255,))


def _draw_hud(draw: ImageDraw.ImageDraw, pal, state: dict, total: int,
              score_font, big_font, truncated: bool) -> None:
    pad = 10
    outline = (150, 160, 180, 255)

    score_label = "SCORE"
    score_number = f"{state['score']:04d}"
    box_w = max(draw.textlength(score_label, font=score_font),
                draw.textlength(score_number, font=big_font)) + 2 * pad
    x0, y0 = GRID_X + 8, GRID_Y + 8
    x1, y1 = x0 + box_w, y0 + 52
    draw.rounded_rectangle((x0, y0, x1, y1), radius=8, outline=outline, width=1)
    draw.text((x0 + pad, y0 + 6), score_label, font=score_font, fill=outline)
    draw.text((x0 + pad, y0 + 26), score_number, font=big_font,
              fill=pal["secondary"] + (255,))

    label = HUD_LABELS[state["data_name"]]
    if state["data_name"] == "commits":
        sub = f"{label}: {state['score']}"
    elif truncated:
        sub = f"TOP {MAX_ITEMS}: {state['eaten']}/{total}"
    else:
        sub = f"{label}: {state['eaten']}/{total}"
    sub_w = draw.textlength(sub, font=score_font)
    x0b = GRID_X + COLS * CELL - 8 - sub_w - 2 * pad
    y0b = GRID_Y + 8
    draw.rounded_rectangle((x0b, y0b, GRID_X + COLS * CELL - 8, y0b + 28),
                           radius=8, outline=outline, width=1)
    draw.text((x0b + pad, y0b + 6), sub, font=score_font,
              fill=pal["primary"] + (255,))

    # Barra de progresso: comidas comidas / total
    bar_w = 96
    bar_h = 6
    bx1 = GRID_X + COLS * CELL - 8
    bx0 = bx1 - bar_w
    by0 = y0b + 28 + 8
    frac = min(1.0, state["eaten"] / max(1, total))
    draw.rounded_rectangle((bx0, by0, bx1, by0 + bar_h), radius=3,
                           outline=outline, width=1)
    if frac > 0:
        fill_w = max(3, int((bar_w - 2) * frac))
        draw.rounded_rectangle((bx0 + 1, by0 + 1, bx0 + 1 + fill_w, by0 + bar_h - 1),
                               radius=2, fill=pal["primary"] + (255,))


def _draw_popups(draw: ImageDraw.ImageDraw, popups: list[dict], font, pal) -> None:
    for p in popups:
        age = p["age"]
        r, c = p["cell"]
        cx = GRID_X + c * CELL + CELL // 2
        cy = GRID_Y + r * CELL + CELL // 2
        t = min(1.0, age / POPUP_FRAMES)
        alpha = int(255 * (1 - t))
        radius = 8 + age * 3
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                     outline=pal["warn"][:3] + (alpha,), width=2)
        text = f"+{p['gain']}"
        tw = draw.textlength(text, font=font)
        draw.text((cx - tw / 2, cy - 16 - age * 2), text, font=font,
                  fill=pal["accent"][:3] + (alpha,))


def render(ctx: RenderContext) -> None:
    ctx.width, ctx.height = WIDTH, HEIGHT
    rng = random.Random(ctx.seed if ctx.seed is not None else random.randrange(2**31))
    items = ctx.items[:MAX_ITEMS] if ctx.items else ctx.items
    total_full = ctx.total_items if ctx.total_items is not None else len(items)
    truncated = total_full > MAX_ITEMS
    if not items:
        items = [{"name": "sem dados", "count": 0, "level": 1}]

    background = _build_background(ctx.palette)
    states = simulate(items, rng)
    for st in states:
        st["data_name"] = ctx.data_name
    steps = len(states) - 1
    if ctx.smooth:
        smooth = max(1, min(SMOOTH, MAX_RENDER_FRAMES // max(1, steps)))
    else:
        smooth = 1

    font_s = load_font(13)
    font_l = load_font(20)
    popups: list[dict] = []
    frames: list[Image.Image] = []

    for k in range(steps):
        a, b = states[k], states[k + 1]
        if b.get("eat"):
            popups.append({"age": 0, "gain": b["eat"]["gain"],
                           "cell": b["eat"]["cell"]})
        for s in range(smooth):
            t = s / smooth
            body = _interp_body(a["body"], b["body"], t)
            food = _interp_cell(a["food"], b["food"], t)

            frame = background.copy()
            overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            current = items[a["idx"]] if a["idx"] < len(items) else None
            if current is not None and not a["done"]:
                avatar_img = ctx.avatars.get(current["name"])
                lvl = 1 if ctx.data_name == "followers" else current.get("level", 1)
                _draw_food(draw, overlay, ctx.palette, food, current["name"],
                           font_s, avatar_img, lvl)
            _draw_snake(draw, overlay, ctx.palette, body, ctx.avatar)
            _draw_hud(draw, ctx.palette, a, len(items), font_s, font_l, truncated)
            _draw_popups(draw, popups, font_l, ctx.palette)

            if a.get("done"):
                msg = "CONCLUÍDO!" if a.get("finished") else "TEMPO LIMITE"
                tw = draw.textlength(msg, font=font_l)
                draw.text(((WIDTH - tw) / 2, GRID_Y + 12), msg, font=font_l,
                          fill=ctx.palette["accent"] + (255,))

            frame = Image.alpha_composite(frame, overlay)
            frames.append(frame)
            for p in popups:
                p["age"] += 1
        popups = [p for p in popups if p["age"] < POPUP_FRAMES]

    if not frames:  # fallback: nenhum estado (não deve acontecer)
        s0 = states[0]
        frame = background.copy()
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        _draw_snake(draw, overlay, ctx.palette, s0["body"], ctx.avatar)
        _draw_hud(draw, ctx.palette, s0, len(items), font_s, font_l, truncated)
        frames.append(Image.alpha_composite(frame, overlay))

    fps = ctx.fps * smooth
    save_gif(frames, ctx.output, fps, ctx.preview)
