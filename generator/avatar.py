from __future__ import annotations

import io
from urllib.request import Request, urlopen

from PIL import Image


def fetch_avatar(username: str, size: int = 96) -> Image.Image | None:
    """Baixa o avatar público do usuário em https://github.com/{user}.png."""
    url = f"https://github.com/{username}.png?size={size}"
    try:
        req = Request(url, headers={"User-Agent": "github-gif-maker"})
        with urlopen(req, timeout=15) as resp:
            data = resp.read()
        return Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception:  # noqa: BLE001
        return None
