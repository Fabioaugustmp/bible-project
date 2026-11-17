"""Testes dos leitores de módulos com arquivos SQLite criados no próprio teste.

Os .bblx são pequenos, sintéticos e gravados em pasta temporária. O 'add' é um
substituto que só guarda as chamadas, para conferir o que o leitor entregaria
ao importador.
"""
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "importer"))

import esword  # noqa: E402
import theword  # noqa: E402


class FakeAdder:
    def __init__(self):
        self.modules, self.verses_calls, self.tokens_calls, self.logs = [], [], [], []

    def module(self, meta):
        self.modules.append(meta)
        return len(self.modules)

    def verses(self, module_id, rows):
        self.verses_calls.append(rows)

    def tokens(self, module_id, words):
        self.tokens_calls.append(words)

    def log(self, level, message):
        self.logs.append((level, message))


def make_bblx(directory, scriptures):
    """Cria um .bblx com a tabela Details e a tabela Bible do e-Sword."""
    path = Path(directory) / "teste.bblx"
    con = sqlite3.connect(path)
    con.execute("create table Details(Description, Abbreviation)")
    con.execute("insert into Details values (?, ?)", ("Bíblia de teste", "TST"))
    # Colunas sem tipo declarado: o cabeçalho ('Livro', ...) e os blobs ficam como foram gravados.
    con.execute("create table Bible(Book, Chapter, Verse, Scripture)")
    con.executemany("insert into Bible values (?, ?, ?, ?)", scriptures)
    con.commit()
    con.close()
    return path


class EswordReadBibleTest(unittest.TestCase):
    def test_pula_cabecalho_e_grava_titulo_separado(self):
        scriptures = [
            ("Livro", "Cap", "Verso", "TítuloConfigTexto"),  # linha de cabeçalho da tabela
            (1, 1, 1, r"{\b\qc O começo}\par\par No princípio Deus criou os céus e a terra."),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            add = FakeAdder()
            count = esword.read_bible(make_bblx(tmp, scriptures), add)

        self.assertEqual(count, 1)
        self.assertEqual(add.modules[0]["title"], "Bíblia de teste")
        self.assertEqual(len(add.verses_calls), 1)
        self.assertEqual(len(add.verses_calls[0]), 1)  # o cabeçalho não virou versículo
        book, chapter, verse, text, tagged, heading, origin_key = add.verses_calls[0][0]
        self.assertEqual((book, chapter, verse), (1, 1, 1))
        self.assertEqual(heading, "O começo")
        self.assertEqual(text, "No princípio Deus criou os céus e a terra.")
        self.assertFalse(text.startswith("O começo"))
        self.assertIsNone(tagged)
        self.assertEqual(origin_key, "1.1.1")

    def test_texto_cifrado_e_registrado_como_ignorado(self):
        scriptures = [(1, 1, 1, b"\x00\x01\x02\xff\xfe")]  # blob: módulo protegido do e-Sword
        with tempfile.TemporaryDirectory() as tmp:
            add = FakeAdder()
            count = esword.read_bible(make_bblx(tmp, scriptures), add)

        self.assertEqual(count, 0)
        self.assertEqual(add.modules, [])  # nada foi gravado
        self.assertEqual(add.verses_calls, [])
        self.assertEqual(len(add.logs), 1)
        level, message = add.logs[0]
        self.assertEqual(level, "ignorado")
        self.assertIn("cifrado", message)

    def test_byte_de_controle_na_origem_nao_vira_strong(self):
        # T04(c): a Bíblia católica tem lixo binário em alguns versículos; um byte 0x01
        # da origem era confundido com o marcador interno de Strong.
        scriptures = [(1, 1, 1, "No princípio, Deus criou o céu e a terra. e\x01qÙ\x01t")]
        with tempfile.TemporaryDirectory() as tmp:
            add = FakeAdder()
            esword.read_bible(make_bblx(tmp, scriptures), add)

        self.assertEqual(add.modules[0]["has_strongs"], 0)
        self.assertEqual(add.tokens_calls, [])
        text, tagged = add.verses_calls[0][0][3], add.verses_calls[0][0][4]
        self.assertIsNone(tagged)
        self.assertNotIn("\x01", text)


def make_dct_twm(directory, topics):
    """Cria um dicionário .twm do theWord (config, topics, content) com títulos em bytes."""
    path = Path(directory) / "teste.dct.twm"
    con = sqlite3.connect(path)
    con.execute("create table config(name text, value text)")
    con.executemany("insert into config values (?, ?)",
                    [("type", "1"), ("title", "Dicionário de teste"), ("abbrev", "TST"), ("lang", "eng")])
    con.execute("create table topics(id integer primary key, pid integer default 0, subject text,"
                " rel_order, content_type text)")
    con.execute("create table content(topic_id integer primary key, data text, data2 blob)")
    for topic_id, subject, data in topics:
        # cast(... as text): grava como TEXTO com bytes que não são UTF-8, como no módulo real
        con.execute("insert into topics(id, subject) values (?, cast(? as text))", (topic_id, subject))
        con.execute("insert into content(topic_id, data) values (?, ?)", (topic_id, data))
    con.commit()
    con.close()
    return path


class ThewordReadTwmTest(unittest.TestCase):
    def test_titulo_que_nao_e_utf8(self):
        # T03(b): no Webster 1828, 'Vis-à-vis' está gravado em Windows-1252, não em UTF-8,
        # e a leitura como texto quebrava o módulo inteiro.
        topics = [
            (1, "Abase", "To lower or depress."),
            (2, "Vis-à-vis".encode("cp1252"), "A carriage in which two persons sit face to face."),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            add = FakeAdder()
            add.entries_calls = []
            add.entries = lambda module_id, rows, links=None: add.entries_calls.append(rows)
            count = theword.read_twm(make_dct_twm(tmp, topics), add)

        self.assertEqual(count, 2)
        self.assertEqual(add.modules[0]["kind"], "dictionary")
        self.assertEqual([row[0] for row in add.entries_calls[0]], ["Abase", "Vis-à-vis"])


if __name__ == "__main__":
    unittest.main()
