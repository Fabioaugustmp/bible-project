# Registro de decisões

Cada decisão tem número, data, o que foi decidido e por quê. Decisões não são
apagadas; quando uma muda, entra uma nova que cita a anterior.

## D001 — Arquitetura híbrida · 2026-11-16

**Decisão:** interface em tecnologia web sobre uma base SQLite local, com
casca desktop adicionada no fim. Escolhida pelo usuário entre híbrido e
desktop nativo.

**Motivo:** melhor tipografia, portabilidade entre sistemas, e a mesma
interface pode servir celular depois. Desktop nativo é o que prendeu o
e-Sword e o theWord ao Windows.

## D002 — Importar para base própria em vez de ler os módulos ao vivo · 2026-11-16

**Decisão:** um importador converte os módulos para `data/library.db`; o
aplicativo só lê essa base.

**Motivo:** os dois programas usam formatos e marcações diferentes (RTF,
tags próprias, codificações distintas). Converter uma vez permite busca
unificada e mantém os originais intocados.

## D003 — Python para importador e servidor local · 2026-11-16

**Decisão:** importador e servidor em Python, usando só a biblioteca padrão
nesta etapa.

**Motivo:** já instalado (3.14), tem SQLite embutido, e é onde os modelos de
embeddings rodam na Fase 4. Sem dependências externas, a instalação fica
trivial e a casca desktop pode trocar o servidor depois sem mexer na base.

## D004 — Interface em HTML, CSS e JavaScript puros · 2026-11-16

**Decisão:** sem framework nem etapa de build nesta fase.

**Motivo:** o protótipo tem poucas telas; evitar build mantém o ciclo de
mudança curto. Reavaliar quando a interface crescer (Fase 5).

## D005 — Versificação KJV como referência única · 2026-11-16

**Decisão:** todo versículo é identificado por (livro 1–66, capítulo,
versículo) na versificação KJV. A tabela de contagens (`importer/canon.json`)
foi gerada a partir da ACF do e-Sword, não digitada.

**Motivo:** é a versificação que os dois programas usam: e-Sword grava
livro, capítulo e versículo; theWord grava uma linha por versículo nessa
mesma ordem (31.102 linhas; 23.145 no AT e 7.957 no NT, conferido).

**Limite conhecido:** livros apócrifos (módulos católicos) ficam fora por
enquanto e são contados no relatório de importação.

## D006 — Texto limpo, com marcação original preservada à parte · 2026-11-16

**Decisão:** a base guarda o texto limpo para leitura e busca. Para Bíblias
com números Strong, guarda também uma versão marcada (`tagged`), com os
códigos entre chaves logo após a palavra, por exemplo `princípio,{H7225}`.

**Motivo:** leitura e busca precisam de texto sem ruído; o estudo de
palavras (Fase 5) precisa dos códigos na posição certa.

## D007 — Módulos e base fora do git · 2026-11-16

**Decisão:** `modules-sample/` e `data/` não entram no repositório.

**Motivo:** vários módulos são textos protegidos por direito autoral (NVI,
ARA, NTLH) e os arquivos são grandes. A procedência fica registrada na base
por caminho e SHA-256, o que permite conferir qual arquivo gerou o quê.

## D008 — Módulos criptografados não são lidos · 2026-11-16

**Decisão:** módulos protegidos por criptografia (`.ontx`/`.ntx` e `.twm` com
`secure = 1`) são registrados no relatório como ignorados. O importador não
tenta quebrar a proteção.

**Motivo:** a criptografia é a proteção de direito autoral escolhida pelos
editores desses módulos. Os módulos continuam utilizáveis no próprio theWord.

## D009 — Base completa substitui a de amostras · 2026-11-16

**Decisão:** a importação completa é gerada em `data/library-full.db` e, depois
de verificada, passa a ser `data/library.db`, a base que o aplicativo abre.

**Motivo:** gerar em arquivo separado mantém o aplicativo funcionando durante
a importação e permite conferir antes de trocar.

## D010 — Backlog como fonte única de tarefas; marcos no lugar de fases · 2026-11-16

**Decisão:** o que executar fica em `docs/BACKLOG.md`, com critérios de aceite
por tarefa; `docs/PLANO.md` guarda só princípios e marcos (M0–M6), que
substituem a numeração anterior de fases (Fases 0–2 = M0; Fase 3 = M1).
`AGENTS.md` na raiz traz as regras de trabalho. Pedido do usuário, para que
outros modelos possam continuar o projeto.

**Motivo:** um único lugar para saber o que fazer e quando está pronto.

**Em aberto (não decidido):** posicionamento do produto, ordem entre M2 e M3,
uso de dependências externas e de modelo de linguagem. São as perguntas P1–P5
do backlog e cabem ao usuário.

## D011 — Bíblia duplicada: fica a cópia sem títulos, com os títulos copiados · 2026-11-16

**Decisão:** quando a mesma Bíblia existe em dois arquivos do e-Sword (por
exemplo `ara.bblx` e `ara_com_cabecalhos.bblx`), a base mantém a cópia sem
títulos e copia para ela os títulos de seção da outra, por livro, capítulo e
versículo. A outra é removida e registrada como `ignorado` em `import_log`.
Revê o critério escrito na tarefa T02 ("manter a que tem títulos").

**Motivo:** comparação verso a verso mostrou que as cópias "com cabeçalhos"
são piores: ARA, ARC e Viva perdem Apocalipse 22:21, e a católica e a Viva
trazem aspas duplicadas (`""dia""`) em milhares de versículos. Os títulos são
os mesmos 1.923 nas seis versões (1.915 na católica), ou seja, foram
aplicados em lote por quem montou os módulos, não vêm de cada tradução.

## D012 — Modelo de palavras (`tokens`) e termos por Strong · 2026-11-16

**Decisão:** as Bíblias com Strong gravam uma linha por palavra na tabela
`tokens` (expressão do módulo, Strong, lema, morfologia e, nos interlineares,
original, transliteração e glosa). O texto e o texto marcado do versículo
(`verses.text`, `verses.tagged`) passam a ser montados a partir dessas
palavras; `tagged` foi mantido. A tabela `strong_terms`, derivada de `tokens`,
conta como cada idioma traduz cada Strong. Código em `importer/tokens.py`.

Regras adotadas:
- Código acima de H8674 ou G5624 é análise verbal (tempo, voz, modo), não
  verbete: vai para `morph`, nunca para `strong`.
- Expressão com vários códigos lexicais: a primeira linha leva a expressão, as
  demais ficam com `surface` vazio. `surface` vazio também marca palavra
  original sem tradução (o "-" dos interlineares, a partícula hebraica H853).
- No formato `<wt>`, o campo que aparece primeiro (`<E>` ou `<O>`) é a linha
  principal do módulo; o outro vira original ou glosa.
- Termo = expressão em minúsculas, sem pontuação e sem as palavras de apoio do
  começo (artigos, preposições, conjunções, possessivos). O lema grego perde
  os acentos, para unir a grafia do TR com a do BSB.
- Fica de fora o termo que aparece uma única vez e responde por menos de 5%
  das ocorrências do Strong.

**Motivo:** consultar por Strong ("todas as palavras com G25") e montar a
ponte português ↔ inglês exigem as palavras como linhas, não um texto marcado.

**Limites conhecidos:** verbos aparecem flexionados (G25 em português dá
"ama", "amou", "amam", cada um com cerca de 10%); traduções diferentes
dividem a contagem (H2617 em inglês: "loving devotion" na BSB, "mercy" na
KJV). A segmentação da ARA e da KJV usa o texto entre um código e o seguinte,
o que às vezes inclui palavras a mais.

## D013 — Busca bilíngue pela ponte Strong: regras e limites · 2026-11-17

**Decisão:** na busca, cada palavra portuguesa é procurada também pelas
traduções inglesas dos números Strong que a ARA traduz com ela, nos
comentários e dicionários (não na Bíblia, que é buscada na versão aberta).
A interface mostra os termos incluídos e por qual Strong, e permite desligar
a ponte (a escolha fica guardada). Código em `app/bridge.py`.

Regras (calibradas em 19 consultas, ver `docs/AVALIACAO-BUSCA-BILINGUE.md`):
- um Strong só expande a palavra se responder por ao menos 15% dos usos dela
  na ARA, se ela for ao menos 20% das traduções portuguesas desse Strong, e
  se isso ocorrer 2 vezes ou mais;
- entram as traduções inglesas com ao menos 15% e 3 ocorrências, no máximo
  duas palavras, até 3 por Strong e 5 por palavra digitada;
- termo que contém um já incluído é descartado ("sin offering" quando "sin" já entrou);
- palavras de apoio (artigos, preposições, verbos muito comuns) nunca são
  expandidas e, quando outra palavra foi expandida, deixam de ser exigidas,
  porque não aparecem no texto em inglês;
- acentos não importam ("graca" = "graça").

**Motivo:** é a primeira entrega da ponte português ↔ inglês sem IA (EC2),
explicável e baseada só em dados da própria biblioteca.

**Limites:** falso positivo ocasional por tradução idiomática da BSB
("loving devotion"); verbos e conceitos sem Strong não são cobertos.

## D014 — Painel "Palavra" e índices acrescentados à base em uso · 2026-11-17

**Decisão:**
- Nas Bíblias com Strong, um botão "Strong" liga o modo palavras: cada
  expressão traduzida vira um elemento clicável com o código ao lado. Com o
  modo desligado, clicar no versículo continua abrindo o painel do versículo.
- O painel "Palavra" mostra: o termo original com acentos (o lema mais comum
  no interlinear BSB), as traduções portuguesas e inglesas de `strong_terms`
  (clicar busca o termo), os verbetes cujo título é o código (os
  verbetes-ligação do LSJ e do MLSJ são seguidos até o verbete real) e as
  ocorrências.
- As ocorrências vêm do interlinear reverso BSB, a única Bíblia com Strong
  nos dois testamentos; o texto mostrado é o da versão aberta e, ao lado, a
  expressão que a ARA com Strong usou naquele versículo.
- Dois índices novos (`entries_by_origin`, `links_by_item`) entraram no
  esquema do importador e foram **criados também na base em uso**, sem
  reimportar. A base continua reprodutível: a próxima importação já os cria.

**Motivo:** sem o índice de origem, seguir o verbete-ligação lia 120 mil
verbetes do LSJ (0,77 s por palavra grega; com o índice, 0,32 s).

**Limites:** a contagem de ocorrências é por versículo, não por palavra; o
léxico LXXHebGreek aparece com o grego e o hebraico em codificação antiga de
fonte (ilegível) e fica por último; não há léxico Strong hebraico legível além
do AHLB e da concordância KJC.

## D015 — Referências cruzadas ranqueadas · 2026-11-17

**Decisão:** o painel do versículo ordena as referências cruzadas por:
1. número de listas curadas que trazem a referência: módulo de referências
   do theWord, referências do interlinear BSB e o TSK/TSKe (o comentário de
   cada versículo no TSK é a própria lista de referências);
2. a mesmo número de listas, versículos de outro capítulo antes dos do mesmo
   capítulo;
3. co-citação: quantos outros comentários e verbetes citam os dois versículos
   no mesmo trecho.

Sem lista curada, uma referência só entra se for citada junto em 3 itens ou
mais. Itens que citam mais de 150 versículos (verbetes temáticos longos) não
contam para a co-citação, e vizinhos a até 3 versículos no mesmo capítulo são
ignorados. O painel mostra 12 e permite ver até 60; cada uma diz de onde veio.
Código em `app/xrefs.py`.

**Motivo:** o TSK é exaustivo e sem ordem; a co-citação dá a ordem a partir do
que os próprios comentaristas da biblioteca juntam.

**Não feito:** os votos do OpenBible.info, citados na pesquisa, não foram
usados (exigiria baixar dado externo e conferir a licença).

## D016 — Citações clicáveis: posição no texto, sem marcas no texto gravado · 2026-11-17

**Decisão:** as citações bíblicas dentro de comentários e verbetes ficam numa
tabela própria, `refs`, com a posição (início e fim, em caracteres do texto
gravado) e o destino (livro, capítulo, versículo e fim do intervalo). O texto
gravado não recebe nenhuma marca, para não atrapalhar a busca. Código em
`importer/refs.py`; os conversores `rtf_to_marked` e `rvf_to_marked` marcam o
trecho de cada link com caracteres de uso privado do Unicode, que `extract`
retira ao calcular as posições.

Regras:
- **theWord:** só links cujo alvo é versículo (`tw://bible...` e
  `tw://[self]?L.C.V`); o marcador `[vref]` é trocado pelo rótulo em português.
- **e-Sword:** reconhecimento no texto, com tabelas de abreviações inglesas do
  e-Sword e portuguesas (do cânon, mais variantes e as grafias da tradução
  automática do espanhol). As abreviações inglesas com sublinhado são trocadas
  no texto gravado pelo rótulo em português (`Exo_19:3-6` vira `Êx 19:3-6`).
  Citação para versículo que não existe é descartada.
- A lista de citados (`links`) dos itens do e-Sword e dos módulos do theWord
  sem lista legível passa a vir das citações, com intervalos expandidos até 60
  versículos. Isso faz os comentários em português aparecerem em "Citado em" e
  contarem na co-citação das referências cruzadas (D015).
- Na interface, a posição é convertida para UTF-16 (o JavaScript) pelo
  servidor; passar o mouse mostra o trecho na versão aberta, clicar navega.

**Validação:** contra a lista de citados do próprio theWord, 99,1% dos itens
coincidem nos módulos que a têm legível (amostra de 12 módulos: 66.732 itens).
As diferenças restantes vêm de versículos que a lista do theWord inclui sem link
no texto e de links que ela omite.

**Resultado na base completa:** 2.310.407 citações (1.585.852 em comentários,
724.555 em verbetes); nos módulos do e-Sword, 60.718 citações, que somaram
140.921 linhas à lista de citados. Links cujo texto é só pontuação (";") ou
passa de 80 caracteres não viram citação.

**Limites:** continuação de citações em inglês ("Hb_4:12; 5:3") não é
reconhecida; citação só de capítulo ("Gn 12") e abreviação toda em maiúsculas
("MT 28.18") também não; no e-Sword,
uma abreviação portuguesa ambígua no começo de frase ("Os 2.3") pode ser lida
como citação.

## D017 — Importação incremental: controle por arquivo e regra de releitura · 2026-11-17

**Decisão:** `importer/build.py --incremental` reaproveita a base de saída em
vez de recriá-la. A tabela `import_files(origin_path, origin_sha256,
importer_version, status)` tem um registro por arquivo de módulo visto, em
toda importação (completa ou incremental). `status` é `importado`, `ignorado`,
`erro` ou `unido` (cópia unida por `merge_duplicate_bibles`, D011).

Regras:
- Arquivo com registro de mesmo SHA-256 e mesma versão do importador é pulado
  sem ser lido pelo leitor. Qualquer outro arquivo novo ou alterado tem antes
  apagado o que gerou (`forget_path`: verses, tokens, xrefs, headings,
  comments, entries, links e refs dos itens dele, modules e import_log) e é
  relido.
- Arquivo que estava na base e sumiu da pasta é apagado com o mesmo critério.
- Se algo mudou ou sumiu, as cópias unidas são relidas também: a cópia que
  fica pode depender delas para os títulos copiados.
- Sempre refeitos depois das leituras: unir Bíblias, `strong_terms` (apagado e
  recalculado), índice FTS, resíduos, `meta` e o relatório.
- Base com versão do importador diferente, ou sem `import_files` (anterior a
  esta decisão): aviso no terminal e importação completa.
- A versão do importador (0.3.0) não mudou: a saída dos módulos é a mesma; só
  foi acrescentada a tabela de controle.

**Motivo:** cópias unidas, arquivos ignorados e com erro não ficam em `modules`.
Sem o controle, seriam relidos a cada execução.

**Limites:** o SHA-256 de todos os arquivos é calculado a cada execução (leitura
de bytes, sem reimportação). Arquivo com `erro` ou `ignorado` fica pulado até
mudar o arquivo ou a versão do importador. Se uma cópia unida muda e a que fica
não, os títulos copiados da versão antiga podem continuar na cópia que fica.
A base é alterada no lugar; se a execução for interrompida, ela pode ficar
inconsistente (com `journal_mode = off`, D009): nesse caso, refazer a
importação completa. Remoções não encolhem o arquivo (no teste, +0,5 MB).

## D018 — Divisão de tela: itens fixáveis, arranjo guardado no navegador · 2026-11-17

**Decisão (T61):**
- O painel de estudo ganha o botão "Fixar": o que ele mostra (versículo,
  verbete, comentário, palavra, busca) vai para uma coluna à direita, com abas
  (até 6). Cada comentário aberto no painel do versículo tem também "Fixar ao
  lado". O conteúdo fixado é o mesmo elemento da tela (os botões continuam
  funcionando); ao recarregar, é remontado a partir da descrição guardada.
- Divisórias arrastáveis (mouse) e ajustáveis pelas setas do teclado
  (Shift = passo maior). O texto nunca fica com menos de 448 px; colunas, no
  mínimo 320 px. Sem largura guardada, as duas colunas encolhem na mesma
  proporção para caber.
- Abaixo de 1100 px, painel e coluna fixada se revezam no mesmo espaço
  (botões "Fixados (n)" e "← Estudo"); abaixo de 820 px ficam embaixo do texto.
- O arranjo (larguras, itens fixados, aba ativa) fica guardado no navegador
  (localStorage, com proteção quando indisponível), **não no endereço**, como
  EC9 propunha.

**Motivo da mudança em relação a EC9:** o endereço continua sendo só a
passagem (`#/versão/livro/capítulo/versículo`), que é o que vale a pena copiar
e compartilhar; o arranjo da tela é preferência de cada aparelho.

## D019 — Grafo de referências: posicionamento próprio, determinístico · 2026-11-17

**Decisão (P6 respondida pelo usuário: escrever no projeto):** o grafo usa um
posicionamento por força escrito em `app/static/graph.js`, sem biblioteca.
- Determinístico: os vizinhos começam num círculo, na ordem do ranqueamento, e
  300 passos de repulsão e atração os acomodam; o mesmo versículo dá sempre o
  mesmo desenho. Depois, o desenho é esticado para ocupar a área.
- Nó maior = mais ligado aos outros vizinhos; cor = Antigo ou Novo Testamento;
  traço pela força da ligação; ligações ao centro tracejadas e mais claras.
- Rótulos evitam outros rótulos e outros nós (tentam os dois lados e
  deslocamentos verticais).
- Clique ou Enter num vizinho recentra o grafo (com voltar); no centro, abre no
  leitor. Passar o mouse ou focar mostra o texto do versículo (a prévia da T24).
- Na seção de referências cruzadas, a escolha Lista/Grafo fica guardada; abaixo
  de 760 px de largura de janela, só a lista.
- O servidor guarda em memória até 500 grafos calculados.

**Medido:** posicionamento em 2 a 7 ms; API de 0,2 a 0,5 s no primeiro cálculo
(1,2 s no pior caso, com a base fria) e 45 ms para recentrar num grafo já visto;
em Sl 23:1, Is 53:5, Jo 3:16, Gn 1:1 e Rm 8:28, nenhum rótulo sobre outro
rótulo ou nó, e os centros esperados aparecem como os maiores nós.

## D020 — Respostas à proposta de design e às dependências de embeddings · 2026-11-17

**Decisões do usuário:**
1. **Primeiro uso pessoal; se der certo, vira produto.** A área Biblioteca e as
   funções de publicação ficam para depois das fases de estudo pessoal (D1–D6 de
   `docs/PROPOSTA-DESIGN.md`). Revê a P1 do backlog.
2. **Endereço com sigla e fixados por chave estável** (refina a D018).
3. **O servidor grava só em `data/user.db`**, com proteção por `Origin`/`Host` e
   cópia de segurança diária. A base da biblioteca continua somente leitura.
4. **Guardar no estudo até 1.000 caracteres do trecho citado**, em base própria
   (`data/user.db`), fora do git (D007). O usuário quer que isso seja considerado
   no desenho da base de dados do usuário.
5. **Fontes com licença OFL no repositório** (Literata, Gentium Plus e uma
   hebraica), depois de conferir cada licença na página de origem.

**Dependências (revê a D003):** bibliotecas de terceiros são aceitas, mas só no
ambiente `.venv-bench` (pasta do projeto, ignorada pelo git), usado para o
benchmark de embeddings. O aplicativo e o importador continuam só com a
biblioteca padrão até que uma decisão nova diga o contrário.

**Modelos:** o download só acontece depois de o usuário confirmar, para cada
arquivo, origem e tamanho. O MTEB-BR ainda precisa ter o tamanho confirmado.

## D021 — Modelo de embeddings: BGE-M3 · 2026-11-17

**Decisão:** o modelo de embeddings do projeto é o `BAAI/bge-m3` (licença MIT),
rodando na GPU com PyTorch CUDA, no ambiente `.venv-bench`.

**Motivo:** medido com dados da própria biblioteca (`bench/eval_embeddings.py`),
em 300 consultas e 3.000 comentários. No caso central do projeto (versículo em
português que encontra o comentário em inglês), o BGE-M3 teve recall@10 de
0,714 contra 0,615 do Qwen3-Embedding-0,6B, e foi mais rápido para indexar
(32 s contra 81 s para 31 mil versículos). Nas referências cruzadas os dois
empatam (0,447 contra 0,450).

**Limites:** a amostra é pequena; o MTEB em português não foi usado, porque
trata de textos gerais e não de texto bíblico. A escolha pode ser revista se o
conjunto de avaliação crescer.

## D022 — Grafo de referências em tela cheia, em qualquer largura · 2026-11-17

**Decisão:** o grafo de um versículo abre em tela cheia dentro do próprio app
(botão "Grafo em tela cheia" no painel do versículo). Não é modal pequeno nem
nova aba do navegador. Esc ou o botão Fechar voltam à leitura, no mesmo
versículo. Clicar num nó recentra o grafo; clicar no centro abre o versículo.
O alternador Lista/Grafo do painel continua abaixo de 760 px de largura
(só a lista), mas o botão de tela cheia aparece em qualquer largura.

**Motivo:** um grafo com dezenas de nós e rótulos fica apertado num modal, e
uma nova aba perde o contexto da leitura. Em janela estreita o grafo do painel
não cabia, e o usuário não tinha como vê-lo.

**Limites:** a tela cheia usa largura máxima de 1200 px; em telas muito largas
o grafo não cresce além disso.

## D023 — Revisão do descarte do montador de sermões · 2026-11-17

**Decisão:** o descarte do "montador de sermões" feito na PESQUISA-FEATURES
(a premissa "nada no plano indica que o usuário prega") fica revisto. A
função entra no backlog como candidata, depois de T40 (notas), com escopo
limitado a: registrar o que foi ensinado (data, passagem, local, notas) e
ligar esse registro ao versículo no leitor. Não entra geração de texto de
sermão nem resumo produzido por modelo de linguagem; o conteúdo vem sempre
dos textos e comentários da própria base, com procedência.

**Motivo:** a PESQUISA-MERCADO-ESTUDO mostra que, entre os produtos
pesquisados, nenhum liga o sermão ou a aula ao versículo no leitor, e que o
registro do ensino é um uso com demanda real de quem ensina [I]. A premissa
de que o usuário não prega não foi confirmada pelo usuário; a revisão
depende de o registro ser útil ao estudo, e não de um perfil de usuário.

**Limites:** a utilidade do registro para o usuário ainda não foi testada.
Antes de implementar, confirmar com o usuário se o uso é desejado. Isto
não altera P4 (uso de modelo de linguagem), que segue pendente.

## D024 — Acesso pelo celular na rede local, com código · 2026-11-18

**Decisão:** o app pode escutar na rede local com `python app/server.py --lan`.
Conexões que não vêm do próprio computador precisam de um código de acesso,
guardado em `data/acesso-celular.txt` (fora do git). Com o código, o navegador
recebe um cookie `HttpOnly` e não precisa digitá-lo de novo. A escrita nas notas
e estudos aceita, fora do computador, só o endereço da rede local com o código.
Sem a opção `--lan`, o app continua escutando só em 127.0.0.1, como antes.

**Motivo:** o usuário quer usar o projeto no celular. O `user.db` tem notas e
estudos pessoais, então abrir a porta sem código deixaria esses dados
acessíveis a qualquer aparelho do mesmo Wi-Fi.

**Limites:** o código é compartilhado e não expira; não há usuários nem
senhas. Isso fica para o painel autenticado previsto para depois. O acesso
funciona só se a rede for do tipo privada e se o Firewall do Windows permitir a
porta 8377, o que é uma configuração do sistema que deve ser feita pelo usuário.

## D025 — Estudo ao lado do texto, só quando aberto, pela coluna fixada · 2026-11-18

**Decisão:** um estudo pode ser aberto ao lado do texto. O botão "Abrir ao lado",
na tela do estudo, fixa o estudo na coluna da direita (mesmo mecanismo da T61),
e ela só aparece quando o usuário abre. Escritas no estudo ou nos blocos
atualizam a coluna e a tela cheia. Apagar pela coluna a fecha.

**Motivo:** a decisão 3 do desenho D5 (DESENHO-ESTUDOS) recomendava mostrar a
coluna só quando aberta, para o texto não perder largura sem pedido. Reaproveitar
a coluna fixada evita um segundo sistema de painéis.

**Limites:** a coluna guarda o estudo no navegador (como os outros itens
fixados). Ao atualizar, um campo de nota que estava em edição é redesenhado. Em
tela estreita, o estudo vira uma aba, como os outros itens fixados.

## D026 — Seleção de versículos por dois toques, em modo próprio · 2026-11-18

**Decisão:** o botão "Selecionar" liga um modo de seleção no capítulo normal. Em
modo ligado, o primeiro toque marca o início, o segundo marca o fim (a faixa vai
do menor ao maior) e um terceiro toque começa outra seleção. Um toque não abre
mais o painel do versículo. A barra de ações tem Copiar com referência,
Adicionar ao estudo (um bloco de passagem por versículo, no estudo mais recente,
ou num estudo novo) e Anotar (abre Minhas notas do primeiro versículo). Esc ou
"Sair da seleção" desliga o modo. No paralelo, o modo não funciona.

**Motivo:** a sugestão 2 do agente Opus (UX-NOTAS-RODADA) pedia seleção como gesto
de estudo. Um modo separado evita o conflito entre toque e rolagem no celular, e
não muda o comportamento normal (abrir o painel) de quem não liga o modo.

**Limites:** no máximo 40 versículos por vez no estudo. As notas são de um
versículo, então "Anotar" não guarda a faixa. A seleção não sobrevive a troca
de capítulo.

## D027 — Continuar de onde parou: faixa só sem endereço, guardada no navegador · 2026-11-18

**Decisão:** ao abrir o app sem endereço (`#/...`), uma faixa oferece a última
leitura e o último estudo aberto. A faixa some ao clicar em Abrir ou em ×. Esses
dois dados ficam no `localStorage` do navegador, como as outras preferências.
Abrir sem endereço não grava a leitura padrão por cima da última.

**Motivo:** T92 (ideia necessária da pesquisa). Mostrar a faixa com um endereço
já presente atrapalharia quem chegou por um link. Guardar no servidor exigiria
um campo novo em `user.db` para uma preferência de navegador, sem ganho para
um app local de uso pessoal.

**Limites:** a informação não passa de um navegador para outro, nem para o
celular, que tem armazenamento próprio.

## D028 — Leitura diária por capítulo, sem data fixa · 2026-11-18

**Decisão:** o plano de leitura (T82) é uma sequência de capítulos, um por dia,
sem datas. "Hoje" é o próximo capítulo não lido. Marcar como lido grava a data;
apagar é lixeira. As tabelas `reading_plans` e `reading_days` ficam em
`data/user.db`. Desenho em `docs/DESENHO-LEITURA.md`.

**Motivo:** o uso pessoal pede constância mais do que calendário (a pesquisa de
PESQUISA-MERCADO-ESTUDO, item 9, associa a leitura frequente a desfechos, com
ressalvas). Capítulos são a unidade mais simples de marcar e de conferir. Sem
data, um dia perdido não cria atraso artificial.

**Limites:** intervalos de versículos, calendário e planos prontos ficam para
depois. O módulo `app/reading.py` usa só a biblioteca padrão e a lista de livros
de `importer/canon.py`.

## D029 — Diário de estudo separado das notas por versículo · 2026-11-19

**Decisão:** o diário (T89) é uma coleção de entradas com data de criação, sem
passagem, em `data/user.db` (tabela `journal`). Criar, editar e buscar pelo texto;
apagar é lixeira. As notas por versículo e os estudos não mudam.

**Motivo:** o Journal Notes do e-Sword (ESTUDO-PROGRAMAS) é o diário de estudo, separado
das notas presas a um versículo. Uma tabela própria evita mexer no modelo de notas
(ancoradas em `anchors`) e mantém os dados pessoais só em `user.db`.

**Limites:** sem exportação, etiquetas ou ligação com estudos nesta etapa; o diário
de oração e louvor (T99) fica para depois e pode reaproveitar a mesma tabela com uma
etiqueta.

## D030 — Notas por tópico separadas das notas por versículo · 2026-11-19

**Decisão:** o tópico (T87) é um assunto com notas que podem ou não apontar uma
passagem. Tabelas `topics` e `topic_notes` em `data/user.db`; o nome do tópico é
único sem diferença de maiúsculas; apagar é lixeira. O botão "Tópicos" não se confunde
com "Temas", a busca por tema.

**Motivo:** o Topic Notes do e-Sword organiza a anotação por assunto, não por
passagem (ESTUDO-PROGRAMAS). Um tópico pode reunir notas de várias passagens, o que
nenhuma nota por versículo faz.

**Limites:** sem etiquetas em notas por versículo (parte de T40), sem exportação e
sem ligação entre tópico e estudos.

## D031 — Memorização de versículos com SM-2 · 2026-11-19

**Decisão:** o cartão de memorização (T80) é um versículo com facilidade, intervalo e
repetições, calculados pelo SM-2 (SuperMemo 2): acertos seguidos com intervalos de 1,
6 dias e depois intervalo x facilidade; erro volta a 1 dia; facilidade mínima 1,3.
Resposta em quatro graus: não lembrei, difícil, bom, fácil. Tabela `memo_cards` em
`data/user.db`; apagar é lixeira.

**Motivo:** SM-2 é o algoritmo de origem do Anki, que os usuários de cartões conhecem;
agenda melhor que intervalos fixos e cabe em poucas linhas da biblioteca padrão.
FSRS (o padrão mais recente do Anki) fica para depois, com a mesma tabela.

**Limites:** um cartão por versículo; sem cartões a partir de notas ou de passagens com
intervalo; sem botão "Memorizar" no painel do versículo ainda.

## D032 — Conjuntos de referências ordenados pelo usuário · 2026-11-19

**Decisão:** T98 cria conjuntos nomeados de passagens, na ordem que o usuário escolhe.
Cada item vem de uma referência cruzada ("+ conjunto" ao lado da referência) e pode
ser subido, descido ou removido. Tabelas `ref_sets` e `ref_set_items` em `data/user.db`;
apagar conjunto é lixeira. A ordem fixa das referências (curadas, depois co-citação)
não muda. Acesso pelo menu Exibir.

**Motivo:** o theWord e o e-Sword mostram referências em ordem fixa; o estudante quer o
próprio critério. Um conjunto guarda essa escolha sem alterar a lista automática.

**Limites:** sem reordenar a lista automática; sem notas por item; sem exportação.

## D033 — Mapa de estudo e linha do tempo, lidos dos dados guardados · 2026-11-19

**Decisão:** o mapa (T93) liga passagens a tópicos e estudos, com as notas, notas de tópico
e blocos de estudo como ligações; mostra as 40 passagens mais estudadas. A linha do tempo
junta eventos com data (notas, tópicos, diário, estudos, memorização, conjuntos e leituras).
Não há tabela nova: os dois são lidos das tabelas que já guardam as datas, então nunca
ficam diferentes do que está guardado. Acesso pelo menu Exibir.

**Motivo:** o grafo de referências (graph.js) já mostra ligações; o mapa reaproveita o mesmo
posicionamento e mostra o próprio estudo. Guardar uma cópia por dia criaria duas fontes de
verdade.

**Limites:** sem instantâneos históricos (a linha do tempo mostra o estado atual com as datas
de criação); sem filtro por período; sem ligação entre passagens que estão no mesmo estudo.

## D034 — Publicação em biblia.famptech.com.br pelo túnel da Cloudflare, com código de acesso · 2026-11-19

**Decisão:** a aplicação roda em um servidor Linux, em contêineres Docker, e é publicada pelo
túnel da Cloudflare que já existe, no endereço https://biblia.famptech.com.br. O túnel já
existe no servidor (contêiner `cloudflared-default`, rede `general-network`); o serviço `web` entra
nessa rede com o nome `biblioteca-web`, e a rota pública aponta para `http://biblioteca-web:8377`.
Não há um segundo conector no compose. Com `BIBLE_PUBLIC_ORIGIN` definido (ou `--public-origin`), o
servidor exige o código de acesso em **todo** pedido, inclusive os que vêm do túnel; o código vem
de `BIBLE_ACCESS_TOKEN` (no `.env`, fora do git) ou de `data/acesso-celular.txt`. A comparação é
em tempo constante e o cookie recebe `Secure`. O endereço público só aceita origem `https`
para escrita em `/api/user/*`. Frontend e API continuam no mesmo processo (`app/server.py`):
o túnel encaminha `/` e `/api/*` para o mesmo serviço `web`.

**Motivo:** o usuário quer a aplicação no ar em um domínio próprio, com o HTTPS e a rede já
resolvidos pela Cloudflare. O código de acesso reaproveita o mecanismo do D024 e fecha a porta que
antes estava aberta (sem login, qualquer um lia e escrevia em `user.db`). Um processo só evita
um proxy extra para o frontend, e a mesma origem dispensa CORS.

**Limites:** o código é único e compartilhado, sem usuários nem expiração; o acesso pela URL (`?t=`)
passa pelos registros da Cloudflare, por isso o servidor grava `?t=***` no próprio registro.
Recomendado, mas feito no painel da Cloudflare e não no repositório: Cloudflare Access (login por
e-mail) na frente do hostname. A base `library.db` tem texto de módulos com direito autoral
(D007); a publicação do texto integral depende de conferir a licença de cada módulo (T52), e
essa decisão é do usuário. O embed (busca por sentido) não foi construído nesta máquina (ver
DEPLOY.md, "Estado da verificação").

## D035 — Busca por sentido continua em fp32, com teto de 3 GB · 2026-11-19

**Decisão:** o serviço `embed` mantém o BGE-M3 em fp32 (CPU), sem quantização, e recebe
`mem_limit: 3g` no compose. Bf16 e int8 foram medidos e descartados (ver
`docs/EXPERIMENTO-MEMORIA-EMBED.md`).

**Motivo:** em fp32 o pico medido foi de 2,46 GB, com 106 ms por consulta mediana e qualidade
igual à referência. Bf16 usou mais memória (4,27 GB) e foi mais lento; int8 usou mais ainda
(5,21 GB) e perdeu qualidade (top-10 em comum de 81%, mínimo de 40%).

**Limite:** medido no Windows, com 4 threads; o servidor ainda precisa ser medido.
