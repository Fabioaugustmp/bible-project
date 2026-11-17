"""Testes das funções de limpeza dos leitores: esword, theword e db.

Cobrem os defeitos corrigidos nas tarefas T01 (títulos de seção), T04 (metadados)
e T05 (interlineares sem texto grego no reverso).
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "importer"))

import db  # noqa: E402
import esword  # noqa: E402
import theword  # noqa: E402


class EswordHeadingTest(unittest.TestCase):
    def test_titulo_de_secao_e_separado_do_texto(self):
        heading, body = esword._split_heading(r"{\b\qc O começo}\par\par No princípio Deus criou.")
        self.assertEqual(heading, "O começo")
        self.assertNotIn("O começo", body)
        self.assertIn("No princípio Deus criou.", body)

    def test_titulo_de_salmo_fica_no_texto(self):
        heading, body = esword._split_heading(r"{\i\qc Salmo de Davi}\par Pastor meu é o Senhor.")
        self.assertIsNone(heading)
        self.assertIn("Salmo de Davi", body)

    def test_versiculo_sem_titulo(self):
        self.assertEqual(esword._split_heading("Texto simples."), (None, "Texto simples."))


class TheWordCleanVerseTest(unittest.TestCase):
    def test_nota_variante_e_titulo_saem_do_texto(self):
        line = "<TS>O começo<Ts>No princípio <RF 1.1.1>nota de rodapé<Rf>Deus criou<VX1>"
        heading, text, tagged, words = theword._clean_verse(line)
        self.assertEqual(heading, "O começo")
        self.assertEqual(text, "No princípio Deus criou")
        self.assertIsNone(tagged)
        self.assertEqual(words, [])

    def test_interlinear_reverso_nao_tem_grego_no_texto(self):
        # <E> vem primeiro: o texto principal é o inglês, sem caracteres gregos.
        line = ("<wt><E>For<e><OG>γὰρ<og><T>gar<t><WG1063>"
                "<wt><E>God<e><OG>Θεὸς<og><T>theos<t><WG2316>")
        heading, text, tagged, words = theword._clean_verse(line)
        self.assertIsNone(heading)
        self.assertEqual(text, "For God")
        self.assertFalse(any("Ͱ" <= ch <= "Ͽ" or "ἀ" <= ch <= "῿" for ch in text))
        self.assertEqual(tagged, "For{G1063} God{G2316}")
        self.assertEqual(len(words), 2)

    def test_verse_index_decodifica_gn_1_1(self):
        self.assertEqual(theword._verse_index(16843008), (1, 1, 1, 0))

    def test_short_title_limita_o_tamanho(self):
        # Descrições do theWord trazem licença; o título fica curto (T04).
        title = theword._short_title("Bíblia de teste. Copyright 2000 " + "x" * 200)
        self.assertLessEqual(len(title), 90)
        self.assertEqual(theword._short_title("Bíblia Sagrada. Copyright 2000"), "Bíblia Sagrada")


class DbHelpersTest(unittest.TestCase):
    def test_strip_controls_remove_controles_e_mantem_quebras(self):
        self.assertEqual(db.strip_controls("A\x01B\x0bC\x0cD\x0eE\x1fF\nG\tH\r"), "ABCDEF\nG\tH\r")

    def test_normalize_lang_normaliza_codigos_da_origem(self):
        self.assertEqual(db.normalize_lang("Eng - English"), "eng")
        self.assertEqual(db.normalize_lang("eng"), "eng")
        self.assertEqual(db.normalize_lang("English"), "eng")
        self.assertEqual(db.normalize_lang("grk"), "grc")
        self.assertEqual(db.normalize_lang("heb"), "heb")
        self.assertEqual(db.normalize_lang(None), "und")


if __name__ == "__main__":
    unittest.main()
