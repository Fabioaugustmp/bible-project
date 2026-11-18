"""Leitura diária (T82): planos por capítulo, marcação de lido e notas de hoje."""
import sqlite3
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import reading  # noqa: E402
import userdata  # noqa: E402


def make_db():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(userdata.SCHEMA)
    return con


class Chapters(unittest.TestCase):
    def test_mesmo_livro(self):
        self.assertEqual(reading.chapters_between(43, 1, 43, 3), [(43, 1), (43, 2), (43, 3)])

    def test_atravessa_livros(self):
        got = reading.chapters_between(40, 27, 41, 2)   # Mt 27 até Mc 2
        self.assertEqual(got, [(40, 27), (40, 28), (41, 1), (41, 2)])

    def test_intervalo_invertido_e_capitulo_inexistente(self):
        with self.assertRaises(ValueError):
            reading.chapters_between(43, 3, 43, 1)
        with self.assertRaises(ValueError):
            reading.chapters_between(43, 99, 43, 99)

    def test_plano_grande_demais(self):
        with self.assertRaises(ValueError):
            reading.chapters_between(1, 1, 66, 22)   # a Bíblia toda, maior que o limite


class Plans(unittest.TestCase):
    def setUp(self):
        self.con = make_db()

    def tearDown(self):
        self.con.close()

    def test_criar_listar_marcar_e_apagar(self):
        made = reading.create_plan(self.con, {"book": 43, "chapter": 1, "to_chapter": 3})
        self.assertEqual(made["days"], 3)
        with mock.patch.object(reading, "today", return_value="2026-11-18"):
            data = reading.list_plans(self.con)
            plan = data["plans"][0]
            self.assertEqual((plan["total"], plan["done"]), (3, 0))
            self.assertEqual((plan["next"]["book"], plan["next"]["chapter"]), (43, 1))
            self.assertFalse(plan["read_today"])

            first = plan["next"]["id"]
            reading.mark_day(self.con, {"id": first, "done": True})
            plan = reading.list_plans(self.con)["plans"][0]
            self.assertEqual((plan["done"], plan["next"]["chapter"]), (1, 2))
            self.assertTrue(plan["read_today"])

            reading.mark_day(self.con, {"id": first, "done": False})
            self.assertEqual(reading.list_plans(self.con)["plans"][0]["done"], 0)

        reading.delete_plan(self.con, {"id": made["id"]})
        self.assertEqual(reading.list_plans(self.con)["plans"], [])

    def test_notas_de_hoje(self):
        self.con.execute("insert into anchors(book, chapter, verse) values (43, 3, 16)")
        self.con.execute("insert into notes(anchor_id, body, created_at, updated_at) values (1, 'x', '2026-11-18T09:00:00', '2026-11-18T09:00:00')")
        self.con.execute("insert into notes(anchor_id, body, created_at, updated_at) values (1, 'y', '2026-11-17T09:00:00', '2026-11-17T09:00:00')")
        with mock.patch.object(reading, "today", return_value="2026-11-18"):
            self.assertEqual(reading.list_plans(self.con)["notes_today"], 1)

    def test_capitulo_inexistente_no_plano(self):
        with self.assertRaises(ValueError):
            reading.mark_day(self.con, {"id": 999, "done": True})


if __name__ == "__main__":
    unittest.main()
