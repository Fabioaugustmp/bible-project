"""Conversão de RTF (documento completo ou fragmento) para texto limpo."""
import re

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


def rtf_to_text(source: str) -> str:
    if not source:
        return ""
    if "\\" not in source and "{" not in source:
        return tidy(source)

    stack = []          # (ucskip, ignorable) de cada grupo aberto
    ignorable = False   # dentro de um grupo sem texto visível
    ucskip = 1          # caracteres de fallback após \uN
    skip = 0
    out = []

    for match in _TOKEN.finditer(source):
        word, arg, hexbyte, symbol, brace, char = match.groups()
        if brace:
            skip = 0
            if brace == "{":
                stack.append((ucskip, ignorable))
            elif stack:
                ucskip, ignorable = stack.pop()
        elif symbol:
            skip = 0
            if symbol == "*":
                ignorable = True
            elif ignorable:
                pass
            elif symbol == "~":
                out.append(" ")
            elif symbol in "{}\\":
                out.append(symbol)
            elif symbol in "\r\n":
                out.append("\n")
            elif symbol == "_":
                out.append("-")
        elif word:
            skip = 0
            if word in _DESTINATIONS:
                ignorable = True
            elif ignorable:
                pass
            elif word in _SPECIAL:
                out.append(_SPECIAL[word])
            elif word == "uc":
                ucskip = int(arg) if arg else 1
            elif word == "u" and arg:
                code = int(arg)
                if code < 0:
                    code += 65536
                try:
                    out.append(chr(code))
                except ValueError:
                    pass
                skip = ucskip
        elif hexbyte:
            if skip > 0:
                skip -= 1
            elif not ignorable:
                out.append(bytes([int(hexbyte, 16)]).decode("cp1252", "replace"))
        elif char:
            if skip > 0:
                skip -= 1
            elif not ignorable:
                out.append(char)

    return tidy("".join(out))
