// Grafo das referências cruzadas de um versículo (T65, EC8; decisão P6: posicionamento
// escrito no projeto, sem biblioteca). Os dados vêm de /api/xref-graph (app/xrefs.py).

const SVG = "http://www.w3.org/2000/svg";

function svg(tag, attrs = {}, ...children) {
  const node = document.createElementNS(SVG, tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value !== null && value !== undefined) node.setAttribute(key, value);
  }
  node.append(...children.filter((child) => child !== null && child !== undefined));
  return node;
}

// Posicionamento por força (Fruchterman-Reingold), determinístico: mesma entrada,
// mesmo desenho. O centro fica fixo no meio; os vizinhos começam num círculo, na
// ordem do ranqueamento, e se acomodam: repelem-se todos, atraem-se pelas ligações.
export function layout(nodes, edges, width, height) {
  const n = nodes.length;
  const cx = width / 2, cy = height / 2;
  const radius = Math.min(width, height) * 0.36;
  const pos = nodes.map((_, i) => i === 0
    ? { x: cx, y: cy }
    : { x: cx + radius * Math.cos((2 * Math.PI * (i - 1)) / (n - 1) - Math.PI / 2),
        y: cy + radius * Math.sin((2 * Math.PI * (i - 1)) / (n - 1) - Math.PI / 2) });
  const k = Math.sqrt((width * height) / Math.max(n, 1)) * 0.85;
  const maxWeight = Math.max(1, ...edges.map((e) => e.weight));
  let temperature = width / 8;
  for (let step = 0; step < 300; step += 1) {
    const disp = pos.map(() => ({ x: 0, y: 0 }));
    for (let i = 0; i < n; i += 1) {
      for (let j = i + 1; j < n; j += 1) {
        let dx = pos[i].x - pos[j].x, dy = pos[i].y - pos[j].y;
        let d = Math.hypot(dx, dy);
        if (d < 0.01) { dx = 0.01 * (i - j); dy = 0.01; d = Math.hypot(dx, dy); }
        const force = (k * k) / d;
        disp[i].x += (dx / d) * force; disp[i].y += (dy / d) * force;
        disp[j].x -= (dx / d) * force; disp[j].y -= (dy / d) * force;
      }
    }
    for (const { a, b, weight } of edges) {
      const dx = pos[a].x - pos[b].x, dy = pos[a].y - pos[b].y;
      const d = Math.max(Math.hypot(dx, dy), 0.01);
      // ligação ao centro puxa menos, para o centro não engolir o desenho
      const pull = ((d * d) / k) * (0.25 + 0.5 * (weight / maxWeight)) * (a === 0 ? 0.3 : 1);
      disp[a].x -= (dx / d) * pull; disp[a].y -= (dy / d) * pull;
      disp[b].x += (dx / d) * pull; disp[b].y += (dy / d) * pull;
    }
    for (let i = 1; i < n; i += 1) {   // o centro não se move
      disp[i].x += (cx - pos[i].x) * 0.01;   // leve gravidade para o meio
      disp[i].y += (cy - pos[i].y) * 0.01;
      const d = Math.max(Math.hypot(disp[i].x, disp[i].y), 0.01);
      const move = Math.min(d, temperature);
      pos[i].x = Math.min(width - 50, Math.max(50, pos[i].x + (disp[i].x / d) * move));
      pos[i].y = Math.min(height - 24, Math.max(24, pos[i].y + (disp[i].y / d) * move));
    }
    temperature = Math.max(0.5, temperature * 0.985);
  }
  // Ocupa a área disponível: estica as distâncias ao centro até o nó mais afastado
  // encostar na margem (o formato do desenho não muda, só a escala).
  const reachX = Math.max(1, ...pos.map((q) => Math.abs(q.x - cx))) / (width / 2 - 70);
  const reachY = Math.max(1, ...pos.map((q) => Math.abs(q.y - cy))) / (height / 2 - 26);
  const scale = 1 / Math.max(reachX, reachY);
  return pos.map((q) => ({ x: cx + (q.x - cx) * scale, y: cy + (q.y - cy) * scale }));
}

// Rótulos sem sobreposição: cada rótulo vai para o lado de fora do nó e, se
// colidir com outro, desce ou sobe até ficar livre.
function placeLabels(items, width) {
  // Obstáculos: os próprios círculos (um rótulo não pode cobrir outro nó) e os rótulos já postos.
  const circles = items.map((item) => ({ x: item.x - item.r - 1, y: item.y - item.r - 1, w: 2 * item.r + 2, h: 2 * item.r + 2 }));
  const placed = [];
  for (const [index, item] of items.entries()) {
    const w = item.text.length * 6.4 + 6, h = 14;
    const outward = item.x >= width / 2 || item.center;
    const sides = outward ? [1, -1] : [-1, 1];
    const blocked = (box) => placed.some((p) => overlaps(p, box))
      || circles.some((c, i) => i !== index && overlaps(c, box));
    let best = null;
    // Tenta os dois lados do nó e, em cada um, subir ou descer aos poucos.
    for (const shift of [0, 8, -8, 16, -16, 24, -24, 32, -32]) {
      for (const side of sides) {
        const box = { w, h, x: side > 0 ? item.x + item.r + 4 : item.x - item.r - 4 - w, y: item.y - h / 2 + shift };
        if (!blocked(box)) { best = box; break; }
      }
      if (best) break;
    }
    best = best || { w, h, x: outward ? item.x + item.r + 4 : item.x - item.r - 4 - w, y: item.y - h / 2 };
    placed.push(best);
    item.label = best;
  }
}

function overlaps(a, b) {
  return a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
}

// Componente: desenha o grafo de um versículo e permite recentrar e voltar.
// `api`, `label` e `preview` vêm de app.js (para não duplicar código).
export function xrefGraph({ book, chapter, verse }, { api, label, preview, hidePreview, open, maxWidth = 640 }) {
  const root = document.createElement("div");
  root.className = "xgraph";
  const history = [];
  let current = { book, chapter, verse };

  async function draw(center) {
    current = center;
    root.setAttribute("aria-busy", "true");
    const data = await api("xref-graph", center);
    root.removeAttribute("aria-busy");
    const width = Math.max(300, Math.min(root.clientWidth || 420, maxWidth));
    const height = Math.round(width * 0.8);
    const pos = layout(data.nodes, data.edges, width, height);
    const maxDegree = Math.max(1, ...data.nodes.map((n) => n.degree));
    const items = data.nodes.map((node, i) => ({
      ...node, ...pos[i], text: label(node.book, node.chapter, node.verse),
      r: node.center ? 11 : 5 + 7 * Math.sqrt(node.degree / maxDegree),
    }));
    placeLabels(items, width);
    const maxWeight = Math.max(1, ...data.edges.map((e) => e.weight));

    const edges = data.edges.map((e) => svg("line", {
      class: "xg-edge" + (e.a === 0 ? " to-center" : ""),
      x1: items[e.a].x, y1: items[e.a].y, x2: items[e.b].x, y2: items[e.b].y,
      "stroke-width": (0.6 + 2.4 * (e.weight / maxWeight)).toFixed(2),
    }));
    const nodes = items.map((item, i) => {
      const name = `${item.text}${item.center ? " (centro)" : `, ${item.degree} ligações`}`;
      const g = svg("g", {
        class: `xg-node ${item.testament === "AT" ? "ot" : "nt"}${item.center ? " center" : ""}`,
        tabindex: "0", role: "button",
        "aria-label": item.center ? `${name}. Enter abre no leitor.` : `${name}. Enter recentra o grafo.`,
        "data-book": item.book, "data-chapter": item.chapter, "data-verse": item.verse,
        "data-to-chapter": item.chapter, "data-to-verse": item.verse,
      },
        svg("circle", { cx: item.x, cy: item.y, r: item.r.toFixed(1) }),
        svg("text", { x: item.label.x, y: item.label.y + 11 }, item.text));
      const activate = () => {
        hidePreview();
        if (item.center) open(current);
        else { history.push(current); draw({ book: item.book, chapter: item.chapter, verse: item.verse }); }
      };
      g.addEventListener("click", activate);
      g.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") { event.preventDefault(); activate(); }
      });
      g.addEventListener("mouseenter", () => preview(g));
      g.addEventListener("mouseleave", hidePreview);
      g.addEventListener("focus", () => preview(g));
      g.addEventListener("blur", hidePreview);
      return g;
    });

    const isolated = items.filter((item) => !item.center && item.degree === 0).map((item) => item.text);
    const centerLabel = items[0].text;
    root.replaceChildren(
      svg("svg", { viewBox: `0 0 ${width} ${height}`, width: "100%", role: "group",
        "aria-label": `Grafo das referências de ${centerLabel}: ${items.length - 1} versículos` },
        svg("g", {}, ...edges), svg("g", {}, ...nodes)),
      legend(centerLabel, isolated),
    );
  }

  function legend(centerLabel, isolated) {
    const bar = document.createElement("div");
    bar.className = "xg-legend";
    if (history.length) {
      const back = document.createElement("button");
      back.className = "link";
      back.textContent = `← ${label(history.at(-1).book, history.at(-1).chapter, history.at(-1).verse)}`;
      back.addEventListener("click", () => draw(history.pop()));
      bar.append(back);
    }
    const openLink = document.createElement("button");
    openLink.className = "link";
    openLink.textContent = `Abrir ${centerLabel} no leitor`;
    openLink.addEventListener("click", () => open(current));
    bar.append(openLink);
    const key = document.createElement("span");
    key.className = "xg-key";
    key.innerHTML = '<i class="ot"></i>Antigo Testamento <i class="nt"></i>Novo Testamento · maior = mais ligado · clique recentra';
    bar.append(key);
    if (isolated.length) {
      const note = document.createElement("span");
      note.className = "xg-key";
      note.textContent = `Sem ligação com os demais: ${isolated.join(", ")}`;
      bar.append(note);
    }
    return bar;
  }

  queueMicrotask(() => draw(current));
  return root;
}
