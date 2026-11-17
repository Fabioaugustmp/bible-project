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
