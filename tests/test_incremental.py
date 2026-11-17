"""Testes da importação incremental (build.py --incremental, D017).

Os módulos são .bblx sintéticos gravados em pasta temporária (como em
test_readers.py). Cada execução roda importer/build.py em um subprocesso, como
no uso real, e confere a base e o resumo impresso.
"""
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "importer" / "build.py"
TABLES = ("modules", "verses", "tokens", "strong_terms", "comments", "entries", "links", "refs",
          "xrefs", "headings", "import_files")


def make_bblx(path, abbr, verses):
    """Um .bblx do e-Sword com Details e Bible; verses = [(versículo, texto), ...] do Gênesis 1."""
    Path(path).unlink(missing_ok=True)  # regravar um arquivo existente (teste de alteração)
    con = sqlite3.connect(path)
    con.execute("create table Details(Description, Abbreviation)")
    con.execute("insert into Details values (?, ?)", (f"Bíblia {abbr}", abbr))
    con.execute("create table Bible(Book, Chapter, Verse, Scripture)")
    con.executemany("insert into Bible values (?, ?, ?, ?)", [(1, 1, number, text) for number, text in verses])
    con.commit()
    con.close()


def run_build(out, folders, incremental=True):
    """Roda build.py e devolve a saída; falha o teste se o processo sair com erro."""
    command = [sys.executable, str(BUILD), "--out", str(out)]
    if incremental:
        command.append("--incremental")
    command += [str(folder) for folder in folders]
    proc = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
    if proc.returncode != 0:
        raise AssertionError(f"build.py saiu com {proc.returncode}:\n{proc.stdout}\n{proc.stderr}")
    return proc.stdout


def counts(db_path):
    """Contagem de cada tabela e o texto de todos os versículos, para comparar duas bases."""
    con = sqlite3.connect(db_path)
    try:
        result = {table: con.execute(f"select count(*) from {table}").fetchone()[0] for table in TABLES}
        result["texto"] = con.execute(
            "select m.abbr, v.verse, v.text, v.heading from verses v join modules m on m.id = v.module_id"
            " order by m.abbr, v.verse").fetchall()
    finally:
        con.close()
    return result


def scalar(db_path, sql, params=()):
    con = sqlite3.connect(db_path)
    try:
        return con.execute(sql, params).fetchone()[0]
    finally:
        con.close()


class IncrementalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.modules = self.root / "modulos"
        self.modules.mkdir()
        make_bblx(self.modules / "AAA.bblx", "AAA", [(1, "No princípio."), (2, "A terra."), (3, "Haja luz.")])
        make_bblx(self.modules / "BBB.bblx", "BBB", [(1, "Deus criou."), (2, "E viu.")])
        make_bblx(self.modules / "CCC.bblx", "CCC", [(1, "Sobre as águas."), (2, "Separou.")])
        self.out = self.root / "inc.db"

    def tearDown(self):
        self.tmp.cleanup()

    def test_segunda_execucao_nao_relê_nada(self):
        first = run_build(self.out, [self.modules])
        self.assertIn("sem base existente", first)
        self.assertEqual(first.count("  ok "), 3)

        before = counts(self.out)
        second = run_build(self.out, [self.modules])

        self.assertNotIn("  ok ", second)  # nenhum módulo foi lido de novo
        self.assertIn("incremental: 3 arquivos pulados sem releitura; 0 relidos", second)
        self.assertEqual(counts(self.out), before)

    def test_arquivo_removido_sai_da_base(self):
        run_build(self.out, [self.modules])
        os.remove(self.modules / "BBB.bblx")

        output = run_build(self.out, [self.modules])

        self.assertIn("removido BBB.bblx", output)
        self.assertIn("0 relidos", output)
        self.assertEqual(scalar(self.out, "select count(*) from modules where abbr = 'BBB'"), 0)
        self.assertEqual(scalar(self.out, "select count(*) from import_files where origin_path like '%BBB%'"), 0)
        self.assertEqual(scalar(self.out, "select count(*) from verses v join modules m on m.id = v.module_id"
                                " where m.abbr = 'BBB'"), 0)
        # Igual a uma importação completa feita sem o arquivo.
        without = self.root / "sem_bbb"
        without.mkdir()
        for name in ("AAA.bblx", "CCC.bblx"):
            (without / name).write_bytes((self.modules / name).read_bytes())
        full = self.root / "completa.db"
        run_build(full, [without], incremental=False)
        self.assertEqual(counts(self.out), counts(full))

    def test_arquivo_alterado_e_relido(self):
        run_build(self.out, [self.modules])
        make_bblx(self.modules / "AAA.bblx", "AAA", [(1, "No princípio Deus criou."), (2, "A terra."),
                                                    (3, "Haja luz.")])

        output = run_build(self.out, [self.modules])

        self.assertEqual(output.count("  ok "), 1)
        self.assertIn("1 relidos", output)
        self.assertIn("2 arquivos pulados sem releitura", output)
        self.assertEqual(scalar(self.out, "select text from verses v join modules m on m.id = v.module_id"
                                " where m.abbr = 'AAA' and v.verse = 1"), "No princípio Deus criou.")
        self.assertEqual(scalar(self.out, "select count(*) from modules where abbr = 'AAA'"), 1)
        self.assertEqual(scalar(self.out, "select count(*) from verses v join modules m on m.id = v.module_id"
                                " where m.abbr = 'AAA'"), 3)

    def test_versao_diferente_faz_importacao_completa(self):
        run_build(self.out, [self.modules])
        con = sqlite3.connect(self.out)
        con.execute("update meta set value = '0.0.0' where key = 'importer_version'")
        con.commit()
        con.close()

        output = run_build(self.out, [self.modules])

        self.assertIn("versão do importador na base: 0.0.0", output)
        self.assertEqual(output.count("  ok "), 3)
        self.assertEqual(scalar(self.out, "select count(*) from modules"), 3)


class DuplicateBibleTest(unittest.TestCase):
    """Cópia unida (D011) segue o controle: fica 'unido' e só volta a ser lida quando algo muda."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.folder = self.root / "dup"
        self.folder.mkdir()
        # A: sem títulos (vira a cópia que fica). B: com título de seção (é unida à A).
        make_bblx(self.folder / "A.bblx", "DUP", [(1, "No princípio.")])
        make_bblx(self.folder / "B.bblx", "DUP", [(1, r"{\b\qc Título} No princípio.")])
        self.out = self.root / "dup.db"

    def tearDown(self):
        self.tmp.cleanup()

    def test_copia_unida_so_e_relida_quando_algo_muda(self):
        first = run_build(self.out, [self.folder])
        self.assertIn("unido    B.bblx -> A.bblx (1 títulos)", first)
        self.assertEqual(scalar(self.out, "select count(*) from modules where abbr = 'DUP'"), 1)
        self.assertEqual(scalar(self.out, "select heading from verses v join modules m on m.id = v.module_id"
                                " where m.abbr = 'DUP'"), "Título")
        self.assertEqual(scalar(self.out, "select status from import_files where origin_path like '%B.bblx'"),
                         "unido")

        second = run_build(self.out, [self.folder])
        self.assertNotIn("  ok ", second)  # nem a cópia unida é relida sem mudança
        self.assertIn("0 relidos", second)

        os.remove(self.folder / "A.bblx")  # a cópia que ficava some: B precisa ser relida
        third = run_build(self.out, [self.folder])
        self.assertIn("removido A.bblx", third)
        self.assertIn("1 relidos", third)
        self.assertEqual(scalar(self.out, "select count(*) from modules where abbr = 'DUP'"), 1)
        self.assertEqual(scalar(self.out, "select origin_path from modules where abbr = 'DUP'"),
                         str(self.folder / "B.bblx"))
        self.assertEqual(scalar(self.out, "select heading from verses v join modules m on m.id = v.module_id"
                                " where m.abbr = 'DUP'"), "Título")


if __name__ == "__main__":
    unittest.main()
