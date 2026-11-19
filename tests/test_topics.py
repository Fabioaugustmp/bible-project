"""Notas por tópico (T87, D030): um assunto reúne notas de várias passagens, ou nenhuma."""
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


class Topics(unittest.TestCase):
    def setUp(self):
        self.con = make_db()

    def tearDown(self):
        self.con.close()

    def test_criar_tópico_e_nome_repetido_sem_diferenca_de_caixa(self):
        userdata.create_topic(self.con, {"name": "Ansiedade"})
        with self.assertRaises(ValueError):
            userdata.create_topic(self.con, {"name": "  ansiedade "})
        with self.assertRaises(ValueError):
            userdata.create_topic(self.con, {"name": "   "})
        topics = userdata.list_topics(self.con, {})["topics"]
        self.assertEqual([(t["name"], t["notes"]) for t in topics], [("Ansiedade", 0)])

    def test_notas_com_e_sem_passagem_no_mesmo_tópico(self):
        topic = userdata.create_topic(self.con, {"name": "Paz"})["id"]
        userdata.add_topic_note(self.con, {"topic_id": topic, "body": "Ideia geral", "book": None})
        userdata.add_topic_note(self.con, {"topic_id": topic, "body": "Filipenses", "book": 50, "chapter": 4, "verse": 7})
        userdata.add_topic_note(self.con, {"topic_id": topic, "body": "João", "book": 43, "chapter": 14, "verse": 27})
        got = userdata.get_topic(self.con, {"id": topic})
        self.assertEqual(got["name"], "Paz")
        # com passagem primeiro, ordenadas pela Bíblia; a sem passagem por último
        self.assertEqual([n["body"] for n in got["notes"]], ["João", "Filipenses", "Ideia geral"])
        self.assertEqual(userdata.list_topics(self.con, {})["topics"][0]["notes"], 3)

    def test_passagem_inexistente_é_recusada(self):
        topic = userdata.create_topic(self.con, {"name": "Teste"})["id"]
        with self.assertRaises(ValueError):
            userdata.add_topic_note(self.con, {"topic_id": topic, "body": "x", "book": 43, "chapter": 3, "verse": 99})
        with self.assertRaises(ValueError):
            userdata.add_topic_note(self.con, {"topic_id": topic, "body": "x", "book": 67, "chapter": 1, "verse": 1})

    def test_editar_e_apagar_nota(self):
        topic = userdata.create_topic(self.con, {"name": "Oração"})["id"]
        note = userdata.add_topic_note(self.con, {"topic_id": topic, "body": "rascunho"})["id"]
        self.assertTrue(userdata.update_topic_note(self.con, {"id": note, "body": "final"})["ok"])
        self.assertEqual(userdata.get_topic(self.con, {"id": topic})["notes"][0]["body"], "final")
        self.assertTrue(userdata.delete_topic_note(self.con, {"id": note})["ok"])
        self.assertEqual(userdata.get_topic(self.con, {"id": topic})["notes"], [])

    def test_apagar_tópico_esconde_o_tópico_e_suas_notas(self):
        topic = userdata.create_topic(self.con, {"name": "Lixo"})["id"]
        userdata.add_topic_note(self.con, {"topic_id": topic, "body": "x"})
        userdata.delete_topic(self.con, {"id": topic})
        self.assertEqual(userdata.list_topics(self.con, {})["topics"], [])
        with self.assertRaises(ValueError):
            userdata.get_topic(self.con, {"id": topic})
        with self.assertRaises(ValueError):
            userdata.add_topic_note(self.con, {"topic_id": topic, "body": "depois"})
        # o nome liberado pode voltar a ser usado
        userdata.create_topic(self.con, {"name": "Lixo"})


if __name__ == "__main__":
    unittest.main()
