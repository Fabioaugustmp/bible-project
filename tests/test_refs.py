"""Testes das citações bíblicas com posição no texto (T24)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "importer"))

import refs  # noqa: E402
import rtf  # noqa: E402
import rvf  # noqa: E402


def shown(text, found):
    """[(trecho do texto, rótulo)] para conferir posição e destino de uma vez."""
    return [(text[start:end], refs.label(*target)) for start, end, *target in found]


class TargetTest(unittest.TestCase):
    def test_versiculo(self):
        self.assertEqual(refs.parse_target("tw://bible.*?id=43.3.16|_AUTODETECT_|"), (43, 3, 16, 3, 16))

    def test_intervalo_no_mesmo_capitulo(self):
        self.assertEqual(refs.parse_target("tw://bible.*?id=2.6.16-20"), (2, 6, 16, 6, 20))

    def test_intervalo_com_livro_capitulo_e_versiculo(self):
        self.assertEqual(refs.parse_target("tw://bible.*?id=51.1.15-51.1.18"), (51, 1, 15, 1, 18))

    def test_link_do_proprio_comentario_para_um_versiculo(self):
        self.assertEqual(refs.parse_target("tw://[self]?1.1.4"), (1, 1, 4, 1, 4))

    def test_alvos_que_nao_sao_versiculo(self):
        for target in ("tw://[strong]?H1322", "tw://*.*?txt=Etymology", "tw://[self]?tid=1675",
                       "tw://bible.*?id=1.51.1"):  # Gênesis só tem 50 capítulos
            self.assertIsNone(refs.parse_target(target), target)

    def test_rotulo_em_portugues(self):
        self.assertEqual(refs.label(45, 3, 21, 4, 2), "Rm 3:21 – 4:2")
        self.assertEqual(refs.label(9, 7, 1, 7, 1), "1Sm 7:1")


class RtfLinksTest(unittest.TestCase):
    SOURCE = (r'{\rtf1 Veja {\field{\*\fldinst HYPERLINK "tw://bible.*?id=9.7.1|_AUTODETECT_|"}'
              r'{\fldrslt \plain \f1\cf2 1 Sam. 7:1}}\plain ; e {\field{\*\fldinst HYPERLINK '
              r'"tw://bible.*?id=2.6.16-20"}{\fldrslt\cf2 [vref]}}; {\field{\*\fldinst HYPERLINK '
              r'"tw://*.*?txt=Etymology"}{\fldrslt Etym.}} fim.}')

    def test_posicao_e_destino_de_cada_link(self):
        text, found = refs.extract(rtf.rtf_to_marked(self.SOURCE))
        self.assertEqual(text, "Veja 1 Sam. 7:1; e Êx 6:16-20; Etym. fim.")
        self.assertEqual(shown(text, found), [("1 Sam. 7:1", "1Sm 7:1"), ("Êx 6:16-20", "Êx 6:16-20")])

    def test_link_so_com_pontuacao_nao_vira_citacao(self):
        source = r'{\rtf1 a{\field{\*\fldinst HYPERLINK "tw://bible.*?id=1.1.1"}{\fldrslt ;}} b}'
        text, found = refs.extract(rtf.rtf_to_marked(source))
        self.assertEqual((text, found), ("a; b", []))

    def test_texto_sem_marcas(self):
        self.assertEqual(rtf.rtf_to_text(self.SOURCE), "Veja 1 Sam. 7:1; e Êx 6:16-20; Etym. fim.")
        for mark in (refs.OPEN, refs.MID, refs.CLOSE):
            self.assertNotIn(mark, rtf.rtf_to_text(self.SOURCE))


def rvf_item(style, text, tail="0"):
    header = f"{style} 1 0 0 0 {tail}\r\n".encode("ascii")
    return header + text.encode("utf-16-le") + b"\x29\x20"


class RvfLinksTest(unittest.TestCase):
    TARGET = '"tw://bible.*?id=9.6.18|_AUTODETECT_|"'

    def test_so_o_texto_curto_com_numero_vira_citacao(self):
        # O alvo aparece também no cabeçalho do item anterior, que não é o link.
        data = (b"-8 1 3\r\n" + rvf_item(2, 'The A.V. has "the Great [stone of] Abel." ', self.TARGET)
                + rvf_item(6, "1 Sam. 6:18", self.TARGET))
        marked, resyncs = rvf.rvf_to_marked(data)
        text, found = refs.extract(marked)
        self.assertEqual(resyncs, 0)
        self.assertEqual(shown(text, found), [("1 Sam. 6:18", "1Sm 6:18")])


class PlainTextTest(unittest.TestCase):
    def test_abreviacao_inglesa_do_esword_vira_rotulo_em_portugues(self):
        text, found = refs.find_plain("(Exo_19:3-6). Veja 1Sa_16:10-11 e Hb_4:12.")
        self.assertEqual(text, "(Êx 19:3-6). Veja 1Sm 16:10-11 e Hb 4:12.")
        self.assertEqual([label for _, label in shown(text, found)], ["Êx 19:3-6", "1Sm 16:10-11", "Hb 4:12"])

    def test_abreviacao_portuguesa_e_continuacao_do_mesmo_livro(self):
        text, found = refs.find_plain("[3] 7.1-2 Sl 10.9; 17.12; 1 Pe 2.3.")
        self.assertEqual(shown(text, found),
                         [("Sl 10.9", "Sl 10:9"), ("17.12", "Sl 17:12"), ("1 Pe 2.3", "1Pe 2:3")])

    def test_numero_antes_do_livro_que_nao_forma_livro(self):
        text, found = refs.find_plain("[3] 46.1-3 Is 54.10.")
        self.assertEqual(shown(text, found), [("Is 54.10", "Is 54:10")])

    def test_intervalo_entre_capitulos_e_grafias_da_traducao_automatica(self):
        text, found = refs.find_plain("em 2 Rseis 9.30-10.28 e Mau 3.17 e Feitos 12.2")
        self.assertEqual([label for _, label in shown(text, found)], ["2Rs 9:30 – 10:28", "Ml 3:17", "At 12:2"])

    def test_palavras_comuns_e_versiculos_inexistentes_nao_sao_citacao(self):
        for text in ("Em 6.11-18, Paulo", "cf. 2 Rss 12.28-30"):  # 2 Reis 12 só tem 21 versículos
            self.assertEqual(refs.find_plain(text)[1], [], text)


if __name__ == "__main__":
    unittest.main()
