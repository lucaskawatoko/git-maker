from __future__ import annotations

DEFAULT_BACKGROUND = "#0d1117"
DEFAULT_FOOD = "#ff6b4a"


def _hex(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#").strip()
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def _mix(a: tuple[int, int, int], b: tuple[int, int, int],
         t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _luminance(rgb: tuple[int, int, int]) -> float:
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def build_palette(color: str, background: str | None = None,
                  food: str | None = None) -> dict:
    """Deriva a paleta da cobrinha a partir de cores hex arbitrárias.

    `color` = cor do corpo; `background` = fundo; `food` = cor da comida.
    Todas aceitam hex no formato `#rrggbb`. Se omitidos, fundo e comida usam
    padrões que contrastam com a cor escolhida.
    """
    base = _hex(color)
    white = (255, 255, 255)
    black = (0, 0, 0)
    bg = _hex(background) if background else _mix(base, black, 0.88)
    # Cabeça mais escura que o corpo se a cor for clara, senão mais clara
    secondary = _mix(base, black if _luminance(base) > 128 else white, 0.35)
    return {
        "bg": bg,
        "grid": _mix(bg, white, 0.22),
        "primary": base,
        "secondary": secondary,
        "accent": (255, 205, 90),
        "warn": _hex(food) if food else _hex(DEFAULT_FOOD),
        "star": _mix(base, white, 0.85),
    }
