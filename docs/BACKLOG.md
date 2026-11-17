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
| P1 | Confirma o posicionamento acima? O projeto será público? | Sim; público muda M5 (assistente de importação, créditos, licença) |
| P2 | Ponte português↔inglês (M2) antes dos embeddings (M3)? | **Respondida: sim** (2026-11-17) |
| P3 | Dependências além da biblioteca padrão são aceitas (necessárias em M3)? | Sim, isoladas no indexador; registrar nova decisão que revê a D003 |
| P4 | Uso de modelo de linguagem (local ou por API) é aceito? | Só opcional e por último (M6) |
| P5 | Manter a página do Notion sincronizada? | Não: hoje ela espelha IDEIAS.md e está desatualizada em relação a este arquivo |

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
| 4 | M3 — busca semântica (T30–T34) | Opus | maior incerteza técnica; depende da resposta P3 | ver EC6 |
| 5 | M4 — notas e exportação (T40–T42) | Sonnet | formatos de notas do e-Sword ainda não examinados | ver backlog |
| 6 | M5 — produto distribuível (T50–T52) | Opus | decisões de arquitetura; depende de P1 | ver EC7 |

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
| T30–T34 (M3) | pendente |
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

## M3 — Busca semântica (embeddings)

- **T30** Verificar se as bibliotecas de embeddings funcionam em Python 3.14;
  escolher o ambiente e registrar decisão que revê a D003. (depende de P3)
- **T31** Conjunto de avaliação com dados da própria base: pares de referência
  cruzada e versículo ↔ comentário do mesmo versículo; medir recall@10.
- **T32** Indexar versículos e parágrafos de comentário, guardando modelo e
  versão junto dos vetores.
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
