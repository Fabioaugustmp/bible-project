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

import reading

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
create table if not exists studies(
    id integer primary key,
    title text not null,
    status text not null default 'rascunho',
    created_at text not null, updated_at text not null,
    deleted_at text);
create table if not exists study_blocks(
    id integer primary key,
    study_id integer not null references studies(id),
    pos integer not null,
    kind text not null,
    anchor_id integer references anchors(id),
    body text);
create index if not exists study_blocks_by_study on study_blocks(study_id, pos);
create table if not exists reading_plans(
    id integer primary key,
    title text not null, created_at text not null, deleted_at text);
create table if not exists reading_days(
    id integer primary key,
    plan_id integer not null references reading_plans(id),
    pos integer not null, book integer not null, chapter integer not null, done_on text);
create table if not exists journal(
    id integer primary key,
    body text not null,
    created_at text not null, updated_at text not null,
    deleted_at text);
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


def list_marks(con, q):
    """Marcas do capítulo para o texto: quantas notas e em quantos estudos cada versículo aparece."""
    book, chapter = int(q["book"]), int(q["chapter"])
    notes = {r["verse"]: r["n"] for r in con.execute(
        "select a.verse, count(*) as n from notes n join anchors a on a.id = n.anchor_id"
        " where a.book = ? and a.chapter = ? and n.deleted_at is null group by a.verse", (book, chapter))}
    studies = {r["verse"]: r["n"] for r in con.execute(
        "select a.verse, count(distinct b.study_id) as n from study_blocks b"
        " join anchors a on a.id = b.anchor_id join studies s on s.id = b.study_id"
        " where b.kind = 'passagem' and a.book = ? and a.chapter = ? and s.deleted_at is null"
        " group by a.verse", (book, chapter))}
    return {"notes": notes, "studies": studies}


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


def export_docx(con, names):
    """As mesmas notas em .docx (T42), só com a biblioteca padrão: um zip com document.xml."""
    import io
    import zipfile
    from xml.sax.saxutils import escape

    rows = con.execute(
        "select n.body, n.created_at, a.book, a.chapter, a.verse from notes n"
        " join anchors a on a.id = n.anchor_id where n.deleted_at is null"
        " order by a.book, a.chapter, a.verse, n.created_at").fetchall()
    paras = []

    def para(text, bold=False, size=None):
        props = ""
        if bold or size:
            props = "<w:rPr>" + ("<w:b/>" if bold else "") + (f'<w:sz w:val="{size}"/>' if size else "") + "</w:rPr>"
        paras.append(f'<w:p><w:r>{props}<w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>')

    para("Minhas notas", bold=True, size=36)
    current = None
    for r in rows:
        ref = (r["book"], r["chapter"], r["verse"])
        if ref != current:
            current = ref
            name = names.get(r["book"], "Livro " + str(r["book"]))
            para(f"{name} {r['chapter']}:{r['verse']}", bold=True, size=28)
        for line in r["body"].split("\n"):
            para(line)
        para(r["created_at"].replace("T", " "), size=18)
    doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
           + "".join(paras) + "<w:sectPr/></w:body></w:document>")
    content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                     '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", doc)
    return buffer.getvalue()


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


# ---- diário de estudo (T89, D029): entradas com data, sem passagem ------------------

def list_journal(con, q):
    """Entradas do diário, da mais recente para a mais antiga; `q` filtra pelo texto."""
    text = (q.get("q") or "").strip()
    rows = con.execute(
        "select id, body, created_at, updated_at from journal"
        " where deleted_at is null and (? = '' or body like '%' || ? || '%')"
        " order by created_at desc, id desc limit 500", (text, text)).fetchall()
    return {"entries": [dict(r) for r in rows]}


def create_journal(con, data):
    body = clean_body(data)
    stamp = now()
    cur = con.execute("insert into journal(body, created_at, updated_at) values (?, ?, ?)", (body, stamp, stamp))
    con.commit()
    return {"id": cur.lastrowid}


def update_journal(con, data):
    body = clean_body(data)
    cur = con.execute("update journal set body = ?, updated_at = ? where id = ? and deleted_at is null",
                      (body, now(), int(data["id"])))
    con.commit()
    return {"ok": cur.rowcount == 1}


def delete_journal(con, data):
    cur = con.execute("update journal set deleted_at = ? where id = ? and deleted_at is null",
                      (now(), int(data["id"])))
    con.commit()
    return {"ok": cur.rowcount == 1}


# ---- estudos (D5, primeira fatia: passagem, título e nota) ----------------------

BLOCK_KINDS = ("passagem", "titulo", "nota")
STATUSES = ("rascunho", "pronto")


def _study(con, study_id):
    row = con.execute("select * from studies where id = ? and deleted_at is null", (study_id,)).fetchone()
    if not row:
        raise ValueError("estudo não encontrado")
    return row


def _touch(con, study_id):
    con.execute("update studies set updated_at = ? where id = ?", (now(), study_id))


def _anchor(con, book, chapter, verse):
    con.execute("insert or ignore into anchors(book, chapter, verse) values (?, ?, ?)", (book, chapter, verse))
    return con.execute("select id from anchors where book = ? and chapter = ? and verse = ?",
                       (book, chapter, verse)).fetchone()["id"]


def _clean_title(value):
    title = str(value or "").strip()
    if not title:
        raise ValueError("o título está vazio")
    if len(title) > 200:
        raise ValueError("o título passa de 200 caracteres")
    return title


def _add_block(con, study_id, kind, data):
    if kind not in BLOCK_KINDS:
        raise ValueError("tipo de bloco desconhecido")
    anchor, body = None, None
    if kind == "passagem":
        anchor = _anchor(con, *ref_of(data))
    else:
        body = clean_body(data)
    pos = con.execute("select coalesce(max(pos), 0) + 1 from study_blocks where study_id = ?",
                      (study_id,)).fetchone()[0]
    cur = con.execute("insert into study_blocks(study_id, pos, kind, anchor_id, body) values (?, ?, ?, ?, ?)",
                      (study_id, pos, kind, anchor, body))
    _touch(con, study_id)
    return cur.lastrowid


def list_studies(con, q):
    rows = con.execute(
        "select s.id, s.title, s.status, s.created_at, s.updated_at,"
        " (select count(*) from study_blocks b where b.study_id = s.id) as blocks"
        " from studies s where s.deleted_at is null order by s.updated_at desc").fetchall()
    return {"studies": [dict(r) for r in rows]}


def get_study(con, q):
    if "id" not in q:
        raise ValueError("id do estudo é obrigatório")
    study = _study(con, int(q["id"]))
    blocks = con.execute(
        "select b.id, b.pos, b.kind, b.body, a.book, a.chapter, a.verse from study_blocks b"
        " left join anchors a on a.id = b.anchor_id where b.study_id = ? order by b.pos",
        (study["id"],)).fetchall()
    return {"study": dict(study), "blocks": [dict(b) for b in blocks]}


def create_study(con, data):
    title = _clean_title(data.get("title") or "Novo estudo")
    stamp = now()
    cur = con.execute("insert into studies(title, status, created_at, updated_at) values (?, 'rascunho', ?, ?)",
                      (title, stamp, stamp))
    study_id = cur.lastrowid
    if data.get("book") is not None:
        _add_block(con, study_id, "passagem", data)
    con.commit()
    return {"id": study_id}


def update_study(con, data):
    study = _study(con, int(data["id"]))
    title = _clean_title(data["title"]) if "title" in data else study["title"]
    status = data.get("status", study["status"])
    if status not in STATUSES:
        raise ValueError("estado inválido")
    con.execute("update studies set title = ?, status = ?, updated_at = ? where id = ?",
                (title, status, now(), study["id"]))
    con.commit()
    return {"ok": True}


def delete_study(con, data):
    cur = con.execute("update studies set deleted_at = ? where id = ? and deleted_at is null",
                      (now(), int(data["id"])))
    con.commit()
    return {"ok": cur.rowcount == 1}


def add_block(con, data):
    study = _study(con, int(data["study_id"]))
    kind = data.get("kind", "nota")
    block_id = _add_block(con, study["id"], kind, data)
    con.commit()
    return {"id": block_id}


def _block(con, block_id):
    row = con.execute("select b.*, s.id as study_id from study_blocks b join studies s on s.id = b.study_id"
                      " where b.id = ? and s.deleted_at is null", (block_id,)).fetchone()
    if not row:
        raise ValueError("bloco não encontrado")
    return row


def update_block(con, data):
    block = _block(con, int(data["id"]))
    if block["kind"] == "passagem":
        raise ValueError("passagem não tem texto para editar")
    cur = con.execute("update study_blocks set body = ? where id = ?", (clean_body(data), block["id"]))
    _touch(con, block["study_id"])
    con.commit()
    return {"ok": cur.rowcount == 1}


def delete_block(con, data):
    block = _block(con, int(data["id"]))
    con.execute("delete from study_blocks where id = ?", (block["id"],))
    _touch(con, block["study_id"])
    con.commit()
    return {"ok": True}


def move_block(con, data):
    block = _block(con, int(data["id"]))
    step = -1 if int(data.get("direction", 0)) < 0 else 1
    other = con.execute(
        "select id, pos from study_blocks where study_id = ? and pos " + ("<" if step < 0 else ">") + " ?"
        " order by pos " + ("desc" if step < 0 else "asc") + " limit 1",
        (block["study_id"], block["pos"])).fetchone()
    if other:
        con.execute("update study_blocks set pos = case id when ? then ? when ? then ? end where id in (?, ?)",
                    (block["id"], other["pos"], other["id"], block["pos"], block["id"], other["id"]))
        _touch(con, block["study_id"])
        con.commit()
    return {"ok": bool(other)}


def export_study(con, q, names):
    """Um estudo em Markdown. A passagem aparece só como referência: o texto fica na biblioteca."""
    study = _study(con, int(q["id"]))
    blocks = con.execute(
        "select b.kind, b.body, a.book, a.chapter, a.verse from study_blocks b"
        " left join anchors a on a.id = b.anchor_id where b.study_id = ? order by b.pos",
        (study["id"],)).fetchall()
    lines = [f"# {study['title']}", "", f"*Estado: {study['status']} · atualizado em {study['updated_at'].replace('T', ' ')}*", ""]
    for b in blocks:
        if b["kind"] == "titulo":
            lines += [f"## {b['body']}", ""]
        elif b["kind"] == "passagem":
            name = names.get(b["book"], f"Livro {b['book']}")
            lines += [f"**Passagem:** {name} {b['chapter']}:{b['verse']}", ""]
        else:
            lines += [b["body"], ""]
    return "\n".join(lines).rstrip() + "\n"


def list_reading(con, q):
    """Leitura de hoje: planos, progresso e notas de hoje (T82)."""
    return reading.list_plans(con, q)


def list_backlinks(con, q):
    """Notas de outros versículos que citam este (T81)."""
    import backlinks
    book, chapter, verse = ref_of(q)
    return {"notes": backlinks.find(con, book, chapter, verse)}


READ = {"notes": list_notes, "all": list_all, "studies": list_studies, "study": get_study, "marks": list_marks,
        "backlinks": list_backlinks, "reading": list_reading, "journal": list_journal}
WRITE = {
    "journal/create": create_journal, "journal/update": update_journal, "journal/delete": delete_journal,
    "note/create": create_note, "note/update": update_note, "note/delete": delete_note,
    "study/create": create_study, "study/update": update_study, "study/delete": delete_study,
    "block/add": add_block, "block/update": update_block, "block/delete": delete_block,
    "block/move": move_block,
    "plan/create": reading.create_plan, "plan/mark": reading.mark_day, "plan/delete": reading.delete_plan,
}
