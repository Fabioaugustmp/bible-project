# Análise dos módulos MySword da pasta do Drive (2026-11-23)

Pedido: avaliar se compensa usar algum módulo MySword da pasta do Drive do usuário.
A pasta não tem um zip único. Tem cerca de 110 arquivos em subpastas (Bibles, dictionaries,
Strongs, Books, Journals), quase todos repetidos. Foram baixados **55 arquivos distintos**
(um por título e tamanho), sem falhas, para uma pasta temporária fora do projeto. Nada foi
copiado para `data/` nem para o git (D007).

Não baixados: o APK do MySword (programa, não módulo), os cadernos `*.jor.mybible`
(modelos vazios de 57 KB e marcadores pessoais) e as cópias `.zip`/`.gz` de módulos já baixados.

Método: cada arquivo foi aberto em modo somente leitura (`mode=ro&immutable=1`). Foram lidos a
tabela `Details`, a contagem de linhas, amostras (Jo 3:16, Gn 1:1, G26, H430) e versículos
vazios. Cada Bíblia foi comparada com a `data/library.db` pelo texto normalizado de quatro
versículos. As frases de licença vieram dos próprios módulos. As licenças da Bíblia Livre e
do OpenGNT foram conferidas também na página de origem (GitHub). As demais **não** foram
conferidas na origem. Este documento não é orientação jurídica.

## Resumo

Compensa, mas para poucos módulos. Quatro têm valor claro:

| Prioridade | Módulo | Por que vale | Licença (indicada) | Onde pode ser usado |
|---|---|---|---|---|
| 1 | **Strong** (BDB + Thayer + Strong + TVM + uso na KJV), 14.696 verbetes | A biblioteca não tem o léxico de Strong, nem Thayer, nem BDB. Hoje o painel Strong usa Dodson (grego) e AHLB (hebraico, © 2005). | Obras de 1889 a 1906, domínio público; formatação de Timothy Morton (Bible Analyzer), "courtesy" | Local e, com crédito, no site |
| 2 | **Bíblia Livre** (BLIVRE), 31.102 versículos | Única Bíblia moderna em português com licença aberta. É o que permite uma demonstração pública sem risco (relatório de prospecção). | **CC BY 3.0 BR**, conferida na origem: uso comercial permitido, atribuição obrigatória, sem compartilhamento obrigatório | Local e site |
| 3 | **Strong-PT** (Dicionário Bíblico Strong da SBB), 14.691 verbetes | O mais valioso para a ponte português-inglês: definições Strong em português. | **© 2002 SBB.** O módulo diz que "não é publicado nem autorizado pelo titular" e que é "exclusivamente para uso pessoal" | **Só uso pessoal e local. Nunca no site.** |
| 4 | **Analytic Septuagint** (ALXX), 23.145 versículos com Strong | A biblioteca não tem a Septuaginta. Liga o hebraico do AT ao grego do NT pelo número Strong. | "Public Domain" indicado no módulo | Local e site, após conferir na origem |

Valor médio: OpenGNT (grego do NT com Strong, morfologia e glosa), Abbott-Smith (léxico grego
de 1922), Bíblias inglesas em domínio público (WEB, NHEB, BBE, AKJV), "Morning and Evening" de
Spurgeon, e as imagens dos atlas de 1910 e 1918 e de Doré.

Não compensa: o restante (já está na biblioteca, tem direitos restritos, está criptografado ou
tem procedência duvidosa).

## O que a biblioteca ganha (por módulo)

### Dicionários

| Arquivo | Verbetes | Já temos? | Licença indicada | Observação |
|---|---|---|---|---|
| `strong.dct` (2 versões, v2.2 de 2025-09-01) | 14.696 com chave Strong | **Não** | Domínio público (Strong 1890, BDB 1906, Thayer 1889) | G26 traz original, transliteração, Thayer, Strong e "116 ocorrências na KJV". Melhor que Dodson e KJC juntos. A versão de 35,7 MB tem as referências; a "lite" não |
| `strong_lite.dct` | 14.696 | Não | Idem | Sem referências de versículos. Redundante se importar o completo |
| `bdb.dct`, `thayer.dct`, `bdb-thayer.dct` | 8.674 / 5.523 / 14.197 | Não | Idem | Já contidos no `strong.dct` |
| `Strongs_BR.dct` | 14.691 | Não | **© SBB, sem autorização** | Definições em português boas. Defeito: a palavra original vem corrompida (G26 aparece em letras hebraicas; H430 traz o escape RTF `\'92`) |
| `AbbottSmith.dct` | 5.523 | Não | Obra de 1922 (fonte: archive.org); situação no Brasil depende da data de morte do autor, não conferida | Léxico do NT mais acadêmico que Thayer |
| `AHLB.dct` | 5.897 | Sim (AHLB) | © 2005 Ancient Hebrew Research Center | Nada a ganhar |
| `LXX-GreekHebrew.dct` | 6.597 | Sim (LXXHebGreek) | — | Nada a ganhar |
| `kjc.dct`, `kjvd.dct`, `americantract.dct` | — | Sim (KJC, KJVD, AmTrac) | — | Nada a ganhar |
| `bridgeway.dct` (2 versões) | 847 | Não | **© Don Fleming, All Rights Reserved** | Dicionário moderno; só uso pessoal |

### Bíblias

| Arquivo | Versículos | Já temos? | Licença indicada | Observação |
|---|---|---|---|---|
| `biblialivre` | 31.102 (5 vazios: Ed 3:6, Sl 108:13, 2Co 13:14, 3Jo 1:14, Ap 12:17) | Não | **CC BY 3.0 BR** (conferido) | Trabalho em andamento: citar a data da versão (2016-10-19 no módulo) |
| `alxx` (Analytic Septuagint) | 23.145, 22.821 com Strong (303 vazios) | Não | "Public Domain" | Grego sem acentos, com morfologia |
| `OpenGNT` (5 variantes) | 7.941 | Parcial (BSBGrkINT, TR) | Texto grego base: **CC BY-SA 4.0** (conferido). Camadas NET (não comercial), Berean (permissão), Mounce (©) têm termos próprios | Se importar, usar só a variante sem NET (`OpenGNT` ou `OpenGNTa`) e respeitar o compartilhamento pela mesma licença |
| `web`, `nheb`, `bbe`, `akjv` | 31.102 cada | Não | Domínio público | Úteis para uma demonstração pública em inglês |
| `kjv` (2 versões, v2.9.4 de 2023) | 31.102 com Strong | Sim (KJV do theWord) | Domínio público (Crown copyright no Reino Unido) | 4 de 4 versículos iguais; ganho só se as marcas forem melhores |
| `berean-bsb` | 31.102 | Parcial (BSB interlinear) | Módulo diz © 2016, 2020, citação até 2.000 versículos | Texto mais recente que o nosso; licença atual não conferida |
| `net` | 31.102 | Não | © Biblical Studies Press | Só citação |
| `isv` | 31.102 | Não | © ISV Foundation, até 500 versículos | Só citação |
| `easyenglish` | 30.464 | Não | © Wycliffe Associates (UK), uso livre com aviso | Inglês simplificado; pouco útil para estudo |
| `hebmodern` | 31.102 | Não | Nada indicado | Procedência desconhecida |
| `ARA+` (3 cópias idênticas) | 31.102 com Strong | Sim (ARA1993+) | Texto da SBB (©) | Nada a ganhar |
| `jfa-ra(pt)`, `jfa-ra(br)`, `jfa-rc(pt)`, `arm1967` (variantes) | 31.102 | Sim (JFA-RA(Pt), JFA-RC(Pt), ARM1967) | Copiados de sites, sem licença | Nada a ganhar |
| `ACF2007` | 31.095 | Sim (ACF) | Texto da SBTB (©) | Nada a ganhar |
| `LTT` (Bíblia Literal do Texto Tradicional) | 31.102 | Não | **Autor proíbe uso acima de 500 versículos sem autorização escrita** | Interessante (literal, com palavras implícitas marcadas), mas só uso pessoal |
| `abp`, `HiSB` | — | Não | — | **Criptografados** (`encryption: 2`). Não abertos (D008) |

### theWord (`.ont`) que estavam na pasta

| Arquivo | Conteúdo | Licença | Avaliação |
|---|---|---|---|
| `jfa-ra-strong.ont` | ARA com Strong, texto do programa "Bíblia Online" da SBB | © SBB | Já temos ARA1993+ |
| `KJA - King James Português.ont` | King James Atualizada (2012) | © Abba Press / SBIA | Só uso pessoal |

### Livros

| Arquivo | Conteúdo | Já temos? | Licença | Observação |
|---|---|---|---|---|
| `spurgeon-morning-evening` | 745 leituras diárias | Não | Domínio público (Spurgeon, séc. XIX) | Devocional diário em inglês |
| `spurgeon-allofgrace` | 22 capítulos | Sim (Spurgeon-Grace) | — | Nada a ganhar |
| `rand-mcnally-bible-atlas` | 30 mapas em alta resolução (57 MB) | Não | Publicação de 1918 | Exige suporte a imagens, que o importador não tem |
| `completesundayschoolatlas` | 32 mapas (7,5 MB) | Não | Publicação de 1910 | Idem |
| `dores-bibleillustrations` | 103 gravuras (8,5 MB) | Não | Doré (1832-1883) | Idem |

## Custo para usar

O importador lê e-Sword e theWord, não MySword. O formato MySword verificado aqui:

- SQLite comum, com uma tabela `Details` (título, descrição, comentários, versão, e às vezes
  `encryption` e `compressed`).
- Bíblia: `Bible(Book, Chapter, Verse, Scripture)`, com a mesma marcação GBF do theWord
  (`<WG26>`, `<FI>…<Fi>`, `<FR>…<Fr>`, `<RF>…<Rf>`). O leitor do theWord pode ser reaproveitado.
- Dicionário: `dictionary(relativeorder, word, data)`, com chave Strong (`G26`, `H430`) e texto em HTML.
- Livro: `journal` (capítulos em HTML) e `data` (imagens em `content`, com `filename` e `description`).
- `encryption` diferente de zero: pular sem abrir (D008).

Estimativa: um leitor `importer/mysword.py` para Bíblia e dicionário é uma tarefa média,
porque a marcação já é tratada pelo leitor do theWord. Imagens dos atlas e de Doré exigem um
tipo novo na base e na interface: tarefa à parte.

## Recomendação

1. **Importar o `strong.dct` (completo).** Maior ganho de qualidade por menor custo, e melhora
   a licença do painel Strong no site (hoje o hebraico vem do AHLB, que tem copyright).
2. **Importar a Bíblia Livre.** Abre caminho para a demonstração pública com conteúdo livre.
   Registrar a licença (CC BY 3.0 BR, crédito "BLIVRE" e data da versão) em DECISOES.
3. **Importar o Strong-PT só na base local**, marcado como uso pessoal, e garantir que o site
   não o sirva. Antes, corrigir a palavra original (usar a do `strong.dct` pelo mesmo número).
   Depende da decisão sobre o que fica público (T52).
4. Depois, se houver interesse: ALXX, Abbott-Smith, Bíblias inglesas em domínio público e
   "Morning and Evening".
5. Não importar o resto.

Pendências: conferir na origem as licenças do ALXX, da formatação de Timothy Morton (Bible
Analyzer) e do Abbott-Smith antes de servi-los no site. Nada aqui entrou no backlog ainda.
