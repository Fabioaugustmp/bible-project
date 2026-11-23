"""Servidor local: API de leitura, painel do versículo e busca, mais a interface.

Uso: python app/server.py [--db data/library.db] [--port 8377]
Só aceita conexões da própria máquina e abre a base somente para leitura.
"""
import argparse
import hmac
import json
import mimetypes
import os
import re
import secrets
import socket
import sqlite3
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import userdata

from bridge import BRIDGE, is_stopword
from xrefs import graph as xref_graph
from xrefs import ranked as ranked_xrefs

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
# Pasta de dados: a padrão é data/ do projeto; o contêiner aponta BIBLE_DATA_DIR para o volume.
DATA_DIR = Path(os.environ.get("BIBLE_DATA_DIR", ROOT.parent / "data"))
DB_PATH = DATA_DIR / "library.db"
EMBED_BASE = os.environ.get("BIBLE_EMBED_URL", "http://127.0.0.1:8378").rstrip("/")

_WORD = re.compile(r"[\w]+", re.UNICODE)
MODULE_COLUMNS = "id, source, kind, abbr, title, author, lang, has_strongs, items"


def connect():
    con = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    # Leitura por mapeamento de memória: as páginas vêm direto do cache do sistema, sem cópia
    # para o cache de cada conexão (abrimos uma por pedido). Na busca "graça": ~105 -> ~60 ms.
    # A base só é lida; substitua library.db com o servidor parado (D009), nunca por cima.
    con.execute("pragma mmap_size = 2147418112")
    return con


def rows(con, sql, params=()):
    return [dict(row) for row in con.execute(sql, params)]


def parse_query(text: str):
    """O que o usuário digitou -> lista de ('phrase', palavras) e ('word', palavra)."""
    parts = []
    for phrase, loose in re.findall(r'"([^"]*)"|([^"]+)', text):
        words = _WORD.findall(phrase)
        if words:
            parts.append(("phrase", words))
        parts.extend(("word", word) for word in _WORD.findall(loose))
    return parts


def quote(words) -> str:
    return '"' + " ".join(words if isinstance(words, list) else [words]) + '"'


def fts_query(text: str) -> str:
    """Consulta FTS5 segura: frase entre aspas é exata; fora delas, todas as palavras são exigidas."""
    return " ".join(quote(value) for _, value in parse_query(text))


def fts_by_mode(text: str, modo: str = "todas", near=5) -> str:
    """Consulta FTS5 conforme o modo escolhido (DESENHO-PESQUISA, fase 1).

    todas: todas as palavras (padrão atual); qualquer: alguma palavra (OR);
    frase: as palavras como uma frase exata; near: as palavras a até n palavras uma da outra.
    """
    values = [value for _, value in parse_query(text)]
    if not values:
        return ""
    words = [w for value in values for w in (value if isinstance(value, list) else [value])]
    if modo == "qualquer":
        return " OR ".join(quote(value) for value in values)
    if modo == "frase":
        return quote(words)
    if modo == "near":
        n = max(1, min(50, int(near)))
        return f"NEAR({' '.join(quote(value) for value in values)}, {n})"
    return fts_query(text)


def bilingual_query(con, text: str):
    """Consulta com a ponte por Strong: cada palavra vira (palavra OR tradução inglesa).

    Devolve (consulta FTS5, expansões). Sem nenhuma expansão, devolve a consulta comum.
    Com expansão, as palavras de apoio (de, pela, o...) deixam de ser exigidas,
    porque não aparecem no texto em inglês.
    """
    parts = parse_query(text)
    expansions, groups = [], []
    for kind, value in parts:
        found = BRIDGE.expand(con, value) if kind == "word" else []
        if found:
            expansions.append({"word": value, "terms": found})
        groups.append((kind, value, found))
    if not expansions:
        return fts_query(text), []
    clauses = []
    for kind, value, found in groups:
        if kind == "word" and not found and is_stopword(value):
            continue
        terms = [quote(value)] + [quote(item["term"].split()) for item in found]
        clauses.append("(" + " OR ".join(terms) + ")" if len(terms) > 1 else terms[0])
    return " AND ".join(clauses), expansions


# --- Endpoints ----------------------------------------------------------------

EXCERPT = 420       # caracteres de cada comentário enviados no painel
PAGE = {"verses": 60, "comments": 30, "entries": 30}


def has_table(con, name):
    return con.execute("select 1 from sqlite_master where name = ?", (name,)).fetchone() is not None


_ASTRAL = re.compile("[\U00010000-\U0010FFFF]")


def item_refs(con, kind, item_ids, text_of, limit_end=None):
    """Citações dos itens, com posições convertidas para o JavaScript (UTF-16).

    `text_of` dá o texto de cada item, para a conversão de posição quando há
    caracteres fora do plano básico (raros). `limit_end` corta as citações que
    passam do trecho enviado.
    """
    if not item_ids or not has_table(con, "refs"):
        return {}
    found = {}
    for start in range(0, len(item_ids), 500):
        chunk = item_ids[start:start + 500]
        for item_id, a, b, book, chapter, verse, to_chapter, to_verse in con.execute(
            "select item_id, start, end, book, chapter, verse, to_chapter, to_verse from refs"
            f" where kind = ? and item_id in ({','.join('?' * len(chunk))}) order by item_id, start",
            (kind, *chunk),
        ):
            if limit_end is not None and b > limit_end:
                continue
            text = text_of(item_id)
            if text and _ASTRAL.search(text[:b]):
                a = a + len(_ASTRAL.findall(text[:a]))
                b = b + len(_ASTRAL.findall(text[:b]))
            found.setdefault(item_id, []).append(
                {"start": a, "end": b, "book": book, "chapter": chapter, "verse": verse,
                 "to_chapter": to_chapter, "to_verse": to_verse})
    return found


def api_passage(con, q):
    """Texto de um trecho na versão escolhida (para a prévia de uma citação)."""
    book, chapter, verse = int(q["book"]), int(q["chapter"]), int(q["verse"])
    to_chapter, to_verse = int(q.get("to_chapter", chapter)), int(q.get("to_verse", verse))
    module = int(q["module"])
    verses = rows(
        con,
        "select chapter, verse, text from verses where module_id = ? and book = ?"
        " and (chapter * 1000 + verse) between ? and ? order by chapter, verse limit 8",
        (module, book, chapter * 1000 + verse, max(chapter * 1000 + verse, to_chapter * 1000 + to_verse)),
    )
    total = to_verse - verse + 1 if to_chapter == chapter else None
    return {"verses": verses, "more": total is None or total > len(verses)}


def api_library(con, q):
    return {
        "modules": rows(con, f"select {MODULE_COLUMNS} from modules order by kind, lang <> 'por', abbr"),
        "books": [
            {"book": r["book"], "abbr": r["abbr"], "name": r["name"], "chapters": json.loads(r["chapters"])}
            for r in con.execute("select * from books order by book")
        ],
    }


def modules_with_tokens(con):
    """Módulos que têm palavras em `tokens` (Bíblias com Strong)."""
    if not has_table(con, "tokens"):
        return set()
    return {row[0] for row in con.execute("select id from modules where kind = 'bible' and has_strongs = 1")}


def api_chapter(con, q):
    module, book, chapter = int(q["module"]), int(q["book"]), int(q["chapter"])
    verses = rows(
        con,
        "select verse, text, heading from verses where module_id = ? and book = ? and chapter = ? order by verse",
        (module, book, chapter),
    )
    if module in modules_with_tokens(con):
        # Palavras do versículo: [[expressão, [códigos]], ...]. Palavra original sem
        # tradução (expressão vazia) junta seu código à expressão anterior.
        words = {}
        for verse, surface, strong in con.execute(
            "select verse, surface, strong from tokens where module_id = ? and book = ? and chapter = ?"
            " order by verse, pos", (module, book, chapter),
        ):
            items = words.setdefault(verse, [])
            if surface:
                items.append([surface, [strong] if strong else []])
            elif strong and items:
                items[-1][1].append(strong)
            elif strong:
                items.append(["", [strong]])
        for item in verses:
            item["words"] = words.get(item["verse"])
    return {"verses": verses}


# Ordem de exibição dos léxicos no painel "Palavra" (os demais vêm depois, por sigla).
LEXICON_ORDER = ["Strong", "Dodson", "AHLB", "MLSJ", "LSJ", "KJC", "LXXHebGreek"]
_LINK_STUB = re.compile(r"^meta=_twmgc_\s+type=link\s+id=(\d+)\s*$")
_STRONG_CODE = re.compile(r"^[GH][1-9][0-9]{0,4}$")


def api_word(con, q):
    """Tudo sobre um número Strong: termo original, traduções, léxicos e ocorrências."""
    strong = q["strong"].upper()
    if not _STRONG_CODE.match(strong):
        raise ValueError("código Strong inválido")
    module = int(q["module"]) if q.get("module") else None
    offset = max(0, int(q.get("offset", 0)))
    original_lang = "grc" if strong[0] == "G" else "heb"

    def terms(lang, limit):
        return rows(con, "select term, count, share from strong_terms where strong = ? and lang = ?"
                         " order by count desc limit ?", (strong, lang, limit))

    # Léxicos: verbetes cujo título é o código; os verbetes-ligação (LSJ) apontam para outro tópico.
    lexicons = []
    for entry in rows(con, "select e.id, e.text, e.module_id, m.abbr, m.title, m.lang from entries e"
                           " join modules m on m.id = e.module_id where e.topic = ? collate nocase", (strong,)):
        link = _LINK_STUB.match(entry["text"])
        if link:
            target = con.execute("select id, text from entries where module_id = ? and origin_key = ?",
                                 (entry["module_id"], f"topic:{link.group(1)}")).fetchone()
            if not target:
                continue
            entry["id"], entry["text"] = target[0], target[1]
        entry["excerpt"], entry["length"] = entry["text"][:EXCERPT], len(entry["text"])
        del entry["text"]
        lexicons.append(entry)
    order = {abbr: index for index, abbr in enumerate(LEXICON_ORDER)}
    lexicons.sort(key=lambda entry: (order.get(entry["abbr"], len(order)), entry["abbr"]))

    # Ocorrências: versículos do interlinear BSB (Bíblia inteira) com o código; o texto vem da
    # versão aberta e, quando houver, a expressão usada pela Bíblia portuguesa com Strong.
    reference = con.execute("select id from modules where abbr = 'BSBRevINT'").fetchone()
    portuguese = con.execute(
        "select id from modules where kind = 'bible' and has_strongs = 1 and lang = 'por' order by id limit 1"
    ).fetchone()
    # "+module_id" impede o SQLite de escolher tokens_by_ref (todas as ~440 mil palavras do
    # módulo) em vez de tokens_by_strong (só as ocorrências do código): de ~70 ms para ~2 ms.
    occurrences, total = [], 0
    if reference:
        total = con.execute("select count(*) from (select distinct book, chapter, verse from tokens"
                            " where +module_id = ? and strong = ?)", (reference[0], strong)).fetchone()[0]
        for book, chapter, verse in con.execute(
            "select distinct book, chapter, verse from tokens where +module_id = ? and strong = ?"
            " order by book, chapter, verse limit ? offset ?", (reference[0], strong, PAGE["verses"], offset),
        ):
            text = con.execute("select text from verses where module_id = ? and book = ? and chapter = ?"
                               " and verse = ?", (module, book, chapter, verse)).fetchone() if module else None
            used = [row[0] for row in con.execute(
                "select surface from tokens where module_id = ? and book = ? and chapter = ? and verse = ?"
                " and strong = ? and surface <> '' order by pos",
                (portuguese[0], book, chapter, verse, strong))] if portuguese else []
            occurrences.append({"book": book, "chapter": chapter, "verse": verse,
                                "text": text[0] if text else None, "used": used})

    # Forma original com acentos e transliteração, tirada do interlinear (strong_terms guarda o
    # lema grego sem acentos, para unir as grafias do TR e do BSB).
    original = rows(con, "select lemma as term, translit, count(*) as count from tokens"
                         " where +module_id = ? and strong = ? and lemma is not null"
                         " group by lemma order by count desc limit 1",
                    (reference[0], strong)) if reference else []
    return {
        "strong": strong,
        "original": original or terms(original_lang, 2),
        "original_lang": original_lang,
        "translations": {"por": terms("por", 10), "eng": terms("eng", 10)},
        "lexicons": lexicons,
        "occurrences": occurrences,
        "total": total,
        "offset": offset,
    }


XBOOK_POOL = 400   # referências consideradas para a faixa por livro (T66)


def api_verse(con, q):
    """Tudo sobre um versículo, em formato enxuto: os textos longos vêm de /api/item."""
    book, chapter, verse = int(q["book"]), int(q["chapter"]), int(q["verse"])
    module = int(q["module"]) if q.get("module") else None
    ref = chapter * 1000 + verse
    versions = rows(
        con,
        "select m.id as module_id, m.abbr, m.lang, v.text from verses v"
        " join modules m on m.id = v.module_id"
        " where v.book = ? and v.chapter = ? and v.verse = ? order by m.lang <> 'por', m.abbr",
        (book, chapter, verse),
    )
    comments = rows(
        con,
        "select c.id, m.id as module_id, m.abbr, m.title, m.lang, c.ref_start, c.ref_end,"
        f" substr(c.text, 1, {EXCERPT}) as excerpt, length(c.text) as length from comments c"
        " join modules m on m.id = c.module_id"
        " where c.book = ? and c.ref_start <= ? and c.ref_end >= ? and c.ref_start > ?"
        " order by m.lang <> 'por', (c.ref_end - c.ref_start), m.abbr",
        (book, ref, ref, chapter * 1000),
    )
    excerpts = {comment["id"]: comment["excerpt"] for comment in comments}
    refs_by_item = item_refs(con, "comment", list(excerpts), excerpts.get, limit_end=EXCERPT)
    for comment in comments:
        comment["refs"] = refs_by_item.get(comment["id"], [])
    cited = rows(
        con,
        "select * from ("
        "select l.kind, m.id as module_id, m.abbr, m.title, m.lang, count(*) as count from links l"
        " join entries e on e.id = l.item_id join modules m on m.id = e.module_id"
        " where l.kind = 'entry' and l.book = ? and l.chapter = ? and l.verse = ? group by m.id"
        " union all"
        " select l.kind, m.id, m.abbr, m.title, m.lang, count(*) from links l"
        " join comments c on c.id = l.item_id join modules m on m.id = c.module_id"
        " where l.kind = 'comment' and l.book = ? and l.chapter = ? and l.verse = ? group by m.id"
        ") order by lang <> 'por', count desc",
        (book, chapter, verse) * 2,
    )
    xrefs, xrefs_total = [], 0
    if has_table(con, "xrefs") and q.get("xbook"):
        # Filtro por livro (T66): as referências do ranqueamento, só daquele livro.
        only = int(q["xbook"])
        everything, _ = ranked_xrefs(con, book, chapter, verse, XBOOK_POOL)
        xrefs = [item for item in everything if item["book"] == only][:60]
        xrefs_total = sum(1 for item in everything if item["book"] == only)
        for item in xrefs:
            found = con.execute("select text from verses where module_id = ? and book = ? and chapter = ?"
                                " and verse = ?", (module, item["book"], item["chapter"], item["verse"])).fetchone()
            item["text"] = found[0] if found else None
    elif has_table(con, "xrefs"):
        limit = min(60, max(1, int(q.get("xrefs", 12))))
        xrefs, xrefs_total = ranked_xrefs(con, book, chapter, verse, limit)
        for item in xrefs:
            found = con.execute("select text from verses where module_id = ? and book = ? and chapter = ?"
                                " and verse = ?", (module, item["book"], item["chapter"], item["verse"])).fetchone()
            item["text"] = found[0] if found else None
    return {"versions": versions, "comments": comments, "cited": cited,
            "xrefs": xrefs, "xrefs_total": xrefs_total}


def api_xref_graph(con, q):
    """Grafo das referências cruzadas de um versículo (T65)."""
    if not has_table(con, "xrefs"):
        return {"nodes": [], "edges": [], "total": 0}
    size = min(20, max(5, int(q.get("size", 15))))
    return xref_graph(con, int(q["book"]), int(q["chapter"]), int(q["verse"]), size)


def api_titles(con, q):
    """Títulos de um dicionário ou livro (T64): filtro por texto, letra inicial e paginação."""
    module = int(q["module"])
    kind = con.execute("select kind from modules where id = ?", (module,)).fetchone()
    if not kind or kind[0] not in ("dictionary", "book"):
        raise ValueError("módulo não é dicionário nem livro")
    text = (q.get("q") or "").strip()
    letter = (q.get("letter") or "").strip()[:1]
    offset = max(0, int(q.get("offset", 0)))
    where, params = ["module_id = ?"], [module]
    if text:
        where.append("topic like ?")
        params.append(f"%{text}%")
    if letter:
        where.append("topic like ?")
        params.append(f"{letter}%")
    clause = " and ".join(where)
    items = rows(con, f"select id, topic from entries where {clause} order by topic collate nocase limit 60 offset ?",
                 (*params, offset))
    total = con.execute(f"select count(*) from entries where {clause}", params).fetchone()[0]
    # Letras disponíveis (com o filtro de texto, se houver), para o índice alfabético.
    letters = [r[0] for r in con.execute(
        "select distinct upper(substr(topic, 1, 1)) from entries where module_id = ? "
        + ("and topic like ? " if text else "") + "order by 1",
        (module, f"%{text}%") if text else (module,)) if r[0]]
    return {"items": items, "total": total, "letters": letters, "offset": offset}


def api_xref_books(con, q):
    """Quantas referências do ranqueamento o versículo tem em cada livro (T66)."""
    everything, _ = ranked_xrefs(con, int(q["book"]), int(q["chapter"]), int(q["verse"]), XBOOK_POOL)
    counts = {}
    for item in everything:
        counts[item["book"]] = counts.get(item["book"], 0) + 1
    return {"books": [{"book": b, "count": counts.get(b, 0)} for b in range(1, 67)]}


def api_commentary(con, q):
    """O comentário de um módulo que cobre um versículo, com as citações (T63).

    Entre os comentários que cobrem o versículo, vale o de intervalo mais curto:
    é o mais específico, como o de um versículo isolado diante de um capítulo inteiro.
    """
    module, book, chapter, verse = int(q["module"]), int(q["book"]), int(q["chapter"]), int(q["verse"])
    info = con.execute("select abbr, title, lang from modules where id = ? and kind = 'commentary'",
                       (module,)).fetchone()
    if not info:
        raise ValueError("módulo não é um comentário")
    ref = chapter * 1000 + verse
    row = con.execute(
        "select id, ref_start, ref_end, text from comments where module_id = ? and book = ?"
        " and ref_start <= ? and ref_end >= ? and ref_start > ?"
        " order by (ref_end - ref_start), id limit 1",
        (module, book, ref, ref, chapter * 1000),
    ).fetchone()
    if not row:
        return {"abbr": info[0], "title": info[1], "item": None}
    refs = item_refs(con, "comment", [row[0]], lambda _: row[3]).get(row[0], [])
    return {"abbr": info[0], "title": info[1], "item": {
        "id": row[0], "ref_start": row[1], "ref_end": row[2], "text": row[3], "lang": info[2], "refs": refs}}


def api_cited(con, q):
    """Itens de um módulo que citam o versículo (aberto sob demanda no painel)."""
    book, chapter, verse = int(q["book"]), int(q["chapter"]), int(q["verse"])
    module = int(q["module"])
    if q["kind"] == "entry":
        return {"items": rows(
            con,
            "select 'entry' as kind, e.id, e.topic as label from links l join entries e on e.id = l.item_id"
            " where l.kind = 'entry' and l.book = ? and l.chapter = ? and l.verse = ? and e.module_id = ?"
            " order by e.topic limit 300", (book, chapter, verse, module))}
    return {"items": rows(
        con,
        "select 'comment' as kind, c.id, c.book, c.ref_start, c.ref_end from links l"
        " join comments c on c.id = l.item_id"
        " where l.kind = 'comment' and l.book = ? and l.chapter = ? and l.verse = ? and c.module_id = ?"
        " order by c.book, c.ref_start limit 300", (book, chapter, verse, module))}


def api_item(con, q):
    item_id = int(q["id"])
    if q["kind"] == "entry":
        sql = ("select e.id, e.topic as label, e.text, m.abbr, m.title, m.lang, e.origin_key, m.origin_path"
               " from entries e join modules m on m.id = e.module_id where e.id = ?")
    else:
        sql = ("select c.id, c.book, c.ref_start, c.ref_end, c.text, m.abbr, m.title, m.lang,"
               " c.origin_key, m.origin_path"
               " from comments c join modules m on m.id = c.module_id where c.id = ?")
    found = rows(con, sql, (item_id,))
    if not found:
        return None
    item = found[0]
    kind = "entry" if q["kind"] == "entry" else "comment"
    item["refs"] = item_refs(con, kind, [item_id], lambda _: item["text"]).get(item_id, [])
    return item


EMBED_URL = EMBED_BASE + "/search"
_WORD = re.compile(r"[^\W\d_]{4,}", re.UNICODE)
SEMANTIC_K = 10


def shared_terms(query, text):
    """Palavras da consulta (4 letras ou mais) que também aparecem no texto: a explicação visível."""
    words = {w.lower() for w in _WORD.findall(query)}
    lowered = text.lower()
    return sorted(w for w in words if w in lowered)[:4]


def api_semantic(con, q):
    """Busca por sentido (T33): pede ao serviço de embeddings os itens mais próximos e os
    devolve com o texto. Se o serviço não estiver rodando, avisa em vez de falhar."""
    query = (q.get("q") or "").strip()
    if not query:
        return {"available": True, "query": "", "verses": [], "comments": []}
    body = json.dumps({"q": query, "kinds": ["verse", "comment"], "k": SEMANTIC_K}).encode("utf-8")
    request = urllib.request.Request(EMBED_URL, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            results = json.loads(response.read().decode("utf-8"))["results"]
    except (urllib.error.URLError, OSError, ValueError, KeyError) as error:
        # T119: texto para quem usa; o comando para iniciar o serviço fica no detalhe (log).
        return {"available": False, "reason": DOWN_REASON,
                "detail": f"Inicie o serviço com .venv-bench\\Scripts\\python.exe app\\embed_service.py ({error})"}
    verse_ids = [r["item_id"] for r in results.get("verse", [])]
    comment_ids = [r["item_id"] for r in results.get("comment", [])]
    scores = {("verse", r["item_id"]): r["score"] for r in results.get("verse", [])}
    scores.update({("comment", r["item_id"]): r["score"] for r in results.get("comment", [])})
    verses, comments = [], []
    if verse_ids:
        marks = ",".join("?" * len(verse_ids))
        for vid, abbr, book, chapter, verse, text in con.execute(
            f"select v.id, m.abbr, v.book, v.chapter, v.verse, v.text from verses v"
            f" join modules m on m.id = v.module_id where v.id in ({marks})", verse_ids):
            verses.append({"id": vid, "abbr": abbr, "book": book, "chapter": chapter, "verse": verse,
                           "text": text, "score": scores[("verse", vid)], "shared": shared_terms(query, text)})
    if comment_ids:
        marks = ",".join("?" * len(comment_ids))
        for cid, abbr, lang, book, ref_start, ref_end, text in con.execute(
            f"select c.id, m.abbr, m.lang, c.book, c.ref_start, c.ref_end, c.text from comments c"
            f" join modules m on m.id = c.module_id where c.id in ({marks})", comment_ids):
            comments.append({"id": cid, "abbr": abbr, "lang": lang, "book": book, "ref_start": ref_start,
                             "ref_end": ref_end, "excerpt": text[:280], "score": scores[("comment", cid)],
                             "shared": shared_terms(query, text)})
    order = lambda item: -item["score"]
    return {"available": True, "query": query, "verses": sorted(verses, key=order),
            "comments": sorted(comments, key=order)}


def api_search(con, q):
    """Busca por palavra. Com `kind` e `offset`, devolve só mais uma página daquele tipo."""
    query = fts_by_mode(q.get("q", ""), q.get("modo", "todas"), q.get("near", 5))
    empty = {"query": "", "verses": [], "comments": [], "entries": [], "totals": {}, "expansions": []}
    if not query:
        return empty
    # Ponte português -> inglês só nos comentários e dicionários; a Bíblia é buscada na versão aberta.
    bilingual = q.get("bilingual", "1") != "0"
    study_query, expansions = bilingual_query(con, q.get("q", "")) if bilingual else (query, [])
    module = int(q["module"]) if q.get("module") else None
    only = q.get("kind")
    offset = max(0, int(q.get("offset", 0)))
    snippet = "snippet({t}, {col}, '[[', ']]', '…', 26)"
    # Escopo por livro (T88): vale para versículos e comentários; dicionários não têm livro.
    book = int(q["book"]) if q.get("book") else None
    if book is not None and not 1 <= book <= 66:
        raise ValueError("livro inválido")
    verse_filter = ("and v.module_id = ?" if module else "") + (" and v.book = ?" if book else "")
    verse_params = (query, *([module] if module else []), *([book] if book else []))
    comment_filter = " and c.book = ?" if book else ""
    comment_params = (study_query, *([book] if book else []))
    result = {"query": query, "verses": [], "comments": [], "entries": [], "totals": {},
              "expansions": expansions, "bilingual": bilingual, "bridge": BRIDGE.available}

    if only in (None, "verses"):
        result["verses"] = rows(
            con,
            f"select v.module_id, m.abbr, v.book, v.chapter, v.verse, {snippet.format(t='verses_fts', col=0)} as hit"
            " from verses_fts join verses v on v.id = verses_fts.rowid join modules m on m.id = v.module_id"
            f" where verses_fts match ? {verse_filter} order by bm25(verses_fts), v.book, v.chapter, v.verse"
            " limit ? offset ?",
            (*verse_params, PAGE["verses"], offset),
        )
    if only in (None, "comments"):
        result["comments"] = rows(
            con,
            f"select c.id, m.abbr, m.lang, c.book, c.ref_start, c.ref_end,"
            f" {snippet.format(t='comments_fts', col=0)} as hit"
            " from comments_fts join comments c on c.id = comments_fts.rowid join modules m on m.id = c.module_id"
            f" where comments_fts match ?{comment_filter} order by m.lang <> 'por', bm25(comments_fts) limit ? offset ?",
            (*comment_params, PAGE["comments"], offset),
        )
    if only in (None, "entries"):
        result["entries"] = rows(
            con,
            f"select e.id, m.abbr, m.lang, m.kind, e.topic, {snippet.format(t='entries_fts', col=1)} as hit"
            " from entries_fts join entries e on e.id = entries_fts.rowid join modules m on m.id = e.module_id"
            " where entries_fts match ? order by m.lang <> 'por', bm25(entries_fts, 8.0, 1.0) limit ? offset ?",
            (study_query, PAGE["entries"], offset),
        )
    if only is None:
        # Sem filtro, a contagem fica só no índice FTS: o join leria uma linha da tabela por
        # resultado (milhares de páginas de comentários longos) só para contar.
        verse_count = ("select count(*) from verses_fts join verses v on v.id = verses_fts.rowid"
                       f" where verses_fts match ? {verse_filter}" if verse_filter
                       else "select count(*) from verses_fts where verses_fts match ?")
        comment_count = ("select count(*) from comments_fts join comments c on c.id = comments_fts.rowid"
                         f" where comments_fts match ?{comment_filter}" if comment_filter
                         else "select count(*) from comments_fts where comments_fts match ?")
        result["totals"] = {
            "verses": con.execute(verse_count, verse_params).fetchone()[0],
            "comments": con.execute(comment_count, comment_params).fetchone()[0],
            "entries": con.execute(
                "select count(*) from entries_fts where entries_fts match ?", (study_query,)).fetchone()[0],
        }
    return result


SIMILAR_URL = EMBED_BASE + "/similar"
SIMILAR_K = 10
# T112: sem o serviço, a conexão recusada leva cerca de 2 s no Windows. Depois de uma falha,
# não se tenta de novo por este tempo; as consultas seguintes respondem na hora.
SIMILAR_DOWN_SECONDS = 30
# T119: mensagem da busca por sentido quando o serviço não responde (sem termos técnicos).
DOWN_REASON = "A busca por sentido está indisponível agora. A busca por palavra funciona normalmente; tente de novo em instantes."
_similar_down_until = 0.0


def api_similar(con, q):
    """Passagens parecidas a um versículo (T34), pela versão ARA1993+ indexada. Sem o serviço, avisa."""
    try:
        book, chapter, verse = int(q["book"]), int(q["chapter"]), int(q["verse"])
    except (KeyError, ValueError):
        return {"available": True, "verses": []}
    row = con.execute(
        "select v.id from verses v join modules m on m.id = v.module_id"
        " where m.abbr = 'ARA1993+' and v.book = ? and v.chapter = ? and v.verse = ?",
        (book, chapter, verse)).fetchone()
    if not row:
        return {"available": True, "verses": []}
    down = {"available": False, "verses": [], "reason": DOWN_REASON}
    global _similar_down_until
    if time.monotonic() < _similar_down_until:
        return down
    body = json.dumps({"kind": "verse", "item_id": row[0], "k": SIMILAR_K}).encode("utf-8")
    request = urllib.request.Request(SIMILAR_URL, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            results = json.loads(response.read().decode("utf-8"))["results"]
    except urllib.error.HTTPError:
        return {"available": True, "verses": []}
    except (urllib.error.URLError, OSError, ValueError, KeyError):
        _similar_down_until = time.monotonic() + SIMILAR_DOWN_SECONDS
        return down
    if not results:
        return {"available": True, "verses": []}
    scores = {r["item_id"]: r["score"] for r in results}
    ids = list(scores)
    marks = ",".join("?" * len(ids))
    found = con.execute(
        f"select v.id, v.book, v.chapter, v.verse, v.text from verses v where v.id in ({marks})", ids).fetchall()
    verses = [{"id": vid, "abbr": "ARA1993+", "book": b, "chapter": c, "verse": vs, "text": t, "score": scores[vid]}
              for vid, b, c, vs, t in found]
    return {"available": True, "verses": sorted(verses, key=lambda v: -v["score"])}


STRONG_RE = re.compile(r"^[GH]\d{1,5}$")


def api_strong(con, q):
    """Ocorrências de um número Strong (fase 2 da busca): versículos onde a palavra original aparece.

    Só as versões com marcação de Strong (tokens): ARA1993+, KJV, TR e BSB. A ARA não tem.
    """
    code = (q.get("code") or "").strip().upper()
    if not STRONG_RE.match(code):
        raise ValueError("número Strong inválido: use G ou H seguido de números")
    module = int(q["module"]) if q.get("module") else None
    filt = " and +t.module_id = ?" if module else ""   # "+": usa tokens_by_strong, não tokens_by_ref (ver api_word)
    params = (code, module) if module else (code,)
    total = con.execute(
        f"select count(*) from (select 1 from tokens t where t.strong = ?{filt}"
        " group by t.module_id, t.book, t.chapter, t.verse)", params).fetchone()[0]
    verses = rows(
        con,
        "select v.module_id, m.abbr, v.book, v.chapter, v.verse, v.text,"
        " group_concat(t.surface, ' · ') as words from tokens t"
        " join verses v on v.module_id = t.module_id and v.book = t.book and v.chapter = t.chapter and v.verse = t.verse"
        f" join modules m on m.id = v.module_id where t.strong = ?{filt}"
        " group by t.module_id, t.book, t.chapter, t.verse order by t.book, t.chapter, t.verse limit ?",
        (*params, PAGE["verses"]))
    return {"code": code, "total": total, "verses": verses}


SUGGEST_MAX = 2          # distância máxima de digitação
_VOCAB = None            # chave sem acento -> palavra original, do dicionário em português


def _plain(word):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", word.lower()) if unicodedata.category(c) != "Mn")


def _vocab(con):
    """Palavras do Dicionário em português (Dic Port), uma vez por processo. Só leitura."""
    global _VOCAB
    if _VOCAB is None:
        vocab = {}
        for (topic,) in con.execute(
                "select e.topic from entries e join modules m on m.id = e.module_id"
                " where m.kind = 'dictionary' and m.lang = 'por'"):
            for word in _WORD.findall((topic or "").lower()):
                vocab.setdefault(_plain(word), word)
        _VOCAB = vocab
    return _VOCAB


def _distance(a, b):
    """Distância de Levenshtein com corte: devolve SUGGEST_MAX + 1 se passar do limite."""
    if abs(len(a) - len(b)) > SUGGEST_MAX:
        return SUGGEST_MAX + 1
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        if min(current) > SUGGEST_MAX:
            return SUGGEST_MAX + 1
        previous = current
    return previous[-1]


def api_suggest(con, q):
    """Sugestões de grafia (DESENHO-PESQUISA, fase 4) a partir do Dicionário em português.

    Para cada palavra digitada que não está no dicionário, devolve até 3 palavras próximas.
    Palavras que só diferem por acento aparecem com o acento correto.
    """
    vocab = _vocab(con)
    suggestions = {}
    for typed in _WORD.findall((q.get("q") or "").lower()):
        key = _plain(typed)
        if key in vocab and vocab[key] == typed:
            continue
        if key in vocab:
            suggestions[typed] = [vocab[key]]
            continue
        scored = []
        for candidate_key, original in vocab.items():
            distance = _distance(key, candidate_key)
            if distance <= SUGGEST_MAX:
                scored.append((distance, original))
        suggestions[typed] = [word for _, word in sorted(scored)[:3]]
    return {"suggestions": suggestions}


def api_topic(con, q):
    """Pesquisa por tema, sem IA: versículos que contêm o termo (na versão aberta) e versículos
    de sentido parecido (BGE-M3), sem repetir os que já aparecem na primeira lista. Só texto bíblico."""
    text = (q.get("q") or "").strip()
    if not text:
        return {"query": "", "literal": [], "meaning": [], "semantic": False, "reason": None}
    literal = api_search(con, {"q": text, "kind": "verses", "bilingual": "0",
                               "module": q.get("module")})["verses"]
    sem = api_semantic(con, {"q": text})
    seen = {(r["abbr"], r["book"], r["chapter"], r["verse"]) for r in literal}
    meaning = []
    if sem.get("available"):
        meaning = [v for v in sem["verses"] if (v["abbr"], v["book"], v["chapter"], v["verse"]) not in seen]
    return {"query": text, "literal": literal, "meaning": meaning,
            "semantic": bool(sem.get("available")), "reason": sem.get("reason")}


API = {"library": api_library, "chapter": api_chapter, "verse": api_verse, "cited": api_cited,
       "item": api_item, "titles": api_titles, "xref-books": api_xref_books, "commentary": api_commentary, "search": api_search, "semantic": api_semantic, "topic": api_topic, "similar": api_similar, "strong": api_strong, "suggest": api_suggest, "word": api_word, "passage": api_passage,
       "xref-graph": api_xref_graph}


LAN = False          # --lan: escuta na rede local, com código de acesso para outros aparelhos
PUBLIC = False       # --public-origin (BIBLE_PUBLIC_ORIGIN): publicado na internet; todo pedido exige o código (D034)
PUBLIC_ORIGIN = ""
TOKEN = None
TOKEN_FILE = DATA_DIR / "acesso-celular.txt"
LOCAL_ADDRESSES = ("127.0.0.1", "::1")


def load_token():
    """Código de acesso, guardado em data/ (fora do git). BIBLE_ACCESS_TOKEN, se definido, tem preferência."""
    env_token = os.environ.get("BIBLE_ACCESS_TOKEN", "").strip()
    if env_token:
        return env_token
    if TOKEN_FILE.is_file():
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    token = secrets.token_urlsafe(18)
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(token, encoding="utf-8")
    return token


def token_ok(value):
    return bool(TOKEN) and hmac.compare_digest(value.encode("utf-8"), TOKEN.encode("utf-8"))


def lan_ip():
    """Endereço da rede local (o de saída para a internet, sem enviar nada)."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("192.168.0.1", 80))
        return probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        probe.close()


class Handler(BaseHTTPRequestHandler):
    server_version = "BibleProject/0.1"

    def gate(self, url):
        """True se a conexão pode seguir.

        Com --lan, fora do computador exige o código (cookie ou ?t=). Com --public-origin,
        todo pedido exige o código, inclusive os que chegam pelo túnel (D034).
        """
        if not (LAN or PUBLIC):
            return True
        if not PUBLIC and self.client_address[0] in LOCAL_ADDRESSES:
            return True
        if token_ok(parse_qs(url.query).get("t", [""])[0]):
            secure = "; Secure" if PUBLIC else ""
            self.send_response(302)
            self.send_header("Set-Cookie", f"bp_t={TOKEN}; Path=/; HttpOnly; SameSite=Strict; Max-Age=31536000{secure}")
            self.send_header("Location", "/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return False
        cookies = [part.strip() for part in self.headers.get("Cookie", "").split(";")]
        if TOKEN and any(part.startswith("bp_t=") and token_ok(part[len("bp_t="):]) for part in cookies):
            return True
        self.send(403, "Acesso negado. Abra o endereço completo com o código de acesso mostrado no computador.".encode("utf-8"),
                  "text/plain; charset=utf-8")
        return False

    def log_message(self, fmt, *args):
        if args and str(args[1]) != "200":
            # o código de acesso vai na URL (?t=): não grava o valor no registro
            line = re.sub(r"([?&]t=)[^ &]*", r"\1***", fmt % args)
            super().log_message("%s", line)

    def send(self, status, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, payload):
        self.send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                  "application/json; charset=utf-8")

    def user_get(self, url):
        """Leitura e exportação das notas (T40). Só lê data/user.db e data/library.db."""
        action = url.path[len("/api/user/"):]
        if action == "export":
            con = userdata.connect()
            lib = connect()
            try:
                names = {r["book"]: r["name"] for r in lib.execute("select book, name from books")}
                text = userdata.export_markdown(con, names)
            except sqlite3.Error as error:
                return self.send_json(500, {"error": str(error)})
            finally:
                con.close()
                lib.close()
            return self.send(200, text.encode("utf-8"), "text/markdown; charset=utf-8")
        if action == "study/export":
            con = userdata.connect()
            lib = connect()
            try:
                names = {r["book"]: r["name"] for r in lib.execute("select book, name from books")}
                text = userdata.export_study(con, {k: v[0] for k, v in parse_qs(url.query).items()}, names)
            except ValueError as error:
                return self.send_json(400, {"error": str(error)})
            except sqlite3.Error as error:
                return self.send_json(500, {"error": str(error)})
            finally:
                con.close()
                lib.close()
            return self.send(200, text.encode("utf-8"), "text/markdown; charset=utf-8")
        if action == "export.docx":
            con = userdata.connect()
            lib = connect()
            try:
                names = {r["book"]: r["name"] for r in lib.execute("select book, name from books")}
                data = userdata.export_docx(con, names)
            except sqlite3.Error as error:
                return self.send_json(500, {"error": str(error)})
            finally:
                con.close()
                lib.close()
            return self.send(200, data, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        handler = userdata.READ.get(action)
        if not handler:
            return self.send_json(404, {"error": "endpoint desconhecido"})
        query = {k: v[0] for k, v in parse_qs(url.query).items()}
        con = userdata.connect()
        try:
            return self.send_json(200, handler(con, query))
        except ValueError as error:
            return self.send_json(400, {"error": str(error)})
        except sqlite3.Error as error:
            return self.send_json(500, {"error": str(error)})
        finally:
            con.close()

    def do_POST(self):
        """Escrita nas notas (T40): só com Origin e Host deste app; grava só em data/user.db."""
        url = urlparse(self.path)
        if not self.gate(url):
            return
        if not url.path.startswith("/api/user/"):
            return self.send_json(404, {"error": "endpoint desconhecido"})
        if not userdata.check_origin(self.headers):
            return self.send_json(403, {"error": "origem não permitida"})
        handler = userdata.WRITE.get(url.path[len("/api/user/"):])
        if not handler:
            return self.send_json(404, {"error": "endpoint desconhecido"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > 200000:
                return self.send_json(413, {"error": "pedido grande demais"})
            data = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            return self.send_json(400, {"error": "pedido inválido"})
        if not isinstance(data, dict):
            return self.send_json(400, {"error": "pedido inválido"})
        con = userdata.connect()
        try:
            return self.send_json(200, handler(con, data))
        except ValueError as error:
            return self.send_json(400, {"error": str(error)})
        except sqlite3.Error as error:
            return self.send_json(500, {"error": str(error)})
        finally:
            con.close()

    def do_GET(self):
        url = urlparse(self.path)
        if not self.gate(url):
            return
        if url.path.startswith("/api/user/"):
            return self.user_get(url)
        if url.path.startswith("/api/"):
            handler = API.get(url.path[5:])
            if not handler:
                return self.send_json(404, {"error": "endpoint desconhecido"})
            query = {k: v[0] for k, v in parse_qs(url.query).items()}
            con = connect()
            try:
                return self.send_json(200, handler(con, query))
            except (KeyError, ValueError) as error:
                return self.send_json(400, {"error": f"parâmetro inválido: {error}"})
            except sqlite3.Error as error:
                return self.send_json(500, {"error": str(error)})
            finally:
                con.close()

        relative = url.path.lstrip("/") or "index.html"
        target = (STATIC / relative).resolve()
        if STATIC not in target.parents or not target.is_file():
            return self.send(404, b"nao encontrado", "text/plain; charset=utf-8")
        mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if target.suffix == ".js":
            mime = "text/javascript"
        if mime.startswith("text/"):
            mime += "; charset=utf-8"
        self.send(200, target.read_bytes(), mime)


def main():
    global DB_PATH
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--lan", action="store_true", help="escuta na rede local (celular), com código de acesso")
    parser.add_argument("--port", type=int, default=8377)
    parser.add_argument("--bind", default=os.environ.get("BIBLE_BIND", "127.0.0.1"),
                        help="endereço de escuta (no contêiner: 0.0.0.0; o host publica só em 127.0.0.1)")
    parser.add_argument("--allow-host", action="append", default=[],
                        help="nome de host aceito além de localhost (ex.: meu-servidor:8377); pode repetir")
    parser.add_argument("--public-origin", default=os.environ.get("BIBLE_PUBLIC_ORIGIN", ""),
                        help="endereço público, com https (ex.: https://biblia.famptech.com.br); exige código de acesso")
    args = parser.parse_args()
    DB_PATH = Path(args.db).resolve()
    if not DB_PATH.is_file():
        raise SystemExit(f"base não encontrada: {DB_PATH}\nrode antes: python importer/build.py PASTA")
    global LAN, PUBLIC, PUBLIC_ORIGIN, TOKEN
    hosts = {f"localhost:{args.port}", f"127.0.0.1:{args.port}"}
    hosts.update(args.allow_host + [h for h in os.environ.get("BIBLE_ALLOWED_HOSTS", "").split(",") if h.strip()])
    bind = args.bind
    print(f"http://localhost:{args.port}  (base: {DB_PATH})", flush=True)
    if args.public_origin:
        origin = args.public_origin.rstrip("/")
        if not origin.startswith("https://"):
            raise SystemExit("o endereço público precisa começar com https:// (o túnel da Cloudflare termina o HTTPS)")
        PUBLIC, PUBLIC_ORIGIN, TOKEN = True, origin, load_token()
        if len(TOKEN) < 16:
            raise SystemExit("código de acesso curto demais: defina BIBLE_ACCESS_TOKEN com pelo menos 16 caracteres")
        hosts.add(urlparse(origin).netloc)
        userdata.PUBLIC_ORIGINS = {origin}
        print(f"publicado em {origin}; todo pedido exige o código (BIBLE_ACCESS_TOKEN ou data/acesso-celular.txt)", flush=True)
    if args.lan:
        LAN, TOKEN = True, load_token()
        ip = lan_ip()
        hosts.add(f"{ip}:{args.port}")
        bind = "0.0.0.0"
        print(f"celular: http://{ip}:{args.port}/?t={TOKEN}", flush=True)
        print("o código fica em data/acesso-celular.txt; quem não tiver não entra", flush=True)
    userdata.ALLOWED_HOSTS = hosts
    server = ThreadingHTTPServer((bind, args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
