"""Leitura dos módulos do e-Sword (.bblx, .cmtx, .dctx), todos SQLite."""
import re

from db import MARK_CLOSE, MARK_OPEN, guess_lang, open_readonly, split_strongs
from rtf import rtf_to_text

# {\cf11\super H1254 [H8804]} -> código Strong e, entre colchetes, análise do verbo.
_STRONG_GROUP = re.compile(r"\{\\cf\d+\\super\s+([^{}]*)\}")
_STRONG_CODE = re.compile(r"[HG]\d+")


def _mark_strongs(match):
    codes = _STRONG_CODE.findall(match.group(1))
    return f"{MARK_OPEN}{'|'.join(codes)}{MARK_CLOSE}" if codes else ""


def _details(src):
    columns = [row[1] for row in src.execute("pragma table_info(Details)")]
    row = src.execute("select * from Details").fetchone() or ()
    details = dict(zip(columns, row))
    return {
        "title": rtf_to_text(str(details.get("Description") or "")),
        "abbr": str(details.get("Abbreviation") or "").strip(),
    }


def _sample(texts, limit=40):
    return " ".join(t for t in texts[:limit] if t)


# {\b\qc O começo} -> título de seção embutido no início do texto do versículo.
# ({\i\qc ...} é o título de um salmo, que faz parte do texto e fica nele.)
_HEADING_GROUP = re.compile(r"\{\\b\\qc\s*([^{}]*)\}")


def _split_heading(scripture: str):
    """Separa os títulos de seção do texto do versículo: (título ou None, texto)."""
    titles = [rtf_to_text(title) for title in _HEADING_GROUP.findall(scripture)]
    titles = [title for title in titles if title]
    if not titles:
        return None, scripture
    return " · ".join(titles), _HEADING_GROUP.sub(" ", scripture)


def read_bible(path, add):
    src = open_readonly(path)
    meta = _details(src) | {"kind": "bible", "has_strongs": 0}
    rows, skipped, unreadable = [], 0, 0
    for book, chapter, verse, scripture in src.execute(
        "select Book, Chapter, Verse, Scripture from Bible order by rowid"
    ):
        if not all(isinstance(number, int) for number in (book, chapter, verse)):
            continue  # linha de cabeçalho da tabela: ('Livro', 'Cap', 'Verso', ...)
        if not 1 <= book <= 66:
            skipped += 1
            continue
        if isinstance(scripture, bytes):
            unreadable += 1  # módulo protegido do e-Sword: o texto vem cifrado
            continue
        heading, body = _split_heading(scripture or "")
        marked = rtf_to_text(_STRONG_GROUP.sub(_mark_strongs, body)).replace("¶", "")
        text, tagged = split_strongs(marked)
        if tagged:
            meta["has_strongs"] = 1
        rows.append((book, chapter, verse, text, tagged, heading, f"{book}.{chapter}.{verse}"))
    src.close()
    if not rows:
        add.log("ignorado", f"texto cifrado em {unreadable} versículos (módulo protegido do e-Sword); não é possível ler"
                if unreadable else "módulo sem versículos")
        return 0
    if unreadable:
        add.log("aviso", f"{unreadable} versículos com texto cifrado foram ignorados")
    rows.sort(key=lambda row: row[:3])
    meta["lang"] = guess_lang(_sample([r[3] for r in rows[23145:23300] or rows]))
    module_id = add.module(meta)
    add.verses(module_id, rows)
    if skipped:
        add.log("aviso", f"{skipped} versículos de livros fora do cânon de 66 foram ignorados")
    return len(rows)


def read_commentary(path, add):
    src = open_readonly(path)
    meta = _details(src) | {"kind": "commentary"}
    tables = {r[0] for r in src.execute("select name from sqlite_master where type='table'")}
    rows = []
    if "Books" in tables:
        for rowid, book, comments in src.execute("select rowid, Book, Comments from Books"):
            rows.append((book, 0, 0, rtf_to_text(comments), f"Books:{rowid}"))
    if "Chapters" in tables:
        for rowid, book, chapter, comments in src.execute(
            "select rowid, Book, Chapter, Comments from Chapters"
        ):
            rows.append((book, chapter * 1000, chapter * 1000, rtf_to_text(comments), f"Chapters:{rowid}"))
    if "Verses" in tables:
        for rowid, book, c1, c2, v1, v2, comments in src.execute(
            "select rowid, Book, ChapterBegin, ChapterEnd, VerseBegin, VerseEnd, Comments from Verses"
        ):
            start, end = c1 * 1000 + v1, (c2 or c1) * 1000 + (v2 or v1)
            rows.append((book, start, max(start, end), rtf_to_text(comments), f"Verses:{rowid}"))
    src.close()
    rows = [r for r in rows if r[3] and 1 <= r[0] <= 66]
    meta["lang"] = guess_lang(_sample([r[3][:400] for r in rows[len(rows) // 2:]]))
    module_id = add.module(meta)
    add.comments(module_id, rows)
    return len(rows)


def read_dictionary(path, add):
    src = open_readonly(path)
    meta = _details(src) | {"kind": "dictionary"}
    rows = [
        (str(topic).strip(), rtf_to_text(definition), f"Dictionary:{rowid}")
        for rowid, topic, definition in src.execute("select rowid, Topic, Definition from Dictionary")
        if topic and definition
    ]
    src.close()
    meta["lang"] = guess_lang(_sample([r[1][:400] for r in rows[len(rows) // 2:]]))
    module_id = add.module(meta)
    add.entries(module_id, rows)
    return len(rows)


READERS = {".bblx": read_bible, ".cmtx": read_commentary, ".dctx": read_dictionary}
