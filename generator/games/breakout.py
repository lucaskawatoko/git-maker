#!/usr/bin/env python3
"""Estilo Breakout: a bolinha quebra os blocos (um por dado do usuário),
a raquete é auto-play e cada bloco solta seu `count` no SCORE. A bolinha é
"rebatida" pela raquete com pontaria na próxima peça — determinístico e
sempre termina `CONCLUÍDO!`."""

from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw, ImageFilter

from ..render import load_font, save_gif
from ..render_context import RenderContext
from ..snake import (GRID_X, GRID_Y, HEIGHT, MAX_ITEMS, WIDTH, _draw_hud)

CELL = 25
PLAY_X0, PLAY_X1 = GRID_X, WIDTH - GRID_X

BRICK_COLS = 5
BRICK_ROWS = 5
BRICK_GAP = 12
BRICK_H = 20
BRICK_TOP = GRID_Y + 74
ROW_PITCH = BRICK_H + 12

PADDLE_W = 90
PADDLE_H = 12
PADDLE_TOP = HEIGHT - 46

BALL_R = 7
SPEED = 22.0  # pixels por passo de simulação

TRAIL = 6      # quantos pontos de rastro a bolinha deixa
TRAIL_ALPHA = 90

INTRO = 10
OUTRO = 8
MAX_STEPS = 1400

SMOOTH = 2
ANIM_FRAMES = 14
MAX_RENDER_FRAMES = 600

# Cor de destaque por linha de blocos (topo → base): dá um degradê "arcade".
ROW_HUES = (
    (255, 92, 92),    # vermelho
    (255, 159, 64),   # laranja
    (255, 214, 89),   # amarelo
    (110, 231, 183),  # verde-água
    (129, 161, 255),  # azul
)


def _brick_rect(i: int) -> tuple[int, int, int, int]:
    col = i % BRICK_COLS
    row = i // BRICK_COLS
    bw = (PLAY_X1 - PLAY_X0 - (BRICK_COLS - 1) * BRICK_GAP) // BRICK_COLS
    x0 = PLAY_X0 + col * (bw + BRICK_GAP)
    y0 = BRICK_TOP + row * ROW_PITCH
    return (x0, y0, x0 + bw, y0 + BRICK_H)


def _build_bricks(items: list[dict]) -> list[dict]:
    bricks: list[dict] = []
    for i, item in enumerate(items):
        x0, y0, x1, y1 = _brick_rect(i)
        bricks.append({
            "name": item["name"],
            "count": item["count"],
            "level": item.get("level", 1),
            "row": (i // BRICK_COLS) % len(ROW_HUES),
            "rect": (x0, y0, x1, y1),
            "alive": True,
        })
    return bricks


def _aim(ball: tuple[float, float], bricks: list[dict],
         rng: random.Random) -> tuple[float, float]:
    """Pontaria reflexiva: mira no centro do próximo bloco vivo e calcula o
    `vx` cuja reflexão nas paredes atinge o alvo quando a bolinha chega à
    altura dele. `vy` é fixo (para cima). Variedade: entre os dois menores
    `|vx|` possíveis, escolhe com a semente."""
    x, y = ball
    target = next(b for b in bricks if b["alive"])
    bx0, by0, bx1, by1 = target["rect"]
    tx = (bx0 + bx1) / 2
    ty = (by0 + by1) / 2
    if ty >= y:
        ty = BRICK_TOP
    w = PLAY_X1 - PLAY_X0
    t = max(1.0, (y - ty) / SPEED)
    rel = x - PLAY_X0
    targ = tx - PLAY_X0
    cands: list[float] = []
    for k in range(-2, 3):
        cands.append(k * 2 * w + targ - rel)
        cands.append(k * 2 * w - targ - rel)
    cands.sort(key=abs)
    d = cands[0]
    if len(cands) > 1 and abs(cands[1]) < abs(d) * 1.3 and rng.random() < 0.5:
        d = cands[1]
    vx = d / t
    # Pequeno ruído no ângulo: caminhos diferentes por semente (sempre consome rng).
    vx += (rng.random() - 0.5) * 3.0
    return vx, -SPEED


def _hit_brick(b: dict, x: float, y: float) -> bool:
    bx0, by0, bx1, by1 = b["rect"]
    cx = min(max(x, bx0), bx1)
    cy = min(max(y, by0), by1)
    dx, dy = x - cx, y - cy
    return dx * dx + dy * dy <= BALL_R * BALL_R


def simulate(items: list[dict], rng: random.Random) -> list[dict]:
    bricks = _build_bricks(items)
    x = (PLAY_X0 + PLAY_X1) / 2
    ball = (x, PADDLE_TOP - BALL_R - 2)
    vx, vy = 0.0, 0.0
    idx = 0
    eaten = 0
    score = 0
    trail: list[tuple[float, float]] = []

    def make(done: bool = False) -> dict:
        return dict(ball=ball, v=(vx, vy), paddle_x=x, bricks=[dict(b) for b in bricks],
                    idx=idx, eaten=eaten, score=score, done=done, finished=False,
                    events=[], trail=list(trail))

    states = [make() for _ in range(INTRO)]

    def advance() -> list[dict]:
        nonlocal ball, vx, vy, x, idx, eaten, score, trail
        bx, by = ball
        bx += vx
        by += vy
        events: list[dict] = []
        if bx - BALL_R < PLAY_X0:
            bx, vx = PLAY_X0 + BALL_R, abs(vx)
        elif bx + BALL_R > PLAY_X1:
            bx, vx = PLAY_X1 - BALL_R, -abs(vx)
        if by - BALL_R < BRICK_TOP:
            by, vy = BRICK_TOP + BALL_R, abs(vy)
        for b in bricks:
            if not b["alive"] or not _hit_brick(b, bx, by):
                continue
            b["alive"] = False
            events.append({"gain": b["count"], "rect": b["rect"], "name": b["name"],
                           "row": b["row"]})
            eaten += 1
            score += b["count"]
            bx0, by0, bx1, by1 = b["rect"]
            cx = min(max(bx, bx0), bx1)
            cy = min(max(by, by0), by1)
            dx, dy = bx - cx, by - cy
            if abs(dx) >= abs(dy):
                vy = -vy
            else:
                vx = -vx
            break
        if by + BALL_R >= PADDLE_TOP:
            by = PADDLE_TOP - BALL_R - 1
            bx = min(max(bx, PLAY_X0 + BALL_R), PLAY_X1 - BALL_R)
            if any(b["alive"] for b in bricks):
                vx, vy = _aim((bx, by), bricks, rng)
            else:
                vx = vy = 0.0
        ball = (bx, by)
        trail.append(ball)
        if len(trail) > TRAIL:
            trail.pop(0)
        x = min(max(bx, PLAY_X0 + PADDLE_W / 2), PLAY_X1 - PADDLE_W / 2)
        return events

    if any(b["alive"] for b in bricks):
        vx, vy = _aim(ball, bricks, rng)
    while any(b["alive"] for b in bricks) and len(states) < MAX_STEPS:
        events = advance()
        state = make()
        state["events"] = events
        states.append(state)

    last = states[-1]
    last["done"] = True
    last["finished"] = not any(b["alive"] for b in bricks)
    for _ in range(OUTRO):
        st = dict(last)
        st["events"] = []
        states.append(st)
    return states


def _build_background(pal) -> Image.Image:
    """Arena com moldura suave e grade pontilhada sutil no fundo."""
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    x0, y0 = GRID_X - 8, GRID_Y - 8
    x1, y1 = GRID_X + BRICK_COLS * 112 + (BRICK_COLS - 1) * BRICK_GAP + 8, HEIGHT - 8
    draw.rounded_rectangle((x0, y0, x1, y1), radius=12,
                           outline=(150, 160, 180, 90), width=1)
    # Grade sutil: pontos a cada célula dão profundidade sem poluir.
    dot = (150, 160, 180, 26)
    for gx in range(GRID_X + CELL // 2, WIDTH - GRID_X, CELL):
        for gy in range(GRID_Y + CELL // 2, HEIGHT - GRID_Y, CELL):
            draw.point((gx, gy), fill=dot)
    return img


def _tint(base: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(int(base[i] + (255 - base[i]) * amount) for i in range(3))


def _shade(base: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(int(base[i] * (1 - amount)) for i in range(3))


def _fit_label(draw: ImageDraw.ImageDraw, name: str, font, max_w: int) -> str:
    if draw.textlength(name, font=font) <= max_w:
        return name
    while name and draw.textlength(name + "…", font=font) > max_w:
        name = name[:-1]
    return name + "…" if name else "…"


def _draw_bricks(draw: ImageDraw.ImageDraw, overlay: Image.Image, pal,
                 bricks: list[dict], font) -> None:
    for b in bricks:
        if not b["alive"]:
            continue
        x0, y0, x1, y1 = b["rect"]
        base = ROW_HUES[b["row"] % len(ROW_HUES)]
        level = max(1, b.get("level", 1))
        # Nível mais alto = um toque mais claro no mesmo matiz (sem lavar).
        color = _tint(base, min(0.18, (level - 1) * 0.05))
        hp = min(1.0, level / 5)
        cx = (x0 + x1) / 2

        # Corpo em cápsula com brilho no topo (look arcade).
        draw.rounded_rectangle((x0, y0, x1, y1), radius=(y1 - y0) // 2,
                               fill=color + (255,),
                               outline=(255, 255, 255, 130), width=1)
        draw.line((x0 + 6, y0 + 3, x1 - 6, y0 + 3),
                  fill=(255, 255, 255, 90), width=1)
        # Barrinha de "vida" na base do bloco.
        if hp < 1.0:
            bw = int((x1 - x0 - 12) * hp)
            if bw > 0:
                draw.line((x0 + 6, y1 - 4, x0 + 6 + bw, y1 - 4),
                          fill=_shade(base, 0.55) + (220,), width=2)

        label = _fit_label(draw, b["name"], font, x1 - x0 - 12)
        tw = draw.textlength(label, font=font)
        draw.text((cx - tw / 2, y0 + (y1 - y0 - 10) / 2), label,
                  font=font, fill=(20, 22, 28, 235) if _luminance(color) > 150
                  else (255, 255, 255, 240))


def _luminance(rgb: tuple[int, int, int]) -> float:
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def _draw_ball(draw: ImageDraw.ImageDraw, overlay: Image.Image, pal,
               ball: tuple[float, float], trail: list) -> None:
    # Rastro luminoso: pontos cada vez menores/mais apagados atrás da bolinha.
    for i, (tx, ty) in enumerate(trail[:-1]):
        f = (i + 1) / max(1, len(trail))
        r = BALL_R * f * 0.85
        a = int(TRAIL_ALPHA * f)
        draw.ellipse((tx - r, ty - r, tx + r, ty + r),
                     fill=pal["secondary"][:3] + (a,))
    x, y = ball
    # Halo suave em volta da bolinha.
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse(
        (x - BALL_R * 3, y - BALL_R * 3, x + BALL_R * 3, y + BALL_R * 3),
        fill=pal["secondary"][:3] + (70,))
    glow = glow.filter(ImageFilter.GaussianBlur(6))
    overlay.alpha_composite(glow)
    draw.ellipse((x - BALL_R, y - BALL_R, x + BALL_R, y + BALL_R),
                 fill=(255, 255, 255, 255), outline=pal["secondary"][:3] + (255,))


def _draw_paddle(draw: ImageDraw.ImageDraw, pal, paddle_x: float) -> None:
    x0 = paddle_x - PADDLE_W / 2
    y0, y1 = PADDLE_TOP, PADDLE_TOP + PADDLE_H
    rect = (int(x0), y0, int(x0 + PADDLE_W), y1)
    draw.rounded_rectangle(rect, radius=PADDLE_H // 2,
                           fill=pal["secondary"] + (255,),
                           outline=(255, 255, 255, 200))
    draw.line((int(x0) + 8, y0 + 3, int(x0 + PADDLE_W) - 8, y0 + 3),
              fill=(255, 255, 255, 120), width=1)
    # Base de apoio brilhante sob a raquete.
    draw.rounded_rectangle((int(x0) + 12, y1 + 2, int(x0 + PADDLE_W) - 12, y1 + 4),
                           radius=1, fill=pal["primary"][:3] + (90,))


def _draw_anims(draw: ImageDraw.ImageDraw, anims: list[dict], font, pal) -> None:
    for an in anims:
        age = an["age"]
        t = min(1.0, age / ANIM_FRAMES)
        alpha = int(255 * (1 - t))
        x0, y0, x1, y1 = an["rect"]
        base = ROW_HUES[an["row"] % len(ROW_HUES)]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        # Explosão em partículas: 8 faíscas radiais que se afastam e apagam.
        for k in range(8):
            ang = k * math.pi / 4 + an.get("phase", 0)
            dist = 4 + age * 2.2
            px = cx + math.cos(ang) * dist
            py = cy + math.sin(ang) * dist
            r = max(0.5, 3.2 * (1 - t))
            draw.ellipse((px - r, py - r, px + r, py + r),
                         fill=base + (alpha,))
        # Anel de choque expandindo.
        ring = int(6 + age * 3.5)
        draw.ellipse((cx - ring, cy - ring, cx + ring, cy + ring),
                     outline=(255, 255, 255, int(alpha * 0.6)), width=2)
        text = f"+{an['gain']}"
        tw = draw.textlength(text, font=font)
        draw.text((cx - tw / 2, cy - 18 - age * 2), text, font=font,
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
    # Paleta local: no breakout o "secondary" vira um ciano arcade (a bolinha,
    # a raquete e o score), em vez do verde do tema da cobrinha.
    pal = dict(ctx.palette)
    pal["secondary"] = (110, 220, 255)
    states = simulate(items, rng)
    for st in states:
        st["data_name"] = ctx.data_name
    steps = len(states) - 1
    if ctx.smooth:
        smooth = max(1, min(SMOOTH, MAX_RENDER_FRAMES // max(1, steps)))
    else:
        smooth = 1

    font_s = load_font(13)
    font_xs = load_font(10)
    font_l = load_font(20)
    anims: list[dict] = []
    frames: list[Image.Image] = []

    for k in range(steps):
        a, b = states[k], states[k + 1]
        for ev in b.get("events", []):
            anims.append({"age": 0, "rect": ev["rect"], "gain": ev["gain"],
                          "row": ev.get("row", 0), "phase": (k % 8) * 0.4})
        for s in range(smooth):
            t = s / smooth
            ax, ay = a["ball"]
            bx, by = b["ball"]
            ball = (ax + (bx - ax) * t, ay + (by - ay) * t)
            paddle_x = a["paddle_x"] + (b["paddle_x"] - a["paddle_x"]) * t
            trail = list(a.get("trail", [])) + [ball]

            frame = background.copy()
            overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            _draw_bricks(draw, overlay, pal, b["bricks"], font_xs)
            _draw_ball(draw, overlay, pal, ball, trail)
            _draw_paddle(draw, pal, paddle_x)
            _draw_hud(draw, pal, a, len(items), font_s, font_l, truncated)
            _draw_anims(draw, anims, font_l, pal)

            if a["done"]:
                msg = "CONCLUÍDO!" if a["finished"] else "TEMPO LIMITE"
                tw = draw.textlength(msg, font=font_l)
                draw.text(((WIDTH - tw) / 2, GRID_Y + 80), msg, font=font_l,
                          fill=ctx.palette["accent"] + (255,))

            frame = Image.alpha_composite(frame, overlay)
            frames.append(frame)
            for an in anims:
                an["age"] += 1
        anims = [an for an in anims if an["age"] < ANIM_FRAMES]

    if not frames:
        s0 = states[0]
        frame = background.copy()
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        _draw_bricks(draw, overlay, pal, s0["bricks"], font_xs)
        _draw_ball(draw, overlay, pal, s0["ball"], list(s0.get("trail", [])))
        _draw_paddle(draw, pal, s0["paddle_x"])
        _draw_hud(draw, pal, s0, len(items), font_s, font_l, truncated)
        frames.append(Image.alpha_composite(frame, overlay))

    fps = ctx.fps * smooth
    save_gif(frames, ctx.output, fps, ctx.preview, colors=64)
