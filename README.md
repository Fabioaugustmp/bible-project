# Biblioteca Bíblica

Leitor e ferramenta de estudo que usa os módulos do e-Sword e do theWord já
instalados, com interface nova e busca unificada. Roda local e offline.

## Como usar

Requer Python 3.11 ou mais novo; nenhuma dependência externa.

Importar módulos (os originais só são lidos, nunca alterados):

```bash
python importer/build.py --out data/library.db modules-sample
```

Conferir a base gerada:

```bash
python importer/verify.py data/library.db
```

Abrir o aplicativo em http://localhost:8377:

```bash
python app/server.py
```

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `importer/` | leitura dos formatos e gravação da base única |
| `app/` | servidor local e interface web |
| `docs/` | [backlog](docs/BACKLOG.md), [plano](docs/PLANO.md), [decisões](docs/DECISOES.md), [formatos](docs/FORMATOS.md) |
| `data/` | base gerada e relatório de importação (fora do git) |
| `modules-sample/` | módulos de amostra (fora do git) |
