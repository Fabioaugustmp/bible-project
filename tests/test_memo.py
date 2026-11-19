"""Memorização com SM-2 (T80, D031): o algoritmo, os cartões e as revisões."""
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


class Sm2(unittest.TestCase):
    def test_sequencia_de_acertos(self):
        ease, interval, reps = 2.5, 0, 0
        steps = []
        for _ in range(3):
            ease, interval, reps = userdata.sm2(ease, interval, reps, 4)
            steps.append(interval)
        self.assertEqual(steps, [1, 6, 15])          # 1, 6 e depois intervalo x facilidade
        self.assertAlmostEqual(ease, 2.5)            # resposta "bom" mantém a facilidade

    def test_erro_volta_ao_comeco_e_reduz_a_facilidade(self):
        ease, interval, reps = userdata.sm2(2.5, 15, 3, 0)
        self.assertEqual((interval, reps), (1, 0))
        self.assertAlmostEqual(ease, 1.7)

    def test_facilidade_nunca_abaixo_de_1_3(self):
        ease, interval, reps = 2.5, 0, 0
        for _ in range(20):
            ease, interval, reps = userdata.sm2(ease, interval, reps, 0)
        self.assertEqual(ease, 1.3)


class Cards(unittest.TestCase):
    def setUp(self):
        self.con = make_db()

    def tearDown(self):
        self.con.close()

    def test_adicionar_revisar_e_listar_por_data(self):
        with mock.patch.object(reading, "today", return_value="2026-11-19"):
            card = userdata.add_memo(self.con, {"book": 50, "chapter": 4, "verse": 7})["id"]
            self.assertEqual(userdata.list_memo(self.con, {})["due"][0]["id"], card)
            res = userdata.review_memo(self.con, {"id": card, "grade": "bom"})
            self.assertEqual((res["interval"], res["due"]), (1, "2026-11-20"))
            self.assertEqual(userdata.list_memo(self.con, {})["due"], [])     # não vence hoje
        with mock.patch.object(reading, "today", return_value="2026-11-20"):
            self.assertEqual(len(userdata.list_memo(self.con, {})["due"]), 1)

    def test_validacoes(self):
        userdata.add_memo(self.con, {"book": 50, "chapter": 4, "verse": 7})
        with self.assertRaises(ValueError):
            userdata.add_memo(self.con, {"book": 50, "chapter": 4, "verse": 7})   # repetido
        with self.assertRaises(ValueError):
            userdata.add_memo(self.con, {"book": 50, "chapter": 4, "verse": 99})  # inexistente
        with self.assertRaises(ValueError):
            userdata.review_memo(self.con, {"id": 1, "grade": "talvez"})          # resposta inválida

    def test_apagar_tira_da_lista(self):
        card = userdata.add_memo(self.con, {"book": 43, "chapter": 3, "verse": 16})["id"]
        self.assertTrue(userdata.delete_memo(self.con, {"id": card})["ok"])
        self.assertEqual(userdata.list_memo(self.con, {})["cards"], [])


if __name__ == "__main__":
    unittest.main()
