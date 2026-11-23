"""Leitura diária (T82): planos de leitura por capítulo, com marcação de lido.

Desenho (docs/DESENHO-LEITURA.md, D028):
- um plano é uma sequência de capítulos, de um capítulo inicial até um final (na ordem da Bíblia);
- cada capítulo é um dia do plano, sem data fixa: "hoje" é o próximo capítulo ainda não lido;
- marcar como lido grava a data do dia (done_on); desmarcar limpa a data;
- "notas de hoje" são as notas criadas na data de hoje.
Só lê/escreve data/user.db; a lista de capítulos vem de canon.py (via importer/).
"""
import sys
import time
from pathlib import Path

IMPORTER = Path(__file__).resolve().parent.parent / "importer"
if str(IMPORTER) not in sys.path:
    sys.path.insert(0, str(IMPORTER))

from canon import BOOKS, VERSES  # noqa: E402

MAX_CHAPTERS = 400   # um plano não passa disso (a Bíblia tem 1.189)


def today() -> str:
    return time.strftime("%Y-%m-%d")


def chapters_between(book, chapter, to_book, to_chapter):
    """Lista (livro, capítulo) de (book, chapter) até (to_book, to_chapter), na ordem da Bíblia."""
    if not (1 <= book <= 66 and 1 <= to_book <= 66):
        raise ValueError("livro inválido")
    if (to_book, to_chapter) < (book, chapter):
        raise ValueError("o capítulo final vem antes do inicial")
    out = []
    for b in range(book, to_book + 1):
        first = chapter if b == book else 1
        last = to_chapter if b == to_book else len(VERSES[b - 1])
        if not (1 <= first <= len(VERSES[b - 1]) and 1 <= last <= len(VERSES[b - 1])):
            raise ValueError("capítulo inexistente")
        out += [(b, c) for c in range(first, last + 1)]
        if len(out) > MAX_CHAPTERS:
            raise ValueError(f"plano grande demais: máximo de {MAX_CHAPTERS} capítulos")
    return out


def _int(data, key, default=None):
    value = data.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"valor inválido: {key}")


def create_plan(con, data):
    book, chapter = _int(data, "book"), _int(data, "chapter", 1)
    to_book, to_chapter = _int(data, "to_book", book), _int(data, "to_chapter", chapter)
    chapters = chapters_between(book, chapter, to_book, to_chapter)
    # Sem título, usa o nome completo dos livros (como na interface).
    if (book, chapter) == (to_book, to_chapter):
        default = f"{BOOKS[book - 1][1]} {chapter}"
    else:
        default = f"{BOOKS[book - 1][1]} {chapter} – {BOOKS[to_book - 1][1]} {to_chapter}"
    title = (data.get("title") or "").strip()[:80] or default
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    cur = con.execute("insert into reading_plans(title, created_at) values (?, ?)", (title, stamp))
    plan_id = cur.lastrowid
    con.executemany("insert into reading_days(plan_id, pos, book, chapter) values (?, ?, ?, ?)",
                    [(plan_id, i + 1, b, c) for i, (b, c) in enumerate(chapters)])
    con.commit()
    return {"id": plan_id, "days": len(chapters)}


def _plan_days(con, plan_id):
    return con.execute("select id, pos, book, chapter, done_on from reading_days where plan_id = ? order by pos",
                       (plan_id,)).fetchall()


def list_plans(con, q=None):
    """Planos ativos com progresso, o próximo capítulo e as notas de hoje."""
    stamp = today()
    plans = []
    for plan in con.execute("select id, title, created_at from reading_plans where deleted_at is null"
                            " order by id").fetchall():
        days = _plan_days(con, plan["id"])
        done = [d for d in days if d["done_on"]]
        nxt = next((d for d in days if not d["done_on"]), None)
        plans.append({
            "id": plan["id"], "title": plan["title"], "total": len(days), "done": len(done),
            "next": dict(nxt) if nxt else None,
            "read_today": any(d["done_on"] == stamp for d in days),
        })
    notes_today = con.execute("select count(*) from notes where deleted_at is null and substr(created_at, 1, 10) = ?",
                              (stamp,)).fetchone()[0]
    return {"date": stamp, "plans": plans, "notes_today": notes_today}


def mark_day(con, data):
    """Marca um capítulo. Exige o plano e o capítulo juntos: um id de dia de outro plano é recusado."""
    day_id = _int(data, "id")
    plan_id = _int(data, "plan_id")
    done = bool(data.get("done", True))
    cur = con.execute("update reading_days set done_on = ? where id = ? and plan_id = ?"
                      " and plan_id in (select id from reading_plans where deleted_at is null)",
                      (today() if done else None, day_id, plan_id))
    if cur.rowcount == 0:
        raise ValueError("capítulo do plano não encontrado")
    con.commit()
    return {"ok": True}


def delete_plan(con, data):
    plan_id = _int(data, "id")
    cur = con.execute("update reading_plans set deleted_at = ? where id = ? and deleted_at is null",
                      (time.strftime("%Y-%m-%dT%H:%M:%S"), plan_id))
    if cur.rowcount == 0:
        raise ValueError("plano não encontrado")
    con.commit()
    return {"ok": True}
