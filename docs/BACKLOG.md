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

## Estado atual (2026-11-16)

- Funciona: importador (`importer/build.py`), verificação
  (`importer/verify.py`), servidor (`app/server.py`, porta 8377) e interface
  (leitura, painel do versículo, busca por palavra, ir para referência).
- `data/library.db`: base de **amostras** (8 módulos), a que o aplicativo abre.
- `data/library-full.db`: importação completa (72 módulos, 569 s, 1,15 GB),
  **com defeitos conhecidos e ainda não promovida**. Log em
  `data/import-full.log`.
- Importado na base completa: 18 Bíblias, 24 comentários, 24 dicionários,
  6 livros; cerca de 3 milhões de citações na tabela `links`.
- Módulos de origem: `C:\Program Files (x86)\e-Sword`,
  `C:\ProgramData\The Word`, `%APPDATA%\The Word`.
- Ambiente: Windows, Python 3.14 (só biblioteca padrão, D003), Node instalado,
  Rust não instalado.

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
| P2 | Ponte português↔inglês (M2) antes dos embeddings (M3)? | Sim: usa só dados existentes e sem dependências |
| P3 | Dependências além da biblioteca padrão são aceitas (necessárias em M3)? | Sim, isoladas no indexador; registrar nova decisão que revê a D003 |
| P4 | Uso de modelo de linguagem (local ou por API) é aceito? | Só opcional e por último (M6) |
| P5 | Manter a página do Notion sincronizada? | Não: hoje ela espelha IDEIAS.md e está desatualizada em relação a este arquivo |

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
| T01–T11 (M1) | pendente |
| T20–T25 (M2) | pendente |
| T30–T34 (M3) | pendente |
| T40–T42 (M4) | pendente |
| T50–T52 (M5) | pendente |

Uma tentativa de aplicar T01–T04 de uma vez falhou antes de rodar (erro de
shell) e **não deixou nenhuma alteração**; recomeçar do zero, uma tarefa por vez.

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
- **Fazer:** pular arquivos cujo SHA-256 e versão do importador não mudaram.
- **Aceite:** segunda execução sem mudanças em menos de 60 s, mesmas contagens.
- **Tamanho:** M.

### T11 — Testes automatizados
- **Fazer:** testes para `rtf.py`, `rvf.py` e os limpadores de versículo, com
  amostras sintéticas (sem texto protegido), usando `unittest`.
- **Aceite:** `python -m unittest` passa; cada defeito de T01–T05 tem um teste.
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
