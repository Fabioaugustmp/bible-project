"""Ponte português -> inglês pela numeração Strong (tarefa T23, desenho em EC2).

Para cada palavra portuguesa da consulta:
1. procura em `strong_terms` os Strong que a ARA traduz com essa palavra;
2. mantém só os sentidos principais (ver limites abaixo);
3. pega as traduções inglesas mais frequentes desses Strong.

A busca então procura "palavra OR tradução" nos comentários e dicionários.
Tudo vem de dados que já estão na base; nada é inventado nem traduzido por
máquina, e cada termo incluído diz de qual Strong veio.
"""
import threading
import unicodedata

# Uma palavra da consulta só é expandida por um Strong se:
MIN_WORD_SHARE = 0.15    # esse Strong responde por pelo menos 15% das vezes em que a ARA usa a palavra
MIN_STRONG_SHARE = 0.20  # e a palavra é pelo menos 20% das traduções portuguesas desse Strong
MIN_WORD_COUNT = 2       # e isso aconteceu pelo menos 2 vezes

# Um termo inglês só entra se for pelo menos 15% das traduções inglesas do Strong,
# aparecer 3 vezes ou mais e tiver no máximo duas palavras.
MIN_TERM_SHARE = 0.15
MIN_TERM_COUNT = 3
MAX_TERM_WORDS = 2
MAX_TERMS_PER_STRONG = 3
MAX_TERMS_PER_WORD = 5

# Palavras muito comuns cuja expansão só traria ruído.
STOPWORDS = set("""
    a o as os um uma uns umas de do da dos das em no na nos nas ao aos à às e é que se por para com sem
    pelo pela pelos pelas num numa dum duma sob sobre entre até contra desde após ante perante
    não sim mais menos muito muita muitos muitas todo toda todos todas tudo nada ele ela eles elas eu tu
    nós vós você vocês me te lhe nos vos lhes meu minha teu tua seu sua nosso nossa este esta esse essa
    aquele aquela isto isso aquilo como quando onde quem qual porque pois mas ou nem já ainda também
    ser estar ter haver ir vir fazer dar dizer ver saber poder querer ficar deixar falar
    é foi era são sou somos está estão tem têm há vai disse
""".split())


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return unicodedata.normalize("NFC", "".join(c for c in decomposed if not unicodedata.combining(c)))


class Bridge:
    """Índice em memória dos termos portugueses, montado uma vez por base."""

    def __init__(self):
        self._lock = threading.Lock()
        self._index = None   # palavra sem acento -> [(strong, termo original, count, share)]
        self._usage = None   # palavra sem acento -> total de ocorrências dessa palavra
        self.available = False

    def _load(self, con):
        index, usage = {}, {}
        has_table = con.execute("select 1 from sqlite_master where name = 'strong_terms'").fetchone()
        if has_table:
            for strong, term, count, share in con.execute(
                "select strong, term, count, share from strong_terms where lang = 'por'"
            ):
                key = strip_accents(term)
                index.setdefault(key, []).append((strong, term, count, share))
                usage[key] = usage.get(key, 0) + count
        self._index, self._usage, self.available = index, usage, bool(index)

    def ensure(self, con):
        if self._index is None:
            with self._lock:
                if self._index is None:
                    self._load(con)

    def expand(self, con, word: str):
        """Termos ingleses para uma palavra portuguesa: [{term, strong, count}], já filtrados."""
        self.ensure(con)
        key = strip_accents(word.lower())
        if key in STOPWORDS or len(key) < 2 or key not in self._index:
            return []
        total = self._usage[key]
        senses = [
            (strong, count, share) for strong, _, count, share in self._index[key]
            if count >= MIN_WORD_COUNT and count / total >= MIN_WORD_SHARE and share >= MIN_STRONG_SHARE
        ]
        found, seen = [], {key}
        for strong, _, _ in sorted(senses, key=lambda sense: -sense[1]):
            for term, count in con.execute(
                "select term, count from strong_terms where strong = ? and lang = 'eng'"
                " and share >= ? and count >= ? order by count desc limit ?",
                (strong, MIN_TERM_SHARE, MIN_TERM_COUNT, MAX_TERMS_PER_STRONG),
            ):
                term = term.strip()
                if len(term.split()) > MAX_TERM_WORDS or strip_accents(term) in seen:
                    continue
                # "sin offering" já é encontrado por "sin": não acrescenta nada à busca.
                if any(word in seen for word in strip_accents(term).split()):
                    continue
                seen.add(strip_accents(term))
                found.append({"term": term, "strong": strong, "count": count})
        return found[:MAX_TERMS_PER_WORD]


BRIDGE = Bridge()


def is_stopword(word: str) -> bool:
    return strip_accents(word.lower()) in STOPWORDS
