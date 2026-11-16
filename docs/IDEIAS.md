# Ideias de funcionalidade

Ideias ainda não transformadas em tarefa. As tarefas a executar estão em
[BACKLOG.md](BACKLOG.md); o roteiro, em
[PLANO.md](PLANO.md). Um item sai daqui quando vira tarefa no backlog (e
então é marcado como `planejado`, com o id da tarefa) ou quando é descartado (com o
motivo).

- **Origem:** `pesquisa` = [PESQUISA-FEATURES.md](PESQUISA-FEATURES.md)
  (2026-11-16, feita por um agente; as fontes externas e licenças **não foram
  conferidas** por nós); `importação` = achado durante a Fase 3; `uso` =
  limitação notada ao testar o aplicativo.
- **Prioridade:** sugestão inicial, ainda não validada pelo usuário.
- **Estado:** `ideia`, `planejado`, `feito`, `descartado`.

Antes de adotar qualquer dado externo, conferir a licença na origem e
registrar a decisão em [DECISOES.md](DECISOES.md).

## Prioridade 1 — alto valor, só com dados que já existem

| ID | Funcionalidade | O que o usuário ganha | Depende de | Esforço | IA | Origem | Estado |
|---|---|---|---|---|---|---|---|
| B01 | Citações bíblicas clicáveis dentro de comentários e verbetes | Passar o mouse em "Rom 8:28" mostra o versículo em português; clicar navega | Tabela `links`; guardar a posição da citação no texto | Baixo | Não | pesquisa #1 | ideia |
| B02 | Busca bilíngue por ponte Strong | Buscar "graça" acha também "grace" e χάρις nos comentários em inglês | ARA com Strong, TR com Strong, KJV | Médio | Não | pesquisa #2 | ideia |
| B03 | Referências cruzadas ranqueadas | Lista curta das passagens mais ligadas, com texto em português e a origem de cada ligação | TSK, `default.xrefs.twm` do theWord, co-citação na tabela `links`; opcional: OpenBible (CC BY) | Baixo | Não | pesquisa #3 + importação | ideia |
| B07 | Mapa de cobertura no leitor | Marca discreta por versículo indicando quanto material existe; painel agrupado | Contagens de `comments` e `links` | Baixo | Não | pesquisa #7 | ideia |
| B22 | Títulos de seção e parágrafos na leitura | Capítulo dividido em perícopes com título, em vez de bloco contínuo | `default.english.hdgs.twm` e `default.prgs.twm` do theWord; versões "com cabeçalhos" do e-Sword | Baixo | Não | importação | ideia |
| B23 | Voltar aos resultados da busca | Abrir um resultado não perde a lista | Nenhum | Baixo | Não | uso | ideia |

## Prioridade 2 — alto valor, exige modelo local ou dado externo

| ID | Funcionalidade | O que o usuário ganha | Depende de | Esforço | IA | Origem | Estado |
|---|---|---|---|---|---|---|---|
| B11 | Avaliação automática da busca semântica | Escolher o modelo de embeddings por medida, não por impressão | TSK e pares versículo ↔ comentário já na base | Baixo | Embeddings locais | pesquisa #11 | ideia (fazer junto com a Fase 4) |
| B04 | Tradução local de comentários, sob demanda | Ler Gill, Henry, ISBE em português, com o original ao lado e cache | Modelo OPUS-MT en→pt (CC BY 4.0, a conferir); quebra a D003 | Médio | Modelo de tradução local | pesquisa #4 | ideia |
| B05 | Léxico breve em português | Clique no Strong responde primeiro em português, com as traduções reais da ARA | STEPBible TBESG/TBESH (CC BY 4.0, a conferir) + tradução única | Médio | Modelo de tradução local, uma vez | pesquisa #5 | ideia (junto com a Fase 5) |
| B06 | Planos de leitura com progresso | Uso diário; "continuar de onde parei" | Módulos `.rdp` e devocionais já instalados | Baixo | Não | pesquisa #6 | ideia |
| B10 | Versificação correta entre tradições | Bíblia católica, Salmos com título e deuterocanônicos alinhados; resolve o limite da D005 | STEPBible TVTMS (CC BY 4.0, a conferir) | Médio | Não | pesquisa #10 | ideia |
| B09 | Aviso de variante textual no comparador | Explica por que ACF/ARC têm trechos que NVI/NTLH omitem | STEPBible TAGNT (CC BY 4.0, a conferir); módulos de variantes já instalados | Médio | Não | pesquisa #9 | ideia (junto com a Fase 5) |
| B08 | Página de tópico em português | Um lugar só para "Arca da Aliança": verbetes de todos os dicionários e versículos | Nave's, Torrey, Thompson, ISBE, Easton; ACAI (CC BY-SA 4.0, a conferir) | Médio/alto | Não (embeddings ajudam) | pesquisa #8 | ideia |

## Prioridade 3 — bom, mas pode esperar

| ID | Funcionalidade | O que o usuário ganha | Depende de | Esforço | IA | Origem | Estado |
|---|---|---|---|---|---|---|---|
| B20 | Busca por morfologia | "Todos os imperativos aoristos em Romanos" | TR com morfologia | Médio | Não | pesquisa #20 | ideia |
| B13 | Interlinear do AT e morfologia por extenso | Hebraico com Strong, glosa e análise explicada | STEPBible TAHOT, TEHMC, TEGMC (a conferir) | Médio | Não | pesquisa #13 | ideia |
| B12 | Mapa dos lugares do capítulo | Ver onde ficam os lugares citados | OpenBible Geocoding (CC BY 4.0, a conferir); atlas instalado | Médio | Não | pesquisa #12 | ideia |
| B15 | Cadernos de estudo e etiquetas nas notas | Notas agrupadas por tema; exportação em Markdown | Base de dados do usuário (Fase 6) | Médio | Não | pesquisa #15 | ideia (junto com a Fase 6) |
| B16 | Áreas de trabalho e painéis lado a lado | Guardar arranjos ("devocional", "grego") | Nenhum | Médio | Não | pesquisa #16 | ideia |
| B14 | Leitura em voz alta | Ouvir o capítulo em português | Voz do sistema pelo navegador | Baixo | Não | pesquisa #14 | ideia |
| B18 | Passagens paralelas e AT citado no NT | Sinopse dos evangelhos, Reis/Crônicas lado a lado | Fonte aberta de paralelos não confirmada; aproximação por embeddings | Médio/alto | Embeddings locais | pesquisa #18 | ideia |
| B17 | Resumo "o que dizem os comentaristas" | Três ou quatro linhas em português por versículo, com fonte por frase | Comentários importados | Médio | LLM | pesquisa #17 | ideia |
| B19 | Pergunte à biblioteca, com resposta citada | Pergunta e resposta em português, com citações clicáveis | Índice da Fase 4 | Alto | LLM; ameaça o "tudo offline" | pesquisa #19 | ideia (opcional, por último) |
| B21 | Linha do tempo e pessoas | Eventos e genealogias ligados aos versículos | Theographic (licença com divergência, a conferir) | Alto | Não | pesquisa #21 | ideia |

## Descartado

| Ideia | Motivo |
|---|---|
| Traduzir a biblioteca inteira de antemão | Muito texto para CPU e a maior parte nunca seria lida; tradução sob demanda com cache (B04) cobre o que importa |
| Chat genérico sem citações | Não dá para conferir; só faz sentido no formato do B19 |
| Treinar ou ajustar modelo próprio | Custo não se paga para biblioteca pessoal |
| Banco de grafos | As relações cabem em tabelas SQLite |
| Árvores sintáticas MACULA na interface | Baseadas em Nestle1904/SBLGNT, não no TR instalado |
| Visualizações decorativas (arcos, nuvem 3D) | Pouco usadas no estudo |
| Recursos sociais, nuvem, sequências de dias | Contrariam "local e offline" |
| Abrir módulos criptografados | Contorna proteção de conteúdo licenciado (D008) |
| Loja ou baixador de módulos de terceiros | Situação de direito autoral incerta |
| NLLB-200 como tradutor | Licença não comercial trava distribuição futura |
| Montador de sermões | Fora do objetivo; a exportação da Fase 6 cobre o essencial |
