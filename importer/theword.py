"""Leitura dos módulos do theWord: Bíblias em texto (.ont/.ot/.nt) e .twm (SQLite)."""
import re

from canon import NT_VERSES, OT_BOOKS, OT_VERSES, references
from db import MARK_CLOSE, MARK_OPEN, open_readonly, split_strongs
from rtf import rtf_to_text, tidy

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
            rows.append((book, chapter, verse, text, tagged, f"L{number}"))
    module_id = add.module(meta)
    add.verses(module_id, rows)
    return len(rows)


# --- .twm -------------------------------------------------------------------

_LINK = re.compile(r",(\d+)\.(\d+)\.(\d+),")
_KINDS = {"1": "dictionary", "2": "commentary"}
_KIND_NAMES = {"3": "livro", "4": "mapa", "5": "plano de leitura", "6": "devocional"}


def _links(src, tables):
    """topic_id -> versículos citados no tópico."""
    if "bible_link_search" not in tables:
        return {}
    found = {}
    for topic_id, data in src.execute("select topic_id, data from bible_link_search"):
        if isinstance(data, str):
            refs = {tuple(map(int, m)) for m in _LINK.findall(data)}
            found[topic_id] = [r for r in refs if 1 <= r[0] <= 66]
    return found


def read_twm(path, add):
    src = open_readonly(path)
    tables = {r[0] for r in src.execute("select name from sqlite_master where type='table'")}
    if not {"config", "content"} <= tables:
        raise ValueError("estrutura .twm não reconhecida (sem tabelas config/content)")
    config = {k: v for k, v in src.execute("select name, value from config")}
    module_type = str(config.get("type"))
    kind = _KINDS.get(module_type)
    if kind is None:
        src.close()
        label = _KIND_NAMES.get(module_type, f"tipo {module_type}")
        add.log("ignorado", f"módulo do tipo '{label}' ainda não é importado")
        return 0
    meta = {
        "kind": kind,
        "abbr": config.get("abbrev") or path.stem[:20],
        "title": config.get("title") or path.stem,
        "author": config.get("author"),
        "lang": config.get("lang") or "und",
    }
    links = _links(src, tables)
    unreadable = 0
    module_id = add.module(meta)

    if kind == "commentary":
        rows, row_links = [], []
        for topic_id, bi, ci, fvi, tvi, data in src.execute(
            "select r.topic_id, r.bi, r.ci, r.fvi, r.tvi, c.data"
            " from bible_refs r join content c on c.topic_id = r.topic_id"
        ):
            if not isinstance(data, str):
                unreadable += 1
                continue
            text = rtf_to_text(data)
            if not text or not 1 <= bi <= 66:
                continue
            start = ci * 1000 + fvi
            rows.append((bi, start, max(start, ci * 1000 + (tvi or fvi)), text, f"topic:{topic_id}"))
            row_links.append(links.get(topic_id, ()))
        add.comments(module_id, rows, row_links)
    else:
        rows, row_links = [], []
        for topic_id, subject, data in src.execute(
            "select t.id, t.subject, c.data from topics t join content c on c.topic_id = t.id"
        ):
            if not isinstance(data, str):
                unreadable += 1
                continue
            text = rtf_to_text(data)
            if subject and text:
                rows.append((str(subject).strip(), text, f"topic:{topic_id}"))
                row_links.append(links.get(topic_id, ()))
        add.entries(module_id, rows, row_links)
    src.close()
    if unreadable:
        add.log("aviso", f"{unreadable} tópicos com conteúdo binário (comprimido ou RVF) foram ignorados")
    return len(rows)


def read_encrypted(path, add):
    add.log("ignorado", "módulo criptografado do theWord (cabeçalho TWENCBMOD); não é possível ler")
    return 0


READERS = {
    ".ont": read_bible, ".ot": read_bible, ".nt": read_bible,
    ".twm": read_twm,
    ".ontx": read_encrypted, ".otx": read_encrypted, ".ntx": read_encrypted,
}
