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
import studymap

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
create table if not exists topics(
    id integer primary key,
    name text not null,
    created_at text not null, updated_at text not null,
    deleted_at text);
create table if not exists topic_notes(
    id integer primary key,
    topic_id integer not null references topics(id),
    anchor_id integer references anchors(id),
    body text not null,
    created_at text not null, updated_at text not null,
    deleted_at text);
create index if not exists topic_notes_by_topic on topic_notes(topic_id);
create table if not exists memo_cards(
    id integer primary key,
    book integer not null, chapter integer not null, verse integer not null,
    ease real not null default 2.5,
    interval integer not null default 0,
    reps integer not null default 0,
    due text not null,
    created_at text not null, updated_at text not null,
    deleted_at text);
create index if not exists memo_cards_due on memo_cards(due);
create table if not exists ref_sets(
    id integer primary key,
    name text not null,
    created_at text not null, updated_at text not null,
    deleted_at text);
create table if not exists ref_set_items(
    id integer primary key,
    set_id integer not null references ref_sets(id),
    pos integer not null,
    book integer not null, chapter integer not null, verse integer not null,
    span integer not null default 0,
    created_at text not null);
create index if not exists ref_set_items_by_set on ref_set_items(set_id, pos);
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


# ---- notas por tópico (T87, D030): um assunto reúne notas de várias passagens ----------

MAX_TOPIC = 80


def _topic(con, topic_id):
    row = con.execute("select id, name from topics where id = ? and deleted_at is null", (topic_id,)).fetchone()
    if not row:
        raise ValueError("tópico não encontrado")
    return row


def _topic_name(con, data, current_id=None):
    name = " ".join(str(data.get("name", "")).split())
    if not name:
        raise ValueError("o nome do tópico está vazio")
    if len(name) > MAX_TOPIC:
        raise ValueError(f"o nome passa de {MAX_TOPIC} caracteres")
    clash = con.execute("select id from topics where deleted_at is null and lower(name) = lower(?)"
                        " and id is not ?", (name, current_id)).fetchone()
    if clash:
        raise ValueError("já existe um tópico com este nome")
    return name


def _optional_anchor(con, data):
    """Passagem opcional da nota de tópico: sem livro, a nota vale para o tópico todo."""
    if data.get("book") in (None, ""):
        return None
    book, chapter, verse = ref_of(data)
    if not (1 <= book <= 66 and 1 <= chapter <= len(reading.VERSES[book - 1])
            and 1 <= verse <= reading.VERSES[book - 1][chapter - 1]):
        raise ValueError("passagem inexistente")
    return _anchor(con, book, chapter, verse)


def list_topics(con, q):
    rows = con.execute(
        "select t.id, t.name, t.updated_at, count(n.id) as notes from topics t"
        " left join topic_notes n on n.topic_id = t.id and n.deleted_at is null"
        " where t.deleted_at is null group by t.id order by lower(t.name)").fetchall()
    return {"topics": [dict(r) for r in rows]}


def get_topic(con, q):
    try:
        topic_id = int(q["id"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("tópico inválido")
    topic = _topic(con, topic_id)
    rows = con.execute(
        "select n.id, n.body, n.created_at, n.updated_at, a.book, a.chapter, a.verse from topic_notes n"
        " left join anchors a on a.id = n.anchor_id"
        " where n.topic_id = ? and n.deleted_at is null order by a.book is null, a.book, a.chapter, a.verse, n.created_at",
        (topic_id,)).fetchall()
    return {"id": topic["id"], "name": topic["name"], "notes": [dict(r) for r in rows]}


def create_topic(con, data):
    name = _topic_name(con, data)
    stamp = now()
    cur = con.execute("insert into topics(name, created_at, updated_at) values (?, ?, ?)", (name, stamp, stamp))
    con.commit()
    return {"id": cur.lastrowid}


def delete_topic(con, data):
    topic_id = int(data["id"])
    _topic(con, topic_id)
    stamp = now()
    con.execute("update topic_notes set deleted_at = ? where topic_id = ? and deleted_at is null", (stamp, topic_id))
    con.execute("update topics set deleted_at = ? where id = ?", (stamp, topic_id))
    con.commit()
    return {"ok": True}


def add_topic_note(con, data):
    topic_id = int(data["topic_id"])
    _topic(con, topic_id)
    body = clean_body(data)
    anchor = _optional_anchor(con, data)
    stamp = now()
    cur = con.execute("insert into topic_notes(topic_id, anchor_id, body, created_at, updated_at)"
                      " values (?, ?, ?, ?, ?)", (topic_id, anchor, body, stamp, stamp))
    _touch_topic(con, topic_id)
    con.commit()
    return {"id": cur.lastrowid}


def update_topic_note(con, data):
    body = clean_body(data)
    cur = con.execute("update topic_notes set body = ?, updated_at = ? where id = ? and deleted_at is null",
                      (body, now(), int(data["id"])))
    con.commit()
    return {"ok": cur.rowcount == 1}


def delete_topic_note(con, data):
    cur = con.execute("update topic_notes set deleted_at = ? where id = ? and deleted_at is null",
                      (now(), int(data["id"])))
    con.commit()
    return {"ok": cur.rowcount == 1}


def _touch_topic(con, topic_id):
    con.execute("update topics set updated_at = ? where id = ?", (now(), topic_id))


# ---- memorização (T80, D031): cartões de um versículo, com o algoritmo SM-2 ------------

MEMO_GRADES = {"esqueci": 0, "dificil": 3, "bom": 4, "facil": 5}


def sm2(ease, interval, reps, quality):
    """SM-2 (SuperMemo 2). Devolve (facilidade, intervalo em dias, repetições) depois da resposta.

    quality 0-5; abaixo de 3 o cartão volta ao começo (intervalo 1 dia).
    """
    if quality < 3:
        reps, interval = 0, 1
    else:
        if reps == 0:
            interval = 1
        elif reps == 1:
            interval = 6
        else:
            interval = max(1, round(interval * ease))
        reps += 1
    ease = ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    return max(1.3, ease), interval, reps


def _memo_day(days):
    import datetime
    return (datetime.date.fromisoformat(reading.today()) + datetime.timedelta(days=days)).isoformat()


def list_memo(con, q):
    today = reading.today()
    rows = con.execute(
        "select id, book, chapter, verse, due, reps, interval from memo_cards where deleted_at is null"
        " order by due, book, chapter, verse").fetchall()
    cards = [dict(r) for r in rows]
    return {"date": today, "due": [c for c in cards if c["due"] <= today], "cards": cards}


def add_memo(con, data):
    book, chapter, verse = ref_of(data)
    if not (1 <= book <= 66 and 1 <= chapter <= len(reading.VERSES[book - 1])
            and 1 <= verse <= reading.VERSES[book - 1][chapter - 1]):
        raise ValueError("passagem inexistente")
    if con.execute("select 1 from memo_cards where deleted_at is null and book = ? and chapter = ? and verse = ?",
                   (book, chapter, verse)).fetchone():
        raise ValueError("este versículo já está na memorização")
    stamp = now()
    cur = con.execute("insert into memo_cards(book, chapter, verse, due, created_at, updated_at)"
                      " values (?, ?, ?, ?, ?, ?)", (book, chapter, verse, reading.today(), stamp, stamp))
    con.commit()
    return {"id": cur.lastrowid}


def review_memo(con, data):
    """Registra a resposta: quality é uma das chaves de MEMO_GRADES (ou um número de 0 a 5)."""
    grade = data.get("grade")
    quality = MEMO_GRADES.get(grade) if isinstance(grade, str) else None
    if quality is None:
        raise ValueError("resposta inválida")
    card = con.execute("select id, ease, interval, reps from memo_cards where id = ? and deleted_at is null",
                       (int(data["id"]),)).fetchone()
    if not card:
        raise ValueError("cartão não encontrado")
    ease, interval, reps = sm2(card["ease"], card["interval"], card["reps"], quality)
    con.execute("update memo_cards set ease = ?, interval = ?, reps = ?, due = ?, updated_at = ? where id = ?",
                (ease, interval, reps, _memo_day(interval), now(), card["id"]))
    con.commit()
    return {"ok": True, "due": _memo_day(interval), "interval": interval}


def delete_memo(con, data):
    cur = con.execute("update memo_cards set deleted_at = ? where id = ? and deleted_at is null",
                      (now(), int(data["id"])))
    con.commit()
    return {"ok": cur.rowcount == 1}


# ---- conjuntos de referências (T98, D032): ordem escolhida pelo usuário ----------------

MAX_SET = 80
MAX_SET_ITEMS = 200


def _set(con, set_id):
    row = con.execute("select id, name from ref_sets where id = ? and deleted_at is null", (set_id,)).fetchone()
    if not row:
        raise ValueError("conjunto não encontrado")
    return row


def list_ref_sets(con, q):
    rows = con.execute(
        "select s.id, s.name, s.updated_at, count(i.id) as items from ref_sets s"
        " left join ref_set_items i on i.set_id = s.id where s.deleted_at is null"
        " group by s.id order by lower(s.name)").fetchall()
    return {"sets": [dict(r) for r in rows]}


def get_ref_set(con, q):
    try:
        set_id = int(q["id"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("conjunto inválido")
    found = _set(con, set_id)
    items = con.execute("select id, pos, book, chapter, verse, span from ref_set_items where set_id = ?"
                        " order by pos", (set_id,)).fetchall()
    return {"id": found["id"], "name": found["name"], "items": [dict(r) for r in items]}


def create_ref_set(con, data):
    name = " ".join(str(data.get("name", "")).split())
    if not name:
        raise ValueError("o nome do conjunto está vazio")
    if len(name) > MAX_SET:
        raise ValueError(f"o nome passa de {MAX_SET} caracteres")
    stamp = now()
    cur = con.execute("insert into ref_sets(name, created_at, updated_at) values (?, ?, ?)", (name, stamp, stamp))
    con.commit()
    return {"id": cur.lastrowid}


def delete_ref_set(con, data):
    set_id = int(data["id"])
    _set(con, set_id)
    con.execute("update ref_sets set deleted_at = ? where id = ?", (now(), set_id))
    con.commit()
    return {"ok": True}


def add_ref_item(con, data):
    set_id = int(data["set_id"])
    _set(con, set_id)
    book, chapter, verse = ref_of(data)
    if not (1 <= book <= 66 and 1 <= chapter <= len(reading.VERSES[book - 1])
            and 1 <= verse <= reading.VERSES[book - 1][chapter - 1]):
        raise ValueError("passagem inexistente")
    try:
        span = max(0, int(data.get("span") or 0))
    except (TypeError, ValueError):
        raise ValueError("intervalo inválido")
    count = con.execute("select count(*) from ref_set_items where set_id = ?", (set_id,)).fetchone()[0]
    if count >= MAX_SET_ITEMS:
        raise ValueError(f"o conjunto passa de {MAX_SET_ITEMS} passagens")
    last = con.execute("select coalesce(max(pos), 0) from ref_set_items where set_id = ?", (set_id,)).fetchone()[0]
    cur = con.execute("insert into ref_set_items(set_id, pos, book, chapter, verse, span, created_at)"
                      " values (?, ?, ?, ?, ?, ?, ?)", (set_id, last + 1, book, chapter, verse, span, now()))
    con.execute("update ref_sets set updated_at = ? where id = ?", (now(), set_id))
    con.commit()
    return {"id": cur.lastrowid}


def move_ref_item(con, data):
    """Sobe (delta -1) ou desce (delta 1) a passagem trocando de lugar com a vizinha."""
    item = con.execute("select id, set_id, pos from ref_set_items where id = ?", (int(data["id"]),)).fetchone()
    if not item:
        raise ValueError("passagem não encontrada")
    delta = -1 if int(data.get("delta", 0)) < 0 else 1
    neighbor = con.execute("select id, pos from ref_set_items where set_id = ? and pos = ?",
                           (item["set_id"], item["pos"] + delta)).fetchone()
    if neighbor:
        con.execute("update ref_set_items set pos = ? where id = ?", (item["pos"], neighbor["id"]))
        con.execute("update ref_set_items set pos = ? where id = ?", (neighbor["pos"], item["id"]))
        con.commit()
    return {"ok": bool(neighbor)}


def remove_ref_item(con, data):
    cur = con.execute("delete from ref_set_items where id = ?", (int(data["id"]),))
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
        "backlinks": list_backlinks, "reading": list_reading, "journal": list_journal,
        "topics": list_topics, "topic": get_topic, "memo": list_memo,
        "sets": list_ref_sets, "set": get_ref_set,
        "map": studymap.map_data, "timeline": studymap.timeline}
WRITE = {
    "set/create": create_ref_set, "set/delete": delete_ref_set, "set/add": add_ref_item,
    "set/move": move_ref_item, "set/remove": remove_ref_item,
    "memo/add": add_memo, "memo/review": review_memo, "memo/delete": delete_memo,
    "topic/create": create_topic, "topic/delete": delete_topic, "topic/note/add": add_topic_note,
    "topic/note/update": update_topic_note, "topic/note/delete": delete_topic_note,
    "journal/create": create_journal, "journal/update": update_journal, "journal/delete": delete_journal,
    "note/create": create_note, "note/update": update_note, "note/delete": delete_note,
    "study/create": create_study, "study/update": update_study, "study/delete": delete_study,
    "block/add": add_block, "block/update": update_block, "block/delete": delete_block,
    "block/move": move_block,
    "plan/create": reading.create_plan, "plan/mark": reading.mark_day, "plan/delete": reading.delete_plan,
}
