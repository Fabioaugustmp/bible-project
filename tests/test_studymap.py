"""Mapa de estudo e linha do tempo (T93, D033)."""
import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import studymap  # noqa: E402
import userdata  # noqa: E402


def make_db():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(userdata.SCHEMA)
    return con


class Map(unittest.TestCase):
    def setUp(self):
        self.con = make_db()
        c = self.con
        c.execute("insert into anchors(id, book, chapter, verse) values (1, 43, 3, 16), (2, 50, 4, 7)")
        c.execute("insert into notes(anchor_id, body, created_at, updated_at) values (1, 'a', '2026-11-01T09:00', '2026-11-01T09:00')")
        c.execute("insert into notes(anchor_id, body, created_at, updated_at) values (1, 'b', '2026-11-02T09:00', '2026-11-02T09:00')")
        c.execute("insert into topics(id, name, created_at, updated_at) values (1, 'Amor', '2026-11-01', '2026-11-01')")
        c.execute("insert into topic_notes(topic_id, anchor_id, body, created_at, updated_at)"
                  " values (1, 1, 'x', '2026-11-03T08:00', '2026-11-03T08:00')")
        c.execute("insert into topics(id, name, created_at, updated_at) values (2, 'Sem passagem', '2026-11-01', '2026-11-01')")
        c.execute("insert into studies(id, title, created_at, updated_at) values (1, 'Estudo de João', '2026-11-04', '2026-11-04')")
        c.execute("insert into study_blocks(study_id, pos, kind, anchor_id) values (1, 1, 'passagem', 1)")
        c.execute("insert into study_blocks(study_id, pos, kind, anchor_id) values (1, 2, 'passagem', 2)")
        c.commit()

    def tearDown(self):
        self.con.close()

    def test_mapa_liga_passagens_a_topicos_e_estudos(self):
        m = studymap.map_data(self.con)
        ids = {n["id"] for n in m["nodes"]}
        self.assertIn("p43-3-16", ids)
        self.assertIn("t1", ids)
        self.assertIn("t2", ids)            # tópico sem passagem continua na lista
        self.assertIn("s1", ids)
        passage = next(n for n in m["nodes"] if n["id"] == "p43-3-16")
        self.assertEqual(passage["weight"], 2 + 1 + 1)   # duas notas, uma nota de tópico, um bloco de estudo
        pairs = {(e["from"], e["to"]) for e in m["edges"]}
        self.assertIn(("t1", "p43-3-16"), pairs)
        self.assertIn(("s1", "p43-3-16"), pairs)
        self.assertIn(("s1", "p50-4-7"), pairs)

    def test_notas_apagadas_saem_do_mapa(self):
        self.con.execute("update notes set deleted_at = '2026-11-05' where id = 1")
        self.con.execute("update notes set deleted_at = '2026-11-05' where id = 2")
        self.con.commit()
        passage = next(n for n in studymap.map_data(self.con)["nodes"] if n["id"] == "p43-3-16")
        self.assertEqual(passage["weight"], 2)


class Timeline(unittest.TestCase):
    def setUp(self):
        self.con = make_db()

    def tearDown(self):
        self.con.close()

    def test_eventos_do_mais_recente_ao_mais_antigo(self):
        self.con.execute("insert into anchors(id, book, chapter, verse) values (1, 43, 3, 16)")
        self.con.execute("insert into notes(anchor_id, body, created_at, updated_at) values (1, 'nota', '2026-11-01T09:00', '2026-11-01T09:00')")
        self.con.execute("insert into journal(body, created_at, updated_at) values ('diário', '2026-11-03T10:00', '2026-11-03T10:00')")
        self.con.execute("insert into reading_plans(id, title, created_at) values (1, 'Plano', '2026-11-01')")
        self.con.execute("insert into reading_days(plan_id, pos, book, chapter, done_on) values (1, 1, 43, 1, '2026-11-02')")
        self.con.commit()
        events = studymap.timeline(self.con)["events"]
        self.assertEqual([e["kind"] for e in events], ["journal", "reading", "notes"])
        self.assertEqual(events[2]["book"], 43)

    def test_leitura_de_plano_apagado_nao_aparece(self):
        self.con.execute("insert into reading_plans(id, title, created_at, deleted_at) values (1, 'Plano', '2026-11-01', '2026-11-05')")
        self.con.execute("insert into reading_days(plan_id, pos, book, chapter, done_on) values (1, 1, 43, 1, '2026-11-02')")
        self.con.commit()
        self.assertEqual(studymap.timeline(self.con)["events"], [])

    def test_apagados_nao_aparecem(self):
        self.con.execute("insert into journal(body, created_at, updated_at, deleted_at) values ('x', '2026-11-03', '2026-11-03', '2026-11-04')")
        self.con.commit()
        self.assertEqual(studymap.timeline(self.con)["events"], [])


if __name__ == "__main__":
    unittest.main()
