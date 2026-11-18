"""Indexação de embeddings (T32): gera vetores para versículos e comentários.

Os vetores ficam em data/embeddings.db, separado da biblioteca (data/library.db),
que continua somente leitura. Cada vetor guarda o modelo e a chave de origem, e a
indexação retoma de onde parou: itens já gravados para o mesmo modelo são pulados.

Uso (no ambiente .venv-bench, a partir da raiz do projeto):
  .venv-bench\\Scripts\\python.exe importer\\embed.py verses
  .venv-bench\\Scripts\\python.exe importer\\embed.py comments
"""
import argparse
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
LIBRARY = ROOT / "data" / "library.db"
TARGET = ROOT / "data" / "embeddings.db"
MODEL_DIR = ROOT / "data" / "hf-cache" / "hub" / "models--BAAI--bge-m3"
MODEL_NAME = "bge-m3"
DIM = 1024
BATCH = 32
MAX_TOKENS = 512   # comentários mais longos são cortados; ver D021 e T32

SCHEMA = """
create table if not exists embeddings(
    kind text not null,            -- 'verse' | 'comment'
    item_id integer not null,      -- id no library.db (verses.id ou comments.id)
    origin_key text,
    model text not null,
    dim integer not null,
    vector blob not null,          -- float16, normalizado
    primary key (kind, item_id, model)
);
"""


def snapshot() -> str:
    snaps = sorted((MODEL_DIR / "snapshots").iterdir())
    return str(snaps[-1])


def items_for(kind):
    lib = sqlite3.connect(f"file:{LIBRARY.as_posix()}?mode=ro", uri=True)
    if kind == "verses":
        module = lib.execute("select id from modules where abbr = 'ARA1993+'").fetchone()[0]
        rows = lib.execute("select id, text, origin_key from verses where module_id = ? order by id", (module,))
    else:
        rows = lib.execute(
            "select c.id, c.text, c.origin_key from comments c join modules m on m.id = c.module_id"
            " where m.lang = 'eng' and m.kind = 'commentary' order by c.id")
    result = rows.fetchall()
    lib.close()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["verses", "comments"])
    args = parser.parse_args()
    kind = "verse" if args.kind == "verses" else "comment"

    import torch
    from sentence_transformers import SentenceTransformer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"dispositivo: {device}", flush=True)
    items = items_for(args.kind)
    print(f"itens a indexar: {len(items)}", flush=True)

    out = sqlite3.connect(TARGET)
    out.executescript(SCHEMA)
    done = {row[0] for row in out.execute(
        "select item_id from embeddings where kind = ? and model = ?", (kind, MODEL_NAME))}
    pending = [item for item in items if item[0] not in done]
    print(f"já indexados: {len(done)}; pendentes: {len(pending)}", flush=True)
    if not pending:
        return

    model = SentenceTransformer(snapshot(), device=device)
    model.max_seq_length = MAX_TOKENS
    if device == "cuda":
        model.half()
    # Textos mais curtos primeiro dentro de cada lote evitam preenchimento desnecessário.
    pending.sort(key=lambda item: len(item[1]))

    start = time.time()
    for begin in range(0, len(pending), BATCH * 16):
        chunk = pending[begin:begin + BATCH * 16]
        vectors = model.encode([item[1] for item in chunk], batch_size=BATCH,
                               normalize_embeddings=True, show_progress_bar=False)
        vectors = np.asarray(vectors, dtype=np.float16)
        assert vectors.shape[1] == DIM, vectors.shape
        out.executemany(
            "insert or replace into embeddings values (?, ?, ?, ?, ?, ?)",
            [(kind, item[0], item[2], MODEL_NAME, DIM, vector.tobytes())
             for item, vector in zip(chunk, vectors)])
        out.commit()
        done_now = begin + len(chunk)
        elapsed = time.time() - start
        print(f"  {done_now}/{len(pending)}  {elapsed:7.1f}s", flush=True)

    total = out.execute("select count(*) from embeddings where kind = ? and model = ?",
                        (kind, MODEL_NAME)).fetchone()[0]
    print(f"concluído: {total} vetores de {kind} em {time.time() - start:.1f}s", flush=True)
    out.close()


if __name__ == "__main__":
    sys.exit(main())
