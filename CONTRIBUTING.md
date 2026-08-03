# Contribuindo

Obrigado por ajudar o github-gif-maker! Guia curto:

## Estrutura

```
generator/
  main.py            # CLI: --user --style --data --color --avatar --output --mock
  api.py             # busca de dados (REST público + GraphQL) e mocks
  avatar.py          # baixa o avatar do usuário
  palettes.py        # presets de cor + conversão/derivação de hex
  render_context.py  # contexto compartilhado entre estilos
  render.py          # utilidades: fontes, crop circular, save GIF
  styles/
    __init__.py      # registro de estilos
    asteroids.py     # estilo Asteroids
    snake.py         # estilo Snake
```

## Adicionar um estilo

1. Crie `generator/styles/novo.py`.
2. Defina `def render(ctx: RenderContext) -> None` e decore com
   `@register("novo")`.
3. Use `ctx.palette`, `ctx.items` (lista de `{"name", "count", "level"}` já
   ordenada), `ctx.avatar`, `ctx.data_name` e `ctx.username`. Salve com
   `save_gif(frames, ctx.output, ctx.fps, ctx.preview)`.

## Adicionar uma fonte de dados

1. Adicione uma função em `generator/api.py` retornando `list[dict]` com
   `{"name", "count"}`.
2. Chame `rank_items(...)` antes de retornar (ordena por `count` e atribui
   nível 1-4).
3. Registre em `main.py` (`DATA_CHOICES`, `_load_items`) e adicione um mock em
   `mock_items`.

## Validar

```bash
python -m generator --style asteroids --data repos --mock --preview
python -m generator --style snake --data commits --mock --preview
```

Testes de CI (`.github/workflows/test.yml`) rodam todas as combinações
estilo×dado com `--mock` nas versões 3.9, 3.11 e 3.12 do Python.

## Convenções

- Fuso padrão `America/Sao_Paulo`, textos em pt-br.
- Sem dependências além do Pillow — Python 3.9+ (`from __future__ import
  annotations` para tipos modernos).
- GIFs devem ficar leves: em estilos com muitos itens, limite a quantidade
  (veja `MAX_ITEMS` no snake) e garanta terminação com limites de passos.
