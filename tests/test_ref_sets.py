"""Conjuntos de referências (T98, D032): passagens escolhidas e ordenadas pelo usuário."""
import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import userdata  # noqa: E402


def make_db():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(userdata.SCHEMA)
    return con


class RefSets(unittest.TestCase):
    def setUp(self):
        self.con = make_db()

    def tearDown(self):
        self.con.close()

    def order(self, set_id):
        return [(i["book"], i["chapter"], i["verse"]) for i in userdata.get_ref_set(self.con, {"id": set_id})["items"]]

    def test_ordem_de_entrada_e_mover(self):
        s = userdata.create_ref_set(self.con, {"name": "Graça"})["id"]
        a = userdata.add_ref_item(self.con, {"set_id": s, "book": 49, "chapter": 2, "verse": 8})["id"]
        userdata.add_ref_item(self.con, {"set_id": s, "book": 43, "chapter": 1, "verse": 14})
        userdata.add_ref_item(self.con, {"set_id": s, "book": 56, "chapter": 3, "verse": 5, "span": 2})
        self.assertEqual(self.order(s), [(49, 2, 8), (43, 1, 14), (56, 3, 5)])
        userdata.move_ref_item(self.con, {"id": a, "delta": 1})          # desce Ef 2:8
        self.assertEqual(self.order(s), [(43, 1, 14), (49, 2, 8), (56, 3, 5)])
        userdata.move_ref_item(self.con, {"id": a, "delta": -1})         # sobe de volta
        self.assertEqual(self.order(s)[0], (49, 2, 8))
        first = userdata.get_ref_set(self.con, {"id": s})["items"][0]["id"]
        self.assertFalse(userdata.move_ref_item(self.con, {"id": first, "delta": -1})["ok"])   # já é o primeiro

    def test_intervalo_e_remocao(self):
        s = userdata.create_ref_set(self.con, {"name": "Teste"})["id"]
        item = userdata.add_ref_item(self.con, {"set_id": s, "book": 56, "chapter": 3, "verse": 5, "span": 2})["id"]
        self.assertEqual(userdata.get_ref_set(self.con, {"id": s})["items"][0]["span"], 2)
        self.assertTrue(userdata.remove_ref_item(self.con, {"id": item})["ok"])
        self.assertEqual(self.order(s), [])

    def test_validacoes_e_apagar_conjunto(self):
        s = userdata.create_ref_set(self.con, {"name": "Lixo"})["id"]
        with self.assertRaises(ValueError):
            userdata.create_ref_set(self.con, {"name": "   "})
        with self.assertRaises(ValueError):
            userdata.add_ref_item(self.con, {"set_id": s, "book": 43, "chapter": 3, "verse": 99})
        userdata.delete_ref_set(self.con, {"id": s})
        self.assertEqual(userdata.list_ref_sets(self.con, {})["sets"], [])
        with self.assertRaises(ValueError):
            userdata.get_ref_set(self.con, {"id": s})


if __name__ == "__main__":
    unittest.main()
