"""Modelo de palavras: transforma um versículo marcado em uma lista de palavras.

Cada palavra é uma tupla
    (surface, strong, lemma, morph, original, translit, gloss)

- surface: o que aparece no texto do módulo (português, inglês ou original);
  vazio quando a palavra original não foi traduzida.
- strong: 'G25' / 'H7225', ou None para texto sem código.
- lemma, morph: quando o módulo traz.
- original, translit, gloss: só nos interlineares.

Há dois formatos de origem:
- texto com códigos depois da expressão (KJV, ARA com Strong): `from_marked`;
- uma palavra por `<wt>` com campos próprios (TR, interlineares BSB): `from_wt`.
"""
import re
import unicodedata

from db import MARK_CLOSE, MARK_OPEN

# Acima destes números o código não é um verbete do Strong, e sim a análise do
# verbo (tempo, voz, modo) usada em alguns módulos, como H8804 e G5656.
LEXICAL_LIMIT = {"H": 8674, "G": 5624}

_MARKER = re.compile(f"{MARK_OPEN}([^{MARK_CLOSE}]*){MARK_CLOSE}")
_SPACES = re.compile(r"\s+")
_HAS_LETTER = re.compile(r"[^\W\d_]")


def split_codes(codes):
    """Separa códigos lexicais dos de análise verbal: (['G25'], ['G5656'])."""
    lexical, morph = [], []
    for code in codes:
        if code[1:].isdigit() and int(code[1:]) <= LEXICAL_LIMIT.get(code[0], 0):
            lexical.append(code)
        else:
            morph.append(code)
    return lexical, morph


def _clean(text):
    return _SPACES.sub(" ", text).strip()


def _emit(out, surface, codes, lemma=None, morph=None, original=None, translit=None, gloss=None):
    """Acrescenta a palavra; com vários códigos lexicais, a expressão fica no primeiro."""
    lexical, extra = split_codes(codes)
    morph = morph or (" ".join(extra) or None)
    if not lexical:
        if surface and (codes or _HAS_LETTER.search(surface)):
            out.append((surface, None, lemma, morph, original, translit, gloss))
        elif surface and out:
            # só pontuação: junta à palavra anterior
            previous = out[-1]
            out[-1] = (previous[0] + surface,) + previous[1:]
        return
    for index, code in enumerate(lexical):
        first = index == 0
        out.append((surface if first else "", code, lemma, morph,
                    original if first else None, translit if first else None, gloss if first else None))


def from_marked(marked: str):
    """Texto com marcadores de Strong depois de cada expressão -> palavras."""
    out = []
    parts = _MARKER.split(marked)  # [texto, códigos, texto, códigos, ..., texto]
    for index in range(0, len(parts) - 1, 2):
        _emit(out, _clean(parts[index]), [c for c in parts[index + 1].split("|") if c])
    tail = _clean(parts[-1])
    if tail:
        _emit(out, tail, [])
    return out


# --- formato <wt> do theWord ------------------------------------------------------

_E = re.compile(r"<E>(.*?)<e>", re.S)
_O = re.compile(r"<OG?>(.*?)<og?>", re.S)
_T = re.compile(r"<T>(.*?)<t>", re.S)
_CODE = re.compile(r"<W([GH])(\d+)[a-z]?>")
_MORPH = re.compile(r'<WT([^ >]*)(?: l="([^"]*)")?[^>]*>')
_ANY_TAG = re.compile(r"<[^<>]*>")
_PLACEHOLDER = {"-", "–", "—", "vvv", ". . ."}


def from_wt(line: str):
    """Linha com uma palavra por `<wt>` -> palavras. A linha já vem sem notas e títulos."""
    out = []
    segments = line.split("<wt>")
    prefix = _clean(_ANY_TAG.sub("", segments[0]))
    if prefix:
        _emit(out, prefix, [])
    for segment in segments[1:]:
        english, original, translit = _E.search(segment), _O.search(segment), _T.search(segment)
        codes = [f"{letter}{number}" for letter, number in _CODE.findall(segment)]
        morph_match = _MORPH.search(segment)
        morph = (morph_match.group(1) or None) if morph_match else None
        lemma = (morph_match.group(2) or None) if morph_match else None
        english_text = _clean(english.group(1)) if english else None
        original_text = _clean(original.group(1)) if original else None
        if english and original:
            # o campo que vem primeiro é a linha principal do módulo
            if english.start() < original.start():
                surface, source, gloss = english_text, original_text, None
            else:
                surface, source, gloss = original_text, None, english_text
        elif english or original:
            surface, source, gloss = english_text or original_text, None, None
        else:
            surface, source, gloss = _clean(_ANY_TAG.sub("", segment)), None, None
        if surface in _PLACEHOLDER:
            surface = ""  # palavra original sem tradução na linha principal
        if gloss in _PLACEHOLDER:
            gloss = None
        _emit(out, surface, codes, lemma, morph, source,
              _clean(translit.group(1)) if translit else None, gloss)
    return out


# --- texto a partir das palavras ---------------------------------------------------

_BEFORE_PUNCT = re.compile(r"\s+([,.;:!?”’)\]])")
_AFTER_OPEN = re.compile(r"([“‘(\[])\s+")


def text_of(words) -> str:
    """Texto corrido do versículo, sem códigos."""
    text = " ".join(word[0] for word in words if word[0])
    return _AFTER_OPEN.sub(r"\1", _BEFORE_PUNCT.sub(r"\1", text)).strip()


def tagged_of(words):
    """Texto com o Strong entre chaves depois de cada expressão, ou None se não há códigos."""
    if not any(word[1] for word in words):
        return None
    parts = []
    for surface, strong, *_ in words:
        code = f"{{{strong}}}" if strong else ""
        if surface:
            parts.append(surface + code)
        elif parts and code:
            parts[-1] += code
        elif code:
            parts.append(code)
    return _AFTER_OPEN.sub(r"\1", _BEFORE_PUNCT.sub(r"\1", " ".join(parts))).strip()


# --- termos por Strong ---------------------------------------------------------------

_NOT_WORD = re.compile(r"[^\w\s'’-]|[\d_]")
# Palavras que antecedem o núcleo da expressão: artigos, preposições, conjunções
# e possessivos. São retiradas só do começo, e nunca a última palavra.
_LEADING = {
    "por": set("o a os as um uma uns umas de do da dos das em no na nos nas ao aos à às e que para por "
               "pelo pela pelos pelas com se porque pois mas também ou nem como quando "
               "meu minha meus minhas teu tua teus tuas seu sua seus suas nosso nossa nossos nossas "
               "vosso vossa vossos vossas este esta estes estas esse essa aquele aquela é há não".split()),
    "eng": set("the a an of to in and that for with unto by on at from but or nor as when because "
               "my thy thine his her its our your their this that these those is are was be not".split()),
}


def strip_accents(text: str) -> str:
    """Remove acentos e espíritos do grego, para unir 'χάρις' e 'χαρις'."""
    decomposed = unicodedata.normalize("NFD", text)
    return unicodedata.normalize("NFC", "".join(c for c in decomposed if not unicodedata.combining(c)))


def normalize_term(surface: str, lang: str):
    """'No princípio,' -> 'princípio'; devolve None se não sobra palavra."""
    words = _NOT_WORD.sub(" ", surface.lower()).split()
    stop = _LEADING.get(lang, ())
    while len(words) > 1 and words[0] in stop:
        words.pop(0)
    term = " ".join(words).strip("'’-")
    return term or None
