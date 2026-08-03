from __future__ import annotations

"""Estilo Snake: a cobra (auto-play com BFS) percorre a arena comendo os
dados do usuário. Cada item é um alimento com seu nome; a pontuação soma o
`count` de cada item (estrelas, contribuições ou seguidores). Com o flag
`avatar`, a cabeça da cobra vira o avatar do usuário."""

import random
from collections import deque

from PIL import Image, ImageDraw

from ..render import circular_crop, load_font, save_gif
from ..render_context import RenderContext
from . import register

CELL = 25
COLS, ROWS = 24, 14
GRID_X, GRID_Y = 50, 46
WIDTH = COLS * CELL + 2 * GRID_X
HEIGHT = ROWS * CELL + GRID_Y + 34

INTRO = 22
OUTRO = 14
FPS = 24
MAX_STEPS = 80
MAX_TOTAL = 900

TITLES = {
    "repos": "ASTRO SNAKE",
    "commits": "ASTRO SNAKE",
    "followers": "ASTRO SNAKE",
}
SUBTITLES = {
    "repos": "seus repositórios viraram comida!",
    "commits": "suas contribuições viraram comida!",
    "followers": "seus seguidores viraram comida!",
}
HUD_LABELS = {"repos": "REPOS", "commits": "CONTRIB", "followers": "FOLLOWERS"}
MAX_NAME = 14

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _in_bounds(cell: tuple[int, int]) -> bool:
    r, c = cell
    return 0 <= r < ROWS and 0 <= c < COLS


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
        cell = (rng.randrange(ROWS), rng.randrange(COLS))
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
    rng = random.Random(3)
    img = Image.new("RGBA", (WIDTH, HEIGHT), pal["bg"] + (255,))
    draw = ImageDraw.Draw(img)
    for x in range(GRID_X, GRID_X + COLS * CELL + 1, CELL):
        draw.line([(x, GRID_Y), (x, GRID_Y + ROWS * CELL)], fill=pal["grid"] + (70,))
    for y in range(GRID_Y, GRID_Y + ROWS * CELL + 1, CELL):
        draw.line([(GRID_X, y), (GRID_X + COLS * CELL, y)], fill=pal["grid"] + (70,))
    for _ in range(70):
        x = rng.randint(0, WIDTH - 1)
        y = rng.randint(0, GRID_Y - 5)
        img.putpixel((x, y), pal["star"] + (rng.randint(40, 140),))
    return img


def _cell_rect(cell: tuple[int, int]) -> tuple[int, int, int, int]:
    r, c = cell
    x = GRID_X + c * CELL + 1
    y = GRID_Y + r * CELL + 1
    return (x, y, x + CELL - 2, y + CELL - 2)


def _draw_food(draw: ImageDraw.ImageDraw, pal, food: tuple[int, int],
               name: str, font) -> None:
    r, c = food
    cx = GRID_X + c * CELL + CELL // 2
    cy = GRID_Y + r * CELL + CELL // 2
    half = 7
    draw.ellipse((cx - half, cy - half, cx + half, cy + half),
                 fill=pal["warn"] + (255,), outline=(255, 255, 255, 180))
    draw.ellipse((cx - half + 2, cy - half + 2, cx - half + 5, cy - half + 5),
                 fill=(255, 255, 255, 220))

    label = name if len(name) <= MAX_NAME else name[: MAX_NAME - 1] + "…"
    tw = draw.textlength(label, font=font)
    lx = max(GRID_X + 2, min(cx - tw / 2, GRID_X + COLS * CELL - tw - 2))
    ly = max(GRID_Y - 16, min(cy - CELL, GRID_Y + ROWS * CELL - 16))
    draw.text((lx, ly), label, font=font, fill=pal["primary"] + (255,))


def _draw_snake(draw: ImageDraw.ImageDraw, overlay: Image.Image, pal, body: list[tuple[int, int]],
                avatar: Image.Image | None) -> None:
    for i in range(len(body) - 1, 0, -1):
        draw.rounded_rectangle(_cell_rect(body[i]), radius=6,
                               fill=pal["primary"] + (230,))
    head = body[0]
    if avatar is not None:
        r, c = head
        cx = GRID_X + c * CELL + CELL // 2
        cy = GRID_Y + r * CELL + CELL // 2
        d = CELL - 4
        half = d // 2
        draw.ellipse((cx - half, cy - half, cx + half, cy + half),
                     outline=(255, 255, 255, 200), width=1)
        av = circular_crop(avatar, d)
        overlay.paste(av, (int(cx - half), int(cy - half)), av)
    else:
        draw.rounded_rectangle(_cell_rect(head), radius=6,
                               fill=pal["secondary"] + (255,))


def _draw_hud(draw: ImageDraw.ImageDraw, pal, state: dict, total: int,
              score_font, big_font) -> None:
    data_name = state["data_name"]
    draw.text((24, 14), "SCORE", font=score_font, fill=(150, 160, 180, 255))
    draw.text((24, 34), f"{state['score']:04d}", font=big_font,
              fill=pal["secondary"] + (255,))
    label = HUD_LABELS[data_name]
    sub = f"{label}: {state['eaten']}/{total}"
    if data_name == "commits":
        sub = f"{label}: {state['score']}"
    tw = draw.textlength(sub, font=score_font)
    draw.text((WIDTH - 24 - tw, 14), sub, font=score_font,
              fill=pal["primary"] + (255,))


def _draw_intro(draw: ImageDraw.ImageDraw, pal, i: int, data_name: str,
                font_s, font_l) -> None:
    if i >= INTRO:
        return
    title = TITLES[data_name]
    tw = draw.textlength(title, font=font_l)
    draw.text(((WIDTH - tw) / 2, 10), title, font=font_l, fill=pal["accent"] + (255,))
    sub = SUBTITLES[data_name]
    sw = draw.textlength(sub, font=font_s)
    draw.text(((WIDTH - sw) / 2, 36), sub, font=font_s, fill=pal["primary"] + (200,))


@register("snake")
def render(ctx: RenderContext) -> None:
    ctx.width, ctx.height = WIDTH, HEIGHT
    rng = random.Random(3)
    items = ctx.items or [{"name": "sem dados", "count": 0, "level": 1}]

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
            _draw_food(draw, ctx.palette, state["food"], current["name"], font_s)
        _draw_snake(draw, overlay, ctx.palette, state["body"], ctx.avatar)
        _draw_hud(draw, ctx.palette, state, len(items), font_s, font_l)
        _draw_intro(draw, ctx.palette, i, ctx.data_name, font_s, font_l)

        if state["done"] and i >= INTRO:
            msg = "CONCLUÍDO!"
            tw = draw.textlength(msg, font=font_l)
            draw.text(((WIDTH - tw) / 2, HEIGHT - 30), msg, font=font_l,
                      fill=ctx.palette["accent"] + (255,))

        frame = Image.alpha_composite(frame, overlay).convert("RGB")

        if i >= TOTAL - OUTRO:
            t = (i - (TOTAL - OUTRO)) / OUTRO
            black = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
            frame = Image.blend(frame, black, min(1.0, t * 1.05))

        frames.append(frame)

    save_gif(frames, ctx.output, ctx.fps, ctx.preview)
