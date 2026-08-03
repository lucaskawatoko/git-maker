from __future__ import annotations

import random
from urllib.request import Request, urlopen

_USER_AGENT = "github-gif-maker"
_TIMEOUT = 30


def rank_repos(nodes: list[dict]) -> list[dict]:
    """Ordena por tamanho (KB) e atribui nível 1-4 por ranking."""
    repos = [{
        "name": n["name"],
        "stars": n.get("stargazers_count", 0) or 0,
        "size": n.get("size", 0) or 0,
    } for n in nodes]
    repos.sort(key=lambda r: r["size"], reverse=True)
    total = len(repos)
    for i, repo in enumerate(repos):
        repo["level"] = 1 + min(3, (i * 4) // max(1, total)) if total else 1
    return repos


def fetch_repos(username: str) -> list[dict]:
    """Repositórios públicos do usuário via REST (sem token)."""
    url = f"https://api.github.com/users/{username}/repos?per_page=100&type=owner&sort=updated"
    req = Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urlopen(req, timeout=_TIMEOUT) as resp:
            import json
            nodes = json.load(resp)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Falha ao buscar repositórios de @{username}: {exc}") from exc
    if isinstance(nodes, dict) and nodes.get("message"):
        raise SystemExit(f"Erro da API GitHub: {nodes['message']}")
    return rank_repos(nodes)


def mock_repos() -> list[dict]:
    names = [
        "api-orders", "django-blog", "portfolio", "todo-api", "pomodoro-cli",
        "infra-docs", "ml-notebooks", "ecommerce-api", "pixel-art", "dotfiles",
        "web-scraper", "financas-cli", "imgs-utils", "nest-crm", "scripts",
    ]
    rng = random.Random(42)
    nodes = [
        {"name": name, "stargazers_count": rng.randint(0, 30), "size": rng.randint(100, 40000)}
        for name in names
    ]
    return rank_repos(nodes)
