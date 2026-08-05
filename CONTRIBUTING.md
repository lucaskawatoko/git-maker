# Contribuindo

Obrigado por ajudar o git-maker! Projeto propositalmente enxuto.

## Estrutura

```
generator/
  main.py            # CLI: --user --data --color --food --output --mock --preview --smooth/--no-smooth
  api.py             # busca de repos (REST) / contribuições (GraphQL) / seguidores (REST) + avatares
  palettes.py        # deriva a paleta (cobra, comida) a partir de cores hex
  snake.py           # o jogo: cobrinha auto-play (BFS) comendo os dados
  render.py          # utilidades: fontes e gravação do GIF (com transparência)
  render_context.py  # contexto compartilhado entre camadas
```

## Como o jogo funciona

- Cada item (repositório, semana de contribuição ou seguidor) vira uma comida
  na grade.
- A cobrinha é auto-play: `find_path` usa BFS para ir até a comida; o `count`
  de cada item soma no SCORE (estrelas em `repos`, contribuições em `commits`,
  1 ponto por seguidor).
- A cobrinha **cresce** a cada comida (`pending += 1` no `simulate`). O BFS
  recebe `growing = pending > 0`: enquanto a cobra cresce a cauda não sai na
  jogada, então ela é tratada como célula ocupada — evita planejar caminho que
  atravessa a própria cauda parada (`_fallback_move` usa a mesma regra).
- A comida é sorteada com `_spawn_food(rng, occupied, exclude)`: a célula da
  comida anterior fica de fora para não repetir posição.
- As linhas 0-2 da arena são a **faixa do HUD** (`PLAY_ROW0 = 3`): a cobrinha
  e as comidas só ocupam as linhas 3 em diante (limite invisível).
- A **cabeça da cobrinha** usa o avatar do usuário (`api.fetch_avatar`,
  `https://github.com/{user}.png`) recortado no formato da célula; se o
  download falhar, cai para a cor derivada.
- Em `followers`, cada comida é o **avatar do seguidor** (`api.load_image` +
  `ctx.avatars`); sem avatar, cai para o círculo da cor `food`. Em
  `repos`/`commits` a comida **escala pelo `level`** (1–4, de
  `api.rank_items`): `half = 6 + level`.
- O fim distingue **`CONCLUÍDO!`** (comeu todos os itens) de **`TEMPO LIMITE`**
  (estourou `MAX_TOTAL` frames): o último estado guarda `finished = idx >= len(items)`.
- **Movimento interpolado**: com `smooth` (padrão on) cada passo da simulação
  vira `SMOOTH` sub-frames interpolando corpo e comida (`_interp_body`, que
  segue `b[i] == a[i-1]` e segura/converge a cauda em mudanças de comprimento);
  o `fps` efetivo vira `ctx.fps * SMOOTH`. O teto de frames renderizados é
  `MAX_RENDER_FRAMES` (proteção de memória).
- **Feedback ao comer**: o estado do "eat" grava `{"gain", "cell"}`; o render
  mantém popups ativos (anel em expansão + texto `+N` subindo e sumindo) por
  `POPUP_FRAMES` sub-frames.
- A simulação é **seedável**: sem `--seed`, o caminho é aleatório a cada
  execução (`random.Random(randrange)`); com `--seed N`, é reproduzível.
- **Sem intro/outro com fade**: não há título na abertura nem fade para
  transparente no fim (evita a "piscada" no loop do GIF); o jogo começa logo
  e termina segurando o último frame.
- O fundo é **transparente** (RGBA); só a borda da arena é desenhada. O GIF é
  salvo com índice de transparência (`render.save_gif` converte RGBA → P).
- A paleta é derivada da `color` (hex) em `palettes.build_palette`, com a cor
  da comida (`food`) sobreponível.
- `MAX_ITEMS = 25` limita a comida para o GIF ficar leve; quando há mais
  dados, o HUD mostra `TOP 25: X/25` e a CLI avisa na geração.

## Validar

```bash
python -m generator --mock --preview
python -m generator --data followers --mock --preview
python -m generator --mock --no-smooth --preview
```

Testes de CI (`.github/workflows/test.yml`) renderizam a cobrinha com dados
fictícios nas versões 3.9, 3.11 e 3.12 do Python, incluindo cores hex,
seguidores, smooth/no-smooth, `finished`, `_spawn_food` com exclusão e a
paginação de `fetch_repos`/`fetch_followers`.

## Convenções

- Fuso padrão `America/Sao_Paulo`, textos em pt-br.
- Sem dependências além do Pillow — Python 3.9+ (`from __future__ import
  annotations` para tipos modernos).
- GIFs devem ficar leves (o alvo é ~2MB).
