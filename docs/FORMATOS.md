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
