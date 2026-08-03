from __future__ import annotations

from ..render_context import RenderContext

STYLES: dict[str, callable] = {}


def register(name: str):
    def decorator(fn):
        STYLES[name] = fn
        return fn

    return decorator


def render_all(ctx: RenderContext, styles: list[str]) -> None:
    for name in styles:
        if name not in STYLES:
            raise SystemExit(f"Estilo desconhecido: {name}")
        STYLES[name](ctx)


from . import asteroids, snake  # noqa: E402,F401
