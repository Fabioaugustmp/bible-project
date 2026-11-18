"""Importa as notas do e-Sword (T41) para data/user.db, com procedência.

Formato verificado (docs/FORMATOS.md): study.notx é um SQLite com a tabela
Verses(Book, Chapter, Verse, Notes), e Notes é RTF. Cada linha vira uma nota
presa ao versículo (chave KJV, D005), ligada a um registro em `imports` com o
caminho e o SHA-256 do arquivo. Reimportar o mesmo arquivo não duplica nada.

Uso (a partir da raiz do projeto):
    python importer/notes_esword.py "C:\\Users\\...\\Documents\\e-Sword\\study.notx"

Só lê o arquivo de origem (modo somente leitura) e não altera a pasta do e-Sword.
"""
import hashlib
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importer"))  # rtf.py importa refs como módulo de topo

from app import userdata  # noqa: E402
from importer.rtf import rtf_to_text  # noqa: E402


def import_file(path: Path) -> str:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    con = userdata.connect()
    try:
        if con.execute("select id from imports where origin_sha256 = ?", (digest,)).fetchone():
            return "já importado (nada a fazer)"
        source = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        try:
            rows = source.execute("select Book, Chapter, Verse, Notes from Verses").fetchall()
        finally:
            source.close()
        stamp = userdata.now()
        cur = con.execute(
            "insert into imports(origin_path, origin_sha256, imported_at, notes_count) values (?, ?, ?, 0)",
            (str(path), digest, stamp))
        import_id = cur.lastrowid
        count = 0
        for book, chapter, verse, notes in rows:
            text = rtf_to_text(notes or "").strip()
            if not text:
                continue
            con.execute("insert or ignore into anchors(book, chapter, verse) values (?, ?, ?)",
                        (book, chapter, verse))
            anchor = con.execute("select id from anchors where book = ? and chapter = ? and verse = ?",
                                 (book, chapter, verse)).fetchone()["id"]
            con.execute(
                "insert into notes(anchor_id, body, created_at, updated_at, import_id) values (?, ?, ?, ?, ?)",
                (anchor, text, stamp, stamp, import_id))
            count += 1
        con.execute("update imports set notes_count = ? where id = ?", (count, import_id))
        con.commit()
        return f"{count} notas importadas de {len(rows)} linhas (import {import_id})"
    finally:
        con.close()


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    for name in argv:
        print(f"{name}: {import_file(Path(name))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
