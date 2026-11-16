"""Esquema da base única e utilitários comuns do importador."""
import re
import sqlite3

from canon import BOOKS, VERSES

IMPORTER_VERSION = "0.2.0"

SCHEMA = """
create table meta(key text primary key, value text);

create table books(book integer primary key, abbr text, name text, chapters text);

-- Um módulo importado, com a procedência do arquivo de origem.
create table modules(
    id integer primary key,
    source text not null,           -- 'esword' | 'theword'
    kind text not null,             -- 'bible' | 'commentary' | 'dictionary' | 'book'
    abbr text, title text, author text, lang text,
    has_strongs integer default 0,
    items integer default 0,
    origin_path text, origin_sha256 text, origin_size integer, origin_mtime text,
    importer_version text, imported_at text
);

create table verses(
    id integer primary key,
    module_id integer not null references modules(id),
    book integer, chapter integer, verse integer,
    text text,                      -- texto limpo
    tagged text,                    -- texto com Strong entre chaves, quando houver
    heading text,                   -- título de seção que antecede o versículo, quando houver
    origin_key text                 -- chave no arquivo de origem
);
create index verses_by_ref on verses(book, chapter, verse);
create index verses_by_module on verses(module_id, book, chapter, verse);

-- Uma linha por palavra das Bíblias com Strong (ver importer/tokens.py).
create table tokens(
    module_id integer not null references modules(id),
    book integer, chapter integer, verse integer,
    pos integer,                    -- ordem da palavra no versículo, a partir de 1
    surface text,                   -- como aparece no módulo; vazio = original sem tradução
    strong text,                    -- 'G25' / 'H7225'; nulo = texto sem código
    lemma text, morph text,
    original text, translit text, gloss text   -- só nos interlineares
);

-- Como cada idioma traduz cada Strong, com contagem (derivada de tokens).
create table strong_terms(
    strong text not null, lang text not null, term text not null,
    count integer not null,
    share real not null,            -- fração das ocorrências do Strong nesse idioma
    primary key (strong, lang, term)
) without rowid;
create index strong_terms_by_term on strong_terms(lang, term);

-- ref_start / ref_end = capítulo * 1000 + versículo.
-- Versículo 0 = introdução do capítulo; capítulo 0 = introdução do livro.
create table comments(
    id integer primary key,
    module_id integer not null references modules(id),
    book integer, ref_start integer, ref_end integer,
    text text, origin_key text
);
create index comments_by_ref on comments(book, ref_start, ref_end);

create table entries(
    id integer primary key,
    module_id integer not null references modules(id),
    topic text, text text, origin_key text
);
create index entries_by_topic on entries(topic collate nocase);

-- Versículos citados dentro de um comentário ('comment') ou verbete ('entry').
create table links(kind text, item_id integer, book integer, chapter integer, verse integer);
create index links_by_ref on links(book, chapter, verse);

create table import_log(
    id integer primary key, at text, level text, origin_path text, message text
);

create virtual table verses_fts using fts5(
    text, content='verses', content_rowid='id', tokenize="unicode61 remove_diacritics 2");
create virtual table comments_fts using fts5(
    text, content='comments', content_rowid='id', tokenize="unicode61 remove_diacritics 2");
create virtual table entries_fts using fts5(
    topic, text, content='entries', content_rowid='id', tokenize="unicode61 remove_diacritics 2");
"""


def create(path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.executescript("pragma journal_mode = off; pragma synchronous = off;")
    con.executescript(SCHEMA)
    import json
    con.executemany(
        "insert into books values (?, ?, ?, ?)",
        [(i + 1, abbr, name, json.dumps(VERSES[i])) for i, (abbr, name) in enumerate(BOOKS)],
    )
    return con


def rebuild_search(con: sqlite3.Connection) -> None:
    for table in ("verses_fts", "comments_fts", "entries_fts"):
        con.execute(f"insert into {table}({table}) values ('rebuild')")


def open_readonly(path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


# --- Strong -----------------------------------------------------------------
# Durante a limpeza, os códigos Strong viajam entre \x01 e \x02 para não se
# misturarem com o texto; no fim viram `{H7225}` (tagged) ou somem (text).

MARK_OPEN, MARK_CLOSE = "\x01", "\x02"
_MARK = re.compile(r"\s*\x01([^\x02]*)\x02")
_SPACES = re.compile(r"\s+")
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.;:!?])")


_CONTROLS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def strip_controls(text: str) -> str:
    """Remove caracteres de controle do texto de origem.

    Há módulos com lixo binário em alguns versículos; sem isto, um \\x01 da
    origem seria confundido com o marcador de Strong.
    """
    return _CONTROLS.sub("", text)


def split_strongs(marked: str):
    """Devolve (texto limpo, texto marcado ou None)."""
    if MARK_OPEN not in marked:
        return _SPACES.sub(" ", marked).strip(), None
    tagged = _SPACES.sub(" ", _MARK.sub(r"{\1}", marked)).strip()
    plain = _SPACE_BEFORE_PUNCT.sub(r"\1", _SPACES.sub(" ", _MARK.sub("", marked))).strip()
    return plain, tagged


# --- Idioma -----------------------------------------------------------------

_LANG_CODES = {"eng": "eng", "por": "por", "grc": "grc", "grk": "grc", "gre": "grc", "ell": "grc",
               "heb": "heb", "hbo": "heb", "spa": "spa", "esp": "spa", "lat": "lat"}


def normalize_lang(value) -> str:
    """'eng', 'English', 'Eng - English', 'grk' -> um código de três letras por idioma."""
    code = str(value or "").strip().lower()[:3]
    return _LANG_CODES.get(code, "und")


_STOPWORDS = {
    "por": set("que não uma para com os as dos das seu sua também são mas ele ao pelo".split()),
    "eng": set("the and of that with for his was not which shall unto is are this".split()),
    "spa": set("que los las una para con del sus pero también más como él por y el".split()),
}
_WORD = re.compile(r"[^\W\d_]+")


def guess_lang(sample: str) -> str:
    """Estima o idioma de um texto (módulos do e-Sword não o declaram)."""
    if sum("Ͱ" <= c <= "Ͽ" or "ἀ" <= c <= "῿" for c in sample) > len(sample) * 0.3:
        return "grc"
    if sum("֐" <= c <= "׿" for c in sample) > len(sample) * 0.3:
        return "heb"
    words = [w.lower() for w in _WORD.findall(sample)]
    scores = {lang: sum(w in stop for w in words) for lang, stop in _STOPWORDS.items()}
    # Palavras exclusivas desempatam português e espanhol.
    scores["por"] += 3 * sum(w in ("não", "uma", "são", "também", "ao", "pelo") for w in words)
    scores["spa"] += 3 * sum(w in ("los", "las", "él", "más", "y", "el") for w in words)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "und"
