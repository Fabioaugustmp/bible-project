# Relatório da primeira versão: avaliação simulada de estudo do evangelho

Data: 2026-11-19. Aplicação: Biblioteca Bíblica em http://localhost:8379 (base `data/library.db`, dados de estudo em `data/user.db`).
Quem avaliou: agente de produto, com o navegador embutido (captura de tela, leitura de página) e chamadas à API local. Nenhum arquivo do projeto foi alterado, exceto este relatório. Nenhum commit ou push.

Como ler: cada item diz se foi VISTO no navegador ou só VERIFICADO por resposta de API. O que não foi testado aparece como "não testado".

---

## Parte 1. Log do estudo

### 1.1 Leituras por API (localhost, 127.0.0.1)

Os tempos foram medidos com cliente Python. Na primeira rodada, o cliente usando `localhost` levou cerca de 2 s por chamada (fallback IPv6 do Windows); repetido com `127.0.0.1`, as respostas ficaram nos tempos abaixo. Com curl em `localhost`, `/api/passage` respondeu em 0,21 s.

| Recurso | Passo | Resultado | Funcionou | Tempo |
|---|---|---|---|---|
| /api/passage (ARA) | Gn 3:15, Gn 22:2, Êx 12:5, Lv 16:30, Is 53:5, Dn 7:13, Mq 5:2, Sl 22:1, Sl 110:1, Jr 31:33, Mt 1:21, Jo 1:1, Jo 3:16, Jo 14:6, Rm 3:23, Rm 5:8, 1Co 15:3, Ef 2:8, Hb 9:12, Ap 5:9 | Todos os 20 textos corretos | Sim | 53 ms |
| /api/chapter (ARA) | Jo 3 | 36 versículos com títulos | Sim | 232 ms (curl) |
| /api/xref-graph | Jo 3:16 | 3.811 bytes de nós e arestas | Sim | 406 ms |
| /api/similar | Jo 3:16 | 2.297 bytes | Sim | 53 ms |
| /api/semantic | "Filho de Deus que salva pela fé" | Resultados com pontuação e termos em comum | Sim | 266 ms |
| /api/search | "cordeiro" (ARA, todas as palavras) | Versículos com trecho em destaque | Sim | 398 ms |
| /api/search | "sangue" (qualquer palavra) | Resultados | Sim | 163 ms |
| /api/search | "redenção" | Resultados | Sim | 70 ms |
| /api/search | NEAR(sangue, cordeiro, 5) | Hb 9 e Ap 22 no topo | Sim | 64 ms |
| /api/search | frase "mundo vida" | Só comentários (sem versículo com a frase exata) | Sim, comportamento esperado | 164 ms |
| /api/search | bilingue, "vida" | Resultados | Sim | 293 ms |
| /api/word | G266 (hamartia) | Tradução e léxicos | Sim | 219 ms |
| /api/word | G2222 (zoé) | "vida" 127 versículos | Sim | 234 ms |
| /api/word | G721 (arnion) | "cordeiro" 29 vezes | Sim | 265 ms |
| /api/word | G5485 (charis) | "graça" | Sim | 264 ms |
| /api/commentary | Jo 3:16 (Gill), Rm 3:23 (JFB) | Textos de comentário | Sim | 14–25 ms |
| /api/topic | "redencao" (sem acento) | Resultados literais | Sim | 195 ms |
| /api/titles | module=3 (versão bíblica) | Erro: "módulo não é dicionário nem livro" | Erro esperado, mensagem clara | 2 ms |
| /api/user/* (leituras) | all, studies, topics, sets, journal, memo, reading, map, timeline, backlinks | Respostas corretas | Sim | 3–35 ms |

### 1.2 Escritas por API (dados de teste, todos apagados depois)

| Recurso | Ids criados | Resultado |
|---|---|---|
| nota de versículo (note/create) | 18 notas, ids 5 a 22 (uma por ponto do roteiro, exceto Sl 22:1 e Sl 110:1) | HTTP 200 em todas |
| tópico (topic/create) | 2 tópicos: "Evangelho" id 3, "Alianca" id 4 | HTTP 200 |
| nota de tópico (topic/note/add) | 11 notas, ids 7 a 17 | HTTP 200 |
| estudo (study/create) | estudo id 10 | HTTP 200 |
| blocos de estudo (block/add, kind passagem) | 10 blocos, ids 66 a 75 | HTTP 200, mas o corpo foi descartado (ver 2.3) |
| bloco de teste kind "nota" | id 76 | HTTP 200, corpo gravado |
| bloco de teste kind "texto" | não criado | HTTP 400 "tipo de bloco desconhecido" |
| conjunto (set/create) | conjunto id 2 | HTTP 200 |
| itens do conjunto (set/add, em ordem) | 10 itens, ids 2 a 11 | HTTP 200 |
| cartão de memorização (memo/add) | Jo 3:16, id 2 | HTTP 200 |
| revisão (memo/review, grade "bom") | id 2 | Próxima revisão 20/11, intervalo 1 dia |
| entrada de diário (journal/create) | id 2 | HTTP 200 |
| plano de leitura (plan/create Jo 1-3) | plano id 3, 3 dias | HTTP 200, "days": 3 |
| marcar dia lido (plan/mark) | dia id 4 marcado como lido, depois desmarcado e marcado de novo | HTTP 200 |
| marcar com id do plano (plan/mark id 3) | nenhum efeito | HTTP 200 "ok" sem mudar nada (ver 2.3) |

### 1.3 Navegador (visto na tela)

| Passo | Resultado | Funcionou |
|---|---|---|
| Abrir a aplicação | Abriu em KJV, João 1, com a barra de ferramentas e o banner "Continuar de onde parou" (última leitura: João 3) | Sim |
| Ir para Jo 3:16 pela busca de referência | URL mudou para `#/28/43/3/16` na hora; o texto só trocou para João 3 cerca de 2 s depois | Sim, com atraso |
| Clicar em Jo 3:16 | Painel lateral abriu com as abas: Versões 15, Minhas notas 2, Parecidas 10, Referências 705, Comentários 19, Citado em 455 | Sim |
| Aba Versões | Lista de versões; atalho "Mostrar todas as versões em português (11)" | Sim (não testei o atalho) |
| Aba Minhas notas | Campo de nova nota, "Salvar nota", "Adicionar ao estudo mais recente", lista com Editar, Apagar, Exportar em Markdown, Exportar em Word. A nota antiga do dono aparece com o prefixo "x'" | Sim, com ressalva |
| Aba Parecidas | "Passagens parecidas (10)", com similaridade (Jo 4:9 = 0,81; Jo 3:17 = 0,78) e a versão ARA1993+ | Sim |
| Aba Referências, lista | "Referências cruzadas (705)", agrupadas por livro (Jo 105, Rm 46, 1Jo 34 etc.), com "+ conjunto" | Sim |
| Aba Referências, Grafo | Grafo com Jo 3:16 no centro, nós do AT em laranja e do NT em azul, legenda e "Abrir Jo 3:16 no leitor" | Sim |
| Aba Comentários | 19 comentários, com filtros Tudo, Português, Outros idiomas; etiqueta EN nos ingleses | Sim (filtros não clicados) |
| Aba Citado em | "455 em 33 obras", agrupado por obra com contagens | Sim |
| Busca "cordeiro" com versão KJV | Só comentários e dicionários (1.602 em "Tudo"). Nenhum versículo, sem explicação | Sim, mas confuso |
| Trocar versão para ARA e refazer a busca | Versículos: 102 em "Bíblia · ARA"; "Tudo" 7.334 | Sim |
| Filtro Livro = Romanos | "Tudo" caiu para 1.602; "Dicionários e livros" continuou 1.511 (filtro de livro não se aplica a eles) | Sim, rótulo confuso |
| Por sentido, "cordeiro" | 19 versículos por similaridade (Lv 3:7 = 0,54; Êx 29:39 = 0,51; Êx 12:5 = 0,50) | Sim |
| Campo Strong na busca | Apareceu preenchido com "G5485" (graça) sem que eu tivesse escolhido | Não entendi a origem (ver 2.2) |
| Clicar em "vida" (ARA1993+) para abrir o Strong | Painel G2222 ζωή: grego, "vida" 127, inglês life 259, léxicos Dodson, MLSJ, LSJ | Sim |
| Paralelo | Duas colunas: ARA1993+ e outra versão, alinhadas por versículo | Sim |
| Exibir | Menu: Paralelo, Marcas, Selecionar versículos, fonte, tema, buscar referência, Conjuntos de referências, Mapa de estudo e linha do tempo, Atalhos | Sim |
| Mapa de estudo, aba Mapa | 18 passagens mostradas; rótulos sobrepostos e ilegíveis em 800 px | Sim, com ressalva |
| Mapa de estudo, aba Linha do tempo | Diário, memorização, itens do conjunto, em ordem decrescente | Sim |
| Estudos (Meus estudos) | Tela cheia com o estudo "rascunho · 10 blocos". Ao abrir: lista de passagens com ↑ ↓ Remover, sem texto de bloco e sem citação | Sim, com ressalva |
| Leitura de hoje | "Jo 1 – Jo 3, 1 de 3 capítulos lidos", "Próximo: Jo 2", "Lido hoje", "Criar plano" | Sim (checkbox "Lido hoje" cortado na borda direita) |
| Diário de estudo | Nova entrada, "Salvar entrada", busca, entradas com data, Editar e Apagar | Sim |
| Memorizar | "0 para revisar", card João 3:16, próxima revisão 20/11/2026, "Tirar da memorização" | Sim |
| Notas por tópico | "Alianca 3 notas", "Evangelho 8 notas", campo "Criar" | Sim |
| Temas (Pesquisa por tema) | Tela cheia; "redenção" retornou "Com o termo" com trechos em destaque (Cl 1:14, Sl 130:7, Rm 3:24 etc.) | Sim |
| Dicionários e livros | Lista "Escolha uma obra": livros em inglês (Day By Day By Grace, The Pilgrim's Progress...) e dicionários | Sim (não abri um verbete) |
| Largura 375 px | Sem rolagem horizontal (scrollWidth 375). Barra de ferramentas ocupa cerca de metade da tela; seletor cortado ("ARA1993"); folha do versículo cobre a metade de baixo sem alça | Sim |
| Largura 768 px | Barra em 3 linhas; folha do versículo com cerca de 40% da altura; abas cabem | Sim |
| Volta ao desktop | Preset desktop aplicado | Sim |

### 1.4 Exportação e demais pendências

| Item | Resultado | Como verifiquei |
|---|---|---|
| Word, /api/user/export.docx | HTTP 200, tipo `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, ZIP íntegro, texto com as notas ("Minhas notas", "Gênesis 3:15"...) | API e leitura do ZIP (VISTO no navegador: não testei o download, para não baixar arquivo) |
| Markdown, /api/user/export | HTTP 200, `text/markdown`, com títulos "# Minhas notas", "## Gênesis 3:15" e data | API (botão "Exportar em Markdown" existe na aba de notas, mas não o cliquei para evitar download) |
| /api/user/export.md | 404 "endpoint desconhecido" | API. A rota de Markdown é /api/user/export |
| PDF | Não existe (T42) | API (/api/user/export.pdf: 404) |
| T40: notas sem etiquetas | Confirmado. O campo de nota é só texto, sem etiquetas nem marcações | VISTO no navegador |
| T90: estudo sem citação e sem palavra | Confirmado: o bloco mostra só a referência e setas; sem citação, sem palavra e sem campo de texto | VISTO no navegador e API |
| T91 (Topic Notes e Journal do e-Sword) | Anotado, não testado | Não testado |
| T95 (Google Docs) | Anotado, não testado | Não testado |
| Dicionários: verbete | Não abri um verbete | Não testado |

---

## Parte 2. Avaliação

### 2.1 O que funcionou bem

1. A base de texto e as leituras por API são rápidas: a maioria das respostas fica entre 14 e 300 ms (medido com 127.0.0.1). Os 20 textos-chave do roteiro vieram corretos.
2. A aba Referências é forte: grafo com AT e NT em cores, lista por livro e botão "+ conjunto". Os números batem com a API (705 referências).
3. A aba Parecidas e a busca "Por sentido" retornam passagens relevantes com pontuação (ex.: Jo 3:16 com Jo 4:9 e Jo 3:17; "cordeiro" com Lv 3:7, Êx 29:39, Êx 12:5).
4. A busca bilíngue com "Termos em inglês incluídos" (cordeiro -> lamb, sheep) explica por que um termo traz resultados extras. Boa ideia.
5. O painel Strong (G2222) mostra a palavra original, a tradução mais usada e os léxicos.
6. Estudo, conjunto, memorização (SM-2), diário, plano e linha do tempo funcionam pela interface e pela API. Os cálculos de memorização batem (revisão "bom" leva a 1 dia).
7. Exportação Word gera um arquivo válido, e o Markdown existe.
8. Sem rolagem horizontal em 375 px.
9. Os botões têm rótulos de acessibilidade (aria-label) descritivos, e as abas são elementos de aba.

### 2.2 O que faltou ou travou

Erros e respostas que induzem a erro:

1. **Corpo dos blocos de passagem é descartado sem aviso** (estudo id 10). A API aceita `body` em `block/add` com `kind: "passagem"`, responde 200, e grava `body = null`. Testei: `kind: "nota"` guarda o corpo. Um texto digitado pelo usuário pode sumir. (API; a interface não tem campo de texto para o bloco de passagem, então o usuário não percebe.)
2. **plan/mark com o id do plano responde "ok" e não muda nada**. O id correto é o do dia (dia 4). Erro silencioso.
3. **Prefixo "x'" na nota antiga do dono** (id 3, criada em 2026-11-17). Aparece na tela de notas, no Markdown e no Word. Parece resíduo de conversão de texto, não conteúdo. Não alterei porque é o dado do dono. Conferir a origem (importação, criação ou edição).
4. **Campo Strong com G5485 (graça) preenchido na busca "cordeiro"** sem que eu tivesse escolhido. Não sei a causa: pode ser estado residual do painel ou um valor escolhido pela interface. Precisa de investigação.
5. **Busca "cordeiro" na KJV traz zero versículos sem explicação.** O painel mostra só comentários e dicionários, sem dizer "nenhum versículo nesta versão". O usuário acha que a busca falhou.
6. **Contagem do "Tudo" mistura categorias**: com o filtro Livro = Romanos, "Dicionários e livros" continua 1.511, que não obedece ao filtro. O total de "Tudo" fica engano.
7. **Atraso de renderização**: depois de Enter na busca de referência ou de clicar numa aba do painel, a tela só mudou depois de cerca de 2 s (vários casos observados nas capturas). Os endpoints respondem em menos de 0,3 s, então o atraso está no front ou no navegador embutido. Não medi com precisão.
8. **Exclusões não limpam tudo**: após apagar plano, estudo, notas e tópicos, a linha do tempo ainda mostra 2 eventos de leitura de 19/11 (Jo 1) gerados pelas marcações do plano de teste. Não há endpoint para removê-los. Resíduo registrado na Parte 3.
9. **Rótulos de tipo de bloco pouco claros**: "tipo de bloco desconhecido" (400) não lista os tipos aceitos. Testei "texto" (rejeitado) e "nota" (aceito).
10. **Painel do versículo: abas cortadas** com a largura de 800 px do navegador embutido: "Comentários" e "Grafo" ficam fora da vista e só aparecem com rolagem horizontal da barra de abas. Em um desktop mais largo pode caber; não testei em 1280 px.

Faltas de funcionalidade (já listadas nas pendências):

11. Estudo sem citação e sem palavra por bloco (T90).
12. Notas sem etiquetas (T40).
13. Sem PDF (T42).
14. Sem Google Docs (T95).
15. Topic Notes e Journal do e-Sword não importados (T91).
16. Títulos de livros em inglês na lista de dicionários e livros ("Day By Day By Grace", "The Pilgrim's Progress"), e comentários marcados como EN.
17. Verbete de dicionário não foi testado; sem avaliação do conteúdo.

Pouca clareza de ação:

18. **Temas x Tópicos**: os botões "Tópicos" (notas por tópico) e "Temas" (pesquisa por tema) ficam lado a lado na barra, com nomes parecidos e funções diferentes. Confirmado na tela. Sugestão: "Notas por tópico" e "Pesquisar tema" nos rótulos visíveis.
19. **Estudos x Meus estudos**: o botão "Estudos" abre "Meus estudos" em tela cheia. Não é óbvio que um estudo fica dentro de "Meus estudos".
20. **Mapa de estudo e Conjuntos** escondidos dentro do menu Exibir, junto de atalhos e tema. O usuário procura o mapa em Estudos e não encontra.
21. **Versão aberta invisível na busca**: a busca usa a versão aberta (Escopo: Versão aberta), mas o rótulo não diz qual é.

### 2.3 Melhorias de maior valor (em ordem)

1. **Corrigir o descarte silencioso de dados**: (a) bloco de passagem deve guardar o corpo ou recusar o campo com erro claro; (b) plan/mark com id inválido deve dar 404. Justificativa: é o único problema que pode fazer o usuário perder texto escrito.
2. **Investigar o prefixo "x'" nas notas** e o campo Strong preenchido sem motivo na busca. Justificativa: afetam a confiança nos dados e na busca, e aparecem nas exportações.
3. **Mensagem clara quando a versão aberta não tem o termo** (busca em KJV). Justificativa: é a primeira experiência de busca para um leitor que abre a KJV por padrão.
4. **Responsividade no celular**: reduzir a barra de ferramentas (agrupar em um menu, ou recolher ao rolar), dar alça e modo de recolher à folha do versículo, e mostrar o seletor de versão inteiro ("ARA1993+"). Justificativa: a barra ocupa cerca de metade da tela de 812 px.
5. **Rótulos**: unir "Temas" e "Tópicos" com nomes distintos e uma dica; mover "Mapa de estudo" para o menu Estudos. Justificativa: confusão de nome foi a principal dúvida ao navegar.
6. **Texto por bloco de estudo e citação** (T90). Justificativa: é o que faz o estudo ser útil como texto, e não só lista de referências.
7. **Tornar o mapa legível**: rótulos sobrepostos e pequenos em 18 passagens. Justificativa: o mapa não serve se os nomes não se leem.
8. **Atraso de renderização** (cerca de 2 s): medir no front com o painel aberto e corrigir o que for gargalo. Justificativa: cada clique parece travado.
9. **Traduzir os títulos em inglês** da lista de dicionários, ou mostrar o título em português quando houver. Justificativa: é o rótulo mais visível em inglês.
10. **Exclusão completa**: apagar também os eventos de leitura derivados do plano, ou oferecer endpoint para isso. Justificativa: dados de teste ou de desistência ficam na linha do tempo.

### 2.4 O que faz sentido para as próximas versões e o que não faz

Faz sentido:
- Estudo com texto por bloco e citação (T90), e notas com etiquetas (T40), que são o núcleo do estudo aprofundado.
- Busca por sentido e referências cruzadas com grafo: já são diferencial, vale reforçar.
- Exportação em Word e Markdown, já funcionando; PDF pode esperar.

Não faz sentido agora:
- PDF (T42) antes de corrigir a perda de dados e a responsividade: exige biblioteca externa e a decisão ainda está pendente.
- Google Docs (T95): exige aprovação e não resolve o uso pessoal.
- Importar Topic Notes e Journal do e-Sword (T91) sem o arquivo localizado: só anotar.

### 2.5 Responsividade e acessibilidade (o que notei)

Responsividade:
- 375 px: sem rolagem horizontal (ok). Barra ocupa cerca de metade da tela. Seletor de versão cortado. Folha do versículo cobre a metade de baixo, sem alça para recolher; abas com rolagem horizontal.
- 768 px: barra em 3 linhas; folha com cerca de 40% da altura; abas cabem. Aceitável.
- Desktop (pane de 800 px): abas do painel cortam "Comentários" e "Grafo"; checkbox "Lido hoje" cortado; grafo e mapa com rótulos pequenos.
- Tema escuro: o tema estava escuro em todos os testes (não sei se por padrão ou por configuração do navegador embutido). Contraste visível nas capturas, mas não medi. Tema claro não foi testado.

Acessibilidade (observação, não auditoria):
- Os botões têm rótulos descritivos (aria-label), e as abas são elementos de aba: bom.
- No celular, alguns botões (Diário, Memorizar, Tópicos, Temas) aparecem com texto cinza-claro, parecendo desativados. Não verifiquei se estão desativados de fato. Contraste baixo.
- Mapa e grafo dependem de cor e posição; sem texto alternativo nos nós.
- Não testei navegação só pelo teclado nem leitor de tela.

---

## Parte 3. Recomendação, limpeza e limitações

### Recomendação

**Não está pronta para ser colocada no ar.** Para uso pessoal local, no desktop, serve com ressalvas, desde que o dono confira o texto que escreve (ponto 2.2, item 1).

Bloqueios para colocar no ar:
1. **Perda silenciosa de dados**: corpo de bloco de passagem descartado (API responde 200), plan/mark com id errado respondendo "ok".
2. **Dados com defeito**: prefixo "x'" nas notas (inclusive a do dono) e Strong G5485 preenchido sem motivo na busca.
3. **Não avaliei segurança, autenticação, implantação nem uso de outras origens**. Antes de ir ao ar, falta essa avaliação.

O que pode esperar: PDF, Google Docs, importação de Topic Notes e Journal do e-Sword, etiquetas nas notas, e os ajustes visuais de tablet e de mapa.

### Limpeza (ids criados e situação)

Todos os itens criados foram apagados pelos endpoints de exclusão (mandam para a lixeira; não usei exclusão física). Registro:

| Tipo | Ids | Exclusão | Situação |
|---|---|---|---|
| notas | 5 a 22 (18) | note/delete | ok, verificado por listagem: não restaram |
| tópicos | 3 (Evangelho), 4 (Alianca) | topic/delete | ok; topic?id=3 retorna "tópico não encontrado" |
| notas de tópico | 7 a 17 (11) | removidas com os tópicos | verificado: lista de tópicos vazia |
| estudo | 10, com blocos 66 a 76 (11 blocos, incluindo o bloco "nota" de teste) | study/delete | ok; study?id=10 retorna "estudo não encontrado" |
| conjunto | 2, com itens 2 a 11 | set/delete | ok; lista de conjuntos vazia |
| memorização | 2 (João 3:16) | memo/delete | ok; cards vazios |
| diário | 2 | journal/delete | ok; diário vazio |
| plano | 3 (Jo 1-3) | plan/delete | ok; plano não aparece na leitura de hoje |

Resíduos que restaram:
- **Dois eventos de leitura** (19/11/2026, Jo 1) na linha do tempo (/api/user/timeline). Foram gerados pelas marcações do plano de teste. Não há endpoint para removê-los. Para apagar, só direto no banco `data/user.db`, o que não fiz por regra de segurança. O dono pode decidir.
- **Estado de visualização no navegador embutido** (versão ARA1993+, paralelo ligado, Strong ligado): não é o banco, e pode ficar no navegador embutido.
- Dados do dono preservados: a nota id 3 (Jo 3:16, prefixo "x'") e a leitura de 18/11 na linha do tempo não foram tocados.

Registro completo de ids e chamadas: `C:\Users\fabio\AppData\Local\Temp\claude\532efd60ea671f7b\0668ad14-50ad-4627-9d07-6a23c3b69804\scratchpad\criados.jsonl` (e `ids.json`, na mesma pasta).

### Limitações do teste

- Os textos de teste foram digitados sem acentos (ex.: "Alianca", "Sequencia"). Isso foi escolha do teste, não defeito da aplicação.
- Não testei em 1280 px nem em tema claro.
- Não cliquei em nenhum botão de exportação que baixa arquivo (Exportar em Markdown ou em Word, na aba de notas) para não baixar arquivo; o conteúdo foi verificado pela API.
- Não abri verbetes de dicionário, não cliquei nos filtros de Comentários (Português, Outros idiomas) nem no atalho de versões em português.
- Não avaliei a qualidade dos comentários nem a precisão das traduções.
- Os tempos de resposta de API são de uma única rodada; não há média.
- Os tempos da interface (cerca de 2 s) são observações das capturas, não medidas precisas.

---

## Parte 4. Conferência após o relatório (2026-11-19)

Conferi os pontos do relatório no código antes de decidir. Correções e confirmações:

- **Resíduo na linha do tempo (2.2, item 8): corrigido.** A linha do tempo lia leituras de planos apagados. Agora só lê planos ativos (`app/studymap.py`, teste `test_leitura_de_plano_apagado_nao_aparece`). Os dois eventos de 19/11 somem após a correção; nenhum dado foi apagado à mão.
- **Prefixo "x'" (2.2, item 3): não é defeito do app.** O `docs/FORMATOS.md` registra que o e-Sword guarda textos que o próprio usuário digitou começando com `x'` (ex.: `x'No verso...`). A nota do dono veio da importação. Mantida como está.
- **Corpo de bloco de passagem (2.2, item 1): comportamento de desenho, mas silencioso.** Um bloco de passagem aponta para um versículo e não tem texto próprio; `app/userdata.py` ignora `body` nesse tipo sem avisar. A interface não envia texto nesse caso. Proposta: recusar `body` com erro claro (decisão pendente, não alterei).
- **plan/mark com id do plano (2.2, item 2): risco real.** `mark_day` aceita qualquer id de dia sem conferir o plano. Um id errado pode marcar outro dia. Proposta: exigir plano e dia juntos e responder 404 quando não batem (não alterei).
- **Campo Strong com G5485 (2.2, item 4): não reproduzido.** Não encontrei no código nada que preencha o campo sozinho; o valor pode ser estado da sessão do navegador. Precisa de nova observação.
- **Atraso de 2 s (2.2, item 7): hipótese, não diagnóstico.** O servidor escuta só em `127.0.0.1` (`app/server.py`). Se o navegador tenta `localhost` como IPv6 primeiro, pode haver espera. Para testar, abrir a aplicação por `http://127.0.0.1:8377` e medir de novo.

Testes unitários: 99 passam.

### Correções feitas depois da conferência (2026-11-19)

- **plan/mark exige o plano:** `plan/mark` passa a receber `plan_id` e recusa dia de outro plano ou de plano apagado (400, "capítulo do plano não encontrado"). A interface envia o plano em "Marcar como lido". Testado pela API: dia de outro plano recusado; dia certo aceito (200); teste unitário novo.
- **Bloco de passagem recusa texto:** `block/add` com `kind: "passagem"` e `body` preenchido responde 400 com a mensagem "bloco de passagem não tem texto próprio: use um bloco de nota". Testado pela API e por teste unitário.
- Testes unitários: 102 passam.
- Não reproduzido: o campo Strong preenchido. Atraso de 2 s: hipótese ainda aberta.
