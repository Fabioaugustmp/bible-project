"""Citações bíblicas dentro de comentários e verbetes (tarefa T24, desenho em EC5).

Duas origens:
- theWord: campos HYPERLINK (RTF) e itens com link (RVF). Os conversores
  marcam o trecho visível de cada link com os caracteres OPEN, MID e CLOSE;
  `extract` tira as marcas e devolve o texto limpo com as posições.
- e-Sword: só texto. `find_plain` reconhece "Exo_19:3-6" (abreviação inglesa
  do e-Sword) e "Is 48.6-7; Jr 31.22" (abreviação portuguesa).

Cada citação: (início, fim, livro, capítulo, versículo, capítulo final, versículo final),
com início e fim em caracteres do texto devolvido.
"""
import re
import unicodedata

from canon import BOOKS, VERSES

# Marcas de uso privado do Unicode: não aparecem em texto de módulo.
OPEN, MID, CLOSE = "", "", ""

_BIBLE_TARGET = re.compile(
    r"tw://(?:bible\.\*/?\?id=|\[self\]\?)(\d+)\.(\d+)\.(\d+)(?:-(?:(\d+)\.(\d+)\.)?(\d+))?")  # "*/?": erro comum nos módulos


def parse_target(target: str):
    """'tw://bible.*?id=51.1.15-51.1.18|...' -> (51, 1, 15, 1, 18); None se não for versículo."""
    match = _BIBLE_TARGET.match(target.strip())
    if not match:
        return None
    book, chapter, verse = int(match.group(1)), int(match.group(2)), int(match.group(3))
    end_book, end_chapter, end_verse = match.group(4), match.group(5), match.group(6)
    if not valid(book, chapter, verse):
        return None
    to_chapter, to_verse = chapter, verse
    if end_verse and (end_book is None or int(end_book) == book):
        to_chapter = int(end_chapter) if end_chapter else chapter
        to_verse = int(end_verse)
        if (to_chapter, to_verse) < (chapter, verse) or not valid(book, to_chapter, to_verse):
            to_chapter, to_verse = chapter, verse
    return book, chapter, verse, to_chapter, to_verse


def valid(book, chapter, verse) -> bool:
    return 1 <= book <= 66 and 1 <= chapter <= len(VERSES[book - 1]) and 1 <= verse <= VERSES[book - 1][chapter - 1]


def label(book, chapter, verse, to_chapter, to_verse) -> str:
    """Rótulo em português: 'Gn 6:16-20', 'Rm 3:21 – 4:2'."""
    text = f"{BOOKS[book - 1][0]} {chapter}:{verse}"
    if (to_chapter, to_verse) == (chapter, verse):
        return text
    return f"{text}-{to_verse}" if to_chapter == chapter else f"{text} – {to_chapter}:{to_verse}"


_PLACEHOLDERS = {"[vref]", "*", ""}
MAX_VISIBLE = 80  # texto de link mais longo que isto não é tratado como citação
_MARKED = re.compile(f"{OPEN}([^{MID}{CLOSE}]*){MID}([^{OPEN}{CLOSE}]*){CLOSE}")


def extract(marked: str):
    """Texto com marcas -> (texto limpo, citações). Marcas sem versículo válido somem."""
    out, refs, last, size = [], [], 0, 0
    for match in _MARKED.finditer(marked):
        before = marked[last:match.start()]
        out.append(before)
        size += len(before)
        last = match.end()
        target, visible = parse_target(match.group(1)), match.group(2)
        if target is None:
            out.append(visible)
            size += len(visible)
            continue
        stripped = visible.strip()
        if stripped in _PLACEHOLDERS:  # o módulo mostra "[vref]" no lugar da referência
            leading = visible[:len(visible) - len(visible.lstrip())]
            visible = leading + label(*target)
            stripped = label(*target)
        start = size + (len(visible) - len(visible.lstrip()))
        out.append(visible)
        size += len(visible)
        # Link cujo texto é só pontuação (";") ou uma frase inteira não é uma citação legível.
        if any(ch.isalnum() for ch in stripped) and len(stripped) <= MAX_VISIBLE:
            refs.append((start, start + len(stripped), *target))
    tail = marked[last:]
    # Marcas soltas (link sem fechamento) não podem chegar ao texto.
    out.append(tail.replace(OPEN, "").replace(MID, "").replace(CLOSE, ""))
    return "".join(out), refs


def strip_marks(marked: str) -> str:
    return extract(marked)[0]


# --- e-Sword: citações só em texto ------------------------------------------------

def _key(name: str) -> str:
    decomposed = unicodedata.normalize("NFD", name.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c) and c.isalnum())


# Abreviações inglesas do e-Sword (as que aparecem nos módulos instalados).
_ESWORD = """Gen Exo Lev Num Deu Jos Jdg Rth Sa1 Sa2 Ki1 Ki2 Ch1 Ch2 Ezr Neh Est Job Psa Pro Ecc Son Isa Jer
Lam Eze Dan Hos Joe Amo Oba Jon Mic Nah Hab Zep Hag Zec Mal Mat Mar Luk Joh Act Rom Co1 Co2 Gal Eph Phi
Col Th1 Th2 Ti1 Ti2 Tit Phm Heb Jam Pe1 Pe2 Jo1 Jo2 Jo3 Jud Rev""".split()
ENGLISH = {}
for number, name in enumerate(_ESWORD, start=1):
    ENGLISH[_key(name[-1] + name[:-1] if name[-1].isdigit() else name)] = number
ENGLISH.update({_key(k): v for k, v in {"Rut": 8, "Jas": 59, "Php": 50, "Jde": 65, "Sng": 22}.items()})
# O comentário Diário Viver mistura abreviações portuguesas no mesmo formato ("Hb_", "Jr_").
_MIXED = {"Et": 17, "Hb": 58, "Hc": 35, "Jd": 65, "Jn": 32, "Jr": 24, "Na": 34, "Ne": 16, "Tt": 56}
ENGLISH.update({_key(k): v for k, v in _MIXED.items()})

PORTUGUESE = {}
for number, (abbr, name) in enumerate(BOOKS, start=1):
    PORTUGUESE[_key(abbr)] = number
    PORTUGUESE[_key(name)] = number
_VARIANTS = {
    # grafias e abreviações alternativas
    "Ex": 2, "Jos": 6, "Rut": 8, "Sal": 19, "Salmo": 19, "Pr": 20, "Can": 22, "Os": 28, "Miq": 33,
    "Sof": 36, "Gênese": 1, "Isaias": 23, "Juizes": 7, "Atos": 44, "1Cor": 46, "2Cor": 47,
    # traduções automáticas do espanhol nos módulos do e-Sword (Reina-Valera, Diário Vivir)
    "1Rss": 11, "2Rss": 12, "1Rseis": 11, "2Rseis": 12, "1Rsseis": 11, "2Rsseis": 12,
    "1Smamuel": 9, "2Smamuel": 10, "Mau": 39, "Feitos": 44,
}
PORTUGUESE.update({_key(k): v for k, v in _VARIANTS.items()})

_UNDERSCORE = re.compile(r"\b([1-3]?[A-Z][a-z]{1,2})_(\d{1,3}):(\d{1,3})(?:-(\d{1,3})(?::(\d{1,3}))?)?")
_DOTTED = re.compile(
    r"(?<![\w.])((?:[1-3] ?)?[A-ZÁÉÍÓÚÊÔ][a-záéíóúêôçãõ]{0,13})\.? (\d{1,3})[.:](\d{1,3})"
    r"(?:\s?[-–]\s?(\d{1,3})(?:[.:](\d{1,3}))?)?")
_CONTINUATION = re.compile(r"; ?(\d{1,3})[.:](\d{1,3})(?:\s?[-–]\s?(\d{1,3})(?:[.:](\d{1,3}))?)?")


def _range(book, chapter, verse, end_a, end_b):
    """Fim do intervalo: '-7' (versículo) ou '-10.28' (capítulo e versículo)."""
    if end_a is None:
        return chapter, verse
    to_chapter, to_verse = (int(end_a), int(end_b)) if end_b else (chapter, int(end_a))
    if (to_chapter, to_verse) < (chapter, verse) or not valid(book, to_chapter, to_verse):
        return chapter, verse
    return to_chapter, to_verse


def _book_of(name: str, table):
    """'2 Rss' -> 12. Se o número na frente não forma livro ('3 Is'), tenta sem ele."""
    key = _key(name)
    if key in table:
        return table[key], 0
    if key[:1].isdigit() and key[1:] in table:
        return table[key[1:]], len(name) - len(name.lstrip("123").lstrip())
    return None, 0


def find_plain(text: str):
    """Citações escritas no texto (e-Sword) -> (texto, citações).

    As abreviações inglesas do e-Sword ('Exo_19:3-6') são trocadas pelo rótulo
    em português ('Êx 19:3-6'); as citações em português ficam como estão.
    """
    pieces, refs, last, size = [], [], 0, 0

    def keep(upto):
        nonlocal last, size
        piece = text[last:upto]
        pieces.append(piece)
        size += len(piece)
        last = upto

    for match in _UNDERSCORE.finditer(text):
        book, _ = _book_of(match.group(1), ENGLISH)
        chapter, verse = int(match.group(2)), int(match.group(3))
        if not book or not valid(book, chapter, verse):
            continue
        to_chapter, to_verse = _range(book, chapter, verse, match.group(4), match.group(5))
        keep(match.start())
        shown = label(book, chapter, verse, to_chapter, to_verse)
        pieces.append(shown)
        refs.append((size, size + len(shown), book, chapter, verse, to_chapter, to_verse))
        size += len(shown)
        last = match.end()
    keep(len(text))
    text = "".join(pieces)

    taken = [(start, end) for start, end, *_ in refs]  # rótulos que acabaram de ser escritos
    for match in _DOTTED.finditer(text):
        if any(start < match.end() and match.start() < end for start, end in taken):
            continue
        book, skip = _book_of(match.group(1), PORTUGUESE)
        chapter, verse = int(match.group(2)), int(match.group(3))
        if not book or not valid(book, chapter, verse):
            continue
        to_chapter, to_verse = _range(book, chapter, verse, match.group(4), match.group(5))
        refs.append((match.start() + skip, match.end(), book, chapter, verse, to_chapter, to_verse))
        # "Sl 10.9; 17.12; 22.13": as seguintes são do mesmo livro.
        position = match.end()
        while True:
            more = _CONTINUATION.match(text, position)
            if not more:
                break
            chapter, verse = int(more.group(1)), int(more.group(2))
            if not valid(book, chapter, verse):
                break
            to_chapter, to_verse = _range(book, chapter, verse, more.group(3), more.group(4))
            start = more.start() + len(more.group(0)) - len(more.group(0).lstrip("; "))
            refs.append((start, more.end(), book, chapter, verse, to_chapter, to_verse))
            position = more.end()
    refs.sort()
    return text, refs


MAX_EXPANDED = 60  # intervalo maior que isto conta só o primeiro versículo na lista de citados


def verses_of(ref):
    """Versículos de uma citação, um a um (como a lista de citados do theWord)."""
    book, chapter, verse, to_chapter, to_verse = ref[2:7]
    found = []
    while (chapter, verse) <= (to_chapter, to_verse) and len(found) < MAX_EXPANDED:
        found.append((book, chapter, verse))
        verse += 1
        if verse > VERSES[book - 1][chapter - 1]:
            chapter, verse = chapter + 1, 1
    return found
