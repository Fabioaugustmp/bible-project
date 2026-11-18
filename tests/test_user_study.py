"""Leitura de estudos sem id deve dar erro de validação (400), não KeyError (T97 / correção do GET sem id)."""
import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import userdata  # noqa: E402


class GetStudyWithoutId(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.con.row_factory = sqlite3.Row

    def tearDown(self):
        self.con.close()

    def test_sem_id_levanta_valueerror(self):
        with self.assertRaisesRegex(ValueError, "obrigatório"):
            userdata.get_study(self.con, {})

    def test_id_invalido_levanta_valueerror(self):
        with self.assertRaises(ValueError):
            userdata.get_study(self.con, {"id": "abc"})


if __name__ == "__main__":
    unittest.main()
