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
