# Formatos dos módulos

O que foi verificado diretamente nos arquivos de amostra (`modules-sample/`)
em 2026-11-16. O que ainda não foi verificado está marcado como tal.

## Onde ficam

| Programa | Pasta |
|---|---|
| e-Sword | `C:\Program Files (x86)\e-Sword` (cópia idêntica em `Documentos\e-Sword`) |
| theWord | `C:\ProgramData\The Word` (módulos); `C:\Program Files (x86)\The Word` só tem o programa |

## e-Sword

Todos são bancos SQLite com uma tabela `Details` (descrição, abreviação).

| Extensão | Tabelas | Observações |
|---|---|---|
| `.bblx` Bíblia | `Bible(Book, Chapter, Verse, Scripture)` | 31.102 linhas. Texto com fragmentos RTF. |
| `.cmtx` comentário | `Verses(Book, ChapterBegin, ChapterEnd, VerseBegin, VerseEnd, Comments)`, `Chapters`, `Books` | RTF; acentos como `\u231?`. Referências no texto como `Mat_22:30`. |
| `.dctx` dicionário | `Dictionary(Topic, Definition)` | RTF simples. |

Números Strong (em `ara_ra_com_strongs.bblx`) vêm depois da palavra, como
`{\cf11\super H7225}`. Um segundo código entre colchetes, como
`{\cf11\super H1254 [H8804]}`, é a análise do verbo.

Não há campo de idioma; o importador estima pelo texto.

## theWord

| Extensão | Formato | Observações |
|---|---|---|
| `.ont` Bíblia completa | texto, uma linha por versículo | 31.102 linhas na ordem canônica, depois linhas `chave=valor` (id, lang, descrição). |
| `.ot` / `.nt` | igual | 23.145 ou 7.957 linhas. |
| `.twm` | SQLite | `config(name, value)` traz título, autor, idioma e `type` (1 dicionário, 2 comentário). |
| `.ontx`, `.ntx` | binário, cabeçalho `TWENCBMOD` | **Criptografado. Não é lido.** `.ntx` não foi testado, presumido igual. |

Codificação dos `.ont`: `tr.nt` é UTF-8 com BOM; `jfa-rc(pt).ont` é
Windows-1252. O importador tenta UTF-8 e recorre a Windows-1252.

Tags nas Bíblias: `<WG976>` / `<WH430>` (Strong, depois da palavra),
`<WT...>` (morfologia), `<wt>` (início de palavra), `<BR>`, `<RF>...<Rf>`
(nota), `<TS>...<Ts>` (título).

Comentário `.cmt.twm`: `content(topic_id, data)` ligado a
`bible_refs(topic_id, bi, ci, fvi, tvi)` — livro, capítulo, versículo inicial
e final. `ci = 0` é introdução do livro; `fvi = 0` é introdução do capítulo.

Dicionário `.dct.twm`: `topics(id, subject)` ligado a `content(topic_id, data)`.

Ambos trazem `bible_link_search(topic_id, data)`: a lista de versículos
citados em cada tópico, uma por linha, no formato `,livro.capítulo.versículo,n`.

O conteúdo é RTF completo ou fragmento. Referências bíblicas aparecem como
campos `HYPERLINK "tw://bible.*?id=9.7.1"`.

### Conteúdo dos `.twm`: quatro variantes (verificado em 2026-11-16)

Levantamento sobre os 81 módulos instalados. A coluna `content.data` pode vir como:

| Variante | Como reconhecer | Tratamento |
|---|---|---|
| RTF em texto | começa com `{\rtf` ou é fragmento RTF | `importer/rtf.py` |
| Comprimido | bytes começam com `78 DA` (zlib); `config.compressed = 1` | descomprimir e tratar o resultado |
| RVF (RichView) | começa com `-8 1 3`; `config.content.type = rvf` | `importer/rvf.py` |
| Criptografado | `config.secure = 1` ou `do.encrypt = 1`; bytes sem padrão | **não é lido**; o módulo é registrado como ignorado |

O importador decide pelo conteúdo, não pelos campos de `config`, porque há
módulos com `encrypted = 1` cujo texto está aberto (Fausset, Hitchcock).

Colunas declaradas como texto podem conter bytes que não são UTF-8 (RVF
gravado em coluna `text`), por isso a leitura usa `cast(data as blob)`.

**RVF.** Sequência de registros; cada um começa com uma linha ASCII de
inteiros (`estilo n_strings parágrafo ...`). Estilo >= 0 é texto: seguem
`n_strings` textos em UTF-16LE, cada um terminado por U+2029. Estilo -9 com
duas strings é um bloco binário de estilos precedido do tamanho em 4 bytes.
Imagens, tabelas e outros itens de estilo negativo não são interpretados: o
leitor pula até o próximo cabeçalho e marca o tópico como lido parcialmente.

### Tipos de `.twm` (`config.type`)

| type | Conteúdo | Importado |
|---|---|---|
| 1 | dicionário / léxico | sim |
| 2 | comentário | sim |
| 3 | livro (`.gbk`) e devocional (`.dev`) | sim, como `book` |
| 4 | mapas (`.map`) | não (são imagens) |
| 5 | plano de leitura (`.rdp`): tabelas `calendar`, `sessions` | não |
| 10 | referências cruzadas (`default.xrefs.twm`, tabela `xrefs`) | não; útil para a Fase 5 |
| 13 | layouts do programa | não |
| sem type | títulos de seção (`hdgs`) e parágrafos (`prgs`) | não; úteis para a leitura |

Os bancos `.twdb` (bases de grego e hebraico) têm `secure = 1` e não são lidos.

### Marcação por palavra nas Bíblias do theWord (verificado em 2026-11-16)

Cada palavra começa em `<wt>`. Conforme o módulo:

| Módulo | Uma palavra |
|---|---|
| `tr.nt` | `<wt>ηγαπησεν<WG25><WTV-AAI-3S l="αγαπαω">` |
| `BSB Interlinear NT-Grk.nt` | `<wt><O> ἠγάπησεν<o><T> ēgapēsen<t><E> loved<e><WG25><WTV-AIA-3S l="ἀγαπάω">` |
| `BSB Reverse Interlinear.ont` | `<wt><E> loved<e><OG> ἠγάπησεν<og><T> ēgapēsen<t><WG25><WT… l="…">` (NT); no AT o original vem em `<O>…<o>` com `<WH…>` |
| `kjv.ont` | `<FR> loved<Fr><WG25>` (sem `<wt>`; `<FR>` = palavras de Jesus, `<FI>` = itálico) |

`<E>` inglês, `<O>`/`<OG>` original, `<T>` transliteração, `<WG>`/`<WH>`
Strong, `<WT…>` morfologia com o lema em `l="…"`. O interlinear reverso tem
443.627 palavras (305.496 hebraicas, 138.131 gregas). O importador atual
remove as tags e concatena o conteúdo, o que mistura as três linhas no texto
(defeito tratado em EC1, `docs/EXECUCOES-CRITICAS.md`).

### Referências cruzadas, títulos e parágrafos do theWord

`default.xrefs.twm`: `xrefs(id, vi1, vi2)`, 19.671 pares.
`default.english.hdgs.twm`: `headings(id, vi, pos, level, content)`, 5.289.
`default.prgs.twm`: `paragraphs(vi, typ)`, 14.074.
`vi = livro<<24 | capítulo<<16 | versículo<<8` (16843008 = Gn 1:1; os três
primeiros pares de Gn 1:1 apontam para Jó 38:4, Sl 33:6 e Sl 89:11). O byte
baixo e o campo `typ` ainda não foram examinados.

Planos de leitura (`.rdp.twm`): `sessions(id, sid, itemorder, URL)` com
intervalos como `1.1.1-1.3.24`.

### Bíblia do e-Sword com texto cifrado (verificado em 2026-11-16)

`gnt-tr_.bblx` (Textus Receptus com Strong, módulo oficial protegido) tem a
coluna `Scripture` como blob cifrado em todos os 7.957 versículos. O importador
registra o módulo como ignorado. O mesmo texto existe aberto no theWord (`tr.nt`).

### Bíblias "com cabeçalhos" do e-Sword

A tabela `Bible` traz uma linha de cabeçalho com textos no lugar dos números
('Livro', 'Cap', 'Verso'). Os títulos de seção vêm no início do versículo, em
um grupo de negrito centralizado (controles `b` e `qc`), e vão para
`verses.heading`. Títulos de salmo usam itálico centralizado (`i` e `qc`) e
ficam no texto. Essas cópias perdem Apocalipse 22:21 em três versões e têm
aspas duplicadas; ver D011.

### Outras tags das Bíblias do theWord (verificado em 2026-11-16)

- `<TS>título<Ts>`: título de seção antes do versículo. O interlinear reverso
  BSB tem 3.082; vão para `verses.heading`.
- `<RX 43.1.1+4>`: referência cruzada embutida (livro.capítulo.versículo e
  quantidade de versículos seguintes), presente no interlinear reverso BSB.
  Hoje é descartada; é uma fonte a mais para a tarefa T25.
- `<V1{><V1}><V2«wt»…«WG…»>` no TR: variante textual de Scrivener, embutida
  em uma tag com `«»` no lugar de `<>`. É descartada. Lucas 17:36 só existe
  como variante, por isso o TR importado tem 7.956 versículos.
- `<XWG…>` na KJV: código repetido de uma expressão dividida; ignorado.
- `<FR>` palavras de Jesus, `<FI>` itálico (palavras acrescentadas), `<FO>`
  citação do AT, `<RF>…<Rf>` nota: a marcação é removida e a nota, descartada.

### Detalhes confirmados dos auxiliares do theWord (2026-11-16)

- `xrefs.vi2`: o byte baixo é a extensão do trecho de destino, em versículos a
  mais (0 em 18.898 pares, 1 em 594, até 31). Em `vi1` é sempre 0. São 19.671
  pares a partir de 8.471 versículos.
- `<RX …>` nos interlineares BSB: 1.935 na forma `livro.cap.vers+n` e 83 sem
  o `+n`. Cerca de 70 têm a forma `livro.n.0` (por exemplo `4.1.0`, `12.2.0`),
  de significado não confirmado; são ignorados e contados em `import_log`.
- `paragraphs(vi, typ)`: `typ` vale 1 ou 2, em proporções opostas nos dois
  módulos (`default.prgs`: 2.980 e 11.094; `default2.prgs`: 11.213 e 240). O
  significado não foi confirmado, então os parágrafos não são importados.
- `headings`: todos com `pos = 1` e `level = 1`; os 5.289 títulos são em inglês.

### Citações bíblicas dentro dos comentários e verbetes (verificado em 2026-11-17)

**theWord, RTF.** Campo `{\field{\*\fldinst HYPERLINK "alvo"}{\fldrslt texto visível}}`.
Alvos de versículo encontrados (contagem nas 300 primeiras entradas de cada módulo):

| Forma | Ocorrências |
|---|---|
| `tw://bible.*?id=L.C.V` (com ou sem `|_AUTODETECT_|`) | cerca de 92 mil |
| `tw://bible.*?id=L.C.V-L.C.V` | cerca de 8 mil |
| `tw://bible.*?id=L.C.V-V` | cerca de 2 mil |
| `tw://[self]?L.C.V` (link do comentário para o próprio versículo) | 265 |
| `tw://bible.*/?id=...` (erro de digitação tolerado pelo theWord) | raro, visto no Four-Fold Gospel |

Outros alvos não são versículo e ficam como texto: `tw://[strong]?H1322`,
`tw://[self]?tid=...` (outro tópico), `tw://*.*?txt=Etymology` (busca de texto).
Na concordância KJC e em outros módulos o texto visível é o marcador `[vref]`;
o importador o troca pelo rótulo em português (`Êx 6:16-20`).

**theWord, RVF.** O alvo vem no fim da linha de cabeçalho do item de texto:
`6 1 -1 9 0 "tw://bible.*?id=9.6.18|_AUTODETECT_|"`. O mesmo alvo aparece também
no cabeçalho de itens vizinhos que não são o link; só o item curto (até 40
caracteres) e com número é tratado como a citação.

**e-Sword.** Não há links; as citações estão escritas no texto:
- abreviação inglesa do e-Sword com sublinhado: `Exo_19:3-6`, `1Sa_16:10-11`
  (63 abreviações distintas; o Diário Viver mistura algumas portuguesas no mesmo
  formato, como `Hb_4:12`);
- abreviação portuguesa com ponto: `Is 48.6-7; Jr 31.22`, `1 Pe 2.3`, e
  continuações do mesmo livro (`Sl 10.9; 17.12; 22.13`).
- As notas da Reina-Valera e o Diário Viver foram traduzidos do espanhol por
  máquina e trazem grafias como `2 Rss`, `2 Rseis`, `1 Smamuel` (Reis, Samuel),
  `Mau` (Malaquias) e `Feitos` (Atos). Há também referências erradas na origem
  (`2 Rss 12.28`, que não existe); citação para versículo inexistente é ignorada.

**Lista de citados do theWord (`bible_link_search`).** Expande intervalos
versículo a versículo e usa versículo 0 para algumas marcas de capítulo
inteiro sem link correspondente no texto. Nos módulos com
`compressed.search.data = 1` (Biblical Illustrator) a lista vem compactada e não
é lida; para eles, a lista de citados passa a vir das citações encontradas no texto.

## MySword (`*.mybible`) — verificado em 2026-11-23 (T104)

Verificado nos 53 arquivos `.mybible` da pasta do Drive (ver
`docs/ANALISE-MYSWORD.md`), abertos com `mode=ro&immutable=1`. Lidos por
`importer/mysword.py`; `source = 'mysword'` na tabela `modules`.

- Todos são SQLite. O tipo está no nome (`.bbl`, `.dct`, `.bok`, `.cmt`), mas o
  leitor decide pelas tabelas: `Bible` → Bíblia, `dictionary` → dicionário,
  `journal` → livro (ainda não importado), `commentary` → comentário (nenhum na amostra).
- **Details:** nas Bíblias a tabela é `Details` com colunas em maiúscula
  (`Title`, `Description`, `Abbreviation`, `Comments`, `Language`, `Strong`...); nos
  dicionários e livros é `details` com colunas em minúscula. O leitor normaliza a caixa.
  `Title` e `Language` faltam em várias Bíblias (WEB, BBE, AKJV, NET, ISV): o título
  vem de `Description` e o idioma é estimado pelo texto. A BSB declara `en` (duas letras).
- **Proteção:** só `abp` e `HiSB` têm `encryption = 2` e `compressed = 1`. Nos demais
  as colunas não existem ou são nulas. Com qualquer uma diferente de zero o leitor
  para depois de ler `Details` (D008).
- **Bíblia:** `Bible(Book INT, Chapter INT, Verse INT, Scripture TEXT)`, sem linha de
  cabeçalho, sem livro fora de 1–66. Marcação GBF igual à do theWord (`<WG26>`, `<FI>`,
  `<FR>`, `<RF>…<Rf>`, `<TS>…<Ts>`, `<CM>`, `<PF1>`, `<PI3>`, `<CI>`), com HTML
  solto (`<br>`, `<b>`, `<em>`) e entidades (`&amp;`, `&hellip;`, `&#1488;`) em poucas.
  Referências cruzadas como `<RX 43.1.1>` e `<RX 43.1.1-5>` (até o versículo 5; o
  theWord usa `+n`). Há versículos só com nota de rodapé (ficam vazios depois da
  limpeza e não são gravados) e versículos fora da versificação KJV, mantidos como no
  e-Sword.
- **WEB (`web.bbl.mybible`, v1.5.3 de 2025-08-04):** 31.103 linhas, não 31.102 como
  dizia a análise: Rm 14:24-26 (a doxologia no fim do cap. 14) existe e Rm 16:26-27
  não; Lc 17:36, At 8:37, 15:34, 24:7 e Rm 16:25 só têm nota. Gravados: 31.098.
  Jo 3:16: "For God so loved the world, that he gave his only born Son, that whoever
  believes in him should not perish, but have eternal life." (origem `43.3.16`).
- **Dicionário:** `dictionary(word, data)`, às vezes com `relativeorder`; `word` é a
  chave (único em todos os verificados), `data` é HTML. Links: `#b43.3.16` e
  `#b43.3.16-18` (versículo; viram citação clicável em `refs`), `#sG25` e `#dG25`
  (Strong e dicionário; fica só o texto), `r…` (abreviaturas do Abbott-Smith). Chave de
  origem gravada: `dictionary:<rowid>`.
- **Strong (`strong.*.dct.mybible`):** há duas cópias. A de 35,3 MB é a v2.2
  (2025-09-01) com 14.700 verbetes: 14.696 com chave Strong e 4 prefixos hebraicos
  (`Hb`, `Hk`, `Hl`, `Hm`). A de 35,7 MB é a v2.0.3 (2015-06-22) com 14.696. Ambas
  trazem as referências (cerca de 349 mil links de versículo). G26 começa com
  "Original: ἀγάπη / Transliteration: agapē"; H430 com "Original: אלהים".
- **OpenGNT:** interlinear com `<Q><G>palavra<WG..><WT.. l="lema"><g><X>…<x><E>glosa<e><q>`.
  O leitor genérico grava a transliteração e a glosa no texto; tratar em T108.

## Notas do e-Sword (`study.notx`) — verificado em 2026-11-17

- É um SQLite 3 com uma única tabela: `Verses(Book INT, Chapter INT, Verse INT, Notes TEXT)`.
  `Book` segue a ordem canônica (43 = João), como nas Bíblias do e-Sword.
- `Notes` é RTF (`{\rtf1 ...}`) com acentos em `\'xx` (cp1252) e `\loch\af1\dbch...`
  de fonte. O conversor de `importer/rtf.py` decodifica os `\'xx` corretamente
  (`\'e9` vira `é`, verificado).
- Pasta: `Documentos\e-Sword\study.notx` (1 nota) e `Documentos\e-Sword\e-Sword\study.notx`
  (vazio). Só a primeira tem conteúdo.
- O texto pode começar com caracteres que o próprio usuário digitou (ex.: `x'No verso...`);
  isso é dado original e não é removido pela importação.
