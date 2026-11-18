"""Backlinks de notas (T81): notas de outros versículos que citam o versículo aberto.

Usa o localizador de citações do importador (importer/refs.py, find_plain), que reconhece
"João 3:16", "Jo 3.16-18", "Is 48.6-7" e similares. Só lê data/user.db e data/library.db
(a lista de livros é a fixa de canon.py); nada é gravado.
"""
import sys
from pathlib import Path

IMPORTER = Path(__file__).resolve().parent.parent / "importer"
if str(IMPORTER) not in sys.path:
    sys.path.insert(0, str(IMPORTER))

import refs  # noqa: E402  (depende do caminho acima)

EXCERPT = 160


def excerpt(text: str) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= EXCERPT else flat[:EXCERPT].rstrip() + "…"


def cites(body: str, book: int, chapter: int, verse: int) -> bool:
    """A nota cita o versículo (book, chapter, verse) numa citação de um ou mais versículos?"""
    _, found = refs.find_plain(body)
    for _, _, b, c, v, to_c, to_v in found:
        if b != book:
            continue
        if (c, v) <= (chapter, verse) <= (to_c, to_v):
            return True
    return False


def find(con, book: int, chapter: int, verse: int):
    """Notas (não apagadas) de outros versículos que citam este. Mais recentes primeiro."""
    rows = con.execute(
        "select n.id, n.body, n.created_at, n.updated_at, a.book, a.chapter, a.verse from notes n"
        " join anchors a on a.id = n.anchor_id where n.deleted_at is null"
        " and not (a.book = ? and a.chapter = ? and a.verse = ?)"
        " order by n.updated_at desc", (book, chapter, verse)).fetchall()
    out = []
    for r in rows:
        if cites(r["body"], book, chapter, verse):
            item = dict(r)
            item["excerpt"] = excerpt(r["body"])
            out.append(item)
    return out
