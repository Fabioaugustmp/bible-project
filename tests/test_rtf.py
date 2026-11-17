"""Testes de importer/rtf.py: conversão de RTF para texto e normalização (tidy)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "importer"))

from rtf import rtf_to_text, tidy  # noqa: E402


class RtfTest(unittest.TestCase):
    def test_unicode_com_caractere_de_reserva_pulado(self):
        # \u231 = ç e \u227 = ã; o '?' seguinte é o caractere de reserva e some.
        self.assertEqual(rtf_to_text(r"a\u231?\u227?o"), "ação")

    def test_byte_hexadecimal_cp1252(self):
        self.assertEqual(rtf_to_text(r"a\'e7o"), "aço")

    def test_tabelas_e_destinos_nao_aparecem(self):
        source = (r"{\rtf1{\fonttbl{\f0 Times;}}{\colortbl;\red0\green0\blue0;}"
                  r"{\*\generator Word;}Texto visível}")
        self.assertEqual(rtf_to_text(source), "Texto visível")

    def test_par_vira_quebra_de_linha(self):
        self.assertEqual(rtf_to_text(r"{\rtf1\ansi Linha um\par Linha dois}"),
                         "Linha um\nLinha dois")

    def test_hyperlink_mantem_so_o_texto_visivel(self):
        source = (r'{\rtf1 Veja {\field{\*\fldinst{HYPERLINK "tw://bible.*?id=9.7.1"}}'
                  r'{\fldrslt{1 Sam. 7:1}}}.}')
        self.assertEqual(rtf_to_text(source), "Veja 1 Sam. 7:1.")

    def test_texto_sem_rtf_passa_so_por_tidy(self):
        self.assertEqual(rtf_to_text("  a   b\r\n\r\n\r\n\r\nc  "), "a b\n\nc")

    def test_entrada_vazia(self):
        self.assertEqual(rtf_to_text(""), "")

    def test_tidy_colapsa_espacos_e_linhas_em_branco(self):
        self.assertEqual(tidy("  x \t y \n\n\n\n z  "), "x y\n\nz")


if __name__ == "__main__":
    unittest.main()
