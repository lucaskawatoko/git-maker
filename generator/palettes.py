from __future__ import annotations

# Presets de paleta. Cada chave é um hex; `build_palette` converte para RGB.
# Chaves: bg, grid, levels (4 níveis), primary, secondary, accent, warn, star.
PRESETS: dict[str, dict[str, str]] = {
    "cyan": {
        "bg": "#050810", "grid": "#182236",
        "levels": ("#0f6458", "#15947a", "#21c89e", "#48ffd2"),
        "primary": "#79c0ff", "secondary": "#3fb950",
        "accent": "#ffcd5a", "warn": "#ff9646", "star": "#d2e0f0",
    },
    "pink": {
        "bg": "#140611", "grid": "#3a1533",
        "levels": ("#8f1d6e", "#c22d94", "#e356b8", "#ff8fdd"),
        "primary": "#ff6bcb", "secondary": "#ff4d6d",
        "accent": "#ffd166", "warn": "#ff9f1c", "star": "#ffe3f4",
    },
    "green": {
        "bg": "#04130a", "grid": "#0f3a20",
        "levels": ("#0e7a3d", "#17a455", "#2bd475", "#7dffb0"),
        "primary": "#56d364", "secondary": "#a8ff60",
        "accent": "#f7ff3d", "warn": "#ffb300", "star": "#d8ffd8",
    },
    "orange": {
        "bg": "#120a05", "grid": "#38210f",
        "levels": ("#8a3c12", "#b65417", "#e07a2a", "#ffb36b"),
        "primary": "#ffa657", "secondary": "#ffd28f",
        "accent": "#ffdf5e", "warn": "#ff6b4a", "star": "#ffe8cc",
    },
    "purple": {
        "bg": "#0c0714", "grid": "#241a3a",
        "levels": ("#5b3c8f", "#7a54bd", "#a07ee0", "#cfb1ff"),
        "primary": "#a371f7", "secondary": "#e0b0ff",
        "accent": "#ffd166", "warn": "#ff9f1c", "star": "#ecdcff",
    },
    "blue": {
        "bg": "#04101a", "grid": "#0d2c42",
        "levels": ("#0f5f8f", "#1c82bd", "#3aa6e0", "#8fd4ff"),
        "primary": "#58a6ff", "secondary": "#39d0ff",
        "accent": "#ffd166", "warn": "#ff9f1c", "star": "#d0f0ff",
    },
}


def _hex(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def _mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _derive(base: tuple[int, int, int]) -> dict:
    """Deriva uma paleta completa a partir de uma cor arbitrária (hex)."""
    white = (255, 255, 255)
    black = (0, 0, 0)
    bg = _mix(base, black, 0.88)
    return {
        "bg": bg,
        "grid": _mix(bg, white, 0.22),
        "levels": (
            _mix(base, black, 0.55),
            _mix(base, black, 0.30),
            _mix(base, black, 0.10),
            base,
        ),
        "primary": base,
        "secondary": _mix(base, white, 0.45),
        "accent": (255, 205, 90),
        "warn": (255, 150, 70),
        "star": _mix(base, white, 0.85),
    }


def build_palette(color: str) -> dict:
    """Retorna a paleta em RGB. Aceita um preset ou uma cor hex (#rrggbb)."""
    color = color.strip().lower()
    if color in PRESETS:
        raw = PRESETS[color]
        return {k: tuple(_hex(v) for v in vals) if isinstance(vals, tuple) else _hex(vals)
                for k, vals in raw.items()}
    if not color.startswith("#"):
        color = "#" + color
    return _derive(_hex(color))
