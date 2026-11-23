"""Testes do leitor de módulos MySword (T104), com bases SQLite sintéticas.

Os arquivos imitam o que foi visto nos módulos reais (docs/FORMATOS.md, seção
MySword): tabela Details com caixa variável, Bíblia com marcação GBF e
dicionário em HTML com links '#bLIVRO.CAP.VERS'. Nenhum módulo real é usado.
"""
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importer"))

import mysword  # noqa: E402

sys.path.insert(0, str(ROOT / "app"))
import server  # noqa: E402


class FakeAdder:
    def __init__(self):
        self.modules, self.verses_calls, self.tokens_calls, self.logs = [], [], [], []
        self.xrefs_calls, self.entries_calls = [], []

    def module(self, meta):
        self.modules.append(meta)
        return len(self.modules)

    def verses(self, module_id, rows):
        self.verses_calls.append(rows)

    def tokens(self, module_id, words):
        self.tokens_calls.append(words)

    def xrefs(self, module_id, rows, count_as_items=False):
        self.xrefs_calls.append(rows)

    def entries(self, module_id, rows, links=None, refs=None):
        self.entries_calls.append((rows, refs))

    def log(self, level, message):
        self.logs.append((level, message))


def make_bible(directory, verses, details=None, name="teste.bbl.mybible"):
    """Bíblia MySword: Details(...) e Bible(Book, Chapter, Verse, Scripture)."""
    details = {"Description": "Bíblia de teste", "Abbreviation": "TST", "Language": "eng"} | (details or {})
    path = Path(directory) / name
    con = sqlite3.connect(path)
    con.execute(f"create table Details({', '.join(details)})")
    con.execute(f"insert into Details values ({', '.join('?' * len(details))})", tuple(details.values()))
    con.execute("create table Bible(Book INT, Chapter INT, Verse INT, Scripture TEXT)")
    con.executemany("insert into Bible values (?, ?, ?, ?)", verses)
    con.commit()
    con.close()
    return path


def make_dictionary(directory, words, details=None, name="teste.dct.mybible"):
    """Dicionário MySword: details (minúsculo, como nos reais) e dictionary(relativeorder, word, data)."""
    details = {"title": "Léxico de teste", "abbreviation": "LEX", "strong": 1} | (details or {})
    path = Path(directory) / name
    con = sqlite3.connect(path)
    con.execute(f"create table details({', '.join(details)})")
    con.execute(f"insert into details values ({', '.join('?' * len(details))})", tuple(details.values()))
    con.execute("create table dictionary(relativeorder INT, word TEXT, data TEXT)")
    con.executemany("insert into dictionary values (?, ?, ?)",
                    [(order, word, data) for order, (word, data) in enumerate(words)])
    con.commit()
    con.close()
    return path


class MyswordBibleTest(unittest.TestCase):
    def test_marcacao_gbf_strong_titulo_nota_e_referencia(self):
        verses = [
            (1, 1, 1, "<TS>A criação<Ts>In the beginning<WH7225> God<WH430> created<WH1254><WH853>"
                      " the heaven<WH8064>.<RF>nota de rodapé<Rf><RX 43.1.1-3>"),
            (43, 3, 16, "<FR>For<WG1063> God<WG2316> so loved<WG25> the world<WG2889> &amp; all.<Fr><CM>"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            add = FakeAdder()
            count = mysword.read_module(make_bible(tmp, verses), add)

        self.assertEqual(count, 2)
        meta = add.modules[0]
        self.assertEqual((meta["kind"], meta["abbr"], meta["lang"], meta["has_strongs"]), ("bible", "TST", "eng", 1))
        first, second = add.verses_calls[0]
        self.assertEqual(first[5], "A criação")
        self.assertEqual(first[3], "In the beginning God created the heaven.")
        self.assertIn("created{H1254}{H853}", first[4])
        self.assertEqual(first[6], "1.1.1")
        self.assertEqual(second[3], "For God so loved the world & all.")
        self.assertEqual(second[6], "43.3.16")
        # <RX 43.1.1-3>: do versículo 1 ao 3, isto é, mais 2.
        self.assertEqual(add.xrefs_calls[0], [(1, 1, 1, 43, 1, 1, 2)])
        self.assertTrue(add.tokens_calls[0])

    def test_idioma_ausente_e_estimado_pelo_texto(self):
        verses = [(43, 3, 16, "Porque Deus amou o mundo de tal maneira que deu o seu Filho, para que"
                              " todo aquele que nele crê não pereça, mas tenha a vida eterna.")]
        with tempfile.TemporaryDirectory() as tmp:
            add = FakeAdder()
            mysword.read_module(make_bible(tmp, verses, {"Language": None}), add)
        self.assertEqual(add.modules[0]["lang"], "por")

    def test_codigo_de_duas_letras(self):
        with tempfile.TemporaryDirectory() as tmp:
            add = FakeAdder()
            mysword.read_module(make_bible(tmp, [(1, 1, 1, "In the beginning.")], {"Language": "en"}), add)
        self.assertEqual(add.modules[0]["lang"], "eng")

    def test_versiculo_vazio_e_livro_fora_do_canon_ficam_de_fora_com_aviso(self):
        verses = [(1, 1, 1, "In the beginning."), (1, 1, 2, ""), (67, 1, 1, "Tobit.")]
        with tempfile.TemporaryDirectory() as tmp:
            add = FakeAdder()
            count = mysword.read_module(make_bible(tmp, verses), add)
        self.assertEqual(count, 1)
        messages = " | ".join(message for level, message in add.logs if level == "aviso")
        self.assertIn("1 versículos de livros fora do cânon", messages)
        self.assertIn("1 versículos vazios", messages)
        self.assertIn("1:1:2", messages)

    def test_modulo_protegido_nao_e_lido(self):
        # D008: com encryption ou compressed diferente de zero, só a tabela Details é consultada.
        for flags in ({"encryption": 2, "compressed": 1}, {"encryption": 0, "compressed": 1}):
            with tempfile.TemporaryDirectory() as tmp:
                add = FakeAdder()
                path = make_bible(tmp, [(1, 1, 1, "\x00\xff cifrado")], flags)
                count = mysword.read_module(path, add)
            self.assertEqual(count, 0)
            self.assertEqual(add.modules, [])
            self.assertEqual(add.verses_calls, [])
            self.assertEqual(add.logs[0][0], "ignorado")
            self.assertIn("D008", add.logs[0][1])

    def test_campos_de_protecao_vazios_nao_bloqueiam(self):
        with tempfile.TemporaryDirectory() as tmp:
            add = FakeAdder()
            count = mysword.read_module(
                make_bible(tmp, [(1, 1, 1, "In the beginning.")], {"encryption": None, "compressed": "0"}), add)
        self.assertEqual(count, 1)


class MyswordDictionaryTest(unittest.TestCase):
    def test_html_vira_texto_com_citacoes_clicaveis(self):
        words = [
            ("G26", "<p>Original: <strong>ἀγάπη</strong></p><ol><li>love</li><li>love feasts</li></ol>"
                    "<p>From <a class='dict' href='#dG25'>G25</a>; see <a class='bible' href='#b43.3.16'>Joh 3:16</a>"
                    " and <a class='bible' href='#b62.4.7-8'>1Jn 4:7-8</a>.</p>"),
            ("H430", "<p>Original: <strong>אלהים</strong></p>"),
            ("vazio", ""),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            add = FakeAdder()
            count = mysword.read_module(make_dictionary(tmp, words, {"language": "eng"}), add)

        self.assertEqual(count, 2)
        meta = add.modules[0]
        self.assertEqual((meta["kind"], meta["abbr"], meta["title"], meta["lang"]),
                         ("dictionary", "LEX", "Léxico de teste", "eng"))
        rows, refs = add.entries_calls[0]
        topic, text, origin_key = rows[0]
        self.assertEqual(topic, "G26")
        self.assertEqual(origin_key, "dictionary:1")
        self.assertNotIn("<", text)
        self.assertTrue(text.startswith("Original: ἀγάπη\n• love\n• love feasts"))
        self.assertEqual(len(refs[0]), 2)
        start, end, *target = refs[0][0]
        self.assertEqual(text[start:end], "Joh 3:16")
        self.assertEqual(tuple(target), (43, 3, 16, 3, 16))
        start, end, *target = refs[0][1]
        self.assertEqual(text[start:end], "1Jn 4:7-8")
        self.assertEqual(tuple(target), (62, 4, 7, 4, 8))
        self.assertEqual(rows[1][0], "H430")

    def test_html_to_marked_ignora_estilo_e_entidades(self):
        text = mysword.html_to_marked("<style>p {color: red}</style><p>a &amp; b</p><p>c<br>d</p>")
        self.assertEqual(text, "a & b\nc\nd")


class MyswordBuildTest(unittest.TestCase):
    def test_build_grava_procedencia(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "mods"
            folder.mkdir()
            make_bible(folder, [(1, 1, 1, "In the beginning<WH7225> God<WH430>.")])
            make_dictionary(folder, [("G26", "<p>love, <a href='#b43.3.16'>Joh 3:16</a></p>")])
            out = Path(tmp) / "out.db"
            proc = subprocess.run([sys.executable, str(ROOT / "importer" / "build.py"), "--out", str(out),
                                   str(folder)], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            con = sqlite3.connect(out)
            try:
                modules = con.execute(
                    "select source, kind, abbr, origin_path, length(origin_sha256), origin_size, origin_mtime"
                    " from modules order by kind").fetchall()
                verse_key = con.execute("select origin_key from verses").fetchone()[0]
                entry_key = con.execute("select origin_key from entries").fetchone()[0]
                links = con.execute("select kind, book, chapter, verse from links").fetchall()
            finally:
                con.close()
        self.assertEqual([row[:3] for row in modules], [("mysword", "bible", "TST"), ("mysword", "dictionary", "LEX")])
        for row in modules:
            self.assertTrue(row[3].endswith(".mybible"))
            self.assertEqual(row[4], 64)
            self.assertGreater(row[5], 0)
            self.assertTrue(row[6])
        self.assertEqual(verse_key, "1.1.1")
        self.assertEqual(entry_key, "dictionary:1")
        self.assertEqual(links, [("entry", 43, 3, 16)])


class MyswordBibliaLivreTest(unittest.TestCase):
    """T106: procedência da Bíblia Livre (CC BY 3.0 BR) e aviso dos versículos vazios, com base sintética."""

    def test_procedencia_e_aviso_dos_vazios_com_referencias(self):
        verses = [(1, 1, 1, "No princípio."), (15, 3, 6, ""), (19, 108, 13, ""), (66, 12, 17, ""),
                  (43, 3, 16, "Porque Deus amou o mundo.")]
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "mods"
            folder.mkdir()
            make_bible(folder, verses, {"Description": "Bíblia Livre", "Abbreviation": "BLivre", "Language": "por"},
                       name="biblialivre.bbl.mybible")
            out = Path(tmp) / "out.db"
            proc = subprocess.run([sys.executable, str(ROOT / "importer" / "build.py"), "--out", str(out),
                                   str(folder)], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            con = sqlite3.connect(out)
            try:
                module = con.execute("select source, kind, abbr, lang, items, origin_path, length(origin_sha256)"
                                     " from modules").fetchone()
                stored = con.execute("select count(*) from verses").fetchone()[0]
                empty_stored = con.execute("select count(*) from verses where trim(text) = ''").fetchone()[0]
                warning = con.execute("select level, message from import_log where level = 'aviso'").fetchone()
            finally:
                con.close()
        self.assertEqual(module[:5], ("mysword", "bible", "BLivre", "por", 2))
        self.assertTrue(module[5].endswith("biblialivre.bbl.mybible"))
        self.assertEqual(module[6], 64)
        self.assertEqual((stored, empty_stored), (2, 0))
        self.assertIn("3 versículos vazios", warning[1])
        for ref in ("15:3:6", "19:108:13", "66:12:17"):
            self.assertIn(ref, warning[1])


class MyswordStrongAoLadoTest(unittest.TestCase):
    """T105 (D038): o Strong completo entra ao lado de Dodson e AHLB, sem substituí-los."""

    def test_painel_strong_mostra_as_fontes_separadas(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "mods"
            folder.mkdir()
            make_dictionary(folder, [("G26", "<p>Dodson: love</p>"), ("H430", "<p>Dodson hebraico</p>")],
                            {"title": "Dodson", "abbreviation": "Dodson"}, name="dodson.dct.mybible")
            make_dictionary(folder, [("G26", "<p>Original: <b>ἀγάπη</b></p><p>Transliteration: agape</p>"),
                                     ("H430", "<p>Original: <b>אֱלֹהִים</b></p>"), ("b-", "<p>prefixo</p>")],
                            {"title": "Strong", "abbreviation": "Strong"}, name="strong.a.dct.mybible")
            out = Path(tmp) / "out.db"
            proc = subprocess.run([sys.executable, str(ROOT / "importer" / "build.py"), "--out", str(out),
                                   str(folder)], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            con = sqlite3.connect(out)
            con.row_factory = sqlite3.Row
            try:
                g26 = server.api_word(con, {"strong": "G26"})
                h430 = server.api_word(con, {"strong": "H430"})
                provenance = con.execute(
                    "select m.source, m.origin_path, e.origin_key from entries e join modules m on m.id = e.module_id"
                    " where m.abbr = 'Strong' and e.topic = 'G26'").fetchone()
                strong_keys = con.execute(
                    "select count(*) from entries e join modules m on m.id = e.module_id"
                    " where m.abbr = 'Strong' and e.topic glob '[GH][0-9]*'").fetchone()[0]
            finally:
                con.close()
        for word, expected in ((g26, ["Dodson", "Strong"]), (h430, ["Dodson", "Strong"])):
            self.assertEqual([lexicon["abbr"] for lexicon in word["lexicons"]], expected)
        dodson, strong = g26["lexicons"]
        self.assertEqual(dodson["excerpt"], "Dodson: love")
        self.assertTrue(strong["excerpt"].startswith("Original: ἀγάπη"))
        self.assertNotEqual(dodson["id"], strong["id"])
        self.assertEqual((provenance[0], provenance[2]), ("mysword", "dictionary:1"))
        self.assertTrue(provenance[1].endswith("strong.a.dct.mybible"))
        self.assertEqual(strong_keys, 2)   # "b-" (prefixo) não conta como chave Strong


if __name__ == "__main__":
    unittest.main()
