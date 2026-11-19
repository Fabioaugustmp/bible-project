"""Diário de estudo (T89, D029): entradas com data, sem passagem; criar, listar, editar e apagar."""
import sqlite3
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import userdata  # noqa: E402


def make_db():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(userdata.SCHEMA)
    return con


class Journal(unittest.TestCase):
    def setUp(self):
        self.con = make_db()

    def tearDown(self):
        self.con.close()

    def test_criar_e_listar_mais_recente_primeiro(self):
        with mock.patch.object(userdata, "now", return_value="2026-11-18T09:00:00"):
            userdata.create_journal(self.con, {"body": "Primeira reflexão"})
        with mock.patch.object(userdata, "now", return_value="2026-11-19T09:00:00"):
            userdata.create_journal(self.con, {"body": "  Segunda reflexão  "})
        entries = userdata.list_journal(self.con, {})["entries"]
        self.assertEqual([e["body"] for e in entries], ["Segunda reflexão", "Primeira reflexão"])

    def test_busca_pelo_texto(self):
        userdata.create_journal(self.con, {"body": "oração pela família"})
        userdata.create_journal(self.con, {"body": "louvor"})
        self.assertEqual(len(userdata.list_journal(self.con, {"q": "oração"})["entries"]), 1)

    def test_corpo_vazio_e_recusado(self):
        with self.assertRaises(ValueError):
            userdata.create_journal(self.con, {"body": "   "})

    def test_editar_atualiza_o_texto(self):
        made = userdata.create_journal(self.con, {"body": "rascunho"})
        self.assertTrue(userdata.update_journal(self.con, {"id": made["id"], "body": "texto final"})["ok"])
        self.assertEqual(userdata.list_journal(self.con, {})["entries"][0]["body"], "texto final")

    def test_apagar_vai_para_a_lixeira(self):
        made = userdata.create_journal(self.con, {"body": "apagar"})
        self.assertTrue(userdata.delete_journal(self.con, {"id": made["id"]})["ok"])
        self.assertEqual(userdata.list_journal(self.con, {})["entries"], [])
        self.assertFalse(userdata.delete_journal(self.con, {"id": made["id"]})["ok"])
        self.assertFalse(userdata.update_journal(self.con, {"id": made["id"], "body": "x"})["ok"])


if __name__ == "__main__":
    unittest.main()
