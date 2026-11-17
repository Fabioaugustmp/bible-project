"""Testes de importer/rvf.py: formato RichView (RVF) usado por parte dos .twm.

Os registros são montados à mão, com os bytes que o formato descreve: linha
ASCII de inteiros terminada em CRLF e textos em UTF-16LE terminados por U+2029.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "importer"))

from rvf import is_rvf, rvf_to_text  # noqa: E402

FIRST_LINE = b"-8 1 3\r\n"  # versão do formato


def header(style, count, paragraph, tag="0"):
    return f"{style} {count} {paragraph} 0 0 {tag}\r\n".encode("ascii")


def utf16_string(text):
    return text.encode("utf-16-le") + b"\x29\x20"


class RvfTest(unittest.TestCase):
    def test_reconhece_cabecalho(self):
        self.assertTrue(is_rvf(FIRST_LINE))
        self.assertFalse(is_rvf(b"<html>"))

    def test_texto_simples_em_dois_paragrafos(self):
        data = (FIRST_LINE + header(0, 1, 0) + utf16_string("Olá")
                + header(0, 1, 0) + utf16_string("mundo"))
        text, resyncs = rvf_to_text(data)
        self.assertEqual(text, "Olá\nmundo")
        self.assertEqual(resyncs, 0)

    def test_paragrafo_menos_um_continua_o_anterior(self):
        data = (FIRST_LINE + header(0, 1, 0) + utf16_string("Olá")
                + header(0, 1, -1) + utf16_string("mundo"))
        text, resyncs = rvf_to_text(data)
        self.assertEqual(text, "Olámundo")
        self.assertEqual(resyncs, 0)

    def test_item_com_duas_strings_separa_por_quebra(self):
        data = FIRST_LINE + header(0, 2, 0) + utf16_string("a") + utf16_string("b")
        text, resyncs = rvf_to_text(data)
        self.assertEqual(text, "a\nb")
        self.assertEqual(resyncs, 0)

    def test_bloco_de_estilos_e_pulado_pelo_tamanho(self):
        block = b"\x01\x02\x03\x04"  # 4 bytes; o leitor deve pular exatamente este bloco
        data = (FIRST_LINE + header(-9, 2, -1) + b"Estilos\r\n"
                + len(block).to_bytes(4, "little") + block
                + header(0, 1, 0) + utf16_string("Depois"))
        text, resyncs = rvf_to_text(data)
        self.assertEqual(text, "Depois")
        self.assertEqual(resyncs, 0)

    def test_estilo_negativo_desconhecido_ressincroniza_sem_perder_o_texto(self):
        data = (FIRST_LINE + header(-3, 1, 0, "img") + b"lixo\r\n"
                + header(0, 1, -1) + utf16_string("Texto"))
        text, resyncs = rvf_to_text(data)
        self.assertGreater(resyncs, 0)
        self.assertEqual(text, "Texto")


if __name__ == "__main__":
    unittest.main()
