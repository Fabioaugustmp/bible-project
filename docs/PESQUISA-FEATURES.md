# Pesquisa de funcionalidades

Pesquisa feita em 2026-11-16. Complementa o [PLANO.md](PLANO.md); não altera
nenhuma fase, só propõe acréscimos e refinamentos.

**Como ler este documento.** Cada afirmação sobre produto ou licença traz uma
destas marcas:

- **[V]** verificado por mim na página primária (site do projeto, repositório
  ou cartão do modelo);
- **[S]** visto apenas em resumo de busca ou em fonte secundária — conferir
  antes de depender disso;
- **[I]** inferência ou proposta minha, sem fonte.

Nada foi medido na base real: estimativas de esforço, tamanho e qualidade são
**[I]** e precisam de um teste pequeno antes de virar compromisso.

## Resumo

O desnível português/inglês se resolve melhor em três camadas, da mais barata
para a mais cara, e as duas primeiras não dependem de IA generativa:

1. **Strong como ponte entre idiomas (sem IA).** A ARA com Strong, o TR com
   Strong e o interlinear já ligam cada palavra portuguesa a um número e esse
   número a palavras inglesas. Isso permite expandir uma busca em português
   para os comentários e dicionários em inglês e montar um glossário bilíngue
   próprio.
2. **Tradução automática local, sob demanda e com cache**, de comentários e
   verbetes, com o original sempre ao lado. É o que o Logos oferece como
   "Auto Translate"; aqui roda offline com um modelo aberto (OPUS-MT, CC BY 4.0).
3. **Referências cruzadas ranqueadas e página de tópico/entidade em português**,
   juntando o que o usuário já tem (TSK, Nave's, Torrey, Thompson, ISBE, Easton)
   com dados abertos (OpenBible, STEPBible, ACAI, Theographic).
4. **Léxico breve em português**, gerado uma única vez a partir dos léxicos
   curtos do STEPBible (CC BY 4.0), para que o clique no Strong já responda em
   português antes de abrir o LSJ ou o Strong em inglês.

Perguntas em linguagem natural com resposta citada (o "Study Assistant" do
Logos) são viáveis, mas ficam como opcional tardio: exigem LLM e são a única
proposta que ameaça o princípio "tudo local e offline".

## Funcionalidades propostas

Ordenadas por valor/esforço (melhor relação primeiro). "Já tem" = módulos da
biblioteca do usuário.

| # | Funcionalidade | O que o usuário ganha | De que dados depende | Esforço | IA |
|---|---|---|---|---|---|
| 1 | Referência bíblica em português dentro do texto inglês | Passar o mouse em "Rom 8:28" num comentário mostra o versículo na versão portuguesa preferida; clicar navega | Já tem (tabela `links`, padrões `Mat_22:30` e `tw://bible`) | Baixo | Não |
| 2 | Busca bilíngue por ponte Strong | Buscar "graça" encontra também "grace" e "charis" nos comentários e dicionários em inglês | Já tem (ARA+Strong, TR+Strong, interlinear, KJV) | Médio | Não |
| 3 | Referências cruzadas ranqueadas | Lista curta e ordenada das passagens mais relacionadas, já com o texto em português | Já tem (TSK, co-citações na tabela `links`) + OpenBible cross-references (CC BY) | Baixo | Não |
| 4 | Tradução local de comentários e verbetes, sob demanda | Ler Gill, Henry, ISBE em português, com o original ao lado | Já tem (comentários, dicionários) + modelo OPUS-MT en→pt (CC BY 4.0) | Médio | Modelo de tradução local (LLM opcional) |
| 5 | Léxico breve em português | Clique no Strong mostra glosa curta em português, depois os léxicos completos | STEPBible TBESG/TBESH (CC BY 4.0) + tradução única em lote; Strong e LSJ já tem | Médio | Modelo de tradução local, uma vez |
| 6 | Planos de leitura com progresso e "continuar de onde parei" | Uso diário; aproveita os planos já instalados | Já tem (`.rdp`, devocionais) | Baixo | Não |
| 7 | Mapa de cobertura no leitor | Marca discreta em cada versículo indicando quanto material existe sobre ele; painel agrupado e ordenado | Já tem (contagens de `comments` e `links`) | Baixo | Não |
| 8 | Página de tópico/entidade em português | Um lugar só para "Arca da Aliança", "Barnabé", "Cafarnaum": verbetes de todos os dicionários, versículos, mapa | Já tem (Nave's, Torrey, Thompson, ISBE, Easton, Smith) + ACAI (CC BY-SA 4.0, com rótulos em português) + TIPNR (CC BY 4.0) | Médio/alto | Não (embeddings ajudam a casar tópicos) |
| 9 | Aviso de variante textual no comparador | Explica por que ACF/ARC têm um trecho que NVI/NTLH omitem ou mudam | Já tem (TR, ACF, NVI etc.) + STEPBible TAGNT (CC BY 4.0) | Médio | Não |
| 10 | Versificação correta entre tradições | Salmos com título, 3 João, versão católica e deuterocanônicos alinhados | STEPBible TVTMS (CC BY 4.0) | Médio | Não |
| 11 | Avaliação automática da busca semântica | Escolher o modelo de embeddings com números, não por impressão | Já tem (TSK e OpenBible como pares "certos"; versículo ↔ comentário do mesmo versículo) | Baixo | Embeddings locais |
| 12 | Mapa dos lugares do capítulo | Ver onde ficam os lugares citados no capítulo aberto | OpenBible Bible-Geocoding-Data (CC BY 4.0) + atlas que já tem | Médio | Não |
| 13 | Interlinear do AT e morfologia por extenso | Hebraico com Strong, glosa e análise explicada; grego com códigos expandidos | STEPBible TAHOT, TEHMC, TEGMC (CC BY 4.0); WLC e TR já tem | Médio | Não |
| 14 | Leitura em voz alta | Ouvir o capítulo em português | Voz do sistema via navegador | Baixo | Não |
| 15 | Cadernos de estudo e etiquetas nas notas | Notas agrupadas por tema, com versículos arrastados para dentro; exportação em Markdown | Dados do usuário (base separada, já prevista) | Médio | Não |
| 16 | Áreas de trabalho e painéis lado a lado sincronizados | Guardar arranjos ("devocional", "grego", "preparar aula") | Nenhum | Médio | Não |
| 17 | Resumo "o que dizem os comentaristas" | Três ou quatro linhas em português por versículo, com fonte por frase | Já tem (comentários) | Médio | LLM |
| 18 | Passagens paralelas e AT citado no NT | Sinopse dos evangelhos, Reis/Crônicas, citações lado a lado | Tabela de paralelos: fonte aberta **não confirmada**; aproximação por referências cruzadas + embeddings | Médio/alto | Embeddings locais |
| 19 | Pergunte à biblioteca (resposta citada) | Pergunta em português, resposta em português com citações clicáveis dos próprios módulos | Já tem + índice da Fase 4 | Alto | LLM |
| 20 | Busca por morfologia | "Todos os imperativos aoristos em Romanos" | Já tem (TR com morfologia) | Médio | Não |
| 21 | Linha do tempo e pessoas | Eventos e genealogias ligados aos versículos | Theographic (CC BY-SA 4.0), rótulos em inglês | Alto | Não |

## As melhores, em detalhe

### 1. Referência bíblica em português dentro do texto inglês

Todo comentário e verbete importado já tem as citações extraídas para a tabela
`links`, e o [FORMATOS.md](FORMATOS.md) documenta como elas aparecem no texto
(`Mat_22:30` no e-Sword, `tw://bible.*?id=9.7.1` no theWord). A proposta é
manter essas citações como elementos clicáveis no texto exibido: ao passar o
mouse, aparece o versículo na versão portuguesa preferida; ao clicar, o leitor
navega. É a mesma dica flutuante que e-Sword e theWord têm, com a diferença de
sempre responder em português mesmo quando o comentário cita a KJV **[I]**.
Limite: o texto limpo guardado hoje pode ter perdido a posição exata da
citação; talvez seja preciso guardar o trecho com marcadores, como já se faz
com o Strong (D006). É a melhoria mais barata contra o desnível de idioma,
porque boa parte de um comentário antigo é citação bíblica.

### 2. Busca bilíngue por ponte Strong

Cada número Strong aparece ligado a palavras portuguesas (ARA com Strong) e a
palavras gregas (TR com Strong); o interlinear e, se tiver Strong, a KJV dão
as palavras inglesas. Contando essas correspondências monta-se uma tabela
`termo_pt → Strong → termo_en` com frequências. Na busca, "graça" vira
`graça OR grace OR G5485 OR χάρις`, e o FTS5 que já existe encontra o material
em inglês. Sem modelo, sem GPU, explicável ("incluí *grace* porque a ARA
traduz G5485 por *graça* 120 vezes"). A mesma tabela serve de glossário para
conferir a tradução automática (item 4). Inspiração: é o que o STEPBible faz
ao buscar "por significado" a partir do termo original e mostrar palavras
relacionadas **[S]**; a aplicação entre português e inglês é **[I]**. Limites:
só cobre vocabulário bíblico (não ajuda com "justificação forense" ou
"pré-milenismo"); palavras muito polissêmicas trazem ruído, então convém
limitar às duas ou três traduções mais frequentes. A busca semântica da Fase 4
cobre o que esta não cobre; as duas se somam.

### 3. Referências cruzadas ranqueadas

O usuário já tem o Treasury of Scripture Knowledge, que é exaustivo mas não
ordenado. O OpenBible.info publica cerca de 340 mil referências cruzadas com
votos, sob CC BY **[V]**; uma fonte secundária diz que derivam principalmente
do próprio TSK **[S]**, de modo que o ganho real é a ordenação. Há ainda um
terceiro sinal que só este projeto tem: a co-citação. Se vinte comentários e
verbetes diferentes citam Rm 3:25 e Lv 16:15 no mesmo parágrafo, a ligação é
forte — e isso sai de uma consulta na tabela `links` **[I]**. O painel
mostraria as dez melhores, com o texto em português, e a origem de cada uma
("TSK", "OpenBible, 45 votos", "citados juntos em 12 lugares"). Inspiração:
Blue Letter Bible e Bible Hub exibem TSK e referências cruzadas por versículo
**[S]**. Risco: os votos do OpenBible refletem um público de língua inglesa e
evangélico; por isso a origem fica visível e os três sinais ficam separáveis.

### 4. Tradução local de comentários e verbetes, sob demanda

Um botão "traduzir" em cada comentário ou verbete; o resultado fica em cache
numa base derivada, chaveado pelo id do item e pela versão do modelo, e o
original fica sempre visível ao lado ou a um clique. O Logos tem isso como
"Auto Translate" para livros da biblioteca, em mais de cem idiomas **[S]**
(página de suporte não abriu para mim; vi só o resumo). Modelo sugerido para
começar: `Helsinki-NLP/opus-mt-tc-big-en-pt`, licença CC BY 4.0, cerca de 0,2
bilhão de parâmetros, com o marcador `>>pob<<` para português do Brasil
**[V]**. Riscos e limites, todos **[I]**: (a) Gill, Henry e Poole escrevem em
inglês dos séculos XVII–XVIII, com períodos longos — a qualidade tende a cair
e precisa ser testada numa amostra antes de decidir; (b) citações bíblicas
dentro do comentário não devem ser traduzidas pela máquina: o ideal é
preservar a referência (item 1) e deixar o versículo vir da versão portuguesa;
(c) termos teológicos precisam de consistência, e o glossário do item 2 pode
sinalizar divergências; (d) o texto traduzido deve ser sempre rotulado como
tradução automática e nunca entrar no índice como se fosse o original;
(e) dependências como PyTorch ou CTranslate2 quebram a decisão D003 ("só
biblioteca padrão") e podem não ter pacote pronto para Python 3.14 — não
verifiquei. Traduzir a biblioteca inteira de antemão não compensa (ver "O que
não vale a pena"). Um LLM local ou remoto daria tradução melhor para prosa
antiga, como opção, não como base.

### 5. Léxico breve em português

O STEPBible publica, sob CC BY 4.0, dois léxicos curtos ligados ao Strong:
TBESG (grego, Abbott-Smith corrigido) e TBESH (hebraico, BDB resumido), além
do LSJ formatado (TFLSJ) **[V]**. Por serem entradas curtas e em número
limitado, dá para traduzi-las uma única vez em lote e guardar como módulo
derivado "Léxico breve (tradução automática)". Assim o clique num Strong da
Fase 5 abre primeiro uma glosa em português, mais as traduções reais que a ARA
usa para aquele número (que são dado humano, não máquina), e só depois o
Strong e o LSJ em inglês. Não encontrei léxico Strong em português com licença
aberta; o da Sociedade Bíblica do Brasil é produto comercial **[S]**. Risco:
glosas muito curtas ("to be, become") são justamente onde a tradução
automática erra por falta de contexto; por isso a lista de traduções da ARA
deve vir em destaque e a glosa traduzida como apoio, com rótulo.

### 8. Página de tópico/entidade em português

Inspiração direta: o Factbook do Logos, que reúne numa página tudo sobre uma
pessoa, lugar ou tema e, desde novembro de 2025, sugere perguntas com resposta
citada **[V]**. Aqui a página juntaria os verbetes de Nave's, Torrey,
Thompson, ISBE, Easton e Smith sobre o mesmo assunto, os versículos mais
citados por eles e, para lugares, o mapa. O problema é que os títulos estão em
inglês ("Ark of the Covenant") e o usuário procura "Arca da Aliança". Duas
fontes ajudam: o ACAI (pessoas, lugares, grupos, fauna, flora, objetos e
termos-chave anotados no texto original, com rótulos localizados que incluem
português, CC BY-SA 4.0) **[V]** e o TIPNR do STEPBible (nomes próprios
separados por indivíduo, com todas as referências, CC BY 4.0) **[V]**. Para
nomes próprios há também um caminho sem dado externo: o nome português sai da
ARA pelo Strong do nome. Casar verbetes de dicionários diferentes entre si
exige normalização de títulos e, nos casos duvidosos, os embeddings da Fase 4
**[I]**. Limites: não conferi a cobertura real dos rótulos em português do
ACAI; temas abstratos ("Justification") não estão em listas de entidades e
dependerão do glossário do item 2 ou de tradução do título.

### 9. Aviso de variante textual no comparador

Quem lê ACF ao lado de NVI tropeça em trechos que uma tem e a outra não
(At 8:37, 1 Jo 5:7, o final do Pai-Nosso). Isso não é diferença de tradução, é
de texto-base. O TAGNT do STEPBible traz o texto grego com marcação de quais
palavras estão em quais edições (NA27/28, TR e outras) **[V]**. O comparador
da Fase 5 poderia, ao detectar grande diferença entre o grupo ACF/ARC e o
grupo NVI/NTLH, verificar se há variante marcada no TAGNT e mostrar uma nota
neutra: "diferença de texto-base: presente no Textus Receptus, ausente em
NA28". Não conheço programa gratuito que faça isso para versões portuguesas
**[I]**. Limites: só NT; a ligação palavra a palavra entre português e grego
existe só para a ARA com Strong, então para as demais versões o aviso é por
versículo, não por palavra; o tom precisa ser descritivo, sem tomar partido.

### 10. Versificação correta entre tradições

A decisão D005 adota a versificação KJV e deixa os apócrifos de fora. O TVTMS
do STEPBible documenta as diferenças entre tradições (hebraica, latina, grega)
e as regras para converter **[V]**, sob CC BY 4.0. Usá-lo resolve três
problemas de uma vez: a Bíblia católica do usuário, os Salmos com título
numerado como versículo 1 e os deslocamentos pontuais que fazem um comentário
apontar para o versículo vizinho. É trabalho de encanamento, sem brilho, mas
cada erro de alinhamento contamina busca, painel, referências cruzadas e
embeddings. Limite: exige decidir como identificar versículos fora do cânon de
66 livros — nova decisão no DECISOES.md.

### 11. Avaliação automática da busca semântica (refina a Fase 4)

Antes de escolher o modelo de embeddings, montar um teste com dados que já
estão na base: (a) pares de referência cruzada com muitos votos devem aparecer
entre os vizinhos mais próximos; (b) dado um versículo em português, o
comentário em inglês sobre esse mesmo versículo deve ficar bem colocado — este
é exatamente o caso "busca em português sobre comentários em inglês" do plano.
Candidatos: `BAAI/bge-m3` (MIT, 1024 dimensões, até 8192 tokens, mais de 100
idiomas) **[V]** e `intfloat/multilingual-e5-small` (MIT, 384 dimensões, 512
tokens, exige prefixos `query:`/`passage:`) **[S]**. O e5-small é bem menor e
talvez baste para versículos; o bge-m3 aceita parágrafos longos de comentário
sem cortar. Uma fonte acadêmica alerta que modelos multilíngues nem sempre
transferem bem entre idiomas **[S]** — mais um motivo para medir. Projetos
abertos recentes (Biblos, BibleLLM, StudyBible MCP) usam embeddings só em
inglês ou via API externa **[S]**; não achei nenhum que documente busca
cruzada português/inglês, então não há atalho pronto.

### 19. Pergunte à biblioteca (opcional, por último)

O Study Assistant do Logos (Logos 46, novembro de 2025) responde perguntas em
conversa, busca na biblioteca do usuário, sintetiza e dá resposta com
referências clicáveis, com opção de restringir aos livros que o usuário possui
**[V]**. A versão local seria: recuperar trechos pela busca híbrida da Fase 4,
entregá-los a um LLM com a instrução de responder em português e citar cada
afirmação, e mostrar os trechos originais embaixo. Um passo intermediário, sem
LLM, já entrega metade do valor: a pergunta retorna os dez parágrafos mais
relevantes, traduzidos pelo item 4 — "resposta extrativa" **[I]**. Riscos:
modelos locais pequenos alucinam e escrevem mal em português; modelos remotos
quebram o princípio offline e enviariam trechos de módulos protegidos por
direito autoral a terceiros; e em assunto doutrinário uma síntese fluente
esconde que Gill e um verbete do ISBE podem discordar. Se for feito: desligado
por padrão, com o provedor escolhido pelo usuário e sem resposta quando não
houver trecho de apoio.

## Dados abertos úteis

| Nome | O que contém | Licença | Link |
|---|---|---|---|
| OpenBible.info Cross References | Cerca de 340 mil referências cruzadas com votos; zip de ~2 MB | CC BY ("Creative Commons Attribution License", o link aponta para 4.0) **[V]** | https://www.openbible.info/labs/cross-references/ |
| OpenBible Bible-Geocoding-Data | Lugares bíblicos com identificações modernas possíveis e grau de confiança, geometrias, miniaturas 512×512 (zip de ~180 MB), em JSON Lines, GeoJSON e KML | Dados CC BY 4.0; partes derivadas do OpenStreetMap em ODbL 1.0; imagens com licença variável por imagem (campo `credit`) **[V]** | https://github.com/openbibleinfo/Bible-Geocoding-Data |
| STEPBible-Data | TAHOT (hebraico com morfologia e Strong estendido), TAGNT (grego com edições e variantes), TBESH/TBESG (léxicos breves), TFLSJ (LSJ formatado), TIPNR (nomes próprios individualizados), TVTMS (versificação), TEHMC/TEGMC (códigos de morfologia por extenso) | CC BY 4.0, crédito "STEP Bible" com link **[V]**. Exceção: TTESV (marcação da ESV) é CC BY-NC **[S]**. Tudo em inglês | https://github.com/STEPBible/STEPBible-Data |
| Theographic Bible Metadata | 3.067 pessoas, 1.298 lugares, 450 eventos, 23 grupos, Easton ligado às entidades; JSON, CSV, GeoJSON | CC BY-SA 4.0 no repositório **[V]**. A página "About" do projeto fala em CC BY 4.0 **[S]** — vale o arquivo LICENSE do repositório | https://github.com/robertrouse/theographic-bible-metadata |
| ACAI (Bible Aquifer) | Entidades (pessoas, lugares, divindades, grupos, fauna, flora, objetos, termos-chave) anotadas no texto original, com rótulos localizados, inclusive português (`por`); JSON | CC BY-SA 4.0, © Mission Mutual 2025 **[V]** | https://github.com/BibleAquifer/ACAI |
| Bible Aquifer (demais recursos) | Notas de estudo, dicionário bíblico, notas de tradução da unfoldingWord, em vários idiomas | **Não confirmei** licença por recurso nem se há português; cada repositório precisa ser conferido | https://github.com/BibleAquifer |
| MACULA Greek | Árvores sintáticas, morfologia, papéis semânticos e referentes para o NT (Nestle1904 e SBLGNT) | CC BY 4.0 para o conjunto (© Biblica); domínios semânticos da UBS/MARBLE "usados com permissão", fora da licença aberta **[V]** | https://github.com/Clear-Bible/macula-greek |
| MACULA Hebrew | Equivalente para o AT, sobre o WLC | Descrito como CC BY 4.0 **[S]**; não abri o LICENSE | https://github.com/Clear-Bible/macula-hebrew |
| Open Scriptures Hebrew Bible (morphhb) | WLC com lema e morfologia | Lema e morfologia CC BY 4.0; texto WLC em domínio público **[S]** | https://github.com/openscriptures/morphhb |
| Open Scriptures Strong's | Dicionários Strong de hebraico e grego em XML/JS | **Não confirmei**: a página do repositório não mostrou a licença | https://github.com/openscriptures/strongs |
| Bíblia Livre | Bíblia em português do Brasil, revisão da Almeida de 1819, base Textus Receptus | CC BY 4.0 **[V]** | https://ebible.org/porbr2018/copyright.htm |
| OPUS-MT `opus-mt-tc-big-en-pt` | Modelo de tradução inglês→português (marcador `>>pob<<` para o Brasil) | CC BY 4.0 **[V]** | https://huggingface.co/Helsinki-NLP/opus-mt-tc-big-en-pt |
| `BAAI/bge-m3` | Modelo de embeddings multilíngue, 1024 dimensões, 8192 tokens | MIT **[V]** | https://huggingface.co/BAAI/bge-m3 |
| `intfloat/multilingual-e5-small` | Modelo de embeddings multilíngue, 384 dimensões, 512 tokens | MIT **[S]** | https://huggingface.co/intfloat/multilingual-e5-small |

Observações de licença **[I]**:

- CC BY e CC BY-SA pedem atribuição: prever uma tela "Créditos e fontes".
- CC BY-SA (Theographic, ACAI) só pesa se o aplicativo for distribuído com os
  dados embutidos. Para uso pessoal não há obstáculo; para distribuir, o mais
  simples é manter cada fonte externa como pacote separado, baixado e importado
  pelo mesmo importador, com a procedência registrada em `modules` como já se
  faz.
- Nada aqui é aconselhamento jurídico; são leituras das páginas de licença.

## O que não vale a pena

- **Traduzir a biblioteca inteira de antemão.** Trinta comentários e trinta
  dicionários são muito texto para traduzir em CPU, e a maior parte nunca será
  lida. Sob demanda com cache dá o mesmo resultado para o que importa **[I]**.
- **Chat genérico sem citações.** É o que mais aparece nos projetos recentes
  com IA, e o que menos se pode conferir. Só faz sentido no formato do item 19.
- **Treinar ou ajustar modelo próprio.** Há quem ajuste modelos abertos para
  texto bíblico (Rhema AI **[S]**); para uma biblioteca pessoal o custo não se
  paga, e recuperação com citação resolve melhor.
- **Banco de grafos (Neo4j ou similar).** O Theographic traz scripts para
  Neo4j **[V]**, mas as relações úteis aqui (versículo–versículo,
  entidade–versículo, verbete–versículo) cabem em tabelas SQLite, sem serviço
  extra para instalar **[I]**.
- **Árvores sintáticas (MACULA) na interface.** Dado excelente e aberto, mas
  baseado em Nestle1904/SBLGNT, não no TR que o usuário tem, e voltado a quem
  lê grego com fluência. Guardar como possibilidade, não planejar.
- **Visualizações decorativas** (arcos de referências cruzadas, nuvem 3D de
  versículos, como no BibleLLM **[S]**). Bonitas na primeira vez, pouco usadas
  no estudo.
- **Recursos sociais, sincronização em nuvem, versículo do dia, sequências de
  dias.** São o centro do YouVersion **[S]**, que atende outro objetivo
  (engajamento e comunidade) e contrariam "local e offline". Do YouVersion vale
  aproveitar só planos de leitura com progresso (item 6).
- **Abrir os módulos criptografados (`.ontx`, `.ntx`).** Além do esforço, é
  contornar proteção de conteúdo licenciado.
- **Loja ou baixador de módulos de terceiros.** A maior parte dos módulos que
  circulam tem situação de direito autoral incerta; o importador de arquivos
  locais já resolve.
- **NLLB-200 como tradutor.** Os pesos são CC BY-NC 4.0 **[S]**. Serve para
  uso pessoal, mas trava qualquer distribuição futura; o OPUS-MT não tem essa
  restrição.
- **Montador de sermões.** Logos e Accordance investem nisso; nada no plano
  indica que o usuário prega. A exportação de estudo da Fase 6 cobre o
  essencial.

## O que cada programa pesquisado oferece (resumo)

- **Logos**: Smart Search (busca híbrida palavra + significado, com sinopse e
  botão de resumo) **[S]**; Study Assistant com respostas citadas e restrição
  à biblioteca; Factbook com perguntas sugeridas **[V]**; Auto Translate de
  livros **[S]**. Recursos de IA exigem assinatura e têm cota mensal **[S]**.
- **Accordance**: comando INFER, que procura em um texto frases semelhantes às
  de outro (intertextualidade); janela de paralelos (sinóticos,
  Reis/Crônicas) **[S]**.
- **STEP Bible**: interlinear configurável, gramática com código de cores,
  palavras relacionadas por traço semântico, interface em dezenas de idiomas,
  versão para instalar e usar offline **[S]**. Não confirmei interface em
  português. É de onde vêm os melhores dados abertos.
- **Blue Letter Bible / Bible Hub**: por versículo, interlinear e interlinear
  reverso, concordância por Strong, léxicos (Thayer, BDB), TSK, comentários,
  dezenas de versões empilhadas **[S]**. São o modelo do "painel do versículo"
  que o projeto já tem.
- **Olive Tree**: painel dividido com o comentário acompanhando o texto;
  compras avulsas, sem planos de leitura fortes **[S]**.
- **YouVersion**: planos de leitura, comunidade, áudio; em 2026 abriu uma
  plataforma para desenvolvedores **[S]**. Não confirmei recursos de IA.
- **MySword**: módulos offline, comparação de versões, Strong ligado a
  dicionário, notas pessoais e diários, lista de versículos, tela dividida na
  edição paga **[S]**.
- **AndBible**: áreas de trabalho com configuração própria, Strong, marcadores
  com etiquetas e notas, cadernos de estudo, leitura em voz alta **[S]**.
- **Projetos recentes com IA**: StudyBible MCP (servidor que expõe notas de
  estudo, dicionário e entidades ACAI a um assistente), Biblos (embeddings por
  versículo, inglês), BibleLLM (RAG local, grafo, mapas, só versões inglesas),
  TextLab Bible (exegese do NT grego com busca híbrida), BibleMate/UniqueBible
  **[S]**. Padrão comum: embeddings por versículo em inglês + RAG. Nenhum
  trata o caso português↔inglês.

## Fontes consultadas

Páginas que abri e li (base das marcas **[V]**):

- https://www.openbible.info/labs/cross-references/
- https://github.com/openbibleinfo/Bible-Geocoding-Data
- https://github.com/STEPBible/STEPBible-Data
- https://github.com/robertrouse/theographic-bible-metadata
- https://github.com/Clear-Bible/macula-greek
- https://github.com/Clear-Bible/macula-greek/blob/main/LICENSE.md
- https://github.com/BibleAquifer
- https://github.com/BibleAquifer/ACAI
- https://github.com/openscriptures/strongs
- https://ebible.org/porbr2018/copyright.htm
- https://huggingface.co/Helsinki-NLP/opus-mt-tc-big-en-pt
- https://huggingface.co/BAAI/bge-m3
- https://www.logos.com/grow/release-november-2025/

Páginas vistas apenas por resumo de busca (base das marcas **[S]**):

- Logos: https://support.logos.com/hc/en-us/articles/35181728416397-How-Logos-uses-AI (bloqueou o acesso direto),
  https://support.logos.com/hc/articles/23526184005261,
  https://community.logos.com/kb/articles/2919-logos-46-0 (bloqueou o acesso direto),
  https://support.logos.com/hc/en-us/articles/8160540355597,
  https://www.logos.com/grow/auto-translate-bibles/
- Accordance: https://www.accordancebible.com/tag/infer,
  https://brianwdavidson.com/2022/02/07/finding-similar-words-with-accordances-infer-command/
- STEP Bible: https://www.stepbible.org/downloads.jsp,
  https://stepweb.atlassian.net/wiki/spaces/SUG/pages/9797667/Bible+Displays,
  https://stepweb.atlassian.net/wiki/spaces/SUG/pages/12484619/Copyrights+Licences
- Blue Letter Bible: https://www.blueletterbible.org/help/using_blb.cfm,
  https://blogs.blueletterbible.org/blb/tag/interlinear/
- Bible Hub: https://biblehub.com/
- MySword: https://mysword.info/features
- AndBible: https://faith.tools/app/andbible
- Olive Tree e YouVersion: https://learnofchrist.com/resources/olive-tree,
  https://learnofchrist.com/resources/youversion (site de resenhas; tratar com cautela)
- Projetos com IA: https://viz.bible/announcing-study-bible-mcp-ai-scripture-integration/,
  https://faith.tools/app/807-biblos, https://biblellm.vercel.app,
  https://github.com/Kiyahj81/TextLab_Bible
- Dados: https://viz.bible/bible-data/, https://theographic.netlify.app/about,
  https://github.com/openscriptures/morphhb, https://hb.openscriptures.org/,
  https://huggingface.co/intfloat/multilingual-e5-small,
  https://github.com/Helsinki-NLP/Opus-MT,
  https://github.com/facebookresearch/fairseq/blob/nllb/README.md,
  https://arxiv.org/pdf/2504.16264
- Strong em português (SBB, comercial): https://media.olivetree.com/store/product/17001

Não consegui confirmar: interface em português no STEP Bible; licença do
repositório `openscriptures/strongs`; licenças e idiomas dos recursos do Bible
Aquifer além do ACAI; cobertura real dos rótulos em português do ACAI;
existência de tabela aberta de passagens paralelas (sinopse) e de léxico
Strong em português com licença aberta; compatibilidade das bibliotecas de
tradução e embeddings com Python 3.14.
