"""Mapa de estudo (T93) e linha do tempo (T93, D033), lidos só de data/user.db.

- O mapa liga passagens a tópicos e estudos pelas notas, notas de tópico e blocos de estudo.
- A linha do tempo junta os eventos já guardados com data (notas, tópicos, diário, estudos,
  memorização, conjuntos, leituras). Não há tabela nova: cada evento vem da data gravada
  na própria linha, então a linha do tempo nunca fica diferente do que está guardado.
"""

MAX_PASSAGES = 40     # o mapa mostra as passagens mais estudadas; o resto fica na lista
TIMELINE_LIMIT = 300


def map_data(con, q=None):
    passages = {}   # (book, chapter, verse) -> nó
    topics, studies, edges = {}, {}, []

    def passage(book, chapter, verse):
        key = (book, chapter, verse)
        if key not in passages:
            passages[key] = {"id": f"p{book}-{chapter}-{verse}", "kind": "passage",
                             "book": book, "chapter": chapter, "verse": verse, "weight": 0}
        return passages[key]

    # notas por versículo: passagem com nota (sem tópico)
    for r in con.execute("select a.book, a.chapter, a.verse, count(n.id) as c from notes n"
                         " join anchors a on a.id = n.anchor_id where n.deleted_at is null"
                         " group by a.book, a.chapter, a.verse"):
        passage(r["book"], r["chapter"], r["verse"])["weight"] += r["c"]

    # notas de tópico com passagem: liga o tópico à passagem
    for r in con.execute("select t.id as tid, t.name, a.book, a.chapter, a.verse, count(n.id) as c"
                         " from topic_notes n join topics t on t.id = n.topic_id and t.deleted_at is null"
                         " join anchors a on a.id = n.anchor_id where n.deleted_at is null"
                         " group by t.id, a.book, a.chapter, a.verse"):
        topic = topics.setdefault(r["tid"], {"id": f"t{r['tid']}", "kind": "topic", "name": r["name"], "weight": 0})
        node = passage(r["book"], r["chapter"], r["verse"])
        topic["weight"] += r["c"]
        node["weight"] += r["c"]
        edges.append({"from": topic["id"], "to": node["id"], "weight": r["c"]})

    # tópicos sem passagem também aparecem, com o número de notas
    for r in con.execute("select t.id, t.name, count(n.id) as c from topics t"
                         " left join topic_notes n on n.topic_id = t.id and n.deleted_at is null"
                         " where t.deleted_at is null group by t.id"):
        topics.setdefault(r["id"], {"id": f"t{r['id']}", "kind": "topic", "name": r["name"], "weight": r["c"]})

    # estudos e os blocos de passagem de cada um
    for r in con.execute("select s.id, s.title, a.book, a.chapter, a.verse, count(b.id) as c from studies s"
                         " join study_blocks b on b.study_id = s.id and b.anchor_id is not null"
                         " join anchors a on a.id = b.anchor_id where s.deleted_at is null"
                         " group by s.id, a.book, a.chapter, a.verse"):
        study = studies.setdefault(r["id"], {"id": f"s{r['id']}", "kind": "study", "name": r["title"], "weight": 0})
        node = passage(r["book"], r["chapter"], r["verse"])
        study["weight"] += r["c"]
        node["weight"] += r["c"]
        edges.append({"from": study["id"], "to": node["id"], "weight": r["c"]})

    ranked = sorted(passages.values(), key=lambda p: (-p["weight"], p["book"], p["chapter"], p["verse"]))
    shown = {p["id"] for p in ranked[:MAX_PASSAGES]}
    nodes = ranked[:MAX_PASSAGES] + list(topics.values()) + list(studies.values())
    kept = [e for e in edges if e["to"] in shown]
    # um nó de tópico ou estudo sem ligação visível continua na lista, mas não no desenho
    linked = {e["from"] for e in kept}
    for node in nodes:
        node["linked"] = node["id"] in linked or node["kind"] == "passage"
    return {"nodes": [n for n in nodes if n["weight"] > 0 or n["kind"] != "passage"],
            "edges": kept, "passages_total": len(passages), "passages_shown": min(MAX_PASSAGES, len(passages))}


def timeline(con, q=None):
    """Eventos com data, do mais recente ao mais antigo (até TIMELINE_LIMIT)."""
    events = []
    sources = [
        ("notes", "nota", "select n.created_at as at, null as title, a.book, a.chapter, a.verse, substr(n.body, 1, 120) as text"
                          " from notes n join anchors a on a.id = n.anchor_id where n.deleted_at is null"),
        ("topic", "tópico", "select n.created_at as at, t.name as title, a.book, a.chapter, a.verse,"
                            " substr(n.body, 1, 120) as text from topic_notes n join topics t on t.id = n.topic_id"
                            " left join anchors a on a.id = n.anchor_id where n.deleted_at is null and t.deleted_at is null"),
        ("journal", "diário", "select created_at as at, null as title, null as book, null as chapter, null as verse,"
                              " substr(body, 1, 120) as text from journal where deleted_at is null"),
        ("study", "estudo", "select created_at as at, title, null as book, null as chapter, null as verse,"
                            " null as text from studies where deleted_at is null"),
        ("memo", "memorização", "select created_at as at, null as title, book, chapter, verse, null as text"
                                " from memo_cards where deleted_at is null"),
        ("set", "conjunto", "select i.created_at as at, s.name as title, i.book, i.chapter, i.verse, null as text"
                            " from ref_set_items i join ref_sets s on s.id = i.set_id where s.deleted_at is null"),
        ("reading", "leitura", "select done_on || 'T00:00:00' as at, null as title, book, chapter, null as verse,"
                               " null as text from reading_days where done_on is not null"
                               " and plan_id in (select id from reading_plans where deleted_at is null)"),
    ]
    for kind, label, sql in sources:
        for r in con.execute(sql + " order by at desc limit ?", (TIMELINE_LIMIT,)).fetchall():
            events.append({"at": r["at"], "kind": kind, "label": label, "title": r["title"],
                           "book": r["book"], "chapter": r["chapter"], "verse": r["verse"], "text": r["text"]})
    events.sort(key=lambda e: e["at"] or "", reverse=True)
    return {"events": events[:TIMELINE_LIMIT]}
