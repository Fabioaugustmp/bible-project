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
| `BIBLE_PUBLIC_ORIGIN` | vazio | web (`.env`) | endereço público com https; vazio = uso local. Com ele, todo pedido exige o código |
| `BIBLE_ACCESS_TOKEN` | vazio (usa `data/acesso-celular.txt`) | web (`.env`) | código de acesso, pelo menos 16 caracteres |
| `CLOUDFLARE_TUNNEL_TOKEN` | vazio | tunnel (`.env`) | token do túnel da Cloudflare (perfil `tunnel`) |
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

## Publicação (https://biblia.famptech.com.br, pelo túnel da Cloudflare)

Decisão D034. Frontend e API ficam no mesmo serviço `web` (um processo Python, rotas
`/` e `/api/*`); o túnel encaminha tudo para ele. Nada precisa de porta aberta no
roteador: o `cloudflared` só faz saída para a Cloudflare.

Passos (uma vez):

1. No servidor, na pasta do projeto, copie o modelo e preencha:

   ```bash
   cp .env.example .env
   python3 -c "import secrets; print(secrets.token_urlsafe(24))"
   ```

   Cole o resultado em `BIBLE_ACCESS_TOKEN` (pelo menos 16 caracteres). Em
   `CLOUDFLARE_TUNNEL_TOKEN`, cole o token do túnel (passo 2).

2. No painel Zero Trust da Cloudflare, em Networks > Tunnels, abra o túnel
   existente. Em **Public Hostname**, crie ou ajuste a rota:
   - Subdomain/domain: `biblia` / `famptech.com.br`
   - Service: `HTTP` e `web:8377`

   Se o túnel já roda como serviço no próprio servidor (fora do Docker), a
   rota pode apontar para `http://localhost:8377`: o `web` publica essa porta
   em `127.0.0.1`. Nesse caso não suba o perfil `tunnel`, para não ter dois
   conectores com o mesmo token.

3. Suba a aplicação com o túnel:

   ```bash
   docker compose --profile tunnel up -d --build
   ```

4. Abra https://biblia.famptech.com.br/?t=SEU_CODIGO uma vez. O navegador guarda
   um cookie `HttpOnly` e `Secure`, e a partir daí o `?t=` não é mais necessário.

Conferir:

```bash
docker compose ps
docker compose logs tunnel --tail 20
curl -s -o /dev/null -w "%{http_code}\n" https://biblia.famptech.com.br/
```

Sem o código, a resposta é `403`. Com ele, a página abre.

Como funciona a segurança:

- Com `BIBLE_PUBLIC_ORIGIN` definido, **todo** pedido exige o código, inclusive
  os de `/api/*` e os que vêm do túnel. Sem `BIBLE_PUBLIC_ORIGIN`, o comportamento é o de uso local.
- Escritas em `/api/user/*` só são aceitas com Origin `https://biblia.famptech.com.br`.
- O código não aparece no registro do servidor (`?t=***`).
- Recomendado: ative o **Cloudflare Access** (login por e-mail) na frente do
  hostname, no painel Zero Trust. Isso é uma configuração da Cloudflare, não do repositório.
- O código é único e não expira. Para trocá-lo, altere `BIBLE_ACCESS_TOKEN` no `.env`,
  rode `docker compose up -d web` e refaça o passo 4 nos aparelhos.

Atenção: `library.db` contém o texto de módulos com direito autoral (D007). Antes
de publicar o texto integral, confira a licença de cada módulo (T52).

## Limites (leia antes de expor)

- **Acesso só pelo código de acesso.** Não há usuários nem senhas separados, e o
  código não expira. Os dados pessoais (`user.db`) ficam acessíveis a quem tiver o código.
- **Sem avaliação de segurança formal** (ver `docs/RELATORIO-PRIMEIRA-VERSAO.md`,
  Parte 3). A publicação pelo túnel (D034) depende do código de acesso e do Cloudflare Access.
- A mensagem de aviso da busca por sentido ainda cita o comando do Windows
  (`.venv-bench`); dentro do contêiner, o perfil `semantic` é o caminho certo.
- A imagem não tem verificação de saúde (`healthcheck`) nem testes; os testes
  rodam com `python -m unittest discover -s tests` fora do contêiner.
- O contêiner `embed` usa CPU. A busca por sentido fica mais lenta que na GPU.
- **Estado da verificação:** a imagem `web` foi construída e testada (biblioteca, passagem, busca, escrita com Origin, rejeição de Host estranho com 403, e o aviso de sentido sem o serviço). A imagem `embed` **não foi construída** nesta máquina: o `pip` dentro do contêiner falhou com erro de SSL ao baixar pacotes de `files.pythonhosted.org`, enquanto o host alcança esse endereço. Isso costuma ser o MTU da rede do Docker Desktop. Se acontecer de novo, ajuste o MTU no Docker ou construa a imagem em outra máquina, e depois rode `docker compose --profile semantic up -d`.
