# Backlog de execução

Tarefas que precisam ser executadas, na ordem. Escrito em 2026-11-16 para que
qualquer pessoa ou modelo continue o trabalho a partir daqui.

Ler antes de começar: [AGENTS.md](../AGENTS.md) (regras e armadilhas),
[PLANO.md](PLANO.md) (princípios e marcos),
[DECISOES.md](DECISOES.md), [FORMATOS.md](FORMATOS.md). Ideias ainda não
transformadas em tarefa estão em [IDEIAS.md](IDEIAS.md).

## Objetivo

Aplicativo local e offline de estudo bíblico que importa os módulos que o
usuário já tem do e-Sword e do theWord, com leitura bem tipografada e busca
unificada. O problema central a resolver: o usuário lê em português, mas quase
todo o material de estudo profundo que ele tem está em inglês.

**Posicionamento proposto (aguarda confirmação do usuário).** O usuário quer
que o projeto se destaque, citando o Bíblia Raízes. Pelo site dele (lido em
2026-11-16): assinatura anual, hebraico e grego dentro da leitura, assistente
de IA com citações, biblioteca fechada de obras em português, notas
sincronizadas. Competir nisso é fazer o mesmo produto com menos conteúdo. O que
este projeto pode ter que aquele não tem:

1. **Biblioteca própria:** importa qualquer módulo e-Sword/theWord; não é
   catálogo fechado.
2. **Local, privado, sem assinatura.**
3. **Ponte português ↔ inglês sem IA** (marco M2): torna utilizável em
   português o acervo em inglês.
4. **Tudo verificável:** cada resultado mostra de que módulo e arquivo veio;
   comparar comentaristas lado a lado em vez de uma resposta única de IA.

Limite: módulos protegidos por direito autoral não podem ser distribuídos com
o aplicativo; cada usuário importa os seus.

## Estado atual (2026-11-17, após a Onda 4)

- `data/library.db` é a base completa: 73 módulos (16 Bíblias, 24
  comentários, 25 dicionários, 6 livros, 1 de referências cruzadas, 1 de
  títulos), 1,26 GB, importada em 413 s, sem nenhum módulo com erro.
  `python importer/verify.py data/library.db` passa.
- Novo na base: 1,42 milhão de palavras em `tokens` (5 Bíblias com Strong),
  137 mil termos em `strong_terms`, 22.677 referências cruzadas em `xrefs`,
  5.289 títulos em inglês em `headings` (ainda não exibidos; D012).
- Interface: leitura com títulos de perícope; painel do versículo com
  versões (outros idiomas recolhidos), referências cruzadas com o texto na
  versão aberta, comentários recolhidos (texto integral ao abrir), filtro de
  idioma e obras que citam o versículo agrupadas; busca paginada com volta
  aos resultados. `/api/verse` responde em cerca de 0,23 s com 10 a 19 KB.
- Ainda não usado pela interface: `tokens` e `strong_terms` (são a base das
  tarefas T20–T23 da Onda 3).
- 49 arquivos ficaram de fora e estão em `import_log` (criptografados, cópias
  unidas pela D011, planos de leitura, mapa, parágrafos).
- Módulos de origem: `C:\Program Files (x86)\e-Sword`,
  `C:\ProgramData\The Word`, `%APPDATA%\The Word`.
- Ambiente: Windows, Python 3.14 (só biblioteca padrão, D003), Node instalado,
  Rust não instalado.

**Ondas 3 e 4 concluídas em 2026-11-17** (marco M2): busca bilíngue (T23,
D013), Strong clicável e painel "Palavra" (T20 + T22, D014), referências
ranqueadas (T25, D015) e citações clicáveis nos comentários (T24, D016). A base
atual (1,48 GB) tem 2.310.407 citações com posição em `refs`; os comentários do
e-Sword em português passaram a alimentar "Citado em" e a co-citação.

**Próximo passo:** passo 4 do "Roteiro por modelo": M3 (embeddings, Opus),
que depende da resposta P3. T10 (importação incremental) concluída: D017.

## Como trabalhar

- Uma tarefa por commit; mensagem diz o que foi verificado.
- Concluída = critérios de aceite conferidos + `python importer/verify.py`
  passa + documentos atualizados (este arquivo, PLANO, FORMATOS se o formato
  foi descoberto, DECISOES se houve escolha).
- Nunca escrever nos módulos de origem. Nunca tentar abrir módulos
  criptografados (D008).
- A importação completa leva cerca de 10 minutos: rodar em segundo plano e
  gravar em arquivo separado antes de promover (D009).
- Scripts com barras invertidas (RTF, regex) devem ir em arquivo `.py`, não em
  heredoc de shell: o heredoc já corrompeu `\r` e `\x` duas vezes.
- Ler colunas de módulos com `cast(coluna as blob)`: há texto que não é UTF-8.

## Decisões pendentes do usuário

| # | Pergunta | Recomendação |
|---|---|---|
| P1 | Confirma o posicionamento acima? O projeto será público? | **Respondida (2026-11-17):** primeiro para uso pessoal; se der certo, vira produto |
| P2 | Ponte português↔inglês (M2) antes dos embeddings (M3)? | **Respondida: sim** (2026-11-17) |
| P3 | Dependências além da biblioteca padrão são aceitas (necessárias em M3)? | **Respondida: sim**, isoladas em `.venv-bench` (2026-11-17); a D003 é revista pela D020 |
| P4 | Uso de modelo de linguagem (local ou por API) é aceito? | Só opcional e por último (M6) |
| P5 | Manter a página do Notion sincronizada? | Não: hoje ela espelha IDEIAS.md e está desatualizada em relação a este arquivo |
| P6 | Grafo e colunas (M7): escrever o posicionamento por força no próprio projeto ou incluir uma biblioteca pronta? | **Respondida: escrever no projeto** (2026-11-17) |
| P7 | Fazer M7 (organização da tela e grafo) antes de M3 (embeddings)? | **Respondida: sim** (2026-11-17) |

## Roteiro por modelo

Cada passo diz qual modelo usar, o que entregar e quando parar. O critério:
tarefa bem especificada e de risco local vai para um modelo menor; tarefa que
mexe em código usado por toda a biblioteca, ou que exige desenho ou
julgamento, vai para o mais capaz. Para trocar de modelo, use `/model`.

| Passo | Tarefa | Modelo | Por quê | Entrega |
|---|---|---|---|---|
| 1 | T11 — testes automatizados — **concluída** | Haiku | especificação fechada, casos listados abaixo; não altera comportamento | pasta `tests/` passando, um commit |
| 2 | T24 — citações clicáveis (EC5) — **concluída** | Opus | altera o conversor de RTF de todos os módulos; posições no texto; validação com julgamento; reimportação | tabela `refs`, interface, reimportação verificada |
| 3 | T10 — importação incremental — **concluída** | Haiku (ou Sonnet, se o Haiku parar) | mudança contida em `build.py`, aceite numérico | opção `--incremental`, um commit |
| 4 | M7 — organização da tela e grafo (T60–T66), se P7 = sim | Opus para T61 e T65 (EC9, EC8); Haiku para T60, T62, T63, T64 e T66 (T62 foi feita no Haiku) | desenho de interface e de visualização exige julgamento; as demais estão especificadas | ver M7 |
| 5 | M3 — busca semântica (T30–T34) | Opus | maior incerteza técnica; depende da resposta P3 | ver EC6 |
| 6 | M4 — notas e exportação (T40–T42) | Sonnet | formatos de notas do e-Sword ainda não examinados | ver backlog |
| 7 | M5 — produto distribuível (T50–T52) | Opus | decisões de arquitetura; depende de P1 | ver EC7 |

**Quando um modelo menor deve parar e devolver a tarefa** (anotando o motivo
na tabela "Estado das tarefas" e sem commitar código pela metade):
- um teste revela defeito no código existente: registrar o defeito como nova
  linha no backlog, marcar o teste como `expectedFailure` com o motivo, e não
  corrigir o código nesta tarefa;
- a tarefa exige uma escolha que não está em `DECISOES.md`;
- duas tentativas seguidas falharam no mesmo critério de aceite;
- seria preciso mudar o esquema da base ou reimportar a biblioteca.

## Prioridade e ordem

A classificação de cada tarefa por relevância e complexidade, a ordem em ondas
e o desenho detalhado das sete execuções mais difíceis e importantes estão em
[EXECUCOES-CRITICAS.md](EXECUCOES-CRITICAS.md). Resumo da ordem:

1. **Base confiável:** T01 → T02 → T03 → T04 → T06 → T07.
2. **Em paralelo:** modelo de palavras (T05 + T21) e T09 no importador;
   interface em escala (T08).
3. **A ponte para o usuário:** busca bilíngue (T23), Strong clicável (T20 + T22), T25.
4. **Citações clicáveis:** T24.
5. **Embeddings:** T30–T34.
6. **Notas** (T40–T42) e **produto** (T50–T52).

## Estado das tarefas

Marcar aqui ao concluir, com o commit: `pendente`, `em andamento`, `concluída (abc1234)`.

| Tarefa | Estado |
|---|---|
| T01 | concluída: 6 módulos com cabeçalhos importam, 1.923 títulos cada (1.915 na católica), texto sem o título |
| T02 | concluída: 6 pares unidos, nenhuma sigla repetida; critério revisto na D011 |
| T03 | concluída: gnt-tr_.bblx registrado como ignorado (cifrado); Webster importa 61.200 verbetes; resíduo do AmTrac aceito |
| T04 | concluída: idiomas normalizados, títulos de Bíblia do theWord com até 90 caracteres, católica sem marca indevida de Strong |
| T05 | concluída (EC1): interlineares BSB com texto limpo e títulos de seção; palavras em `tokens` |
| T06 | concluída: verify.py com tolerâncias e verificações de T02–T04; passa na base de amostras (resultado na base completa: ver T07) |
| T07 | concluída: 71 módulos, 0 erros, 479 s, base de 1,16 GB promovida; verify.py passa; interface testada |
| T08 | concluída (EC4): painel enxuto (Jo 3:16 de 315 KB para 19 KB), recolhido e filtrável; busca paginada com volta; perícopes e referências cruzadas na tela; testado em 1280 px e 375 px, temas claro e escuro |
| T09 | concluída em parte: referências cruzadas (theWord e BSB) e títulos em inglês importados; parágrafos não, por falta de confirmação do campo `typ` |
| T10 | concluída (passo 3 do roteiro, Haiku; D017): `build.py --incremental`; base de amostras (8 módulos, 101.262 versículos): completa 16,4 s, primeira incremental (sem base) 16,6 s, segunda (sem mudanças) 2,8 s com 0 arquivos relidos; arquivo removido (Almeida.dctx) sai da base e, de volta, é relido: contagens de todas as tabelas iguais às da importação completa e `verify.py` passa; 5 testes novos (61 no total, todos passam); não medido na biblioteca completa (critério "menos de 60 s" pendente); **biblioteca real (revisão):** completa 546,5 s, incremental sem mudanças 42,2 s (120 arquivos pulados), todas as contagens iguais às da completa |
| T11 | concluída: 41 testes em `tests/` (39 escritos pelo Haiku; os 2 que faltavam, Webster com título fora do UTF-8 e byte de controle da católica, acrescentados na revisão com dados sintéticos); `python -m unittest discover -s tests` em 0,05 s |
| T21 | concluída (EC1): `strong_terms` com 137 mil termos; 16 de 18 traduções esperadas conferem, as 2 restantes são diferenças legítimas |
| T23 | concluída (EC2): 'graça' passa de 565 para 18.245 comentários; 39 de 40 primeiros resultados em inglês pertinentes em 4 consultas; D013 |
| T20 + T22 | concluídas (EC3): botão Strong nas 5 Bíblias com Strong; painel Palavra com termo original, traduções em português e inglês, léxicos e ocorrências; 0,17 a 0,32 s |
| T25 | concluída: referências ranqueadas por listas curadas (theWord, BSB, TSK) e co-citação; 0,02 a 0,04 s; D015 |
| T24 | concluída (EC5): 2,31 milhões de citações clicáveis (theWord e e-Sword), prévia na versão aberta; 99,1% de acordo com a lista do theWord; D016 |
| T30 | concluída: ambiente `.venv-bench` com PyTorch CUDA, sentence-transformers 6.3, mteb 2.27 e ragas; D020 |
| T31 | concluída: `bench/eval_embeddings.py`; BGE-M3 vence no caso central (versículo -> comentário em inglês: 0,714 contra 0,615); D021 |
| T32 | concluída: `data/embeddings.db` com 31.102 vetores de versículos (54 s) e 199.150 de comentários em inglês (1.075 s), BGE-M3, 1024 dimensões, float16; separado da biblioteca |
| T33 | concluída: busca por sentido na interface, em grupo separado "Por sentido" (com o "Por palavra" acima); serviço `app/embed_service.py` (BGE-M3, porta 8378) e endpoint `/api/semantic`; mostra os termos em comum ou "sem termos em comum"; sem o serviço, avisa e a busca por palavra continua; testada com "perdão" (Sl 130:4 entre os primeiros) |
| T34 | concluída: aba "Parecidas" no painel do versículo (10 passagens de sentido parecido, ARA1993+, com similaridade); serviço `/similar` no `embed_service.py` usa o vetor guardado; endpoint `/api/similar`; testada em João 3:16 (1 João 4:9 em 0,81, João 3:17 em 0,78); a aba some quando não há resultados |
| T60 | concluída: seis cores por tipo (`--type-*` em style.css, claro e escuro) e etiquetas nas seções do painel, em cada item (versões, referências, comentários, citados, verbetes abertos), nos resultados de busca e na seção Léxicos do painel Palavra; Léxico = Dodson, AHLB, LSJ, MLSJ, KJC, LXXHebGreek. Contraste do texto medido com WCAG (painel e fundo da leitura): tema claro de 4,88:1 (comentário, sobre o fundo da leitura) a 6,96:1; tema escuro de 7,46:1 a 10,64:1; testado em Jo 3:16, busca "graça" e painel Palavra (G25) nos dois temas, sem erros no console; revisão: a etiqueta escrita ficou só onde os tipos se misturam (Citado em, dicionários e livros na busca, item aberto, léxicos); seções homogêneas mostram uma barra na cor do tipo no título |
| T61 | concluída (EC9, D018): botão Fixar e 'Fixar ao lado', coluna com abas, divisórias por mouse e teclado, arranjo guardado; testada em 1280, 1024, 768 e 375 px e nos dois temas |
| T65 | concluída (EC8, D019): grafo no painel do versículo (Lista/Grafo), posicionamento próprio em `app/static/graph.js`; centros e isolado conferidos nos 5 versículos, 0 rótulos sobrepostos, recentrar 45 ms com cache; só lista abaixo de 760 px |
| T64 | concluída: botão 'Dic.' abre as 26 obras de dicionário e livro; índice alfabético, filtro por texto e paginação (`/api/titles`); verificado com o Easton (382 títulos com A, 'abin' acha Abinadab, verbete abre). Dic Port (36 mil) não foi medido |
| T66 | concluída (Haiku): faixa com 66 barras por livro, agrupadas em 8 grupos; clique filtra a lista; contagem pelo mesmo ranqueamento da lista (`/api/xref-books`); Sl 23:1 mostra Ez 29, Jo 34, Is 19, 1Pe 3; Gn 1:1 mostra Sl 43, Pv 13, Jo 19. Só no modo Lista |
| T63 | concluída (Haiku): 'Acompanhar na leitura' em cada comentário do painel fixa um comentário que troca o trecho ao mudar de versículo (85 a 265 ms, critério 0,3 s) e ao rolar o texto (versículo do meio da tela); citações clicáveis; sobrevive a recarregar. `/api/commentary` (2 a 5 ms). JFB em Rm 8 |
| T62 | concluída (Haiku; o roteiro previa Sonnet, mas não houve condição de parada): botão '‖' liga o modo paralelo; até 4 versões lado a lado, alinhadas por versículo (linhas com a mesma altura), hebraico com dir=rtl; escolha guardada. Testado com ARA + ACF + KJV (João 3:16), ARA + WLC (Sl 23:1) e limite de 4. Sem títulos de seção nem Strong nesse modo; em tela estreita, as colunas empilham |
| T40 | parcial: `data/user.db` com notas presas a passagens (criar, editar, apagar para a lixeira); aba "Minhas notas" no painel do versículo; escrita só pelo servidor, com conferência de Origin e Host (testada: origem falsa recusada, 403); critério da D4 verificado em parte: importação de amostras (`modules-sample`) não altera o `user.db` (hash idêntico antes e depois); a reimportação completa não foi rodada; faltam marcações, etiquetas e estudos (D5) |
| T90 | parcial (D5, primeira fatia, decisões do usuário aprovadas): área Meus estudos (botão Estudos), estudos com blocos de passagem, título e nota; "Adicionar ao estudo mais recente" no painel do versículo; reordenar, editar, remover e exportar em Markdown; estudos vão para a lixeira; testado: API (origem falsa recusada), criação a partir do painel e edição no navegador. Faltam citação e palavra (D5, próxima fatia), coluna ao lado do Ler (decisão 3, só quando aberta: feita com "Abrir ao lado", D025; testada com criar, nota, renomear e apagar pela coluna; não testada em tela estreita) |
| T41 | concluída: notas do e-Sword (`study.notx`, RTF) importadas para `data/user.db` com procedência (tabela `imports`, SHA-256, `import_id` em cada nota); reimportar o mesmo arquivo não duplica (testado); 1 nota importada (João 3:16) conferida na interface |
| T42 | parcial: todas as notas exportadas em Markdown (`/api/user/export`) e em Word (`/api/user/export.docx`, só biblioteca padrão; pacote validado: 3 partes, XML bem formado); faltam PDF (exige biblioteca externa, D003: decisão sua) e exportação de estudos (D5) |
| T97 | concluída: na busca por palavra, "Copiar versículos" (com referência) e "Adicionar versículos ao estudo" (um bloco por versículo, até os 49 da busca de teste); a busca traz no máximo 60 versículos por vez, e o aviso diz quando há mais; testado no navegador (49 blocos, toast; cópia sem leitura do clipboard, bloqueada no navegador de teste) |
| GET `/api/user/study` sem `id` | corrigido: responde 400 em vez de derrubar a conexão; teste em `tests/test_user_study.py` |
| T81 | concluída: "Citado em notas" dentro de "Minhas notas" do versículo: notas de outros versículos que citam este (inclui intervalos; ignora notas apagadas e as do próprio versículo); citações reconhecidas pelo localizador do importador (`importer/refs.py`, `find_plain`); `app/backlinks.py`, endpoint `/api/user/backlinks`; 5 testes em `tests/test_backlinks.py` (68 no total, OK); testado no navegador com uma nota de teste, apagada depois |
| T82 | concluída (primeira etapa, D028): "Leitura" na barra abre "Leitura de hoje": planos de capítulos sem data, marcar como lido (grava a data), próximo capítulo, notas de hoje, apagar plano (lixeira); `app/reading.py`, endpoints `/api/user/reading` e `/api/user/plan/*`; desenho em `docs/DESENHO-LEITURA.md`; 9 testes em `tests/test_reading.py` (75 no total, OK); testado no navegador (criar pelo formulário, marcar, progresso 0→1 de 2, planos de teste apagados). Pendente: marcação por intervalo de versículos, calendário e planos prontos |
| T83 | concluída: "Paralelo" mostra a comparação de um clique (sem escolher versões antes): a versão aberta e outra do mesmo idioma, ou a primeira disponível; com uma só versão, aviso "Escolha mais uma versão nas fichas acima"; testado no navegador a 1280 px (ACF + ARA; remover uma mostra o aviso) e 375 px (sem rolagem horizontal); 75 testes OK; a escolha das fichas continua guardada |
| T84 | concluída: botão "Exibir" abre o menu com as alternâncias (Paralelo com p, Marcas, Selecionar, fonte menor e maior, tema, buscar com /, atalhos com ?), com estado "ligado" e teclas visíveis; ações chamam os mesmos botões da barra; testado no navegador a 1280 px (paralelo ligado pelo menu: 2 colunas) e 375 px (sem rolagem horizontal, linhas de 40 px); 75 testes OK |
| T85 | concluída (já existia): o painel Palavra mostra as ocorrências em contexto (versículo com o texto e as palavras usadas pela ARA), 60 por página com "Mais ocorrências"; testado com G1722 (2.112 ocorrências); léxicos com trecho e traduções em português e inglês no mesmo painel |
| T96 | concluída (já existia, commit b0bad3e): modo "Próximas (NEAR)" com campo "Alcance" de 1 a 50 palavras; conferido no código (`fts_by_mode`) e no painel de busca |
| T88 | concluída: escopo por livro (select "Livro", 66 livros ou toda a Bíblia) em versículos e comentários, no servidor (`book` em `/api/search`); testado no navegador com "graça" em João (comentários de 18.245 para 841; versículos da versão aberta KJV sem resultado, por a palavra ser "grace"); 375 px sem rolagem horizontal; 75 testes OK. Escopo de obra segue como "Versão aberta / Todas as versões"; dicionários não têm livro |
| T89 | concluída (primeira etapa, D029): botão "Diário" abre "Diário de estudo": entradas com data, sem passagem, em `user.db` (tabela `journal`); criar, editar, buscar pelo texto e apagar para a lixeira; endpoints `/api/user/journal` e `journal/create|update|delete`; 5 testes em `tests/test_journal.py` (80 no total, OK); testado no navegador (criar com quebra de linha, editar, buscar com e sem resultado, apagar; 375 px sem rolagem horizontal). Pendente: exportar o diário e etiquetas (T99) |
| T87 | concluída (D030): botão "Tópicos" (distinto de "Temas", a busca): tópicos com notas de várias passagens, com ou sem passagem; criar, editar, apagar nota e apagar tópico (lixeira); nomes únicos sem diferença de caixa; tabelas `topics` e `topic_notes` em `user.db`; endpoints `/api/user/topics`, `topic`, `topic/*`; 5 testes em `tests/test_topics.py`; testado no navegador (dois tópicos de notas, edição, apagar tópico; 375 px sem rolagem horizontal). Etiquetas de notas por versículo (parte de T40) continuam pendentes |
| T80 | concluída, primeira etapa (D031): botão "Memorizar": cartões de um versículo com SM-2 (facilidade, intervalo e repetições); revisão com o versículo oculto até pedir, respostas Não lembrei, Difícil, Bom e Fácil; tabela `memo_cards` em `user.db`; `sm2()` em `app/userdata.py`; 91 testes no total (OK; 6 novos em `tests/test_memo.py`, incluindo a sequência 1, 6, 15 dias, o erro e o piso de 1,3); testado no navegador (adicionar João 3:16, revisar, "Bom" agenda para amanhã; tirar da memorização; 375 px sem rolagem horizontal). Pendente: botão "Memorizar" no painel do versículo, cartões a partir de notas e FSRS |
| T98 | concluída (D032): "+ conjunto" ao lado de cada referência cruzada; conjuntos nomeados com passagens na ordem escolhida (subir, descer, remover; criar e apagar conjunto, com lixeira); acesso pelo menu Exibir; tabelas `ref_sets` e `ref_set_items`; 6 testes em `tests/test_ref_sets.py` (94 no total, OK); testado no navegador (criar conjunto a partir de João 16:16, adicionar a segunda passagem, subir, remover, apagar; 375 px sem rolagem horizontal). Pendente: notas por item e exportação |
| T93 | concluída (D033): menu Exibir → "Mapa de estudo e linha do tempo": mapa com passagens (40 mais estudadas), tópicos e estudos ligados pelas notas e blocos, layout do grafo de referências, clique abre a passagem; linha do tempo por dia com notas, tópicos, diário, estudos, memorização, conjuntos e leituras, lida das datas já guardadas (sem tabela nova); `app/studymap.py`; 4 testes em `tests/test_studymap.py` (98 no total, OK); testado no navegador com um tópico de três passagens (3 ligações, linha do tempo por dia) e 375 px sem rolagem horizontal. Pendente: instantâneos históricos, filtro por período |
| T101 | parcial (D034): publicação em https://biblia.famptech.com.br pelo túnel da Cloudflare; `BIBLE_PUBLIC_ORIGIN` e `BIBLE_ACCESS_TOKEN` exigem código em todo pedido (`app/server.py`, `gate`); origem https aceita só no host público (`userdata.check_origin`); web entra na rede `general-network` do túnel existente (`cloudflared-default`, rota para `http://biblioteca-web:8377`); código gravado no log como `***`; 7 testes em `tests/test_publico.py` (111 no total, OK); testado no contêiner com Host e Origin do domínio: sem código 403, código 302 com cookie Secure, escrita https 200, escrita http 403. Pendente: rota criada no painel e teste no servidor; Cloudflare Access; decisão de licença (T52) |
| T103 | concluída (D037): indicador de carregamento na busca, com busca por palavra primeiro, contador, tempo limite de 20 s, aquecimento ao abrir a página e descarte de respostas antigas; testado no navegador (desktop e 375 px) com atraso simulado de 8 s, 25 s e troca de busca; 111 testes OK. Nota: "fe" e "fé" dão zero resultados por palavra (termo de duas letras), fora deste escopo. Antigo plano: Problema: `showSearch` (app/static/app.js) espera busca por palavra, busca por sentido e Strong juntas (`Promise.all`); a primeira busca por sentido carrega o modelo no servidor (dezenas de segundos em CPU), e o usuário vê só "Buscando…" sem fim. Mudanças: (1) mostrar a busca por palavra assim que chegar, em bloco separado; (2) bloco "Buscando por sentido…" com contador de segundos e aviso de primeira vez; (3) tempo limite de 20 s no cliente, com a mensagem "o modelo ainda está carregando, tente em instantes", mantendo os resultados por palavra; (4) aquecimento: ao abrir a página, uma consulta em segundo plano (ex.: "aquecimento") para carregar o modelo antes da primeira busca; (5) indicador visual (spinner CSS, `role="status"`, respeitando `prefers-reduced-motion`); (6) opcional: endpoint de situação do serviço (modelo carregado ou não) para trocar o contador por "carregando modelo". Riscos: resultados chegando fora de ordem (usar contador de requisição para descartar respostas antigas); cuidar do celular, que já tem "Buscando…" (D036). Testes: navegador no desktop e no celular com serviço parado, lento e normal; 111 testes OK. |
| T104 | concluída: `importer/mysword.py` lê Bíblias (`Bible`) e dicionários (`dictionary`, HTML → texto, links `#bL.C.V` viram citações em `refs`) e a tabela `Details`; protegidos (`encryption`/`compressed` ≠ 0) pulados só com `Details` lida (D008); `build.py` aceita `.mybible` (`source = 'mysword'`), sem mudar o esquema nem a versão do importador. Conferido nos 53 `.mybible` da pasta do Drive: 0 erros, 42 importados, 2 protegidos e 5 livros ignorados, 6 cópias unidas. WEB: 31.103 linhas (a análise dizia 31.102: Rm 14:24-26 a mais, Rm 16:26-27 a menos), 31.098 gravadas (5 só com nota); Jo 3:16 confere. Strong v2.2 (`strong.a`, 35,3 MB): 14.700 verbetes, 14.696 com chave Strong (confere com a análise) + 4 prefixos hebraicos; 349.504 citações; G26 e H430 conferem. Cópia `data/library-candidata.db` + WEB + Strong pela incremental: 114 arquivos pulados, 8 relidos, 144 s, 75 módulos; `verify.py` passa (não promovida). 120 testes OK (9 novos em `tests/test_mysword.py`). OpenGNT é lido, mas o texto leva transliteração e glosa (T108) |
| T106 | parcial na candidata: `biblialivre.bbl.mybible` importada como `BLivre` (Bíblia Livre, por, origem `MySword`, sha256 gravado): 31.097 versículos gravados (a fonte tem 31.102 linhas; 5 vazios não gravados e sinalizados no `import_log` com a referência: 15:3:6, 19:108:13, 47:13:14, 64:1:14, 66:12:17; nenhum texto inventado); Jo 3:16 confere. O aviso agora lista as referências (`importer/mysword.py`). `verify.py` passa; 121 testes OK (1 novo, em `tests/test_mysword.py`). Falta T52: crédito "BLIVRE", tela de créditos e decidir o acesso sem código na demonstração (nada do site foi mudado) |
| T105 | concluída na candidata (D038): `strong.a.dct.mybible` (v2.2) importado como dicionário `Strong`, origem `MySword`, **ao lado** de Dodson e AHLB (não substitui). Candidata: 14.700 verbetes, 14.696 com chave Strong (confere); G26 mostra Dodson, MLSJ, LSJ, KJC, LXXHebGreek e Strong; H430 mostra AHLB, KJC, LXXHebGreek e Strong. Dodson e AHLB intactos. Teste novo `MyswordStrongAoLadoTest`; `verify.py` passa; 122 testes OK. Não promovida; licença a conferir antes do site (T52) |
| T102 | parcial (D036): navegação do celular (até 560 px) pela Alternativa 1 de `docs/UX-MOBILE-S23.md`: cabeçalho de uma linha ("João 1 ▾" e versão) que some ao descer; barra inferior fixa ‹ Buscar Estudo Aa ⋯ ›; busca em tela própria; folhas Estudo (Leitura de hoje primeiro), Texto e tema (Claro, Escuro, Sistema) e Mais (Ler, Ferramentas, Preferências); seletor de passagem em grade; folha a 60% com o versículo aberto acima dela e botão para quase tela cheia; abas do versículo em duas linhas; faixa "Continuar" em uma linha; `interactive-widget=resizes-content` e barra inferior oculta com campo em foco; "Toque" e sem "Esc" em tela de toque. Medido em 412 × 915: barra superior 265 → 57 px, texto começa em y 599 → 218, 9 → 18 linhas na primeira dobra; desktop 1280 × 800 sem mudança nas medidas. Pendente: "voltar" do Android fechando folhas (item 10), rolagem do documento inteiro (item 9), teste em aparelho real com teclado virtual; reorganização do desktop (item 13) |
| T50–T52 (M5) | pendente |

## M1 — Fechar a importação completa

### T01 — Bíblias do e-Sword com linha de cabeçalho e títulos de seção
- **Por quê:** 4 módulos `*_com_cabecalhos.bblx` falham com
  `TypeError: '<=' not supported between 'int' and 'str'`: a tabela `Bible`
  tem uma linha `('Livro','Cap','Verso','TítuloConfigTexto')`. Nos que
  importam (NVI, NTLH), o título vaza para o texto: Gn 1:1 ficou
  "O começo No princípio Deus criou…". No arquivo o título vem como
  `\par\par {\b\qc O começo}\par\par No princípio…`.
- **Fazer:** em `importer/esword.py::read_bible`, pular linhas em que
  Book/Chapter/Verse não são inteiros; extrair grupos `{\b\qc …}` para uma
  coluna nova `verses.heading` (esquema em `importer/db.py`); título no fim de
  um versículo pertence ao seguinte. Ajustar `Adder.verses` em `build.py` e o
  leitor do theWord (passa `None`).
- **Aceite:** os 6 `*_com_cabecalhos` importam; NVI Gn 1:1 tem texto
  "No princípio Deus criou os céus e a terra." e heading "O começo"; mais de
  1.000 títulos por módulo; nenhum texto de versículo começa com o título.
- **Tamanho:** M.

### T02 — Uma só cópia de cada Bíblia
- **Por quê:** a mesma versão existe com e sem títulos (hoje NVI e NTLH
  aparecem duas vezes no seletor; depois de T01, também ARA, ARC, Viva e
  católica).
- **Fazer:** após importar, para Bíblias com mesma `source` e `abbr`, manter a
  que tem mais `heading` e apagar a outra, registrando `ignorado` em
  `import_log` com o nome do arquivo mantido.
- **Aceite:** `select abbr from modules where kind='bible' group by source, abbr having count(*)>1` vazio.
- **Depende de:** T01. **Tamanho:** P.

### T03 — Erros restantes de leitura
- **Fazer:** (a) `gnt-tr_.bblx` tem `Scripture` em blob cifrado: registrar
  `ignorado` em vez de `erro`. (b) Webster 1828: `topics.subject` não é UTF-8
  ("Vis-à-vis"): ler com `cast(t.subject as blob)` e decodificar com
  `_decode`. (c) AmTrac, verbete "Cockle", tem `\par` literal na origem: aceitar.
- **Aceite:** nenhuma linha `erro` em `import_log`; Webster com mais de 60 mil verbetes.
- **Tamanho:** P.

### T04 — Metadados limpos
- **Fazer:** (a) normalizar idioma em `Adder.module`: hoje há `eng`,
  `English`, `Eng - English`, `grk`, `grc`; resultado só em
  {por, eng, grc, heb, spa, lat, und}. (b) Título de Bíblia do theWord com até
  90 caracteres (hoje a BSB traz o aviso de licença inteiro). (c) `CATOLICA`
  está com `has_strongs = 1` indevidamente: investigar o que os grupos
  `{\cfN\super …}` contêm nela e só marcar Strong com códigos `[HG]\d+` em
  volume.
- **Aceite:** consultas correspondentes em `verify.py` passam.
- **Tamanho:** P.

### T05 — Interlineares BSB legíveis
- **Por quê:** `BSB Reverse Interlinear.ont` e `BSB Interlinear NT-Grk.nt`
  viram texto misturado: "For γὰρ gar{G1063} - ὁ ho{G3588} God Θεὸς…".
- **Fazer:** examinar as tags brutas desses dois arquivos, documentar em
  FORMATOS.md, e fazer `text` conter só a língua principal (inglês no
  reverso, grego no outro), mantendo Strong em `tagged`. Guardar grego,
  transliteração e glosa por palavra para a T20 (definir tabela `tokens`).
- **Aceite:** Jo 3:16 do reverso é prosa inglesa sem caracteres gregos.
- **Tamanho:** M.

### T06 — Verificação para a base completa
- **Fazer:** em `verify.py`: tolerar até 1% de diferença na contagem de
  versículos (NVI 31.105, NTLH 31.101, Viva 31.103, católica 31.271 têm
  versificação própria) e até 0,01% de linhas com sobra de marcação; acrescentar
  verificações de T02, T03 e T04.
- **Aceite:** `python importer/verify.py data/library-full.db` sai com 0.
- **Tamanho:** P.

### T07 — Reimportar, verificar e promover
- **Fazer:** `python -u importer/build.py --out data/library-full.db "C:\Program Files (x86)\e-Sword" "C:\ProgramData\The Word" "%APPDATA%\The Word"`;
  rodar T06; parar o servidor; substituir `data/library.db`; testar na
  interface: Jo 3:16 (versões, comentários, citações), busca "graça",
  referência "sl 23.1", console sem erros, painel respondendo em menos de 1 s.
  Marcar M1 no PLANO conforme o critério de conclusão.
- **Depende de:** T01–T06. **Tamanho:** P.

### T08 — Interface na escala da biblioteca completa
- **Fazer:** (a) mostrar `heading` como título de perícope na leitura
  (`/api/chapter` devolve o campo). (b) Painel do versículo com 24
  comentários: agrupar por módulo, português primeiro, recolhido por padrão,
  filtro por idioma. (c) "Citado em" pode ter centenas de itens: agrupar por
  módulo com contagem. (d) Abrir um resultado de busca não deve perder a lista
  (botão de voltar).
- **Aceite:** Jo 3:16 na base completa é navegável sem rolagem excessiva;
  voltar à busca funciona.
- **Depende de:** T07. **Tamanho:** M.

### T09 — Auxiliares do theWord
- **Fazer:** importar `default.xrefs.twm` (tabela `xrefs(vi1, vi2)`, 19.671
  pares), `default.english.hdgs.twm` (`headings(vi, pos, level, content)`,
  5.289) e `default.prgs.twm` (`paragraphs(vi, typ)`, 14.074). O campo `vi`
  é `livro<<24 | capítulo<<16 | versículo<<8`: 16843008 = Gn 1:1, e os três
  primeiros pares de Gn 1:1 decodificam para Jó 38:4, Sl 33:6 e Sl 89:11. O
  significado do byte baixo e de `typ` ainda não foi examinado. Criar tabelas
  `xrefs` e `paragraphs`; usar parágrafos na leitura.
- **Aceite:** 19.671 pares importados; Gn 1:1 lista Jó 38:4, Sl 33:6 e Sl 89:11.
- **Tamanho:** M.

### T10 — Importação incremental (opcional)
- **Modelo:** Haiku (passo 3 do roteiro). Fazer depois da T24.
- **Fazer:** opção `--incremental` em `importer/build.py`:
  1. copiar a base de saída anterior para um arquivo temporário e abri-lo;
  2. para cada arquivo de módulo, se já existe linha em `modules` com o mesmo
     `origin_path`, `origin_sha256` e `importer_version`, pular a leitura;
  3. apagar da base os módulos cujo arquivo mudou ou sumiu (todas as tabelas
     com `module_id`, mais `links` dos seus itens) e importar só esses;
  4. refazer sempre as etapas derivadas: `merge_duplicate_bibles`,
     `strong_terms` (apagar e recalcular), índice FTS (`rebuild`) e relatório.
- **Testar só com cópias:** copiar `modules-sample/` para `data/test-inc/`;
  importar; importar de novo com `--incremental`; depois apagar uma cópia e
  rodar de novo. Nunca alterar os módulos de origem.
- **Aceite:** na segunda execução, nenhum módulo é relido e as contagens de
  `verify.py` são idênticas às da importação completa; apagar um módulo da
  pasta o remove da base; sem mudanças, a biblioteca completa importa em
  menos de 60 s.
- **Tamanho:** M.

### T11 — Testes automatizados
- **Modelo:** Haiku (passo 1 do roteiro). Fazer antes da T24.
- **Onde:** pasta `tests/`, um arquivo por módulo testado, só `unittest`
  (D003). Cada arquivo acrescenta `importer/` ao `sys.path`. Comando:
  `python -m unittest discover -s tests -v`.
- **Regras:** amostras sintéticas escritas no próprio teste, nunca texto de
  módulo protegido nem leitura das pastas dos programas. Strings com barra
  invertida sempre como `r"..."` e o arquivo escrito com a ferramenta de
  edição, não por heredoc de shell (ver armadilhas em AGENTS.md). Os testes
  descrevem o comportamento atual; não alterar o código testado.
- **Casos mínimos:**
  - `test_rtf.py` (`rtf_to_text`): `\uN?` com o caractere de reserva pulado
    (`a\u231?\u227?o` vira `ação`); byte hexadecimal `\'e7` vira `ç`; grupos
    `fonttbl`, `colortbl` e `\*` somem; `\par` vira quebra de linha; campo
    `HYPERLINK` mantém só o texto visível (`1 Sam. 7:1`); texto sem RTF passa
    só por `tidy`.
  - `test_rvf.py` (`rvf_to_text`): montar bytes RVF à mão — linha
    `-8 1 3\r\n`, cabeçalho `0 1 0 0 0 0\r\n`, texto em UTF-16LE terminado por
    `\x29\x20` — e conferir o texto e `resyncs == 0`; bloco de estilos
    `-9 2 ...` com tamanho de 4 bytes é pulado; item de estilo negativo
    desconhecido faz `resyncs > 0` sem perder o texto seguinte.
  - `test_tokens.py`: `from_marked` (código de análise verbal como H8804 vai
    para `morph`; código sem texto como H853 fica com expressão vazia;
    pontuação sozinha junta à palavra anterior); `from_wt` no formato do
    interlinear reverso (`<E>` primeiro: expressão em inglês, original e
    transliteração preenchidos), do interlinear grego (`<O>` primeiro: glosa
    inglesa) e do TR (lema e morfologia); `text_of` sem espaço antes da
    pontuação; `tagged_of`; `normalize_term` ("No princípio," vira
    "princípio"; "..." vira None); `strip_accents` une "χάρις" e "χαρις".
  - `test_cleaners.py`: `esword._split_heading` separa `{\b\qc O começo}` e
    mantém o título de salmo `{\i\qc ...}` no texto; `theword._clean_verse`
    remove nota `<RF>...<Rf>`, variante `<V...>`, devolve o título `<TS>` e
    não deixa caractere grego no texto do interlinear reverso;
    `theword._verse_index(16843008) == (1, 1, 1, 0)`; `db.strip_controls`,
    `db.normalize_lang` ("Eng - English" vira "eng", "grk" vira "grc").
  - `test_readers.py`: criar um `.bblx` temporário com `sqlite3` (tabela
    `Details` e `Bible`, incluindo a linha de cabeçalho
    `('Livro','Cap','Verso','...')` e um versículo com título de seção) e um
    `Adder` falso que guarda as chamadas; conferir que `esword.read_bible`
    pula o cabeçalho e grava o título em `heading` (defeito da T01). Idem um
    `.bblx` com `Scripture` em blob: deve registrar `ignorado` (T03).
- **Aceite:** todos passam; há ao menos um teste para cada defeito corrigido
  em T01, T03, T04 e T05; a suíte roda em menos de 5 s; nenhum arquivo fora
  de `tests/` alterado.
- **Tamanho:** M.

## M2 — Ponte português ↔ inglês sem IA

### T20 — Strong clicável na leitura
- **Fazer:** `/api/chapter` devolve `tagged`; a interface mostra os códigos
  (com liga/desliga) e, ao clicar, abre o painel "Palavra" com os verbetes cujo
  `topic` é o código. Léxicos legíveis por Strong na base: Dodson (grego),
  AHLB (hebraico), LSJ, MLSJ, KJC, LXXHebGreek. Não há dicionário Strong
  hebraico legível (o de Mickelson é criptografado): avaliar fonte aberta e
  conferir a licença.
- **Aceite:** em Jo 3:16 da ARA com Strong, clicar em "amou" abre G25.
- **Tamanho:** M.

### T21 — Tabela de correspondência por Strong
- **Fazer:** na importação, montar `strong_terms(strong, lang, term, count)`
  a partir de `tagged` da ARA1993+ (por), KJV (eng) e TR (grc). O TR traz o
  lema em `l="…"`, hoje descartado em `theword.py::_clean_verse`: preservar.
- **Aceite:** G5485 dá "graça" (por) e "grace" (eng) como termos mais frequentes.
- **Depende de:** T07. **Tamanho:** M.

### T22 — Ocorrências e traduções de um termo
- **Fazer:** no painel "Palavra", listar versículos com o código e como cada
  versão o traduz, com contagem.
- **Depende de:** T20, T21. **Tamanho:** M.

### T23 — Busca bilíngue
- **Fazer:** expandir a busca em português com os termos ingleses e gregos
  mais frequentes do mesmo Strong (limitar aos dois ou três principais);
  mostrar o que foi incluído e permitir desligar.
- **Aceite:** buscar "graça" traz comentários em inglês com "grace", marcados
  "incluído por G5485".
- **Depende de:** T21. **Tamanho:** M.

### T24 — Citações clicáveis nos comentários
- **Fazer:** preservar a posição das referências no texto. theWord: campo
  `HYPERLINK "tw://bible.*?id=L.C.V"` (hoje descartado em `rtf.py`); e-Sword:
  padrões como `Mat_22:30` e `1Sa_16:10-11`. Decidir o formato de marcação
  no texto e registrar em DECISOES.md. Passar o mouse mostra o versículo em
  português; clicar navega.
- **Tamanho:** G.

### T25 — Referências cruzadas ranqueadas
- **Fazer:** combinar TSK/TSKe (já em `links`), `xrefs` (T09) e co-citação
  entre comentários; mostrar as dez melhores com o texto em português e a
  origem de cada uma.
- **Depende de:** T09. **Tamanho:** M.

## M7 — Organização da tela e visualização

Planejado em 2026-11-17 a pedido do usuário. Desenho das duas partes mais
difíceis em [EXECUCOES-CRITICAS.md](EXECUCOES-CRITICAS.md) (EC8, EC9).

**Como está hoje (avaliado na base completa):**
- Duas colunas: o texto e um único painel à direita (embaixo, no celular). O
  painel troca de modo (versículo, busca, palavra, verbete): só uma coisa por
  vez. Abrir um verbete tira o versículo da vista; há botões de voltar, mas
  não dá para ler um comentário e um dicionário ao mesmo tempo.
- Bíblia, comentário, dicionário, léxico e livro se distinguem só pelo título
  da seção e pela sigla; não há marca visual por tipo.
- Dicionários e livros só são alcançados pela busca ou por "Citado em"; não há
  como folhear um dicionário.
- Comentários aparecem por versículo; não há leitura contínua de um
  comentário acompanhando o texto.
- Versões aparecem empilhadas no painel, um versículo por vez; não há leitura
  de versões lado a lado.
- Referências cruzadas: lista ranqueada (T25). Medido em 5 versículos: os 15
  primeiros vizinhos têm entre 24 e 53 ligações entre si e formam núcleos
  claros (Sl 23:1: Is 40:11 ligado a 12 deles, Jo 10:11 a 10; Is 53:5:
  2Co 5:21 é o centro e Gn 3:15 fica isolado). Há estrutura real de grafo.

### T60 — Marca visual por tipo de conteúdo
- **Modelo:** Haiku.
- **Fazer:** uma cor de acento e um rótulo curto por tipo (Bíblia, comentário,
  dicionário, léxico, livro, referência), definidos como variáveis CSS com
  versões clara e escura, usados nos títulos de seção do painel, nos
  resultados de busca e nas etiquetas de origem. Léxico = dicionário cujos
  verbetes são números Strong (Dodson, AHLB, LSJ, MLSJ, KJC, LXXHebGreek).
- **Aceite:** em Jo 3:16 e na busca "graça", cada item mostra o tipo; contraste
  de texto de pelo menos 4,5:1 nos dois temas (medir); nada muda de lugar.
- **Tamanho:** P.

### T61 — Divisão de tela em colunas (EC9)
- **Modelo:** Opus.
- **Fazer:** layout de estudo com até três colunas redimensionáveis: texto |
  painel de estudo | coluna fixada. Fixar qualquer item do painel (um
  comentário, um verbete, o grafo, a busca) o leva para a terceira coluna, que
  fica lá enquanto o painel continua mudando. Larguras e itens fixados ficam
  guardados. Telas menores: duas colunas (tablet) ou painel inferior com abas
  (celular, como hoje).
- **Aceite:** ler Jo 3 com o Gill fixado numa coluna e o painel mostrando o
  verbete "propitiation" do Easton, sem perder nenhum dos dois; arrastar a
  divisória; recarregar a página mantém o arranjo; 1280, 1024, 768 e 375 px
  sem rolagem horizontal; console sem erros.
- **Tamanho:** G.

### T62 — Versões em paralelo
- **Modelo:** Sonnet.
- **Fazer:** modo de leitura com 2 a 4 versões lado a lado, alinhadas por
  versículo (linhas de mesma altura), incluindo grego, hebraico (da direita
  para a esquerda) e inglês. A escolha das versões fica guardada.
- **Aceite:** Jo 3 em ARA, NVI, KJV e TR alinhados; Sl 23 em ARA e WLC;
  versículo ausente numa versão aparece vazio, sem desalinhar.
- **Depende de:** T61 (usa a largura das colunas). **Tamanho:** M.

### T63 — Comentário que acompanha a leitura
- **Modelo:** Sonnet.
- **Fazer:** fixar um comentário na coluna (T61) e, ao selecionar ou rolar até
  um versículo, mostrar o trecho do comentário que o cobre, com as citações
  clicáveis (T24).
- **Aceite:** ler Rm 8 com o JFB acompanhando; mudar de versículo troca o
  trecho em menos de 0,3 s.
- **Depende de:** T61. **Tamanho:** M.

### T64 — Navegador de dicionários e livros
- **Modelo:** Haiku (ou Sonnet).
- **Fazer:** escolher um dicionário ou livro e folhear os títulos (índice
  alfabético com letras, filtro por texto do título, paginação); abrir o
  verbete com citações clicáveis. Novo endpoint que lista títulos por módulo.
- **Aceite:** abrir o Easton e chegar a "Abinadab" pela letra A e pelo filtro;
  abrir o Dicionário Almeida; 36 mil títulos do Dic Port sem travar.
- **Tamanho:** M.

### T65 — Grafo das referências de um versículo (EC8)
- **Modelo:** Opus.
- **Fazer:** ver EC8. Grafo do versículo aberto com os 12 a 20 vizinhos mais
  fortes (T25) e as ligações entre eles; nó maior = mais ligado; cor por
  testamento; clicar num nó recentra o grafo (com voltar), passar o mouse
  mostra o texto; a lista continua disponível ao lado.
- **Aceite:** em Sl 23:1, Is 40:11 e Jo 10:11 aparecem como os nós maiores;
  em Is 53:5, 2Co 5:21; em Gn 1:1, Sl 89:11 aparece isolado; resposta em menos de 1 s;
  rótulos sem sobreposição; legível nos dois temas; navegável por teclado; no
  celular, só a lista.
- **Depende de:** P6; fica melhor com T61 (coluna larga). **Tamanho:** G.

### T66 — Mapa de conexões por livro
- **Modelo:** Sonnet.
- **Fazer:** faixa com os 66 livros em ordem, agrupados (Lei, Históricos,
  Poéticos, Profetas, Evangelhos, Atos, Cartas, Apocalipse), com barras para a
  quantidade de referências do versículo (ou do capítulo inteiro) que vão para
  cada livro. Clicar num livro filtra a lista de referências.
- **Aceite:** em Sl 23:1 aparecem as barras de Ezequiel, Isaías, João e 1 Pedro;
  em Gn 1:1, as de Salmos e Provérbios e a de João; leitura correta nos dois
  temas.
- **Tamanho:** P. Mais barato que o grafo e útil sozinho; pode vir antes.

### Descartado nesta frente
- **Arcos da Bíblia inteira** (todas as 340 mil ligações num só desenho):
  bonito, mas não ajuda a estudar um texto; já estava descartado em IDEIAS.md.
- **Grafo de todo um capítulo ou livro:** passa de 100 nós e vira emaranhado;
  o mapa por livro (T66) responde a mesma pergunta ("para onde este capítulo
  aponta?") de forma legível.

## M3 — Busca semântica (embeddings)

- **T30** Verificar se as bibliotecas de embeddings funcionam em Python 3.14;
  escolher o ambiente e registrar decisão que revê a D003. (depende de P3)
- **T31** Conjunto de avaliação com dados da própria base: pares de referência
  cruzada e versículo ↔ comentário do mesmo versículo; medir recall@10.
- **T32** Indexar versículos e parágrafos de comentário, guardando modelo e
  versão junto dos vetores.
  Escolha do modelo: BGE-M3 (D021). Armazenamento proposto: tabela `embeddings`
  com vetor de 1024 valores em float16 (2 KB por item), chave de origem e modelo.
  Ordem: versículos em português, depois comentários em inglês, em lotes. Tempo
  esperado a medir: 32 s para 31 mil versículos; os comentários são ~92 mil
  (amostra de 3 mil em 16 s).
- **T33** Busca híbrida (palavra + significado) na interface.
- **T34** "Passagens parecidas" no painel do versículo.

## M4 — Dados do usuário

- **T40** Base separada `user.db` com notas e marcações.
- **T41** Importar notas do e-Sword (`Documentos\e-Sword`, arquivos `.notx`,
  `.jnlx`, `.topx`; formatos ainda não examinados).
- **T42** Exportar estudo em Markdown e Word.

## M5 — Produto distribuível

- **T50** Assistente de importação na interface (hoje é linha de comando).
- **T51** Casca desktop; decidir entre Tauri e Electron.
- **T52** Tela de créditos e licenças; revisão do que pode ser distribuído.
  (depende de P1)

## M6 — Opcional

Tradução local sob demanda, léxico breve em português, perguntas com resposta
citada: ver [IDEIAS.md](IDEIAS.md) (B04, B05, B19). Dependem de P3 e P4.


## M9 — Fontes MySword (análise de 2026-11-23, `docs/ANALISE-MYSWORD.md`)

Pasta do Drive com 55 módulos MySword distintos (formato SQLite). Nenhum foi
importado na base em uso; o leitor existe desde T104. Conferir a licença na origem antes de importar cada um (ver o relatório).

### T104 — Leitor de módulos MySword (Bíblia e dicionário)
- **Fazer:** `importer/mysword.py` lê `Details`, `Bible` e `dictionary`, com a
  mesma marcação GBF do theWord (reaproveitar `importer/theword.py`). Módulos
  com `encryption` diferente de zero são pulados sem abrir (D008).
- **Aceite:** o leitor abre `web.bbl.mybible` (31.102 versículos) e
  `strong.dct.mybible` (14.696 verbetes) sem erro; procedência por módulo e
  chave preservadas; `verify.py` continua passando.
- **Tamanho:** M.
- **Estado:** concluída (ver "Estado das tarefas"). Formato verificado em
  FORMATOS.md, seção MySword. Nada foi importado em `data/library.db`: quais
  módulos entram é T105–T108. Os 53 arquivos estão numa pasta temporária fora
  do projeto (D007).

### T105 — Dicionário Strong completo (BDB, Thayer, Strong)
- **Fazer:** importar `strong.dct.mybible` (versão 2.2, 2025-09-01) como
  dicionário de origem `MySword`. Substitui Dodson e AHLB como fonte do painel
  Strong quando houver número coberto.
- **Aceite:** G26 e H430 mostram original, transliteração e definição do
  léxico completo; a fonte aparece no painel; o texto do AHLB deixa de ser
  servido se o novo cobrir o mesmo número. Decidir a regra de precedência em
  DECISOES.
- **Licença:** domínio público indicado no módulo; formatação de Timothy Morton
  (Bible Analyzer) "courtesy". Conferir na origem antes de servir no site.
- **Estado (2026-11-23):** decisão do usuário: **não substitui** (D038); as fontes ficam
  separadas no painel. Importada na candidata (ver "Estado das tarefas").
- **Tamanho:** M. Depende de T104.

### T106 — Bíblia Livre (BLIVRE) como texto de demonstração pública
- **Fazer:** importar `biblialivre.bbl.mybible` (31.102 versículos, 5 vazios
  a conferir). Crédito "BLIVRE" e data da versão na tela de créditos (T52).
- **Aceite:** 5 versículos vazios conferidos na fonte ou sinalizados; aparece
  no seletor de versões; é a única versão servida sem código de acesso
  na demonstração (a decidir com T52).
- **Licença:** CC BY 3.0 BR, conferida no GitHub da BLIVRE em 2026-11-23:
  uso comercial permitido, atribuição obrigatória, sem compartilhamento
  obrigatório.
- **Estado (2026-11-23):** importada na candidata; aviso dos vazios com as referências. Falta a
  parte de T52 (créditos e acesso sem código).
- **Tamanho:** P. Depende de T104 e de T52.

### T107 — Strong em português (SBB), só uso pessoal
- **Fazer:** importar `Strongs_BR.dct.mybible` marcado como uso pessoal. A
  palavra original vem corrompida (G26 em letras hebraicas; H430 com escape
  RTF): usar a palavra original do `strong.dct` pelo mesmo número.
- **Aceite:** nunca servido pelo site público (teste automatizado de
  `/api/strong` com a base de demonstração); aparece só na base local.
- **Licença:** © 2002 Sociedade Bíblica do Brasil; "uso pessoal, venda
  proibida" no próprio módulo. Não servir publicamente.
- **Tamanho:** P. Depende de T104 e T105.

### T108 — Grego do Novo Testamento (OpenGNT), para estudo
- **Fazer:** importar a variante `OpenGNT.bbl.mybible` (27 livros, 7.941
  versículos, Strong e morfologia), como texto grego de estudo. Não importar
  `OpenGNTnet` (texto NET, só não comercial com crédito) nem `OpenGNTbe`
  (tradução Berean, "all rights reserved") até confirmar a permissão.
- **Aceite:** Jo 1:1 mostra as palavras gregas com Strong ligado ao painel;
  procedência por módulo; a tela de créditos (T52) registra CC BY-SA 4.0 e a
  atribuição "Open Greek New Testament Project by Eliran Wong".
- **Licença:** texto base CC BY-SA 4.0, conferido no README do GitHub em
  2026-11-23. Uso declarado: estudo pessoal, não comercial. Compartilhamento
  pela mesma licença se o módulo ou derivados forem redistribuídos; isso
  inclui publicar no site (decisão em T52 e na outra conversa jurídica).
  Camadas Berean e Mounce: termos não conferidos.
- **Cobertura:** 7.941 versículos; o NT padrão tem cerca de 7.957. Conferir
  a diferença antes de usar como referência.
- **Tamanho:** M. Depende de T104 (concluída; o leitor genérico ainda grava transliteração e glosa no texto do OpenGNT).

### Ideias da pesquisa em background (2026-11-18)

Marcadas como **necessária** (lacuna real frente aos programas) ou **criativa**
(diferencial a validar com o usuário antes de construir).

- **T91** *Necessária:* importar as **Topic Notes** e o **Journal** do e-Sword com
  procedência, como a T41 faz com as notas por versículo. Antes: localizar o
  arquivo de origem (o `study.notx` visto tem só a tabela Verses; os outros
  dois não foram encontrados nesta visita) e registrar o formato em FORMATOS.
- **T92** *Necessária.* **Concluída** (2026-11-18): faixa "Continuar de onde parou" ao abrir sem endereço, com a última leitura e o último estudo (guardados só no navegador). Testada: abrir, voltar à leitura e ao estudo. Descrição original: ao abrir o app, mostrar a última
  passagem lida e o último estudo aberto. Os programas não fazem isso de forma
  clara; é um ganho pequeno e barato.
- **T93** *Criativa:* mapa de conexões das notas: o grafo que já existe (graph.js)
  mostra passagens, tópicos e notas ligados, para o usuário ver quais partes do
  texto ele mais estuda. Não é texto gerado; é uma visualização do próprio
  estudo.
- **T94** *Criativa:* história de estudo por palavra: contar quantas vezes o
  usuário abriu um Strong (ex.: G3956) e mostrar as notas que o citam. Útil para
  lembrar o que já estudou sobre um termo.
- **T95** *Necessária, depende de decisão:* exportar estudos para Google Docs.
  Exige conta e autorização do usuário; fica com a decisão sobre bibliotecas
  (D003) e o formato de intercâmbio. Não implementar sem essa aprovação.


### Ideias da rodada 3 do theWord, ponderadas (2026-11-18)

Peso considera escopo, custo, procedência e a regra de biblioteca padrão (D003).

- **T96** NEAR com alcance configurável na busca. *Peso: baixo custo, valor
  moderado.* O FTS5 já suporta NEAR; falta expor o alcance na interface.
- **T97** Copiar todos os versículos de uma busca (para o estudo ou para a
  exportação). *Peso: baixo custo, valor claro.* Liga-se à exportação (T42) e aos
  estudos (D5).
- **T98** Conjuntos de referências cruzadas escolhidos e ordenados pelo usuário,
  em vez da ordem fixa atual (curadas, depois co-citação). *Peso: médio; exige
  desenho de ordem e de conjuntos; é o que mais aproxima o estudante do seu
  próprio critério.*
- **T99** Diário de oração e louvor com datas que se repetem, ligado ao estudo.
  *Peso: criativo, a validar.* Dados pessoais: ficam só em `user.db`. Relaciona-se
  com T89 (diário de estudo); pode ser a mesma coleção com uma etiqueta.
- **T100** Sugestão de ortografia ("você quis dizer?") quando a busca não acha
  nada. *Peso: baixo, depende de um léxico de palavras; avaliar depois.*
- **Não copiar:** a densidade de opções ligadas e desligadas (muitas caixas de
  seleção sem explicação). Se houver opções, cada uma precisa de um rótulo claro.

## M8 — Estudo guiado (levantamento dos programas, 2026-11-18)

Origem: `docs/ESTUDO-PROGRAMAS.md`, navegação no theWord e no e-Sword com olhar
de estudante. Nada aqui foi implementado ainda; cada item precisa de
aceitação própria antes de entrar em execução.

- **T80** (confirmado na rodada 2: o Vocabulário do theWord guarda referência ao módulo, não cópia) Memorização e revisão espaçada sobre versículos lidos e notas, com
  procedência. Referência: "Memorização de versículos" do theWord (cartões e
  quatro avaliações). Diferencial: os cartões vêm do próprio estudo.
  Depende de T40 (notas) e de decisão sobre o algoritmo (SM-2 ou Leitner).
- **T81** Backlinks de notas: no painel do versículo, "notas que citam este
  versículo", a partir das notas de `user.db`. Diferencial sem equivalente no
  theWord nem no e-Sword.
- **T82** Leitura diária ou plano de leitura, com marcação de intervalo de versículos como lido e as notas do dia. Referência:
  "Leitura diária" do theWord.
- **T83** Comparar com um clique: abrir o paralelo sem etapa de seleção de
  textos (o theWord pede "Selecionar textos da Bíblia" antes). Já existe T62;
  falta o atalho e o estado vazio sem atrito.
- **T84** Rótulos e atalhos visíveis: os atalhos de tecla de função do theWord
  não aparecem no painel. Nosso `?` já lista os atalhos; falta o menu "Exibir"
  com rótulos.
- **T85** Estudo de palavra com ocorrências em contexto, no painel Strong
  (pelo menos as cinco primeiras, com o trecho). Ponto de comparação: os léxicos
  do theWord em abas; o nosso painel deve mostrar o termo original e as
  traduções sem abrir cada léxico.
- **T86** Levantamento do e-Sword: **concluído** na segunda visita (menus Tools,
  Options e Download; Super Search; Topic Notes). Ver `docs/ESTUDO-PROGRAMAS.md`.
- **T87** Notas por tópico, além das notas por versículo: o e-Sword tem a aba
  Topic Notes, em que a anotação segue um assunto escolhido (ex.: "ansiedade"),
  e não uma passagem. Diferencial para a área de Estudos: um tópico pode reunir
  notas de várias passagens. Depende de T40 e do desenho D5.
- **T88** Busca avançada com escopo escolhido antes de buscar (toda a biblioteca,
  uma obra, um livro) e modo de palavras (todas, qualquer, frase). Referência:
  Super Search do e-Sword. A nossa busca já tem ponte e filtros; falta o escopo
  explícito.
- **T89** Diário de estudo separado das notas por versículo. Referência: Journal
  Notes do e-Sword. Pode ser uma coleção de notas sem passagem em `user.db`.

## M10 — Correções de UX (relatório do agente de navegação, 2026-11-23)

Origem: agente com navegador no desktop e no celular, sem alterar arquivos nem
gravar dados. Cada item tem aceitação própria: testar no navegador (desktop e
375 px) e rodar `python -m unittest discover -s tests`. Prioridade: alta,
média, baixa.

### Alta

- **T110 — Botão "← João 1:1" do painel Palavra.** `onclick: showVerse` recebe
  o evento como referência e o servidor responde 400. Aceitação: o botão volta
  ao versículo sem erro, em desktop e celular. Estado: concluída (branch
  `ux-correcoes-t110`, ver `git log`). Testado no navegador: João 3:16 em KJV,
  Palavra G1161, "← João 3:16" volta ao versículo sem erro; 122 testes OK.
  Celular não testado.
- **T111 — Mensagem de erro enganosa.** A mensagem manda verificar o servidor
  mesmo quando ele está no ar. Aceitação: a mensagem diz a causa real (falha
  de rede, tempo esgotado, erro do servidor) e não culpa o servidor sem motivo.
  Estado: concluída (branch `ux-correcoes-t110`). Falha de rede (`TypeError` de
  fetch) diz "Não foi possível conectar ao servidor..."; demais erros mostram
  a causa. Testado no navegador com as duas falhas simuladas; 122 testes OK.
- **T112 — Versículo abre em cerca de 3 s.** As consultas (versão, comentários,
  "Parecidas") são feitas em sequência; "Parecidas" espera até 2 s pelo serviço
  parado. Aceitação: consultas em paralelo; serviço indisponível lembrado e
  não repetido a cada versículo.
  Estado: concluída (branch `ux-correcoes-t110`). Consultas do versículo em
  `Promise.all` (app.js); `api_similar` lembra a falha por 30 s
  (`SIMILAR_DOWN_SECONDS`). Medido no servidor ao vivo: 1ª consulta de
  `/api/similar` 2.075 ms (serviço parado), seguintes 9 a 10 ms; versículo
  abre com o texto visível em cerca de 1,2 s. Não coberto por teste
  automatizado. A primeira consulta a cada 30 s ainda espera os 2 s.
- **T113 — Versão em inglês na busca.** Sem versículos, sem explicação, com
  botões de copiar e adicionar visíveis. Aceitação: aviso claro de que a versão
  não tem versículos buscáveis, e botões que não se aplicam ficam ocultos.
- **T114 — Celular: opções ocupam a busca.** A primeira tela de busca abre com
  as opções expandidas e os resultados fora da tela. Aceitação: opções
  recolhidas por padrão; os primeiros resultados aparecem sem rolagem em 375 px.

### Média

- **T115 — Plano de leitura de hoje** corta o capítulo final no painel.
- **T116 — Respostas lentas sobrescrevem o painel atual**, e "voltar" leva a
  uma busca antiga. Aceitação: descartar respostas de consultas antigas
  (contador de requisição, como em D037).
- **T117 — Barra do desktop com 15 botões de mesmo peso.** "Tópicos" e "Temas"
  se confundem; "Mapa" e "Linha do tempo" são notas do estudante, não um mapa.
  Aceitação: hierarquia clara e nomes que não criam expectativa errada.
- **T118 — Estudo de palavra com dados inconsistentes.** A contagem de
  ocorrências não bate com os chips, o título vem sem acentos e as fontes estão
  só em inglês. Aceitação: contagem igual à dos chips; título com acentos.
- **T119 — Aba "Por sentido" fora do ar** mostra mensagem técnica. Aceitação:
  texto em português simples, com o que o usuário pode fazer.

### Baixa

- **T120 — Setas não trocam de capítulo.**
- **T121 — Falta atalho "pular para o texto"**, e os versículos são controles
  de tabulação.
- **T122 — Números de versículo com 11,6 px**, pequenos demais. Aceitação:
  legíveis em 375 px, sem alterar o alinhamento da leitura.
