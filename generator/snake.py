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

HUD_LABELS = {"repos": "REPOS", "commits": "CONTRIB", "followers": "SEGUIDORES"}
MAX_NAME = 14

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _in_bounds(cell: tuple[int, int]) -> bool:
    r, c = cell
    return PLAY_ROW0 <= r < ROWS and 0 <= c < COLS


def find_path(body: list[tuple[int, int]], goal: tuple[int, int]) -> list[tuple[int, int]] | None:
    head = body[0]
    if head == goal:
        return []
    occupied = set(body[:-1])  # a cauda sai na mesma jogada
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


def _fallback_move(body: list[tuple[int, int]]) -> tuple[int, int]:
    head = body[0]
    occupied = set(body[:-1])
    for dr, dc in DIRS:
        nxt = (head[0] + dr, head[1] + dc)
        if _in_bounds(nxt) and nxt not in occupied:
            return nxt
    return head


def _spawn_food(rng: random.Random, occupied: set) -> tuple[int, int]:
    for _ in range(500):
        cell = (rng.randrange(PLAY_ROW0, ROWS), rng.randrange(COLS))
        if cell not in occupied:
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
        path = find_path(body, goal)
        step = path[0] if path else _fallback_move(body)
        body.insert(0, step)
        if pending:
            pending -= 1
        else:
            body.pop()

        if step == goal:
            eaten += 1
            score += items[idx]["count"]
            idx += 1
            pending += 1  # cresce a cada comida
            stuck = 0
            if idx < len(items):
                food = _spawn_food(rng, set(body))
        else:
            stuck += 1
            if stuck >= MAX_STEPS:
                food = _spawn_food(rng, set(body))
                stuck = 0

        states.append(dict(body=list(body), food=food, idx=idx, eaten=eaten,
                           score=score, done=idx >= len(items)))

    if states[-1]["idx"] < len(items):
        states[-1]["done"] = True

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


def _cell_rect(cell: tuple[int, int]) -> tuple[int, int, int, int]:
    r, c = cell
    x = GRID_X + c * CELL + 1
    y = GRID_Y + r * CELL + 1
    return (x, y, x + CELL - 2, y + CELL - 2)


def _draw_food(draw: ImageDraw.ImageDraw, overlay: Image.Image, pal, food: tuple[int, int],
               name: str, font, avatar_img: Image.Image | None = None) -> None:
    r, c = food
    cx = GRID_X + c * CELL + CELL // 2
    cy = GRID_Y + r * CELL + CELL // 2
    half = 7
    if avatar_img is not None:
        d = 2 * half + 2
        x0, y0 = cx - d // 2, cy - d // 2
        img = avatar_img.resize((d, d), Image.LANCZOS)
        mask = Image.new("L", (d, d), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, d - 1, d - 1), fill=255)
        overlay.paste(img, (x0, y0), mask)
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
    draw.text((lx, ly), label, font=font, fill=pal["primary"] + (255,))


def _draw_snake(draw: ImageDraw.ImageDraw, overlay: Image.Image, pal,
                body: list[tuple[int, int]], avatar: Image.Image | None = None) -> None:
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
              score_font, big_font) -> None:
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
    sub = f"{label}: {state['eaten']}/{total}"
    if state["data_name"] == "commits":
        sub = f"{label}: {state['score']}"
    sub_w = draw.textlength(sub, font=score_font)
    x0b = GRID_X + COLS * CELL - 8 - sub_w - 2 * pad
    y0b = GRID_Y + 8
    draw.rounded_rectangle((x0b, y0b, GRID_X + COLS * CELL - 8, y0b + 28),
                           radius=8, outline=outline, width=1)
    draw.text((x0b + pad, y0b + 6), sub, font=score_font,
              fill=pal["primary"] + (255,))


def render(ctx: RenderContext) -> None:
    ctx.width, ctx.height = WIDTH, HEIGHT
    rng = random.Random(ctx.seed if ctx.seed is not None else random.randrange(2**31))
    items = ctx.items[:MAX_ITEMS] if ctx.items else ctx.items
    if not items:
        items = [{"name": "sem dados", "count": 0, "level": 1}]

    background = _build_background(ctx.palette)
    states = simulate(items, rng)
    TOTAL = len(states)

    font_s = load_font(13)
    font_l = load_font(20)
    frames = []

    for i, state in enumerate(states):
        state["data_name"] = ctx.data_name
        frame = background.copy()
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        current = items[state["idx"]] if state["idx"] < len(items) else None
        if current is not None and not state["done"]:
            avatar_img = ctx.avatars.get(current["name"])
            _draw_food(draw, overlay, ctx.palette, state["food"], current["name"],
                       font_s, avatar_img)
        _draw_snake(draw, overlay, ctx.palette, state["body"], ctx.avatar)
        _draw_hud(draw, ctx.palette, state, len(items), font_s, font_l)

        if state["done"] and i >= INTRO:
            msg = "CONCLUÍDO!"
            tw = draw.textlength(msg, font=font_l)
            draw.text(((WIDTH - tw) / 2, GRID_Y + 12), msg, font=font_l,
                      fill=ctx.palette["accent"] + (255,))

        frame = Image.alpha_composite(frame, overlay)
        frames.append(frame)

    save_gif(frames, ctx.output, ctx.fps, ctx.preview)
