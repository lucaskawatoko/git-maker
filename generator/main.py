#!/usr/bin/env python3
"""CLI do git-maker: gera o GIF da cobrinha comendo os dados do GitHub.

Uso:
    python -m generator [--user USUARIO] [--data repos|commits|followers]
                        [--game snake|breakout]
                        [--color HEX] [--food HEX]
                        [--output PATH] [--mock] [--preview]
                        [--smooth|--no-smooth] [--seed N]
"""

from __future__ import annotations

import argparse
import os
import re
import sys

from . import api
from .games.breakout import render as render_breakout
from .palettes import build_palette
from .render_context import RenderContext
from .snake import MAX_ITEMS, render as render_snake

DEFAULT_USER = "lucaskawatoko"
DEFAULT_COLOR = "#3fb950"
DEFAULT_OUTPUT = "imgs/contribution-animation.gif"
DATA_CHOICES = ("repos", "commits", "followers")
GAME_CHOICES = ("snake", "breakout")
GAMES = {"snake": render_snake, "breakout": render_breakout}

_HEX_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")


def _check_hex(value: str | None, flag: str) -> None:
    if value is not None and not _HEX_RE.match(value):
        raise SystemExit(f"{flag} deve ser #rrggbb (ex.: #3fb950); recebido: {value!r}")


def _load_items(args, username: str, token: str | None) -> list[dict]:
    if args.mock:
        return api.mock_items(args.data)
    if args.data == "followers":
        return api.fetch_followers(username)
    if args.data == "repos":
        return api.fetch_repos(username)
    if token:
        return api.fetch_commits(username, token)
    print("Aviso: --data commits exige GH_TOKEN/GITHUB_TOKEN. Usando dados fictícios.",
          file=sys.stderr)
    return api.mock_items("commits")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generator",
        description="Gera o GIF da cobrinha comendo os dados do usuário.",
    )
    parser.add_argument("--user", "--username", dest="user", default=None,
                        help=f"usuário do GitHub (padrão: GH_USER ou {DEFAULT_USER})")
    parser.add_argument("--data", choices=DATA_CHOICES, default="repos",
                        help="dados que viram comida do jogo (repos, commits, followers)")
    parser.add_argument("--game", choices=GAME_CHOICES, default="snake",
                        help="estilo do jogo: snake ou breakout (padrão: snake)")
    parser.add_argument("--color", default=None,
                        help="cor da cobrinha em hex (padrão: #3fb950)")
    parser.add_argument("--food", default=None,
                        help="cor da comida em hex (padrão: #ff6b4a)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=None,
                        help="semente da simulação (padrão: aleatória a cada execução)")
    parser.add_argument("--mock", action="store_true",
                        help="usa dados fictícios em vez da API")
    parser.add_argument("--preview", action="store_true",
                        help="salva também um PNG do primeiro frame")
    parser.add_argument("--smooth", dest="smooth", action="store_true", default=None,
                        help="movimento interpolado (padrão: ligado)")
    parser.add_argument("--no-smooth", dest="smooth", action="store_false",
                        help="movimento em passos, sem interpolação")
    parser.set_defaults(smooth=True)
    args = parser.parse_args(argv)

    _check_hex(args.color, "--color")
    _check_hex(args.food, "--food")

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    username = args.user or os.environ.get("GH_USER") or DEFAULT_USER

    items = _load_items(args, username, token)
    if len(items) > MAX_ITEMS:
        print(f"Aviso: exibindo top {MAX_ITEMS} de {len(items)} itens.",
              file=sys.stderr)
    palette = build_palette(args.color or DEFAULT_COLOR, args.food)

    avatar = None
    avatars: dict = {}
    if not args.mock:
        avatar = api.fetch_avatar(username)
        if args.data == "followers":
            for item in items[:MAX_ITEMS]:
                url = item.get("avatar_url")
                if url:
                    img = api.load_image(url, 64)
                    if img:
                        avatars[item["name"]] = img

    ctx = RenderContext(
        output=args.output,
        palette=palette,
        items=items,
        data_name=args.data,
        username=username,
        preview=args.preview,
        avatar=avatar,
        avatars=avatars,
        seed=args.seed,
        total_items=len(items),
        smooth=args.smooth,
    )
    render_game = GAMES[args.game]
    render_game(ctx)
    size = os.path.getsize(args.output) / 1024
    print(f"GIF gerado em {args.output} ({size:.0f} KB, {ctx.width}x{ctx.height}) "
          f"para @{username} ({len(items)} itens)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
