"""Extração de texto do formato RVF (RichView), usado por parte dos .twm.

Um documento RVF é uma sequência de registros. Cada registro começa com uma
linha ASCII de inteiros terminada em CRLF:

    <estilo> <n_strings> <parágrafo> <...> <tag>

- estilo >= 0: item de texto; seguem n_strings textos em UTF-16LE, cada um
  terminado por U+2029. parágrafo = -1 continua o parágrafo anterior.
- estilo -9 com n_strings = 2: bloco de estilos; segue uma linha com o nome e
  um bloco binário precedido do tamanho em 4 bytes.
- demais estilos negativos (imagens, tabelas, marcadores): estrutura não
  tratada; o leitor procura o próximo cabeçalho de registro e segue.

Devolve o texto e quantas vezes foi preciso ressincronizar (0 = leitura limpa).
"""
import re

from refs import CLOSE, MID, OPEN, strip_marks
from rtf import tidy

_HEADER = re.compile(rb"(-?\d{1,4}) (\d{1,5}) (-?\d{1,5}) (\d{1,4}) (\d{1,4}) ([^\r\n]{0,600})\r\n")
_NEXT_HEADER = re.compile(rb"(?:\r\n|\x29\x20)(?=-?\d{1,4} \d{1,5} -?\d{1,5} \d{1,4} \d{1,4} [^\r\n]{0,600}\r\n)")
_SEPARATOR = b"\x29\x20"  # U+2029 em UTF-16LE


def is_rvf(data: bytes) -> bool:
    return data.startswith(b"-8 ")


def _read_string(data: bytes, pos: int):
    """Lê um texto UTF-16LE terminado por U+2029 a partir de pos."""
    end = pos
    while True:
        end = data.find(_SEPARATOR, end)
        if end < 0:
            return None, pos
        if (end - pos) % 2 == 0:
            return data[pos:end].decode("utf-16-le", "replace"), end + 2
        end += 1


_LINK = re.compile(rb'"(tw://[^"]{1,200})"')
_DIGIT = re.compile(r"\d")


def rvf_to_text(data: bytes):
    """RVF -> (texto limpo, ressincronizações). Links viram só o texto visível."""
    marked, resyncs = rvf_to_marked(data)
    return strip_marks(marked), resyncs


def rvf_to_marked(data: bytes):
    """Como rvf_to_text, mas com o texto de cada item com link entre as marcas de importer/refs.py.
    O alvo vem no fim da linha de cabeçalho do item: `6 1 -1 9 0 "tw://bible.*?id=9.6.18|..."`."""
    out, resyncs, size = [], 0, len(data)
    pos = data.find(b"\r\n") + 2  # primeira linha: versão do formato ("-8 1 3")

    def resync(start):
        found = _NEXT_HEADER.search(data, start)
        return found.end() if found else size

    while pos < size:
        header = _HEADER.match(data, pos)
        if not header:
            resyncs += 1
            pos = resync(pos)
            continue
        style, count, paragraph = int(header.group(1)), int(header.group(2)), int(header.group(3))
        pos = header.end()

        if style >= 0:
            if paragraph != -1:
                out.append("\n")
            link = _LINK.search(header.group(6))
            texts = []
            for index in range(count):
                text, after = _read_string(data, pos)
                if text is None:
                    resyncs += 1
                    pos = resync(pos)
                    break
                texts.append(text)
                pos = after
            joined = "\n".join(texts)
            # O alvo também aparece no cabeçalho de itens vizinhos que não são o link;
            # só o texto curto com número é a própria referência ("1 Sam. 6:18").
            if link and len(joined.strip()) <= 40 and _DIGIT.search(joined):
                out.append(OPEN + link.group(1).decode("latin-1") + MID + joined + CLOSE)
            else:
                out.append(joined)
        elif style == -9 and count == 2:
            name_end = data.find(b"\r\n", pos)
            if name_end < 0 or name_end + 6 > size:
                break
            length = int.from_bytes(data[name_end + 2:name_end + 6], "little")
            pos = name_end + 6 + length
        elif count == 0:
            if style == -12:  # tabulação
                out.append("\t")
        else:
            resyncs += 1
            pos = resync(pos)

    return tidy("".join(out)), resyncs
