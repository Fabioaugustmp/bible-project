# Notas de UI/UX: rodada com o agente Opus (2026-11-18)

Origem: agente de análise (Opus), que leu o código e propôs três sugestões gerais
(sem abrir o app). A primeira foi implementada e testada no navegador.

## As três sugestões

1. **O texto mostra o seu estudo** (implementada). Ponto (●) no número do versículo
   com nota; traço (▬) quando o versículo está num estudo. Tocar na marca abre a
   aba "Minhas notas". Botão **Marcas** na barra liga e desliga; a escolha fica no
   navegador. Custo baixo; prepara backlinks (T81), marcações e "continuar de onde
   parou" (T92).
2. **Selecionar um trecho como gesto de estudo** (não implementada). Seleção de
   versículos (shift-clique ou arrastar) com barra de ações (Anotar, Adicionar ao
   estudo, Copiar com referência). Impacto alto, custo alto. No celular, o toque
   conflita com a rolagem; talvez seja melhor tocar no primeiro e no último
   versículo. Liga-se à citação do D5 e aos cartões (T80).
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
  responder 400. Não corrigido nesta rodada.
