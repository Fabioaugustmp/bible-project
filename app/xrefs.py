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


# --- Grafo das referências de um versículo (T65, EC8) --------------------------------

EDGES_PER_NODE = 4   # cada nó mostra só as suas ligações mais fortes: o grafo fica legível
MIN_EDGE_WEIGHT = 3  # ligação mais fraca que isto não aparece (uma lista curada vale 3)


def graph(con, book, chapter, verse, size=15):
    """Nós = o versículo e os `size` vizinhos mais fortes (ranked); arestas = ligações entre eles.

    Peso de uma ligação entre dois vizinhos: 3 por lista curada que liga um ao
    outro (theWord, BSB, TSK) mais o número de comentários e verbetes que citam os
    dois (co-citação, até 10; itens que citam mais de MAX_LINKS_PER_ITEM versículos
    não contam). Cada nó guarda as EDGES_PER_NODE ligações mais fortes, com peso
    mínimo MIN_EDGE_WEIGHT; o centro liga-se a todos os vizinhos.
    """
    center = (book, chapter, verse)
    top, total = ranked(con, book, chapter, verse, size)
    keys = [(x["book"], x["chapter"], x["verse"]) for x in top]
    index = {key: i + 1 for i, key in enumerate(keys)}   # 0 é o centro
    weight = defaultdict(int)

    def pair(a, b):
        return (a, b) if a < b else (b, a)

    # Listas curadas entre os vizinhos.
    for key in keys:
        for target in con.execute(
            "select to_book, to_chapter, to_verse from xrefs where book = ? and chapter = ? and verse = ?", key
        ):
            target = tuple(target)
            if target in index and target != key:
                weight[pair(index[key], index[target])] += 3

    # Quem cita cada vizinho; o comentário do TSK de um vizinho é a lista curada dele.
    placeholders = ",".join("?" * len(TSK_MODULES))
    tsk = {row[0] for row in con.execute(
        f"select id from modules where abbr in ({placeholders})", TSK_MODULES)}
    citing = {}
    for key in keys:
        rows = con.execute(
            "select l.kind, l.item_id, x.module_id, x.book, x.ref_start from links l"
            " left join comments x on l.kind = 'comment' and x.id = l.item_id"
            " where l.book = ? and l.chapter = ? and l.verse = ?", key).fetchall()
        citing[key] = set()
        for kind, item_id, module_id, owner_book, owner_ref in rows:
            if module_id in tsk:
                owner = (owner_book, owner_ref // 1000, owner_ref % 1000)
                if owner in index and owner != key:
                    weight[pair(index[key], index[owner])] += 3
            else:
                citing[key].add((kind, item_id))

    # Co-citação, sem os itens que citam versículos demais.
    items = set().union(*citing.values()) if citing else set()
    sizes = {}
    for kind in ("comment", "entry"):
        ids = [item_id for k, item_id in items if k == kind]
        for start in range(0, len(ids), CHUNK):
            chunk = ids[start:start + CHUNK]
            for item_id, count in con.execute(
                f"select item_id, count(*) from links where kind = ? and item_id in ({','.join('?' * len(chunk))})"
                " group by item_id", (kind, *chunk),
            ):
                sizes[(kind, item_id)] = count
    usable = {key: {item for item in found if sizes.get(item, 0) <= MAX_LINKS_PER_ITEM}
              for key, found in citing.items()}
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            shared = len(usable[a] & usable[b])
            if shared:
                weight[pair(index[a], index[b])] += min(shared, 10)

    kept = set()
    for node in range(1, len(keys) + 1):
        strongest = sorted(((w, p) for p, w in weight.items() if node in p and w >= MIN_EDGE_WEIGHT),
                           reverse=True)[:EDGES_PER_NODE]
        kept.update(p for _, p in strongest)
    degree = defaultdict(int)
    for a, b in kept:
        degree[a] += 1
        degree[b] += 1
    edges = [{"a": 0, "b": i + 1, "weight": 3 * len(x["sources"]) + min(x["cocited"], 10)}
             for i, x in enumerate(top)]
    edges += [{"a": a, "b": b, "weight": weight[(a, b)]} for a, b in sorted(kept)]
    nodes = [{"book": book, "chapter": chapter, "verse": verse, "center": True, "testament":
              "AT" if book <= 39 else "NT", "degree": 0, "sources": [], "cocited": 0}]
    nodes += [{"book": key[0], "chapter": key[1], "verse": key[2], "center": False,
               "testament": "AT" if key[0] <= 39 else "NT", "degree": degree[i + 1],
               "sources": top[i]["sources"], "cocited": top[i]["cocited"]}
              for i, key in enumerate(keys)]
    return {"nodes": nodes, "edges": edges, "total": total}
