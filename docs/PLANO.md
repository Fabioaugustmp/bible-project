# Plano

Aplicativo local e offline de estudo bíblico que lê os módulos já instalados
do e-Sword e do theWord, com interface nova e busca moderna.

Este arquivo guarda os princípios e os marcos. As tarefas de cada marco, com
critérios de aceite, estão em [BACKLOG.md](BACKLOG.md), que é a fonte única do
que executar. Quem continua o trabalho começa por [AGENTS.md](../AGENTS.md).

## Problema que o projeto resolve

O usuário lê em português, mas quase todo o material de estudo profundo que
ele tem (comentários, dicionários, léxicos) está em inglês e preso a dois
programas de interface antiga e busca por palavra exata.

## Princípios

- **Os módulos originais nunca são alterados.** O importador só lê; tudo é
  convertido para uma base própria (`data/library.db`).
- **A base é descartável e reprodutível.** Rodar o importador de novo sobre os
  mesmos arquivos gera o mesmo conteúdo.
- **Dados do usuário (notas, marcações) ficam em base separada**, para que
  reimportar a biblioteca nunca os apague.
- **Tudo roda local e offline.**
- **Tudo é verificável:** cada texto exibido aponta para o módulo e a chave de
  origem.

## Rastreabilidade

| O quê | Onde fica |
|---|---|
| Histórico de mudanças do código | commits git, um por tarefa concluída |
| Tarefas, critérios de aceite e estado | [BACKLOG.md](BACKLOG.md) |
| Decisões e seus motivos | [DECISOES.md](DECISOES.md), numeradas e datadas |
| O que foi descoberto sobre cada formato | [FORMATOS.md](FORMATOS.md) |
| Ideias ainda não transformadas em tarefa | [IDEIAS.md](IDEIAS.md) |
| Pesquisa que originou as ideias | [PESQUISA-FEATURES.md](PESQUISA-FEATURES.md) |
| Procedência de cada módulo importado | tabela `modules` na base: caminho de origem, SHA-256, tamanho, data do arquivo, versão do importador, contagens |
| O que foi ignorado e por quê | tabela `import_log` na base e `data/import-report.json` |
| Procedência de cada texto exibido | cada versículo, comentário e verbete aponta para o módulo de origem e a chave original |

## Marcos

Estado: `concluído`, `em andamento`, `pendente`. A ordem de M2 e M3 e o
alcance de M5 e M6 dependem de respostas do usuário (tabela "Decisões
pendentes" no backlog).

| Marco | Entrega | Estado |
|---|---|---|
| M0 | Reconhecimento dos formatos, importador com procedência, leitor, painel do versículo e busca por palavra, sobre 8 módulos de amostra | concluído (commits `50ee3e7`, `b4e419e`, `19d7d3c`) |
| M1 | Importação completa e confiável das duas instalações; interface utilizável com a biblioteca inteira | concluído: 73 módulos, 0 erros, verify.py passa, painel de Jo 3:16 em 0,23 s (T01–T09; T10 e T11 seguem como melhorias contínuas) |
| M2 | Ponte português ↔ inglês sem IA: Strong clicável, tabela de correspondência, busca bilíngue, citações clicáveis, referências cruzadas | concluído: busca bilíngue, Strong clicável, referências ranqueadas e citações clicáveis (T20–T25) |
| M3 | Busca semântica com embeddings locais, medida por um conjunto de avaliação próprio | pendente |
| M4 | Notas e marcações em base separada; importação das notas do e-Sword; exportação de estudo | pendente |
| M5 | Produto distribuível: assistente de importação, casca desktop, créditos e licenças | pendente |
| M7 | Organização da tela e visualização: marcas por tipo, colunas, versões em paralelo, comentário acompanhando, navegador de dicionários, grafo de referências e mapa por livro | pendente (planejado; ordem em relação a M3 depende de P7) |
| M6 | Opcional: tradução local sob demanda, léxico breve em português, perguntas com resposta citada | pendente |

### Critério de conclusão de cada marco

- **M1:** `python importer/verify.py data/library.db` passa sobre a base
  completa, sem linhas `erro` no log de importação; na interface, Jo 3:16
  mostra versões, comentários e citações de toda a biblioteca em menos de 1 s.
- **M2:** buscar "graça" traz também o material em inglês sobre "grace", com
  a indicação de por que foi incluído; clicar em uma palavra da ARA com Strong
  abre o termo original e os léxicos.
- **M3:** a busca por significado supera a busca por palavra no conjunto de
  avaliação, com os números registrados.
- **M4:** reimportar a biblioteca não altera nenhuma nota.
- **M5:** uma pessoa sem linha de comando instala, importa seus módulos e lê.
