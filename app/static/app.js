import { xrefGraph, layout as graphLayout } from "./graph.js";

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

// Celular (D036): até 560 px, a navegação usa cabeçalho de uma linha, barra inferior e folhas.
const phoneQuery = matchMedia("(max-width: 560px)");
const isPhone = () => phoneQuery.matches;
// Tela de toque: "Toque" em vez de "Clique" nos textos de ajuda.
const touch = matchMedia("(pointer: coarse)").matches;
const TAP = touch ? "Toque" : "Clique";
const tap = TAP.toLowerCase();

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

// --- Seleção de versículos (sugestão 2 do agente Opus): toque no primeiro e no último ---
let chapterVerses = [];                                  // versículos do capítulo aberto
const selection = { on: false, start: null, end: null }; // só existe no capítulo normal
const MAX_SELECTION_STUDY = 40;                          // cada versículo vira um bloco do estudo

// --- Continuar de onde parou (T92): última leitura e último estudo, só no navegador ---
function readStored(key) {
  try { return JSON.parse(store.get(key) || "null"); } catch { return null; }
}

// Ao abrir sem endereço (#/...), oferece a última leitura e o último estudo.
function resumeInfo() {
  const read = readStored("ultimaLeitura");
  const study = readStored("ultimoEstudo");
  if (!read && !study) return null;
  return { read, study };
}

function showResume(info) {
  const box = $("#resume");
  const hide = () => { box.hidden = true; };
  // Celular (D036): uma linha só com a última leitura; o último estudo fica na folha Estudo.
  if (isPhone()) {
    if (!info.read) return;
    const module = state.bibles.some((m) => m.id === info.read.module) ? info.read.module : state.module;
    box.replaceChildren(el("div", { class: "resume-row" },
      el("span", { class: "resume-text" }, `Continuar: ${refLabel(info.read.book, info.read.chapter, info.read.verse)}`),
      el("button", { class: "chip on", onclick: () => { hide(); go({ ...info.read, module }); } }, "Abrir")),
      el("button", { class: "link resume-close", "aria-label": "Fechar", onclick: hide }, "×"));
    box.hidden = false;
    return;
  }
  const items = [];
  if (info.read) {
    const module = state.bibles.some((m) => m.id === info.read.module) ? info.read.module : state.module;
    items.push(el("span", {}, `Última leitura: ${refLabel(info.read.book, info.read.chapter, info.read.verse)}`),
      el("button", { class: "chip on", onclick: () => { hide(); go({ ...info.read, module }); } }, "Abrir"));
  }
  if (info.study) {
    items.push(el("span", {}, `Último estudo: ${info.study.title}`),
      el("button", { class: "chip", onclick: () => { hide(); openStudies(info.study.id); } }, "Abrir estudo"));
  }
  box.replaceChildren(el("div", { class: "resume-row" }, el("strong", {}, "Continuar de onde parou"), ...items),
    el("button", { class: "link resume-close", "aria-label": "Fechar", onclick: hide }, "×"));
  box.hidden = false;
}

function saveLastRead() {
  store.set("ultimaLeitura", JSON.stringify({ module: state.module, book: state.book, chapter: state.chapter, verse: state.verse }));
}

async function render() {
  const token = ++renderToken;
  if (location.hash) saveLastRead();   // a abertura sem endereço não apaga a última leitura
  const module = state.bibles.find((m) => m.id === state.module);
  $("#version").value = state.module;
  $("#book").value = state.book;
  const chapters = bookOf(state.book).chapters.length;
  $("#chapter").replaceChildren(
    ...Array.from({ length: chapters }, (_, i) => el("option", { value: i + 1 }, String(i + 1))));
  $("#chapter").value = state.chapter;
  $("#prev").disabled = $("#b-prev").disabled = state.book === 1 && state.chapter === 1;
  $("#next").disabled = $("#b-next").disabled = state.book === state.books.length && state.chapter === chapters;
  $("#passage").textContent = refLabel(state.book, state.chapter);

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
    const marks = await api("user/marks", { book: state.book, chapter: state.chapter }).catch(() => ({ notes: {}, studies: {} }));
    shown = { module: state.module, book: state.book, chapter: state.chapter, words: state.words };
    chapterVerses = verses;
    selection.start = selection.end = null;   // outro capítulo: a seleção antiga não vale
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
          class: "v" + (marks.notes[v.verse] ? " has-note" : "") + (marks.studies[v.verse] ? " has-study" : ""),
          "data-verse": v.verse, role: "button", tabindex: "0",
          title: [marks.notes[v.verse] ? `${marks.notes[v.verse]} nota(s)` : null,
            marks.studies[v.verse] ? `em ${marks.studies[v.verse]} estudo(s)` : null].filter(Boolean).join(" · ") || null,
          onclick: (event) => {
            if (selection.on) { tapVerse(v.verse); return; }
            const word = event.target.closest(".w");
            if (word && state.words) {
              event.stopPropagation();
              showWord(word.dataset.strong.split(" ")[0], word);
            } else {
              if (marks.notes[v.verse]) pendingTab = "notas";
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
    if (isPhone()) revealAboveSheet(selected, sameChapter ? "smooth" : "auto");
    else if (!sameChapter) selected.scrollIntoView({ block: "center" });
    $("#hint").hidden = true;
    showVerse();
  } else if (panelMode === "verse") {
    closePanel();
  }
  applySelection();
}

// Celular (D036): a folha ocupa a parte de baixo; o versículo aberto sobe para a parte
// visível acima dela, em vez de ficar escondido atrás.
function revealAboveSheet(node, behavior = "smooth") {
  document.body.classList.add("sheet-open");   // dá ao texto espaço para rolar acima da folha
  setSheetTall(false);
  const reader = $("#reader");
  const box = reader.getBoundingClientRect();
  const sheetTop = box.bottom - innerHeight * 0.6;
  const rect = node.getBoundingClientRect();
  if (rect.top >= box.top + 8 && rect.bottom <= sheetTop - 8) return;   // já está à vista
  reader.scrollTo({ top: reader.scrollTop + rect.top - box.top - 12, behavior });
}

// --- Seleção de versículos: funções ------------------------------------------------

function tapVerse(verse) {
  if (selection.start === null || selection.end !== null) { selection.start = verse; selection.end = null; }
  else selection.end = verse;
  applySelection();
}

function selectedRange() {
  if (selection.start === null) return null;
  const a = selection.start, b = selection.end ?? selection.start;
  return { from: Math.min(a, b), to: Math.max(a, b) };
}

function applySelection() {
  const range = selection.on ? selectedRange() : null;
  document.body.classList.toggle("selecting", selection.on);
  $("#select").setAttribute("aria-pressed", String(selection.on));
  document.querySelectorAll("#text .v").forEach((node) => {
    const n = Number(node.dataset.verse);
    node.classList.toggle("in-range", !!range && n >= range.from && n <= range.to);
  });
  renderSelBar(range);
}

function setSelectMode(on) {
  selection.on = on;
  selection.start = selection.end = null;
  if (on && state.parallel) { state.parallel = false; store.set("parallel", "0"); render(); return; }
  applySelection();
}

function renderSelBar(range) {
  const bar = $("#selbar");
  bar.hidden = !selection.on;
  if (!selection.on) { bar.replaceChildren(); return; }
  if (!range) {
    bar.replaceChildren(el("span", { class: "selbar-label" }, "Toque no primeiro versículo e depois no último."),
      el("button", { class: "link", onclick: () => setSelectMode(false) }, "Sair da seleção"));
    return;
  }
  const count = range.to - range.from + 1;
  const label = refLabel(state.book, state.chapter, range.from) + (count > 1 ? `–${range.to}` : "");
  bar.replaceChildren(
    el("span", { class: "selbar-label" }, `${label} · ${count} ${count > 1 ? "versículos" : "versículo"}`),
    el("button", { class: "chip", onclick: () => copyRange(range) }, "Copiar com referência"),
    el("button", { class: "chip", onclick: () => addRangeToStudy(range) }, "Adicionar ao estudo"),
    el("button", { class: "chip", onclick: () => annotateRange(range) }, "Anotar"),
    el("button", { class: "link", onclick: () => setSelectMode(false) }, "Sair da seleção"));
}

async function copyRange(range) {
  const verses = chapterVerses.filter((v) => v.verse >= range.from && v.verse <= range.to);
  const module = state.bibles.find((m) => m.id === state.module);
  const head = refLabel(state.book, state.chapter, range.from) + (range.to > range.from ? `–${range.to}` : "") + ` (${module.abbr})`;
  const text = [head, ...verses.map((v) => `${v.verse} ${v.text}`)].join("\n");
  try {
    await navigator.clipboard.writeText(text);
    showToast(`${verses.length} versículo(s) copiados com a referência.`);
  } catch (error) {
    showToast("Não foi possível copiar neste navegador.");
  }
}

// Um bloco de passagem por versículo (o esquema do estudo guarda um versículo por bloco).
async function addRangeToStudy(range) {
  const numbers = Array.from({ length: range.to - range.from + 1 }, (_, i) => range.from + i);
  if (numbers.length > MAX_SELECTION_STUDY) { showToast(`Seleção grande demais: máximo de ${MAX_SELECTION_STUDY} versículos por vez.`); return; }
  const { book, chapter } = state;
  const added = await addPassagesToStudy(numbers.map((verse) => ({ book, chapter, verse })));
  if (added) setSelectMode(false);
}

// Adiciona passagens (uma por bloco) ao estudo mais recente, ou cria um estudo com a primeira.
// Devolve true se deu certo.
async function addPassagesToStudy(passages, note = "") {
  if (!passages.length) { showToast("Não há versículos para adicionar."); return false; }
  try {
    const data = await api("user/studies");
    let studyId, title, todo = passages;
    if (data.studies.length) {
      studyId = data.studies[0].id;
      title = data.studies[0].title;
    } else {
      const first = passages[0];
      const name = `Estudo: ${refLabel(first.book, first.chapter, first.verse)}`;
      const made = await userWrite("study/create", { title: name, book: first.book, chapter: first.chapter, verse: first.verse });
      studyId = made.id;
      title = name;
      todo = passages.slice(1);   // o estudo novo já tem a primeira passagem
    }
    for (const p of todo) await userWrite("block/add", { study_id: studyId, kind: "passagem", book: p.book, chapter: p.chapter, verse: p.verse });
    showToast(`${passages.length} passagem(ns) adicionada(s) a «${title}»${note}`);
    return true;
  } catch (error) {
    showToast(`Não foi possível adicionar: ${error.message}`);
    return false;
  }
}

// Adiciona à mesma lista de estudo os versículos da busca exibida (T97).
function addSearchToStudy() {
  const verses = (state.lastSearch && state.lastSearch.data && state.lastSearch.data.verses) || [];
  addPassagesToStudy(verses.map((v) => ({ book: v.book, chapter: v.chapter, verse: v.verse })), partialSearchNote(verses.length));
}

// A busca devolve no máximo 60 versículos por vez; avisa quando há mais no total.
function partialSearchNote(shown) {
  const total = (state.lastSearch && state.lastSearch.data && state.lastSearch.data.totals && state.lastSearch.data.totals.verses) || 0;
  return total > shown ? ` (só os primeiros ${shown} de ${total})` : "";
}

// Anotar: as notas são de um versículo, então abre "Minhas notas" do primeiro da seleção.
function annotateRange(range) {
  setSelectMode(false);
  pendingTab = "notas";
  go({ verse: range.from });
}

// --- Versões em paralelo (T62) -----------------------------------------------------

const MAX_COLUMNS = 4;

// Versões escolhidas para o paralelo: as guardadas (só as que existem); sem escolha guardada,
// a aberta e uma segunda, do mesmo idioma quando houver (T83: o botão já mostra a comparação).
function parallelChoice() {
  const ids = state.parallelIds.filter((id) => state.bibles.some((m) => m.id === id)).slice(0, MAX_COLUMNS);
  if (ids.length) return ids;
  const open = state.bibles.find((m) => m.id === state.module);
  const others = state.bibles.filter((m) => m.id !== state.module);
  const second = others.find((m) => open && m.lang === open.lang) || others[0];
  return second ? [state.module, second.id] : [state.module];
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
  // T83: com uma só versão, o estado vazio diz como comparar sem sair da tela.
  const hint = columns.length === 1 && state.bibles.length > 1
    ? el("p", { class: "pnote" }, "Escolha mais uma versão nas fichas acima para comparar.")
    : null;
  text.replaceChildren(picker, ...(hint ? [hint] : []), head, ...rows);
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
    ...(data.more ? [el("div", { class: "origin" }, `Trecho mais longo: ${tap} para ler.`)] : []));
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
// T116: cada painel que carrega dados recebe um número; resposta de um número antigo é descartada.
let panelToken = 0;
// Quando definido, openPanel escreve num item fixado em vez do painel (restauração).
let renderTarget = null;

function openPanel(mode, title, ...content) {
  const nodes = content.flat(Infinity).filter(Boolean);
  if (renderTarget) {
    renderTarget.title = title;
    renderTarget.body.replaceChildren(...nodes);
    return;
  }
  if (mode !== panelMode) setSheetTall(false);
  panelMode = mode;
  currentView = pendingView ? { ...pendingView, title } : null;
  pendingView = null;
  $("#panel-title").textContent = title;
  $("#panel-body").replaceChildren(...nodes);
  $("#panel-body").scrollTop = 0;
  $("#panel").hidden = false;
  $("#panel").dataset.mode = mode;
  // Celular: a busca ocupa a tela inteira (tela própria); o resto abre como folha.
  $("#panel").classList.toggle("full", mode === "search" || mode === "buscar");
  document.body.classList.add("sheet-open");
  markBottomNav(mode);
  $("#panel-pin").hidden = !currentView;
  layout.showPinned(false);
  layout.update();
}

function closePanel() {
  panelMode = null;
  currentView = null;
  $("#panel").hidden = true;
  $("#panel").classList.remove("full");
  document.body.classList.remove("sheet-open");
  setSheetTall(false);
  markBottomNav(null);
  layout.update();
}

// Folha do celular: 60% da altura ou quase a tela toda (botão ⌃ no cabeçalho da folha).
function setSheetTall(on) {
  $("#panel").classList.toggle("tall", on);
  $("#panel-grip").setAttribute("aria-pressed", String(on));
  $("#panel-grip").setAttribute("aria-label", on ? "Reduzir a folha" : "Aumentar a folha");
}

// Destaca na barra inferior o botão da folha aberta.
const BNAV_MODES = { "#b-search": ["buscar", "search"], "#b-study": ["estudo"], "#b-text": ["texto"], "#b-more": ["mais"] };
function markBottomNav(mode) {
  for (const [id, modes] of Object.entries(BNAV_MODES)) {
    const button = $(id);
    if (modes.includes(mode)) button.setAttribute("aria-current", "true");
    else button.removeAttribute("aria-current");
  }
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
    tabs.replaceChildren(...[
      // Em tela estreita, volta ao painel de estudo.
      panelOpen ? el("button", { class: "pin-tab back-to-panel", onclick: () => this.showPinned(false) }, "← Estudo") : null,
      ...this.pins.map((pin) => el("span", { class: "pin-tab" + (pin.id === this.active ? " on" : "") },
        el("button", {
          class: "pin-title", role: "tab", "aria-selected": String(pin.id === this.active),
          title: pin.title, onclick: () => this.activate(pin.id),
        }, pin.title),
        el("button", { class: "pin-close", "aria-label": `Desafixar ${pin.title}`, onclick: () => this.unpin(pin.id) }, "×"))),
    ].filter(Boolean));
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
    else if (view.type === "study") await fillStudyPin(view.id, target);
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
let pendingTab = null;      // aba pedida por um clique (ex.: marca de nota abre "Minhas notas")
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
  const mine = ++panelToken;
  const verseKey = `${book}.${chapter}.${verse}`;
  if (verseKey !== xrefVerse) { xrefVerse = verseKey; xrefLimit = 12; xrefBook = null; versionsOpen = false; }
  if (pendingTab) { verseTab = pendingTab; pendingTab = null; }
  // T112: as consultas saem juntas; a de "Parecidas" não deixa as demais esperando.
  const [data, similar, notesData, backlinks] = await Promise.all([
    api("verse", { book, chapter, verse, module: state.module, xrefs: xrefLimit, xbook: xrefBook }),
    api("similar", { book, chapter, verse }).catch(() => ({ available: false, verses: [] })),
    api("user/notes", { book, chapter, verse }).catch(() => ({ notes: [] })),
    api("user/backlinks", { book, chapter, verse }).catch(() => ({ notes: [] })),
  ]);
  refreshCommentaryPins({ book, chapter, verse });
  const bookCounts = data.xrefs_total || xrefBook ? (await api("xref-books", { book, chapter, verse })).books : null;
  if (mine !== panelToken) return;
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
  const xrefs = data.xrefs.map((x) => el("div", { class: "xref-row" },
    el("button", {
      class: "result", onclick: () => go({ book: x.book, chapter: x.chapter, verse: x.verse }),
      title: "Listas curadas: theWord, BSB e TSK. Citados juntos: comentários e verbetes que citam os dois versículos.",
    }, el("div", { class: "source" },
        el("b", {}, refLabel(x.book, x.chapter, x.verse) + (x.span ? `–${x.verse + x.span}` : "")),
        el("span", {}, why(x))),
      x.text ? el("div", { class: "t clamp2" }, x.text) : null),
    el("button", { class: "chip xref-add", title: "Adicionar esta passagem a um conjunto de referências",
      onclick: () => pickRefSet(x).catch((error) => showToast(`Não foi possível abrir os conjuntos: ${error.message}`)) },
      "+ conjunto")));
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
    ["notas", "Minhas notas", notesData.notes.length, () => notesTab(book, chapter, verse, notesData.notes, backlinks.notes)],
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
  const mine = ++panelToken;
  const item = await api("item", { kind, id });
  if (mine !== panelToken) return;
  pendingView = { type: "item", kind, id };
  if (!item) return;
  const title = kind === "entry" ? item.label : `${item.abbr} · ${rangeLabel(item.book, item.ref_start, item.ref_end)}`;
  const backVerse = state.verse
    ? el("button", { class: "link back", onclick: () => showVerse() }, `← ${refLabel(state.book, state.chapter, state.verse)}`)
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
  const mine = ++panelToken;
  const data = await api("word", { strong, module: state.module, offset });
  if (mine !== panelToken) return;
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
    ? el("button", { class: "link back", onclick: () => showVerse() }, `← ${refLabel(state.book, state.chapter, state.verse)}`)
    : null;
  openPanel("word", `${strong}${original ? " · " + original : ""}`,
    backVerse, backToSearch(),
    original ? el("p", { class: "lemma", lang: LANG[data.original_lang] }, original,
      el("span", { lang: "pt-BR" }, ` ${langLabel} · ${data.total} versículos` +
        (data.original[0] && data.original[0].count ? ` · ${data.original[0].count} palavras no texto original` : ""))) : null,
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
// Busca salva e recente (DESENHO-PESQUISA, fase 3). Fica só no navegador, por decisão do usuário.
function readSearchStore(key) {
  try { return JSON.parse(localStorage.getItem(key) || "[]"); } catch (error) { return []; }
}

function writeSearchStore(key, list) {
  try { localStorage.setItem(key, JSON.stringify(list)); } catch (error) { /* navegador sem armazenamento */ }
}

function currentSearchOptions(query) {
  return { q: query, scope: state.searchScope || "aberta", modo: state.searchModo || "todas",
    near: state.searchNear || 5, strong: state.searchStrong || null, book: state.searchBook || null };
}

function addRecentSearch(query) {
  const item = currentSearchOptions(query);
  const same = (a) => a.q === item.q && a.scope === item.scope && a.modo === item.modo && a.strong === item.strong
    && (a.book || null) === item.book;
  const recent = [item, ...readSearchStore("buscas.recentes").filter((a) => !same(a))].slice(0, 10);
  writeSearchStore("buscas.recentes", recent);
}

function saveCurrentSearch() {
  const query = state.lastSearch && state.lastSearch.query;
  if (!query) return;
  const item = currentSearchOptions(query);
  const saved = readSearchStore("buscas.salvas").filter((a) => !(a.q === item.q && a.scope === item.scope && a.modo === item.modo && a.strong === item.strong));
  writeSearchStore("buscas.salvas", [item, ...saved].slice(0, 30));
  showToast("Busca salva neste navegador.");
}

function runSavedSearch(item) {
  state.searchScope = item.scope;
  state.searchModo = item.modo;
  state.searchNear = item.near;
  state.searchStrong = item.strong;
  state.searchBook = item.book || null;
  $("#q").value = item.q;
  showSearch(item.q);
}

// Copia os versículos da busca exibida (T97), sem os marcadores de destaque.
async function copySearchResults() {
  const verses = (state.lastSearch && state.lastSearch.data && state.lastSearch.data.verses) || [];
  if (!verses.length) { showToast("Não há versículos para copiar."); return; }
  const text = verses.map((v) => `${refLabel(v.book, v.chapter, v.verse)} (${v.abbr}): ${String(v.hit).replace(/\[\[|\]\]/g, "")}`).join("\n");
  try {
    await navigator.clipboard.writeText(text);
    showToast(`${verses.length} versículos copiados${partialSearchNote(verses.length)}.`);
  } catch (error) {
    showToast("Não foi possível copiar neste navegador.");
  }
}

// Escopo e modo da busca por palavra (DESENHO-PESQUISA, fase 1). Mudar refaz a busca.
function searchOptions(filterRow = null) {
  const rerun = () => showSearch(state.lastSearch.query);
  const scope = el("select", { "aria-label": "Escopo da busca", onchange: (event) => {
    state.searchScope = event.target.value; rerun();
  } }, el("option", { value: "aberta" }, "Versão aberta"), el("option", { value: "todas" }, "Todas as versões"));
  scope.value = state.searchScope || "aberta";
  const modes = [["todas", "Todas as palavras"], ["qualquer", "Qualquer palavra"], ["frase", "Frase exata"], ["near", "Próximas (NEAR)"]];
  const mode = el("select", { "aria-label": "Modo da busca", onchange: (event) => {
    state.searchModo = event.target.value; rerun();
  } }, modes.map(([value, text]) => el("option", { value }, text)));
  mode.value = state.searchModo || "todas";
  const strongField = el("input", { type: "text", placeholder: "G5485 ou H…", "aria-label": "Número Strong", onchange: (event) => {
    state.searchStrong = event.target.value.trim().toUpperCase() || null; rerun();
  } });
  strongField.value = state.searchStrong || "";
  // Livro (T88): restringe versículos e comentários; dicionários não têm livro, então não entram.
  const bookScope = el("select", { "aria-label": "Livro da busca", onchange: (event) => {
    state.searchBook = Number(event.target.value) || null; rerun();
  } }, el("option", { value: "" }, "Toda a Bíblia"),
     state.books.map((b) => el("option", { value: String(b.book) }, b.name)));
  bookScope.value = String(state.searchBook || "");
  const children = [el("label", {}, "Strong ", strongField), el("label", {}, "Escopo ", scope),
    el("label", {}, "Livro ", bookScope), el("label", {}, "Modo ", mode)];
  if ((state.searchModo || "todas") === "near") {
    const distance = el("input", { type: "number", min: "1", max: "50", "aria-label": "Alcance em palavras", onchange: (event) => {
      state.searchNear = Math.max(1, Math.min(50, Number(event.target.value) || 5)); rerun();
    } });
    distance.value = String(state.searchNear || 5);
    children.push(el("label", {}, "Alcance ", distance, " palavras"));
  }
  const recent = readSearchStore("buscas.recentes");
  const saved = readSearchStore("buscas.salvas");
  const entries = [...saved.map((item) => ({ ...item, label: `★ ${item.q}` })), ...recent.map((item) => ({ ...item, label: item.q }))];
  if (entries.length) {
    const list = el("select", { "aria-label": "Buscas salvas e recentes", onchange: (event) => {
      const item = entries[Number(event.target.value)];
      if (item) runSavedSearch(item);
    } }, el("option", { value: "" }, "Recentes e salvas…"), entries.map((item, index) => el("option", { value: String(index) }, item.label)));
    children.push(list);
  }
  // Opções de busca ficam recolhíveis; no celular começam fechadas, para o primeiro resultado aparecer logo (item 5).
  const config = children.splice(0);
  if (filterRow) config.unshift(filterRow);
  if (state.searchConfigOpen === undefined) state.searchConfigOpen = !window.matchMedia("(max-width: 560px)").matches;
  const configBox = el("details", { class: "search-config", open: state.searchConfigOpen, ontoggle: (event) => { state.searchConfigOpen = event.target.open; } },
    el("summary", {}, "Opções de busca"),
    el("div", { class: "search-opts" }, ...config));
  // T113: copiar e adicionar só fazem sentido com versículos encontrados.
  const hasVerses = ((state.lastSearch && state.lastSearch.data && state.lastSearch.data.verses) || []).length > 0;
  if (hasVerses) {
    children.push(el("button", { class: "link", onclick: copySearchResults }, "Copiar versículos"));
    children.push(el("button", { class: "link", onclick: addSearchToStudy }, "Adicionar versículos ao estudo"));
  }
  children.push(el("button", { class: "link", onclick: saveCurrentSearch }, "Salvar busca"));
  return el("div", { class: "search-opts-wrap" }, configBox, el("div", { class: "search-opts search-actions" }, ...children));
}

// Você quis dizer? (DESENHO-PESQUISA, fase 4): sugestões do Dicionário em português.
function suggestionBlock(suggest) {
  const items = Object.entries((suggest && suggest.suggestions) || {}).filter(([, options]) => options.length);
  if (!items.length) return el("p", { class: "empty" }, "Nada encontrado.");
  return el("div", { class: "suggest" },
    el("p", { class: "empty" }, "Nada encontrado. Você quis dizer:"),
    items.map(([typed, options]) => options.map((option) => el("button", {
      class: "chip", "aria-label": `Pesquisar ${option}`, onclick: () => {
        $("#q").value = option; addRecentSearch(option); showSearch(option);
      },
    }, option))));
}

// Ocorrências de um número Strong (DESENHO-PESQUISA, fase 2).
function strongBody(sr) {
  if (!sr) return [el("p", { class: "empty" }, "Digite um número Strong, como G5485.")];
  if (sr.error) return [el("p", { class: "empty" }, sr.error)];
  return [
    el("p", { class: "group-note" },
      `${sr.code}: ${sr.total} versículo(s) nas versões com marcação de Strong (ARA1993+, KJV, TR, BSB). A ARA não tem essa marcação.`),
    sr.verses.map((v) => el("button", {
      class: "result", onclick: () => { closeTopicsSafe(); go({ book: v.book, chapter: v.chapter, verse: v.verse }); },
    }, el("div", { class: "source" }, el("b", {}, refLabel(v.book, v.chapter, v.verse)), el("span", {}, v.abbr)),
      el("div", { class: "t" }, v.text),
      el("div", { class: "origin" }, `no original: ${v.words}`))),
  ];
}

function closeTopicsSafe() {
  if (typeof closeStudies === "function") closeStudies();
}

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
  // Filtros de tipo ficam dentro de "Opções de busca" (no celular, o primeiro resultado sobe).
  const filterRow = el("div", { class: "chips" },
    chip("tudo", "Tudo", keyword),
    chip("verses", "Versículos", counts.verses),
    chip("comments", "Comentários", counts.comments),
    chip("entries", "Dicionários e livros", counts.entries));
  const semState = state.lastSearch.semanticState || "done";
  const loading = semState === "loading";
  if (loading) startSemanticClock();
  const semanticBody = loading ? semanticLoading(state.lastSearch.startedAt)
    : semState === "timeout" ? semanticTimedOut(query)
    : semanticGroup(semantic);
  const body = mode === "sentido"
    ? [el("p", { class: "group-note" }, "Passagens de assunto parecido, mesmo sem as palavras digitadas. A ordem vem da similaridade de sentido (modelo BGE-M3)."),
       semanticBody]
    : state.searchStrong ? [searchOptions(), ...strongBody(state.lastSearch.strong)]
    : [loading ? semanticStatus(state.lastSearch.startedAt) : null,
       el("p", { class: "group-note" }, "Versículos e comentários que contêm os termos digitados."),
       searchOptions(filterRow),
       bridgeNote(query, data),
       englishVersionNote(query, data, module),
       keyword ? null : suggestionBlock(state.lastSearch.suggest),
       show("verses") ? searchSection("verses", `Bíblia · ${module.abbr}`) : null,
       show("comments") ? searchSection("comments", "Comentários") : null,
       show("entries") ? searchSection("entries", "Dicionários e livros") : null];
  openPanel("search", `Busca: ${query}`, isPhone() ? phoneSearchForm(query) : null, modeBar, body);
  if (keepScroll) $("#panel-body").scrollTop = scroll;
}

// --- Busca em tela própria no celular (D036) --------------------------------------

// Mesmo comportamento do campo da barra do desktop: referência abre o texto, palavra busca.
function submitSearch(query) {
  query = query.trim();
  if (!query) return;
  $("#q").value = query;
  const reference = parseReference(query);
  if (reference) {
    if (isPhone() && (panelMode === "buscar" || panelMode === "search")) closePanel();
    go(reference);
  } else {
    // Celular: a busca por sentido pode levar alguns segundos; mostra que está em andamento.
    if (isPhone() && (panelMode === "buscar" || panelMode === "search")) {
      $("#panel-body").replaceChildren(...[...$("#panel-body").children].filter((node) => node.matches(".m-search")),
        el("p", { class: "empty", role: "status" }, "Buscando…"));
    }
    addRecentSearch(query);
    showSearch(query);
  }
}

function phoneSearchForm(query = "") {
  const input = el("input", { type: "search", enterkeyhint: "search", autocomplete: "off",
    placeholder: "Palavra, ou referência como Jo 3:16", "aria-label": "Buscar ou ir para referência" });
  input.value = query;
  return el("form", { class: "m-search", role: "search", onsubmit: (event) => {
    event.preventDefault();
    input.blur();
    submitSearch(input.value);
  } }, input, el("button", { class: "chip on", type: "submit" }, "Buscar"));
}

function openSearchScreen() {
  const form = phoneSearchForm();
  const recent = readSearchStore("buscas.recentes");
  const saved = readSearchStore("buscas.salvas");
  const row = (item, label) => el("button", { class: "view-row", onclick: () => runSavedSearch(item) }, el("span", {}, label));
  const resultsBack = state.lastSearch
    ? el("button", { class: "view-row", onclick: () => renderSearch() }, el("span", {}, `← Resultados de "${state.lastSearch.query}"`))
    : null;
  openPanel("buscar", "Buscar",
    form,
    el("div", { class: "sheet-menu" },
      resultsBack,
      saved.length ? [el("h3", {}, "Salvas"), saved.map((item) => row(item, `★ ${item.q}`))] : null,
      recent.length ? [el("h3", {}, "Recentes"), recent.map((item) => row(item, item.q))] : null,
      el("p", { class: "group-note" }, "Digite uma palavra para buscar no texto, nos comentários e nos dicionários, ou uma referência (Jo 3:16, Sl 23) para abrir a passagem.")));
  form.querySelector("input").focus();
}

// Explica o que a ponte por Strong acrescentou à busca e permite desligá-la.
// T113: versão aberta em inglês e nenhum versículo: explica por que e oferece buscar em todas as versões.
function englishVersionNote(query, data, module) {
  if (state.searchStrong || !module || module.lang === "por" || (data.totals.verses || 0) > 0) return null;
  if (state.searchScope === "todas") return null;
  return el("div", { class: "bridge" },
    `Nenhum versículo da versão aberta (${module.abbr}, em inglês) contém "${query}". `,
    el("button", { class: "link", onclick: () => { state.searchScope = "todas"; showSearch(query); } }, "Buscar em todas as versões"));
}

function bridgeNote(query, data) {
  if (!data.bridge) return null;
  const toggle = (on, label) => el("button", {
    class: "link", onclick: () => { state.bilingual = on; store.set("bilingual", on ? "1" : "0"); showSearch(query); },
  }, label);
  if (!data.bilingual) {
    return el("div", { class: "bridge" }, "Buscando só os termos digitados. ", toggle(true, "Incluir termos em inglês"));
  }
  if (!data.expansions.length) return null;
  // Recolhível (item 5 do ajuste): no celular começa fechado, para os resultados subirem.
  if (state.bridgeOpen === undefined) state.bridgeOpen = !window.matchMedia("(max-width: 560px)").matches;
  return el("details", { class: "bridge", open: state.bridgeOpen, ontoggle: (event) => { state.bridgeOpen = event.target.open; } },
    el("summary", {}, `Termos em inglês incluídos (${data.expansions.length})`),
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

// Busca por sentido pode levar muito tempo na primeira vez (o modelo carrega no servidor).
// Ela corre em paralelo; a busca por palavra aparece assim que chega (T103).
const SEMANTIC_TIMEOUT_MS = 20000;
const TIMED_OUT = Symbol("tempo esgotado");
let searchToken = 0;   // resposta de uma busca antiga não pode sobrescrever a nova

function withTimeout(promise, ms) {
  let timer;
  const limit = new Promise((resolve) => { timer = setTimeout(() => resolve(TIMED_OUT), Math.max(0, ms)); });
  return Promise.race([promise, limit]).finally(() => clearTimeout(timer));
}

function semanticSeconds(startedAt) {
  return `${Math.floor((Date.now() - startedAt) / 1000)} s`;
}

let clockTimer = null;
function tickSemanticClocks() {
  const nodes = document.querySelectorAll(".sem-clock");
  if (!nodes.length) { clearInterval(clockTimer); clockTimer = null; return; }
  nodes.forEach((node) => { node.textContent = semanticSeconds(Number(node.dataset.started)); });
}
function startSemanticClock() {
  if (!clockTimer) clockTimer = setInterval(tickSemanticClocks, 1000);
}
function semanticClock(startedAt) {
  return el("span", { class: "sem-clock", "data-started": String(startedAt) }, semanticSeconds(startedAt));
}

// Indicador discreto na aba "Por palavra" enquanto a busca por sentido não chega.
function semanticStatus(startedAt) {
  return el("p", { class: "sem-status", role: "status" }, "Buscando por sentido… ", semanticClock(startedAt));
}

function semanticLoading(startedAt) {
  return el("div", { class: "sem-loading", role: "status" },
    el("span", { class: "spinner", "aria-hidden": "true" }),
    el("div", {},
      el("p", {}, "Buscando por sentido… ", semanticClock(startedAt)),
      el("p", { class: "group-note" }, "Na primeira vez, o servidor carrega o modelo, o que pode demorar. Os resultados por palavra já estão na aba ao lado.")));
}

function semanticTimedOut(query) {
  return el("div", { class: "sem-loading", role: "status" },
    el("div", {},
      el("p", {}, "O modelo de sentido ainda está carregando."),
      el("p", { class: "group-note" }, "Os resultados por palavra continuam disponíveis. Tente de novo em instantes."),
      el("button", { class: "chip on", onclick: () => showSearch(query) }, "Tentar de novo")));
}

async function showSearch(query) {
  const token = ++searchToken;
  const mine = ++panelToken;  // T116
  const semanticStart = Date.now();
  const semanticP = api("semantic", { q: query }).catch(() => ({ available: false, reason: "Não foi possível consultar a busca por sentido." }));
  const [data, strong] = await Promise.all([
    api("search", {
      q: query,
      module: state.searchScope === "todas" ? null : state.module,
      bilingual: state.bilingual ? 1 : 0,
      modo: state.searchModo || "todas",
      near: state.searchNear || 5,
      book: state.searchBook || "",
    }),
    state.searchStrong ? api("strong", { code: state.searchStrong }).catch(() => ({ error: "Não foi possível buscar este número Strong. Use G ou H seguido de números." })) : null,
  ]);
  if (token !== searchToken || mine !== panelToken) return;
  const nothing = !Object.values(data.totals || {}).some((n) => n);
  const suggest = nothing && !state.searchStrong ? await api("suggest", { q: query }).catch(() => null) : null;
  if (token !== searchToken || mine !== panelToken) return;
  const startedAt = semanticStart;
  state.lastSearch = { query, data, semantic: null, semanticState: "loading", startedAt, strong, suggest };
  renderSearch();

  const semantic = await withTimeout(semanticP, SEMANTIC_TIMEOUT_MS - (Date.now() - semanticStart));
  if (token !== searchToken) return;
  const timedOut = semantic === TIMED_OUT;
  state.lastSearch.semanticState = timedOut ? "timeout" : "done";
  state.lastSearch.semantic = timedOut ? null : semantic;
  if (panelMode === "search" || panelMode === "buscar") renderSearch(true);
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

let fontSize = 20;

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
  setTheme(dark ? "light" : "dark");
}

// Tema (D036): "light", "dark" ou "system" (segue prefers-color-scheme).
function setTheme(theme) {
  const root = document.documentElement;
  if (theme === "light" || theme === "dark") root.dataset.theme = theme;
  else delete root.dataset.theme;
  store.set("theme", theme);
}

function currentTheme() {
  const theme = store.get("theme");
  return theme === "light" || theme === "dark" ? theme : "system";
}

// --- Folhas do celular: Estudo, Texto (Aa), Mais e seletor de passagem (D036) ------

const menuRow = (label, action, { note = null, pressed } = {}) => {
  const props = { class: "view-row", onclick: action };
  if (pressed !== undefined) props["aria-pressed"] = String(pressed);
  return el("button", props, el("span", {}, label, note ? el("span", { class: "row-note" }, note) : null));
};
const openFail = (what) => (error) => showToast(`Não foi possível abrir ${what}: ${error.message}`);

// Abre a folha; se a mesma folha já está aberta, fecha (o botão da barra alterna).
function toggleSheet(mode, open) {
  if (panelMode === mode && !$("#panel").hidden) { closePanel(); return; }
  open();
}

function openStudyHub() {
  const study = readStored("ultimoEstudo");
  openPanel("estudo", "Estudo", el("div", { class: "sheet-menu" },
    menuRow("Leitura de hoje", () => openReading().catch(openFail("a leitura")), { note: "Planos de capítulos, marcados como lidos" }),
    study ? menuRow(`Continuar: ${study.title}`, () => { closePanel(); openStudies(study.id); }, { note: "Último estudo aberto" }) : null,
    menuRow("Meus estudos", () => { closePanel(); openStudies(); }),
    menuRow("Diário", () => openJournal().catch(openFail("o diário")), { note: "Reflexões com data, sem passagem" }),
    menuRow("Memorizar", () => openMemo().catch(openFail("a memorização")), { note: "Revisão com intervalos crescentes" }),
    menuRow("Notas por tópico", () => openTopicNotes().catch(openFail("os tópicos")), { note: "Um assunto com notas de várias passagens" })));
}

function openTextPanel() {
  const module = state.bibles.find((m) => m.id === state.module);
  const hasWords = module && module.has_strongs === 1;
  const size = el("output", { "aria-live": "polite" }, String(fontSize));
  const resize = (delta) => { fontSize = setFontSize(fontSize + delta); size.textContent = String(fontSize); };
  const themes = [["light", "Claro"], ["dark", "Escuro"], ["system", "Sistema"]];
  const marksOn = !document.body.classList.contains("marks-off");
  openPanel("texto", "Texto e tema", el("div", { class: "sheet-menu" },
    el("h3", {}, "Tamanho do texto"),
    el("div", { class: "size-row" },
      el("button", { "aria-label": "Diminuir fonte", onclick: () => resize(-1) }, "A−"), size,
      el("button", { "aria-label": "Aumentar fonte", onclick: () => resize(1) }, "A+")),
    el("h3", {}, "Tema"),
    el("div", { class: "seg", role: "group", "aria-label": "Tema" }, themes.map(([value, label]) => el("button", {
      "aria-pressed": String(currentTheme() === value), onclick: () => { setTheme(value); openTextPanel(); },
    }, label))),
    el("h3", {}, "No texto"),
    menuRow("Marcas: versículos com notas ou em estudos", () => { $("#marks").click(); openTextPanel(); }, { pressed: marksOn }),
    hasWords
      ? menuRow("Palavras originais (Strong)", () => { $("#words").click(); openTextPanel(); },
          { pressed: state.words, note: `${TAP} numa palavra para ver o termo grego ou hebraico` })
      : el("p", { class: "group-note" }, "Palavras originais (Strong): disponível nas versões com marcação, como ARA1993+ e KJV.")));
}

function openMoreMenu() {
  const fine = matchMedia("(pointer: fine)").matches;
  const pins = layout.pins.length;
  openPanel("mais", "Mais", el("div", { class: "sheet-menu" },
    el("h3", {}, "Ler"),
    menuRow("Versões em paralelo", () => { closePanel(); $("#parallel").click(); }, { pressed: state.parallel }),
    menuRow("Selecionar versículos", () => { closePanel(); setSelectMode(!selection.on); },
      { pressed: selection.on, note: "Toque no primeiro e no último para copiar, anotar ou estudar" }),
    pins ? menuRow(`Itens fixados (${pins})`, () => layout.showPinned(true)) : null,
    el("h3", {}, "Ferramentas"),
    menuRow("Pesquisa por tema", () => { closePanel(); openTopics(); }, { note: "Um assunto na Bíblia (ex.: perdão, paz)" }),
    menuRow("Dicionários e livros", () => $("#browse").click()),
    menuRow("Conjuntos de referências", () => openRefSets().catch(refSetFail)),
    menuRow("Mapa de estudo e linha do tempo", () => openStudyMap().catch(refSetFail)),
    el("h3", {}, "Preferências"),
    menuRow("Texto e tema (Aa)", openTextPanel),
    fine ? menuRow("Atalhos de teclado", showShortcuts) : null));
}

// Liga a barra inferior, o cabeçalho que some ao rolar e o ajuste ao teclado virtual.
function setupPhoneNav() {
  document.querySelectorAll(".tap-word").forEach((node) => { node.textContent = TAP; });
  $("#b-prev").addEventListener("click", () => step(-1));
  $("#b-next").addEventListener("click", () => step(1));
  $("#b-search").addEventListener("click", () => toggleSheet("buscar", openSearchScreen));
  $("#b-study").addEventListener("click", () => toggleSheet("estudo", openStudyHub));
  $("#b-text").addEventListener("click", () => toggleSheet("texto", openTextPanel));
  $("#b-more").addEventListener("click", () => toggleSheet("mais", openMoreMenu));
  $("#passage").addEventListener("click", () => toggleSheet("passagem", () => openPassagePicker()));
  $("#panel-grip").addEventListener("click", () => setSheetTall(!$("#panel").classList.contains("tall")));

  // Cabeçalho: some ao descer e volta ao subir ou perto do topo. A barra inferior fica.
  const reader = $("#reader");
  let lastTop = 0;
  reader.addEventListener("scroll", () => {
    const top = reader.scrollTop;
    if (!isPhone()) { document.body.classList.remove("bar-hidden"); lastTop = top; return; }
    if (top < 40) document.body.classList.remove("bar-hidden");
    else if (top > lastTop + 6) document.body.classList.add("bar-hidden");
    else if (top < lastTop - 6) document.body.classList.remove("bar-hidden");
    else return;   // movimento pequeno: guarda a referência anterior
    lastTop = top;
  }, { passive: true });

  // Teclado virtual: enquanto um campo de texto tem o foco, a barra inferior sai e a folha
  // ocupa a altura visível (CSS, :has(:focus)); aqui o campo e o botão abaixo dele rolam para a vista.
  const textField = (node) => node.matches?.("textarea, input:not([type=checkbox]):not([type=radio]):not([type=button]):not([type=submit])");
  document.addEventListener("focusin", (event) => {
    if (!isPhone() || !textField(event.target)) return;
    const field = event.target;
    setTimeout(() => {
      const actions = field.closest(".note-new, .note, form")?.querySelector(".note-actions, button[type=submit]");
      (actions || field).scrollIntoView({ block: "nearest" });
      field.scrollIntoView({ block: "nearest" });
    }, 350);
  });
  phoneQuery.addEventListener("change", () => { document.body.classList.remove("bar-hidden"); });
}

// Seletor de passagem: grade de livros (AT e NT) e depois de capítulos.
function openPassagePicker(book = null) {
  if (book) {
    const count = bookOf(book).chapters.length;
    openPanel("passagem", bookOf(book).name,
      el("button", { class: "link back", onclick: () => openPassagePicker() }, "← Livros"),
      el("div", { class: "pick-grid", role: "group", "aria-label": "Capítulos" },
        Array.from({ length: count }, (_, i) => el("button", {
          class: book === state.book && i + 1 === state.chapter ? "on" : null,
          onclick: () => { closePanel(); go({ book, chapter: i + 1, verse: null }); },
        }, String(i + 1)))));
    setSheetTall(true);
    return;
  }
  const grid = (from, to) => el("div", { class: "pick-grid", role: "group" },
    state.books.slice(from - 1, to).map((b) => el("button", {
      class: b.book === state.book ? "on" : null, title: b.name, "aria-label": b.name,
      onclick: () => (b.chapters.length === 1 ? (closePanel(), go({ book: b.book, chapter: 1, verse: null })) : openPassagePicker(b.book)),
    }, b.abbr)));
  openPanel("passagem", "Escolher passagem",
    el("h3", {}, "Antigo Testamento"), grid(1, 39),
    el("h3", {}, "Novo Testamento"), grid(40, 66));
  setSheetTall(true);
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
  fontSize = setFontSize(Number(store.get("fontSize")) || 20);
  const resume = location.hash ? null : resumeInfo();   // antes de render() gravar a leitura atual
  readHash();
  // Aquecimento (T103): uma consulta em segundo plano carrega o modelo antes da primeira busca.
  // O resultado é descartado; falha em silêncio (sem o serviço, a busca por sentido já avisa).
  setTimeout(() => api("semantic", { q: "aquecimento" }).catch(() => {}), 1500);

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
  $("#select").addEventListener("click", () => setSelectMode(!selection.on));
  $("#view").addEventListener("click", showView);
  setupPhoneNav();
  $("#memo").addEventListener("click", () => openMemo().catch((error) => showToast(`Não foi possível abrir a memorização: ${error.message}`)));
  $("#topics-notes").addEventListener("click", () => openTopicNotes().catch((error) => showToast(`Não foi possível abrir os tópicos: ${error.message}`)));
  $("#journal").addEventListener("click", () => openJournal().catch((error) => showToast(`Não foi possível abrir o diário: ${error.message}`)));
  $("#parallel").addEventListener("click", () => {
    selection.on = false; selection.start = selection.end = null;   // a seleção é só do capítulo normal
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
    else { addRecentSearch(query); showSearch(query); }
  });
  $("#text").addEventListener("keydown", (e) => {
    if ((e.key === "Enter" || e.key === " ") && e.target.classList.contains("v")) {
      e.preventDefault();
      if (selection.on) { tapVerse(Number(e.target.dataset.verse)); return; }
      go({ verse: Number(e.target.dataset.verse) });
    }
  });
  window.addEventListener("hashchange", () => { readHash(); render(); });

  render();
  if (resume) showResume(resume);
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

// --- Meus estudos (D5, primeira fatia): passagem, título e nota -------------------

// --- Leitura diária (T82): planos por capítulo, marcados como lidos --------------
async function openReading() {
  const data = await api("user/reading");
  openPanel("leitura", "Leitura de hoje", readingBody(data));
}

// --- Mapa de estudo e linha do tempo (T93, D033) -----------------------------------

async function openStudyMap(tab = "mapa") {
  const [map, timeline] = await Promise.all([api("user/map"), api("user/timeline")]);
  const tabs = el("div", { class: "pbar", role: "tablist" },
    [["mapa", "Mapa"], ["tempo", "Linha do tempo"]].map(([key, label]) => el("button", {
      class: "chip" + (key === tab ? " on" : ""), role: "tab", "aria-selected": String(key === tab),
      onclick: () => openStudyMap(key).catch(refSetFail),
    }, label)));
  openPanel("mapa", "Mapa de estudo", [tabs, tab === "mapa" ? studyMapBody(map) : timelineBody(timeline)]);
}

function studyMapBody(map) {
  if (!map.nodes.length) return el("p", { class: "empty" }, "Ainda não há notas, tópicos ou estudos para desenhar.");
  const width = 640, height = 480;
  // o nó mais estudado vai para o centro (índice 0), como no grafo de referências
  const drawn = map.nodes.filter((n) => n.kind === "passage" || n.linked).sort((x, y) => y.weight - x.weight);
  const remap = new Map(drawn.map((n, i) => [n.id, i]));
  const edges = map.edges.filter((e) => remap.has(e.from) && remap.has(e.to))
    .map((e) => ({ a: remap.get(e.from), b: remap.get(e.to), weight: e.weight }));
  const positions = drawn.length > 1 ? graphLayout(drawn, edges, width, height) : [{ x: width / 2, y: height / 2 }];
  const labelOf = (n) => n.kind === "passage" ? refLabel(n.book, n.chapter, n.verse) : n.name;
  const NS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("class", "study-map");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "Mapa de estudo: passagens, tópicos e estudos ligados");
  edges.forEach((e) => {
    const line = document.createElementNS(NS, "line");
    line.setAttribute("x1", positions[e.a].x); line.setAttribute("y1", positions[e.a].y);
    line.setAttribute("x2", positions[e.b].x); line.setAttribute("y2", positions[e.b].y);
    line.setAttribute("class", "map-edge");
    line.setAttribute("stroke-width", String(1 + Math.min(4, e.weight)));
    svg.append(line);
  });
  drawn.forEach((n, i) => {
    const g = document.createElementNS(NS, "g");
    g.setAttribute("class", `map-node map-${n.kind}`);
    const c = document.createElementNS(NS, "circle");
    c.setAttribute("cx", positions[i].x); c.setAttribute("cy", positions[i].y);
    c.setAttribute("r", String(6 + Math.min(10, n.weight * 2)));
    const t = document.createElementNS(NS, "text");
    t.setAttribute("x", positions[i].x); t.setAttribute("y", positions[i].y - 12 - Math.min(10, n.weight * 2));
    t.setAttribute("text-anchor", "middle");
    t.textContent = labelOf(n);
    g.append(c, t);
    if (n.kind === "passage") {
      g.style.cursor = "pointer";
      g.addEventListener("click", () => go({ book: n.book, chapter: n.chapter, verse: n.verse }));
    }
    svg.append(g);
  });
  const legend = el("p", { class: "group-note" },
    `Passagens: ${map.passages_total} (mostrando as ${map.passages_shown} mais estudadas). ${TAP} numa passagem para abri-la. Tópicos e estudos são os nós com nome.`);
  return [legend, svg];
}

function timelineBody(timeline) {
  if (!timeline.events.length) return el("p", { class: "empty" }, "Nenhum evento datado ainda.");
  const kindLabel = { nota: "Nota", tópico: "Tópico", diário: "Diário", estudo: "Estudo", memorização: "Memorização", conjunto: "Conjunto", leitura: "Leitura" };
  let day = null;
  const out = [];
  for (const ev of timeline.events) {
    const d = brDate(ev.at);
    if (d !== day) { day = d; out.push(el("h3", { class: "tl-day" }, d)); }
    const ref = ev.book ? refLabel(ev.book, ev.chapter, ev.verse) : null;
    out.push(el("div", { class: "tl-item" },
      el("span", { class: "group-note" }, kindLabel[ev.label] || ev.label),
      ev.title ? el("b", {}, ` ${ev.title}`) : null,
      ref ? el("button", { class: "link", onclick: () => go({ book: ev.book, chapter: ev.chapter, verse: ev.verse }) }, ref) : null,
      ev.text ? el("div", { class: "journal-text" }, ev.text) : null));
  }
  return out;
}

// --- Conjuntos de referências (T98, D032): passagens ordenadas pelo usuário ---------

const refSetFail = (error) => showToast(`Não foi possível salvar: ${error.message}`);

async function openRefSets() {
  const data = await api("user/sets");
  const name = el("input", { type: "text", placeholder: "Nome do conjunto, ex.: graça", "aria-label": "Nome do novo conjunto" });
  const create = el("section", { class: "plan plan-new" },
    el("h3", {}, "Novo conjunto"),
    el("div", { class: "note-actions" }, name, el("button", { class: "chip on", onclick: async () => {
      try { await userWrite("set/create", { name: name.value }); openRefSets(); } catch (error) { refSetFail(error); }
    } }, "Criar")));
  const rows = data.sets.map((s) => el("button", { class: "result", onclick: () => openRefSet(s.id).catch(refSetFail) },
    el("b", {}, s.name), " ", el("span", { class: "group-note" }, `${s.items} ${s.items === 1 ? "passagem" : "passagens"}`)));
  openPanel("conjuntos", "Conjuntos de referências", [
    el("p", { class: "group-note" }, "Escolha passagens das referências cruzadas e ponha-as na ordem que quiser."),
    create,
    rows.length ? rows : el("p", { class: "empty" }, "Nenhum conjunto ainda."),
  ]);
}

async function openRefSet(id) {
  const set = await api("user/set", { id });
  const label = (item) => refLabel(item.book, item.chapter, item.verse) + (item.span ? `–${item.verse + item.span}` : "");
  const rows = set.items.map((item, index) => el("div", { class: "xref-row" },
    el("button", { class: "result", onclick: () => go({ book: item.book, chapter: item.chapter, verse: item.verse }) },
      el("b", {}, label(item))),
    el("button", { class: "chip", "aria-label": "Subir", disabled: index === 0 ? true : null,
      onclick: () => userWrite("set/move", { id: item.id, delta: -1 }).then(() => openRefSet(id)).catch(refSetFail) }, "↑"),
    el("button", { class: "chip", "aria-label": "Descer", disabled: index === set.items.length - 1 ? true : null,
      onclick: () => userWrite("set/move", { id: item.id, delta: 1 }).then(() => openRefSet(id)).catch(refSetFail) }, "↓"),
    el("button", { class: "chip", "aria-label": "Remover do conjunto",
      onclick: () => userWrite("set/remove", { id: item.id }).then(() => openRefSet(id)).catch(refSetFail) }, "×")));
  openPanel("conjunto", set.name, [
    el("button", { class: "link back", onclick: () => openRefSets().catch(refSetFail) }, "← Conjuntos"),
    rows.length ? rows : el("p", { class: "empty" }, "Nenhuma passagem neste conjunto. Use “+ conjunto” nas referências."),
    el("div", { class: "note-actions" }, el("button", { class: "link", onclick: async () => {
      if (!confirm(`Apagar o conjunto "${set.name}"? Vai para a lixeira.`)) return;
      try { await userWrite("set/delete", { id: set.id }); openRefSets(); } catch (error) { refSetFail(error); }
    } }, "Apagar conjunto")),
  ]);
}

async function pickRefSet(x) {
  const data = await api("user/sets");
  const label = refLabel(x.book, x.chapter, x.verse) + (x.span ? `–${x.verse + x.span}` : "");
  const name = el("input", { type: "text", placeholder: "Novo conjunto", "aria-label": "Novo conjunto para esta passagem" });
  const add = async (setId) => {
    try {
      await userWrite("set/add", { set_id: setId, book: x.book, chapter: x.chapter, verse: x.verse, span: x.span || 0 });
      openRefSet(setId).catch(refSetFail);
    } catch (error) { refSetFail(error); }
  };
  openPanel("conjuntos", `Adicionar ${label}`, [
    el("p", { class: "group-note" }, "Escolha o conjunto, ou crie um novo para esta passagem."),
    el("div", { class: "note-actions" }, name, el("button", { class: "chip on", onclick: async () => {
      try {
        const made = await userWrite("set/create", { name: name.value });
        await add(made.id);
      } catch (error) { refSetFail(error); }
    } }, "Criar e adicionar")),
    data.sets.length
      ? data.sets.map((s) => el("button", { class: "result", onclick: () => add(s.id) }, el("b", {}, s.name), " ",
          el("span", { class: "group-note" }, `${s.items} ${s.items === 1 ? "passagem" : "passagens"}`)))
      : el("p", { class: "empty" }, "Nenhum conjunto ainda."),
  ]);
}

// --- Memorização (T80, D031): SM-2 sobre cartões de versículos ---------------------

const MEMO_BUTTONS = [["esqueci", "Não lembrei"], ["dificil", "Difícil"], ["bom", "Bom"], ["facil", "Fácil"]];

async function openMemo() {
  const data = await api("user/memo");
  openPanel("memo", "Memorização", memoBody(data));
}

function memoBody(data) {
  const fail = (error) => showToast(`Não foi possível salvar: ${error.message}`);
  const head = el("p", { class: "group-note" }, `Hoje: ${data.date} · ${data.due.length} para revisar · ${data.cards.length} ${data.cards.length === 1 ? "versículo" : "versículos"}`);
  const review = data.due.length
    ? el("div", { class: "note-actions" }, el("button", { class: "chip on", onclick: () => startReview(data.due, 0) }, `Revisar agora (${data.due.length})`))
    : el("p", { class: "group-note" }, "Nada para revisar hoje.");

  const bookSelect = el("select", { "aria-label": "Livro do versículo" },
    state.books.map((b) => el("option", { value: b.book, selected: b.book === state.book ? true : null }, b.name)));
  const chapter = el("input", { type: "number", min: 1, value: state.chapter, "aria-label": "Capítulo do versículo", style: "width:4.5em" });
  const verse = el("input", { type: "number", min: 1, placeholder: "vers.", "aria-label": "Versículo a memorizar", style: "width:4.5em" });
  const add = el("section", { class: "plan plan-new" },
    el("h3", {}, "Novo versículo"),
    el("div", { class: "note-actions" }, bookSelect, " ", chapter, " ", verse),
    el("div", { class: "note-actions" }, el("button", { class: "chip on", onclick: async () => {
      try {
        await userWrite("memo/add", { book: Number(bookSelect.value), chapter: Number(chapter.value), verse: Number(verse.value) });
        openMemo();
      } catch (error) { fail(error); }
    } }, "Adicionar")));

  const card = (c) => el("section", { class: "plan journal-entry" },
    el("p", { class: "group-note" }, `${refLabel(c.book, c.chapter, c.verse)} · próxima revisão ${brDate(c.due)} · ${c.reps} acertos seguidos`),
    el("div", { class: "note-actions" }, el("button", { class: "link", onclick: async () => {
      if (!confirm("Tirar este versículo da memorização? Ele vai para a lixeira.")) return;
      try { await userWrite("memo/delete", { id: c.id }); openMemo(); } catch (error) { fail(error); }
    } }, "Tirar da memorização")));

  return [head, review, add,
    data.cards.length ? data.cards.map(card) : el("p", { class: "empty" }, "Nenhum versículo ainda. Adicione um acima."),
  ];
}

// Uma revisão por vez: mostra o versículo só quando pedido, e a resposta fica com o usuário.
function startReview(queue, index) {
  if (index >= queue.length) {
    showToast("Revisão concluída.");
    openMemo().catch(() => {});
    return;
  }
  const item = queue[index];
  const text = el("div", { class: "journal-text", "aria-live": "polite" }, "");
  const reveal = el("button", { class: "chip on", onclick: async () => {
    reveal.disabled = true;
    try {
      const data = await api("passage", { module: state.module, book: item.book, chapter: item.chapter, verse: item.verse });
      text.textContent = data.verses[0]?.text || "Texto indisponível nesta versão.";
    } catch (error) { text.textContent = "Não foi possível carregar o versículo."; }
    grades.hidden = false;
  } }, "Mostrar versículo");
  const grades = el("div", { class: "note-actions", hidden: true }, MEMO_BUTTONS.map(([grade, label]) =>
    el("button", { class: "chip", onclick: async () => {
      try {
        await userWrite("memo/review", { id: item.id, grade });
        startReview(queue, index + 1);
      } catch (error) { showToast(`Não foi possível salvar: ${error.message}`); }
    } }, label)));
  openPanel("memo-review", "Revisão", el("p", { class: "group-note" }, `${index + 1} de ${queue.length} · ${refLabel(item.book, item.chapter, item.verse)}`),
    reveal, text, grades,
    el("button", { class: "link", onclick: () => openMemo().catch(() => {}) }, "Sair da revisão"));
}

// --- Notas por tópico (T87, D030) -------------------------------------------------

async function openTopicNotes() {
  const data = await api("user/topics");
  openPanel("topicos", "Notas por tópico", topicNotesListBody(data));
}

async function openTopicNote(id) {
  const topic = await api("user/topic", { id });
  openPanel("topico", topic.name, topicNoteBody(topic));
}

function topicNotesListBody(data) {
  const fail = (error) => showToast(`Não foi possível salvar: ${error.message}`);
  const name = el("input", { type: "text", placeholder: "Nome do tópico, ex.: ansiedade", "aria-label": "Nome do novo tópico" });
  const create = el("section", { class: "plan plan-new" },
    el("h3", {}, "Novo tópico"),
    el("div", { class: "note-actions" }, name, el("button", { class: "chip on", onclick: async () => {
      try { await userWrite("topic/create", { name: name.value }); openTopicNotes(); } catch (error) { fail(error); }
    } }, "Criar")));
  const list = data.topics.map((t) => el("button", { class: "result", onclick: () => openTopicNote(t.id).catch(fail) },
    el("b", {}, t.name), " ", el("span", { class: "group-note" }, `${t.notes} ${t.notes === 1 ? "nota" : "notas"}`)));
  return [
    el("p", { class: "group-note" }, "Um assunto reúne notas de várias passagens. Para anotar só um versículo, use as notas dele."),
    create,
    list.length ? list : el("p", { class: "empty" }, "Nenhum tópico ainda."),
  ];
}

function topicNoteBody(topic) {
  const fail = (error) => showToast(`Não foi possível salvar: ${error.message}`);
  const reopen = () => openTopicNote(topic.id).catch(fail);

  const noteCard = (note) => {
    const card = el("section", { class: "plan journal-entry" });
    const where = note.book ? refLabel(note.book, note.chapter, note.verse) : "Sem passagem";
    const showCard = () => card.replaceChildren(
      el("p", { class: "group-note" }, where),
      el("div", { class: "journal-text" }, note.body),
      el("div", { class: "note-actions" },
        el("button", { class: "link", onclick: editCard }, "Editar"),
        el("button", { class: "link", onclick: async () => {
          if (!confirm("Apagar esta nota do tópico? Ela vai para a lixeira.")) return;
          try { await userWrite("topic/note/delete", { id: note.id }); reopen(); } catch (error) { fail(error); }
        } }, "Apagar")));
    const editCard = () => {
      const area = el("textarea", { rows: 5, "aria-label": "Texto da nota" });
      area.value = note.body;
      card.replaceChildren(area, el("div", { class: "note-actions" },
        el("button", { class: "chip on", onclick: async () => {
          try { await userWrite("topic/note/update", { id: note.id, body: area.value }); reopen(); } catch (error) { fail(error); }
        } }, "Salvar"),
        el("button", { class: "link", onclick: showCard }, "Cancelar")));
      area.focus();
    };
    showCard();
    return card;
  };

  const bookSelect = el("select", { "aria-label": "Passagem da nota" },
    el("option", { value: "" }, "Sem passagem"),
    state.books.map((b) => el("option", { value: b.book }, b.name)));
  const chapter = el("input", { type: "number", min: 1, placeholder: "cap.", "aria-label": "Capítulo da nota", style: "width:4.5em" });
  const verse = el("input", { type: "number", min: 1, placeholder: "vers.", "aria-label": "Versículo da nota", style: "width:4.5em" });
  const area = el("textarea", { rows: 4, placeholder: "O que a Bíblia diz sobre este assunto?", "aria-label": "Nova nota do tópico" });
  const add = el("section", { class: "plan plan-new" },
    el("h3", {}, "Nova nota"),
    area,
    el("div", { class: "note-actions" }, bookSelect, " ", chapter, " ", verse),
    el("div", { class: "note-actions" }, el("button", { class: "chip on", onclick: async () => {
      if (!area.value.trim()) return fail(new Error("a nota está vazia"));
      const hasBook = bookSelect.value !== "";
      try {
        await userWrite("topic/note/add", {
          topic_id: topic.id, body: area.value,
          book: hasBook ? Number(bookSelect.value) : null,
          chapter: hasBook ? Number(chapter.value) : null,
          verse: hasBook ? Number(verse.value) : null,
        });
        reopen();
      } catch (error) { fail(error); }
    } }, "Adicionar nota")));

  return [
    el("button", { class: "link back", onclick: () => openTopicNotes().catch(fail) }, "← Tópicos"),
    add,
    topic.notes.length ? topic.notes.map(noteCard) : el("p", { class: "empty" }, "Nenhuma nota neste tópico ainda."),
    el("div", { class: "note-actions" }, el("button", { class: "link", onclick: async () => {
      if (!confirm(`Apagar o tópico "${topic.name}" e todas as suas notas? Vai para a lixeira.`)) return;
      try { await userWrite("topic/delete", { id: topic.id }); openTopicNotes(); } catch (error) { fail(error); }
    } }, "Apagar tópico")),
  ];
}

// --- Diário de estudo (T89, D029) -------------------------------------------------

async function openJournal(query = "") {
  const data = await api("user/journal", { q: query || null });
  openPanel("diario", "Diário de estudo", journalBody(data, query));
}

function brDate(stamp) {
  const [y, m, d] = String(stamp).slice(0, 10).split("-");
  return d && m && y ? `${d}/${m}/${y}` : String(stamp);
}

function journalBody(data, query) {
  const fail = (error) => showToast(`Não foi possível salvar: ${error.message}`);
  const reopen = () => openJournal(query).catch(fail);

  const entry = (item) => {
    const card = el("section", { class: "plan journal-entry" });
    const showCard = () => card.replaceChildren(
      el("p", { class: "group-note" }, `${brDate(item.created_at)}${item.updated_at !== item.created_at ? " · editada" : ""}`),
      el("div", { class: "journal-text" }, item.body),
      el("div", { class: "note-actions" },
        el("button", { class: "link", onclick: editCard }, "Editar"),
        el("button", { class: "link", onclick: async () => {
          if (!confirm("Apagar esta entrada do diário? Ela vai para a lixeira.")) return;
          try { await userWrite("journal/delete", { id: item.id }); reopen(); } catch (error) { fail(error); }
        } }, "Apagar")));
    const editCard = () => {
      const area = el("textarea", { rows: 5, "aria-label": "Texto da entrada" });
      area.value = item.body;
      card.replaceChildren(
        area,
        el("div", { class: "note-actions" },
          el("button", { class: "chip on", onclick: async () => {
            try { await userWrite("journal/update", { id: item.id, body: area.value }); reopen(); } catch (error) { fail(error); }
          } }, "Salvar"),
          el("button", { class: "link", onclick: showCard }, "Cancelar")));
      area.focus();
    };
    showCard();
    return card;
  };

  const area = el("textarea", { rows: 4, placeholder: "O que você percebeu hoje?", "aria-label": "Nova entrada do diário" });
  const create = el("section", { class: "plan plan-new" },
    el("h3", {}, "Nova entrada"),
    area,
    el("div", { class: "note-actions" }, el("button", { class: "chip on", onclick: async () => {
      if (!area.value.trim()) return fail(new Error("a entrada está vazia"));
      try { await userWrite("journal/create", { body: area.value }); reopen(); } catch (error) { fail(error); }
    } }, "Salvar entrada")));

  const search = el("input", { type: "search", value: query, placeholder: "Buscar no diário", "aria-label": "Buscar no diário",
    onchange: (event) => openJournal(event.target.value.trim()).catch(fail) });
  return [
    el("p", { class: "group-note" }, "Entradas com data, sem passagem. Para anotar um versículo, use as notas dele."),
    create,
    search,
    data.entries.length ? data.entries.map(entry) : el("p", { class: "empty" }, query ? "Nenhuma entrada com este texto." : "Nenhuma entrada ainda."),
  ];
}

function readingBody(data) {
  const fail = (error) => showToast(`Não foi possível salvar: ${error.message}`);
  const plans = data.plans.map((plan) => el("section", { class: "plan" },
    el("h3", {}, plan.title),
    el("p", { class: "group-note" }, `${plan.done} de ${plan.total} capítulos lidos`),
    plan.next
      ? el("div", { class: "note-actions" },
          el("button", { class: "result", onclick: () => go({ book: plan.next.book, chapter: plan.next.chapter, verse: null }) },
            el("b", {}, `Próximo: ${refLabel(plan.next.book, plan.next.chapter)}`)),
          plan.read_today
            ? el("span", { class: "group-note" }, "Lido hoje ✓")
            : el("button", { class: "chip on", onclick: async () => {
                try { await userWrite("plan/mark", { id: plan.next.id, plan_id: plan.id, done: true }); openReading(); } catch (error) { fail(error); }
              } }, "Marcar como lido"))
      : el("p", { class: "group-note" }, "Plano concluído."),
    el("button", { class: "link", onclick: async () => {
      if (!confirm("Apagar este plano? O progresso some (as notas continuam).")) return;
      try { await userWrite("plan/delete", { id: plan.id }); openReading(); } catch (error) { fail(error); }
    } }, "Apagar plano")));

  const bookSelect = (value) => el("select", { "aria-label": "Livro" },
    state.books.map((b) => el("option", { value: b.book, selected: b.book === value ? true : null }, b.name)));
  const startBook = bookSelect(state.book);
  const startChapter = el("input", { type: "number", min: 1, value: state.chapter, "aria-label": "Capítulo inicial", style: "width:4.5em" });
  const endBook = bookSelect(state.book);
  const endChapter = el("input", { type: "number", min: 1, value: state.chapter, "aria-label": "Capítulo final", style: "width:4.5em" });
  const create = el("section", { class: "plan plan-new" },
    el("h3", {}, "Novo plano por capítulos"),
    el("p", { class: "group-note" }, "Um capítulo por dia, na ordem da Bíblia. Marque cada um como lido ao terminar."),
    el("div", { class: "note-actions" }, startBook, " ", startChapter, " até ", endBook, " ", endChapter),
    el("div", { class: "note-actions" }, el("button", { class: "chip on", onclick: async () => {
      try {
        await userWrite("plan/create", {
          book: Number(startBook.value), chapter: Number(startChapter.value),
          to_book: Number(endBook.value), to_chapter: Number(endChapter.value),
        });
        openReading();
      } catch (error) { fail(error); }
    } }, "Criar plano")));

  const head = el("p", { class: "group-note" }, `Hoje: ${data.date} · notas de hoje: ${data.notes_today}`);
  return [head, plans.length ? plans : el("p", { class: "empty" }, "Nenhum plano ainda."), create];
}

function openStudies(id = null) {
  $("#studies-full").hidden = false;
  if (id) renderStudy(id);
  else renderStudyList();
}

function closeStudies() {
  overlayStudyId = null;
  $("#studies-full").hidden = true;
  $("#studies-body").replaceChildren();
}

async function renderStudyList() {
  overlayStudyId = null;
  const data = await api("user/studies");
  const input = el("input", { type: "text", placeholder: "Título do novo estudo", "aria-label": "Título do novo estudo" });
  const create = el("form", { class: "topic-form", onsubmit: async (event) => {
    event.preventDefault();
    const title = input.value.trim();
    if (!title) return;
    try { const made = await userWrite("study/create", { title }); renderStudy(made.id); } catch (error) { showToast(error.message); }
  } }, input, el("button", { class: "chip on", type: "submit" }, "Criar estudo"));
  const rows = data.studies.map((s) => el("button", { class: "result", onclick: () => renderStudy(s.id) },
    el("div", { class: "source" }, el("b", {}, s.title), el("span", {}, `${s.status} · ${s.blocks} blocos`)),
    el("div", { class: "origin" }, `atualizado ${s.updated_at.replace("T", " ")}`)));
  $("#studies-body").replaceChildren(create,
    ...(rows.length ? rows : [el("p", { class: "empty" }, "Nenhum estudo ainda. Crie um aqui ou use \"Adicionar ao estudo\" no painel de um versículo.")]));
}

let overlayStudyId = null;   // estudo na tela cheia (null = lista)

async function renderStudy(id) {
  overlayStudyId = id;
  const data = await api("user/study", { id });
  $("#studies-body").replaceChildren(...buildStudy(data, false));
}

// Tela de um estudo: a mesma na tela cheia e na coluna ao lado (pinned).
// As escritas passam por userWrite, que atualiza as duas (T90, D5 decisão 3).
function buildStudy(data, pinned) {
  const study = data.study;
  store.set("ultimoEstudo", JSON.stringify({ id: study.id, title: study.title }));   // T92
  const fail = (error) => showToast(error.message);
  const redo = () => {};
  const title = el("input", { type: "text", class: "study-title", "aria-label": "Título do estudo" });
  title.value = study.title;
  title.addEventListener("change", async () => {
    try { await userWrite("study/update", { id: study.id, title: title.value }); } catch (error) { fail(error); }
  });
  const status = el("select", { "aria-label": "Estado do estudo", onchange: async () => {
    try { await userWrite("study/update", { id: study.id, status: status.value }); redo(); } catch (error) { fail(error); }
  } }, el("option", { value: "rascunho" }, "Rascunho"), el("option", { value: "pronto" }, "Pronto"));
  status.value = study.status;

  const blockRow = (block, index) => {
    const move = (direction) => async () => {
      try { await userWrite("block/move", { id: block.id, direction }); redo(); } catch (error) { fail(error); }
    };
    const remove = async () => {
      if (!confirm("Remover este bloco do estudo?")) return;
      try { await userWrite("block/delete", { id: block.id }); redo(); } catch (error) { fail(error); }
    };
    const actions = el("div", { class: "note-actions" },
      el("button", { class: "link", "aria-label": "Mover para cima", onclick: move(-1) }, "↑"),
      el("button", { class: "link", "aria-label": "Mover para baixo", onclick: move(1) }, "↓"),
      el("button", { class: "link", onclick: remove }, "Remover"));
    if (block.kind === "passagem") {
      return el("div", { class: "note" },
        el("div", { class: "note-meta" }, "Passagem"),
        el("button", { class: "link", onclick: () => { closeStudies(); go({ book: block.book, chapter: block.chapter, verse: block.verse }); } },
          refLabel(block.book, block.chapter, block.verse)),
        actions);
    }
    const area = el("textarea", { class: "note-input", rows: 3, "aria-label": block.kind === "titulo" ? "Título da seção" : "Nota do estudo" });
    area.value = block.body;
    area.addEventListener("change", async () => {
      try { await userWrite("block/update", { id: block.id, body: area.value }); } catch (error) { fail(error); }
    });
    return el("div", { class: "note" }, el("div", { class: "note-meta" }, block.kind === "titulo" ? "Título" : "Nota"), area, actions);
  };

  const addNote = el("textarea", { class: "note-input", rows: 3, "aria-label": "Nova nota no estudo", placeholder: "Escreva uma nota para este estudo" });
  const addTitle = el("input", { type: "text", placeholder: "Título de uma seção", "aria-label": "Nova seção" });
  const addBlock = (kind, source) => async () => {
    const body = source.value.trim();
    if (!body) return;
    try { await userWrite("block/add", { study_id: study.id, kind, body }); redo(); } catch (error) { fail(error); }
  };
  const addCurrent = async () => {
    if (!state.verse) { showToast("Abra um versículo para adicionar a passagem atual."); return; }
    try {
      await userWrite("block/add", { study_id: study.id, kind: "passagem", book: state.book, chapter: state.chapter, verse: state.verse });
      redo();
    } catch (error) { fail(error); }
  };

  return [
    el("div", { class: "note-actions" },
      el("button", { class: "link", onclick: () => openStudies() }, "← Meus estudos"),
      ...(pinned ? [] : [el("button", { class: "link", onclick: () => { closeStudies(); pinStudy(study.id); } }, "Abrir ao lado")]),
      el("a", { href: `/api/user/study/export?id=${study.id}`, class: "link" }, "Exportar em Markdown"),
      el("button", { class: "link", onclick: async () => {
        if (!confirm("Mover este estudo para a lixeira?")) return;
        try { await userWrite("study/delete", { id: study.id }); unpinStudies(study.id); if (overlayStudyId === study.id) renderStudyList(); } catch (error) { fail(error); }
      } }, "Apagar estudo")),
    el("div", { class: "note-new" }, title, status),
    ...(data.blocks.length ? data.blocks.map(blockRow) : [el("p", { class: "empty" }, "O estudo ainda não tem blocos.")]),
    el("div", { class: "note-new" },
      el("div", { class: "note-actions" }, el("button", { class: "chip", onclick: addCurrent }, "Adicionar a passagem atual")),
      addTitle, el("button", { class: "chip", onclick: addBlock("titulo", addTitle) }, "Adicionar título"),
      addNote, el("button", { class: "chip on", onclick: addBlock("nota", addNote) }, "Adicionar nota"))];
}

// --- Estudo ao lado (coluna fixada, D5 decisão 3): só quando o usuário abre -----
async function fillStudyPin(id, pin) {
  try {
    const data = await api("user/study", { id });
    pin.title = `Estudo · ${data.study.title}`;
    pin.body.replaceChildren(...buildStudy(data, true));
  } catch (error) {
    pin.title = pin.title || "Estudo";
    pin.body.replaceChildren(el("p", { class: "empty" }, "Este estudo não está mais disponível."));
  }
}

async function pinStudy(id) {
  const pin = { body: el("div", { class: "pinned-content" }) };
  await fillStudyPin(id, pin);
  layout.add({ type: "study", id }, pin.title, pin.body);
}

// Recarrega as colunas de estudo (chamado depois de cada escrita em estudo ou bloco).
async function refreshPinnedStudies() {
  const pins = layout.pins.filter((pin) => pin.view.type === "study");
  if (!pins.length) return;
  await Promise.all(pins.map((pin) => fillStudyPin(pin.view.id, pin)));
  layout.save();
  layout.renderTabs();
}

function unpinStudies(id) {
  layout.pins.filter((pin) => pin.view.type === "study" && pin.view.id === id).forEach((pin) => layout.unpin(pin.id));
}

async function addToStudy(book, chapter, verse) {
  try {
    const data = await api("user/studies");
    if (data.studies.length) {
      const study = data.studies[0];
      await userWrite("block/add", { study_id: study.id, kind: "passagem", book, chapter, verse });
      showToast(`Adicionado a «${study.title}»`);
    } else {
      await userWrite("study/create", { title: `Estudo: ${refLabel(book, chapter, verse)}`, book, chapter, verse });
      showToast("Estudo criado com esta passagem");
    }
  } catch (error) {
    showToast(`Não foi possível adicionar: ${error.message}`);
  }
}

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
  if (action.startsWith("note")) render();   // atualiza as marcas do texto
  if (action.startsWith("study") || action.startsWith("block")) {
    if (overlayStudyId && action !== "study/create") renderStudy(overlayStudyId).catch(() => {});
    refreshPinnedStudies();
  }
  return data;
}

function notesTab(book, chapter, verse, notes, backlinks = []) {
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
    el("div", { class: "note-new" }, input, el("div", { class: "note-actions" }, save,
      el("button", { class: "link", onclick: () => addToStudy(book, chapter, verse) }, "Adicionar ao estudo mais recente"))),
    rows.length ? rows : el("p", { class: "empty" }, "Nenhuma nota neste versículo ainda."),
    backlinkSection(backlinks),
    el("p", { class: "group-note" }, el("a", { href: "/api/user/export", class: "link" }, "Exportar em Markdown"), " · ", el("a", { href: "/api/user/export.docx", class: "link" }, "Exportar em Word")),
  ];
}

// Backlinks (T81): notas de outros versículos que citam este. Clicar leva ao versículo da nota.
function backlinkSection(backlinks) {
  if (!backlinks.length) return null;
  return el("details", { class: "fold plain", open: true },
    el("summary", {}, el("b", {}, `Citado em notas (${backlinks.length})`)),
    el("p", { class: "group-note" }, "Notas que citam este versículo, escritas em outros versículos."),
    backlinks.map((note) => el("button", {
      class: "result", onclick: () => go({ book: note.book, chapter: note.chapter, verse: note.verse }),
    }, el("div", { class: "source" }, el("b", {}, refLabel(note.book, note.chapter, note.verse))),
      el("div", { class: "t" }, note.excerpt))));
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
$("#studies").addEventListener("click", () => openStudies());
$("#reading").addEventListener("click", () => openReading().catch((error) => showToast(`Não foi possível abrir: ${error.message}`)));
// Marcas no texto (notas e estudos): liga e desliga; a escolha fica no navegador.
function applyMarks(on) {
  document.body.classList.toggle("marks-off", !on);
  $("#marks").setAttribute("aria-pressed", String(on));
}
applyMarks(store.get("marks") !== "0");
$("#marks").addEventListener("click", () => {
  const on = document.body.classList.contains("marks-off");
  store.set("marks", on ? "1" : "0");
  applyMarks(on);
});
$("#studies-close").addEventListener("click", closeStudies);

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

// Menu Exibir (T84): as alternâncias da barra com o estado atual e a tecla de cada uma, quando há.
function showView() {
  const on = (id) => $(id).getAttribute("aria-pressed") === "true";
  const row = (label, keys, action, pressed) => {
    const props = { class: "view-row", onclick: () => { action(); showView(); } };
    if (pressed !== undefined) props["aria-pressed"] = String(pressed);
    return el("button", props, el("span", {}, label), keys ? el("kbd", {}, keys) : null);
  };
  openPanel("exibir", "Exibir",
    el("div", { class: "view-menu" },
      row("Paralelo: versões lado a lado", "p", () => $("#parallel").click(), on("#parallel")),
      row("Marcas: versículos com notas ou em estudos", null, () => $("#marks").click(), on("#marks")),
      row("Selecionar versículos", null, () => $("#select").click(), on("#select")),
      row("Fonte menor", null, () => $("#smaller").click()),
      row("Fonte maior", null, () => $("#larger").click()),
      row("Alternar tema claro e escuro", null, () => $("#theme").click()),
      row("Buscar ou ir para uma referência", "/", () => $("#q").focus()),
      row("Conjuntos de referências", null, () => openRefSets().catch(refSetFail)),
      row("Mapa de estudo e linha do tempo", null, () => openStudyMap().catch(refSetFail)),
      row("Atalhos de teclado", "?", () => showShortcuts())));
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
    if (!$("#studies-full").hidden) closeStudies();
    else if (!$("#topic-full").hidden) closeTopics();
    else if (!$("#graph-full").hidden) closeGraphFull();
    else if (!$("#preview").hidden) hidePreview();
    else if (!$("#panel").hidden) $("#panel-close").click();
    else if (selection.on) setSelectMode(false);
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
  const reason = event.reason;
  console.error(reason);
  // Falha de rede do navegador (fetch não chegou ao servidor) é diferente de erro do servidor ou do código.
  const network = reason instanceof TypeError && /fetch|NetworkError|Load failed/i.test(reason.message || "");
  showToast(network
    ? "Não foi possível conectar ao servidor da biblioteca. Verifique se ele está rodando."
    : `Não foi possível concluir a ação${reason && reason.message ? `: ${reason.message}` : "."}`);
});

init().catch((error) => {
  console.error(error);
  $("#text").replaceChildren(el("p", { class: "empty" }, "Não foi possível carregar a biblioteca."));
});
