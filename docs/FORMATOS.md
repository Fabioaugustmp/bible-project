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

Ainda não verificado: módulos com conteúdo comprimido ou em formato RVF,
livros (`.gbk`), devocionais (`.dev`), planos de leitura (`.rdp`), mapas
(`.map`) e os bancos `.twdb`.
