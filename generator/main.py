from __future__ import annotations

import argparse
import os
import sys

from PIL import Image, ImageDraw

from . import api, avatar
from .palettes import build_palette
from .render import load_font
from .render_context import RenderContext
from .styles import STYLES

DEFAULT_USER = "lucaskawatoko"
DATA_CHOICES = ("repos", "commits", "followers")


def _load_items(args, username: str, token: str | None) -> list[dict]:
    if args.mock:
        return api.mock_items(args.data)
    if args.data == "repos":
        return api.fetch_repos(username)
    if args.data == "followers":
        return api.fetch_followers(username)
    if token:
        return api.fetch_commits(username, token)
    print("Aviso: --data commits exige GH_TOKEN/GITHUB_TOKEN. Usando dados fictícios.",
          file=sys.stderr)
    return api.mock_items("commits")


def _mock_avatar(data: str) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (20, 28, 44, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse((4, 4, 60, 60), fill=(90, 130, 200, 255))
    initial = {"repos": "R", "commits": "C", "followers": "F"}[data]
    font = load_font(30)
    tw = draw.textlength(initial, font=font)
    draw.text(((64 - tw) / 2, 16), initial, font=font, fill=(255, 255, 255, 255))
    return img


def _load_avatar(args, username: str) -> Image.Image | None:
    if not args.avatar:
        return None
    if args.mock:
        return _mock_avatar(args.data)
    img = avatar.fetch_avatar(username)
    return img if img is not None else _mock_avatar(args.data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generator",
        description="Gera GIFs animados de perfil com dados do GitHub.",
    )
    parser.add_argument("--user", "--username", dest="user", default=None,
                        help=f"usuário do GitHub (padrão: GH_USER ou {DEFAULT_USER})")
    parser.add_argument("--style", choices=sorted(STYLES), default="asteroids",
                        help="estilo da animação")
    parser.add_argument("--data", choices=DATA_CHOICES, default="repos",
                        help="dados a transformar em cometas/comida")
    parser.add_argument("--limit", type=int, default=0,
                        help="máximo de cometas/comida (0 = todos, um por vez no jogo)")
    parser.add_argument("--color", default="cyan",
                        help="paleta preset (cyan|pink|green|orange|purple|blue) ou hex")
    parser.add_argument("--avatar", action="store_true",
                        help="usa o avatar do usuário na animação")
    parser.add_argument("--output", default="imgs/contribution-animation.gif")
    parser.add_argument("--mock", action="store_true",
                        help="usa dados fictícios em vez da API")
    parser.add_argument("--preview", action="store_true",
                        help="salva também um PNG do primeiro frame")
    args = parser.parse_args(argv)

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    username = args.user or os.environ.get("GH_USER") or DEFAULT_USER
    raw_items = _load_items(args, username, token)
    total = len(raw_items)
    limit = args.limit if args.limit and args.limit > 0 else total
    items = raw_items[:limit]
    palette = build_palette(args.color)
    av = _load_avatar(args, username)

    ctx = RenderContext(
        output=args.output,
        palette=palette,
        items=items,
        data_name=args.data,
        username=username,
        avatar=av,
        preview=args.preview,
    )
    STYLES[args.style](ctx)
    size = os.path.getsize(args.output) / 1024
    shown = f" ({len(items)} de {total} itens)" if total > len(items) else ""
    print(f"GIF gerado em {args.output} ({size:.0f} KB, {ctx.width}x{ctx.height}) "
          f"para @{username} ({len(items)} cometas{shown})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
