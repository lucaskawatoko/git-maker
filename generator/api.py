from __future__ import annotations

import io
import json
import random
import sys
from urllib.request import Request, urlopen

from PIL import Image

_USER_AGENT = "github-gif-maker"
_TIMEOUT = 30
_FOLLOWERS_PAGES = 10  # até 1000 seguidores (~10 req/h sem token)


def _get_json(url: str) -> dict | list:
    req = Request(url, headers={"User-Agent": _USER_AGENT})
    with urlopen(req, timeout=_TIMEOUT) as resp:
        return json.load(resp)


def rank_items(items: list[dict]) -> list[dict]:
    """Ordena por `count` (maior primeiro) e atribui nível 1-4 por ranking."""
    items.sort(key=lambda i: i["count"], reverse=True)
    total = len(items)
    for i, item in enumerate(items):
        item["level"] = 1 + min(3, (i * 4) // max(1, total)) if total else 1
    return items


def fetch_repos(username: str) -> list[dict]:
    """Top repositórios públicos do usuário por estrelas via Search API.

    O endpoint REST `GET /users/{login}/repos` não aceita `sort=stars`; a
    Search API (`q=user:{login} fork:false&sort=stars`) sim e já devolve
    ordenado por estrelas. Uma chamada cobre o top 100 — mais que os 25 do GIF.
    """
    items: list[dict] = []
    page = 1
    while page <= 5:
        url = ("https://api.github.com/search/repositories"
               f"?q=user:{username}+fork:false"
               f"&sort=stars&order=desc&per_page=100&page={page}")
        try:
            data = _get_json(url)
        except Exception as exc:  # noqa: BLE001
            raise SystemExit(f"Falha ao buscar repositórios de @{username}: {exc}") from exc
        if isinstance(data, dict) and data.get("message"):
            raise SystemExit(f"Erro da API GitHub: {data['message']}")
        nodes = data.get("items", []) if isinstance(data, dict) else []
        if not nodes:
            break
        items.extend(nodes)
        if len(nodes) < 100:
            break
        page += 1
    repos = [{"name": n.get("name", ""), "count": n.get("stargazers_count", 0) or 0}
             for n in items]
    return rank_items(repos)


def fetch_commits(username: str, token: str) -> list[dict]:
    """Contribuições do ano via GraphQL (exige token). Uma comida/semana."""
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays { contributionCount }
            }
          }
        }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"login": username}}).encode()
    req = Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": _USER_AGENT,
        },
    )
    try:
        with urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.load(resp)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Falha ao buscar contribuições de @{username}: {exc}") from exc
    if data.get("errors"):
        raise SystemExit(f"Erro da API GraphQL: {data['errors']}")
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    items = []
    for i, week in enumerate(weeks):
        count = sum(d.get("contributionCount", 0) for d in week.get("contributionDays", []))
        if count:
            items.append({"name": f"S{i + 1:02d}", "count": count})
    return rank_items(items)


def fetch_followers(username: str) -> list[dict]:
    """Seguidores públicos via REST (sem token), paginado. Cada seguidor = 1 comida."""
    items: list[dict] = []
    for page in range(1, _FOLLOWERS_PAGES + 1):
        url = (f"https://api.github.com/users/{username}/followers"
               f"?per_page=100&page={page}")
        try:
            nodes = _get_json(url)
        except Exception as exc:  # noqa: BLE001
            raise SystemExit(f"Falha ao buscar seguidores de @{username}: {exc}") from exc
        if isinstance(nodes, dict) and nodes.get("message"):
            raise SystemExit(f"Erro da API GitHub: {nodes['message']}")
        if not nodes:
            break
        items.extend(nodes)
        if len(nodes) < 100:
            break
    followers = [
        {"name": n.get("login", ""), "count": 1, "avatar_url": n.get("avatar_url", "")}
        for n in items
    ]
    return rank_items(followers)


# ---------------------------------------------------------------------------
# Avatares (cabeça da cobrinha e comidas que são seguidores)
# ---------------------------------------------------------------------------
def load_image(url: str, size: int) -> Image.Image | None:
    """Baixa uma imagem e redimensiona para `size`×`size`. None se falhar."""
    try:
        req = Request(url, headers={"User-Agent": _USER_AGENT})
        with urlopen(req, timeout=_TIMEOUT) as resp:
            data = resp.read()
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        if img.size != (size, size):
            img = img.resize((size, size), Image.LANCZOS)
        return img
    except Exception:  # noqa: BLE001
        return None


def fetch_avatar(username: str, size: int = 96) -> Image.Image | None:
    """Avatar do usuário, usado na cabeça da cobrinha."""
    return load_image(f"https://github.com/{username}.png?size={size}", size)


# ---------------------------------------------------------------------------
# Dados fictícios (úteis para pré-visualizar localmente / CI)
# ---------------------------------------------------------------------------
_MOCK_REPOS = [
    "api-orders", "django-blog", "portfolio", "todo-api", "pomodoro-cli",
    "infra-docs", "ml-notebooks", "ecommerce-api", "pixel-art", "dotfiles",
    "web-scraper", "financas-cli", "imgs-utils", "nest-crm", "scripts",
]


def mock_items(data: str) -> list[dict]:
    rng = random.Random(42)
    if data == "repos":
        items = [
            {"name": name, "count": rng.randint(100, 40000)} for name in _MOCK_REPOS
        ]
    elif data == "followers":
        items = [{"name": f"user{i:03d}", "count": 1} for i in range(1, 40)]
    else:
        items = [
            {"name": f"S{i + 1:02d}", "count": rng.randint(0, 25)} for i in range(52)
        ]
        items = [i for i in items if i["count"] > 0]
    return rank_items(items)
