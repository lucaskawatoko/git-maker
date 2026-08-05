#!/usr/bin/env python3
"""CLI do git-maker: gera o GIF da cobrinha comendo os dados do GitHub.

Uso:
    python -m generator [--user USUARIO] [--data repos|commits]
                        [--color HEX] [--food HEX]
                        [--output PATH] [--mock] [--preview]
"""

from __future__ import annotations

import argparse
import os
import sys

from . import api
from .palettes import build_palette
from .render_context import RenderContext
from .snake import MAX_ITEMS, render

DEFAULT_USER = "lucaskawatoko"
DEFAULT_COLOR = "#3fb950"
DEFAULT_OUTPUT = "imgs/contribution-animation.gif"
DATA_CHOICES = ("repos", "commits", "followers")


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
                        help="dados que viram comida da cobrinha (repos, commits, followers)")
    parser.add_argument("--color", default=DEFAULT_COLOR,
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
    args = parser.parse_args(argv)

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    username = args.user or os.environ.get("GH_USER") or DEFAULT_USER
    items = _load_items(args, username, token)
    palette = build_palette(args.color, args.food)

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
    )
    render(ctx)
    size = os.path.getsize(args.output) / 1024
    print(f"GIF gerado em {args.output} ({size:.0f} KB, {ctx.width}x{ctx.height}) "
          f"para @{username} ({len(items)} itens)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
