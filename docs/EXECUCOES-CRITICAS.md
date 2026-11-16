# Execuções críticas

As tarefas do [BACKLOG.md](BACKLOG.md) classificadas por relevância e
complexidade, a ordem em que devem ser executadas e, para as mais difíceis e
importantes, um desenho detalhado. Escrito em 2026-11-16.

Os fatos citados aqui (marcação dos arquivos, contagens) foram conferidos nos
módulos reais e na base `data/library-full.db`. O que é proposta de desenho
está marcado como proposta e pode ser revisto por quem executar, desde que a
mudança seja registrada em [DECISOES.md](DECISOES.md).

## Critérios

**Relevância**
- **A** — sem isto o objetivo do projeto não é atingido (base confiável ou a
  ponte português ↔ inglês).
- **B** — melhora forte para o uso diário.
- **C** — conveniência ou trabalho de apoio.

**Complexidade**
- **Alta** — exige desenho novo, formato ainda não totalmente conhecido ou
  mexe em várias camadas (importador, base, API, interface); erro custa
  reimportar tudo.
- **Média** — mudança em uma ou duas camadas, com critério de aceite claro.
- **Baixa** — mudança local.

**Executor recomendado**
- **Capaz** — o modelo mais capaz disponível, com tempo para investigar antes
  de escrever código.
- **Padrão** — qualquer modelo competente; a tarefa está especificada o
  bastante para ser seguida.

## Classificação de todas as tarefas

| Tarefa | Assunto | Relevância | Complexidade | Executor | Onda |
|---|---|---|---|---|---|
| T01 | Linha de cabeçalho e títulos de seção (e-Sword) | A | Média | Padrão | 1 |
| T02 | Uma só cópia de cada Bíblia | A | Baixa | Padrão | 1 |
| T03 | Erros restantes de leitura | A | Baixa | Padrão | 1 |
| T04 | Metadados limpos | B | Baixa | Padrão | 1 |
| T06 | Verificação para a base completa | A | Baixa | Padrão | 1 |
| T07 | Reimportar, verificar e promover | A | Baixa | Padrão | 1 |
| **T05 + T21** | **Modelo de palavras e tabela de correspondência (EC1)** | **A** | **Alta** | **Capaz** | **2** |
| **T08** | **Interface na escala da biblioteca (EC4)** | **A** | **Alta** | **Capaz** | **2** |
| T09 | Auxiliares do theWord (referências cruzadas, parágrafos) | B | Média | Padrão | 2 |
| **T23** | **Busca bilíngue (EC2)** | **A** | **Alta** | **Capaz** | **3** |
| **T20 + T22** | **Strong clicável e painel "Palavra" (EC3)** | **A** | **Média** | Padrão | 3 |
| T25 | Referências cruzadas ranqueadas | B | Média | Padrão | 3 |
| **T24** | **Citações clicáveis nos comentários (EC5)** | **A** | **Alta** | **Capaz** | **4** |
| T11 | Testes automatizados | C | Média | Padrão | contínuo |
| T10 | Importação incremental | C | Média | Padrão | 4 |
| **T30–T33** | **Busca semântica (EC6)** | **B** | **Alta** | **Capaz** | **5** |
| T34 | Passagens parecidas | B | Baixa | Padrão | 5 |
| T40–T42 | Notas, importação de notas, exportação | B | Média | Padrão | 6 |
| **T50–T51** | **Assistente de importação e casca desktop (EC7)** | **A se o projeto for público** | **Alta** | **Capaz** | **7** |
| T52 | Créditos e licenças | A se público | Baixa | Padrão | 7 |

## Ordem de execução

Cada onda só começa quando a anterior passou nos critérios de aceite.

**Onda 1 — Base confiável.** T01 → T02 → T03 → T04 → T06 → T07. Todas mexem
em `importer/esword.py`, `importer/build.py` e `importer/verify.py`: um só
executor, em sequência, uma reimportação completa no fim (cerca de 10
minutos). Nada das ondas seguintes vale a pena sobre uma base com defeito.

**Onda 2 — Duas trilhas em paralelo**, porque tocam arquivos diferentes:
- trilha de dados: EC1 (T05 + T21) e T09, em `importer/`;
- trilha de interface: EC4 (T08), em `app/`.

O ponto de contato é `app/server.py`: combinar antes quem altera qual
endpoint. As duas trilhas terminam com uma reimportação.

**Onda 3 — A ponte aparece para o usuário.** EC2 (T23) e EC3 (T20 + T22),
depois T25. É aqui que o projeto passa a fazer algo que os outros não fazem.

**Onda 4 — Citações.** EC5 (T24). Fica depois da ponte porque altera o
conversor de RTF, que é usado por quase tudo, e exige reimportação.

**Onda 5 — Embeddings.** EC6. Depende da resposta do usuário sobre
dependências externas (P3 no backlog).

**Ondas 6 e 7 — Notas e produto.** Dependem de P1 (projeto público ou não).

## EC1 — Modelo de palavras e tabela de correspondência (T05 + T21)

**Por que é crítica.** É a fundação de toda a ponte português ↔ inglês: busca
bilíngue, painel "Palavra", ocorrências e interlinear dependem dela. Hoje os
códigos Strong estão embutidos num texto (`verses.tagged`), o que não permite
consultar "todas as palavras com G25".

**O que os arquivos trazem (conferido).** Cinco Bíblias têm marcação por palavra:

| Módulo | Marcação bruta de uma palavra | Dá |
|---|---|---|
| `tr.nt` (theWord) | `<wt>ηγαπησεν<WG25><WTV-AAI-3S l="αγαπαω">` | grego, Strong, morfologia, lema |
| `BSB Interlinear NT-Grk.nt` | `<wt><O> ἠγάπησεν<o><T> ēgapēsen<t><E> loved<e><WG25><WTV-AIA-3S l="ἀγαπάω">` | grego acentuado, transliteração, glosa inglesa, Strong, morfologia, lema |
| `BSB Reverse Interlinear.ont` | `<wt><E> loved<e><OG> ἠγάπησεν<og><T> ēgapēsen<t><WG25><WT… l="…">`; no AT, `<O>…<o>` com `<WH…>` | inglês alinhado ao original, na ordem do inglês, Bíblia inteira |
| `kjv.ont` | `<FR> loved<Fr><WG25>` | expressão inglesa, Strong |
| `ara_ra_com_strongs.bblx` (e-Sword) | `amou {\cf11\super G25 [G5656]}` | expressão portuguesa, Strong, código de análise do verbo |

O interlinear reverso tem 443.627 palavras (305.496 hebraicas, 138.131
gregas). Estimativa para as cinco: cerca de 1,3 milhão de linhas.

**Desenho proposto.** Tabela nova, preenchida pelo importador:

```
tokens(module_id, book, chapter, verse, pos,   -- pos = ordem na frase
       surface,      -- o que aparece no texto do módulo (português, inglês ou grego)
       strong,       -- 'G25' / 'H7225'; nulo se a palavra não tem código
       lemma, morph, -- quando o módulo traz
       original, translit, gloss)  -- só nos interlineares
índices: (strong), (module_id, book, chapter, verse, pos)
```

`verses.text` passa a ser montado a partir de `surface` (resolve a T05: o
texto do interlinear reverso vira prosa inglesa limpa). `verses.tagged` pode
ser mantido por compatibilidade ou removido; decidir e registrar.

Tabela derivada, calculada no fim da importação:

```
strong_terms(strong, lang, term, count, share)   -- share = fração das ocorrências
```

`term` é `surface` normalizado: minúsculas, sem pontuação, sem artigos e
preposições iniciais ("No princípio," → "princípio").

**Passos.**
1. Escrever um analisador de palavra por formato, devolvendo a mesma
   estrutura. Começar pelo TR (mais simples) e pelo interlinear reverso (mais
   rico).
2. ARA: a expressão portuguesa de um código é o texto entre o código anterior
   e ele. Código logo após outro código, sem texto, é palavra original não
   traduzida (por exemplo `{H853}`): gravar com `surface` vazio.
3. Separar códigos lexicais dos de análise verbal: Strong hebraico vai até
   H8674 e grego até G5624; acima disso (H8804, G5656) é análise e vai para
   `morph`, não para `strong`.
4. Calcular `strong_terms` para português (ARA), inglês (KJV e BSB) e grego
   (lema do TR).
5. Reimportar e validar.

**Riscos.**
- Segmentação da ARA: a expressão pode incluir palavras a mais ("ao mundo").
  A normalização reduz, não elimina. Aceitar ruído e confiar na contagem.
- Um mesmo Strong tem várias traduções; `share` existe para filtrar as raras.
- Aumento do tamanho da base (estimado em 100 a 200 MB) e do tempo de importação.
- A marcação da KJV tem variações (`<XWG`, itálicos `<FI>`): cobrir com testes.

**Validação.**
- Contagem de tokens por módulo igual à contagem de tags `<wt>` ou de códigos
  no arquivo de origem.
- Jo 3:16 do interlinear reverso: `verses.text` é inglês sem caracteres gregos.
- Para cada código abaixo, o termo mais frequente confere:

| Strong | Português (ARA) | Inglês (KJV) |
|---|---|---|
| G5485 | graça | grace |
| G4102 | fé | faith |
| G1343 | justiça | righteousness |
| G3056 | palavra | word |
| H430 | Deus | God |
| H7965 | paz | peace |
| H2617 | misericórdia ou benignidade | mercy |

Se algum não conferir, investigar antes de seguir; não ajustar a tabela à mão.

**Arquivos.** `importer/db.py`, `importer/theword.py`, `importer/esword.py`,
`importer/build.py`, `importer/verify.py`, `docs/FORMATOS.md`.

## EC2 — Busca bilíngue (T23)

**Por que é crítica.** É a funcionalidade que justifica o projeto: digitar em
português e encontrar o acervo em inglês, sem IA e com explicação.

**Desenho proposto.** Em `app/server.py::api_search`:
1. Para cada palavra da consulta, procurar em `strong_terms` os códigos em que
   ela é termo português com `share` acima de um limite (começar em 0,2).
2. Para cada código, pegar os dois ou três termos ingleses de maior `share`.
3. Montar a consulta FTS com um grupo por palavra:
   `("graça" OR "grace")`, grupos unidos por E.
4. Devolver `expansions`: para cada palavra, os termos incluídos e por qual
   código, com a contagem. A interface mostra isso acima dos resultados
   ("incluí *grace* por G5485, 120 ocorrências") e permite desligar.

**Riscos.**
- Palavras muito comuns ("ser", "ter", "dizer") expandem para dezenas de
  termos: lista de exclusão e teto de expansões por palavra.
- Só cobre vocabulário que aparece na Bíblia. Termos teológicos posteriores
  ("pré-milenismo") ficam para a busca semântica (EC6).
- Resultados em inglês misturados aos em português: manter português primeiro
  e mostrar o idioma em cada resultado (a etiqueta já existe).

**Validação.** Montar 15 consultas em português (graça, fé, arrependimento,
aliança, justificação, expiação, ressurreição, batismo, oração, santificação,
reino, misericórdia, redenção, esperança, pecado). Para cada uma, conferir à
mão os 10 primeiros resultados de comentários com e sem expansão e registrar
quantos são pertinentes. A expansão tem de aumentar os pertinentes sem que os
10 primeiros fiquem dominados por ruído. Guardar a planilha em `docs/`.

**Depende de.** EC1.

## EC3 — Strong clicável e painel "Palavra" (T20 + T22)

**Desenho proposto.** `/api/chapter` devolve os tokens do capítulo quando o
módulo os tem; a interface desenha cada palavra como elemento clicável (com
opção de mostrar ou esconder os números). Novo endpoint `/api/word?strong=G25`
devolve:
- verbetes cujo `topic` é o código, por módulo. Léxicos legíveis na base:
  Dodson (grego), AHLB (hebraico), LSJ, MLSJ, KJC, LXXHebGreek;
- como cada versão traduz o termo (`strong_terms`), com contagem;
- ocorrências, paginadas, com o versículo na versão portuguesa preferida.

**Lacuna conhecida.** Não há dicionário Strong hebraico legível (o de
Mickelson é criptografado). A pesquisa de conteúdo de domínio público
(`docs/PESQUISA-CONTEUDO-PUBLICO.md`, em andamento) deve indicar uma fonte;
conferir a licença antes de usar.

**Validação.** Em Jo 3:16 da ARA com Strong, clicar em "amou" abre G25 com o
verbete do Dodson, "amar" e "love" como traduções e a lista de ocorrências.

**Depende de.** EC1.

## EC4 — Interface na escala da biblioteca (T08)

**Por que é crítica.** A interface foi testada com 2 comentários. Com 24, o
painel de um versículo muito comentado fica inutilizável, e a resposta da API
traz o texto integral de todos (Gill sozinho pode ter várias páginas por
versículo). Sem isto, promover a base completa piora a experiência.

**Desenho proposto.**
- `/api/verse` devolve, por comentário, só um trecho (primeiros 400
  caracteres) e o tamanho total; o texto integral vem de `/api/item` quando o
  usuário abre.
- Painel agrupado por módulo, português primeiro, uma linha por comentário
  (sigla, intervalo, início do texto), abrindo no clique.
- Filtros no topo do painel: idioma e tipo. Guardar a escolha.
- "Citado em": agrupar por módulo com contagem; listar os itens só ao abrir o
  grupo. Em versículos centrais pode haver centenas.
- Seletor de versão: agrupar por idioma.
- Busca: paginação ("mais resultados") e botão de voltar à lista depois de
  abrir um resultado.
- Títulos de perícope na leitura (campo `heading`, depende de T01).

**Orçamento de desempenho.** Medir, na base completa, em Jo 3:16, Rm 8:28,
Sl 23:1 e Gn 1:1: tamanho da resposta de `/api/verse` (meta: abaixo de 200 KB)
e tempo até o painel aparecer (meta: abaixo de 1 s). Registrar os números
antes e depois.

**Riscos.** A consulta de comentários usa intervalo (`ref_start <= ? and
ref_end >= ?`), que o índice atual atende mal; se ficar lenta, criar índice
por `(book, ref_start)` e limitar pelo capítulo.

**Arquivos.** `app/server.py`, `app/static/app.js`, `app/static/style.css`.
Testar no navegador, inclusive em tela estreita e nos dois temas (ainda não
testados).

## EC5 — Citações clicáveis nos comentários (T24)

**Por que é crítica.** Boa parte de um comentário antigo é citação bíblica.
Mostrar o versículo em português ao passar o mouse reduz muito o esforço de
ler em inglês. É difícil porque a posição das citações se perde na conversão
para texto limpo.

**O que existe (conferido).**
- theWord, RTF: `{\field{\*\fldinst HYPERLINK "tw://bible.*?id=9.7.1|_AUTODETECT_|"}{\fldrslt … 1 Sam. 7:1}}`.
  O conversor descarta o `fldinst` e mantém só o texto visível.
- theWord, RVF: o alvo vem no fim do cabeçalho do item de texto:
  `6 1 -1 9 0 "tw://bible.*?id=9.6.18|_AUTODETECT_|"`.
- e-Sword: só padrões textuais. Vistos na base: `Gen_17:1-16`, `1Jo_3:2`,
  `Eph_2:8-10` (abreviações inglesas do e-Sword) e `At 13.39`, `Jo 1.29`,
  `Gl 2.16` (abreviações portuguesas). O comentário "MH" não mostrou nenhum
  padrão na amostra examinada.
- A tabela `links` já tem, por tópico do theWord, o conjunto de versículos
  citados (2,1 milhões em comentários, 866 mil em verbetes), sem posição.

**Desenho proposto.** Não colocar marcadores dentro do texto (mantém a busca
simples). Tabela nova com posições:

```
refs(kind, item_id, start, end,        -- posição em caracteres no texto limpo
     book, chapter, verse_start, verse_end)
```

- `rtf.py`: nova função que devolve o texto e a lista de trechos com alvo,
  registrando a posição enquanto monta a saída. Atenção: `tidy()` altera
  espaços no fim; ou as posições são calculadas depois da limpeza, ou a
  limpeza passa a ser feita de modo que preserve o mapeamento.
- `rvf.py`: ler o alvo do cabeçalho e associar ao texto do item.
- e-Sword: expressões regulares com duas tabelas de abreviação (inglesa do
  e-Sword e portuguesa, esta a partir de `importer/canon.py` mais variantes).
- Interface: ao exibir um comentário, envolver os trechos de `refs` em
  elementos clicáveis; ao passar o mouse, buscar o versículo na versão
  portuguesa preferida.

**Validação (há um oráculo pronto).** Para cada tópico do theWord, o conjunto
de versículos em `refs` deve coincidir com o da tabela `links`. Meta: 99% dos
tópicos idênticos; listar e explicar as diferenças. Para o e-Sword, conferir à
mão 50 citações de três comentários.

**Riscos.** Mexe no conversor de RTF usado por todos os módulos: escrever os
testes da T11 para `rtf.py` antes de alterar. Intervalos que cruzam capítulos
e listas ("vv. 3, 5-7") precisam de regra explícita.

## EC6 — Busca semântica (T30–T33)

**Por que é crítica.** Cobre o que a ponte por Strong não cobre (temas e
conceitos sem palavra bíblica direta). É a parte com mais incerteza técnica.

**Ordem obrigatória: medir antes de construir.**
1. **T30 — ambiente.** Verificar se as bibliotecas necessárias têm pacote
   para Python 3.14; se não, usar um ambiente separado com versão anterior só
   para o indexador. Registrar a decisão (revê a D003). Depende de P3.
2. **T31 — conjunto de avaliação**, com dados da própria base:
   (a) pares de referência cruzada (TSK e `xrefs` da T09): dado um versículo,
   os relacionados devem aparecer entre os vizinhos;
   (b) versículo em português ↔ comentário em inglês sobre o mesmo versículo:
   é exatamente o caso de uso. Métrica: recall@10 e MRR. A busca por palavra
   com expansão (EC2) é a linha de base a superar.
3. **Medir vazão** em uma amostra de 2.000 trechos, para estimar o tempo total
   antes de indexar tudo.
4. **T32 — indexar por etapas:** primeiro os versículos de uma Bíblia em
   português e da KJV (cerca de 62 mil); depois os comentários em português;
   depois dois ou três comentários em inglês. Só ampliar se a etapa anterior
   mostrar ganho na avaliação.
5. **T33 — busca híbrida**, combinando as duas listas por posição (RRF).

**Riscos.**
- Volume: há 204 mil comentários, muitos longos; divididos em trechos podem
  passar de um milhão. Em CPU isso pode levar muitas horas, e a busca exata
  deixa de ser instantânea. Por isso as etapas.
- Modelos multilíngues nem sempre aproximam bem português e inglês: a
  avaliação (b) decide o modelo, não a reputação dele.
- Guardar junto de cada vetor o modelo, a versão e a chave de origem do texto,
  para poder reindexar só o que mudou.

**Candidatos citados na pesquisa** (licenças não conferidas por nós):
`BAAI/bge-m3` e `intfloat/multilingual-e5-small`.

## EC7 — Assistente de importação e casca desktop (T50–T51)

**Por que é crítica, se o projeto for público.** Hoje usar o aplicativo exige
Python e linha de comando. Sem isto não há produto para outras pessoas. Se o
uso for só pessoal, a relevância cai para C.

**Pontos de desenho a resolver antes de codificar** (registrar em DECISOES):
- como o aplicativo embute o importador (Python empacotado junto, ou
  importador reescrito na linguagem da casca);
- detecção automática das pastas do e-Sword e do theWord e escolha manual;
- progresso da importação na interface, com o relatório de ignorados em
  linguagem simples;
- onde ficam a base e os dados do usuário em cada sistema;
- nenhum módulo protegido é distribuído junto.

**Depende de.** P1 no backlog.

## O que não é crítico

T03, T04, T06, T10 e T11 são necessárias, mas simples e bem especificadas:
servem para qualquer executor e não devem consumir o tempo do modelo mais
capaz. T34, T40–T42 e T52 só entram depois que as ondas 1 a 4 estiverem prontas.
