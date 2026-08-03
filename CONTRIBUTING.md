# Contribuindo

Obrigado por ajudar o github-gif-maker! Projeto propositalmente enxuto.

## Estrutura

```
generator/
  main.py        # CLI: --user --limit --output --mock --preview
  api.py         # busca de repositórios públicos (REST) + dados fictícios
  asteroids.py   # o jogo: nave atira nos repositórios, um cometa por vez
  render.py      # utilidades: fontes e gravação do GIF
```

## Como o jogo funciona

- Cada repositório vira um cometa; cometas maiores = repositórios maiores
  (tamanho em KB, por ranking) com nível 1-4.
- Os cometas aparecem **um por vez** (`ts = INTRO + i * CYCLE`, em que
  `CYCLE = TRAVEL + EXPLOSION_MS + GAP`), sequencialmente.
- A saída é decimada (`DECIMATE = 2`) para ~12fps, mantendo o GIF leve.

## Validar

```bash
python -m generator --mock --preview
```

Testes de CI (`.github/workflows/test.yml`) renderizam o GIF com dados
fictícios nas versões 3.9, 3.11 e 3.12 do Python.

## Convenções

- Fuso padrão `America/Sao_Paulo`, textos em pt-br.
- Sem dependências além do Pillow — Python 3.9+ (`from __future__ import
  annotations` para tipos modernos).
- GIFs devem ficar leves (o alvo é ~2MB para 15 cometas).
