import { xrefGraph } from "./graph.js";

const $ = (selector) => document.querySelector(selector);

const state = {
  modules: [], bibles: [], books: [],
  module: null, book: 43, chapter: 1, verse: null,
  langFilter: "all",   // 'all' | 'por' | 'other': filtra comentários e citações no painel
  lastSearch: null,    // { query, data }: permite voltar aos resultados
  bilingual: true,     // ponte por Strong na busca (T23)
  words: false,        // modo palavras: clicar abre o termo original (T20)
  parallel: false,     // versões em paralelo (T62)
  parallelIds: [],     // versões escolhidas para o paralelo
};

// --- Utilitários --------------------------------------------------------------

async function api(endpoint, params = {}) {
  const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined));
  const response = await fetch(`/api/${endpoint}?${new URLSearchParams(clean)}`);
  if (!response.ok) throw new Error(`${endpoint}: ${response.status}`);
  return response.json();
}

function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === "class") node.className = value;
    else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2), value);
    else if (value !== null && value !== undefined && value !== false) node.setAttribute(key, value === true ? "" : value);
  }
  node.append(...children.flat(Infinity).filter((child) => child !== null && child !== undefined && child !== false));
  return node;
}

const store = {
  get(key) { try { return localStorage.getItem(key); } catch { return null; } },
  set(key, value) { try { localStorage.setItem(key, value); } catch { /* sem armazenamento */ } },
};

const bookOf = (number) => state.books[number - 1];
const LANG = { por: "pt-BR", eng: "en", spa: "es", grc: "grc", heb: "he" };
const LANG_LABEL = { por: "PT", eng: "EN", spa: "ES", grc: "GR", heb: "HE" };
const LANG_NAME = { por: "Português", eng: "Inglês", spa: "Espanhol", grc: "Grego", heb: "Hebraico", und: "Outros" };

// Tipos de conteúdo (T60): etiqueta de cada um; cores em style.css (--type-*).
const TYPE_LABEL = {
  bible: "Bíblia", commentary: "Comentário", dictionary: "Dicionário",
  lexicon: "Léxico", book: "Livro", xref: "Referências",
};
// Dicionários cujos verbetes são números Strong: aparecem como "Léxico", não "Dicionário".
const LEXICON_ABBRS = new Set(["Dodson", "AHLB", "LSJ", "MLSJ", "KJC", "LXXHebGreek"]);

function refLabel(book, chapter, verse) {
  return `${bookOf(book).name} ${chapter}${verse ? ":" + verse : ""}`;
}

// ref = capítulo * 1000 + versículo (ver importer/db.py)
function rangeLabel(book, start, end) {
  const [c1, v1, c2, v2] = [Math.floor(start / 1000), start % 1000, Math.floor(end / 1000), end % 1000];
  const abbr = bookOf(book).abbr;
  if (c1 === 0) return `${abbr} (introdução)`;
  if (v1 === 0) return `${abbr} ${c1} (introdução)`;
  if (start === end) return `${abbr} ${c1}:${v1}`;
  return c1 === c2 ? `${abbr} ${c1}:${v1}–${v2}` : `${abbr} ${c1}:${v1} – ${c2}:${v2}`;
}

// O servidor marca o trecho encontrado com [[ ]]; aqui vira <mark> sem usar innerHTML.
function highlighted(text) {
  const fragment = document.createDocumentFragment();
  text.split(/(\[\[.*?\]\])/s).forEach((part) => {
    if (part.startsWith("[[") && part.endsWith("]]")) fragment.append(el("mark", {}, part.slice(2, -2)));
    else if (part) fragment.append(part);
  });
  return fragment;
}

const normalize = (text) =>
  text.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[\s.]/g, "");

// "Jo 3:16", "joão 3.16", "1 co 13", "salmos 23" -> {book, chapter, verse}
function parseReference(input) {
  const match = input.trim().match(/^(\d?\s*[^\d\s][^\d]*?)\s*(\d+)(?:\s*[:.,]\s*(\d+))?$/);
  if (!match) return null;
  const typed = match[1].toLowerCase().replace(/[\s.]/g, "");
  const key = normalize(match[1]);
  const book =
    state.books.find((b) => b.abbr.toLowerCase() === typed || b.name.toLowerCase().replace(/\s/g, "") === typed) ||
    state.books.find((b) => normalize(b.abbr) === key || normalize(b.name) === key) ||
    (key.length >= 3 && state.books.find((b) => normalize(b.name).startsWith(key)));
  if (!book) return null;
  const chapter = Number(match[2]);
  if (chapter < 1 || chapter > book.chapters.length) return null;
  const verse = match[3] ? Number(match[3]) : null;
  if (verse && verse > book.chapters[chapter - 1]) return null;
  return { book: book.book, chapter, verse };
}

// --- Navegação ------------------------------------------------------------------

function readHash() {
  const [module, book, chapter, verse] = location.hash.replace(/^#\/?/, "").split("/").map(Number);
  if (state.bibles.some((m) => m.id === module)) state.module = module;
  if (bookOf(book) && chapter >= 1 && chapter <= bookOf(book).chapters.length) {
    state.book = book;
    state.chapter = chapter;
    state.verse = verse >= 1 && verse <= bookOf(book).chapters[chapter - 1] ? verse : null;
  }
}

function go(changes) {
  Object.assign(state, changes);
  const parts = [state.module, state.book, state.chapter];
  if (state.verse) parts.push(state.verse);
  const hash = "#/" + parts.join("/");
  if (location.hash === hash) render();
  else location.hash = hash; // dispara hashchange -> render
}

function step(direction) {
  let { book, chapter } = state;
  chapter += direction;
  if (chapter < 1) {
    if (book === 1) return;
    book -= 1;
    chapter = bookOf(book).chapters.length;
  } else if (chapter > bookOf(book).chapters.length) {
    if (book === state.books.length) return;
    book += 1;
    chapter = 1;
  }
  go({ book, chapter, verse: null });
}

// --- Leitura --------------------------------------------------------------------

let renderToken = 0;
let shown = { module: null, book: null, chapter: null };

async function render() {
  const token = ++renderToken;
  const module = state.bibles.find((m) => m.id === state.module);
  $("#version").value = state.module;
  $("#book").value = state.book;
  const chapters = bookOf(state.book).chapters.length;
  $("#chapter").replaceChildren(
    ...Array.from({ length: chapters }, (_, i) => el("option", { value: i + 1 }, String(i + 1))));
  $("#chapter").value = state.chapter;
  $("#prev").disabled = state.book === 1 && state.chapter === 1;
  $("#next").disabled = state.book === state.books.length && state.chapter === chapters;

  const text = $("#text");
  const hasWords = module.has_strongs === 1;
  $("#words").hidden = !hasWords;
  $("#words").setAttribute("aria-pressed", String(state.words && hasWords));
  $("#text").classList.toggle("words-on", state.words && hasWords);
  const sameChapter = shown.module === state.module && shown.book === state.book
    && shown.chapter === state.chapter && shown.words === state.words;
  $("#parallel").setAttribute("aria-pressed", String(state.parallel));
  if (state.parallel) await renderParallel(token);
  else if (!sameChapter) {
    const { verses } = await api("chapter", { module: state.module, book: state.book, chapter: state.chapter });
    if (token !== renderToken) return; // navegação mais nova já em andamento
    shown = { module: state.module, book: state.book, chapter: state.chapter, words: state.words };
    document.title = `${refLabel(state.book, state.chapter)} · ${module.abbr}`;
    $("#kicker").textContent = module.title || module.abbr;
    $("#title").textContent = refLabel(state.book, state.chapter);
    text.lang = LANG[module.lang] || "";
    text.dir = module.lang === "heb" ? "rtl" : "ltr";
    if (!verses.length) {
      text.replaceChildren(el("p", { class: "empty" }, `${module.abbr} não contém este capítulo.`));
    } else {
      text.replaceChildren(...verses.flatMap((v) => [
        v.heading ? el("h2", { class: "pericope", dir: "ltr" }, v.heading) : null,
        el("span", {
          class: "v", "data-verse": v.verse, role: "button", tabindex: "0",
          onclick: (event) => {
            const word = event.target.closest(".w");
            if (word && state.words) {
              event.stopPropagation();
              showWord(word.dataset.strong.split(" ")[0], word);
            } else {
              go({ verse: v.verse });
            }
          },
        }, el("sup", {}, String(v.verse)), state.words && v.words ? wordsOf(v.words) : v.text),
        " ",
      ]).filter(Boolean));
    }
    $("#hint").hidden = !verses.length;
    followReading();
    if (!state.verse) $("#reader").scrollTop = 0;
  }

  // Seleção: só troca a marca, sem redesenhar o capítulo.
  text.querySelector(".selected")?.classList.remove("selected");
  const selected = state.verse ? text.querySelector(`.v[data-verse="${state.verse}"], .prow[data-verse="${state.verse}"]`) : null;
  if (selected) {
    selected.classList.add("selected");
    if (!sameChapter) selected.scrollIntoView({ block: "center" });
    $("#hint").hidden = true;
    showVerse();
  } else if (panelMode === "verse") {
    closePanel();
  }
}

// --- Versões em paralelo (T62) -----------------------------------------------------

const MAX_COLUMNS = 4;

// Versões escolhidas para o paralelo: as guardadas (só as que existem) ou, por padrão, a aberta.
function parallelChoice() {
  const ids = state.parallelIds.filter((id) => state.bibles.some((m) => m.id === id)).slice(0, MAX_COLUMNS);
  return ids.length ? ids : [state.module];
}

async function renderParallel(token) {
  const ids = parallelChoice();
  const { book, chapter } = state;
  const results = await Promise.all(ids.map((id) => api("chapter", { module: id, book, chapter })));
  if (token !== renderToken) return;
  const columns = ids.map((id, i) => {
    const module = state.bibles.find((m) => m.id === id);
    return { module, verses: new Map(results[i].verses.map((v) => [v.verse, v.text])) };
  });
  const numbers = [...new Set(columns.flatMap((c) => [...c.verses.keys()]))].sort((a, b) => a - b);
  shown = { module: null, book: null, chapter: null, words: null };   // o modo normal redesenha ao voltar
  const text = $("#text");
  $("#kicker").textContent = "Versões em paralelo";
  $("#title").textContent = refLabel(book, chapter);
  document.title = `${refLabel(book, chapter)} · paralelo`;
  text.lang = ""; text.dir = "ltr";
  $("#hint").hidden = true;

  const picker = el("div", { class: "pbar", role: "group", "aria-label": "Versões mostradas" },
    state.bibles.map((m) => {
      const on = ids.includes(m.id);
      return el("button", {
        class: "chip" + (on ? " on" : ""), "aria-pressed": String(on),
        title: m.title || m.abbr,
        onclick: () => {
          let next = on ? ids.filter((id) => id !== m.id) : [...ids, m.id];
          if (next.length === 0) next = [m.id];
          if (next.length > MAX_COLUMNS) return;
          state.parallelIds = next;
          store.set("parallelIds", JSON.stringify(next));
          render();
        },
      }, m.abbr);
    }));
  const grid = `grid-template-columns: repeat(${columns.length}, minmax(0, 1fr))`;
  const head = el("div", { class: "prow phead", style: grid },
    columns.map((c) => el("div", { class: "pcol-head", lang: LANG[c.module.lang] || null }, c.module.abbr)));
  const rows = numbers.map((n) => el("div", {
    class: "prow" + (n === state.verse ? " selected" : ""), "data-verse": n, style: grid,
    role: "button", tabindex: "0",
    onclick: () => go({ verse: n }),
    onkeydown: (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); go({ verse: n }); } },
  }, columns.map((c, index) => el("div", {
    class: "pcell", lang: LANG[c.module.lang] || null, dir: c.module.lang === "heb" ? "rtl" : null,
  }, index === 0 ? el("sup", {}, String(n)) : null,
     c.verses.has(n) ? c.verses.get(n) : el("span", { class: "pempty" }, "—")))));
  text.replaceChildren(picker, head, ...rows);
  followReading();
}

// Versículo palavra por palavra: cada expressão com Strong vira um elemento clicável.
function wordsOf(words) {
  const nodes = [];
  words.forEach(([surface, codes], index) => {
    if (index && surface && !/^[,.;:!?”’)\]]/.test(surface)) nodes.push(" ");
    if (!codes.length) { nodes.push(surface); return; }
    nodes.push(el("span", { class: "w", "data-strong": codes.join(" "), title: codes.join(" ") },
      surface || "·", el("sub", {}, codes.join(" "))));
  });
  return nodes;
}

// --- Citações bíblicas dentro dos comentários (T24) ------------------------------

// Texto com as citações (posições vindas do servidor) como elementos clicáveis.
function linked(text, refs = []) {
  const fragment = document.createDocumentFragment();
  let last = 0;
  for (const ref of refs || []) {
    if (ref.start < last || ref.end > text.length) continue;
    fragment.append(text.slice(last, ref.start));
    fragment.append(el("a", {
      class: "ref", href: `#/${state.module}/${ref.book}/${ref.chapter}/${ref.verse}`,
      "data-book": ref.book, "data-chapter": ref.chapter, "data-verse": ref.verse,
      "data-to-chapter": ref.to_chapter, "data-to-verse": ref.to_verse,
    }, text.slice(ref.start, ref.end)));
    last = ref.end;
  }
  fragment.append(text.slice(last));
  return fragment;
}

// Prévia do trecho citado, na versão aberta, ao passar o mouse ou focar a citação.
const passageCache = new Map();
let previewFor = null;

async function showPreview(anchor) {
  const d = anchor.dataset;
  const key = `${state.module}:${d.book}.${d.chapter}.${d.verse}-${d.toChapter}.${d.toVerse}`;
  previewFor = anchor;
  if (!passageCache.has(key)) {
    passageCache.set(key, api("passage", {
      module: state.module, book: d.book, chapter: d.chapter, verse: d.verse,
      to_chapter: d.toChapter, to_verse: d.toVerse,
    }).catch(() => null));
  }
  const data = await passageCache.get(key);
  if (previewFor !== anchor || !data) return;
  const module = state.bibles.find((m) => m.id === state.module);
  const book = Number(d.book);
  const range = Number(d.toChapter) === Number(d.chapter) && Number(d.toVerse) === Number(d.verse)
    ? refLabel(book, Number(d.chapter), Number(d.verse))
    : `${refLabel(book, Number(d.chapter), Number(d.verse))}–${Number(d.toChapter) === Number(d.chapter) ? d.toVerse : d.toChapter + ":" + d.toVerse}`;
  const box = $("#preview");
  box.replaceChildren(
    el("div", { class: "source" }, el("b", {}, range), el("span", {}, module.abbr)),
    data.verses.length
      ? el("div", { class: "t", lang: LANG[module.lang] || null },
          data.verses.map((v, i) => [i ? " " : null, el("sup", {}, String(v.verse)), v.text]))
      : el("p", { class: "empty" }, `${module.abbr} não tem este trecho.`),
    ...(data.more ? [el("div", { class: "origin" }, "Trecho mais longo: clique para ler.")] : []));
  box.hidden = false;
  const rect = anchor.getBoundingClientRect();
  const width = Math.min(360, innerWidth - 24);
  box.style.width = width + "px";
  box.style.left = Math.max(12, Math.min(rect.left, innerWidth - width - 12)) + "px";
  const below = rect.bottom + 8;
  box.style.top = (below + box.offsetHeight < innerHeight ? below : Math.max(8, rect.top - box.offsetHeight - 8)) + "px";
}

function hidePreview() {
  previewFor = null;
  $("#preview").hidden = true;
}

document.addEventListener("mouseover", (event) => {
  const anchor = event.target.closest?.(".ref");
  if (anchor && anchor !== previewFor) showPreview(anchor);
});
document.addEventListener("mouseout", (event) => {
  const anchor = event.target.closest?.(".ref");
  if (anchor && !anchor.contains(event.relatedTarget)) hidePreview();
});
document.addEventListener("focusin", (event) => {
  if (event.target.classList?.contains("ref")) showPreview(event.target);
});
document.addEventListener("focusout", (event) => {
  if (event.target.classList?.contains("ref")) hidePreview();
});
document.addEventListener("click", (event) => {
  const anchor = event.target.closest?.(".ref");
  if (!anchor) return;
  event.preventDefault();
  hidePreview();
  const d = anchor.dataset;
  go({ book: Number(d.book), chapter: Number(d.chapter), verse: Number(d.verse) });
});

// --- Painel ---------------------------------------------------------------------

let panelMode = null; // 'verse' | 'search' | 'item'

// O que o painel mostra agora, para poder fixá-lo (T61). Cada show* define
// `pendingView` antes de chamar openPanel.
let currentView = null;
let pendingView = null;
// Quando definido, openPanel escreve num item fixado em vez do painel (restauração).
let renderTarget = null;

function openPanel(mode, title, ...content) {
  const nodes = content.flat(Infinity).filter(Boolean);
  if (renderTarget) {
    renderTarget.title = title;
    renderTarget.body.replaceChildren(...nodes);
    return;
  }
  panelMode = mode;
  currentView = pendingView ? { ...pendingView, title } : null;
  pendingView = null;
  $("#panel-title").textContent = title;
  $("#panel-body").replaceChildren(...nodes);
  $("#panel-body").scrollTop = 0;
  $("#panel").hidden = false;
  $("#panel-pin").hidden = !currentView;
  layout.showPinned(false);
  layout.update();
}

function closePanel() {
  panelMode = null;
  currentView = null;
  $("#panel").hidden = true;
  layout.update();
}

// --- Comentário que acompanha a leitura (T63) ------------------------------------

function currentWhere() {
  return { book: state.book, chapter: state.chapter, verse: state.verse || 1 };
}

function commentaryNodes(data, where) {
  const header = el("div", { class: "source" }, kindTag("commentary"), el("b", {}, data.abbr),
    data.item ? el("span", { class: "range" }, rangeLabel(where.book, data.item.ref_start, data.item.ref_end)) : null);
  if (!data.item) return [header, el("p", { class: "empty" }, "Nenhum comentário cobre este versículo neste módulo.")];
  return [header, el("div", { class: "t", lang: LANG[data.item.lang] || null }, linked(data.item.text, data.item.refs))];
}

// Atualiza os comentários acompanhados para o versículo dado (sem mudar a seleção).
async function refreshCommentaryPins(where) {
  const pins = layout.pins.filter((pin) => pin.view.type === "commentary");
  if (!pins.length) return;
  const key = `${where.book}.${where.chapter}.${where.verse}`;
  await Promise.all(pins.map(async (pin) => {
    if (pin.key === key) return;
    pin.key = key;
    const token = pin.token = (pin.token || 0) + 1;
    try {
      const data = await api("commentary", { module: pin.view.module, book: where.book, chapter: where.chapter, verse: where.verse });
      if (pin.token !== token) return;
      pin.title = `${data.abbr} · ${bookOf(where.book).abbr} ${where.chapter}:${where.verse}`;
      pin.body.replaceChildren(...commentaryNodes(data, where));
      layout.save();
      layout.renderTabs();
    } catch {
      if (pin.token === token) pin.key = null;
    }
  }));
}

function pinCommentary(moduleId) {
  const body = el("div", { class: "pinned-content" }, el("p", { class: "empty" }, "Acompanhando a leitura…"));
  layout.add({ type: "commentary", module: moduleId }, "Comentário", body);
  refreshCommentaryPins(currentWhere());
}

// Quando o texto muda de posição, o versículo que está no meio da tela é o que vale.
let readingObserver = null;

function followReading() {
  if (readingObserver) readingObserver.disconnect();
  if (typeof IntersectionObserver === "undefined") return;
  readingObserver = new IntersectionObserver((entries) => {
    if (!layout.pins.some((pin) => pin.view.type === "commentary")) return;
    const verse = entries.filter((entry) => entry.isIntersecting)
      .map((entry) => Number(entry.target.dataset.verse)).sort((a, b) => a - b)[0];
    if (verse) refreshCommentaryPins({ book: state.book, chapter: state.chapter, verse });
  }, { root: $("#reader"), rootMargin: "-45% 0px -50% 0px" });
  $("#text").querySelectorAll(".v, .prow[data-verse]").forEach((node) => readingObserver.observe(node));
}

// --- Colunas: painel, itens fixados e divisórias (T61) ----------------------------

const MIN_READER = 448, MIN_COLUMN = 320, MAX_PINS = 6, WIDE = 1100;

const layout = {
  pins: [],          // [{ id, view, title, body }]
  active: null,      // id do item fixado visível
  narrowPinned: false,

  isWide: () => innerWidth >= WIDE,

  // Telas estreitas: painel e coluna fixada se revezam no mesmo espaço.
  showPinned(on) {
    this.narrowPinned = on && this.pins.length > 0;
    this.update();
  },

  update() {
    const hasPins = this.pins.length > 0;
    const panelOpen = !$("#panel").hidden;
    const root = $(".layout");
    root.classList.toggle("has-pins", hasPins);
    root.classList.toggle("show-pinned", this.narrowPinned || (hasPins && !panelOpen));
    $("#pinned").hidden = !hasPins;
    $("#split-panel").hidden = !panelOpen;
    $("#split-pinned").hidden = !hasPins;
    const switcher = $("#show-pins");
    switcher.hidden = !hasPins;
    switcher.textContent = `Fixados (${this.pins.length})`;
    this.renderTabs();
    this.applyWidths();
  },

  renderTabs() {
    const tabs = $("#pin-tabs");
    const panelOpen = !$("#panel").hidden;
    tabs.replaceChildren(
      // Em tela estreita, volta ao painel de estudo.
      panelOpen ? el("button", { class: "pin-tab back-to-panel", onclick: () => this.showPinned(false) }, "← Estudo") : null,
      ...this.pins.map((pin) => el("span", { class: "pin-tab" + (pin.id === this.active ? " on" : "") },
        el("button", {
          class: "pin-title", role: "tab", "aria-selected": String(pin.id === this.active),
          title: pin.title, onclick: () => this.activate(pin.id),
        }, pin.title),
        el("button", { class: "pin-close", "aria-label": `Desafixar ${pin.title}`, onclick: () => this.unpin(pin.id) }, "×"))));
    const pin = this.pins.find((item) => item.id === this.active);
    $("#pinned-body").replaceChildren(...(pin ? [pin.body] : []));
  },

  activate(id) {
    this.active = id;
    this.save();
    this.showPinned(true);
  },

  add(view, title, body) {
    const same = this.pins.find((pin) => JSON.stringify(pin.view) === JSON.stringify(view));
    if (same) {
      same.body = body;
      same.title = title;
      return this.activate(same.id);
    }
    const pin = { id: `p${Date.now()}${Math.random().toString(36).slice(2, 6)}`, view, title, body };
    this.pins.push(pin);
    if (this.pins.length > MAX_PINS) this.pins.shift();
    this.activate(pin.id);
  },

  unpin(id) {
    this.pins = this.pins.filter((pin) => pin.id !== id);
    if (this.active === id) this.active = this.pins.at(-1)?.id ?? null;
    if (!this.pins.length) this.narrowPinned = false;
    this.save();
    this.update();
  },

  save() {
    store.set("pins", JSON.stringify({ active: this.pins.findIndex((p) => p.id === this.active),
      views: this.pins.map((pin) => ({ ...pin.view, title: pin.title })) }));
  },

  // Larguras (guardadas ou padrão), sempre deixando ao texto pelo menos MIN_READER.
  applyWidths() {
    const root = $(".layout");
    if (!this.isWide()) {
      root.style.setProperty("--panel-w", "");
      root.style.setProperty("--pinned-w", "");
      return;
    }
    const total = root.clientWidth;
    const panelOpen = !$("#panel").hidden, pinsOpen = this.pins.length > 0;
    let panel = Number(store.get("panelWidth")) || Math.min(480, total * 0.42);
    let pinned = Number(store.get("pinnedWidth")) || Math.min(448, total * 0.34);
    const room = total - MIN_READER - 14;   // 14 = duas divisórias
    const used = (panelOpen ? panel : 0) + (pinsOpen ? pinned : 0);
    if (used > room) {   // encolhe as duas colunas na mesma proporção, sem passar do mínimo
      const factor = room / used;
      panel = Math.max(MIN_COLUMN, panel * factor);
      pinned = Math.max(MIN_COLUMN, pinned * factor);
    }
    root.style.setProperty("--panel-w", Math.round(panel) + "px");
    root.style.setProperty("--pinned-w", Math.round(pinned) + "px");
  },
};

// Fixa o que o painel mostra: o conteúdo (com seus botões) vai para a coluna.
function pinCurrent() {
  if (!currentView) return;
  const body = el("div", { class: "pinned-content" });
  body.append(...$("#panel-body").childNodes);
  const { title, ...view } = currentView;
  layout.add(view, title, body);
  closePanel();
  if (view.type === "verse" && state.verse) go({ verse: null });
}

// Fixa uma vista sem passar pelo painel (por exemplo, um comentário aberto no painel do versículo).
async function pinView(view) {
  const pin = { body: el("div", { class: "pinned-content" }) };
  await renderView(view, pin);
  layout.add(view, pin.title, pin.body);
}

// Remonta um item fixado a partir da descrição guardada (ao recarregar a página).
async function renderView(view, target) {
  renderTarget = target;
  try {
    if (view.type === "verse") await showVerse(view);
    else if (view.type === "item") await showItem(view.kind, view.id);
    else if (view.type === "word") await showWord(view.strong);
    else if (view.type === "commentary") target.body.replaceChildren(el("p", { class: "empty" }, "Acompanhando a leitura…"));
    else if (view.type === "search") {
      const saved = state.lastSearch;
      await showSearch(view.query);
      state.lastSearch = saved;
    }
  } finally {
    renderTarget = null;
  }
}

async function restorePins() {
  let saved = null;
  try { saved = JSON.parse(store.get("pins") || "null"); } catch { saved = null; }
  if (!saved?.views?.length) return;
  for (const { title, ...view } of saved.views.slice(-MAX_PINS)) {
    const pin = { id: `p${Math.random().toString(36).slice(2, 10)}`, view, title, body: el("div", { class: "pinned-content" }) };
    await renderView(view, pin);
    layout.pins.push(pin);
  }
  layout.active = layout.pins[Math.max(0, saved.active)]?.id ?? layout.pins[0]?.id ?? null;
  layout.update();
  layout.applyWidths();
  refreshCommentaryPins(currentWhere());
}

// Divisórias: arrastar com o mouse ou usar as setas do teclado.
function setupSplitter(splitter, column, key) {
  const resize = (width) => {
    const total = $(".layout").clientWidth;
    const other = key === "panelWidth"
      ? (layout.pins.length ? $("#pinned").getBoundingClientRect().width : 0)
      : (!$("#panel").hidden ? $("#panel").getBoundingClientRect().width : 0);
    const clamped = Math.round(Math.max(MIN_COLUMN, Math.min(width, total - MIN_READER - other)));
    store.set(key, clamped);
    layout.applyWidths();
  };
  splitter.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    splitter.setPointerCapture(event.pointerId);
    splitter.classList.add("dragging");
    const move = (e) => resize($(column).getBoundingClientRect().right - e.clientX);
    const stop = () => {
      splitter.classList.remove("dragging");
      splitter.removeEventListener("pointermove", move);
      splitter.removeEventListener("pointerup", stop);
    };
    splitter.addEventListener("pointermove", move);
    splitter.addEventListener("pointerup", stop);
  });
  splitter.addEventListener("keydown", (event) => {
    const step = event.shiftKey ? 64 : 24;
    const width = $(column).getBoundingClientRect().width;
    if (event.key === "ArrowLeft") resize(width + step);
    else if (event.key === "ArrowRight") resize(width - step);
    else return;
    event.preventDefault();
  });
}

function badge(lang) {
  return lang && lang !== "por" ? el("span", { class: "badge" }, LANG_LABEL[lang] || lang) : null;
}

function section(title, count, ...content) {
  return [el("h3", {}, title + " ", count === null ? null : el("small", {}, `(${count})`)), ...content.flat(Infinity)];
}

// Etiqueta de tipo de conteúdo (T60).
function kindTag(type) {
  return type ? el("i", { class: `kind kind-${type}` }, TYPE_LABEL[type]) : null;
}

// Tipo de um módulo; dicionário cujos verbetes são números Strong vira léxico.
function typeOf(kind, abbr) {
  if (kind === "dictionary") return LEXICON_ABBRS.has(abbr) ? "lexicon" : "dictionary";
  return { bible: "bible", commentary: "commentary", book: "book", xrefs: "xref" }[kind] || null;
}

// Tipo de um item: comentário, ou verbete (o tipo do módulo dele, achado pela sigla).
function itemType(kind, abbr, moduleId = null) {
  if (kind === "comment" || kind === "commentary") return "commentary";
  const module = moduleId !== null
    ? state.modules.find((m) => m.id === moduleId)
    : state.modules.find((m) => m.abbr === abbr);
  return module ? typeOf(module.kind, module.abbr) : null;
}

// Como section, com uma barra na cor do tipo antes do título (T60). O título já diz o
// tipo; a etiqueta escrita fica só nos itens de seções que misturam tipos.
function typedSection(types, title, count, ...content) {
  const [heading, ...rest] = section(title, count, ...content);
  const distinct = [...new Set(types)].filter(Boolean);
  heading.classList.add("typed", distinct.length === 1 ? `kind-${distinct[0]}` : "kind-mixed");
  return [heading, ...rest];
}

const passesFilter = (lang) =>
  state.langFilter === "all" || (state.langFilter === "por" ? lang === "por" : lang !== "por");

function backToSearch() {
  return state.lastSearch
    ? el("button", { class: "link back", onclick: () => renderSearch() }, `← Resultados de "${state.lastSearch.query}"`)
    : null;
}

function filterBar(onChange) {
  const options = [["all", "Tudo"], ["por", "Português"], ["other", "Outros idiomas"]];
  return el("div", { class: "filters", role: "group", "aria-label": "Idioma do material" },
    options.map(([value, label]) => el("button", {
      class: "chip" + (state.langFilter === value ? " on" : ""), "aria-pressed": String(state.langFilter === value),
      onclick: () => { state.langFilter = value; store.set("langFilter", value); onChange(); },
    }, label)));
}

// Um comentário: uma linha recolhida; ao abrir, busca o texto inteiro uma vez.
function commentRow(book, comment) {
  const body = el("div", { class: "t", lang: LANG[comment.lang] || null }, linked(comment.excerpt, comment.refs));
  const partial = comment.length > comment.excerpt.length;
  let loaded = !partial;
  return el("details", {
    class: "fold",
    ontoggle: async (event) => {
      if (!event.target.open || loaded) return;
      loaded = true;
      try {
        const item = await api("item", { kind: "comment", id: comment.id });
        body.replaceChildren(linked(item.text, item.refs));
      } catch {
        loaded = false;
      }
    },
  },
    el("summary", {},
      el("b", {}, comment.abbr), el("span", { class: "range" }, rangeLabel(book, comment.ref_start, comment.ref_end)),
      badge(comment.lang),
      el("span", { class: "peek", lang: LANG[comment.lang] || null }, comment.excerpt.slice(0, 110))),
    body,
    el("div", { class: "origin fold-actions" },
      partial ? `${Math.round(comment.length / 1000)} mil caracteres · ` : null,
      el("button", { class: "link", onclick: () => pinView({ type: "item", kind: "comment", id: comment.id }) },
        "Fixar ao lado"), " · ",
      el("button", { class: "link", onclick: () => pinCommentary(comment.module_id) }, "Acompanhar na leitura")));
}

// Um módulo que cita o versículo: a lista de itens só é buscada ao abrir.
function citedGroup(group) {
  const list = el("div", { class: "chips" });
  let loaded = false;
  return el("details", {
    class: "fold",
    ontoggle: async (event) => {
      if (!event.target.open || loaded) return;
      loaded = true;
      const { book, chapter, verse } = state;
      const { items } = await api("cited", { kind: group.kind, module: group.module_id, book, chapter, verse });
      list.replaceChildren(...items.map((item) => el("button", {
        class: "chip", onclick: () => showItem(item.kind, item.id),
      }, item.kind === "entry" ? item.label : rangeLabel(item.book, item.ref_start, item.ref_end))));
    },
  },
    el("summary", {}, kindTag(itemType(group.kind, group.abbr, group.module_id)),
      el("b", {}, group.abbr), el("span", { class: "range" }, group.title || ""),
      badge(group.lang), el("span", { class: "count" }, String(group.count))),
    list);
}

let xrefLimit = 12, xrefVerse = null;
let verseTab = "versoes";   // aba do painel do versículo (ergonomia)
let versionsOpen = false; // mostra todas as versões em português
let xrefBook = null;   // livro escolhido na faixa (T66); null = todos

// Grupos da faixa por livro (T66), na ordem da Bíblia.
const BOOK_GROUPS = [["Lei", 1, 5], ["Históricos", 6, 17], ["Poéticos", 18, 22], ["Profetas", 23, 39],
  ["Evangelhos", 40, 43], ["Atos", 44, 44], ["Cartas", 45, 65], ["Apocalipse", 66, 66]];

// Faixa com uma barra por livro: a altura é a quantidade de referências daquele livro.
function bookStrip(counts) {
  const max = Math.max(1, ...counts.map((c) => c.count));
  const bars = BOOK_GROUPS.map(([name, from, to]) => {
    const row = counts.filter((c) => c.book >= from && c.book <= to);
    return el("div", { class: "bk-group" },
      el("span", { class: "bk-name" }, name),
      el("div", { class: "bk-bars", role: "group", "aria-label": name },
        row.map((c) => {
          const label = bookOf(c.book).name;
          return el("button", {
            class: "bk-bar" + (xrefBook === c.book ? " on" : "") + (c.count ? "" : " zero"),
            disabled: c.count ? null : "disabled",
            style: `height:${Math.max(2, Math.round((c.count / max) * 34))}px`,
            title: `${label}: ${c.count} referências`,
            "aria-label": `${label}: ${c.count} referências`,
            "aria-pressed": String(xrefBook === c.book),
            onclick: () => { xrefBook = xrefBook === c.book ? null : c.book; showVerse(); },
          });
        })));
  });
  const present = counts.filter((c) => c.count);
  const chips = el("div", { class: "chips bk-chips" },
    present.map((c) => el("button", {
      class: "chip" + (xrefBook === c.book ? " on" : ""), "aria-pressed": String(xrefBook === c.book),
      onclick: () => { xrefBook = xrefBook === c.book ? null : c.book; showVerse(); },
    }, `${bookOf(c.book).abbr} ${c.count}`)));
  return el("div", { class: "bookmap" },
    bars,
    chips,
    xrefBook ? el("button", { class: "link", onclick: () => { xrefBook = null; showVerse(); } },
      `Mostrar todos os livros (filtro: ${bookOf(xrefBook).name})`) : null);
}

async function showVerse(ref = null) {
  const { book, chapter, verse } = ref || state;
  const verseKey = `${book}.${chapter}.${verse}`;
  if (verseKey !== xrefVerse) { xrefVerse = verseKey; xrefLimit = 12; xrefBook = null; versionsOpen = false; }
  const data = await api("verse", { book, chapter, verse, module: state.module, xrefs: xrefLimit, xbook: xrefBook });
  const similar = await api("similar", { book, chapter, verse }).catch(() => ({ available: false, verses: [] }));
  const notesData = await api("user/notes", { book, chapter, verse }).catch(() => ({ notes: [] }));
  refreshCommentaryPins({ book, chapter, verse });
  const bookCounts = data.xrefs_total || xrefBook ? (await api("xref-books", { book, chapter, verse })).books : null;
  if (!ref && (book !== state.book || chapter !== state.chapter || verse !== state.verse)) return;
  pendingView = { type: "verse", book, chapter, verse };

  const versionItem = (v) => el("div", { class: "item", lang: LANG[v.lang] || null, dir: v.lang === "heb" ? "rtl" : null },
    el("div", { class: "source", dir: "ltr" },
      v.module_id === state.module
        ? el("b", {}, v.abbr)
        : el("button", { class: "link", title: "Ler nesta versão", onclick: () => go({ module: v.module_id }) }, v.abbr),
      badge(v.lang)),
    el("div", { class: "t" }, v.text));
  const native = data.versions.filter((v) => v.lang === "por");
  const foreign = data.versions.filter((v) => v.lang !== "por");

  // Referências ranqueadas (T25): listas curadas primeiro, depois co-citação nos comentários.
  const why = (x) => [
    ...x.sources,
    x.cocited ? `citados juntos ${x.cocited}×` : null,
  ].filter(Boolean).join(" · ");
  const xrefs = data.xrefs.map((x) => el("button", {
    class: "result", onclick: () => go({ book: x.book, chapter: x.chapter, verse: x.verse }),
    title: "Listas curadas: theWord, BSB e TSK. Citados juntos: comentários e verbetes que citam os dois versículos.",
  }, el("div", { class: "source" },
      el("b", {}, refLabel(x.book, x.chapter, x.verse) + (x.span ? `–${x.verse + x.span}` : "")),
      el("span", {}, why(x))),
    x.text ? el("div", { class: "t clamp2" }, x.text) : null));
  // Lista ou grafo (T65). O grafo precisa de largura: em telas estreitas, só a lista.
  const graphFits = matchMedia("(min-width: 760px)").matches;
  const xrefMode = graphFits && store.get("xrefView") === "graph" ? "graph" : "list";
  const xrefSwitch = el("div", { class: "filters xref-switch", role: "group", "aria-label": "Mostrar referências como" },
    graphFits ? [["list", "Lista"], ["graph", "Grafo"]].map(([value, text]) => el("button", {
      class: "chip" + (xrefMode === value ? " on" : ""), "aria-pressed": String(xrefMode === value),
      onclick: () => { store.set("xrefView", value); showVerse(); },
    }, text)) : null,
    el("button", { class: "chip", onclick: () => openGraphFull({ book, chapter, verse }) }, "Grafo em tela cheia"));
  const graph = xrefMode === "graph"
    ? xrefGraph({ book, chapter, verse }, {
        api,
        label: (b, c, v) => `${bookOf(b).abbr} ${c}:${v}`,
        preview: showPreview,
        hidePreview,
        open: (ref) => go(ref),
      })
    : null;
  const strip = !graph && bookCounts ? bookStrip(bookCounts) : null;
  const moreXrefs = data.xrefs.length < data.xrefs_total && data.xrefs.length < 60
    ? el("button", {
        class: "more", onclick: () => { xrefLimit = Math.min(60, xrefLimit + 24); showVerse(); },
      }, `Mais referências (${data.xrefs.length} de ${data.xrefs_total})`)
    : null;

  const comments = data.comments.filter((c) => passesFilter(c.lang));
  const cited = data.cited.filter((c) => passesFilter(c.lang));
  const citedTotal = cited.reduce((sum, group) => sum + group.count, 0);
  const of = (visible, all) => (visible.length === all.length ? String(all.length) : `${visible.length} de ${all.length}`);

  // Abas do painel (ergonomia): uma seção por vez, com a contagem no nome.
  const versionShown = versionsOpen ? native : native.slice(0, 6);
  const citedCount = data.cited.reduce((sum, g) => sum + g.count, 0);
  const tabsDef = [
    ["versoes", "Versões", data.versions.length, () => typedSection(["bible"], "Versões", data.versions.length,
      versionShown.map(versionItem),
      !versionsOpen && native.length > 6
        ? el("button", { class: "more", onclick: () => { versionsOpen = true; showVerse(); } },
            `Mostrar todas as versões em português (${native.length})`)
        : null,
      foreign.length
        ? el("details", { class: "fold plain", open: native.length === 0 },
            el("summary", {}, el("b", {}, `Outros idiomas (${foreign.length})`),
              el("span", { class: "range" }, foreign.map((v) => v.abbr).join(" · "))),
            foreign.map(versionItem))
        : null)],
    ["notas", "Minhas notas", notesData.notes.length, () => notesTab(book, chapter, verse, notesData.notes)],
    ["parecidas", "Parecidas", similar.verses.length, () => typedSection(["bible"], "Passagens parecidas", similar.verses.length,
      el("p", { class: "group-note" }, similar.available
        ? "Passagens de sentido parecido ao versículo, pela versão ARA1993+. Ordem pela proximidade de sentido."
        : similar.reason),
      similar.verses.map((v) => el("button", {
        class: "result", onclick: () => go({ book: v.book, chapter: v.chapter, verse: v.verse }),
      }, el("div", { class: "source" }, el("b", {}, refLabel(v.book, v.chapter, v.verse)),
          el("span", {}, `similaridade ${v.score.toFixed(2)}`)),
        el("div", { class: "t" }, v.text))))],
    ["referencias", "Referências", data.xrefs_total, () => typedSection(["xref"], "Referências cruzadas", data.xrefs_total, xrefSwitch,
      graph || [strip, xrefs.length ? xrefs : el("p", { class: "empty" }, "Nenhuma referência neste livro."), moreXrefs])],
    ["comentarios", "Comentários", data.comments.length, () => [
      filterBar(showVerse),
      typedSection(["commentary"], "Comentários", of(comments, data.comments),
        comments.length ? comments.map((c) => commentRow(book, c))
          : el("p", { class: "empty" }, data.comments.length ? "Nenhum neste idioma." : "Nenhum comentário cobre este versículo."))]],
    ["citado", "Citado em", citedCount, () => [
      filterBar(showVerse),
      typedSection(cited.map((g) => itemType(g.kind, g.abbr, g.module_id)), "Citado em",
        `${citedTotal} em ${cited.length} obras`, cited.map(citedGroup))]],
  ];
  const shown = tabsDef.filter(([id, , count]) => id === "versoes" || id === "notas" || count);
  const active = shown.find(([id]) => id === verseTab) || shown[0];
  const tabBar = el("div", { class: "mode-tabs verse-tabs", role: "tablist" },
    shown.map(([id, label, count]) => el("button", {
      class: "mode-tab" + (id === active[0] ? " on" : ""), role: "tab", "aria-selected": String(id === active[0]),
      onclick: () => { verseTab = id; showVerse(); },
    }, label, el("small", {}, ` ${count}`))));

  openPanel("verse", refLabel(book, chapter, verse),
    backToSearch(),
    tabBar,
    active[3]());
}

async function showItem(kind, id) {
  const item = await api("item", { kind, id });
  pendingView = { type: "item", kind, id };
  if (!item) return;
  const title = kind === "entry" ? item.label : `${item.abbr} · ${rangeLabel(item.book, item.ref_start, item.ref_end)}`;
  const backVerse = state.verse
    ? el("button", { class: "link back", onclick: showVerse }, `← ${refLabel(state.book, state.chapter, state.verse)}`)
    : null;
  openPanel("item", title,
    backVerse, backToSearch(),
    el("div", { class: "item" },
      el("div", { class: "source" }, kindTag(itemType(kind, item.abbr)), el("b", {}, item.abbr), el("span", {}, item.title || ""), badge(item.lang)),
      el("div", { class: "t", lang: LANG[item.lang] || null }, linked(item.text, item.refs)),
      el("div", { class: "origin" }, `Origem: ${item.origin_path} · ${item.origin_key}`)));
}

// --- Palavra (Strong) --------------------------------------------------------------

async function showWord(strong, source = null, offset = 0, previous = null) {
  document.querySelectorAll(".w.picked").forEach((node) => node.classList.remove("picked"));
  source?.classList.add("picked");
  const data = await api("word", { strong, module: state.module, offset });
  pendingView = { type: "word", strong };
  if (previous) data.occurrences = previous.concat(data.occurrences);
  const original = data.original[0]?.term;
  const langLabel = data.original_lang === "grc" ? "grego" : "hebraico";

  const chips = (items, lang) => el("div", { class: "chips" }, items.map((item) => el("button", {
    class: "chip", lang, title: `${Math.round(item.share * 100)}% das ocorrências · buscar este termo`,
    onclick: () => { $("#q").value = item.term; showSearch(item.term); },
  }, item.term, el("span", { class: "n" }, String(item.count)))));

  const lexicon = (entry) => {
    const body = el("div", { class: "t", lang: LANG[entry.lang] || null }, entry.excerpt);
    let loaded = entry.length <= entry.excerpt.length;
    return el("details", {
      class: "fold", open: entry === data.lexicons[0],
      ontoggle: async (event) => {
        if (!event.target.open || loaded) return;
        loaded = true;
        body.textContent = (await api("item", { kind: "entry", id: entry.id })).text;
      },
    }, el("summary", {}, kindTag(typeOf("dictionary", entry.abbr)), el("b", {}, entry.abbr),
        el("span", { class: "range" }, entry.title || ""), badge(entry.lang)),
      body);
  };
  // O primeiro léxico já vem aberto: carrega o texto inteiro dele.
  queueMicrotask(() => document.querySelector("#panel-body details.fold[open]")?.dispatchEvent(new Event("toggle")));

  const occurrence = (item) => el("button", {
    class: "result", onclick: () => go({ book: item.book, chapter: item.chapter, verse: item.verse }),
  }, el("div", { class: "source" }, el("b", {}, refLabel(item.book, item.chapter, item.verse)),
      item.used.length ? el("span", {}, "ARA: " + item.used.join(", ")) : null),
    item.text ? el("div", { class: "t clamp2" }, item.text) : null);

  const more = data.occurrences.length < data.total
    ? el("button", {
        class: "more",
        onclick: () => showWord(strong, null, data.occurrences.length, data.occurrences).then(() => {
          $("#panel-body").scrollTop = $("#panel-body").scrollHeight;
        }),
      }, `Mais ocorrências (${data.occurrences.length} de ${data.total})`)
    : null;

  const backVerse = state.verse
    ? el("button", { class: "link back", onclick: showVerse }, `← ${refLabel(state.book, state.chapter, state.verse)}`)
    : null;
  openPanel("word", `${strong}${original ? " · " + original : ""}`,
    backVerse, backToSearch(),
    original ? el("p", { class: "lemma", lang: LANG[data.original_lang] }, original,
      el("span", { lang: "pt-BR" }, ` ${langLabel} · ${data.total} versículos`)) : null,
    data.translations.por.length ? section("Como a Bíblia em português traduz", null, chips(data.translations.por, "pt-BR")) : null,
    data.translations.eng.length ? section("Em inglês", null, chips(data.translations.eng, "en")) : null,
    typedSection(data.lexicons.map((e) => typeOf("dictionary", e.abbr)), "Léxicos", data.lexicons.length,
      data.lexicons.length ? data.lexicons.map(lexicon) : el("p", { class: "empty" }, "Nenhum léxico legível tem este número.")),
    section("Ocorrências", data.total, data.occurrences.map(occurrence), more));
}

// --- Folhear dicionários e livros (T64) -------------------------------------------

let browseState = { module: null, letter: "", q: "" };

// Lista de dicionários e livros disponíveis, para escolher o que folhear.
function browseHome() {
  const sources = state.modules.filter((m) => m.kind === "dictionary" || m.kind === "book");
  const list = sources.map((m) => el("button", {
    class: "result", onclick: () => { browseState = { module: m.id, letter: "", q: "" }; showBrowse(); },
  }, el("div", { class: "source" }, kindTag(typeOf(m.kind, m.abbr)), el("b", {}, m.abbr),
      el("span", {}, `${m.items} itens`)),
    el("div", { class: "t clamp2" }, m.title || "")));
  openPanel("browse", "Dicionários e livros", section("Escolha uma obra", sources.length, list));
}

async function showBrowse() {
  const source = state.modules.find((m) => m.id === browseState.module);
  if (!source) return browseHome();
  const data = await api("titles", { module: source.id, letter: browseState.letter, q: browseState.q });
  const search = el("input", {
    type: "search", value: browseState.q, placeholder: "Filtrar títulos", "aria-label": "Filtrar títulos",
    class: "browse-filter",
  });
  let timer = null;
  search.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      browseState = { ...browseState, q: search.value.trim(), letter: "" };
      showBrowse();
    }, 250);
  });
  const letters = el("nav", { class: "letters", "aria-label": "Letras" },
    ["", ...data.letters].map((letter) => el("button", {
      class: "chip" + (browseState.letter === letter ? " on" : ""),
      "aria-pressed": String(browseState.letter === letter),
      onclick: () => { browseState = { ...browseState, letter, q: "" }; showBrowse(); },
    }, letter || "Todas")));
  const rows_ = data.items.map((item) => el("button", {
    class: "result browse-row", onclick: () => showItem("entry", item.id),
  }, el("div", { class: "source" }, el("b", {}, item.topic))));
  const more = data.offset + data.items.length < data.total
    ? el("button", {
        class: "more", onclick: async () => {
          const page = await api("titles", { module: source.id, letter: browseState.letter, q: browseState.q, offset: data.offset + data.items.length });
          data.items.push(...page.items);
          data.offset = page.offset;
          showBrowse();
        },
      }, `Mais títulos (${data.items.length} de ${data.total})`)
    : null;
  openPanel("browse", source.abbr, el("button", { class: "link back", onclick: browseHome }, "← Obras"),
    el("p", { class: "t browse-intro" }, source.title || ""),
    search, letters,
    section("Títulos", data.total, data.items.length ? rows_ : el("p", { class: "empty" }, "Nenhum título encontrado."), more));
}

// --- Busca ----------------------------------------------------------------------

const resultBuilders = {
  verses: (v) => el("button", {
    class: "result", onclick: () => go({ book: v.book, chapter: v.chapter, verse: v.verse }),
  }, el("div", { class: "source" }, el("b", {}, refLabel(v.book, v.chapter, v.verse))),
    el("div", { class: "t" }, highlighted(v.hit))),
  comments: (c) => el("button", {
    class: "result", onclick: () => showItem("comment", c.id),
  }, el("div", { class: "source" }, el("b", {}, c.abbr),
      el("span", {}, rangeLabel(c.book, c.ref_start, c.ref_end)), badge(c.lang)),
    el("div", { class: "t" }, highlighted(c.hit))),
  entries: (e) => el("button", {
    class: "result", onclick: () => showItem("entry", e.id),
  }, el("div", { class: "source" }, kindTag(typeOf(e.kind, e.abbr)), el("b", {}, e.topic), el("span", {}, e.abbr),
      badge(e.lang)),
    el("div", { class: "t" }, highlighted(e.hit))),
};

function searchSection(kind, title) {
  const { query, data } = state.lastSearch;
  const items = data[kind];
  const total = data.totals[kind] || 0;
  if (!items.length) return null;
  const more = items.length < total
    ? el("button", {
        class: "more",
        onclick: async () => {
          const page = await api("search", { q: query, module: state.module, kind, offset: items.length, bilingual: state.bilingual ? 1 : 0 });
          items.push(...page[kind]);
          renderSearch(true);
        },
      }, `Mais resultados (${items.length} de ${total})`)
    : null;
  return section(title, total, items.map(resultBuilders[kind]), more);
}

// Busca em duas abas: "Por palavra" (com filtros por tipo) e "Por sentido".
// Mostra só uma parte por vez, para não exigir rolagem longa (T33, ajuste de ergonomia).
function renderSearch(keepScroll = false) {
  const { query, data, semantic } = state.lastSearch;
  pendingView = { type: "search", query };
  const module = state.bibles.find((m) => m.id === state.module);
  const scroll = $("#panel-body").scrollTop;
  const mode = state.searchMode || "palavra";
  const filter = state.searchFilter || "tudo";
  const counts = {
    verses: data.totals.verses || 0,
    comments: data.totals.comments || 0,
    entries: data.totals.entries || 0,
  };
  const keyword = counts.verses + counts.comments + counts.entries;
  const meaning = semantic && semantic.available ? semantic.verses.length + semantic.comments.length : null;
  const modeTab = (id, label, n) => el("button", {
    class: "mode-tab" + (mode === id ? " on" : ""),
    onclick: () => { state.searchMode = id; renderSearch(); },
  }, label, n === null ? null : el("small", {}, ` ${n}`));
  const chip = (id, label, n) => (id === "tudo" || n) ? el("button", {
    class: "chip" + (filter === id ? " on" : ""),
    onclick: () => { state.searchFilter = id; renderSearch(); },
  }, label, el("small", {}, ` ${n}`)) : null;
  const modeBar = el("div", { class: "mode-tabs" },
    modeTab("palavra", "Por palavra", keyword),
    modeTab("sentido", "Por sentido", meaning));
  const show = (kind) => filter === "tudo" || filter === kind;
  const body = mode === "sentido"
    ? [el("p", { class: "group-note" }, "Passagens de assunto parecido, mesmo sem as palavras digitadas. A ordem vem da similaridade de sentido (modelo BGE-M3)."),
       semanticGroup(semantic)]
    : [el("p", { class: "group-note" }, "Versículos e comentários que contêm os termos digitados."),
       el("div", { class: "chips" },
         chip("tudo", "Tudo", keyword),
         chip("verses", "Versículos", counts.verses),
         chip("comments", "Comentários", counts.comments),
         chip("entries", "Dicionários e livros", counts.entries)),
       bridgeNote(query, data),
       keyword ? null : el("p", { class: "empty" }, "Nada encontrado."),
       show("verses") ? searchSection("verses", `Bíblia · ${module.abbr}`) : null,
       show("comments") ? searchSection("comments", "Comentários") : null,
       show("entries") ? searchSection("entries", "Dicionários e livros") : null];
  openPanel("search", `Busca: ${query}`, modeBar, body);
  if (keepScroll) $("#panel-body").scrollTop = scroll;
}

// Explica o que a ponte por Strong acrescentou à busca e permite desligá-la.
function bridgeNote(query, data) {
  if (!data.bridge) return null;
  const toggle = (on, label) => el("button", {
    class: "link", onclick: () => { state.bilingual = on; store.set("bilingual", on ? "1" : "0"); showSearch(query); },
  }, label);
  if (!data.bilingual) {
    return el("div", { class: "bridge" }, "Buscando só os termos digitados. ", toggle(true, "Incluir termos em inglês"));
  }
  if (!data.expansions.length) return null;
  return el("div", { class: "bridge" },
    el("div", {}, "Nos comentários e dicionários também busquei:"),
    el("ul", {}, data.expansions.map((item) => el("li", {},
      el("b", {}, item.word), " → ",
      item.terms.map((term, index) => [
        index ? ", " : null,
        el("span", { lang: "en" }, term.term),
        el("span", { class: "why", title: `A Bíblia com Strong traduz ${term.strong} assim ${term.count} vezes` },
          ` ${term.strong}`),
      ])))),
    toggle(false, "Buscar só o que digitei"));
}

async function showSearch(query) {
  const [data, semantic] = await Promise.all([
    api("search", { q: query, module: state.module, bilingual: state.bilingual ? 1 : 0 }),
    api("semantic", { q: query }).catch(() => ({ available: false, reason: "Não foi possível consultar a busca por sentido." })),
  ]);
  state.lastSearch = { query, data, semantic };
  renderSearch();
}

// Cabeçalho de grupo: deixa claro de que tipo de busca vêm os resultados abaixo (T33).
function groupHeader(title, note) {
  return el("div", { class: "search-group" },
    el("h2", { class: "group-title" }, title),
    el("p", { class: "group-note" }, note));
}

// Resultados por sentido: similaridade de embeddings, com os termos em comum quando houver.
function semanticGroup(sem) {
  if (!sem) return null;
  if (!sem.available) return [el("p", { class: "empty" }, sem.reason)];
  const why = (item) => item.shared.length
    ? `Termos em comum: ${item.shared.join(", ")}`
    : "Sem termos em comum: achado pelo sentido";
  const verses = sem.verses.map((v) => el("button", {
    class: "result", onclick: () => go({ book: v.book, chapter: v.chapter, verse: v.verse }),
  }, el("div", { class: "source" }, el("b", {}, refLabel(v.book, v.chapter, v.verse)),
      el("span", {}, `${v.abbr} · similaridade ${v.score.toFixed(2)}`)),
    el("div", { class: "t" }, v.text),
    el("div", { class: "origin" }, why(v))));
  const comments = sem.comments.map((c) => el("button", {
    class: "result", onclick: () => showItem("comment", c.id),
  }, el("div", { class: "source" }, el("b", {}, c.abbr),
      el("span", {}, rangeLabel(c.book, c.ref_start, c.ref_end)), badge(c.lang),
      el("span", {}, `similaridade ${c.score.toFixed(2)}`)),
    el("div", { class: "t" }, c.excerpt),
    el("div", { class: "origin" }, why(c))));
  return [
    section("Versículos", verses.length, verses),
    section("Comentários", comments.length, comments),
  ];
}

// --- Aparência ------------------------------------------------------------------

function setFontSize(size) {
  const clamped = Math.min(30, Math.max(15, size));
  document.documentElement.style.setProperty("--reading-size", clamped + "px");
  store.set("fontSize", clamped);
  return clamped;
}

function toggleTheme() {
  const root = document.documentElement;
  const dark = root.dataset.theme
    ? root.dataset.theme === "dark"
    : matchMedia("(prefers-color-scheme: dark)").matches;
  root.dataset.theme = dark ? "light" : "dark";
  store.set("theme", root.dataset.theme);
}

// --- Início ---------------------------------------------------------------------

async function init() {
  const library = await api("library");
  state.modules = library.modules;
  state.books = library.books;
  state.bibles = library.modules.filter((m) => m.kind === "bible");
  if (!state.bibles.length) {
    $("#text").replaceChildren(el("p", { class: "empty" }, "Nenhuma Bíblia importada."));
    return;
  }

  // Versões agrupadas por idioma, português primeiro.
  const languages = [...new Set(state.bibles.map((m) => m.lang))];
  $("#version").replaceChildren(...languages.map((lang) =>
    el("optgroup", { label: LANG_NAME[lang] || lang },
      state.bibles.filter((m) => m.lang === lang).map((m) => el("option", { value: m.id, title: m.title }, m.abbr)))));
  $("#book").replaceChildren(...state.books.map((b) => el("option", { value: b.book }, b.name)));

  const saved = Number(store.get("module"));
  state.module = state.bibles.some((m) => m.id === saved) ? saved : state.bibles[0].id;
  const savedFilter = store.get("langFilter");
  if (["all", "por", "other"].includes(savedFilter)) state.langFilter = savedFilter;
  state.bilingual = store.get("bilingual") !== "0";
  state.words = store.get("words") === "1";
  state.parallel = store.get("parallel") === "1";
  try { state.parallelIds = JSON.parse(store.get("parallelIds") || "[]"); } catch { state.parallelIds = []; }
  let fontSize = setFontSize(Number(store.get("fontSize")) || 20);
  readHash();

  $("#version").addEventListener("change", (e) => {
    store.set("module", e.target.value);
    go({ module: Number(e.target.value) });
  });
  $("#book").addEventListener("change", (e) => go({ book: Number(e.target.value), chapter: 1, verse: null }));
  $("#chapter").addEventListener("change", (e) => go({ chapter: Number(e.target.value), verse: null }));
  $("#prev").addEventListener("click", () => step(-1));
  $("#next").addEventListener("click", () => step(1));
  $("#smaller").addEventListener("click", () => { fontSize = setFontSize(fontSize - 1); });
  $("#larger").addEventListener("click", () => { fontSize = setFontSize(fontSize + 1); });
  $("#theme").addEventListener("click", toggleTheme);
  $("#browse").addEventListener("click", () => {
    if (browseState.module) showBrowse(); else browseHome();
  });
  $("#parallel").addEventListener("click", () => {
    state.parallel = !state.parallel;
    store.set("parallel", state.parallel ? "1" : "0");
    render();
  });
  $("#words").addEventListener("click", () => {
    state.words = !state.words;
    store.set("words", state.words ? "1" : "0");
    render();
  });
  $("#panel-pin").addEventListener("click", pinCurrent);
  $("#show-pins").addEventListener("click", () => layout.showPinned(true));
  setupSplitter($("#split-panel"), "#panel", "panelWidth");
  setupSplitter($("#split-pinned"), "#pinned", "pinnedWidth");
  window.addEventListener("resize", () => layout.applyWidths());
  $("#panel-close").addEventListener("click", () => {
    state.lastSearch = null;
    closePanel();
    if (state.verse) go({ verse: null });
  });
  $("#search").addEventListener("submit", (e) => {
    e.preventDefault();
    const query = $("#q").value.trim();
    if (!query) return;
    const reference = parseReference(query);
    if (reference) go(reference);
    else showSearch(query);
  });
  $("#text").addEventListener("keydown", (e) => {
    if ((e.key === "Enter" || e.key === " ") && e.target.classList.contains("v")) {
      e.preventDefault();
      go({ verse: Number(e.target.dataset.verse) });
    }
  });
  window.addEventListener("hashchange", () => { readHash(); render(); });

  render();
  layout.applyWidths();
  await restorePins();
}

function openGraphFull(center) {
  const label = (b, c, v) => `${bookOf(b).abbr} ${c}:${v}`;
  // Altura ajustada à janela: o grafo e a legenda cabem sem rolar.
  const width = Math.min(innerWidth - 32, 1200);
  const aspect = Math.min(0.85, Math.max(0.45, (innerHeight - 200) / width));
  $("#graph-full-title").textContent = `Referências de ${label(center.book, center.chapter, center.verse)}`;
  $("#graph-full-body").replaceChildren(xrefGraph(center, {
    api, label,
    preview: showPreview,
    hidePreview,
    open: (ref) => { closeGraphFull(); go(ref); },
    maxWidth: 1200, aspect, full: true,
  }));
  $("#graph-full").hidden = false;
  $("#graph-full-close").focus();
}

function closeGraphFull() {
  hidePreview();
  $("#graph-full").hidden = true;
  $("#graph-full-body").replaceChildren();
}

function showToast(message) {
  const box = $("#toast");
  if (!box) return;
  box.textContent = message;
  box.hidden = false;
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => { box.hidden = true; }, 6000);
}

$("#graph-full-close").addEventListener("click", closeGraphFull);

// --- Minhas notas (T40): gravadas só em data/user.db pelo servidor --------------
let editingNoteId = null;

async function userWrite(action, body) {
  const response = await fetch(`/api/user/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `erro ${response.status}`);
  return data;
}

function notesTab(book, chapter, verse, notes) {
  const fail = (error) => showToast(`Não foi possível salvar: ${error.message}`);
  const input = el("textarea", { class: "note-input", rows: 4, "aria-label": "Nova nota sobre o versículo",
    placeholder: "Escreva sobre este versículo: o que ele diz, o que você percebe, perguntas." });
  const save = el("button", { class: "chip on", onclick: async () => {
    const text = input.value.trim();
    if (!text) return;
    try { await userWrite("note/create", { book, chapter, verse, body: text }); showVerse(); } catch (error) { fail(error); }
  } }, "Salvar nota");
  const rows = notes.map((note) => {
    if (editingNoteId === note.id) {
      const edit = el("textarea", { class: "note-input", rows: 5, "aria-label": "Editar nota" });
      edit.value = note.body;
      return el("div", { class: "note" }, edit,
        el("div", { class: "note-actions" },
          el("button", { class: "chip on", onclick: async () => {
            try { await userWrite("note/update", { id: note.id, body: edit.value }); editingNoteId = null; showVerse(); } catch (error) { fail(error); }
          } }, "Salvar"),
          el("button", { class: "link", onclick: () => { editingNoteId = null; showVerse(); } }, "Cancelar")));
    }
    return el("div", { class: "note" },
      el("div", { class: "note-body" }, note.body),
      el("div", { class: "note-meta" }, note.updated_at.replace("T", " ")),
      el("div", { class: "note-actions" },
        el("button", { class: "link", onclick: () => { editingNoteId = note.id; showVerse(); } }, "Editar"),
        el("button", { class: "link", onclick: async () => {
          if (!confirm("Mover esta nota para a lixeira?")) return;
          try { await userWrite("note/delete", { id: note.id }); showVerse(); } catch (error) { fail(error); }
        } }, "Apagar")));
  });
  return [
    el("div", { class: "note-new" }, input, el("div", { class: "note-actions" }, save)),
    rows.length ? rows : el("p", { class: "empty" }, "Nenhuma nota neste versículo ainda."),
    el("p", { class: "group-note" }, el("a", { href: "/api/user/export", class: "link" }, "Exportar todas as notas (Markdown)")),
  ];
}

// --- Pesquisa por tema (sem IA): só texto bíblico --------------------------------
function markedText(text) {
  // O servidor marca o termo com [[ e ]]; aqui vira <mark>, sem usar HTML do texto.
  return String(text).split(/\[\[|\]\]/).map((part, i) => (i % 2 ? el("mark", {}, part) : part));
}

function openTopics(query = "") {
  $("#topic-q").value = query;
  $("#topic-full").hidden = false;
  $("#topic-q").focus();
  if (query) runTopic(query);
}

function closeTopics() {
  $("#topic-full").hidden = true;
}

async function runTopic(query) {
  const body = $("#topic-body");
  body.replaceChildren(el("p", { class: "empty" }, "Pesquisando…"));
  const data = await api("topic", { q: query, module: state.module });
  const verseRow = (v, text, why) => el("button", {
    class: "result", onclick: () => { closeTopics(); go({ book: v.book, chapter: v.chapter, verse: v.verse }); },
  }, el("div", { class: "source" }, el("b", {}, refLabel(v.book, v.chapter, v.verse)), el("span", {}, v.abbr)),
    el("div", { class: "t" }, text),
    why ? el("div", { class: "origin" }, why) : null);
  const literal = data.literal.map((v) => verseRow(v, markedText(v.hit)));
  const meaning = data.meaning.map((v) => verseRow(v, v.text,
    v.shared.length ? `Termos em comum: ${v.shared.join(", ")}` : "Sem termos em comum: achado pelo sentido"));
  body.replaceChildren(...[
    el("h2", {}, "Com o termo"),
    el("p", { class: "group-note" }, `Versículos que contêm "${data.query}"${data.literal.length >= 60 ? " (os primeiros 60)" : ""}.`),
    literal.length ? literal : el("p", { class: "empty" }, "Nenhum versículo contém este termo nesta versão."),
    el("h2", {}, "Sobre o assunto"),
    el("p", { class: "group-note" }, data.semantic
      ? "Versículos de sentido parecido, mesmo sem a palavra. Ordem pela proximidade de sentido (texto ARA1993+)."
      : (data.reason || "Busca por sentido indisponível.")),
    data.semantic ? meaning : null].flat(Infinity).filter(Boolean));
}

$("#topic-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const query = $("#topic-q").value.trim();
  if (query) runTopic(query);
});
$("#topic-close").addEventListener("click", closeTopics);
$("#topics").addEventListener("click", () => openTopics());

// --- Atalhos de teclado (D2): só fora de campos de texto; Esc vale sempre ----------

const SHORTCUTS = [
  ["/", "buscar"],
  ["[ e ]", "capítulo anterior e seguinte"],
  ["j e k", "versículo seguinte e anterior"],
  ["f", "fixar o que o painel mostra"],
  ["p", "liga ou desliga o paralelo"],
  ["Esc", "fecha a prévia ou o painel"],
  ["?", "mostra esta lista"],
];

function showShortcuts() {
  openPanel("help", "Atalhos de teclado",
    el("dl", { class: "shortcuts" }, SHORTCUTS.flatMap(([keys, action]) => [
      el("dt", {}, el("kbd", {}, keys)), el("dd", {}, action),
    ])));
}

function moveVerse(delta) {
  const count = bookOf(state.book).chapters[state.chapter - 1];
  const next = state.verse ? state.verse + delta : (delta > 0 ? 1 : count);
  if (next < 1 || next > count) return;
  go({ verse: next });
}

document.addEventListener("keydown", (event) => {
  if (event.ctrlKey || event.metaKey || event.altKey) return;
  const typing = event.target.closest?.("input, textarea, select, [contenteditable]");
  if (event.key === "Escape") {
    if (!$("#topic-full").hidden) closeTopics();
    else if (!$("#graph-full").hidden) closeGraphFull();
    else if (!$("#preview").hidden) hidePreview();
    else if (!$("#panel").hidden) $("#panel-close").click();
    return;
  }
  if (typing) return;
  const keys = {
    "/": () => $("#q").focus(),
    "[": () => step(-1),
    "]": () => step(1),
    j: () => moveVerse(1),
    k: () => moveVerse(-1),
    p: () => $("#parallel").click(),
    f: () => { if (currentView) pinCurrent(); },
    "?": showShortcuts,
  };
  const action = keys[event.key];
  if (!action) return;
  event.preventDefault();
  action();
});

window.addEventListener("unhandledrejection", (event) => {
  console.error(event.reason);
  showToast("Não foi possível concluir a ação. Verifique se o servidor da biblioteca está rodando.");
});

init().catch((error) => {
  console.error(error);
  $("#text").replaceChildren(el("p", { class: "empty" }, "Não foi possível carregar a biblioteca."));
});
