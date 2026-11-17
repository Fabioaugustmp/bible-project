"""Conversão de RTF (documento completo ou fragmento) para texto limpo."""
import re

from refs import CLOSE, MID, OPEN, strip_marks

# Grupos cujo conteúdo não é texto visível.
_DESTINATIONS = frozenset(
    """fonttbl colortbl stylesheet info pict object header footer headerl headerr
    footerl footerr footnote ftnsep ftnsepc ftncn generator listtable
    listoverridetable revtbl rsidtbl datastore themedata colorschememapping
    latentstyles xmlnstbl fldinst pntext pntxta pntxtb bkmkstart bkmkend""".split()
)

_SPECIAL = {
    "par": "\n", "sect": "\n\n", "page": "\n\n", "line": "\n", "row": "\n",
    "tab": "\t", "cell": "\t", "emdash": "—", "endash": "–", "bullet": "•",
    "emspace": " ", "enspace": " ", "qmspace": " ",
    "lquote": "‘", "rquote": "’", "ldblquote": "“", "rdblquote": "”",
}

_TOKEN = re.compile(
    r"\\([a-zA-Z]{1,32})(-?\d{1,10})?[ ]?"  # palavra de controle
    r"|\\'([0-9a-fA-F]{2})"                 # byte em hexadecimal
    r"|\\([^a-zA-Z])"                       # símbolo de controle
    r"|([{}])"                              # grupo
    r"|[\r\n]+"                             # quebra de linha crua (ignorada no RTF)
    r"|(.)",                                # caractere comum
    re.S,
)

_SPACES = re.compile(r"[ \t\u00a0]+")
_BLANK_LINES = re.compile(r"\n{3,}")


def tidy(text: str) -> str:
    """Normaliza espaços e linhas em branco."""
    lines = [_SPACES.sub(" ", line).strip() for line in text.replace("\r", "\n").split("\n")]
    return _BLANK_LINES.sub("\n\n", "\n".join(lines)).strip()


_HYPERLINK = re.compile(r'HYPERLINK\s+"([^"]*)"')


def rtf_to_text(source: str) -> str:
    """RTF -> texto limpo (links viram só o texto visível)."""
    return strip_marks(rtf_to_marked(source))


def rtf_to_marked(source: str) -> str:
    """RTF -> texto limpo, com o trecho visível de cada HYPERLINK entre as marcas
    OPEN alvo MID ... CLOSE de importer/refs.py (para guardar a posição das citações)."""
    if not source:
        return ""
    if "\\" not in source and "{" not in source:
        return tidy(source)

    stack = []          # (ucskip, ignorable, mode) de cada grupo aberto
    ignorable = False   # dentro de um grupo sem texto visível
    ucskip = 1          # caracteres de fallback após \uN
    mode = None         # None | 'fldinst' (instrução do campo) | 'fldrslt' (texto visível do campo)
    instruction = []    # texto da instrução do campo em leitura
    target = None       # alvo do último HYPERLINK lido, à espera do fldrslt
    link_open = False
    skip = 0
    out = []

    def emit(text):
        if mode == "fldinst":
            instruction.append(text)
        elif not ignorable:
            out.append(text)

    for match in _TOKEN.finditer(source):
        word, arg, hexbyte, symbol, brace, char = match.groups()
        if brace:
            skip = 0
            if brace == "{":
                stack.append((ucskip, ignorable, mode))
            elif stack:
                closing = mode
                ucskip, ignorable, mode = stack.pop()
                if closing == "fldinst" and mode != "fldinst":
                    found = _HYPERLINK.search("".join(instruction))
                    target = found.group(1) if found else None
                    instruction = []
                elif closing == "fldrslt" and mode != "fldrslt":
                    if link_open:
                        out.append(CLOSE)
                        link_open = False
                    target = None
        elif symbol:
            skip = 0
            if symbol == "*":
                ignorable = True
            elif symbol == "~":
                emit(" ")
            elif symbol in "{}\\":
                emit(symbol)
            elif symbol in "\r\n":
                emit("\n")
            elif symbol == "_":
                emit("-")
        elif word:
            skip = 0
            if word == "fldinst":
                mode, ignorable, instruction = "fldinst", True, []
            elif word == "fldrslt":
                mode = "fldrslt"
                if target and not ignorable and not link_open:
                    out.append(OPEN + target + MID)
                    link_open = True
            elif word in _DESTINATIONS:
                ignorable = True
            elif ignorable and mode != "fldinst":
                pass
            elif word in _SPECIAL:
                emit(_SPECIAL[word])
            elif word == "uc":
                ucskip = int(arg) if arg else 1
            elif word == "u" and arg:
                code = int(arg)
                if code < 0:
                    code += 65536
                try:
                    emit(chr(code))
                except ValueError:
                    pass
                skip = ucskip
        elif hexbyte:
            if skip > 0:
                skip -= 1
            else:
                emit(bytes([int(hexbyte, 16)]).decode("cp1252", "replace"))
        elif char:
            if skip > 0:
                skip -= 1
            else:
                emit(char)

    if link_open:
        out.append(CLOSE)
    return tidy("".join(out))
