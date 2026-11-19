"""Serviço de busca por sentido (T33), roda no ambiente .venv-bench.

Carrega o BGE-M3 na GPU e os vetores de data/embeddings.db na memória, e responde
buscas por proximidade de sentido. O servidor da interface (app/server.py) usa só
a biblioteca padrão e consulta este serviço; se ele estiver parado, a busca por
palavra continua funcionando.

Uso (a partir da raiz do projeto):
  .venv-bench\\Scripts\\python.exe app\\embed_service.py
Escuta só em 127.0.0.1:8378.
"""
import json
import os
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("BIBLE_DATA_DIR", ROOT / "data"))
EMBED_DB = DATA_DIR / "embeddings.db"
MODEL_DIR = DATA_DIR / "hf-cache" / "hub" / "models--BAAI--bge-m3"
MODEL = "bge-m3"
PORT = int(os.environ.get("BIBLE_EMBED_PORT", "8378"))
HOST = os.environ.get("BIBLE_EMBED_HOST", "127.0.0.1")   # no contêiner: 0.0.0.0


def scores(matrix, vector, chunk=20000):
    """Produto escalar. Matriz em float32 vai direto; em float16, em blocos (não copia tudo)."""
    if matrix.dtype == np.float32:
        return matrix @ vector
    out = np.empty(matrix.shape[0], dtype=np.float32)
    for i in range(0, matrix.shape[0], chunk):
        out[i:i + chunk] = matrix[i:i + chunk].astype(np.float32) @ vector
    return out


class Index:
    def __init__(self):
        self.model = None
        self.kinds = {}   # kind -> (ids, matrix float32 normalizado)
        self.load()

    def load(self):
        con = sqlite3.connect(f"file:{EMBED_DB.as_posix()}?mode=ro", uri=True)
        for kind in ("verse", "comment"):
            rows = con.execute(
                "select item_id, vector from embeddings where kind = ? and model = ? order by item_id",
                (kind, MODEL)).fetchall()
            ids = np.array([r[0] for r in rows], dtype=np.int64)
            matrix = np.vstack([np.frombuffer(r[1], dtype=np.float16) for r in rows])
            del rows
            if kind == "verse":           # poucos vetores: float32 é barato
                matrix = matrix.astype(np.float32)
            # comentários ficam em float16 (cerca de 400 MB em vez de 800); ver scores()
            self.kinds[kind] = (ids, matrix)
            print(f"  {kind}: {len(ids)} vetores", flush=True)
        con.close()

    def encoder(self):
        if self.model is None:
            import torch
            from sentence_transformers import SentenceTransformer
            snap = sorted((MODEL_DIR / "snapshots").iterdir())[-1]
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = SentenceTransformer(str(snap), device=device)
            self.model.max_seq_length = 512
            if device == "cuda":
                self.model.half()
            print(f"  modelo carregado em {device}", flush=True)
        return self.model

    def search(self, text, kinds, k):
        vector = self.encoder().encode([text], normalize_embeddings=True)[0].astype(np.float32)
        out = {}
        for kind in kinds:
            ids, matrix = self.kinds[kind]
            sims = scores(matrix, vector)
            top = np.argsort(-sims)[:k]
            out[kind] = [{"item_id": int(ids[i]), "score": round(float(sims[i]), 4)} for i in top]
        return out

    def similar(self, kind, item_id, k):
        """Itens mais parecidos a um item já indexado, pelo vetor guardado (sem o modelo)."""
        ids, matrix = self.kinds[kind]
        i = int(np.searchsorted(ids, item_id))
        if i >= len(ids) or ids[i] != item_id:
            return None
        sims = scores(matrix, matrix[i].astype(np.float32))
        sims[i] = -1.0
        top = np.argsort(-sims)[:k]
        return [{"item_id": int(ids[j]), "score": round(float(sims[j]), 4)} for j in top]


INDEX = None


class Handler(BaseHTTPRequestHandler):
    server_version = "EmbedService/0.1"

    def log_message(self, fmt, *args):
        pass

    def reply(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self.reply(200, {"ok": True, "model": MODEL})
        else:
            self.reply(404, {"error": "não encontrado"})

    def do_POST(self):
        if self.path == "/similar":
            return self.similar_reply()
        if self.path != "/search":
            return self.reply(404, {"error": "não encontrado"})
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            text = str(data["q"]).strip()
            kinds = [k for k in data.get("kinds", ["verse", "comment"]) if k in ("verse", "comment")]
            k = max(1, min(50, int(data.get("k", 10))))
        except (ValueError, KeyError, TypeError):
            return self.reply(400, {"error": "pedido inválido"})
        if not text:
            return self.reply(400, {"error": "consulta vazia"})
        self.reply(200, {"results": INDEX.search(text, kinds, k)})


def _similar_reply(self):
    length = int(self.headers.get("Content-Length", 0))
    try:
        data = json.loads(self.rfile.read(length).decode("utf-8"))
        kind = data.get("kind", "verse")
        item_id = int(data["item_id"])
        k = max(1, min(50, int(data.get("k", 10))))
    except (ValueError, KeyError, TypeError):
        return self.reply(400, {"error": "pedido inválido"})
    if kind not in ("verse", "comment"):
        return self.reply(400, {"error": "tipo inválido"})
    results = INDEX.similar(kind, item_id, k)
    if results is None:
        return self.reply(404, {"error": "fora do índice"})
    self.reply(200, {"results": results})


Handler.similar_reply = _similar_reply


def main():
    global INDEX
    print("carregando vetores...", flush=True)
    INDEX = Index()
    INDEX.encoder()   # carrega o modelo já na partida, para a primeira busca ser rápida
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"busca por sentido em http://{HOST}:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main())
