# Proposta de design: de leitor com ferramentas a plataforma de estudo

Escrita em 2026-11-17, depois do fim do M7 (commit `8f41d96`). É uma
**proposta**: nada aqui está decidido. O que for aceito entra no
[BACKLOG.md](BACKLOG.md) como tarefa e, quando houver escolha, em
[DECISOES.md](DECISOES.md). Não substitui nenhuma tarefa existente; quando uma
fase coincide com uma tarefa do backlog, ela é citada pelo ID.

**Base das afirmações.** Li `app/static/app.js`, `index.html`, `style.css`,
`graph.js`, `app/server.py`, `xrefs.py`, `bridge.py`, `importer/db.py` e os
documentos de `docs/`. Consultei `/api/library` no servidor local (somente
leitura). **Não abri a interface no navegador** para esta proposta: o que diz
respeito a comportamento visto na tela vem dos relatórios de teste do backlog
(T08, T60–T66) ou da leitura do código, e está marcado como tal. Não há testes
automatizados da interface: `tests/` cobre só o importador.

---

## 1. Diagnóstico

### O que a interface já faz bem

- **A leitura é o centro.** O texto tem medida de 36rem, corpo de 20 px com
  entrelinha 1,75, numerais de estilo antigo e hifenização (`style.css`,
  `.reader > *` e `.text`); D018 garante ao texto pelo menos 448 px quando há
  colunas. Os títulos de perícope aparecem na leitura (T08).
- **A passagem está sempre no endereço** (`#/módulo/livro/capítulo/versículo`,
  `go()` em `app.js`), o que dá voltar, recarregar e copiar o link (D018).
- **O painel do versículo responde em escala**: 73 módulos, `/api/verse` em
  cerca de 0,23 s e 19 KB em Jo 3:16 (T08), comentários recolhidos com o texto
  integral sob demanda, filtro de idioma guardado, atalhos para as seções.
- **A ponte português ↔ inglês é explicada e desligável** (`bridgeNote`): o
  usuário vê "graça → grace G5485" e pode buscar só o que digitou (D013).
  É o diferencial do projeto e está bem resolvido na interface.
- **Procedência no conteúdo**: cada referência cruzada diz de que lista veio
  e quantas vezes foi citada junto (D015); cada verbete aberto mostra
  `Origem: caminho · chave` (`showItem`).
- **Marca por tipo** (T60) com contraste medido: de 4,88:1 a 10,64:1.
- **Colunas fixáveis** (T61), **paralelo** (T62), **comentário que acompanha**
  (T63), **folhear dicionários** (T64), **grafo** (T65) e **mapa por livro**
  (T66): o leitor já tem quase todas as peças de uma mesa de estudo.

### Onde é confuso (com evidência)

1. **Ferramentas sem nome.** A barra tem `Dic.`, `‖`, `◐`, `A−`, `A+` e
   `Strong` (`index.html`). Só os `title` explicam o que fazem; no celular não
   há passar o mouse. Três dos botões mudam o modo do texto (paralelo, Strong)
   e um abre um painel (Dic.), sem nada que os distinga.
2. **Um painel com seis modos e "voltar" feito à mão.** `openPanel` troca o
   conteúdo entre versículo, busca, item, palavra e folhear (o comentário em
   `app.js:369` ainda lista só três). Cada modo monta os próprios links de
   volta (`backToSearch`, `backVerse`); não há pilha de navegação. Abrir uma
   palavra a partir de um verbete aberto a partir da busca deixa dois "voltar"
   e perde o verbete.
3. **Fixar e acompanhar são parecidos, mas diferentes.** "Fixar" copia os nós
   do painel para a coluna (`pinCurrent`); "Fixar ao lado" remonta o item;
   "Acompanhar na leitura" cria um item que muda sozinho. As três ações moram
   em lugares distintos e o resultado aparece no mesmo lugar (as abas).
4. **Os identificadores mudam a cada importação.** O endereço e os itens
   fixados guardam `modules.id` e `comments.id`/`entries.id`
   (`layout.save`, `go`), que são números de sequência (`/api/library` mostra
   ids com lacunas: 1, 3, 5, 6, 23… porque as cópias unidas pela D011 foram
   apagadas). Uma importação completa ou incremental (D017, `forget_path`)
   pode renumerar: links guardados e fixados passam a apontar para outra
   coisa. Hoje é um incômodo; com notas, seria perda de dados.
5. **Erros silenciosos.** `api()` lança exceção em resposta não-OK, mas só
   `init()` e o carregamento de comentários tratam a falha; `showVerse`,
   `showWord`, `showSearch` e `showItem` não têm `catch`. Se o servidor cai, o
   clique não faz nada e não diz nada.
6. **Defeitos encontrados na leitura do código (não verificados no navegador):**
   - no modo paralelo, a linha recebe `onkeydown` como propriedade, mas `el()`
     só converte `onclick` e `ontoggle` em evento; o resto vira atributo de
     texto (`app.js:25` e `:260`). Enter numa linha do paralelo não seleciona;
   - `followReading` observa só `.v` (`app.js:457`); no paralelo as linhas são
     `.prow`, então o comentário acompanhando não segue a rolagem nesse modo;
   - no tema escuro escolhido pelo botão (`[data-theme="dark"]`), `--ot` e
     `--nt` não são redefinidos (estão só no bloco `prefers-color-scheme`, e
     duplicados ali, `style.css:27–28`): o grafo usa as cores do tema claro;
   - no toque, a prévia da citação depende de `mouseover`/`focusin`; tocar
     numa citação navega direto (`click` em `.ref`), e o leitor perde o
     comentário que estava lendo.

### O que falta para ser uma plataforma

Hoje o produto é **uma mesa de consulta**: tudo o que o usuário encontra
desaparece quando ele fecha o painel. Faltam quatro coisas, nesta ordem de
importância:

1. **Um lugar para guardar o que se achou** (notas, marcações, estudos). O
   único estado persistente é o `localStorage` (12 chaves: tema, fonte, versão,
   fixados, larguras…), que é preferência do aparelho, não dado do usuário.
2. **Um caminho de saída**: copiar com referência, exportar um estudo (T42).
3. **Uma visão da própria biblioteca**: que obras existem, de onde vieram, o
   que ficou de fora e por quê. O `import_log` e o relatório existem, mas só
   na linha de comando; o folhear (T64) lista só dicionários e livros.
4. **Uma busca que seja um lugar**, não um modo do painel: com 18.245
   comentários para "graça" (AVALIACAO-BUSCA-BILINGUE), a lista de 30 por
   página no painel estreito não serve para pesquisa de verdade.

---

## 2. Público e jornadas

O problema do projeto é o do próprio usuário: lê em português, o acervo
profundo está em inglês. As personas abaixo são hipóteses de uso para orientar
o desenho, não pesquisa com pessoas.

| Persona | Quem é | Do que precisa |
|---|---|---|
| **Pastor** | prega toda semana, lê inglês com esforço | ir da passagem ao sermão: contexto, palavras-chave, o que dizem 3 ou 4 comentaristas, ilustrações; guardar e reaproveitar |
| **Professor de escola dominical** | prepara uma aula por semana com pouco tempo; lê pouco inglês | esboço rápido, perguntas, referências cruzadas em português, algo para imprimir |
| **Estudante de teologia** | faz exegese, cita fontes em trabalhos | grego e hebraico, léxicos, comparar comentaristas, citação com procedência exata |
| **Leitor devocional** | lê um capítulo por dia | ler sem distração, marcar, anotar, continuar de onde parou |

### Jornadas e atritos atuais

**Professor: preparar uma aula sobre Romanos 8 em 40 minutos.**
1. Abre Rm 8 na ARA. *Sem atrito.*
2. Lê o capítulo com o JFB acompanhando (T63). *Funciona; mas o JFB está em
   inglês e o professor lê pouco inglês; as citações viram prévias em
   português (T24), o comentário não.*
3. Clica em Rm 8:28, vê as referências (lista ou grafo). *Bom.*
4. Quer guardar 5 referências, 2 trechos de comentário e um esboço de 3
   pontos. **Não há onde.** Copia para outro programa, perdendo a origem.
5. Imprime ou envia aos alunos. **Não há exportação.**

**Pastor: entender "propiciação" em Romanos 3:25 para o sermão.**
1. Liga Strong, clica na palavra, abre G2435 no painel Palavra. *Bom.*
2. Lê o Dodson; quer o Easton "propitiation" ao lado: fixa o painel Palavra,
   busca, abre o verbete. *Funciona (critério da T61), mas são 6 a 8 cliques
   e o caminho não é óbvio.*
3. Quer comparar Gill, Henry e Barnes em Rm 3:25 lado a lado. **Só um
   comentário por vez no painel**; fixar três vira três abas, não três colunas.
4. Quer guardar a definição com a fonte para citar. **Não há onde.**

**Estudante: levantar todas as ocorrências de ἀγάπη em João com a tradução
da ARA.**
1. Painel Palavra de G26: ocorrências da BSB com a expressão da ARA ao lado.
   *Bom.*
2. Quer filtrar por livro e exportar a lista. **Não há filtro nem
   exportação**; "Mais ocorrências" carrega de 30 em 30 no painel.

**Leitor devocional: ler um capítulo por dia e anotar.**
1. Abre o aplicativo: volta à última versão, mas a passagem só volta se o
   endereço estiver aberto (`readHash`); **não há "continuar de onde parei"**
   nem plano de leitura (B06).
2. Quer sublinhar um versículo e escrever uma frase. **Não há marcação nem
   nota.**

**Conclusão das jornadas:** a consulta está pronta; **guardar, organizar e
sair** não existem. As fases da seção 9 atacam exatamente isso.

---

## 3. Princípios de design

1. **O texto primeiro.** A Bíblia aberta é a tela inicial e a referência de
   todo o resto; painéis servem ao texto, nunca o cobrem por inteiro em tela
   larga. *Base:* D001 (tecnologia web escolhida pela tipografia), D018
   (texto com no mínimo 448 px).
2. **Procedência à vista, sempre conferível.** Todo trecho mostrado, citado,
   guardado ou exportado leva obra e chave de origem. Nenhuma síntese sem
   fonte. *Base:* D002, D007, D015, D016 e o princípio "tudo é verificável"
   do PLANO.
3. **Explicar, não decidir pelo usuário.** O aplicativo mostra por que trouxe
   algo e deixa desligar; compara comentaristas em vez de resumir. *Base:*
   D013 (ponte explicada e desligável), D015 (motivo de cada referência), P4
   (modelo de linguagem só opcional e por último).
4. **Local, offline e privado.** Nada sai da máquina; nada depende de rede,
   inclusive fontes tipográficas. *Base:* D001, D003, PLANO; descartes de
   nuvem e recursos sociais em IDEIAS.md.
5. **O que é do usuário nunca se perde.** Dados do usuário ficam em base
   separada, com chaves que sobrevivem à reimportação; a biblioteca é
   descartável, as notas não. *Base:* princípio do PLANO, critério do M4,
   D009 (nunca substituir sem verificar).

"Nada de decoração sem função" já está nas decisões (D019, descartes de M7 e
IDEIAS) e fica implícito em 1 e 3.

---

## 4. Arquitetura de informação

### Áreas

Quatro áreas no primeiro nível. **Estudar não é uma área**: é o que acontece
no Ler quando o painel e as colunas estão abertos, e no Meus estudos quando um
estudo está aberto. Separar "Ler" de "Estudar" obrigaria a escolher antes de
começar, e a jornada real alterna as duas a cada minuto.

| Área | O que vive nela | Existe hoje? |
|---|---|---|
| **Ler** | leitor, paralelo, Strong; painel (versículo, palavra, item, busca rápida); colunas fixadas; **coluna do estudo ativo** (nova) | sim, menos o estudo ativo |
| **Pesquisar** | busca em tela inteira: resultados por tipo, filtros (tipo, idioma, obra, livro bíblico), ponte explicada, histórico de buscas | só como modo do painel |
| **Biblioteca** | obras por tipo e idioma; folhear (T64); ficha da obra com procedência (arquivo, SHA-256, data, contagens); o que ficou de fora (`import_log`); créditos (T52); mais tarde, o assistente de importação (T50) | só o folhear |
| **Meus estudos** | estudos (esboço com passagens, citações e notas), notas soltas, marcações, etiquetas; exportar | não |

### Navegação

- **Barra superior** com as quatro áreas como abas nomeadas (texto, não
  ícone). Em menos de 560 px, a barra vira uma **barra inferior** de quatro
  alvos de 48 px.
- O **seletor de passagem** (versão, livro, capítulo) só aparece no Ler. A
  caixa de busca fica em todas as áreas: referência vai para o Ler; palavra
  abre o Pesquisar.
- As ferramentas do texto (paralelo, Strong, tamanho, tema) saem da barra e
  vão para um menu **"Exibir"** com rótulos escritos. `Dic.` some: folhear
  passa a ser a Biblioteca.
- **Endereço por área**: `#/ler/ARA/43/3/16`, `#/pesquisar?q=graça`,
  `#/biblioteca/gill`, `#/estudos/12`. O endereço antigo (`#/3/43/3/16`)
  continua aceito e é convertido. Usar a **sigla**, não o id, resolve o item 4
  do diagnóstico para links (ver seção 5). Isso refina a D018; exige decisão
  nova.

### Mapa do site

```
Ler  #/ler/{versão}/{livro}/{cap}[/{vers}]
├─ Texto: normal | paralelo (T62) | Strong (T20)
├─ Painel de estudo (uma pilha com voltar)
│  ├─ Versículo: versões · referências (lista | grafo | livros) · comentários · citado em
│  ├─ Palavra (Strong): original · traduções · léxicos · ocorrências
│  ├─ Item: comentário ou verbete, com procedência
│  └─ Busca rápida (os 5 primeiros de cada tipo + "abrir no Pesquisar")
├─ Colunas fixadas (abas; T61) e comentário acompanhando (T63)
└─ Estudo ativo (coluna; recebe "Adicionar ao estudo")
Pesquisar  #/pesquisar?q=…&tipo=…&idioma=…&obra=…
├─ Resultados agrupados: Bíblia · comentários · dicionários · livros
├─ Ponte explicada (D013) e, depois de M3, "por significado" (T33)
└─ Histórico de buscas (local)
Biblioteca  #/biblioteca[/{obra}]
├─ Obras por tipo e idioma, com contagem
├─ Ficha da obra: procedência, folhear títulos (T64), abrir no Ler
├─ Fora da biblioteca: arquivos ignorados e motivo (import_log)
└─ Créditos e licenças (T52) · Importar (T50)
Meus estudos  #/estudos[/{id}]
├─ Estudos: lista, abrir, exportar (T42)
├─ Notas: por passagem, por etiqueta
├─ Marcações
└─ Importadas do e-Sword (T41)
```

### Pilha do painel

O painel passa a ter uma **pilha**: cada abertura empilha a vista anterior;
um único "←" no cabeçalho volta. Os botões de volta de cada modo
(`backToSearch`, `backVerse`) somem. A pilha não vai para o endereço (o
endereço continua sendo a passagem, como a D018 escolheu).

---

## 5. Modelo de objetos de estudo

### Os objetos

| Objeto | O que é | Liga-se a |
|---|---|---|
| **Âncora** | um ponto citável: uma passagem (livro, capítulo, versículo, fim) ou um trecho de uma obra (obra, chave de origem, início e fim no texto) | biblioteca, por chave estável |
| **Marcação** | cor sobre uma âncora de passagem | âncora |
| **Nota** | texto do usuário (Markdown simples), com etiquetas, presa ou não a uma âncora | âncora, etiquetas |
| **Estudo** | título, passagem principal, estado (rascunho, pronto), e uma lista ordenada de **blocos** | blocos, etiquetas |
| **Bloco** | um item do esboço: título de seção, nota, passagem, citação de obra, palavra (Strong) ou referência cruzada | âncora ou Strong, ou só texto |

Um estudo **não copia** a Bíblia nem o comentário: guarda a âncora e, só para
citações de obra, uma cópia curta do trecho escolhido (ver abaixo).

### Chaves estáveis (pré-requisito)

Nada na base do usuário pode apontar para `modules.id`, `comments.id` ou
`entries.id`: mudam ao reimportar (diagnóstico, item 4). As chaves são:

- **Passagem:** (livro, capítulo, versículo) na versificação KJV, que é a
  referência única da D005. Estável enquanto a D005 valer; se a B10
  (versificação) for adotada, a conversão se aplica também às âncoras.
- **Obra:** `source_key = fonte + ":" + nome do arquivo em minúsculas`
  (`theword:gill.cmt.twm`). Não usar `origin_path` inteiro (contém a pasta do
  usuário e muda se o programa for reinstalado), nem o SHA-256 (muda quando a
  obra é atualizada). Exige conferir que não há dois arquivos com o mesmo
  nome na mesma fonte; se houver, desempatar pela pasta.
- **Item da obra:** `origin_key`, que já está em `comments`, `entries` e
  `verses` (D002). Falta índice em `comments(module_id, origin_key)`; os
  verbetes já têm (`entries_by_origin`, D014).

### Esquema proposto de `data/user.db`

```sql
create table meta(key text primary key, value text);   -- schema_version, criado_em

-- Obras citadas pelo usuário: identidade estável, sem conteúdo.
create table sources(
    source_key text primary key,       -- 'theword:gill.cmt.twm'
    abbr text, title text, kind text, lang text,
    last_sha256 text, last_seen text   -- para avisar quando a obra mudou ou sumiu
);

create table anchors(
    id integer primary key,
    book integer not null, chapter integer not null, verse integer,
    to_chapter integer, to_verse integer,          -- passagem (D005)
    source_key text references sources(source_key), -- nulo = passagem bíblica
    origin_key text,                                -- item da obra
    start integer, end integer,                     -- trecho no texto gravado (como refs, D016)
    quote text,                                     -- cópia do trecho, no máximo 1.000 caracteres
    quote_sha256 text                               -- para notar mudança na origem
);
create index anchors_by_ref on anchors(book, chapter, verse);

create table highlights(id integer primary key, anchor_id integer not null references anchors(id),
                        color text not null, created_at text not null);
create table notes(id integer primary key, anchor_id integer references anchors(id),
                   body text not null, created_at text not null, updated_at text not null);
create table studies(id integer primary key, title text not null,
                     book integer, chapter integer, verse integer, to_chapter integer, to_verse integer,
                     status text not null default 'rascunho', created_at text, updated_at text);
create table study_blocks(id integer primary key, study_id integer not null references studies(id),
                          pos integer not null,
                          kind text not null,      -- 'titulo' | 'nota' | 'passagem' | 'citacao' | 'palavra' | 'referencia'
                          anchor_id integer references anchors(id),
                          strong text, body text);
create table tags(id integer primary key, name text unique not null);
create table note_tags(note_id integer, tag_id integer, primary key (note_id, tag_id));
create table study_tags(study_id integer, tag_id integer, primary key (study_id, tag_id));
-- Origem de dados vindos de fora (T41: notas do e-Sword), com procedência.
create table imports(id integer primary key, origin_path text, origin_sha256 text,
                     imported_at text, notes_count integer);
```

Nada é apagado de fato sem o usuário pedir: `notes`, `studies` e `highlights`
podem ganhar `deleted_at` (lixeira) na implementação.

### Por que guardar `quote`

É a única cópia de conteúdo da biblioteca na base do usuário, e é pequena por
regra. Serve a três coisas: (1) exportar sem a biblioteca aberta; (2) detectar
que a obra mudou (o trecho na nova importação não bate com `quote_sha256`) e
mostrar "o texto na origem mudou desde que você citou"; (3) não perder a
citação se a obra sair da biblioteca. A procedência continua sendo
`source_key + origin_key`; `quote` não é fonte, é lembrança. Como `data/` está
fora do git (D007), a cópia de texto protegido não é distribuída.

### Derivado e do usuário

| | Biblioteca (`library.db`) | Usuário (`user.db`) |
|---|---|---|
| Origem | módulos do e-Sword e do theWord | o que o usuário escreve ou escolhe |
| Reprodutível | sim, reimportando (PLANO) | não: é original |
| Pode ser apagada | sim, e é substituída (D009) | nunca pelo aplicativo nem pelo importador |
| Escrita por | só o importador | só o servidor, por pedido da interface |
| Conexão no servidor | somente leitura (`mode=ro`, `server.py:28`) | leitura e escrita, separada |
| Cópia de segurança | desnecessária | a cada abertura, cópia diária com rotação (proposta) |
| Chaves para a outra | — | passagem KJV, `source_key`, `origin_key` |

O servidor resolve as âncoras na leitura: procura o módulo pelo `source_key`,
o item pelo `origin_key` e confere o trecho. As junções são feitas em Python
(volumes pequenos), sem `attach`, para a conexão da biblioteca continuar
somente leitura.

O `localStorage` continua para **preferências do aparelho** (tema, fonte,
larguras, filtros). Os itens fixados passam a guardar chaves estáveis em vez
de ids.

---

## 6. Padrões de interação

| Padrão | Proposta | Existe hoje? |
|---|---|---|
| **Abrir** | clique no versículo abre o painel; clique em citação mostra a prévia e só navega com um segundo clique ou com "Ir"; no toque, tocar sempre mostra a prévia primeiro | parcial: clique navega direto (`.ref` em `app.js`) |
| **Voltar no painel** | uma pilha, um botão "←" no cabeçalho | não: links de volta por modo |
| **Fixar** | um só verbo, "Fixar", em todo item do painel; "Acompanhar" vira opção do item fixado de comentário ("seguir a leitura: sim/não") | sim, em três formas (T61, T63) |
| **Comparar** | colunas fixadas lado a lado em tela larga (até 3 visíveis), não só abas; "Comparar comentários" no painel do versículo abre os escolhidos em colunas | versões sim (T62); comentários não |
| **Selecionar e agir** | selecionar texto num comentário ou versículo mostra uma barra pequena: Copiar com referência · Marcar · Nota · Adicionar ao estudo | não |
| **Anotar** | nota curta presa ao versículo, sinal discreto (ponto na margem) no texto; edição no painel do versículo, seção "Minhas notas" no topo | não (M4) |
| **Estudo ativo** | um estudo pode estar "ativo": aparece como coluna; todo item tem "Adicionar ao estudo", que acrescenta um bloco com a âncora | não |
| **Exportar** | do estudo: Markdown primeiro (procedência em notas de rodapé: obra, chave, arquivo); Word depois (T42); copiar versículo com referência e versão | não |
| **Estados vazios** | dizer o que fazer: "Nenhuma nota neste capítulo. Selecione um texto e escolha Nota." Hoje há bons exemplos ("Nenhum comentário cobre este versículo.") | parcial |
| **Erros** | toda chamada à API com estado de carregando (`aria-busy`) e mensagem de erro no lugar do conteúdo, com "Tentar de novo"; servidor fora do ar: faixa no topo | não (só o grafo usa `aria-busy`) |
| **Salvar** | gravação automática na base do usuário, com indicador "Salvo"; falha de gravação mantém o texto na tela e avisa | não |
| **Offline** | o aplicativo já é local; o único "offline" relevante é o servidor parado. Fontes embutidas, nada de rede | sim, menos as fontes (ver 7) |

### Atalhos de teclado (propostos)

Nenhum atalho global existe hoje; há Enter/espaço no versículo
(`app.js:1203`), setas nas divisórias (`app.js:640`) e Enter nos nós do grafo
(`graph.js:144`).

| Tecla | Ação |
|---|---|
| `/` | foco na busca |
| `[` e `]` | capítulo anterior e seguinte |
| `j` e `k` | versículo seguinte e anterior (abre o painel) |
| `Esc` | fecha a prévia; depois volta na pilha; depois fecha o painel |
| `f` | fixar o que o painel mostra |
| `n` | nota no versículo selecionado |
| `e` | adicionar ao estudo ativo |
| `p` | liga ou desliga o paralelo |
| `?` | lista dos atalhos |

Letras simples só valem fora de campos de texto. Setas ficam livres para
rolagem e divisórias.

---

## 7. Sistema visual

Parto de `style.css`, que já tem uma base boa: paleta quente de papel,
serifa para leitura, sem-serifa para interface, seis cores de tipo medidas
(T60). Proponho **acrescentar tokens e corrigir**, não reescrever.

### Cor

- **Corrigir:** redefinir `--ot` e `--nt` em `:root[data-theme="dark"]` e
  tirar a linha duplicada do bloco `prefers-color-scheme` (`style.css:27–28`).
- **Evitar a duplicação** que causou o defeito: os valores escuros estão
  escritos duas vezes (bloco de mídia e bloco de tema). Proposta: o script do
  `index.html` grava `data-theme` sempre (a partir da preferência do sistema
  quando o usuário não escolheu) e o CSS fica com um único bloco escuro,
  `:root[data-theme="dark"]`.
- **Novos tokens semânticos** para os estados que vão surgir: `--danger`
  (erro), `--ok` (salvo), `--note` (sinal de nota na margem) e quatro cores de
  marcação (`--hl-1..4`) com versão escura, todas medidas contra `--paper` e
  `--surface` com o mesmo critério da T60 (texto 4,5:1; marcação de fundo com
  o texto por cima a 4,5:1).

### Tipografia

| Uso | Hoje | Proposta |
|---|---|---|
| Leitura | `--serif`: Literata, Iowan, Palatino… | manter; **embutir Literata** (licença OFL, a conferir) em `app/static/fonts/`, porque hoje ela só aparece se estiver instalada |
| Interface | `--sans`: Segoe UI, sistema | manter |
| Grego | `--original`: Gentium Plus, SBL Greek… | separar em `--greek` (Gentium Plus embutida, OFL, a conferir) |
| Hebraico | o mesmo `--original` | `--hebrew` próprio (candidata: Ezra SIL ou SBL Hebrew; conferir licenças), corpo 1,15× e entrelinha maior por causa dos pontos vocálicos |
| Tamanhos | 10, 11, 12, 13, 15 px espalhados | escala de 6 passos (`--fs-xs` 12 px … `--fs-xl`); **nada abaixo de 12 px**: hoje `.badge` e `i.kind` têm 10 px e `.origin` 11 px |

Fontes embutidas cumprem o princípio 4 (offline) e dão a mesma aparência em
qualquer máquina; a licença de cada uma vai para DECISOES e para a tela de
créditos (T52).

### Espaçamento e forma

Hoje os valores são soltos (4, 6, 8, 10, 12, 14, 18, 22, 24 px). Proposta: uma
escala de 4 px (`--sp-1` = 4 … `--sp-6` = 32) e dois raios (`--r-sm` 4 px,
`--r-md` 8 px), aplicada aos poucos, arquivo por arquivo, sem mudar a
aparência de uma vez.

### Temas

Claro e escuro já existem e foram medidos (T60). Proposta pequena: um terceiro
valor "sépia/leitura noturna" **não** entra agora; o ganho é baixo e cada tema
dobra a medição de contraste.

---

## 8. Responsividade e acessibilidade

### Pontos de quebra

Hoje há quatro: 1100 px (colunas se revezam, D018), 820 px (painel embaixo),
760 px (grafo, por `matchMedia` na janela, `app.js:831`) e 560 px (barra
compacta). Proposta:

- manter 560, 820 e 1100 para a página;
- o grafo e o mapa por livro dependem da **largura do painel**, não da
  janela: usar `@container` no painel (grafo a partir de 420 px de painel, que
  é a largura usada na validação da EC8);
- abaixo de 560 px: barra inferior com as quatro áreas.

### Alvos de toque

Hoje: botões e seletores de 36 px; `.chip` de 28 px; abas fixadas de 30 px;
barras do mapa por livro com 3 a 16 px de largura (`.bk-bar`). Proposta: com
`@media (pointer: coarse)`, mínimo de 44 px para tudo que é tocável; no mapa
por livro, no toque, as barras viram só leitura e a seleção fica nos chips
(que já existem).

### Contraste

Medido na T60 para texto e etiquetas de tipo (4,88:1 a 10,64:1). **Não
medido:** o grafo no tema escuro escolhido pelo botão (afetado pelo defeito de
`--ot`/`--nt`), os traços das ligações do grafo (`stroke-opacity .18`),
`--muted` sobre `--accent-soft` (nota da ponte) e o realce `mark` no escuro.

### Teclado e leitor de tela

| Item | Estado |
|---|---|
| Versículo como botão com Enter | existe (`role="button"`, `tabindex="0"`) |
| Divisórias por teclado | existe (T61) |
| Grafo navegável por Tab e Enter, com rótulo | existe (T65, `graph.js:131`) |
| Paralelo por teclado | **quebrado** (diagnóstico, item 6) |
| Foco ao abrir o painel | não vai para o painel; quem usa teclado precisa atravessar o capítulo inteiro (um versículo é uma parada de Tab: até 176 em Sl 119) |
| Abas fixadas | têm `role="tab"`, mas falta `tabpanel` e setas entre abas |
| Anúncio de mudanças | não há região `aria-live` (busca concluída, salvo, erro) |
| Movimento | `scrollIntoView({behavior: "smooth"})` e transições sem `prefers-reduced-motion` |
| Zoom a 200% | não testado |
| Leitor de tela | **nunca testado** (nenhum registro no backlog) |

Propostas: o texto do capítulo com um único ponto de Tab e setas entre os
versículos (*roving tabindex*); levar o foco ao título do painel quando ele
abre; região `aria-live="polite"` para estado; respeitar
`prefers-reduced-motion`; testar uma vez com NVDA no Windows e registrar.

### O que já foi testado (segundo o backlog)

T08: 1280 e 375 px, dois temas. T60: contraste medido nos dois temas. T61:
1280, 1024, 768 e 375 px, dois temas. T65: teclado no grafo, só lista abaixo
de 760 px. T62: colunas empilhadas em tela estreita. Nada registrado sobre
leitor de tela, zoom, toque real ou movimento reduzido.

---

## 9. Roteiro de entrega

Fases pequenas, cada uma um commit (ou poucos), na ordem. "Fase" aqui não é
marco: as fases D1–D8 entram no backlog como tarefas se o usuário aceitar.
Quando uma fase **é** uma tarefa existente, ela é citada e não duplicada.

| Fase | Entrega | Critério de aceite verificável | Depende de |
|---|---|---|---|
| **D1** Correções | os 4 defeitos do diagnóstico (Enter no paralelo, acompanhar no paralelo, `--ot`/`--nt` no escuro, prévia no toque); erros da API com mensagem e "Tentar de novo" | Enter numa linha do paralelo seleciona; com o servidor parado, clicar num versículo mostra a mensagem; grafo no escuro escolhido usa as cores escuras (conferir com o inspetor); console sem erros | — |
| **D2** Rótulos e atalhos | menu "Exibir" com rótulos; atalhos da seção 6; `?` mostra a lista; foco vai ao painel ao abrir; pilha de "voltar" no painel | percorrer a jornada do pastor (seção 2) só pelo teclado; nenhum botão da barra só com símbolo; nenhuma função do painel perdida (comparar com os testes de T08, T20, T23, T24, T61–T66) | — |
| **D3** Chaves estáveis | `source_key` calculado na leitura de `modules`; endereço `#/ler/{sigla}/…` (aceita o antigo); fixados guardados por chave; índice em `comments(module_id, origin_key)` | reimportar a base de amostras e recarregar: o link e os fixados abrem o mesmo conteúdo; `verify.py` passa; nova decisão que refina a D018 | decisão do usuário (pergunta 2) |
| **D4 = T40** Base do usuário | `user.db`, esquema da seção 5; servidor com `POST` só para `/api/user/*`, conferindo `Origin` e `Host`; marcações e notas no Ler | **critério do M4:** reimportar a biblioteca (completa e incremental) não altera nenhuma nota (contar e comparar hash do `user.db`); nota presa a trecho de comentário reaparece no mesmo trecho; página de outra origem não consegue gravar (teste com `curl` e `Origin` falso) | D3, pergunta 3 |
| **D5** Estudos | Meus estudos; estudo ativo como coluna; "Adicionar ao estudo" em versículo, referência, palavra, trecho de comentário | jornada do professor (Rm 8) feita em menos de 40 minutos sem sair do aplicativo, com 5 referências, 2 citações e 3 tópicos; cada citação mostra obra e chave | D4 |
| **D6 = T42** Exportar | Markdown do estudo com procedência em rodapé; depois Word | o Markdown abre em qualquer editor; cada citação tem obra, chave e arquivo; nada de texto além dos trechos citados | D5 |
| **D7** Pesquisar como área | busca em tela inteira com filtros por tipo, idioma, obra e livro bíblico; o painel mostra só os 5 primeiros de cada tipo | "graça" com filtro "comentários · inglês · Romanos" lista só esses; voltar mantém filtros e posição; prepara T33 (busca híbrida) sem mudar a tela | D2 |
| **D8** Biblioteca | obras por tipo; ficha com procedência; arquivos fora da biblioteca com motivo; folhear (T64) dentro dela; lugar reservado para T50 e T52 | as 73 obras aparecem com contagem igual à de `modules`; os 49 arquivos de `import_log` aparecem com motivo em linguagem simples | — (T50 e T52 dependem de P1) |
| **D9** Visual e acessibilidade | fontes embutidas, escala tipográfica (mínimo 12 px), tokens de espaçamento e de estado, alvos de 44 px no toque, `aria-live`, movimento reduzido, *roving tabindex* | contraste medido nos dois temas para os tokens novos; 1280, 1024, 768 e 375 px sem rolagem horizontal; um teste com NVDA registrado no backlog | licenças das fontes conferidas |

Encaixe com o que já está no backlog:

- **T41** (importar notas do e-Sword) entra depois de D4, gravando em
  `imports` e `notes` com procedência.
- **M3 (T30–T34)** não muda a arquitetura: T33 vive no Pesquisar (D7) como
  "por significado", sempre com a explicação do porquê; T34 é uma seção do
  painel do versículo. Continua dependendo de P3.
- **M5 (T50–T52)** cabe na Biblioteca (D8). Depende de P1.
- **M6** e B17/B19 ficam fora deste roteiro (P4). Se vierem, entram como
  blocos de estudo marcados "gerado por máquina", nunca como fonte.
- **P5 (Notion):** a exportação em Markdown (D6) permite colar no Notion sem
  sincronização; nenhuma fase depende de Notion.
- **B06** (planos de leitura) e **B16** (áreas de trabalho) ficam em IDEIAS;
  o "continuar de onde parei" do leitor devocional pode entrar em D2 como
  preferência local (última passagem), sem plano.

Ordem sugerida: D1 → D2 → D3 → D4 → D5 → D6, com D7, D8 e D9 em paralelo
quando houver folga. D1 e D2 não dependem de nenhuma resposta.

---

## 10. Riscos e perguntas

### Riscos

- **Escrita local abre uma porta.** Hoje o servidor só lê; com `POST`, uma
  página qualquer aberta no navegador pode tentar gravar em
  `localhost:8377`. Mitigação: conferir `Origin`/`Host`, aceitar só JSON,
  nunca `GET` que grava.
- **`app.js` tem 1.219 linhas num arquivo só**, com estado global e o painel
  misturado às colunas. Cada fase acima mexe nele. A EC9 já alertava. Separar
  em módulos ES (`panel.js`, `layout.js`, `user.js`) antes de D4 reduz o
  risco; a D004 (sem framework, sem build) continua válida com módulos
  nativos.
- **Sem testes da interface.** Toda verificação é manual no navegador. Um
  roteiro de verificação escrito (as jornadas da seção 2) evita regressões.
- **`source_key` por nome de arquivo** falha se dois arquivos tiverem o mesmo
  nome em pastas diferentes da mesma fonte. Conferir na base antes de D3.
- **Escopo:** as quatro áreas são muita coisa para um projeto pessoal. Se o
  projeto não for público (P1), D7 e D8 podem ficar menores.

### Perguntas para o usuário

| # | Pergunta | Recomendação |
|---|---|---|
| 1 | Para quem é o produto primeiro: você estudando (pregação, aulas?) ou outras pessoas? Muda a ordem entre D5–D6 e D8 (P1). | Você primeiro: D1–D6 antes de D8; o produto público (M5) depois. |
| 2 | Aceita trocar o id do módulo pela sigla no endereço (`#/ler/ARA/43/3/16`) e guardar fixados por chave estável? Refina a D018. | Sim: é pré-requisito de notas que sobrevivam à reimportação. |
| 3 | Aceita que o servidor passe a gravar, só em `data/user.db`, com cópia de segurança diária? | Sim, com as proteções da seção 10; guardar notas no `localStorage` seria frágil. |
| 4 | Pode guardar no estudo uma cópia curta (até 1.000 caracteres) do trecho citado de uma obra, mesmo protegida, para exportar e detectar mudanças? | Sim: fica em `data/`, fora do git (D007), e é uso pessoal. |
| 5 | Aceita embutir fontes com licença OFL (Literata, Gentium Plus e uma hebraica) no repositório? Não é dependência de Python (P3), mas é dado externo. | Sim, depois de conferir cada licença na origem e registrar em DECISOES. |
