"""Referências cruzadas ranqueadas (tarefa T25).

Três sinais, todos da própria biblioteca:
- **listas curadas**: o módulo de referências do theWord, as referências
  embutidas no interlinear BSB e o Treasury of Scripture Knowledge (TSK e
  TSKe, cujo comentário de cada versículo é uma lista de referências);
- **co-citação**: quantos outros comentários e verbetes citam, no mesmo
  trecho, o versículo aberto e o versículo candidato.

Ordem: primeiro pelo número de listas curadas que trazem a referência, depois
pela co-citação. Cada resultado diz de onde veio.
"""
from collections import defaultdict

TSK_MODULES = ("TSK", "TSKe")
MAX_LINKS_PER_ITEM = 150   # itens que citam centenas de versículos (verbetes temáticos) só trazem ruído
NEIGHBOURHOOD = 3          # versículos vizinhos do mesmo capítulo não contam como referência
MIN_COCITED = 3            # sem lista curada, só entra o que é citado junto em 3 itens ou mais
CHUNK = 500


def _source_label(abbr):
    if abbr.startswith("BSB"):
        return "BSB"
    if abbr in TSK_MODULES:
        return "TSK"
    return "theWord"


def ranked(con, book, chapter, verse, limit=12):
    ref = chapter * 1000 + verse
    curated = defaultdict(set)     # (livro, cap, vers) -> {fontes}
    spans = {}

    # 1. Listas curadas de referências.
    for to_book, to_chapter, to_verse, span, abbr in con.execute(
        "select x.to_book, x.to_chapter, x.to_verse, x.to_span, m.abbr from xrefs x"
        " join modules m on m.id = x.module_id where x.book = ? and x.chapter = ? and x.verse = ?",
        (book, chapter, verse),
    ):
        key = (to_book, to_chapter, to_verse)
        curated[key].add(_source_label(abbr))
        spans[key] = max(spans.get(key, 0), span or 0)

    # 2. TSK: o comentário do próprio versículo é a lista de referências.
    placeholders = ",".join("?" * len(TSK_MODULES))
    tsk_items = [row[0] for row in con.execute(
        f"select c.id from comments c join modules m on m.id = c.module_id where m.abbr in ({placeholders})"
        " and c.book = ? and c.ref_start <= ? and c.ref_end >= ? and c.ref_start > ?",
        (*TSK_MODULES, book, ref, ref, chapter * 1000),
    )]
    for item_id in tsk_items:
        for key in con.execute("select book, chapter, verse from links where kind = 'comment' and item_id = ?",
                               (item_id,)):
            curated[tuple(key)].add("TSK")

    # 3. Co-citação: outros itens que citam este versículo e também o candidato.
    # Os itens do TSK ficam de fora: já entraram como lista curada.
    citing = con.execute(
        "select l.kind, l.item_id from links l left join comments c on l.kind = 'comment' and c.id = l.item_id"
        " left join modules m on m.id = c.module_id"
        f" where l.book = ? and l.chapter = ? and l.verse = ? and coalesce(m.abbr, '') not in ({placeholders})",
        (book, chapter, verse, *TSK_MODULES)).fetchall()
    cocited = defaultdict(int)
    for kind in ("comment", "entry"):
        ids = [item_id for k, item_id in citing if k == kind]
        for start in range(0, len(ids), CHUNK):
            chunk = ids[start:start + CHUNK]
            targets = defaultdict(set)
            for item_id, to_book, to_chapter, to_verse in con.execute(
                f"select item_id, book, chapter, verse from links where kind = ?"
                f" and item_id in ({','.join('?' * len(chunk))})", (kind, *chunk),
            ):
                targets[item_id].add((to_book, to_chapter, to_verse))
            for refs in targets.values():
                if len(refs) <= MAX_LINKS_PER_ITEM:
                    for key in refs:
                        cocited[key] += 1

    def is_self_or_neighbour(key):
        return key[0] == book and key[1] == chapter and abs(key[2] - verse) <= NEIGHBOURHOOD

    candidates = set(curated) | {key for key, count in cocited.items() if count >= MIN_COCITED}
    scored = sorted(
        (key for key in candidates if not is_self_or_neighbour(key)),
        # mesmo número de listas: outro capítulo antes do mesmo capítulo, depois a co-citação
        key=lambda key: (-len(curated.get(key, ())), key[:2] == (book, chapter), -cocited.get(key, 0), key),
    )
    return [
        {"book": key[0], "chapter": key[1], "verse": key[2], "span": spans.get(key, 0),
         "sources": sorted(curated.get(key, ())), "cocited": cocited.get(key, 0)}
        for key in scored[:limit]
    ], len(scored)
