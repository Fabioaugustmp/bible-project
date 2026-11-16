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


def fts_query(text: str) -> str:
    """Transforma o que o usuário digitou em consulta FTS5 segura.

    Entre aspas vira frase exata; fora delas, todas as palavras são exigidas.
    """
    parts = []
    for phrase, loose in re.findall(r'"([^"]*)"|([^"]+)', text):
        if phrase.strip():
            words = _WORD.findall(phrase)
            if words:
                parts.append('"' + " ".join(words) + '"')
        for word in _WORD.findall(loose):
            parts.append(f'"{word}"')
    return " ".join(parts)


# --- Endpoints ----------------------------------------------------------------

def api_library(con, q):
    return {
        "modules": rows(con, f"select {MODULE_COLUMNS} from modules order by kind, lang <> 'por', abbr"),
        "books": [
            {"book": r["book"], "abbr": r["abbr"], "name": r["name"], "chapters": json.loads(r["chapters"])}
            for r in con.execute("select * from books order by book")
        ],
    }


def api_chapter(con, q):
    return {"verses": rows(
        con,
        "select verse, text from verses where module_id = ? and book = ? and chapter = ? order by verse",
        (int(q["module"]), int(q["book"]), int(q["chapter"])),
    )}


def api_verse(con, q):
    book, chapter, verse = int(q["book"]), int(q["chapter"]), int(q["verse"])
    ref = chapter * 1000 + verse
    versions = rows(
        con,
        "select m.id as module_id, m.abbr, m.lang, v.text, v.tagged from verses v"
        " join modules m on m.id = v.module_id"
        " where v.book = ? and v.chapter = ? and v.verse = ? order by m.lang <> 'por', m.abbr",
        (book, chapter, verse),
    )
    comments = rows(
        con,
        "select c.id, m.abbr, m.title, m.lang, c.ref_start, c.ref_end, c.text from comments c"
        " join modules m on m.id = c.module_id"
        " where c.book = ? and c.ref_start <= ? and c.ref_end >= ? and c.ref_start > ?"
        " order by m.lang <> 'por', (c.ref_end - c.ref_start), m.abbr",
        (book, ref, ref, chapter * 1000),
    )
    cited = rows(
        con,
        "select 'entry' as kind, e.id, m.abbr, m.lang, e.topic as label from links l"
        " join entries e on e.id = l.item_id join modules m on m.id = e.module_id"
        " where l.kind = 'entry' and l.book = ? and l.chapter = ? and l.verse = ?"
        " union all"
        " select 'comment', c.id, m.abbr, m.lang, c.book || '.' || c.ref_start from links l"
        " join comments c on c.id = l.item_id join modules m on m.id = c.module_id"
        " where l.kind = 'comment' and l.book = ? and l.chapter = ? and l.verse = ?"
        " limit 200",
        (book, chapter, verse) * 2,
    )
    return {"versions": versions, "comments": comments, "cited": cited}


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
    query = fts_query(q.get("q", ""))
    if not query:
        return {"query": "", "verses": [], "comments": [], "entries": [], "totals": {}}
    module = int(q["module"]) if q.get("module") else None
    snippet = "snippet({t}, {col}, '[[', ']]', '…', 26)"

    verse_filter = "and v.module_id = ?" if module else ""
    verse_params = (query, module) if module else (query,)
    verses = rows(
        con,
        f"select v.module_id, m.abbr, v.book, v.chapter, v.verse, {snippet.format(t='verses_fts', col=0)} as hit"
        " from verses_fts join verses v on v.id = verses_fts.rowid join modules m on m.id = v.module_id"
        f" where verses_fts match ? {verse_filter} order by bm25(verses_fts), v.book, v.chapter, v.verse limit 80",
        verse_params,
    )
    comments = rows(
        con,
        f"select c.id, m.abbr, m.lang, c.book, c.ref_start, c.ref_end, {snippet.format(t='comments_fts', col=0)} as hit"
        " from comments_fts join comments c on c.id = comments_fts.rowid join modules m on m.id = c.module_id"
        " where comments_fts match ? order by bm25(comments_fts) limit 40",
        (query,),
    )
    entries = rows(
        con,
        f"select e.id, m.abbr, m.lang, e.topic, {snippet.format(t='entries_fts', col=1)} as hit"
        " from entries_fts join entries e on e.id = entries_fts.rowid join modules m on m.id = e.module_id"
        " where entries_fts match ? order by bm25(entries_fts, 8.0, 1.0) limit 40",
        (query,),
    )
    totals = {
        "verses": con.execute(
            f"select count(*) from verses_fts join verses v on v.id = verses_fts.rowid"
            f" where verses_fts match ? {verse_filter}", verse_params).fetchone()[0],
        "comments": con.execute(
            "select count(*) from comments_fts where comments_fts match ?", (query,)).fetchone()[0],
        "entries": con.execute(
            "select count(*) from entries_fts where entries_fts match ?", (query,)).fetchone()[0],
    }
    return {"query": query, "verses": verses, "comments": comments, "entries": entries, "totals": totals}


API = {"library": api_library, "chapter": api_chapter, "verse": api_verse,
       "item": api_item, "search": api_search}


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
