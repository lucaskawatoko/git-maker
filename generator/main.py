#!/usr/bin/env python3
"""CLI do git-maker: gera o GIF da cobrinha comendo os dados do GitHub.

Uso:
    python -m generator [--user USUARIO] [--data repos|commits]
                        [--color HEX] [--food HEX]
                        [--output PATH] [--mock] [--preview]
    python -m generator --ascii [--width COLUNAS] [--color HEX]
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


def _run_ascii(args, username: str) -> int:
    from . import ascii_art
    from .palettes import _hex

    if args.mock:
        avatar = ascii_art.mock_avatar()
    else:
        avatar = api.fetch_avatar(username, 256)
        if avatar is None:
            print("Aviso: não foi possível baixar o avatar. Usando gradiente de teste.",
                  file=sys.stderr)
            avatar = ascii_art.mock_avatar()

    ink = ascii_art.DEFAULT_INK if not args.color else _hex(args.color) + (255,)
    ascii_art.render_ascii(
        avatar, args.output, cols=args.width, ink=ink,
        fps=24, preview=args.preview,
    )
    size = os.path.getsize(args.output) / 1024
    print(f"ASCII gerado em {args.output} ({size:.0f} KB, {args.width} colunas) "
          f"para @{username}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generator",
        description="Gera o GIF da cobrinha comendo os dados do usuário.",
    )
    parser.add_argument("--user", "--username", dest="user", default=None,
                        help=f"usuário do GitHub (padrão: GH_USER ou {DEFAULT_USER})")
    parser.add_argument("--data", choices=DATA_CHOICES, default="repos",
                        help="dados que viram comida da cobrinha (repos, commits, followers)")
    parser.add_argument("--color", default=None,
                        help="cor da cobrinha/tinta em hex (padrão cobrinha: #3fb950; "
                             "padrão ASCII: cinza-claro)")
    parser.add_argument("--food", default=None,
                        help="cor da comida em hex (padrão: #ff6b4a)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=None,
                        help="semente da simulação (padrão: aleatória a cada execução)")
    parser.add_argument("--mock", action="store_true",
                        help="usa dados fictícios em vez da API")
    parser.add_argument("--preview", action="store_true",
                        help="salva também um PNG do primeiro frame")
    parser.add_argument("--ascii", action="store_true",
                        help="gera o GIF ASCII do avatar (foto com efeito de impressão)")
    parser.add_argument("--width", type=int, default=56,
                        help="largura da grade ASCII em colunas (padrão: 56)")
    args = parser.parse_args(argv)

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    username = args.user or os.environ.get("GH_USER") or DEFAULT_USER

    if args.ascii:
        return _run_ascii(args, username)

    items = _load_items(args, username, token)
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
    )
    render(ctx)
    size = os.path.getsize(args.output) / 1024
    print(f"GIF gerado em {args.output} ({size:.0f} KB, {ctx.width}x{ctx.height}) "
          f"para @{username} ({len(items)} itens)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
