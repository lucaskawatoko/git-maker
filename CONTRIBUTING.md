# Contribuindo

Obrigado por ajudar o git-maker! Projeto propositalmente enxuto.

## Estrutura

```
generator/
  main.py            # CLI: --user --data --color --food --output --mock --preview --ascii --width
  api.py             # busca de repos (REST) / contribuições (GraphQL) / seguidores (REST) + avatares
  palettes.py        # deriva a paleta (cobra, comida) a partir de cores hex
  snake.py           # o jogo: cobrinha auto-play (BFS) comendo os dados
  ascii_art.py       # foto ASCII: avatar -> grade -> GIF com efeito de impressão
  render.py          # utilidades: fontes e gravação do GIF (com transparência)
  render_context.py  # contexto compartilhado entre camadas
```

## Como o jogo funciona

- Cada item (repositório, semana de contribuição ou seguidor) vira uma comida
  na grade.
- A cobrinha é auto-play: `find_path` usa BFS para ir até a comida; o `count`
  de cada item soma no SCORE (estrelas em `repos`, contribuições em `commits`,
  1 ponto por seguidor).
- A cobrinha **cresce** a cada comida (`pending += 1` no `simulate`).
- As linhas 0-2 da arena são a **faixa do HUD** (`PLAY_ROW0 = 3`): a cobrinha
  e as comidas só ocupam as linhas 3 em diante (limite invisível).
- A **cabeça da cobrinha** usa o avatar do usuário (`api.fetch_avatar`,
  `https://github.com/{user}.png`) recortado no formato da célula; se o
  download falhar, cai para a cor derivada.
- Em `followers`, cada comida é o **avatar do seguidor** (`api.load_image` +
  `ctx.avatars`); sem avatar, cai para o círculo da cor `food`.
- A simulação é **seedável**: sem `--seed`, o caminho é aleatório a cada
  execução (`random.Random(randrange)`); com `--seed N`, é reproduzível.
- **Sem intro/outro com fade**: não há título na abertura nem fade para
  transparente no fim (evita a "piscada" no loop do GIF); o jogo começa logo
  e termina segurando o último frame.
- O fundo é **transparente** (RGBA); só a borda da arena é desenhada. O GIF é
  salvo com índice de transparência (`render.save_gif` converte RGBA → P).
- A paleta é derivada da `color` (hex) em `palettes.build_palette`, com a cor
  da comida (`food`) sobreponível.
- `MAX_ITEMS = 25` limita a comida para o GIF ficar leve.

## Foto ASCII (`ascii_art.py`)

- `to_grid` converte o avatar (RGBA) em grade de caracteres pela luminância
  (rampa ` .:-=+*#%@`), com a proporção corrigida pela célula da fonte
  (DejaVuSansMono; altura da célula = `ascent`).
- Cada linha é pré-renderizada uma vez; os frames mostram o "cabeçote"
  revelando caractere a caractere, de cima para baixo.
- O último frame (foto completa) recebe uma `duration` maior para o hold —
  **nunca** use frames duplicados no fim: o Pillow os mescla e corrompe o GIF
  transparente.
- O GIF é salvo com **paleta global fixa** (`render.save_gif_fixed`): quantizar
  cada frame isolado corrompe as cores quando a cor dominante muda entre
  frames. Use-o para GIFs transparentes; `save_gif` (quantize por frame) serve
  para GIFs opacos (a cobrinha).
- Não há fade-out: o loop corta da foto completa de volta para o começo da
  impressão (sem piscada). O Pillow corrompe o arquivo se frames com
  transparência parcial (`putalpha`) aparecem no fim.

## Validar

```bash
python -m generator --mock --preview
python -m generator --data followers --mock --preview
```

Testes de CI (`.github/workflows/test.yml`) renderizam a cobrinha com dados
fictícios nas versões 3.9, 3.11 e 3.12 do Python, incluindo cores hex,
seguidores, paginação de `fetch_repos`/`fetch_followers` e a progressão da
foto ASCII.

## Convenções

- Fuso padrão `America/Sao_Paulo`, textos em pt-br.
- Sem dependências além do Pillow — Python 3.9+ (`from __future__ import
  annotations` para tipos modernos).
- GIFs devem ficar leves (o alvo é ~2MB).
