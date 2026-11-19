# UX no celular (Galaxy S23 Ultra, Chrome Android): diagnóstico e proposta

Data: 2026-11-19. Avaliação e proposta apenas; nada em `app/static` foi alterado.

## Resumo

No celular, a barra superior fica **sempre visível** e ocupa **265 px de 915 (29% da
tela)**, com 23 controles em 5 linhas, todos na parte de cima, onde o polegar não
alcança no S23 Ultra. Somada à faixa "Continuar de onde parou" (187 px), o texto de
João 1 começa em y=599 e **só 3 versículos aparecem inteiros** na primeira tela. A
folha do versículo cobre o próprio versículo aberto. Recomendação: cabeçalho de uma
linha ("João 1 ▾" e versão) que some ao rolar, barra inferior fixa com
`‹ Buscar Estudo Aa ⋯ ›`, e o resto numa folha "Mais" agrupada. Tudo dentro de
`@media (max-width: 560px)`, sem mudar o desktop.

## Como foi testado

- Servidor local com `data/library.db` (o preview subiu na porta 8379 porque a 8377
  estava ocupada). Navegador do painel com emulação de 412 × 915 e 360 × 800
  (`pointer: coarse` ativo, DPR 2).
- **Capturas de tela falharam** (tempo esgotado em todas as tentativas). As medidas
  abaixo vêm de `getBoundingClientRect` no próprio navegador emulado; não há imagem.
- O navegador de teste tinha estado salvo de rodadas anteriores (modo paralelo
  ligado, faixa "Continuar" com João 3:6 e um estudo de teste). Desliguei o paralelo
  para medir a leitura normal e restaurei o `localStorage` ao final.
- Não testado: aparelho real, toque real, teclado virtual, botão/gesto "voltar" do
  Android, tema escuro no celular. Não gravei nota (para não criar dados); o fluxo
  (e) foi avaliado até o campo e o botão.
- Observação: a largura CSS real do S23 Ultra no Chrome depende da resolução e do
  zoom de tela escolhidos no aparelho; vale abrir o site no aparelho e conferir
  `innerWidth`. Usei 412 × 915 como pedido.

## Medidas (412 × 915)

| Elemento | Posição / tamanho |
|---|---|
| Barra superior (`.bar`) | y 0 a 265, **265 px**, fixa (não rola) |
| Linha 1: versão, ‹, livro, capítulo, › | y 8, 44 px de altura; ‹ e › com 36 px de largura |
| Linha 2: campo de busca | y 60, 388 × 44 |
| Linhas 3 a 5: 15 botões de ferramentas | y 112, 162 e 212 (3 linhas, 144 px) |
| Faixa "Continuar de onde parou" | y 289, **187 px** (duas ações: leitura e estudo) |
| Título "João 1" | y 515 (sem a faixa: y 339) |
| Início do texto | **y 599** (sem a faixa: y 406) |
| Área de leitura (`.reader`, rolagem interna) | 651 px de altura |
| Versículos inteiros na 1ª tela | **3 de 51** (4 começam); sem a faixa: 6 |
| Linha de texto | 35 px (fonte 20 px × 1,75); cabem cerca de 14 linhas sem a faixa |

Em 360 × 800: a barra também tem 265 px (5 linhas), o texto começa em y 599, só
**2 versículos** inteiros; o seletor de livro fica com 86 px de largura. Sem rolagem
horizontal nas duas larguras (largura do documento = viewport).

Em desktop 1280 × 800: a barra tem 101 px em **duas linhas** (já registrado em
UX-NOTAS-RODADA como incômodo).

## A. Diagnóstico

### A1. A primeira dobra é dos controles, não do texto

- 265 px de barra + 187 px de faixa "Continuar" + título = o texto começa a 65% da
  altura da tela. A barra não some ao rolar: o `body` tem `height: 100%` e a rolagem
  é do `.reader` (`overflow-y: auto`), então a barra fica parada e ocupa 29% da tela
  o tempo todo.
- Consequência adicional (comportamento conhecido do Chrome Android, não verificado
  no aparelho): como o documento não rola, a barra de endereço do Chrome **não se
  recolhe**, e perdem-se mais uns 56 px.
- A barra mistura três naturezas de controle no mesmo nível: navegação (livro,
  capítulo), ações raras (Memorizar, Tópicos, Dicionários, Diário) e preferências
  (A−, A+, Tema, Marcas). Não há hierarquia.

### A2. Tudo fica onde o polegar não alcança

- Todos os 23 controles estão entre y 8 e y 256, na faixa de cima do S23 Ultra
  (6,8"), a região mais difícil para uma mão. Anterior e próximo capítulo, a ação
  mais repetida da leitura, estão em y 8.
- A folha do versículo (y 275 a 915) tem o × em y 285, também no alto, e com 36 px
  de largura (abaixo dos 44/48 recomendados; `min-height` é 44, a largura não).
- "Fechar · Esc" das telas cheias (Meus estudos, Temas, grafo) é um `.chip` com
  **40 px** de altura, no canto superior direito, e cita a tecla Esc, que não existe
  no celular.

### A3. Duplicação e rótulos pensados para teclado

- O menu **Exibir** (T84) repete sete itens que já estão na barra: Paralelo, Marcas,
  Selecionar, Fonte menor, Fonte maior, Tema e Buscar. Inclui "Atalhos de teclado" e
  mostra teclas (`p`, `/`, `?`) que não servem no toque. No celular ele só acrescenta
  uma linha de botão.
- Texto de ajuda: "**Clique** em um versículo..." (deveria ser "Toque" em tela de
  toque).
- Nomes parecidos e ambíguos lado a lado: "Tópicos" (notas por tópico) e "Temas"
  (pesquisa por tema); "Tema" (claro/escuro) ao lado de "Temas". Só o `title`
  explica, e `title` não aparece no toque.

### A4. Perda de contexto ao abrir o painel

- Busca "graça": o resultado abre a folha inferior (y 275, 641 px). Sobra **10 px**
  de texto visível entre a barra (fim em 265) e a folha. O usuário vê barra + folha,
  sem a leitura.
- Abrir o resultado Romanos 11:6: o leitor vai a Romanos 11 e destaca o versículo
  em y 522, **atrás da folha**. O usuário não vê o versículo que abriu.
- Abas do painel do versículo: Versões, Minhas notas, Parecidas, Referências,
  **Comentários (x 386)** e **Citado em (x 492)**. As duas últimas ficam fora da tela
  de 412 px; só se descobrem rolando a faixa de abas para o lado.
- "Leitura de hoje" abre na mesma folha; com nenhum plano, a primeira coisa é uma
  lista de 66 livros.
- Navegação por hash: cada versículo tocado vira entrada no histórico. Pelo código,
  o "voltar" do Android troca de passagem em vez de fechar a folha (não há
  `pushState` para painéis). Não verificado no aparelho.

### A5. Fluxos do usuário (contagem de toques, 412 × 915)

| Fluxo | Hoje | Atrito principal |
|---|---|---|
| a) abrir e ler João 1 | 0 toques | 3 versículos visíveis; texto começa em y 599 |
| b) próximo/anterior capítulo | 1 toque | botão de 36 × 44 em y 8, fora do alcance |
| b) trocar de livro | 2 toques + rolar lista nativa de 66 itens | seletor de 86 a 112 px corta nomes longos; capítulo é outro seletor |
| c) buscar "graça" e abrir | toque no campo (y 60), digitar, Enter, rolar folha, tocar | resultado começa em y 635; versículo aberto fica atrás da folha |
| d) painel do versículo | 1 toque no versículo | cobre o versículo; 2 abas escondidas à direita |
| e) nota | 1 toque + aba "Minhas notas" + campo + Salvar | campo em y 476, Salvar em y 603: com o teclado aberto (cerca de 40% da tela), o Salvar tende a ficar atrás dele (não verificado) |
| f) Exibir → tema | 2 toques (Exibir y 212, linha y 574), ou 1 toque em "Tema" | duplicado; Exibir abre por cima do texto |
| g) fonte | 1 toque por passo (A− / A+, 34 px de largura) | sem indicação do tamanho atual; passos um a um |
| h) Meus estudos / Leitura de hoje | 1 toque (y 112) | Estudos abre em tela cheia; Leitura em folha: dois padrões diferentes |

## B. Propostas de organização para o celular

Todas valem só até 560 px de largura (o mesmo ponto de corte já usado no CSS). O
desktop fica como está.

### Alternativa 1 (recomendada): cabeçalho mínimo + barra inferior + folha "Mais"

```
┌──────────────────────────────────────┐
│  João 1 ▾                    ARA ▾   │  48 px; some ao descer, volta ao subir
├──────────────────────────────────────┤
│ ▸ Continuar: João 3:6        Abrir × │  44 px, uma linha (só se houver)
│                                      │
│ JOÃO 1                               │
│ ¹ No princípio era o Verbo, e o      │
│ Verbo estava com Deus, e o Verbo     │
│ era Deus. ² Ele estava no princípio  │
│ com Deus. ³ Todas as coisas foram    │
│ feitas por intermédio dele...        │
│                 (cerca de 20 linhas) │
│                                      │
├──────────────────────────────────────┤
│  ‹    🔍     📖      Aa     ⋯     ›  │  56 px + área segura; sempre visível
│     Buscar Estudo  Texto  Mais       │
└──────────────────────────────────────┘
```

- **Cabeçalho (topo, 48 px):** "João 1 ▾" abre o seletor de passagem (folha com grade
  de livros AT/NT e depois grade de capítulos, botões de 48 px); "ARA ▾" abre a
  lista de versões. Sai do topo: busca, ferramentas, A−/A+, tema.
- **Barra inferior (56 px + `env(safe-area-inset-bottom)`):** 6 alvos de 68 px
  (412) ou 60 px (360) de largura.
  - `‹` e `›`: capítulo anterior e próximo, no alcance do polegar, nas pontas.
  - **Buscar:** abre a busca em tela própria (campo no topo com teclado, recentes
    abaixo, resultados em lista). Tocar num resultado fecha a busca e leva ao
    versículo; um "← Resultados" no cabeçalho volta.
  - **Estudo:** folha "Estudo" com Leitura de hoje (primeiro, é diária), Meus
    estudos, Diário, Memorizar e Notas por tópico.
  - **Aa:** painel de texto, como nos leitores de livros: tamanho (− valor +),
    tema (Claro, Escuro, Sistema), Marcas no texto, Palavras originais (Strong).
  - **⋯ Mais:** folha agrupada (abaixo).
- **Folha "Mais"** (substitui o Exibir no celular), com títulos de grupo:
  - *Ler:* Versões em paralelo, Selecionar versículos.
  - *Ferramentas:* Pesquisa por tema, Dicionários e livros, Conjuntos de
    referências, Mapa de estudo.
  - *Preferências:* Texto (Aa), Atalhos de teclado só quando `pointer: fine`.
- **Ao rolar:** o cabeçalho some ao descer e volta ao subir ou ao chegar no topo;
  a barra inferior fica (é a navegação). Para isso, no celular, a rolagem passa do
  `.reader` para o documento; o Chrome então recolhe também a barra de endereço.
- **Folha do versículo:** abre a 60% da altura com alça; ao abrir, o leitor rola
  para que o versículo fique visível acima da folha; arrastar a alça leva a 92% ou
  fecha; × com 48 × 48; "voltar" do Android fecha a folha. Abas que não cabem:
  "Notas" como segunda aba e um indicador de que a faixa rola (sombra na borda
  direita), ou abas em duas linhas.

**Primeira dobra estimada** (cálculo, não medido): texto a partir de cerca de y 150
(cabeçalho 48 + faixa 44 + título); área até y 859 (915 − 56). São cerca de 700 px,
ou 20 linhas de 35 px, contra 9 linhas hoje com a faixa.

### Alternativa 2: só a barra superior compacta + "⋯"

- Linha única no topo: `‹  João 1 ▾  ›  🔍  ⋯`. O "⋯" abre a mesma folha
  agrupada (com Estudo e Aa dentro dela).
- Prós: menor mudança; libera cerca de 210 px.
- Contras: mantém todas as ações no alto (alcance ruim no S23 Ultra); Estudo e fonte
  passam a exigir 2 toques.

### Alternativa 3: tela limpa com um botão flutuante

- Cabeçalho "João 1 ▾" que some ao rolar; um botão redondo de 56 px no canto
  inferior direito abre uma folha com tudo (navegação, busca, estudo, Aa, mais).
- Prós: máximo de texto; bom para leitura longa.
- Contras: descoberta pior; anterior/próximo exigem 2 toques; o botão cobre o fim
  das linhas.

**Por que a 1:** põe as ações frequentes (capítulo, busca, estudo, fonte) num toque e
no alcance do polegar, devolve cerca de 2,3 vezes mais texto na primeira tela e não
mexe no desktop.

### O que fica na primeira linha e o que vai para o menu

| Controle | Celular | Motivo |
|---|---|---|
| Livro e capítulo | Cabeçalho ("João 1 ▾") | contexto principal; um toque abre o seletor |
| Versão | Cabeçalho (sigla curta) | contexto; troca menos frequente |
| Anterior / próximo | Barra inferior, pontas | ação mais repetida da leitura |
| Busca / ir para referência | Barra inferior → tela própria | frequente; precisa de espaço e teclado |
| Meus estudos, Leitura de hoje, Diário, Memorizar, Tópicos | Folha "Estudo" | mesmo assunto; Leitura de hoje primeiro |
| A−, A+, Tema, Marcas, Strong | Painel "Aa" | preferências de exibição, ajustadas raramente |
| Paralelo, Selecionar | "Mais" → Ler | uso ocasional; Selecionar já tem barra própria |
| Temas, Dicionários, Conjuntos, Mapa | "Mais" → Ferramentas | consulta ocasional |
| Exibir | Some no celular (vira "Mais") | hoje duplica a barra |
| Atalhos de teclado | Só com mouse/teclado | inútil no toque |

## C. Mudanças priorizadas

| # | Problema | Mudança | Esforço | Risco para o desktop |
|---|---|---|---|---|
| 1 | Barra de 265 px fixa | Até 560 px: esconder `.tools` e o campo de busca; cabeçalho com "João 1 ▾" e versão | Médio | Baixo (só media query) |
| 2 | Ações fora do alcance | Barra inferior fixa `‹ Buscar Estudo Aa ⋯ ›`, 56 px + área segura; `padding-bottom` no leitor | Médio | Baixo (elemento oculto acima de 560 px) |
| 3 | Exibir duplicado e com teclas | Folha "Mais" agrupada (Ler, Ferramentas, Preferências) reaproveitando `openPanel` | Baixo | Nenhum (desktop mantém Exibir) |
| 4 | Fonte e tema espalhados | Painel "Aa": tamanho com valor visível, tema Claro/Escuro/Sistema, Marcas, Strong | Baixo a médio | Baixo; pode ser adotado no desktop depois |
| 5 | Faixa "Continuar" com 187 px | No celular, uma linha de 44 px com a última leitura; estudo vai para a folha Estudo | Baixo | Nenhum |
| 6 | Folha cobre o versículo | Ao abrir, rolar o versículo para cima da folha; folha a 60% com alça; × 48 px | Médio | Baixo |
| 7 | Abas do versículo escondidas | Notas como 2ª aba; sombra indicando rolagem, ou duas linhas | Baixo | Baixo (se só no celular) |
| 8 | Seletor de livro nativo e estreito | Folha com grade de livros (AT/NT) e depois capítulos | Médio | Baixo (pode ficar só no celular) |
| 9 | Barra não some; barra do Chrome não recolhe | Rolagem no documento até 560 px; cabeçalho `sticky` que some ao descer | Alto | Médio: código que usa `#reader.scrollTop`/rolagem interna precisa de ramo para o celular |
| 10 | "Voltar" do Android troca de passagem | `history.pushState` ao abrir folha/tela cheia; `popstate` fecha | Médio | Médio: mexe no histórico, que o desktop também usa |
| 11 | Teclado cobre nota e Salvar | `interactive-widget=resizes-content` na meta viewport; rolar o campo para a vista no foco | Baixo | Nenhum |
| 12 | Textos de teclado no toque | "Toque" em vez de "Clique"; tirar "· Esc" dos botões Fechar; Fechar com 44 px | Baixo | Nenhum |
| 13 | Barra do desktop em 2 linhas (101 px a 1280) | Agrupar Estudos/Leitura/Diário/Memorizar/Tópicos em "Estudo ▾" e Temas/Dicionários em "Ferramentas ▾" | Médio | É mudança do desktop; fazer depois, separado |

Ordem sugerida: 12 e 5 (rápidas), depois 1 + 2 + 3 + 4 juntas (formam a nova
navegação), depois 6, 7, 11, depois 8, 10 e 9. Cada uma entra antes no backlog
(regra do projeto).

## D. Esboço visual

Ver os desenhos em texto na Alternativa 1. Folha "Mais":

```
┌──────────────────────────────────────┐
│               ───                    │  alça
│  LER                                 │
│  ▢ Versões em paralelo          ○    │  48 px cada linha
│  ▢ Selecionar versículos             │
│  FERRAMENTAS                         │
│  ▢ Pesquisa por tema                 │
│  ▢ Dicionários e livros              │
│  ▢ Conjuntos de referências          │
│  ▢ Mapa de estudo e linha do tempo   │
│  PREFERÊNCIAS                        │
│  ▢ Texto e tema (Aa)                 │
├──────────────────────────────────────┤
│  ‹    🔍     📖      Aa     ⋯     ›  │
└──────────────────────────────────────┘
```

Painel "Aa":

```
│  Tamanho do texto    [ A− ]  20  [ A+ ]  │
│  Tema        ( Claro )( Escuro )( Sistema )│
│  Marcas no texto                   [on]  │
│  Palavras originais (Strong)       [off] │
```

Os ícones são indicativos; com texto e ícone, o rótulo some o problema "Tema" ×
"Temas".

## E. Decisões para o usuário

| # | Pergunta | Recomendação |
|---|---|---|
| 1 | Barra de ações embaixo (Alt. 1), só em cima compacta (Alt. 2) ou botão flutuante (Alt. 3)? | Embaixo (Alt. 1) |
| 2 | Aceita que o cabeçalho suma ao rolar para baixo? A barra inferior também some? | Só o cabeçalho some; a barra inferior fica |
| 3 | Anterior/próximo na barra inferior, em botões flutuantes ou por gesto de deslizar? | Na barra inferior; sem deslizar (conflita com seleção e com o gesto "voltar" da borda) |
| 4 | Busca em tela própria ou folha? | Tela própria |
| 5 | Botão "Estudo" abre um hub (Leitura de hoje, Meus estudos, Diário, Memorizar, Tópicos) ou vai direto a Meus estudos? | Hub, com Leitura de hoje primeiro |
| 6 | Tema com duas opções (alternar) ou três (Claro, Escuro, Sistema)? | Três |
| 7 | Faixa "Continuar" no celular: uma linha ou só no primeiro acesso do dia? | Uma linha, com × |
| 8 | "Voltar" do Android deve fechar folhas antes de trocar de passagem? | Sim |
| 9 | Aplicar a reorganização também no desktop (menus "Estudo ▾" e "Ferramentas ▾")? | Depois, como tarefa separada |
| 10 | Ponto de corte: só largura ≤ 560 px, ou também celular deitado (cerca de 915 px de largura e pouca altura)? | ≤ 560 px agora; avaliar celular deitado depois |
