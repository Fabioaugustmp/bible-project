"""Leitura dos módulos do theWord: Bíblias em texto (.ont/.ot/.nt) e .twm (SQLite)."""
import re
import zlib

from canon import NT_VERSES, OT_BOOKS, OT_VERSES, references
from db import MARK_CLOSE, MARK_OPEN, open_readonly, split_strongs, strip_controls
from rtf import rtf_to_text, tidy
from rvf import is_rvf, rvf_to_text
from tokens import from_marked, from_wt, tagged_of, text_of

# --- Bíblias ----------------------------------------------------------------

_NOTE = re.compile(r"<RF[^>]*>.*?<Rf>", re.S)
_HEADING = re.compile(r"<TS\d?>(.*?)<Ts>", re.S)
_VARIANT = re.compile(r"<V[^<>]*>")  # variantes textuais do TR, embutidas em uma tag
_XREF = re.compile(r"<RX (\d+)\.(\d+)\.(\d+)(?:\+(\d+))?>")  # referência cruzada embutida
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
    """Uma linha de versículo -> (título de seção, texto, texto marcado, palavras)."""
    line = strip_controls(line)
    titles = [tidy(_TAG.sub("", title)) for title in _HEADING.findall(line)]
    heading = " · ".join(title for title in titles if title) or None
    line = _VARIANT.sub("", _HEADING.sub(" ", _NOTE.sub("", line)))
    if "<wt>" in line:  # uma palavra por <wt>: TR e interlineares
        words = from_wt(_BREAK.sub(" ", line))
        return heading, text_of(words), tagged_of(words), words
    line = _STRONG.sub(lambda m: f"{MARK_OPEN}{m.group(1)}{m.group(2)}{MARK_CLOSE}", line)
    line = _TAG.sub("", _BREAK.sub(" ", line))
    # Códigos seguidos da mesma expressão viram um só marcador.
    line = line.replace(f"{MARK_CLOSE}{MARK_OPEN}", "|")
    if MARK_OPEN not in line:
        return heading, split_strongs(line)[0], None, []
    words = from_marked(line)
    return heading, text_of(words), tagged_of(words), words


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


_TITLE_END = re.compile(r"[.;] |, Copyright| Copyright| Toggles| With ")


def _short_title(text: str) -> str:
    """As descrições de Bíblia do theWord trazem licença e instruções; fica o começo."""
    title = _TITLE_END.split(tidy(text).replace("\n", " "), maxsplit=1)[0]
    return title[:90].strip(" .,;")


def read_bible(path, add):
    first, last, count = _RANGES[path.suffix.lower()]
    lines = _decode(path.read_bytes()).replace("\r\n", "\n").split("\n")
    if len(lines) < count:
        raise ValueError(f"esperadas {count} linhas de versículo, encontradas {len(lines)}")
    config = _trailer(lines[count:])
    meta = {
        "kind": "bible",
        "abbr": config.get("short.title") or path.stem,
        "title": _short_title(config.get("description") or config.get("title") or path.stem),
        "author": config.get("author"),
        "lang": config.get("lang") or "und",
        "has_strongs": 0,
    }
    rows, words, xrefs, odd_xrefs = [], [], [], 0
    for number, ((book, chapter, verse), line) in enumerate(zip(references(first, last), lines), start=1):
        for to_book, to_chapter, to_verse, span in _XREF.findall(line):
            if int(to_verse) == 0:
                odd_xrefs += 1  # forma 'livro.n.0', de significado ainda não confirmado
                continue
            xrefs.append((book, chapter, verse, int(to_book), int(to_chapter), int(to_verse), int(span or 0)))
        heading, text, tagged, verse_words = _clean_verse(line)
        if tagged:
            meta["has_strongs"] = 1
        if text:
            rows.append((book, chapter, verse, text, tagged, heading, f"L{number}"))
            words.extend((book, chapter, verse, pos, *word) for pos, word in enumerate(verse_words, start=1))
    module_id = add.module(meta)
    add.verses(module_id, rows)
    if meta["has_strongs"]:
        add.tokens(module_id, words)
    if xrefs:
        add.xrefs(module_id, xrefs)
    if odd_xrefs:
        add.log("aviso", f"{odd_xrefs} referências cruzadas na forma 'livro.n.0' foram ignoradas (significado não confirmado)")
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


def _verse_index(vi: int):
    """Índice de versículo do theWord: livro<<24 | capítulo<<16 | versículo<<8 | extra."""
    return vi >> 24, (vi >> 16) & 255, (vi >> 8) & 255, vi & 255


def _read_xrefs(src, path, config, add):
    """Módulo de referências cruzadas: xrefs(vi1, vi2); o byte baixo de vi2 é a extensão do trecho."""
    rows = []
    for vi1, vi2 in src.execute("select vi1, vi2 from xrefs order by id"):
        book, chapter, verse, _ = _verse_index(vi1)
        to_book, to_chapter, to_verse, span = _verse_index(vi2)
        if 1 <= book <= 66 and 1 <= to_book <= 66:
            rows.append((book, chapter, verse, to_book, to_chapter, to_verse, span))
    src.close()
    title = config.get("tables.xrefs.description") or path.stem
    module_id = add.module({"kind": "xrefs", "abbr": "theWord xrefs", "title": title, "lang": "und"})
    add.xrefs(module_id, rows, count_as_items=True)
    return len(rows)


def _read_headings(src, path, config, add):
    """Módulo de títulos de seção: headings(vi, pos, level, content)."""
    rows = []
    for vi, level, content in src.execute("select vi, level, cast(content as blob) from headings order by id"):
        book, chapter, verse, _ = _verse_index(vi)
        text = tidy(_decode(content or b""))
        if 1 <= book <= 66 and text:
            rows.append((book, chapter, verse, level, text))
    src.close()
    title = config.get("tables.headings.description") or path.stem
    lang = "eng" if "english" in path.name.lower() else "und"
    module_id = add.module({"kind": "headings", "abbr": path.name.split(".")[1][:20] + " hdgs",
                            "title": title, "lang": lang})
    add.headings(module_id, rows)
    return len(rows)


def read_twm(path, add):
    src = open_readonly(path)
    tables = {r[0] for r in src.execute("select name from sqlite_master where type='table'")}
    config = {k: v for k, v in src.execute("select name, value from config")} if "config" in tables else {}
    module_type = str(config.get("type"))
    if "xrefs" in tables:
        return _read_xrefs(src, path, config, add)
    if "headings" in tables:
        return _read_headings(src, path, config, add)
    if "paragraphs" in tables:
        src.close()
        add.log("ignorado", "marcas de parágrafo: o significado do campo 'typ' ainda não foi confirmado")
        return 0
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
        query = ("select t.id, cast(t.subject as blob), cast(c.data as blob)"
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
            subject = _decode(record[1] or b"").strip()  # há títulos que não são UTF-8
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
