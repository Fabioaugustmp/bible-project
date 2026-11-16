"""Confere a base importada contra os critérios de aceite da Fase 1.

Uso: python importer/verify.py data/library.db
Sai com código 1 se alguma verificação falhar.
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from canon import NT_VERSES, OT_VERSES  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
con = sqlite3.connect(f"file:{Path(sys.argv[1]).as_posix()}?mode=ro", uri=True)
failures = 0


def check(ok, label):
    global failures
    failures += not ok
    print(f"  [{'ok' if ok else 'FALHA'}] {label}")


print("Módulos:")
for mid, source, kind, abbr, lang, strongs, items in con.execute(
    "select id, source, kind, abbr, lang, has_strongs, items from modules order by id"
):
    print(f"  {mid:>3} {source:<8} {kind:<11} {lang:<4} strong={strongs} {items:>7}  {abbr}")

print("Contagem de versículos por Bíblia:")
for mid, abbr, count, first in con.execute(
    "select m.id, m.abbr, count(*), min(v.book) from verses v join modules m on m.id = v.module_id group by m.id"
):
    expected = (OT_VERSES + NT_VERSES, NT_VERSES)
    check(count in expected or first == 1 and count == OT_VERSES, f"{abbr}: {count} versículos")

print("Itens gravados = itens declarados no módulo:")
for mid, abbr, kind, items in con.execute("select id, abbr, kind, items from modules"):
    table = {"bible": "verses", "commentary": "comments"}.get(kind, "entries")
    real = con.execute(f"select count(*) from {table} where module_id = ?", (mid,)).fetchone()[0]
    check(real == items, f"{abbr}: {real}")

print("Sobras de marcação:")
for table in ("verses", "comments", "entries"):
    count = con.execute(
        f"select count(*) from {table} where text like '%\\par%' or text like '%{{\\%'"
        " or text like '%\\cf%' or text like '%\\u2__?%' or text glob '*<W[GHT]*'"
        " or text like '%HYPERLINK%'"
    ).fetchone()[0]
    check(count == 0, f"{table}: {count} linhas suspeitas")

print("Procedência:")
missing = con.execute(
    "select count(*) from modules where origin_sha256 is null or length(origin_sha256) <> 64"
).fetchone()[0]
check(missing == 0, "todo módulo tem SHA-256 do arquivo de origem")
for table in ("verses", "comments", "entries"):
    count = con.execute(f"select count(*) from {table} where origin_key is null or origin_key = ''").fetchone()[0]
    check(count == 0, f"{table}: toda linha tem chave de origem")

print("Amostras (conferir a olho):")
for book, chapter, verse in ((1, 1, 1), (43, 3, 16)):
    for abbr, text, tagged in con.execute(
        "select m.abbr, v.text, v.tagged from verses v join modules m on m.id = v.module_id"
        " where book = ? and chapter = ? and verse = ? order by m.id", (book, chapter, verse)
    ):
        print(f"  {book}.{chapter}.{verse} {abbr}: {text}")
        if tagged:
            print(f"      marcado: {tagged[:150]}")
for abbr, start, end, text in con.execute(
    "select m.abbr, c.ref_start, c.ref_end, c.text from comments c join modules m on m.id = c.module_id"
    " where book = 43 and ref_start <= 3016 and ref_end >= 3016 and ref_start > 3000"
):
    print(f"  comentário {abbr} [{start}-{end}]: {text[:260]!r}")
for abbr, topic, text in con.execute(
    "select m.abbr, e.topic, e.text from entries e join modules m on m.id = e.module_id"
    " where e.topic in ('Abinadab', 'ADIVINHO')"
):
    print(f"  verbete {abbr} / {topic}: {text[:220]!r}")
print("  citações de João 3:16:", con.execute(
    "select kind, count(*) from links where book = 43 and chapter = 3 and verse = 16 group by kind").fetchall())
print("  busca 'graca' (sem acento):", con.execute(
    "select count(*) from verses_fts where verses_fts match 'graca'").fetchone()[0], "versículos")
print("Log de importação:")
for level, path, message in con.execute("select level, origin_path, message from import_log"):
    print(f"  {level}: {Path(path).name}: {message}")

print("\nRESULTADO:", "tudo certo" if not failures else f"{failures} verificações falharam")
sys.exit(1 if failures else 0)
