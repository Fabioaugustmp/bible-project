"""Backlinks de notas (T81): notas de outros versículos que citam o versículo aberto."""
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

import backlinks  # noqa: E402


def make_db():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript("""
        create table anchors(id integer primary key, book integer, chapter integer, verse integer);
        create table notes(id integer primary key, anchor_id integer, body text,
                           created_at text, updated_at text, deleted_at text);
    """)
    return con


def add_note(con, note_id, book, chapter, verse, body, deleted=False):
    cur = con.execute("insert or ignore into anchors(book, chapter, verse) values (?, ?, ?)", (book, chapter, verse))
    anchor = con.execute("select id from anchors where book=? and chapter=? and verse=?", (book, chapter, verse)).fetchone()[0]
    con.execute("insert into notes(id, anchor_id, body, created_at, updated_at, deleted_at) values (?,?,?,?,?,?)",
                (note_id, anchor, body, f"2026-11-18T10:0{note_id}:00", f"2026-11-18T10:0{note_id}:00",
                 "2026-11-18T11:00:00" if deleted else None))


class Backlinks(unittest.TestCase):
    def setUp(self):
        self.con = make_db()

    def tearDown(self):
        self.con.close()

    def test_nota_em_outro_versiculo_que_cita_aparece(self):
        add_note(self.con, 1, 1, 1, 1, "Em Gn 1:1 se vê a criação; compare com Jo 1:1.")
        add_note(self.con, 2, 40, 5, 3, "Ver João 3:16 para o amor de Deus.")
        found = backlinks.find(self.con, 43, 3, 16)
        self.assertEqual([n["id"] for n in found], [2])
        self.assertEqual(found[0]["book"], 40)

    def test_intervalo_cobre_o_versiculo(self):
        add_note(self.con, 3, 40, 5, 1, "Leia Jo 3:16-18 com calma.")
        self.assertEqual([n["id"] for n in backlinks.find(self.con, 43, 3, 17)], [3])
        self.assertEqual(backlinks.find(self.con, 43, 3, 19), [])

    def test_nota_do_proprio_versiculo_nao_entra(self):
        add_note(self.con, 4, 43, 3, 16, "Eu mesmo escrevi sobre João 3:16.")
        self.assertEqual(backlinks.find(self.con, 43, 3, 16), [])

    def test_nota_apagada_nao_entra(self):
        add_note(self.con, 5, 40, 5, 3, "Veja João 3:16.", deleted=True)
        self.assertEqual(backlinks.find(self.con, 43, 3, 16), [])

    def test_trecho_longo_vira_resumo(self):
        add_note(self.con, 6, 40, 5, 3, "Jo 3:16 " + "palavra " * 60)
        found = backlinks.find(self.con, 43, 3, 16)
        self.assertLessEqual(len(found[0]["excerpt"]), backlinks.EXCERPT + 1)
        self.assertTrue(found[0]["excerpt"].endswith("…"))


if __name__ == "__main__":
    unittest.main()
