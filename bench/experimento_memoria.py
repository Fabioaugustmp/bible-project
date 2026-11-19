"""Experimento de memória e qualidade da busca por sentido (BGE-M3), em CPU com 4 threads.

Mede, para cada modo, o pico de memória do processo (modelo + índice) e o tempo por consulta,
e compara as consultas com a versão fp32 (cosseno e sobreposição do top-10 nos versículos).
Os vetores dos textos vêm de data/embeddings.db, calculados pelo BGE-M3 em fp32; por isso
só as consultas mudam de modo.

Uso (a partir da raiz do projeto, no ambiente .venv-bench):
  .venv-bench\\Scripts\\python.exe bench\\experimento_memoria.py fp32 SAIDA
  .venv-bench\\Scripts\\python.exe bench\\experimento_memoria.py bf16 SAIDA
  .venv-bench\\Scripts\\python.exe bench\\experimento_memoria.py int8 SAIDA
  .venv-bench\\Scripts\\python.exe bench\\experimento_memoria.py comparar SAIDA
"""
import json
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
EMBED_DB = DATA / "embeddings.db"
MODEL_DIR = DATA / "hf-cache" / "hub" / "models--BAAI--bge-m3"
THREADS = 4          # o servidor tem 4 vCPUs

QUERIES = [
    "amor ao próximo como a si mesmo",
    "a graça de Deus salva pela fé",
    "Deus criou o mundo em seis dias",
    "perdão dos pecados por meio de Cristo",
    "quem é o bom pastor",
    "a ressurreição de Jesus ao terceiro dia",
    "orar sem cessar",
    "o Espírito Santo consola os crentes",
    "bem-aventurados os mansos",
    "não se preocupe com o amanhã",
    "a lei foi dada por Moisés",
    "o reino dos céus é semelhante a um tesouro escondido",
    "a fé sem obras é morta",
    "Jesus acalma a tempestade",
    "vencer o mal com o bem",
    "a sabedoria começa no temor do Senhor",
    "o sofrimento produz perseverança",
    "Davi e Golias",
    "a última ceia e a instituição da eucaristia",
    "esperança em tempos difíceis",
    "a parábola do filho pródigo",
    "servir aos outros com humildade",
    "a vinda do Messias profetizada em Isaías",
    "deixar as riquezas para seguir a Cristo",
    "a aliança de Deus com Abraão",
    "o juízo final e a volta de Cristo",
    "paz que excede todo entendimento",
    "Paulo escreve sobre o corpo de Cristo",
    "a oração do Pai Nosso",
    "a cura dos enfermos por Jesus",
    "o temor e a alegria no louvor",
]


def load_index():
    """Vetores como o serviço atual: versículos e comentários em float16 no arquivo,
    versículos convertidos para float32 e comentários mantidos em float16 (ver measure)."""
    con = sqlite3.connect(f"file:{EMBED_DB.as_posix()}?mode=ro", uri=True)
    index = {}
    for kind in ("verse", "comment"):
        rows = con.execute("select item_id, vector from embeddings where kind = ? and model = 'bge-m3'"
                           " order by item_id", (kind,)).fetchall()
        ids = np.array([r[0] for r in rows], dtype=np.int64)
        matrix = np.vstack([np.frombuffer(r[1], dtype=np.float16) for r in rows])
        if kind == "verse":
            matrix = matrix.astype(np.float32)
        index[kind] = (ids, matrix)
    con.close()
    return index


def scores(matrix, vector, chunk=20000):
    """Produto escalar em blocos: não converte a matriz inteira para float32 de uma vez."""
    if matrix.dtype == np.float32:
        return matrix @ vector
    out = np.empty(matrix.shape[0], dtype=np.float32)
    for i in range(0, matrix.shape[0], chunk):
        out[i:i + chunk] = matrix[i:i + chunk].astype(np.float32) @ vector
    return out


def load_model(mode):
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(THREADS)
    snap = sorted((MODEL_DIR / "snapshots").iterdir())[-1]
    model = SentenceTransformer(str(snap), device="cpu")
    model.max_seq_length = 512
    if mode == "bf16":
        model = model.to(torch.bfloat16)
    elif mode == "int8":
        model = torch.ao.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
    model.eval()
    return model


def measure(mode, out_dir):
    import psutil
    proc = psutil.Process()
    base = proc.memory_info().rss
    t0 = time.perf_counter()
    index = load_index()
    t_index = time.perf_counter() - t0
    t0 = time.perf_counter()
    model = load_model(mode)
    t_model = time.perf_counter() - t0

    vectors, times = [], []
    with torch_no_grad():
        model.encode(["aquecimento"], normalize_embeddings=True)   # primeira chamada é mais lenta
        for text in QUERIES:
            t0 = time.perf_counter()
            vec = model.encode([text], normalize_embeddings=True)[0].astype(np.float32)
            times.append(time.perf_counter() - t0)
            vectors.append(vec)
            _ = scores(index["verse"][1], vec)   # busca completa, como no serviço
            _ = scores(index["comment"][1], vec)
    vectors = np.stack(vectors)
    np.save(Path(out_dir) / f"consultas_{mode}.npy", vectors)

    mem = proc.memory_info()
    result = {
        "modo": mode,
        "pico_mb": round(getattr(mem, "peak_wset", mem.rss) / 2**20, 1),
        "rss_final_mb": round(mem.rss / 2**20, 1),
        "rss_antes_mb": round(base / 2**20, 1),
        "indice_carregado_s": round(t_index, 1),
        "modelo_carregado_s": round(t_model, 1),
        "consulta_mediana_ms": round(float(np.median(times)) * 1000, 0),
        "consulta_p90_ms": round(float(np.percentile(times, 90)) * 1000, 0),
        "consultas": len(QUERIES),
    }
    (Path(out_dir) / f"resultado_{mode}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


class torch_no_grad:
    def __enter__(self):
        import torch
        self.ctx = torch.no_grad()
        self.ctx.__enter__()

    def __exit__(self, *args):
        self.ctx.__exit__(*args)


def compare(out_dir):
    out = Path(out_dir)
    index = load_index()
    base = np.load(out / "consultas_fp32.npy")
    top = {}
    for mode in ("fp32", "bf16", "int8"):
        path = out / f"consultas_{mode}.npy"
        if not path.exists():
            continue
        vecs = np.load(path)
        cos = np.sum(vecs * base, axis=1) / (np.linalg.norm(vecs, axis=1) * np.linalg.norm(base, axis=1))
        overlaps = []
        for q_base, q_mode in zip(base, vecs):
            top_base = set(np.argsort(-scores(index["verse"][1], q_base))[:10])
            top_mode = set(np.argsort(-scores(index["verse"][1], q_mode))[:10])
            overlaps.append(len(top_base & top_mode) / 10)
        top[mode] = {
            "cosseno_medio_vs_fp32": round(float(cos.mean()), 4),
            "cosseno_minimo_vs_fp32": round(float(cos.min()), 4),
            "top10_sobreposicao_media": round(float(np.mean(overlaps)), 3),
            "top10_sobreposicao_minima": round(float(np.min(overlaps)), 3),
        }
    (out / "comparacao.json").write_text(json.dumps(top, indent=2), encoding="utf-8")
    print(json.dumps(top, indent=2), flush=True)


if __name__ == "__main__":
    mode, out_dir = sys.argv[1], sys.argv[2]
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    if mode == "comparar":
        compare(out_dir)
    else:
        measure(mode, out_dir)
