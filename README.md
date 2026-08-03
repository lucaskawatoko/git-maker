# git-maker

Gera o GIF da **cobrinha** comendo os seus dados do GitHub (repositórios ou
contribuições), igualzinho ao famoso snake de contribuição — mas **totalmente
personalizável**: cor da cobrinha, fundo e comida em qualquer hex. Tudo
**dentro do GitHub Actions** — sem servidor, sem hosting.

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

      - name: Generate snake GIF
        uses: lucaskawatoko/git-maker/.github/actions/generate-gifs@main
        with:
          username: "lucaskawatoko"  # seu usuário
          data: "repos"              # repos ou commits
          color: "#aac8d6"           # cor da cobrinha (hex)
          background: "#0d1117"      # cor de fundo (hex)
          food: "#e5534b"            # cor da comida (hex)

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

> Para `data: commits` (contribuições) a action usa a API GraphQL, que exige
> um token. Sem token, as contribuições caem para dados fictícios. Defina o
> secret `GH_TOKEN` no repositório para usar dados reais.

## Inputs

| Input        | Padrão                 | Descrição                                            |
| ------------ | ---------------------- | ---------------------------------------------------- |
| `username`   | `lucaskawatoko`        | Usuário do GitHub com os dados                       |
| `data`       | `repos`                | Comida da cobrinha: `repos` ou `commits`             |
| `color`      | `#3fb950`              | Cor da cobrinha em hex (`#rrggbb`)                   |
| `background` | *(derivada da cor)*    | Cor de fundo em hex. Vazio deriva da cor da cobrinha |
| `food`       | `#ff6b4a`              | Cor da comida em hex                                 |
| `output`     | `imgs/contribution-animation.gif` | Caminho do GIF gerado                    |

## Cores personalizadas

Qualquer cor em hex funciona. A paleta (fundo, grade, estrelas, cabeça) é
derivada automaticamente da `color` escolhida para manter contraste — uma cor
clara como `#aac8d6` (azul calcinha) ganha cabeça mais escura, uma cor escura
ganha cabeça mais clara.

Sugestões de hex:

| Cor            | Hex        |
| -------------- | ---------- |
| Verde GitHub   | `#3fb950`  |
| Azul calcinha  | `#aac8d6`  |
| Vermelho       | `#e5534b`  |
| Roxo           | `#a371f7`  |
| Amarelo        | `#e3b341`  |
| Rosa           | `#f778ba`  |

## Desenvolvimento local

```bash
pip install -r requirements.txt

# dados fictícios (pré-visualizar)
python -m generator --mock --preview

# dados reais (repos)
python -m generator --user lucaskawatoko

# cobrinha azul calcinha comendo contribuições
python -m generator --user lucaskawatoko --data commits \
  --color "#aac8d6" --background "#0d1117" --food "#e5534b"
```

## Licença

MIT — veja o arquivo [LICENSE](LICENSE).
