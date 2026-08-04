# git-maker

Gera o GIF da **cobrinha** comendo os seus dados do GitHub (repositórios,
contribuições ou seguidores), igualzinho ao famoso snake de contribuição — mas
**totalmente personalizável**: cor da cobrinha e da comida em qualquer hex,
com **fundo transparente** (o GIF se adapta ao tema do seu README) e com o seu
**avatar na cabeça** da cobrinha. Tudo **dentro do GitHub Actions** — sem
servidor, sem hosting.

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
          data: "repos"              # repos, commits ou followers
          color: "#aac8d6"           # cor da cobrinha (hex)
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

| Input      | Padrão                 | Descrição                                            |
| ---------- | ---------------------- | ---------------------------------------------------- |
| `username` | `lucaskawatoko`        | Usuário do GitHub com os dados                       |
| `data`     | `repos`                | Comida da cobrinha: `repos`, `commits` ou `followers` |
| `color`    | `#3fb950`              | Cor da cobrinha em hex (`#rrggbb`)                   |
| `food`     | `#ff6b4a`              | Cor da comida em hex                                 |
| `output`   | `imgs/contribution-animation.gif` | Caminho do GIF gerado                    |

> O fundo é **transparente** — o GIF usa o fundo do seu README (claro ou
> escuro). A única moldura é a borda da arena.

## Avatar e seguidores

- A **cabeça** da cobrinha é sempre o seu avatar (baixado de
  `https://github.com/{username}.png`). Se o download falhar, cai para a cor
  derivada da `color`.
- Com `data: followers`, cada comida é o **avatar de um seguidor** — a cobrinha
  "come" os seus seguidores, e cada um vale 1 ponto. Sem avatar, cai para o
  círculo da cor `food`.

## Cores personalizadas

Qualquer cor em hex funciona. A cabeça é derivada automaticamente da `color`
escolhida para manter contraste — uma cor clara como `#aac8d6` (azul
calcinha) ganha cabeça mais escura, uma cor escura ganha cabeça mais clara.

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
  --color "#aac8d6" --food "#e5534b"

# cobrinha roxa comendo seguidores (com avatar na cabeça)
python -m generator --user lucaskawatoko --data followers \
  --color "#a371f7" --food "#3fb950"
```

## Licença

MIT — veja o arquivo [LICENSE](LICENSE).
