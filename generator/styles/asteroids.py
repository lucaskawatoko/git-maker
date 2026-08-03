from __future__ import annotations

"""Estilo Asteroids: repositórios/seguidores/semanas de contribuição virando
cometas que a nave central destrói. Cometa maior = dado maior. Com o flag
`avatar`, o avatar do usuário aparece no cometa principal."""

import math
import random

from PIL import Image, ImageDraw

from ..render import circular_crop, load_font, save_gif
from ..render_context import RenderContext
from . import register

WIDTH = 700
HEIGHT = 420
CX = WIDTH // 2
CY = HEIGHT // 2

R0 = 196
RH_BASE = 64
TRAVEL = 18          # frames de aproximação de cada cometa
EXPLOSION_MS = 6     # frames de explosão
GAP = 3              # pausa entre a explosão e o próximo cometa
DECIMATE = 2         # render a cada 2 sim frames => ~12fps de saída (GIF leve)

FPS = 24
INTRO = 18
OUTRO = 14
# Um cometa por vez: cada ciclo = aproximação + explosão + pausa.
CYCLE = TRAVEL + EXPLOSION_MS + GAP

TITLES = {
    "repos": "ASTRO REPOS",
    "commits": "ASTRO COMMITS",
    "followers": "ASTRO FOLLOWERS",
}
SUBTITLES = {
    "repos": "seus repositórios viraram cometas!",
    "commits": "suas contribuições viraram cometas!",
    "followers": "seus seguidores viraram cometas!",
}
TOTAL_LABELS = {
    "repos": "REPOS PÚBLICOS",
    "commits": "SEMANAS",
    "followers": "SEGUIDORES",
}


def build_background(pal) -> Image.Image:
    img = Image.new("RGBA", (WIDTH, HEIGHT), pal["bg"] + (255,))
    draw = ImageDraw.Draw(img)
    for x in range(0, WIDTH, 28):
        draw.line([(x, 0), (x, HEIGHT)], fill=pal["grid"] + (70,), width=1)
    for y in range(0, HEIGHT, 28):
        draw.line([(0, y), (WIDTH, y)], fill=pal["grid"] + (70,), width=1)

    rng = random.Random(11)
    for _ in range(110):
        x = rng.randint(0, WIDTH - 1)
        y = rng.randint(0, HEIGHT - 1)
        color = pal["star"] if rng.random() < 0.85 else pal["primary"]
        draw.ellipse((x, y, x + 1, y + 1), fill=color + (rng.randint(30, 150),))

    for y in range(0, HEIGHT, 3):
        draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, 22), width=1)
    return img


def ship_points(cx: float, cy: float, ang: float) -> tuple[tuple, tuple, tuple, tuple]:
    nose = (cx + 22 * math.cos(ang), cy + 22 * math.sin(ang))
    bl = (cx + 14 * math.cos(ang + 2.45), cy + 14 * math.sin(ang + 2.45))
    br = (cx + 14 * math.cos(ang - 2.45), cy + 14 * math.sin(ang - 2.45))
    rear = (cx + 6 * math.cos(ang + math.pi), cy + 6 * math.sin(ang + math.pi))
    return nose, bl, rear, br


def draw_ship(draw: ImageDraw.ImageDraw, pal, ang: float, i: int) -> tuple[float, float]:
    nose, bl, rear, br = ship_points(CX, CY, ang)
    draw.polygon([nose, bl, rear, br], fill=(13, 22, 44), outline=pal["primary"])
    cockpit = (CX + 10 * math.cos(ang), CY + 10 * math.sin(ang))
    draw.ellipse(
        (cockpit[0] - 2, cockpit[1] - 2, cockpit[0] + 2, cockpit[1] + 2),
        fill=(80, 255, 220),
    )
    flame = 8 + 4 * math.sin(i * 0.9)
    fx, fy = -math.cos(ang), -math.sin(ang)
    px, py = -fy, fx
    tip = (rear[0] + fx * flame, rear[1] + fy * flame)
    draw.polygon(
        [rear, (rear[0] + px * 3, rear[1] + py * 3), tip, (rear[0] - px * 3, rear[1] - py * 3)],
        fill=pal["warn"],
    )
    return nose


def draw_comet(overlay: Image.Image, pal, cx: float, cy: float,
               theta: float, level: int, avatar_img: Image.Image | None) -> None:
    draw = ImageDraw.Draw(overlay)
    tail = 8 + 5 * level
    for seg in range(4):
        a0, a1 = 0.25 * seg, 0.25 * (seg + 1)
        x0 = cx + math.cos(theta) * tail * a0
        y0 = cy + math.sin(theta) * tail * a0
        x1 = cx + math.cos(theta) * tail * a1
        y1 = cy + math.sin(theta) * tail * a1
        alpha = int(150 * (1 - seg * 0.25))
        draw.line((x0, y0, x1, y1), fill=pal["levels"][level - 1] + (alpha,), width=1)

    if avatar_img is not None:
        d = 14 + 2 * level
        half = d // 2
        draw.ellipse((cx - half, cy - half, cx + half, cy + half),
                     outline=pal["primary"] + (255,))
        av = circular_crop(avatar_img, d)
        overlay.paste(av, (int(cx - half), int(cy - half)), av)
        draw.ellipse((cx - half, cy - half, cx + half, cy + half),
                     outline=(255, 255, 255, 160), width=1)
        return

    r = 2 + level
    draw.ellipse((cx - r, cy - r, cx + r, cy + r),
                 outline=pal["levels"][level - 1] + (170,))
    draw.ellipse((cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1),
                 fill=(255, 255, 255, 210))


def draw_laser(overlay: Image.Image, pal, nose: tuple[float, float],
               target: tuple[float, float], p: float) -> None:
    draw = ImageDraw.Draw(overlay)
    hx = nose[0] + (target[0] - nose[0]) * p
    hy = nose[1] + (target[1] - nose[1]) * p
    dx, dy = target[0] - nose[0], target[1] - nose[1]
    d = math.hypot(dx, dy) or 1
    ux, uy = dx / d, dy / d
    bx, by = hx - ux * 10, hy - uy * 10
    draw.line((bx, by, hx, hy), fill=pal["primary"] + (220,), width=1)
    draw.ellipse((hx - 2, hy - 2, hx + 2, hy + 2), fill=(255, 255, 255, 240))


def draw_explosion(overlay: Image.Image, pal, pos: tuple[float, float],
                   level: int, age: float, seed: int) -> None:
    draw = ImageDraw.Draw(overlay)
    t = min(1.0, age / EXPLOSION_MS)
    cx, cy = pos
    r = 2 + (6 + level) * t
    draw.ellipse((cx - r, cy - r, cx + r, cy + r),
                 fill=(255, 255, 255, int(190 * (1 - t))))
    for k in range(7):
        angle = seed * 2.399 + k * 2.399
        dist = 3 + (11 + level) * t
        px = cx + math.cos(angle) * dist
        py = cy + math.sin(angle) * dist
        color = pal["levels"][level - 1] if k % 3 else pal["warn"]
        size = 2 if k % 2 else 1
        alpha = int(220 * (1 - t))
        draw.rectangle((px - size, py - size, px + size, py + size),
                       fill=color + (alpha,))


def draw_hud(frame: Image.Image, pal, score: int, total: int, target_name: str | None,
             i: int, data_name: str, font_s, font_l) -> None:
    draw = ImageDraw.Draw(frame)
    draw.text((24, 16), "SCORE", font=font_s, fill=(150, 160, 180, 255))
    draw.text((24, 38), f"{score:03d}", font=font_l, fill=pal["secondary"] + (255,))
    draw.text((24, 78), f"{TOTAL_LABELS[data_name]}: {total}", font=font_s,
              fill=(150, 160, 180, 255))
    if target_name:
        name = target_name if len(target_name) <= 24 else target_name[:21] + "..."
        tw = draw.textlength(name, font=font_s)
        draw.text((WIDTH - 24 - tw, 16), name, font=font_s, fill=pal["primary"] + (255,))
    if i < INTRO:
        title = TITLES[data_name]
        tw = draw.textlength(title, font=font_l)
        draw.text(((WIDTH - tw) / 2, 16), title, font=font_l, fill=pal["accent"] + (255,))
        sub = SUBTITLES[data_name]
        sw = draw.textlength(sub, font=font_s)
        draw.text(((WIDTH - sw) / 2, 46), sub, font=font_s, fill=pal["primary"] + (200,))


def build_comets(items: list[dict]) -> list[dict]:
    rng = random.Random(7)
    comets = []
    for i, item in enumerate(items):
        theta = rng.uniform(0, 2 * math.pi)
        rh = RH_BASE + (i % 5) * 13
        comets.append({
            "name": item["name"],
            "level": item["level"],
            "avatar": i == 0,  # cometa principal (maior) recebe o avatar
            "ts": INTRO + i * CYCLE,  # um por vez, em sequência
            "theta": theta,
            "rh": rh,
            "speed": (R0 - rh) / TRAVEL,
            "hit_pos": (CX + math.cos(theta) * rh, CY + math.sin(theta) * rh),
        })
    return comets


def comet_pos(comet: dict, t: float) -> tuple[float, float]:
    r = R0 - comet["speed"] * t
    return (CX + math.cos(comet["theta"]) * r, CY + math.sin(comet["theta"]) * r)


def closest_angle(cur: float, target: float) -> float:
    return (target - cur + math.pi) % (2 * math.pi) - math.pi


@register("asteroids")
def render(ctx: RenderContext) -> None:
    ctx.width, ctx.height = WIDTH, HEIGHT
    background = build_background(ctx.palette)
    comets = build_comets(ctx.items) if ctx.items else []
    n = len(comets)
    last_ts = comets[-1]["ts"] if n else INTRO
    TOTAL = int(round(last_ts + TRAVEL + EXPLOSION_MS)) + OUTRO

    font_s = load_font(14)
    font_l = load_font(20)
    frames = []

    cur_angle = -math.pi / 2
    for i in range(TOTAL):
        if i % DECIMATE:
            continue
        frame = background.copy()
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))

        target = None
        for c in comets:
            t = i - c["ts"]
            if 0 <= t < TRAVEL:
                target = c
                break

        if target is not None:
            tx, ty = comet_pos(target, i - target["ts"])
            wanted = math.atan2(ty - CY, tx - CX)
            d = closest_angle(cur_angle, wanted)
            cur_angle += d * 0.30
            if abs(d) < 0.05:
                cur_angle = wanted
        else:
            cur_angle += 0.015

        draw = ImageDraw.Draw(frame)
        nose = draw_ship(draw, ctx.palette, cur_angle, i)

        for k, c in enumerate(comets):
            t = i - c["ts"]
            if 0 <= t < TRAVEL:
                px, py = comet_pos(c, t)
                av = ctx.avatar if c["avatar"] else None
                draw_comet(overlay, ctx.palette, px, py, c["theta"], c["level"], av)
            elif TRAVEL <= t < TRAVEL + EXPLOSION_MS:
                draw_explosion(overlay, ctx.palette, c["hit_pos"], c["level"],
                               t - TRAVEL, k)

        if target is not None:
            p = (i - target["ts"]) / TRAVEL
            draw_laser(overlay, ctx.palette, nose, comet_pos(target, i - target["ts"]), p)

        score = sum(1 for c in comets if (i - c["ts"]) >= TRAVEL)
        target_name = target["name"] if target else None
        draw_hud(frame, ctx.palette, score, len(comets), target_name, i,
                 ctx.data_name, font_s, font_l)

        frame = Image.alpha_composite(frame, overlay).convert("RGB")

        if i >= TOTAL - OUTRO:
            t = (i - (TOTAL - OUTRO)) / OUTRO
            black = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
            frame = Image.blend(frame, black, min(1.0, t * 1.05))

        frames.append(frame)

    save_gif(frames, ctx.output, max(1, ctx.fps // DECIMATE), ctx.preview)
