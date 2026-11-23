"""Leitura dos módulos do MySword (`*.mybible`, SQLite): Bíblias e dicionários (T104).

Formato verificado nos arquivos reais em docs/FORMATOS.md (seção MySword):
- tabela `Details` (ou `details`, colunas com caixa variável): título, sigla,
  idioma, licença em `Comments` e, nos protegidos, `encryption` e `compressed`;
- Bíblia: `Bible(Book, Chapter, Verse, Scripture)`, com a marcação GBF do theWord;
- dicionário: `dictionary(word, data)` (às vezes com `relativeorder`), texto em HTML,
  com links `#bLIVRO.CAP.VERS` para versículos.

Módulo com `encryption` ou `compressed` diferente de zero é pulado sem ler o
conteúdo (D008). Livros (`journal`) e comentários ainda não são importados.
"""
import html
import re
import sqlite3
from html.parser import HTMLParser

from db import guess_lang, normalize_lang
from refs import CLOSE, MID, OPEN, extract
from rtf import tidy
from theword import _clean_verse, _decode, _short_title


def _open(path):
    """Somente leitura e sem travas: o arquivo de origem nunca é alterado."""
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro&immutable=1", uri=True)


def _details(src, tables):
    """Tabela Details -> dicionário com as chaves em minúsculas."""
    name = tables.get("details")
    if not name:
        return {}
    columns = [row[1].lower() for row in src.execute(f'pragma table_info("{name}")')]
    row = src.execute(f'select * from "{name}"').fetchone() or ()
    return {column: value for column, value in zip(columns, row)}


def _flag(value) -> int:
    if value is None:
        return 0
    try:
        return int(str(value).strip() or 0)
    except ValueError:
        return 1  # valor estranho num campo de proteção: tratar como protegido


def _text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return _decode(value)
    return str(value)


def _lang(details, sample: str) -> str:
    """Idioma declarado em Details; se faltar ou não for reconhecido, estimado pelo texto."""
    lang = normalize_lang(details.get("language"))
    if lang == "und":
        two = str(details.get("language") or "").strip().lower()[:2]
        lang = {"en": "eng", "pt": "por", "es": "spa", "el": "grc", "he": "heb", "la": "lat"}.get(two, "und")
    return lang if lang != "und" else guess_lang(sample)


def _meta(details, path, kind):
    title = _text(details.get("title")) or _text(details.get("description")) or path.name.split(".")[0]
    return {
        "kind": kind,
        "abbr": _text(details.get("abbreviation")).strip() or path.name.split(".")[0],
        "title": _short_title(title) if kind == "bible" else tidy(title)[:200],
        "author": _text(details.get("author")).strip() or None,
    }


# --- Bíblias ----------------------------------------------------------------

# Referência cruzada embutida: <RX 43.3.16>, <RX 43.3.16-18> (até o versículo 18)
# ou a forma do theWord <RX 43.3.16+2> (mais 2 versículos).
_XREF = re.compile(r"<RX (\d+)\.(\d+)\.(\d+)(?:([-+])(\d+))?[^>]*>")


def _xrefs(book, chapter, verse, line):
    found = []
    for to_book, to_chapter, to_verse, sign, number in _XREF.findall(line):
        to_verse = int(to_verse)
        if to_verse == 0:
            continue
        span = 0
        if number:
            span = int(number) if sign == "+" else max(0, int(number) - to_verse)
        found.append((book, chapter, verse, int(to_book), int(to_chapter), to_verse, span))
    return found


def _unescape_word(word):
    return (html.unescape(word[0]) if word[0] else word[0], *word[1:])


def read_bible(src, path, details, add):
    meta = _meta(details, path, "bible") | {"has_strongs": 0}
    rows, words, xrefs, outside, empty = [], [], [], 0, []
    for book, chapter, verse, raw in src.execute(
        "select Book, Chapter, Verse, cast(Scripture as blob) from Bible order by Book, Chapter, Verse"
    ):
        if not all(isinstance(number, int) for number in (book, chapter, verse)) or not 1 <= book <= 66:
            outside += 1
            continue
        line = _decode(raw or b"")
        xrefs.extend(_xrefs(book, chapter, verse, line))
        heading, text, tagged, verse_words = _clean_verse(line)
        text = html.unescape(text)
        if not text:
            empty.append(f"{book}:{chapter}:{verse}")
            continue
        if tagged:
            meta["has_strongs"] = 1
            tagged = html.unescape(tagged)
        rows.append((book, chapter, verse, text, tagged, html.unescape(heading) if heading else None,
                     f"{book}.{chapter}.{verse}"))
        words.extend((book, chapter, verse, pos, *_unescape_word(word))
                     for pos, word in enumerate(verse_words, start=1))
    src.close()
    if not rows:
        add.log("ignorado", "módulo sem versículos")
        return 0
    meta["lang"] = _lang(details, " ".join(row[3] for row in rows[len(rows) // 2:][:40]))
    module_id = add.module(meta)
    add.verses(module_id, rows)
    if meta["has_strongs"]:
        add.tokens(module_id, words)
    if xrefs:
        add.xrefs(module_id, xrefs)
    if outside:
        add.log("aviso", f"{outside} versículos de livros fora do cânon de 66 foram ignorados")
    if empty:
        add.log("aviso", f"{len(empty)} versículos vazios no módulo não foram gravados"
                f" (livro:capítulo:versículo): {', '.join(empty[:20])}")
    return len(rows)


# --- Dicionários ------------------------------------------------------------

_BLOCKS = {"p", "div", "br", "li", "ol", "ul", "tr", "table", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote"}
_HIDDEN = {"style", "script", "head", "title"}
_BLANK_LINES = re.compile(r"\n(?:[ \t]*\n)+")  # um bloco por linha, sem linha em branco
# Link para versículo: '#b43.3.16' ou '#b43.3.16-18'.
_BIBLE_HREF = re.compile(r"#b(\d+)\.(\d+)\.(\d+)(?:-(\d+))?$")


class _HtmlText(HTMLParser):
    """HTML -> texto, com o trecho visível dos links de versículo entre as marcas de refs.py."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.hidden, self.link_open = [], 0, False

    def handle_starttag(self, tag, attrs):
        if tag in _HIDDEN:
            self.hidden += 1
        elif tag in _BLOCKS:
            self.out.append("\n• " if tag == "li" else "\n")
        elif tag == "a" and not self.link_open:
            match = _BIBLE_HREF.match((dict(attrs).get("href") or "").strip())
            if match:
                book, chapter, verse, end = match.groups()
                target = f"tw://bible.*?id={book}.{chapter}.{verse}" + (f"-{end}" if end else "")
                self.out.append(f"{OPEN}{target}{MID}")
                self.link_open = True

    def handle_startendtag(self, tag, attrs):
        if tag in _BLOCKS:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in _HIDDEN:
            self.hidden = max(0, self.hidden - 1)
        elif tag in _BLOCKS and tag != "br":
            self.out.append("\n")
        elif tag == "a" and self.link_open:
            self.out.append(CLOSE)
            self.link_open = False

    def handle_data(self, data):
        if not self.hidden:
            # Fora de <pre>, quebras de linha no HTML são só espaço.
            self.out.append(re.sub(r"\s+", " ", data))


def html_to_marked(source: str) -> str:
    """HTML de um verbete -> texto com as citações marcadas (ver refs.extract)."""
    parser = _HtmlText()
    parser.feed(source)
    parser.close()
    if parser.link_open:
        parser.out.append(CLOSE)
    return tidy(_BLANK_LINES.sub("\n", "".join(parser.out)))


def read_dictionary(src, path, details, add):
    meta = _meta(details, path, "dictionary")
    rows, row_refs = [], []
    for rowid, word, data in src.execute(
        "select rowid, cast(word as blob), cast(data as blob) from dictionary order by rowid"
    ):
        topic = _decode(word or b"").strip()
        text, item_refs = extract(html_to_marked(_decode(data or b"")))
        if topic and text:
            rows.append((topic, text, f"dictionary:{rowid}"))
            row_refs.append(item_refs)
    src.close()
    if not rows:
        add.log("ignorado", "dicionário sem verbetes")
        return 0
    meta["lang"] = _lang(details, " ".join(row[1][:400] for row in rows[len(rows) // 2:][:40]))
    module_id = add.module(meta)
    add.entries(module_id, rows, refs=row_refs)
    return len(rows)


# --- Entrada ----------------------------------------------------------------

def read_module(path, add):
    src = _open(path)
    tables = {row[0].lower(): row[0] for row in src.execute("select name from sqlite_master where type = 'table'")}
    details = _details(src, tables)
    # D008: módulo protegido não é lido; só a tabela Details foi consultada.
    if _flag(details.get("encryption")) or _flag(details.get("compressed")):
        src.close()
        add.log("ignorado", f"módulo protegido do MySword (encryption = {details.get('encryption')},"
                            f" compressed = {details.get('compressed')}); não lido (D008)")
        return 0
    if "bible" in tables:
        return read_bible(src, path, details, add)
    if "dictionary" in tables:
        return read_dictionary(src, path, details, add)
    src.close()
    if "journal" in tables:
        add.log("ignorado", "livro do MySword (tabela journal) ainda não é importado")
    elif "commentary" in tables:
        add.log("ignorado", "comentário do MySword ainda não é importado")
    else:
        add.log("ignorado", f"tipo de módulo MySword não reconhecido (tabelas: {', '.join(sorted(tables))})")
    return 0


READERS = {".mybible": read_module}
