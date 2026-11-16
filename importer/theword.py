"""Leitura dos módulos do theWord: Bíblias em texto (.ont/.ot/.nt) e .twm (SQLite)."""
import re
import zlib

from canon import NT_VERSES, OT_BOOKS, OT_VERSES, references
from db import MARK_CLOSE, MARK_OPEN, open_readonly, split_strongs
from rtf import rtf_to_text, tidy
from rvf import is_rvf, rvf_to_text

# --- Bíblias ----------------------------------------------------------------

_NOTE = re.compile(r"<RF[^>]*>.*?<Rf>", re.S)
_HEADING = re.compile(r"<TS\d?>.*?<Ts>", re.S)
_STRONG = re.compile(r"<W([GH])(\d+)[a-z]?>")
_BREAK = re.compile(r"<(?:BR|CM|CL|CI|PF\d?|PI\d?)>")
_TAG = re.compile(r"<[^<>]{0,300}>")

# extensão -> (primeiro livro, último livro, quantidade de versículos)
_RANGES = {
    ".ont": (1, 66, OT_VERSES + NT_VERSES),
    ".ot": (1, OT_BOOKS, OT_VERSES),
    ".nt": (OT_BOOKS + 1, 66, NT_VERSES),
}


def _decode(raw: bytes) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252", "replace")


def _clean_verse(line: str):
    line = _HEADING.sub(" ", _NOTE.sub("", line))
    line = _STRONG.sub(lambda m: f"{MARK_OPEN}{m.group(1)}{m.group(2)}{MARK_CLOSE}", line)
    line = _TAG.sub("", _BREAK.sub(" ", line))
    # Códigos seguidos da mesma palavra viram um só marcador: {G1|G2}.
    line = line.replace(f"{MARK_CLOSE}{MARK_OPEN}", "|")
    return split_strongs(line)


def _trailer(lines):
    """Linhas `chave=valor` depois do último versículo."""
    config, key = {}, None
    for line in lines:
        if key and line.startswith(" "):
            config[key] += " " + line.strip().rstrip("\\")
        elif "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            config[key] = value.strip().rstrip("\\")
    return config


def read_bible(path, add):
    first, last, count = _RANGES[path.suffix.lower()]
    lines = _decode(path.read_bytes()).replace("\r\n", "\n").split("\n")
    if len(lines) < count:
        raise ValueError(f"esperadas {count} linhas de versículo, encontradas {len(lines)}")
    config = _trailer(lines[count:])
    meta = {
        "kind": "bible",
        "abbr": config.get("short.title") or path.stem,
        "title": tidy(config.get("description") or config.get("title") or path.stem)[:200],
        "author": config.get("author"),
        "lang": config.get("lang") or "und",
        "has_strongs": 0,
    }
    rows = []
    for number, ((book, chapter, verse), line) in enumerate(zip(references(first, last), lines), start=1):
        text, tagged = _clean_verse(line)
        if tagged:
            meta["has_strongs"] = 1
        if text:
            rows.append((book, chapter, verse, text, tagged, None, f"L{number}"))
    module_id = add.module(meta)
    add.verses(module_id, rows)
    return len(rows)


# --- .twm -------------------------------------------------------------------

_LINK = re.compile(r",(\d+)\.(\d+)\.(\d+),")
_KINDS = {"1": "dictionary", "2": "commentary", "3": "book"}
_KIND_NAMES = {"4": "mapa", "5": "plano de leitura", "10": "referências cruzadas",
               "13": "layouts do programa", "None": "dados auxiliares (títulos ou parágrafos)"}
_ZLIB_HEADERS = (b"x\x01", b"x\x5e", b"x\x9c", b"x\xda")


def _links(src, tables):
    """topic_id -> versículos citados no tópico."""
    if "bible_link_search" not in tables:
        return {}
    found = {}
    for topic_id, data in src.execute("select topic_id, cast(data as blob) from bible_link_search"):
        if data:
            refs = {tuple(map(int, m)) for m in _LINK.findall(data.decode("ascii", "ignore"))}
            found[topic_id] = [r for r in refs if 1 <= r[0] <= 66]
    return found


def _looks_like_text(data: bytes) -> bool:
    sample = data[:400]
    printable = sum(32 <= b < 127 or b in (9, 10, 13) for b in sample)
    return printable >= len(sample) * 0.7


def _content_text(data):
    """Converte o conteúdo de um tópico em texto.

    Devolve (texto, estado): 'ok', 'parcial' (RVF com trechos pulados) ou
    'ilegivel' (criptografado ou formato desconhecido).
    """
    if not data:
        return "", "ok"
    if data[:2] in _ZLIB_HEADERS:
        try:
            data = zlib.decompress(data)
        except zlib.error:
            return "", "ilegivel"
    if is_rvf(data):
        text, resyncs = rvf_to_text(data)
        return text, "parcial" if resyncs else "ok"
    if not _looks_like_text(data):
        return "", "ilegivel"
    try:
        decoded = data.decode("utf-8")
    except UnicodeDecodeError:
        decoded = data.decode("cp1252", "replace")
    return rtf_to_text(decoded), "ok"


def read_twm(path, add):
    src = open_readonly(path)
    tables = {r[0] for r in src.execute("select name from sqlite_master where type='table'")}
    config = {k: v for k, v in src.execute("select name, value from config")} if "config" in tables else {}
    module_type = str(config.get("type"))
    kind = _KINDS.get(module_type)
    if kind is None or "content" not in tables:
        src.close()
        label = _KIND_NAMES.get(module_type, f"tipo {module_type}")
        add.log("ignorado", f"módulo do tipo '{label}' ainda não é importado")
        return 0
    if kind == "commentary" and "bible_refs" not in tables:
        kind = "book"

    if kind == "commentary":
        query = ("select r.topic_id, r.bi, r.ci, r.fvi, r.tvi, cast(c.data as blob)"
                 " from bible_refs r join content c on c.topic_id = r.topic_id")
    else:
        query = ("select t.id, t.subject, cast(c.data as blob)"
                 " from topics t join content c on c.topic_id = t.id order by t.id")

    rows, topic_ids, states = [], [], {"ok": 0, "parcial": 0, "ilegivel": 0}
    for record in src.execute(query):
        text, state = _content_text(record[-1])
        states[state] += 1
        if not text:
            continue
        topic_id = record[0]
        if kind == "commentary":
            _, bi, ci, fvi, tvi, _ = record
            if not (isinstance(bi, int) and 1 <= bi <= 66):
                continue
            ci, fvi, tvi = ci or 0, fvi or 0, tvi or 0
            start = ci * 1000 + fvi
            rows.append((bi, start, max(start, ci * 1000 + (tvi or fvi)), text, f"topic:{topic_id}"))
        else:
            subject = str(record[1] or "").strip()
            if not subject:
                continue
            rows.append((subject, text, f"topic:{topic_id}"))
        topic_ids.append(topic_id)

    if not rows:
        src.close()
        if states["ilegivel"]:
            add.log("ignorado", f"conteúdo criptografado ou em formato desconhecido ({states['ilegivel']} tópicos)")
        else:
            add.log("ignorado", "módulo sem conteúdo")
        return 0

    links = _links(src, tables)
    src.close()
    row_links = [links.get(topic_id, ()) for topic_id in topic_ids]
    module_id = add.module({
        "kind": kind,
        "abbr": config.get("abbrev") or path.stem[:20],
        "title": config.get("title") or path.stem,
        "author": config.get("author"),
        "lang": config.get("lang") or "und",
    })
    if kind == "commentary":
        add.comments(module_id, rows, row_links)
    else:
        add.entries(module_id, rows, row_links)
    if states["ilegivel"]:
        add.log("aviso", f"{states['ilegivel']} tópicos ilegíveis foram ignorados")
    if states["parcial"]:
        add.log("aviso", f"{states['parcial']} tópicos RVF lidos parcialmente (imagens ou tabelas puladas)")
    return len(rows)


def read_encrypted(path, add):
    add.log("ignorado", "módulo criptografado do theWord (cabeçalho TWENCBMOD); não é possível ler")
    return 0


READERS = {
    ".ont": read_bible, ".ot": read_bible, ".nt": read_bible,
    ".twm": read_twm,
    ".ontx": read_encrypted, ".otx": read_encrypted, ".ntx": read_encrypted,
}
