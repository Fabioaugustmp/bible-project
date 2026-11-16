# Plano de execução

Aplicativo de estudo bíblico que lê os módulos já instalados do e-Sword e do
theWord, com interface nova e busca moderna (por palavra e por significado).

Estado de cada fase: `pendente`, `em andamento`, `concluída`. Este arquivo é
atualizado no mesmo commit que conclui a fase.

## Princípios

- **Os módulos originais nunca são alterados.** O importador só lê; tudo é
  convertido para uma base própria (`data/library.db`).
- **A base é descartável e reprodutível.** Rodar o importador de novo sobre os
  mesmos arquivos gera o mesmo conteúdo.
- **Dados do usuário (notas, marcações) ficam em base separada**, para que
  reimportar a biblioteca nunca os apague.
- **Tudo roda local e offline.**

## Rastreabilidade

| O quê | Onde fica |
|---|---|
| Histórico de mudanças do código | commits git, um por etapa concluída |
| Decisões e seus motivos | [DECISOES.md](DECISOES.md), numeradas e datadas |
| O que foi descoberto sobre cada formato | [FORMATOS.md](FORMATOS.md) |
| Procedência de cada módulo importado | tabela `modules` na base: caminho de origem, SHA-256, tamanho, data do arquivo, versão do importador, contagens |
| O que foi ignorado e por quê | tabela `import_log` na base e `data/import-report.json` |
| Procedência de cada texto exibido | cada versículo, comentário e verbete aponta para o módulo de origem e a chave original (linha ou id) |
| Estado de cada fase | este arquivo |

## Fases

### Fase 0 — Reconhecimento · concluída

- Inventário das instalações (e-Sword: 23 módulos; theWord: cerca de 110).
- Nove módulos de amostra copiados para `modules-sample/`.
- Formatos validados; resultado em [FORMATOS.md](FORMATOS.md).

### Fase 1 — Importador e base única · em andamento

Entregas:
- `importer/`: leitura de `.bblx`, `.cmtx`, `.dctx` (e-Sword) e `.ont`, `.ot`,
  `.nt`, `.cmt.twm`, `.dct.twm` (theWord).
- Base SQLite com Bíblias, comentários, verbetes, citações de versículos e
  índice de busca por palavra (FTS5, ignorando acentos).
- Registro de procedência e relatório de importação.

Critérios de aceite:
- Cada Bíblia completa importada tem 31.102 versículos (7.957 se só NT).
- João 3:16 e Gênesis 1:1 conferem com o texto do módulo original.
- Nenhum resíduo de marcação RTF no texto (verificação automática).
- Módulos ilegíveis aparecem no relatório com o motivo, sem interromper os demais.

### Fase 2 — Leitor e painel do versículo · pendente

Entregas:
- Servidor local (`app/server.py`) com API de leitura, painel e busca.
- Interface web: leitura por capítulo com tipografia de livro, tema claro e
  escuro, tamanho de fonte ajustável.
- Painel do versículo: todas as versões, comentários que cobrem o versículo e
  verbetes que o citam, de todos os módulos.
- Busca por palavra em Bíblias, comentários e dicionários; campo aceita
  referência ("Jo 3:16").

Critérios de aceite:
- Abrir João 3, clicar no versículo 16 e ver versões e comentários.
- Buscar "graça" e navegar até um resultado.
- Sem erros no console do navegador.

### Fase 3 — Importação da biblioteca completa · pendente

- Rodar o importador sobre as duas instalações (cerca de 2,5 GB).
- Tratar os tipos de módulo restantes: livros (`.gbk`), devocionais (`.dev`),
  planos de leitura (`.rdp`).
- Revisar o relatório e corrigir os formatos que falharem.

### Fase 4 — Busca semântica com embeddings · pendente

- Gerar vetores por versículo e por parágrafo de comentário, com modelo
  multilíngue local.
- Busca híbrida: palavra (FTS5) combinada com significado (vetores).
- "Passagens parecidas" no painel do versículo.
- Busca em português sobre comentários em inglês.

### Fase 5 — Estudo de palavras · pendente

- Strong clicável na ARA e no grego TR, ligado aos léxicos.
- Ocorrências de um termo original e como cada versão o traduz.
- Comparador de versões com diferenças destacadas.

### Fase 6 — Notas e exportação · pendente

- Notas e marcações próprias; importação das notas existentes do e-Sword.
- Montagem de estudo exportável.

### Fase 7 — Empacotamento desktop · pendente

- Casca desktop (Tauri ou Electron) sobre a mesma interface.
