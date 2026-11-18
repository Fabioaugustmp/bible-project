"""Dados do usuário (T40): notas presas a passagens, gravadas só em data/user.db.

A biblioteca (data/library.db) é somente leitura para o servidor; esta base é a
única que a interface pode gravar. Notas ficam ligadas a uma passagem pela
referência (livro, capítulo, versículo) na versificação KJV (D005), que não
muda ao reimportar a biblioteca. Apagar vai para a lixeira (deleted_at).

Só biblioteca padrão (D003).
"""
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USER_DB = ROOT / "data" / "user.db"
ALLOWED_HOSTS = {"localhost:8377", "127.0.0.1:8377"}   # ajustado pelo servidor ao iniciar
MAX_BODY = 20000

SCHEMA = """
create table if not exists meta(key text primary key, value text);
create table if not exists anchors(
    id integer primary key,
    book integer not null, chapter integer not null, verse integer not null,
    unique(book, chapter, verse));
create table if not exists notes(
    id integer primary key,
    anchor_id integer not null references anchors(id),
    body text not null,
    created_at text not null, updated_at text not null,
    deleted_at text);
create index if not exists notes_by_anchor on notes(anchor_id);
create table if not exists imports(
    id integer primary key,
    origin_path text, origin_sha256 text unique,
    imported_at text, notes_count integer);
"""


def connect():
    USER_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(USER_DB)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    columns = [row[1] for row in con.execute("pragma table_info(notes)")]
    if "import_id" not in columns:   # migração: notas importadas guardam a origem (T41)
        con.execute("alter table notes add column import_id integer references imports(id)")
    con.execute("insert or ignore into meta(key, value) values ('schema_version', '2')")
    con.commit()
    return con


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def ref_of(data):
    try:
        return int(data["book"]), int(data["chapter"]), int(data["verse"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("passagem inválida")


def clean_body(data):
    body = str(data.get("body", "")).replace("\r\n", "\n").strip()
    if not body:
        raise ValueError("a nota está vazia")
    if len(body) > MAX_BODY:
        raise ValueError(f"a nota passa de {MAX_BODY} caracteres")
    return body


def check_origin(headers):
    """Escrita só de páginas servidas por este app (D021 e proposta, seção 10)."""
    host = headers.get("Host", "")
    origin = headers.get("Origin", "")
    return host in ALLOWED_HOSTS and origin == f"http://{host}"


# ---- leitura ----------------------------------------------------------------

def list_notes(con, q):
    book, chapter, verse = ref_of(q)
    rows = con.execute(
        "select n.id, n.body, n.created_at, n.updated_at from notes n"
        " join anchors a on a.id = n.anchor_id"
        " where a.book = ? and a.chapter = ? and a.verse = ? and n.deleted_at is null"
        " order by n.created_at", (book, chapter, verse)).fetchall()
    return {"notes": [dict(r) for r in rows]}


def list_all(con, q):
    text = (q.get("q") or "").strip()
    rows = con.execute(
        "select n.id, n.body, n.created_at, n.updated_at, a.book, a.chapter, a.verse from notes n"
        " join anchors a on a.id = n.anchor_id"
        " where n.deleted_at is null and (? = '' or n.body like '%' || ? || '%')"
        " order by a.book, a.chapter, a.verse, n.created_at limit 500", (text, text)).fetchall()
    return {"notes": [dict(r) for r in rows]}


def export_markdown(con, names):
    """Todas as notas, em Markdown, agrupadas por passagem na ordem da Bíblia."""
    rows = con.execute(
        "select n.body, n.created_at, a.book, a.chapter, a.verse from notes n"
        " join anchors a on a.id = n.anchor_id where n.deleted_at is null"
        " order by a.book, a.chapter, a.verse, n.created_at").fetchall()
    lines = ["# Minhas notas", ""]
    current = None
    for r in rows:
        ref = (r["book"], r["chapter"], r["verse"])
        if ref != current:
            current = ref
            name = names.get(r["book"], f"Livro {r['book']}")
            lines += ["", f"## {name} {r['chapter']}:{r['verse']}", ""]
        lines += [r["body"], "", f"*{r['created_at'].replace('T', ' ')}*", ""]
    return "\n".join(lines).rstrip() + "\n"


# ---- escrita ----------------------------------------------------------------

def create_note(con, data):
    book, chapter, verse = ref_of(data)
    body = clean_body(data)
    con.execute("insert or ignore into anchors(book, chapter, verse) values (?, ?, ?)",
                (book, chapter, verse))
    anchor = con.execute("select id from anchors where book = ? and chapter = ? and verse = ?",
                         (book, chapter, verse)).fetchone()["id"]
    stamp = now()
    cur = con.execute("insert into notes(anchor_id, body, created_at, updated_at) values (?, ?, ?, ?)",
                      (anchor, body, stamp, stamp))
    con.commit()
    return {"id": cur.lastrowid}


def update_note(con, data):
    body = clean_body(data)
    cur = con.execute("update notes set body = ?, updated_at = ? where id = ? and deleted_at is null",
                      (body, now(), int(data["id"])))
    con.commit()
    return {"ok": cur.rowcount == 1}


def delete_note(con, data):
    cur = con.execute("update notes set deleted_at = ? where id = ? and deleted_at is null",
                      (now(), int(data["id"])))
    con.commit()
    return {"ok": cur.rowcount == 1}


READ = {"notes": list_notes, "all": list_all}
WRITE = {"note/create": create_note, "note/update": update_note, "note/delete": delete_note}
