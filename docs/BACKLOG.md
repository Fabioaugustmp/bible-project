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
| T33–T34 (M3) | pendente: busca por significado na interface e passagens parecidas |
| T60 | concluída: seis cores por tipo (`--type-*` em style.css, claro e escuro) e etiquetas nas seções do painel, em cada item (versões, referências, comentários, citados, verbetes abertos), nos resultados de busca e na seção Léxicos do painel Palavra; Léxico = Dodson, AHLB, LSJ, MLSJ, KJC, LXXHebGreek. Contraste do texto medido com WCAG (painel e fundo da leitura): tema claro de 4,88:1 (comentário, sobre o fundo da leitura) a 6,96:1; tema escuro de 7,46:1 a 10,64:1; testado em Jo 3:16, busca "graça" e painel Palavra (G25) nos dois temas, sem erros no console; revisão: a etiqueta escrita ficou só onde os tipos se misturam (Citado em, dicionários e livros na busca, item aberto, léxicos); seções homogêneas mostram uma barra na cor do tipo no título |
| T61 | concluída (EC9, D018): botão Fixar e 'Fixar ao lado', coluna com abas, divisórias por mouse e teclado, arranjo guardado; testada em 1280, 1024, 768 e 375 px e nos dois temas |
| T65 | concluída (EC8, D019): grafo no painel do versículo (Lista/Grafo), posicionamento próprio em `app/static/graph.js`; centros e isolado conferidos nos 5 versículos, 0 rótulos sobrepostos, recentrar 45 ms com cache; só lista abaixo de 760 px |
| T64 | concluída: botão 'Dic.' abre as 26 obras de dicionário e livro; índice alfabético, filtro por texto e paginação (`/api/titles`); verificado com o Easton (382 títulos com A, 'abin' acha Abinadab, verbete abre). Dic Port (36 mil) não foi medido |
| T66 | concluída (Haiku): faixa com 66 barras por livro, agrupadas em 8 grupos; clique filtra a lista; contagem pelo mesmo ranqueamento da lista (`/api/xref-books`); Sl 23:1 mostra Ez 29, Jo 34, Is 19, 1Pe 3; Gn 1:1 mostra Sl 43, Pv 13, Jo 19. Só no modo Lista |
| T63 | concluída (Haiku): 'Acompanhar na leitura' em cada comentário do painel fixa um comentário que troca o trecho ao mudar de versículo (85 a 265 ms, critério 0,3 s) e ao rolar o texto (versículo do meio da tela); citações clicáveis; sobrevive a recarregar. `/api/commentary` (2 a 5 ms). JFB em Rm 8 |
| T62 | concluída (Haiku; o roteiro previa Sonnet, mas não houve condição de parada): botão '‖' liga o modo paralelo; até 4 versões lado a lado, alinhadas por versículo (linhas com a mesma altura), hebraico com dir=rtl; escolha guardada. Testado com ARA + ACF + KJV (João 3:16), ARA + WLC (Sl 23:1) e limite de 4. Sem títulos de seção nem Strong nesse modo; em tela estreita, as colunas empilham |
| T40–T42 (M4) | pendente |
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
