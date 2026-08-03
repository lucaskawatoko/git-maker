from __future__ import annotations

import json
import random
import sys
from urllib.request import Request, urlopen

_USER_AGENT = "github-gif-maker"
_TIMEOUT = 30


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
    """Repositórios públicos do usuário via REST (sem token), paginado."""
    items: list[dict] = []
    page = 1
    while page <= 10:
        url = (f"https://api.github.com/users/{username}/repos"
               f"?per_page=100&page={page}&type=owner&sort=updated")
        try:
            nodes = _get_json(url)
        except Exception as exc:  # noqa: BLE001
            raise SystemExit(f"Falha ao buscar repositórios de @{username}: {exc}") from exc
        if isinstance(nodes, dict) and nodes.get("message"):
            raise SystemExit(f"Erro da API GitHub: {nodes['message']}")
        if not nodes:
            break
        items.extend(nodes)
        if len(nodes) < 100:
            break
        page += 1
    repos = [{"name": n.get("name", ""), "count": n.get("size", 0) or 0} for n in items]
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
    else:
        items = [
            {"name": f"S{i + 1:02d}", "count": rng.randint(0, 25)} for i in range(52)
        ]
        items = [i for i in items if i["count"] > 0]
    return rank_items(items)
