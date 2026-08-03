#!/usr/bin/env python3
"""CLI do github-gif-maker: gera o GIF Asteroids atirando nos repositórios
públicos do usuário (um cometa por vez).

Uso:
    python -m generator [--user USUARIO] [--limit N] [--mock] [--preview] [--output PATH]
"""

from __future__ import annotations

import argparse
import os
import sys

from . import api
from .asteroids import WIDTH, HEIGHT, render

DEFAULT_USER = "lucaskawatoko"
DEFAULT_OUTPUT = "imgs/contribution-animation.gif"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generator",
        description="Gera o GIF Asteroids com os repositórios do usuário virando cometas.",
    )
    parser.add_argument("--user", "--username", dest="user", default=None,
                        help=f"usuário do GitHub (padrão: GH_USER ou {DEFAULT_USER})")
    parser.add_argument("--limit", type=int, default=0,
                        help="máximo de cometas (0 = todos, um por vez)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--mock", action="store_true",
                        help="usa dados fictícios em vez da API")
    parser.add_argument("--preview", action="store_true",
                        help="salva também um PNG do primeiro frame")
    args = parser.parse_args(argv)

    username = args.user or os.environ.get("GH_USER") or DEFAULT_USER
    if args.mock:
        repos = api.mock_repos()
    else:
        repos = api.fetch_repos(username)

    total = len(repos)
    limit = args.limit if args.limit and args.limit > 0 else total
    repos = repos[:limit]

    if not repos:
        print("Nenhum repositório público encontrado.", file=sys.stderr)

    render(repos, args.output, args.preview)
    size = os.path.getsize(args.output) / 1024
    shown = f" ({len(repos)} de {total})" if total > len(repos) else ""
    print(f"GIF gerado em {args.output} ({size:.0f} KB, {WIDTH}x{HEIGHT}) "
          f"para @{username} ({len(repos)} cometas{shown})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
