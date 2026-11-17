"""Servidor local: API de leitura, painel do versículo e busca, mais a interface.

Uso: python app/server.py [--db data/library.db] [--port 8377]
Só aceita conexões da própria máquina e abre a base somente para leitura.
"""
import argparse
import json
import mimetypes
import re
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from bridge import BRIDGE, is_stopword
from xrefs import ranked as ranked_xrefs

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DB_PATH = ROOT.parent / "data" / "library.db"

_WORD = re.compile(r"[\w]+", re.UNICODE)
MODULE_COLUMNS = "id, source, kind, abbr, title, author, lang, has_strongs, items"


def connect():
    con = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
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
LEXICON_ORDER = ["Dodson", "AHLB", "MLSJ", "LSJ", "KJC", "LXXHebGreek"]
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
    occurrences, total = [], 0
    if reference:
        total = con.execute("select count(*) from (select distinct book, chapter, verse from tokens"
                            " where module_id = ? and strong = ?)", (reference[0], strong)).fetchone()[0]
        for book, chapter, verse in con.execute(
            "select distinct book, chapter, verse from tokens where module_id = ? and strong = ?"
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
                         " where module_id = ? and strong = ? and lemma is not null"
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
    if has_table(con, "xrefs"):
        limit = min(60, max(1, int(q.get("xrefs", 12))))
        xrefs, xrefs_total = ranked_xrefs(con, book, chapter, verse, limit)
        for item in xrefs:
            found = con.execute("select text from verses where module_id = ? and book = ? and chapter = ?"
                                " and verse = ?", (module, item["book"], item["chapter"], item["verse"])).fetchone()
            item["text"] = found[0] if found else None
    return {"versions": versions, "comments": comments, "cited": cited,
            "xrefs": xrefs, "xrefs_total": xrefs_total}


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
    return found[0] if found else None


def api_search(con, q):
    """Busca por palavra. Com `kind` e `offset`, devolve só mais uma página daquele tipo."""
    query = fts_query(q.get("q", ""))
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
    verse_filter = "and v.module_id = ?" if module else ""
    verse_params = (query, module) if module else (query,)
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
            " where comments_fts match ? order by m.lang <> 'por', bm25(comments_fts) limit ? offset ?",
            (study_query, PAGE["comments"], offset),
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
        result["totals"] = {
            "verses": con.execute(
                f"select count(*) from verses_fts join verses v on v.id = verses_fts.rowid"
                f" where verses_fts match ? {verse_filter}", verse_params).fetchone()[0],
            "comments": con.execute(
                "select count(*) from comments_fts where comments_fts match ?", (study_query,)).fetchone()[0],
            "entries": con.execute(
                "select count(*) from entries_fts where entries_fts match ?", (study_query,)).fetchone()[0],
        }
    return result


API = {"library": api_library, "chapter": api_chapter, "verse": api_verse, "cited": api_cited,
       "item": api_item, "search": api_search, "word": api_word}


class Handler(BaseHTTPRequestHandler):
    server_version = "BibleProject/0.1"

    def log_message(self, fmt, *args):
        if args and str(args[1]) != "200":
            super().log_message(fmt, *args)

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

    def do_GET(self):
        url = urlparse(self.path)
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
    parser.add_argument("--port", type=int, default=8377)
    args = parser.parse_args()
    DB_PATH = Path(args.db).resolve()
    if not DB_PATH.is_file():
        raise SystemExit(f"base não encontrada: {DB_PATH}\nrode antes: python importer/build.py PASTA")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"http://localhost:{args.port}  (base: {DB_PATH})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
