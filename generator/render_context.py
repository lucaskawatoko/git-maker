from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image

from .render import FPS


@dataclass
class RenderContext:
    """Contexto compartilhado entre os estilos.

    `items` é a lista já ordenada (maior primeiro) de dicionários
    `{"name", "count", "level"}` fornecida pela camada de dados.
    """

    output: str
    palette: dict
    items: list[dict] = field(default_factory=list)
    data_name: str = "repos"
    username: str = ""
    avatar: Image.Image | None = None
    fps: int = FPS
    preview: bool = False
    width: int = 700
    height: int = 420
