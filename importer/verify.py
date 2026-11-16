"""Confere a base importada contra os critérios de aceite.

Uso: python importer/verify.py data/library.db
Sai com código 1 se alguma verificação falhar. Linhas [aviso] não reprovam.
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from canon import NT_VERSES, OT_VERSES  # noqa: E402

LANGS = {"por", "eng", "grc", "heb", "spa", "lat", "und"}
VERSE_TOLERANCE = 0.01      # NVI, NTLH, Viva e a católica têm versificação própria
RESIDUE_TOLERANCE = 0.0001  # sobras de marcação que já vêm erradas na origem

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
con = sqlite3.connect(f"file:{Path(sys.argv[1]).as_posix()}?mode=ro", uri=True)
failures = 0


def check(ok, label, warn=False):
    global failures
    if not ok and not warn:
        failures += 1
    print(f"  [{'ok' if ok else 'aviso' if warn else 'FALHA'}] {label}")


def one(sql, params=()):
    return con.execute(sql, params).fetchone()[0]


print("Módulos por tipo:")
for kind, count, items in con.execute("select kind, count(*), sum(items) from modules group by kind order by kind"):
    print(f"  {kind:<11} {count:>3} módulos  {items:>8} itens")

print("Importação:")
errors = con.execute("select origin_path, message from import_log where level = 'erro'").fetchall()
check(not errors, f"{len(errors)} módulos com erro")
for path, message in errors:
    print(f"        {Path(path).name}: {message}")
ignored = one("select count(*) from import_log where level = 'ignorado'")
print(f"  [info] {ignored} arquivos ignorados (criptografados, tipos não importados, duplicatas)")

print("Versículos por Bíblia:")
for abbr, count, headings in con.execute(
    "select m.abbr, count(*), sum(v.heading is not null) from verses v join modules m on m.id = v.module_id"
    " group by m.id order by m.id"
):
    nearest = min((OT_VERSES + NT_VERSES, NT_VERSES, OT_VERSES), key=lambda n: abs(n - count))
    note = "" if count == nearest else f" (padrão {nearest}; versificação própria)"
    note += f", {headings} títulos" if headings else ""
    check(abs(count - nearest) <= nearest * VERSE_TOLERANCE, f"{abbr}: {count}{note}")

print("Sem repetição e com metadados limpos:")
duplicates = con.execute(
    "select source, abbr from modules where kind = 'bible' group by source, abbr having count(*) > 1").fetchall()
check(not duplicates, f"Bíblias repetidas: {duplicates or 'nenhuma'}")
langs = {row[0] for row in con.execute("select distinct lang from modules")}
check(langs <= LANGS, f"idiomas: {sorted(langs)}")
undefined = [row[0] for row in con.execute("select abbr from modules where lang = 'und'")]
check(not undefined, f"módulos sem idioma identificado: {undefined or 'nenhum'}", warn=True)
longest = one("select max(length(title)) from modules where kind = 'bible'")
check(longest <= 90, f"título de Bíblia mais longo: {longest} caracteres")
strongs = [row[0] for row in con.execute("select abbr from modules where has_strongs = 1 order by abbr")]
few = [row[0] for row in con.execute(
    "select m.abbr from modules m where m.has_strongs = 1 and"
    " (select count(*) from verses v where v.module_id = m.id and v.tagged is not null) < m.items / 2")]
check(not few, f"Bíblias com Strong: {strongs}; marcadas com Strong em menos da metade dos versículos: {few or 'nenhuma'}")

print("Itens gravados = itens declarados no módulo:")
mismatched = []
for mid, abbr, kind, items in con.execute("select id, abbr, kind, items from modules"):
    table = {"bible": "verses", "commentary": "comments", "xrefs": "xrefs", "headings": "headings"}.get(kind, "entries")
    real = one(f"select count(*) from {table} where module_id = ?", (mid,))
    if real != items:
        mismatched.append((abbr, items, real))
check(not mismatched, f"divergências: {mismatched or 'nenhuma'}")

print("Sobras de marcação:")
for table in ("verses", "comments", "entries"):
    total = one(f"select count(*) from {table}")
    count = one(
        f"select count(*) from {table} where text like '%\\par%' or text like '%{{\\%'"
        " or text like '%\\cf%' or text like '%\\u2__?%' or text glob '*<W[GHT]*'"
        " or text like '%HYPERLINK%'"
    )
    check(count <= total * RESIDUE_TOLERANCE, f"{table}: {count} linhas suspeitas em {total}")
control = one("select count(*) from verses where text glob '*[' || char(1) || '-' || char(8) || ']*'")
check(control == 0, f"versículos com caractere de controle: {control}")
leaked = one("select count(*) from verses where heading is not null and text like heading || ' ' || heading || '%'")
check(leaked == 0, f"versículos com o título repetido dentro do texto: {leaked}")

print("Palavras e termos por Strong:")
without_words = [row[0] for row in con.execute(
    "select m.abbr from modules m where m.has_strongs = 1"
    " and not exists (select 1 from tokens t where t.module_id = m.id)")]
check(not without_words, f"Bíblias com Strong sem palavras em tokens: {without_words or 'nenhuma'}")
for abbr, words, coded, untranslated in con.execute(
    "select m.abbr, count(*), sum(t.strong is not null), sum(t.surface = '') from tokens t"
    " join modules m on m.id = t.module_id group by m.id order by m.id"
):
    print(f"  [info] {abbr}: {words} palavras, {coded} com Strong, {untranslated} sem tradução na linha principal")
beyond = one(
    "select count(*) from tokens where (strong like 'G%' and cast(substr(strong, 2) as integer) > 5624)"
    " or (strong like 'H%' and cast(substr(strong, 2) as integer) > 8674)")
check(beyond == 0, f"códigos de análise verbal gravados como Strong: {beyond}")
mixed = one(
    "select count(*) from verses v join modules m on m.id = v.module_id"
    " where m.lang = 'eng' and m.kind = 'bible' and v.text glob '*[α-ωא-ת]*'")
check(mixed == 0, f"versículos de Bíblia em inglês com grego ou hebraico no texto: {mixed}")
# Traduções que têm de aparecer em primeiro lugar quando há Bíblia com Strong no idioma.
for strong, lang, expected in (("G5485", "por", "graça"), ("G5485", "eng", "grace"), ("G4102", "por", "fé"),
                               ("G4102", "eng", "faith"), ("H7965", "por", "paz"), ("H7965", "eng", "peace")):
    top = con.execute(
        "select term, count from strong_terms where strong = ? and lang = ? order by count desc limit 1",
        (strong, lang)).fetchone()
    if top:
        check(top[0] == expected, f"{strong} em {lang}: '{top[0]}' ({top[1]} ocorrências), esperado '{expected}'")

print("Referências cruzadas:")
for abbr, count in con.execute(
    "select m.abbr, count(*) from xrefs x join modules m on m.id = x.module_id group by m.id"
):
    print(f"  [info] {abbr}: {count} referências")
if one("select count(*) from modules where kind = 'xrefs'"):
    targets = {tuple(row) for row in con.execute(
        "select x.to_book, x.to_chapter, x.to_verse from xrefs x join modules m on m.id = x.module_id"
        " where m.kind = 'xrefs' and x.book = 1 and x.chapter = 1 and x.verse = 1")}
    check({(18, 38, 4), (19, 33, 6), (19, 89, 11)} <= targets, "Gn 1:1 aponta para Jó 38:4, Sl 33:6 e Sl 89:11")
out_of_range = one(
    "select count(*) from xrefs x where not exists (select 1 from books b where b.book = x.to_book)"
    " or x.to_chapter < 1 or x.to_verse < 1")
check(out_of_range == 0, f"referências para fora do cânon: {out_of_range}")

print("Procedência:")
check(one("select count(*) from modules where origin_sha256 is null or length(origin_sha256) <> 64") == 0,
      "todo módulo tem SHA-256 do arquivo de origem")
for table in ("verses", "comments", "entries"):
    check(one(f"select count(*) from {table} where origin_key is null or origin_key = ''") == 0,
          f"{table}: toda linha tem chave de origem")

print("Amostras (conferir a olho):")
for book, chapter, verse in ((1, 1, 1), (43, 3, 16)):
    for abbr, text, heading in con.execute(
        "select m.abbr, v.text, v.heading from verses v join modules m on m.id = v.module_id"
        " where book = ? and chapter = ? and verse = ? order by m.lang <> 'por', m.abbr", (book, chapter, verse)
    ):
        title = f" [{heading}]" if heading else ""
        print(f"  {book}.{chapter}.{verse} {abbr}{title}: {text[:110]}")
print("  comentários sobre João 3:16:", one(
    "select count(*) from comments where book = 43 and ref_start <= 3016 and ref_end >= 3016 and ref_start > 3000"))
print("  citações de João 3:16:", con.execute(
    "select kind, count(*) from links where book = 43 and chapter = 3 and verse = 16 group by kind").fetchall())
print("  busca 'graca' (sem acento):", one(
    "select count(*) from verses_fts where verses_fts match 'graca'"), "versículos")

print("\nRESULTADO:", "tudo certo" if not failures else f"{failures} verificações falharam")
sys.exit(1 if failures else 0)
