"""Avaliação de modelos de embeddings com dados da própria biblioteca (T31).

Duas tarefas, ambas com resposta conhecida a partir da base:
  A. Referências cruzadas (português -> português): dado um versículo, os versículos
     que a biblioteca liga a ele (listas curadas do theWord) devem aparecer entre os
     primeiros resultados.
  B. Versículo -> comentário (português -> inglês): dado um versículo, o comentário
     que o cobre deve aparecer entre os primeiros resultados. É o caso central do
     projeto: pergunta em português, material em inglês.

Métricas: recall@10 (o alvo está entre os 10 primeiros?) e MRR@10 (quão alto ele aparece).

Uso (a partir da raiz do projeto, no ambiente .venv-bench):
  .venv-bench\\Scripts\\python.exe bench\\eval_embeddings.py bge-m3 qwen3-0.6b
"""
import json
import random
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "library.db"
OUT = ROOT / "data" / "bench"
SEED = 7
N_QUERIES_A = 300     # consultas da tarefa A
N_QUERIES_B = 300     # comentários usados na tarefa B
N_DISTRACTORS_B = 2700  # comentários extras só para ocupar o índice
TOP_K = 10

MODELS = {
    "bge-m3": ROOT / "data" / "hf-cache" / "hub" / "models--BAAI--bge-m3",
    "qwen3-0.6b": ROOT / "data" / "hf-cache" / "hub" / "models--Qwen--Qwen3-Embedding-0.6B",
}


def snapshot(path: Path) -> str:
    snaps = sorted((path / "snapshots").iterdir())
    return str(snaps[-1])


def load_data(con):
    """Corpus de versículos em português (ARA1993+) e pares de referências cruzadas."""
    module = con.execute("select id from modules where abbr = 'ARA1993+'").fetchone()[0]
    verses = {}
    for book, chapter, verse, text in con.execute(
        "select book, chapter, verse, text from verses where module_id = ?", (module,)
    ):
        verses[(book, chapter, verse)] = text
    pairs = {}
    for book, chapter, verse, to_book, to_chapter, to_verse in con.execute(
        "select distinct book, chapter, verse, to_book, to_chapter, to_verse from xrefs"
    ):
        src, dst = (book, chapter, verse), (to_book, to_chapter, to_verse)
        if src in verses and dst in verses and src != dst:
            pairs.setdefault(src, set()).add(dst)
    # Comentários em inglês cobrindo um único versículo (intervalo curto), para a tarefa B.
    comments = con.execute(
        "select c.id, c.book, c.ref_start, c.ref_end, c.text from comments c join modules m on m.id = c.module_id"
        " where m.lang = 'eng' and m.kind = 'commentary' and c.ref_start > 1000"
        " and (c.ref_end - c.ref_start) <= 1 and length(c.text) between 200 and 1200"
    ).fetchall()
    return verses, pairs, comments


def mrr_recall(scores, relevant_sets):
    """scores: matriz consulta x alvo; relevant_sets: lista de conjuntos de índices relevantes."""
    recalls, rr = [], []
    for row, relevant in zip(scores, relevant_sets):
        top = np.argsort(-row)[:TOP_K]
        hit = [rank for rank, idx in enumerate(top, start=1) if idx in relevant]
        recalls.append(1.0 if hit else 0.0)
        rr.append(1.0 / hit[0] if hit else 0.0)
    return float(np.mean(recalls)), float(np.mean(rr))


def run(name, model_path, verses, pairs, comments):
    from sentence_transformers import SentenceTransformer
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(model_path, device=device, trust_remote_code=False)
    model.half() if device == "cuda" else None
    use_query_prompt = "query" in (model.prompts or {})
    rng = random.Random(SEED)
    result = {"model": name, "device": device}

    # --- Tarefa A: referências cruzadas, português -> português
    keys = sorted(pairs)
    rng.shuffle(keys)
    keys = [k for k in keys if k in verses][:N_QUERIES_A]
    corpus_keys = sorted(verses)
    index_of = {k: i for i, k in enumerate(corpus_keys)}
    t0 = time.time()
    corpus_vecs = model.encode([verses[k] for k in corpus_keys], batch_size=64,
                               normalize_embeddings=True, show_progress_bar=False)
    t_index = time.time() - t0
    query_texts = [verses[k] for k in keys]
    query_kwargs = {"prompt_name": "query"} if use_query_prompt else {}
    t0 = time.time()
    query_vecs = model.encode(query_texts, batch_size=64, normalize_embeddings=True,
                              show_progress_bar=False, **query_kwargs)
    t_query = time.time() - t0
    scores = query_vecs @ corpus_vecs.T
    relevant = [{index_of[d] for d in pairs[k]} for k in keys]
    recall_a, mrr_a = mrr_recall(scores, relevant)
    result["A_referencias"] = {"recall@10": round(recall_a, 4), "mrr@10": round(mrr_a, 4),
                               "consultas": len(keys), "indice_versiculos": len(corpus_keys),
                               "tempo_indexar_s": round(t_index, 1), "tempo_consultas_s": round(t_query, 1)}
    print(name, "A", result["A_referencias"], flush=True)

    # --- Tarefa B: versículo (português) -> comentário (inglês)
    rng.shuffle(comments)
    chosen = comments[:N_QUERIES_B]
    distract = comments[N_QUERIES_B:N_QUERIES_B + N_DISTRACTORS_B]
    items = chosen + distract
    item_texts = [c[4] for c in items]
    t0 = time.time()
    item_vecs = model.encode(item_texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
    t_index = time.time() - t0
    queries, relevant = [], []
    for i, (cid, book, ref_start, ref_end, text) in enumerate(chosen):
        verse_key = (book, ref_start // 1000, ref_start % 1000)
        if verse_key not in verses:
            continue
        queries.append(verses[verse_key])
        relevant.append({i})
    query_vecs = model.encode(queries, batch_size=64, normalize_embeddings=True,
                              show_progress_bar=False, **query_kwargs)
    scores = query_vecs @ item_vecs.T
    recall_b, mrr_b = mrr_recall(scores, relevant)
    result["B_comentarios"] = {"recall@10": round(recall_b, 4), "mrr@10": round(mrr_b, 4),
                               "consultas": len(queries), "itens_indexados": len(items),
                               "tempo_indexar_s": round(t_index, 1)}
    print(name, "B", result["B_comentarios"], flush=True)

    del model
    if device == "cuda":
        torch.cuda.empty_cache()
    return result


def main():
    wanted = sys.argv[1:] or list(MODELS)
    OUT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    verses, pairs, comments = load_data(con)
    print(f"versículos={len(verses)} consultas_A={len(pairs)} comentarios_B={len(comments)}", flush=True)
    results = []
    for name in wanted:
        results.append(run(name, snapshot(MODELS[name]), verses, pairs, comments))
    out = OUT / "resultados.json"
    existing = json.loads(out.read_text(encoding="utf-8")) if out.exists() else []
    merged = {r["model"]: r for r in existing}
    merged.update({r["model"]: r for r in results})
    out.write_text(json.dumps(list(merged.values()), ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n| modelo | A recall@10 | A MRR@10 | B recall@10 | B MRR@10 |")
    print("|---|---|---|---|---|")
    for r in merged.values():
        a, b = r["A_referencias"], r["B_comentarios"]
        print(f"| {r['model']} | {a['recall@10']} | {a['mrr@10']} | {b['recall@10']} | {b['mrr@10']} |")


if __name__ == "__main__":
    main()
