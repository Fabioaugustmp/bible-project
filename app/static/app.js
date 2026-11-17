import { xrefGraph } from "./graph.js";

const $ = (selector) => document.querySelector(selector);

const state = {
  modules: [], bibles: [], books: [],
  module: null, book: 43, chapter: 1, verse: null,
  langFilter: "all",   // 'all' | 'por' | 'other': filtra comentários e citações no painel
  lastSearch: null,    // { query, data }: permite voltar aos resultados
  bilingual: true,     // ponte por Strong na busca (T23)
  words: false,        // modo palavras: clicar abre o termo original (T20)
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
    else if (key === "onclick") node.addEventListener("click", value);
    else if (key === "ontoggle") node.addEventListener("toggle", value);
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
  if (!sameChapter) {
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
    if (!state.verse) $("#reader").scrollTop = 0;
  }

  // Seleção: só troca a marca, sem redesenhar o capítulo.
  text.querySelector(".v.selected")?.classList.remove("selected");
  const selected = state.verse ? text.querySelector(`.v[data-verse="${state.verse}"]`) : null;
  if (selected) {
    selected.classList.add("selected");
    if (!sameChapter) selected.scrollIntoView({ block: "center" });
    $("#hint").hidden = true;
    showVerse();
  } else if (panelMode === "verse") {
    closePanel();
  }
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
        "Fixar ao lado")));
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

async function showVerse(ref = null) {
  const { book, chapter, verse } = ref || state;
  const verseKey = `${book}.${chapter}.${verse}`;
  if (verseKey !== xrefVerse) { xrefVerse = verseKey; xrefLimit = 12; }
  const data = await api("verse", { book, chapter, verse, module: state.module, xrefs: xrefLimit });
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
  const xrefSwitch = graphFits
    ? el("div", { class: "filters xref-switch", role: "group", "aria-label": "Mostrar referências como" },
        [["list", "Lista"], ["graph", "Grafo"]].map(([value, text]) => el("button", {
          class: "chip" + (xrefMode === value ? " on" : ""), "aria-pressed": String(xrefMode === value),
          onclick: () => { store.set("xrefView", value); showVerse(); },
        }, text)))
    : null;
  const graph = xrefMode === "graph"
    ? xrefGraph({ book, chapter, verse }, {
        api,
        label: (b, c, v) => `${bookOf(b).abbr} ${c}:${v}`,
        preview: showPreview,
        hidePreview,
        open: (ref) => go(ref),
      })
    : null;
  const moreXrefs = data.xrefs.length < data.xrefs_total && data.xrefs.length < 60
    ? el("button", {
        class: "more", onclick: () => { xrefLimit = Math.min(60, xrefLimit + 24); showVerse(); },
      }, `Mais referências (${data.xrefs.length} de ${data.xrefs_total})`)
    : null;

  const comments = data.comments.filter((c) => passesFilter(c.lang));
  const cited = data.cited.filter((c) => passesFilter(c.lang));
  const citedTotal = cited.reduce((sum, group) => sum + group.count, 0);
  const of = (visible, all) => (visible.length === all.length ? String(all.length) : `${visible.length} de ${all.length}`);

  // Atalhos para as seções: com a biblioteca inteira o painel fica longo.
  const jump = (label, title) => el("button", {
    class: "chip", onclick: () => {
      const heading = [...document.querySelectorAll("#panel-body h3")].find((h) => h.textContent.startsWith(title));
      heading?.scrollIntoView({ block: "start", behavior: "smooth" });
    },
  }, label);
  const jumps = el("nav", { class: "jumps", "aria-label": "Seções do painel" },
    data.xrefs.length ? jump(`Referências ${data.xrefs_total}`, "Referências cruzadas") : null,
    jump(`Comentários ${data.comments.length}`, "Comentários"),
    data.cited.length ? jump(`Citado em ${data.cited.reduce((sum, g) => sum + g.count, 0)}`, "Citado em") : null);

  openPanel("verse", refLabel(book, chapter, verse),
    backToSearch(),
    jumps,
    typedSection(["bible"], "Versões", data.versions.length,
      native.map(versionItem),
      foreign.length
        ? el("details", { class: "fold plain", open: native.length === 0 },
            el("summary", {}, el("b", {}, `Outros idiomas (${foreign.length})`),
              el("span", { class: "range" }, foreign.map((v) => v.abbr).join(" · "))),
            foreign.map(versionItem))
        : null),
    data.xrefs.length
      ? typedSection(["xref"], "Referências cruzadas", data.xrefs_total, xrefSwitch,
          graph || [xrefs, moreXrefs])
      : null,
    filterBar(showVerse),
    typedSection(["commentary"], "Comentários", of(comments, data.comments),
      comments.length ? comments.map((c) => commentRow(book, c))
        : el("p", { class: "empty" }, data.comments.length ? "Nenhum neste idioma." : "Nenhum comentário cobre este versículo.")),
    data.cited.length
      ? typedSection(cited.map((g) => itemType(g.kind, g.abbr, g.module_id)), "Citado em",
          `${citedTotal} em ${cited.length} obras`, cited.map(citedGroup))
      : null);
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

function renderSearch(keepScroll = false) {
  const { query, data } = state.lastSearch;
  pendingView = { type: "search", query };
  const module = state.bibles.find((m) => m.id === state.module);
  const scroll = $("#panel-body").scrollTop;
  const total = Object.values(data.totals).reduce((sum, n) => sum + n, 0);
  openPanel("search", `Busca: ${query}`,
    bridgeNote(query, data),
    total ? null : el("p", { class: "empty" }, "Nada encontrado."),
    searchSection("verses", `Bíblia · ${module.abbr}`),
    searchSection("comments", "Comentários"),
    searchSection("entries", "Dicionários e livros"));
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
  const data = await api("search", { q: query, module: state.module, bilingual: state.bilingual ? 1 : 0 });
  state.lastSearch = { query, data };
  renderSearch();
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

init().catch((error) => {
  console.error(error);
  $("#text").replaceChildren(el("p", { class: "empty" }, "Não foi possível carregar a biblioteca."));
});
