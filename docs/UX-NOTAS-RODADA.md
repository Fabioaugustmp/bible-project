# Notas de UI/UX: rodada com o agente Opus (2026-11-18)

Origem: agente de análise (Opus), que leu o código e propôs três sugestões gerais
(sem abrir o app). A primeira foi implementada e testada no navegador.

## As três sugestões

1. **O texto mostra o seu estudo** (implementada). Ponto (●) no número do versículo
   com nota; traço (▬) quando o versículo está num estudo. Tocar na marca abre a
   aba "Minhas notas". Botão **Marcas** na barra liga e desliga; a escolha fica no
   navegador. Custo baixo; prepara backlinks (T81), marcações e "continuar de onde
   parou" (T92).
2. **Selecionar um trecho como gesto de estudo** (implementada, D026). Botão
   "Selecionar": o modo marca o início e o fim com dois toques (funciona no
   celular, sem conflito com a rolagem) e mostra uma barra com Copiar com
   referência, Adicionar ao estudo e Anotar. Não usou shift-clique nem arrastar.
3. **Estudo aberto ao lado, como destino visível** (implementada, D025). Botão
   "Abrir ao lado" na tela do estudo fixa o estudo na coluna da direita, com
   passagens, títulos e notas. A coluna só aparece quando aberta. Em tela
   estreita, vira aba (folha inferior não foi feita). Risco: abaixo de 1099 px,
   leitor, painel e estudo não cabem juntos.

Ordem sugerida pelo agente: 1, depois 3, por último 2.

## Testado (sugestão 1)

- API: `/api/user/marks?book=43&chapter=3` devolveu nota no versículo 16 e estudo
  no 17.
- Navegador: ● no 16 e ▬ no 17; botão Marcas desliga (CSS sem marca) e liga de
  novo; tocar no 16 abre "Minhas notas 1".
- Estudo de teste criado e apagado depois.

## Limites conhecidos

- **Modo paralelo não recebe marcas.** O paralelo usa outra estrutura de linhas
  (`.prow`); as marcas só aparecem no texto normal.
- **Marcas de um intervalo:** o estudo guarda o versículo, não o intervalo (o
  esquema tem `to_verse`, ainda não usado pela interface).
- **Barra de ferramentas:** com o botão Marcas, a barra passa a ocupar duas linhas
  em 1202 px. Vale rever o agrupamento dos botões (ergonomia).
- **Atualização:** salvar uma nota redesenha o capítulo; as marcas de estudo só
  mudam ao navegar de novo.
- Não testado no celular.

## Testado (sugestão 3)

- Navegador (janela de 800 px de largura, faixa de duas colunas): criei um estudo de teste com a passagem João 3:16 e um
  título pela API; em "Meus estudos", abri o estudo e cliquei em "Abrir ao lado".
  A coluna apareceu com o estudo; a aba mostrou "Estudo · Teste ao lado".
- Pela coluna: adicionei uma nota (apareceu na coluna), renomeei o estudo (a aba
  mudou) e apaguei (a coluna fechou; o estudo foi para a lixeira).
- Recarregar a página: a coluna voltou com o estudo, e a barra de abas não mostra
  mais o texto "null" (corrigido nesta rodada: `replaceChildren` recebia `null`).
- Testes unitários: 61 passaram.

## Limites da sugestão 3

- Não testado em tela estreita (menos de 760 px), onde o estudo vira aba.
- Ao salvar uma escrita, a coluna é redesenhada: um campo de nota que estava em
  edição perde o foco.
- Uma requisição GET a `/api/user/study` sem `id` derruba a resposta (ERR_EMPTY_RESPONSE,
  porque `int(q["id"])` levanta KeyError). Não afeta a interface, mas deveria
  responder 400. **Corrigido depois:** agora responde 400 (teste em
  `tests/test_user_study.py`).

## Testado (sugestão 2)

- Navegador (800 px, João 1): dois toques marcaram 3 a 5 (barra "João 1:3–5 · 3
  versículos"); um terceiro toque começou outra seleção; sem painel aberto.
- Adicionar ao estudo: criou o estudo "Estudo: João 1:5" e, com um estudo
  existente, adicionou 3 blocos (3, 4 e 5). Estudo de teste apagado pela API.
- Copiar: a mensagem de confirmação apareceu. O conteúdo do clipboard não foi
  lido (o navegador bloqueou a leitura).
- Anotar: abriu "Minhas notas" do versículo 16 com a seleção desligada.
- Não testado no celular nem em tela estreita.

## Limites da sugestão 2

- Máximo de 40 versículos por "Adicionar ao estudo".
- "Anotar" abre o primeiro versículo: a nota não guarda a faixa.
- A seleção some ao trocar de capítulo.

## Validação responsiva (itens 1 a 3 aplicados)

Validação feita por um agente de revisão (Opus) em 375, 768, 1024 e 1280 px. Os itens 1 a 3 foram aplicados em seguida; o item 4 (painel como folha inferior no celular) fica para depois, por ser um desenho maior.

- **1. Barra de ferramentas:** `.tools` quebra linha (`flex-wrap`); no celular ocupa a largura toda. Medido em 375 px: a página não tem rolagem horizontal (375 = 375) e a barra ocupa duas linhas. No desktop de 1280 px continua numa linha.
- **2. Botões ligados:** Marcas, Selecionar e Paralelo com `aria-pressed="true"` ficam com o fundo de destaque (medido: `rgb(138, 75, 31)` em Marcas).
- **3. Alvos de toque:** em telas de toque (`pointer: coarse`), botões, seletores e campos têm 44 px de altura mínima; chips 40 px; × da faixa "Continuar" 44×44. Medido em 375 px: os botões da barra com 44 px. Em desktop com mouse, a altura continua 36 px.

Não verificado: a captura de tela do celular saiu cortada, embora as medidas mostrem que o conteúdo cabe; toque real; tablet e celular em tema escuro.

## Item 4: painel como folha no celular

- Até 560 px, o painel de estudo e a coluna fixada viram uma folha inferior, com 70% da altura e bordas arredondadas em cima. A leitura continua visível atrás dela.
- Durante a seleção de versículos (`body.selecting`), a folha some, e a barra de ações fica fixa no pé da tela. Assim o texto e a barra ficam visíveis. Ao sair da seleção, a folha volta.
- Medido em 375 px: a folha ocupa 375 × 568 px, fixa no pé. Na seleção, a folha fica `display: none` e a barra fica fixa no pé, com 155 px de altura (ocupa cerca de um quinto da tela).
- Em 1280 px, o painel continua estático e a barra continua pegajosa (sticky), sem mudança.

Limites: a folha não tem alça para recolher; fecha pelo ×. A barra de ações tem 155 px porque os botões de 44 px quebram em duas linhas; pode ser reduzida depois. Não testei gestos de arrastar nem toque real.

## Itens 5 e 6: busca no celular e largura no desktop

- **5. Busca no celular:** "Opções de busca" (Strong, escopo, modo, alcance e recentes) virou um bloco recolhível. Em até 560 px começa fechado; acima disso, aberto. A linha de ações (Copiar, Adicionar ao estudo, Salvar) fica numa linha de rolagem horizontal. Medido em 375 px: o primeiro resultado começa em y=807, com a folha terminando em 812, ou seja, no limite. Para ele aparecer inteiro sem rolar ainda faltam cerca de 40 px (a faixa de filtros e o aviso de ponte ocupam o resto).
- **6. Desktop entre 1100 e 1399 px:** painel e coluna fixada encolhem com `flex-shrink`, e a leitura tem largura mínima de 34rem. Medido em 1280 px com as duas colunas abertas (larguras salvas no navegador de teste): leitura 544 px, texto 481 px (antes: 448 e 385), sem rolagem horizontal.

Não verificado: o recolhimento das opções com toque real; a leitura em 1100 px exato; outras larguras entre 1100 e 1399.

## Ajuste da busca no celular (fecha o item 5)

- Os filtros de tipo (Tudo, Versículos, Comentários, Dicionários e livros) foram para dentro de "Opções de busca", como a primeira linha do bloco. No desktop o bloco começa aberto, então a aparência continua a mesma.
- Medido em 375 px, com a busca "amor de Deus": o primeiro resultado começa em y=717 e a folha termina em 812. Ele aparece inteiro, com a parte de baixo no limite. Antes, começava em y=807.
- Não verificado: toque real; a faixa de ponte (155 px) continua entre as opções e os resultados.
