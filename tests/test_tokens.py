"""Testes de importer/tokens.py: palavras, Strong e texto a partir das palavras."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "importer"))

from tokens import (  # noqa: E402
    from_marked, from_wt, normalize_term, split_codes, strip_accents, tagged_of, text_of,
)

# Marcadores usados pelo importador: \x01 abre e \x02 fecha os códigos de uma expressão.
OPEN, CLOSE = "\x01", "\x02"


class FromMarkedTest(unittest.TestCase):
    def test_codigo_de_analise_verbal_vai_para_morph(self):
        # H1254 é o verbete; H8804 é a análise do verbo (acima do limite lexical).
        words = from_marked(f"criou{OPEN}H1254|H8804{CLOSE} Deus")
        self.assertEqual(words[0], ("criou", "H1254", None, "H8804", None, None, None))
        self.assertEqual(words[1][0], "Deus")
        self.assertIsNone(words[1][1])

    def test_codigo_sem_texto_fica_com_expressao_vazia(self):
        self.assertEqual(from_marked(f"{OPEN}H853{CLOSE}"), [("", "H853", None, None, None, None, None)])

    def test_pontuacao_sozinha_junta_a_palavra_anterior(self):
        words = from_marked(f"Deus{OPEN}G2316{CLOSE} .")
        self.assertEqual(len(words), 1)
        self.assertEqual(words[0][0], "Deus.")
        self.assertEqual(words[0][1], "G2316")

    def test_split_codes_separa_lexico_de_analise(self):
        self.assertEqual(split_codes(["G25", "G5656", "H8804", "H7225"]),
                         (["G25", "H7225"], ["G5656", "H8804"]))


class FromWtTest(unittest.TestCase):
    def test_interlinear_reverso_tem_ingles_na_frente(self):
        # <E> vem primeiro: a expressão é o inglês; original e transliteração ficam preenchidos.
        words = from_wt("<wt><E>For<e><OG>γὰρ<og><T>gar<t><WG1063>")
        self.assertEqual(words, [("For", "G1063", None, None, "γὰρ", "gar", None)])

    def test_interlinear_grego_tem_original_na_frente(self):
        # <O> vem primeiro: a expressão é o grego e a glosa inglesa fica em gloss.
        words = from_wt("<wt><O>λόγος<o><E>word<e><WG3056>")
        self.assertEqual(words, [("λόγος", "G3056", None, None, None, None, "word")])

    def test_tr_traz_lema_e_morfologia(self):
        words = from_wt('<wt><WG3056><WTN-NSM l="λόγος"><E>palavra<e>')
        self.assertEqual(words, [("palavra", "G3056", "λόγος", "N-NSM", None, None, None)])


class TextTest(unittest.TestCase):
    def test_text_of_sem_espaco_antes_da_pontuacao(self):
        words = [("Deus", None, None, None, None, None, None),
                 ("disse", None, None, None, None, None, None),
                 (",", None, None, None, None, None, None),
                 ("“", None, None, None, None, None, None),
                 ("luz", None, None, None, None, None, None),
                 ("”", None, None, None, None, None, None),
                 (".", None, None, None, None, None, None)]
        self.assertEqual(text_of(words), "Deus disse, “luz”.")

    def test_text_of_ignora_palavra_vazia(self):
        words = [("", "H853", None, None, None, None, None),
                 ("Deus", None, None, None, None, None, None)]
        self.assertEqual(text_of(words), "Deus")

    def test_tagged_of_com_codigos(self):
        words = [("No", "H7225", None, None, None, None, None),
                 ("princípio", None, None, None, None, None, None)]
        self.assertEqual(tagged_of(words), "No{H7225} princípio")

    def test_tagged_of_sem_codigos_devolve_none(self):
        self.assertIsNone(tagged_of([("Deus", None, None, None, None, None, None)]))

    def test_normalize_term_tira_artigo_e_pontuacao(self):
        self.assertEqual(normalize_term("No princípio,", "por"), "princípio")

    def test_normalize_term_sem_palavra_devolve_none(self):
        self.assertIsNone(normalize_term("...", "por"))

    def test_strip_accents_une_grafias_do_grego(self):
        self.assertEqual(strip_accents("χάρις"), "χαρις")
        self.assertEqual(strip_accents("χάρις"), strip_accents("χαρις"))


if __name__ == "__main__":
    unittest.main()
