"""Cânon de 66 livros na versificação KJV (a usada por e-Sword e theWord)."""
import json
from pathlib import Path

# (abreviação, nome) na ordem canônica; o número do livro é a posição + 1.
BOOKS = [
    ("Gn", "Gênesis"), ("Êx", "Êxodo"), ("Lv", "Levítico"), ("Nm", "Números"),
    ("Dt", "Deuteronômio"), ("Js", "Josué"), ("Jz", "Juízes"), ("Rt", "Rute"),
    ("1Sm", "1 Samuel"), ("2Sm", "2 Samuel"), ("1Rs", "1 Reis"), ("2Rs", "2 Reis"),
    ("1Cr", "1 Crônicas"), ("2Cr", "2 Crônicas"), ("Ed", "Esdras"), ("Ne", "Neemias"),
    ("Et", "Ester"), ("Jó", "Jó"), ("Sl", "Salmos"), ("Pv", "Provérbios"),
    ("Ec", "Eclesiastes"), ("Ct", "Cânticos"), ("Is", "Isaías"), ("Jr", "Jeremias"),
    ("Lm", "Lamentações"), ("Ez", "Ezequiel"), ("Dn", "Daniel"), ("Os", "Oséias"),
    ("Jl", "Joel"), ("Am", "Amós"), ("Ob", "Obadias"), ("Jn", "Jonas"),
    ("Mq", "Miquéias"), ("Na", "Naum"), ("Hc", "Habacuque"), ("Sf", "Sofonias"),
    ("Ag", "Ageu"), ("Zc", "Zacarias"), ("Ml", "Malaquias"),
    ("Mt", "Mateus"), ("Mc", "Marcos"), ("Lc", "Lucas"), ("Jo", "João"),
    ("At", "Atos"), ("Rm", "Romanos"), ("1Co", "1 Coríntios"), ("2Co", "2 Coríntios"),
    ("Gl", "Gálatas"), ("Ef", "Efésios"), ("Fp", "Filipenses"), ("Cl", "Colossenses"),
    ("1Ts", "1 Tessalonicenses"), ("2Ts", "2 Tessalonicenses"), ("1Tm", "1 Timóteo"),
    ("2Tm", "2 Timóteo"), ("Tt", "Tito"), ("Fm", "Filemom"), ("Hb", "Hebreus"),
    ("Tg", "Tiago"), ("1Pe", "1 Pedro"), ("2Pe", "2 Pedro"), ("1Jo", "1 João"),
    ("2Jo", "2 João"), ("3Jo", "3 João"), ("Jd", "Judas"), ("Ap", "Apocalipse"),
]

OT_BOOKS = 39

# VERSES[livro - 1][capítulo - 1] = quantidade de versículos.
VERSES = json.loads((Path(__file__).with_name("canon.json")).read_text(encoding="utf-8"))


def references(first_book: int = 1, last_book: int = 66):
    """Gera (livro, capítulo, versículo) em ordem canônica."""
    for book in range(first_book, last_book + 1):
        for chapter, count in enumerate(VERSES[book - 1], start=1):
            for verse in range(1, count + 1):
                yield book, chapter, verse


OT_VERSES = sum(sum(chapters) for chapters in VERSES[:OT_BOOKS])
NT_VERSES = sum(sum(chapters) for chapters in VERSES[OT_BOOKS:])
