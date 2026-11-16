const $ = (selector) => document.querySelector(selector);

const state = {
  modules: [], bibles: [], books: [],
  module: null, book: 43, chapter: 1, verse: null,
};

// --- Utilitários --------------------------------------------------------------

async function api(endpoint, params = {}) {
  const response = await fetch(`/api/${endpoint}?${new URLSearchParams(params)}`);
  if (!response.ok) throw new Error(`${endpoint}: ${response.status}`);
  return response.json();
}

function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === "class") node.className = value;
    else if (key === "onclick") node.addEventListener("click", value);
    else if (value !== null && value !== undefined) node.setAttribute(key, value);
  }
  node.append(...children.filter((child) => child !== null && child !== undefined));
  return node;
}

const store = {
  get(key) { try { return localStorage.getItem(key); } catch { return null; } },
  set(key, value) { try { localStorage.setItem(key, value); } catch { /* sem armazenamento */ } },
};

const bookOf = (number) => state.books[number - 1];
const LANG = { por: "pt-BR", eng: "en", spa: "es", grc: "grc", heb: "heb" };
const LANG_LABEL = { por: "PT", eng: "EN", spa: "ES", grc: "GR", heb: "HE" };

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

  const { verses } = await api("chapter", { module: state.module, book: state.book, chapter: state.chapter });
  if (token !== renderToken) return; // navegação mais nova já em andamento

  document.title = `${refLabel(state.book, state.chapter)} · ${module.abbr}`;
  $("#kicker").textContent = module.title || module.abbr;
  $("#title").textContent = refLabel(state.book, state.chapter);
  const text = $("#text");
  text.lang = LANG[module.lang] || "";
  if (!verses.length) {
    text.replaceChildren(el("p", { class: "empty" }, `${module.abbr} não contém este capítulo.`));
  } else {
    text.replaceChildren(...verses.flatMap((v) => [
      el("span", {
        class: "v" + (v.verse === state.verse ? " selected" : ""), "data-verse": v.verse,
        role: "button", tabindex: "0", onclick: () => go({ verse: v.verse }),
      }, el("sup", {}, String(v.verse)), v.text),
      " ",
    ]));
  }
  $("#hint").hidden = Boolean(state.verse) || !verses.length;

  if (state.verse) {
    text.querySelector(".selected")?.scrollIntoView({ block: "center" });
    showVerse();
  } else if (panelMode === "verse") {
    closePanel();
  }
  if (!state.verse) $("#reader").scrollTop = 0;
}

// --- Painel ---------------------------------------------------------------------

let panelMode = null; // 'verse' | 'search' | 'item'

function openPanel(mode, title, ...content) {
  panelMode = mode;
  $("#panel-title").textContent = title;
  $("#panel-body").replaceChildren(...content);
  $("#panel-body").scrollTop = 0;
  $("#panel").hidden = false;
}

function closePanel() {
  panelMode = null;
  $("#panel").hidden = true;
}

function badge(lang) {
  return lang && lang !== "por" ? el("span", { class: "badge" }, LANG_LABEL[lang] || lang) : null;
}

function section(title, count, ...content) {
  return [el("h3", {}, title + " ", el("small", {}, count === null ? "" : `(${count})`)), ...content];
}

function clampable(text, lang) {
  const body = el("div", { class: "t clamp", lang: LANG[lang] || null }, text);
  const item = [body];
  if (text.length > 420) {
    const toggle = el("button", { class: "link", onclick: () => {
      const open = body.classList.toggle("clamp");
      toggle.textContent = open ? "Ler tudo" : "Recolher";
    } }, "Ler tudo");
    item.push(toggle);
  } else {
    body.classList.remove("clamp");
  }
  return item;
}

async function showVerse() {
  const { book, chapter, verse } = state;
  const data = await api("verse", { book, chapter, verse });
  if (book !== state.book || chapter !== state.chapter || verse !== state.verse) return;

  const versions = data.versions.map((v) => el("div", { class: "item", lang: LANG[v.lang] || null },
    el("div", { class: "source" },
      v.module_id === state.module
        ? el("b", {}, v.abbr)
        : el("button", { class: "link", title: "Ler nesta versão", onclick: () => go({ module: v.module_id }) }, v.abbr),
      badge(v.lang)),
    el("div", { class: "t" }, v.text)));

  const comments = data.comments.map((c) => el("div", { class: "item" },
    el("div", { class: "source" }, el("b", {}, c.abbr),
      el("span", {}, rangeLabel(book, c.ref_start, c.ref_end)), badge(c.lang)),
    ...clampable(c.text, c.lang)));

  const cited = data.cited.map((c) => el("button", {
    class: "chip", title: c.abbr, onclick: () => showItem(c.kind, c.id),
  }, c.kind === "entry" ? c.label : `${c.abbr}: ${itemRef(c.label)}`));

  openPanel("verse", refLabel(book, chapter, verse),
    ...section("Versões", versions.length, ...versions),
    ...section("Comentários", comments.length,
      ...(comments.length ? comments : [el("p", { class: "empty" }, "Nenhum comentário cobre este versículo.")])),
    ...(cited.length ? section("Citado em", cited.length, el("div", { class: "chips" }, ...cited)) : []));
}

// "43.3001" (livro.ref) -> "Jo 3:1"
function itemRef(label) {
  const [book, start] = label.split(".").map(Number);
  return rangeLabel(book, start, start);
}

async function showItem(kind, id) {
  const item = await api("item", { kind, id });
  if (!item) return;
  const title = kind === "entry" ? item.label : rangeLabel(item.book, item.ref_start, item.ref_end);
  const back = state.verse
    ? el("button", { class: "link", onclick: showVerse }, `← ${refLabel(state.book, state.chapter, state.verse)}`)
    : null;
  openPanel("item", title,
    el("div", { class: "item" },
      el("div", { class: "source" }, el("b", {}, item.abbr), el("span", {}, item.title || ""), badge(item.lang)),
      el("div", { class: "t", lang: LANG[item.lang] || null }, item.text),
      el("div", { class: "origin" }, `Origem: ${item.origin_path} · ${item.origin_key}`)),
    back);
}

async function showSearch(query) {
  const data = await api("search", { q: query, module: state.module });
  const module = state.bibles.find((m) => m.id === state.module);

  const verses = data.verses.map((v) => el("button", {
    class: "result", onclick: () => go({ book: v.book, chapter: v.chapter, verse: v.verse }),
  }, el("div", { class: "source" }, el("b", {}, refLabel(v.book, v.chapter, v.verse))),
    el("div", { class: "t" }, highlighted(v.hit))));

  const comments = data.comments.map((c) => el("button", {
    class: "result", onclick: () => showItem("comment", c.id),
  }, el("div", { class: "source" }, el("b", {}, c.abbr),
      el("span", {}, rangeLabel(c.book, c.ref_start, c.ref_end)), badge(c.lang)),
    el("div", { class: "t" }, highlighted(c.hit))));

  const entries = data.entries.map((e) => el("button", {
    class: "result", onclick: () => showItem("entry", e.id),
  }, el("div", { class: "source" }, el("b", {}, e.topic), el("span", {}, e.abbr), badge(e.lang)),
    el("div", { class: "t" }, highlighted(e.hit))));

  const shown = (list, total) => (total > list.length ? `${list.length} de ${total}` : String(total ?? 0));
  const total = (data.totals.verses || 0) + (data.totals.comments || 0) + (data.totals.entries || 0);
  openPanel("search", `Busca: ${query}`,
    ...(total ? [] : [el("p", { class: "empty" }, "Nada encontrado.")]),
    ...(verses.length ? section(`Bíblia · ${module.abbr}`, shown(verses, data.totals.verses), ...verses) : []),
    ...(comments.length ? section("Comentários", shown(comments, data.totals.comments), ...comments) : []),
    ...(entries.length ? section("Dicionários", shown(entries, data.totals.entries), ...entries) : []));
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

  $("#version").replaceChildren(...state.bibles.map((m) =>
    el("option", { value: m.id, title: m.title }, m.abbr)));
  $("#book").replaceChildren(...state.books.map((b) => el("option", { value: b.book }, b.name)));

  const saved = Number(store.get("module"));
  state.module = state.bibles.some((m) => m.id === saved) ? saved : state.bibles[0].id;
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
  $("#panel-close").addEventListener("click", () => {
    if (panelMode === "verse" || state.verse) go({ verse: null });
    closePanel();
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
}

init().catch((error) => {
  console.error(error);
  $("#text").replaceChildren(el("p", { class: "empty" }, "Não foi possível carregar a biblioteca."));
});
