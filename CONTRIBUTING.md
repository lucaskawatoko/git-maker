# Contribuindo

Obrigado por ajudar o git-maker! Projeto propositalmente enxuto.

## Estrutura

```
generator/
  main.py            # CLI: --user --data --color --food --output --mock --preview
  api.py             # busca de repositórios (REST) / contribuições (GraphQL) + dados fictícios
  palettes.py        # deriva a paleta (cobra, comida) a partir de cores hex
  snake.py           # o jogo: cobrinha auto-play (BFS) comendo os dados
  render.py          # utilidades: fontes e gravação do GIF (com transparência)
  render_context.py  # contexto compartilhado entre camadas
```

## Como o jogo funciona

- Cada item (repositório ou semana de contribuição) vira uma comida na grade.
- A cobrinha é auto-play: `find_path` usa BFS para ir até a comida; o `count`
  de cada item soma no SCORE (estrelas em `repos`, contribuições em `commits`).
- A cobrinha **cresce** a cada comida (`pending += 1` no `simulate`).
- As linhas 0-2 da arena são a **faixa do HUD** (`PLAY_ROW0 = 3`): a cobrinha
  e as comidas só ocupam as linhas 3 em diante (limite invisível).
- O fundo é **transparente** (RGBA); só a borda da arena é desenhada. O GIF é
  salvo com índice de transparência (`render.save_gif` converte RGBA → P).
- A paleta é derivada da `color` (hex) em `palettes.build_palette`, com a cor
  da comida (`food`) sobreponível.
- `MAX_ITEMS = 25` limita a comida para o GIF ficar leve.

## Validar

```bash
python -m generator --mock --preview
```

Testes de CI (`.github/workflows/test.yml`) renderizam a cobrinha com dados
fictícios nas versões 3.9, 3.11 e 3.12 do Python, incluindo cores hex.

## Convenções

- Fuso padrão `America/Sao_Paulo`, textos em pt-br.
- Sem dependências além do Pillow — Python 3.9+ (`from __future__ import
  annotations` para tipos modernos).
- GIFs devem ficar leves (o alvo é ~2MB).
