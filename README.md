# github-gif-maker

Gera um GIF de perfil estilo **Asteroids** com os seus repositórios públicos
virando cometas: a nave gira, atira com laser e destrói cada repositório, um
por vez. Tudo **dentro do GitHub Actions** — sem servidor, sem hosting.

![asteroids](imgs/samples/asteroids.gif)

## Como usar

Adicione o workflow abaixo em `.github/workflows/contribution-gif.yml` do seu
perfil/repositório e ajuste o `username`:

```yaml
name: contribution-gif

on:
  push:
    branches: [main]
  schedule:
    - cron: "0 0 * * *" # gera novamente todo dia

permissions:
  contents: write

jobs:
  gif:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Generate GIF
        uses: lucaskawatoko/git-maker/.github/actions/generate-gifs@main
        with:
          username: "lucaskawatoko" # seu usuário

      - name: Commit
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add imgs/contribution-animation.gif
          git diff --cached --quiet || git commit -m "chore: atualiza gif de contribuição"
          git push
```

Depois é só referenciar no seu README:

```markdown
![contributions](imgs/contribution-animation.gif)
```

> Os repositórios são buscados na API pública do GitHub, sem token. No jogo os
> cometas aparecem **um por vez**: o próximo só nasce depois que o atual é
> destruído.

## Inputs

| Input      | Padrão                     | Descrição                                       |
| ---------- | -------------------------- | ----------------------------------------------- |
| `username` | `lucaskawatoko`            | Usuário do GitHub com os repositórios           |
| `limit`    | `0`                        | Máximo de cometas (0 = todos, um por vez)       |
| `output`   | `imgs/contribution-animation.gif` | Caminho do GIF gerado                    |

## Desenvolvimento local

```bash
pip install -r requirements.txt

# dados fictícios (pré-visualizar)
python -m generator --mock --preview

# dados reais
python -m generator --user lucaskawatoko

# limita a quantidade de cometas (0 = todos)
python -m generator --user lucaskawatoko --limit 10
```

## Licença

MIT — veja o arquivo [LICENSE](LICENSE).
