"""Converte módulos do e-Sword e do theWord em uma base SQLite única.

Uso:
    python importer/build.py --out data/library.db PASTA [PASTA ...]

Os arquivos de origem são abertos somente para leitura. A base de saída é
recriada do zero a cada execução, salvo com --incremental: então a base
existente é reaproveitada e só os arquivos novos ou alterados são relidos
(regras em docs/DECISOES.md, D017).
"""
import argparse
import hashlib
import json
import sqlite3
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import db  # noqa: E402
import esword  # noqa: E402
import theword  # noqa: E402
from refs import verses_of  # noqa: E402
from tokens import normalize_term, strip_accents  # noqa: E402

READERS = {**{ext: ("esword", fn) for ext, fn in esword.READERS.items()},
           **{ext: ("theword", fn) for ext, fn in theword.READERS.items()}}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


class Adder:
    """O que um leitor de módulo pode gravar, já com a procedência do arquivo."""

    def __init__(self, con, path: Path, source: str, sha: str | None = None):
        self.con, self.path, self.source, self.sha = con, path, source, sha
        self.module_id = None
        self.items = 0

    def log(self, level, message):
        self.con.execute(
            "insert into import_log(at, level, origin_path, message) values (?, ?, ?, ?)",
            (now(), level, str(self.path), message),
        )

    def module(self, meta) -> int:
        stat = self.path.stat()
        cursor = self.con.execute(
            "insert into modules(source, kind, abbr, title, author, lang, has_strongs,"
            " origin_path, origin_sha256, origin_size, origin_mtime, importer_version, imported_at)"
            " values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (self.source, meta["kind"], meta.get("abbr") or self.path.stem,
             meta.get("title") or self.path.stem, meta.get("author"), db.normalize_lang(meta.get("lang")),
             meta.get("has_strongs", 0), str(self.path), self.sha or sha256(self.path), stat.st_size,
             datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds"),
             db.IMPORTER_VERSION, now()),
        )
        self.module_id = cursor.lastrowid
        return self.module_id

    def verses(self, module_id, rows):
        self.con.executemany(
            "insert into verses(module_id, book, chapter, verse, text, tagged, heading, origin_key)"
            " values (?, ?, ?, ?, ?, ?, ?, ?)",
            [(module_id, *row) for row in rows],
        )
        self.items += len(rows)

    def tokens(self, module_id, rows):
        self.con.executemany(
            "insert into tokens(module_id, book, chapter, verse, pos, surface, strong, lemma, morph,"
            " original, translit, gloss) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(module_id, *row) for row in rows],
        )

    def xrefs(self, module_id, rows, count_as_items=False):
        self.con.executemany(
            "insert into xrefs(module_id, book, chapter, verse, to_book, to_chapter, to_verse, to_span)"
            " values (?, ?, ?, ?, ?, ?, ?, ?)",
            [(module_id, *row) for row in rows],
        )
        if count_as_items:
            self.items += len(rows)

    def headings(self, module_id, rows):
        self.con.executemany(
            "insert into headings(module_id, book, chapter, verse, level, text) values (?, ?, ?, ?, ?, ?)",
            [(module_id, *row) for row in rows],
        )
        self.items += len(rows)

    def _with_links(self, sql, kind, module_id, rows, links, refs):
        """Grava itens; `links[i]` são os versículos citados (do módulo) e `refs[i]` as
        citações com posição no texto. Sem `links`, os versículos citados vêm das citações."""
        for index, row in enumerate(rows):
            item_id = self.con.execute(sql, (module_id, *row)).lastrowid
            item_refs = refs[index] if refs else ()
            if item_refs:
                self.con.executemany(
                    "insert into refs values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [(kind, item_id, *ref) for ref in item_refs],
                )
            cited = links[index] if links else sorted({verse for ref in item_refs for verse in verses_of(ref)})
            if cited:
                self.con.executemany(
                    "insert into links values (?, ?, ?, ?, ?)",
                    [(kind, item_id, *ref) for ref in cited],
                )
        self.items += len(rows)

    def comments(self, module_id, rows, links=None, refs=None):
        self._with_links(
            "insert into comments(module_id, book, ref_start, ref_end, text, origin_key)"
            " values (?, ?, ?, ?, ?, ?)", "comment", module_id, rows, links, refs)

    def entries(self, module_id, rows, links=None, refs=None):
        self._with_links(
            "insert into entries(module_id, topic, text, origin_key) values (?, ?, ?, ?)",
            "entry", module_id, rows, links, refs)


def find_modules(folders):
    """Arquivos de módulo nas pastas, sem repetir o mesmo arquivo (nome + tamanho)."""
    seen, found = set(), []
    for folder in folders:
        for path in sorted(Path(folder).rglob("*")):
            if path.is_file() and path.suffix.lower() in READERS:
                key = (path.name.lower(), path.stat().st_size)
                if key not in seen:
                    seen.add(key)
                    found.append(path)
    return found


def merge_duplicate_bibles(con):
    """Mesma Bíblia em mais de um arquivo (com e sem títulos de seção): fica uma só.

    Mantém a cópia sem títulos (nos módulos examinados é a completa e a de
    texto mais limpo), copia para ela os títulos da outra e remove a outra.
    Devolve os caminhos das cópias removidas.
    """
    donors = []
    groups = con.execute(
        "select source, abbr from modules where kind = 'bible' group by source, abbr having count(*) > 1"
    ).fetchall()
    for source, abbr in groups:
        ranked = con.execute(
            "select m.id, m.origin_path, (select count(*) from verses v where v.module_id = m.id"
            " and v.heading is not null) as headings from modules m"
            " where m.kind = 'bible' and m.source = ? and m.abbr = ? order by headings, m.items desc, m.id",
            (source, abbr),
        ).fetchall()
        keeper_id, keeper_path, _ = ranked[0]
        for donor_id, donor_path, headings in ranked[1:]:
            copied = 0
            if headings:
                copied = con.execute(
                    "update verses set heading = (select d.heading from verses d where d.module_id = ?"
                    " and d.book = verses.book and d.chapter = verses.chapter and d.verse = verses.verse)"
                    " where module_id = ? and heading is null and exists (select 1 from verses d"
                    " where d.module_id = ? and d.book = verses.book and d.chapter = verses.chapter"
                    " and d.verse = verses.verse and d.heading is not null)",
                    (donor_id, keeper_id, donor_id),
                ).rowcount
            con.execute("delete from verses where module_id = ?", (donor_id,))
            con.execute("delete from tokens where module_id = ?", (donor_id,))
            con.execute("delete from xrefs where module_id = ?", (donor_id,))
            con.execute("delete from modules where id = ?", (donor_id,))
            message = (f"mesma Bíblia ({abbr}) que {Path(keeper_path).name}; mantida aquela, "
                       f"com {copied} de {headings} títulos de seção copiados desta")
            con.execute(
                "insert into import_log(at, level, origin_path, message) values (?, 'ignorado', ?, ?)",
                (now(), donor_path, message),
            )
            print(f"  unido    {Path(donor_path).name} -> {Path(keeper_path).name} ({copied} títulos)")
            donors.append(donor_path)
    return donors


def build_strong_terms(con):
    """Índices de `tokens` e a tabela `strong_terms`: como cada idioma traduz cada Strong."""
    con.execute("create index if not exists tokens_by_strong on tokens(strong)")
    con.execute("create index if not exists tokens_by_ref on tokens(module_id, book, chapter, verse, pos)")
    con.execute("delete from strong_terms")  # derivada de tokens: sempre recalculada

    counts = Counter()
    for lang, surface, strong, lemma in con.execute(
        "select m.lang, t.surface, t.strong, t.lemma from tokens t join modules m on m.id = t.module_id"
        " where t.strong is not null"
    ):
        if surface and lang in ("por", "eng"):
            term = normalize_term(surface, lang)
            if term:
                counts[(strong, lang, term)] += 1
        if lemma:  # o lema está sempre na língua original
            if strong[0] == "G":
                counts[(strong, "grc", strip_accents(lemma.lower()))] += 1
            else:
                counts[(strong, "heb", lemma)] += 1
    totals = Counter()
    for (strong, lang, _), count in counts.items():
        totals[(strong, lang)] += count
    rows = [
        (strong, lang, term, count, round(count / totals[(strong, lang)], 4))
        for (strong, lang, term), count in counts.items()
        if count >= 2 or count / totals[(strong, lang)] >= 0.05  # descarta traduções isoladas
    ]
    con.executemany("insert into strong_terms values (?, ?, ?, ?, ?)", rows)
    return len(rows)


def check_residue(con):
    """Procura sobras de marcação no texto importado."""
    problems = []
    for table in ("verses", "comments", "entries"):
        count = con.execute(
            f"select count(*) from {table} where text like '%\\par%' or text like '%{{\\%'"
            " or text like '%\\cf%' or text like '%<W%>%'"
        ).fetchone()[0]
        if count:
            problems.append(f"{count} linhas em '{table}' com possível sobra de marcação")
    return problems


def forget_path(con, origin_path: str) -> int:
    """Apaga da base o que um arquivo de módulo gerou (D017). Devolve quantos módulos eram dele."""
    ids = [row[0] for row in con.execute("select id from modules where origin_path = ?", (origin_path,))]
    for module_id in ids:
        # Links e refs de comentários e verbetes saem antes, enquanto os itens ainda existem.
        for kind, table in (("comment", "comments"), ("entry", "entries")):
            for owner in ("links", "refs"):
                con.execute(f"delete from {owner} where kind = ? and item_id in"
                            f" (select id from {table} where module_id = ?)", (kind, module_id))
        for table in ("verses", "tokens", "xrefs", "headings", "comments", "entries"):
            con.execute(f"delete from {table} where module_id = ?", (module_id,))
        con.execute("delete from modules where id = ?", (module_id,))
    con.execute("delete from import_log where origin_path = ?", (origin_path,))
    con.execute("delete from import_files where origin_path = ?", (origin_path,))
    return len(ids)


def import_one(con, path: Path, sha: str) -> None:
    """Lê um arquivo de módulo, grava o resultado e registra o estado dele em import_files."""
    source, reader = READERS[path.suffix.lower()]
    adder = Adder(con, path, source, sha)
    tick = time.time()
    try:
        con.execute("savepoint module")
        reader(path, adder)
        con.execute("release module")
    except Exception as error:  # um módulo ruim não interrompe os demais
        con.execute("rollback to module")
        con.execute("release module")
        adder.module_id, adder.items = None, 0
        adder.log("erro", f"{type(error).__name__}: {error}")
    if adder.module_id:
        con.execute("update modules set items = ? where id = ?", (adder.items, adder.module_id))
        print(f"  ok       {adder.items:>7}  {time.time() - tick:5.1f}s  {path.name}")
        status = "importado"
    else:
        reason = con.execute(
            "select level, message from import_log where origin_path = ? order by id desc", (str(path),)
        ).fetchone()
        print(f"  {reason[0]:<8} {path.name}: {reason[1]}")
        status = "erro" if reason[0] == "erro" else "ignorado"
    con.execute("insert or replace into import_files values (?, ?, ?, ?)",
                (str(path), sha, db.IMPORTER_VERSION, status))
    con.commit()


def open_existing(out: Path):
    """Abre a base de saída para a importação incremental: (conexão, None) ou (None, motivo)."""
    try:
        con = sqlite3.connect(out)
        tables = {row[0] for row in con.execute("select name from sqlite_master where type = 'table'")}
        found = None
        if "meta" in tables:
            row = con.execute("select value from meta where key = 'importer_version'").fetchone()
            found = row[0] if row else None
    except sqlite3.DatabaseError as error:
        return None, f"não foi possível ler a base: {error}"
    if "import_files" not in tables:
        con.close()
        return None, "a base não tem a tabela import_files (é anterior à T10)"
    if found != db.IMPORTER_VERSION:
        con.close()
        return None, f"versão do importador na base: {found}; atual: {db.IMPORTER_VERSION}"
    con.executescript("pragma journal_mode = off; pragma synchronous = off;")
    return con, None


def sync_files(con, paths):
    """Lê os arquivos novos ou alterados, apaga os que sumiram e deixa os demais como estão (D017).

    Sem base anterior não há controle, então tudo é lido: é a importação completa.
    """
    control = {row[0]: row[1:] for row in con.execute(
        "select origin_path, origin_sha256, importer_version, status from import_files")}
    present = {str(path): path for path in paths}
    shas = {key: sha256(path) for key, path in present.items()}
    to_read, donors, skipped = [], [], 0
    for key, path in present.items():
        row = control.get(key)
        if row and row[0] == shas[key] and row[1] == db.IMPORTER_VERSION:
            if row[2] == "unido":
                donors.append(path)
            else:
                skipped += 1
        else:
            to_read.append(path)
    removed = [key for key in control if key not in present]
    if to_read or removed:
        # Algo mudou: as cópias unidas são relidas, porque a cópia que ficou pode depender delas.
        to_read.extend(donors)
    else:
        skipped += len(donors)
    for key in removed:
        forget_path(con, key)
        print(f"  removido {Path(key).name}")
    for path in to_read:
        key = str(path)
        if key in control:
            forget_path(con, key)
        import_one(con, path, shas[key])
    con.commit()
    return {"pulados": skipped, "lidos": len(to_read), "removidos": len(removed)}


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("folders", nargs="+", help="pastas com módulos")
    parser.add_argument("--out", default="data/library.db")
    parser.add_argument("--incremental", action="store_true",
                        help="reaproveita a base de saída e relê só o que mudou (D017)")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    con = None
    if args.incremental and out.exists():
        con, reason = open_existing(out)
        if con is None:
            print(f"aviso: a base existente não serve à importação incremental ({reason});"
                  " fazendo a importação completa")
    elif args.incremental:
        print(f"sem base existente em {out}; fazendo a importação completa")
    if con is None:
        if out.exists():
            out.unlink()
        con = db.create(out)
    started = time.time()

    paths = find_modules(args.folders)
    print(f"{len(paths)} arquivos de módulo encontrados")
    stats = sync_files(con, paths)
    donors = merge_duplicate_bibles(con)
    for donor in donors:
        con.execute("update import_files set status = 'unido' where origin_path = ?", (donor,))
    con.commit()
    if args.incremental:
        print(f"incremental: {stats['pulados']} arquivos pulados sem releitura; {stats['lidos']} relidos"
              f" (novos, alterados ou cópias unidas); {stats['removidos']} removidos da base")
    print("montando termos por Strong...")
    terms = build_strong_terms(con)
    words = con.execute("select count(*) from tokens").fetchone()[0]
    print(f"  {words} palavras, {terms} termos")
    con.commit()
    print("montando índice de busca...")
    db.rebuild_search(con)
    con.execute("delete from import_log where level = 'aviso' and origin_path = ''")  # refeito a cada execução
    for problem in check_residue(con):
        con.execute("insert into import_log(at, level, origin_path, message) values (?, 'aviso', '', ?)",
                    (now(), problem))
        print("  aviso:", problem)
    con.executemany("insert or replace into meta values (?, ?)", [
        ("importer_version", db.IMPORTER_VERSION), ("built_at", now()),
        ("source_folders", json.dumps([str(Path(f).resolve()) for f in args.folders])),
    ])
    con.commit()

    columns = ("id source kind abbr title lang has_strongs items origin_path origin_sha256"
               " origin_size origin_mtime").split()
    report = {
        "built_at": now(),
        "importer_version": db.IMPORTER_VERSION,
        "source_folders": [str(Path(f).resolve()) for f in args.folders],
        "modules": [dict(zip(columns, row)) for row in
                    con.execute(f"select {', '.join(columns)} from modules order by id")],
        "log": [dict(zip(("at", "level", "origin_path", "message"), row)) for row in
                con.execute("select at, level, origin_path, message from import_log order by id")],
    }
    report_path = out.with_name("import-report.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    con.close()
    print(f"pronto em {time.time() - started:.1f}s: {len(report['modules'])} módulos importados,"
          f" {len(report['log'])} registros no log -> {out} ({out.stat().st_size / 1e6:.1f} MB)")
    print(f"relatório: {report_path}")


if __name__ == "__main__":
    main()
