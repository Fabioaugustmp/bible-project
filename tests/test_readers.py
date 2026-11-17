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


if __name__ == "__main__":
    unittest.main()
