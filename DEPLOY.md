# Implantação com contêineres

Esta página explica como subir a Biblioteca Bíblica com Docker, o que vai em cada
contêiner e o que **não** vai. Leia a seção "Limites" antes de expor a aplicação
em qualquer rede.

## O que vai para a imagem e o que não vai

| Item | Onde fica | Por quê |
|---|---|---|
| Código (`app/`, `importer/`) | imagem | é o programa |
| Módulos do e-Sword e do theWord | **fora** (só no host, lidos pelo importador) | têm direito autoral (D007) |
| `data/library.db` (biblioteca gerada) | pasta `data/` do host, montada em `/data` | grande (cerca de 1,5 GB) e derivada dos módulos |
| `data/user.db` (notas, estudos, diário...) | `data/` do host, montada em `/data` | dados pessoais; criado na primeira execução |
| `data/embeddings.db` e `data/hf-cache/` | `data/` do host (só para o perfil `semantic`) | vetores e o modelo BGE-M3 (cerca de 5 GB) |

## Pré-requisitos

- Docker Desktop (Windows, Mac) ou Docker Engine (Linux), com Compose v2.
- A pasta `data/` com `library.db` gerada. Ela não vem no repositório. Gere-a na
  máquina onde estão os módulos:

  ```bash
  python importer/build.py --out data/library.db "C:\Program Files (x86)\e-Sword" "C:\ProgramData\The Word" "%APPDATA%\The Word"
  python importer/verify.py data/library.db
  ```

## Subir a aplicação

Só leitura, estudo e busca por palavra (o caso comum):

```bash
docker compose up -d --build web
```

Com busca por sentido e a aba "Parecidas" (exige `data/embeddings.db` e `data/hf-cache/`):

```bash
docker compose --profile semantic up -d --build
```

Abra http://localhost:8377. A porta é publicada só em `127.0.0.1`: outro
aparelho na rede não alcança a aplicação por esta configuração.

Conferir:

```bash
docker compose ps
curl -s http://127.0.0.1:8377/api/library | head -c 200
docker compose logs web --tail 20
```

Parar:

```bash
docker compose down
```

Os dados ficam em `./data` e não são apagados por `down`.

## Divisão das APIs por serviço

| Serviço | Porta | Exposto | Endpoints | Função |
|---|---|---|---|---|
| `web` | 8377 | `127.0.0.1:8377` no host | `/` e arquivos estáticos; `/api/library`, `/api/chapter`, `/api/passage`, `/api/verse`, `/api/item`, `/api/search`, `/api/word`, `/api/strong` (ver `API` em `app/server.py`); `/api/xref-graph`, `/api/commentary`, `/api/titles`, `/api/topic`, `/api/suggest` | leitura da biblioteca e busca por palavra; faz a ponte para a busca por sentido |
| `web` (escrita) | 8377 | mesma | `/api/user/*` (GET para leitura, POST para escrita) | estudos, notas, tópicos, diário, memorização, conjuntos, leituras, mapa e linha do tempo; dados em `user.db`; POST só aceito com Origin e Host conferidos |
| `embed` (perfil `semantic`) | 8378 | **não** (só rede interna do compose) | `GET /health`, `POST /search`, `POST /similar` | busca por sentido com BGE-M3 (`/api/semantic`, `/api/similar` e a parte por sentido de `/api/topic` chamam este serviço) |

Sem o perfil `semantic`, as rotas de sentido respondem `available: false` com um
aviso, e a busca por palavra continua funcionando.

## Configuração (variáveis de ambiente)

| Variável | Padrão | Onde | Para quê |
|---|---|---|---|
| `BIBLE_DATA_DIR` | `data/` do projeto | web, embed | pasta com `library.db`, `user.db`, `embeddings.db`, `hf-cache/` |
| `BIBLE_BIND` | `127.0.0.1` | web | endereço de escuta (no contêiner: `0.0.0.0`) |
| `BIBLE_ALLOWED_HOSTS` | vazio | web | nomes extras aceitos no cabeçalho Host, separados por vírgula (ex.: `meu-host:8377`) |
| `BIBLE_EMBED_URL` | `http://127.0.0.1:8378` | web | endereço do serviço de sentido |
| `BIBLE_EMBED_HOST`, `BIBLE_EMBED_PORT` | `127.0.0.1`, `8378` | embed | escuta do serviço de sentido |

O servidor também aceita `--bind`, `--port`, `--db` e `--allow-host` na linha de comando.

## Backup

Pare a aplicação antes de copiar `user.db` (é um SQLite):

```bash
docker compose stop web
cp data/user.db backup/user-$(date +%F).db
docker compose start web
```

`library.db` pode ser gerado de novo pelo importador; não precisa de backup se os
módulos continuam instalados.

## Atualizar

```bash
git pull
docker compose up -d --build
```

Os dados em `./data` continuam os mesmos. Se o esquema de `user.db` mudar, as
tabelas novas são criadas sozinhas (`create table if not exists`).

## Limites (leia antes de expor)

- **Sem autenticação.** A aplicação foi feita para uso pessoal. Quem alcança a
  porta lê e escreve nos dados. Por isso a porta é publicada só em `127.0.0.1`.
- **Sem HTTPS.** Atrás de um proxy HTTPS, as escritas em `/api/user/*` falham,
  porque a conferência de Origin espera `http://` com o mesmo Host. Isso precisa de
  alteração no código antes de uma publicação real.
- **Sem avaliação de segurança formal** (ver `docs/RELATORIO-PRIMEIRA-VERSAO.md`,
  Parte 3). Não é recomendado colocar a aplicação na internet nesta versão.
- A mensagem de aviso da busca por sentido ainda cita o comando do Windows
  (`.venv-bench`); dentro do contêiner, o perfil `semantic` é o caminho certo.
- A imagem não tem verificação de saúde (`healthcheck`) nem testes; os testes
  rodam com `python -m unittest discover -s tests` fora do contêiner.
- O contêiner `embed` usa CPU. A busca por sentido fica mais lenta que na GPU.
- **Estado da verificação:** a imagem `web` foi construída e testada (biblioteca, passagem, busca, escrita com Origin, rejeição de Host estranho com 403, e o aviso de sentido sem o serviço). A imagem `embed` **não foi construída** nesta máquina: o `pip` dentro do contêiner falhou com erro de SSL ao baixar pacotes de `files.pythonhosted.org`, enquanto o host alcança esse endereço. Isso costuma ser o MTU da rede do Docker Desktop. Se acontecer de novo, ajuste o MTU no Docker ou construa a imagem em outra máquina, e depois rode `docker compose --profile semantic up -d`.
