# Pesquisa de conteúdo em domínio público ou com licença aberta

Pesquisa feita em 2026-11-16. Complementa o
[PESQUISA-FEATURES.md](PESQUISA-FEATURES.md) (que já cobre referências
cruzadas, léxicos do STEPBible, geocodificação, ACAI, MACULA) e não repete o
que está lá. Nenhum arquivo foi baixado; só levantei e documentei.

**Como ler.** Cada afirmação de licença ou disponibilidade traz uma marca:

- **[V]** verificado por mim na página primária (site do projeto, repositório,
  página do módulo);
- **[S]** visto só em resumo de busca ou fonte secundária — conferir antes de
  depender disso;
- **[I]** inferência minha (inclusive tamanhos estimados e esforço).

Nada aqui é aconselhamento jurídico.

## Resumo

- A melhor aquisição **em português** não é obra antiga: são os recursos do
  **Bible Aquifer** (notas de estudo e dicionário bíblico da Tyndale, notas de
  estudo da Biblica), que têm pasta `por` e licença CC BY-SA 4.0 **[V]**, e os
  recursos **unfoldingWord em pt-br** no Door43 (notas, palavras-chave e
  perguntas, CC BY-SA 4.0) **[V]**. Juntos dão ao usuário o que hoje ele quase
  não tem: comentário e dicionário modernos, em português, redistribuíveis.
- Bíblias em português livres de fato: **Bíblia Livre** (CC BY 4.0),
  **Almeida Recebida** (domínio público declarado), **Bíblia Portuguesa
  Mundial** (domínio público, com deuterocanônicos), **Nova Bíblia Viva
  "Open"** da Biblica e **NVA** (CC BY-SA 4.0) **[V]**.
- Em inglês, as lacunas se fecham quase todas com módulos SWORD do CrossWire
  marcados "Public Domain" (Strong, Barnes NT, Clarke, Calvino, Keil &
  Delitzsch, Josefo, confissões) **[V]** e com XML aberto do Open Scriptures
  (Strong hebraico e BDB, CC BY 4.0) e do MorphGNT (Strong grego, CC0) **[V]**.
- **Não encontrei** dicionário Strong em português com licença aberta, nem
  comentário clássico completo em português em domínio público com texto
  digital pronto.
- Riscos principais: (1) **tradução tem direito próprio** — quase todo
  clássico em português (Henry, Spurgeon, Calvino, Agostinho) é tradução
  moderna protegida; (2) a **Tradução Brasileira de 1917** é domínio público
  nos EUA, mas a situação no Brasil é discutida; (3) **CC BY-SA** obriga a
  manter a mesma licença no material derivado, o que recomenda distribuir como
  pacotes separados; (4) CCEL, StudyLight e sites de módulos reivindicam
  direitos ou impõem condições sobre a **edição digital**; (5) alguns módulos
  "gratuitos" são só de uso não comercial (Kingcomments, Projeto Spurgeon).

## Em português

Ordenada por valor para o usuário.

| # | Obra | Autor e data | Tipo | O que acrescenta | Situação legal | Onde obter e formato | Esforço |
|---|---|---|---|---|---|---|---|
| 1 | Aquifer Open Study Notes (adaptação das Tyndale Open Study Notes) | Tyndale House Publishers 2023; adaptação Mission Mutual | comentário (notas de estudo) | Notas de estudo modernas em português, por versículo; hoje ele só tem notas de duas Bíblias de estudo | CC BY-SA 4.0 **[V]**; pasta `por` existe **[V]**; cobertura e se a tradução é humana ou automática: **não confirmei** | https://github.com/BibleAquifer/AquiferOpenStudyNotes — JSON e Markdown (também docx e pdf) por idioma **[V]**; tamanho não informado, estimo dezenas de MB **[I]** | Médio (leitor novo de JSON; formato documentado no repositório `docs`) |
| 2 | Aquifer Open Bible Dictionary (adaptação do Tyndale Open Bible Dictionary) | Tyndale 2023; Mission Mutual | dicionário | Dicionário bíblico moderno em português, muito além do "dicionário Almeida" | CC BY-SA 4.0 **[V]**; pasta `por` **[V]**; cobertura não confirmada | https://github.com/BibleAquifer/AquiferOpenBibleDictionary — JSON e Markdown **[V]** | Médio |
| 3 | Biblica Study Notes | Biblica 2023; Mission Mutual | comentário (notas) | Segundo conjunto de notas de estudo em português | CC BY-SA 4.0 **[V]**; pasta `por` **[V]** | https://github.com/BibleAquifer/BiblicaStudyNotes — JSON e Markdown **[V]** | Médio (mesmo leitor do item 1) |
| 4 | translationNotes pt-br (v7.1, 2022) | unfoldingWord / Door43, tradução brasileira | comentário (notas exegéticas para tradutores) | Notas versículo a versículo explicando expressões difíceis; vi pastas só dos 27 livros do NT **[V]** | CC BY-SA 4.0 (rodapé do DCS) **[V]** | https://git.door43.org/Door43-Catalog/pt-br_tn — Markdown, um arquivo por versículo; zip do release **[V]** | Médio |
| 5 | translationWords pt-br (v6.4, 2022) | unfoldingWord / Door43 | dicionário (termos-chave, nomes) | Verbetes curtos de termos teológicos e nomes, em português | CC BY-SA 4.0, com crédito "Original work available at https://door43.org/" **[V]** | https://git.door43.org/Door43-Catalog/pt-br_tw — Markdown, 547 KiB **[V]** | Baixo/médio |
| 6 | translationQuestions pt-br (v9.2) e Histórias Bíblicas Livres (OBS v3.2.3) | unfoldingWord / Door43 | livro / perguntas de compreensão | Perguntas por capítulo; 50 histórias bíblicas | CC BY-SA 4.0 (padrão do DCS) **[V]** para o site; LICENSE de cada repositório não abri **[I]** | https://git.door43.org/Door43-Catalog/pt-br_tq e `pt-br_obs` — Markdown **[V]** | Baixo/médio |
| 7 | Bíblia Livre (BLIVRE) | Diego Santos, Mario Sérgio, Marco Teles, 2018; revisão da Almeida 1819, Textus Receptus | Bíblia | Almeida em português atual que pode ser embutida no aplicativo | CC BY 4.0 **[V]** | https://ebible.org/find/details.php?id=porbr2018 — USFM, USFX, VPL+SQL, texto, módulo SWORD **[V]**; também módulos `PorBLivre` e `PorBLivreTR` no CrossWire **[V]**; ~1–5 MB **[I]** | Baixo (USFM/VPL) |
| 8 | Almeida Recebida (AR) | revisão da Almeida segundo o Textus Receptus; versão 1.7 de 2017 | Bíblia | Outra Almeida TR livre, linguagem atualizada | "This Bible (PorAR) is in the Public Domain" **[V]** | https://www.almeidarecebida.org/ — zip descrito como MySQL/XML; PDFs das edições de 1848 e 1850 **[V]** | Baixo/médio |
| 9 | Bíblia Portuguesa Mundial | eBible.org, 2022–2026 (rascunho em revisão) | Bíblia | Única livre com 15 livros deuterocanônicos (6.955 versículos) **[V]**; útil ao lado da católica | Domínio público **[V]**; tradutores e base não declarados na página **[V]** | https://ebible.org/porbrbsl/ — formatos eBible (USFM etc.) **[I]** | Baixo |
| 10 | Biblica Open Nova Bíblia Viva 2007 | Biblica, 2007/2010 | Bíblia | Versão legalmente redistribuível da "Viva" que ele já tem | CC BY-SA 4.0 **[V]** | https://ebible.org/poronbv/ — formatos eBible **[I]** | Baixo |
| 11 | NVA — Nova Versão de Acesso Livre | biblianva.com.br; baseada na Unlocked Literal Bible | Bíblia (o site fala em "Bíblia de Estudos") | Tradução literal moderna; possíveis notas | Módulo SWORD `PorNVA`: CC BY-SA 4.0 **[V]**; o site só diz "livre acesso, gratuita" sem licença formal **[V]**; notas de estudo: licença não confirmada | CrossWire `PorNVA`, 2 MB **[V]** | Médio (formato SWORD) |
| 12 | Almeida 1911 (reimpressão de edição de 1900) | João Ferreira de Almeida | Bíblia | Almeida histórica, ortografia antiga | Texto em domínio público **[I]**; o módulo declara "GPL" **[V]** (licença de software, estranha para texto) | CrossWire `PorAlmeida1911`, 1,6 MB **[V]** | Médio |
| 13 | Almeida 1819 (ortografia original e atualizada) | João Ferreira de Almeida | Bíblia | Texto-base histórico da Bíblia Livre | Autor morto em 1691: domínio público **[I]**; transcrição no Wikisource sob CC BY-SA 4.0 **[V]** | https://pt.wikisource.org/wiki/Bíblia — páginas wiki **[V]**; Almeida no Project Gutenberg nº 62383 **[S]** (site fora do ar na consulta) | Médio (extrair da wiki) |
| 14 | Tradução Brasileira (1917) | comissão de H. C. Tucker, W. C. Brown e outros | Bíblia | Primeira tradução feita no Brasil; valor histórico e literário | **Incerta no Brasil**: o próprio Wikisource a mantém só pela regra dos EUA (publicada antes de 1931) e a discussão não chega a conclusão **[V]**; a edição de 2010 da SBB tem ortografia atualizada e é vendida **[S]** | https://pt.wikisource.org/wiki/Tradução_Brasileira_da_Bíblia — 66 livros, copiada de bibliaonline.com.br (procedência de segunda mão) **[V]** | Médio; **não embutir** |
| 15 | Sermões | Pe. Antônio Vieira (1608–1697) | sermões | Clássico da língua, cheio de exposição bíblica | Autor em domínio público **[I]**; edições modernas (1965, 1974) usadas por alguns PDFs podem ter direitos de edição **[S]** | https://pt.wikisource.org/wiki/Autor:Antônio_Vieira — cerca de 40 sermões listados, nem todos transcritos **[V]**; PDFs avulsos em bibliotecas universitárias **[S]** | Médio/alto |
| 16 | Bíblia de Figueiredo (da Vulgata) | Pe. António Pereira de Figueiredo (m. 1797) | Bíblia católica | Tradução católica clássica com deuterocanônicos | Domínio público **[I]** | Só digitalizações: galerias de 1821, 1828, 1866 e 1891–96 no Wikisource, sem texto transcrito **[V]**; NT de 1803 na ATLA **[S]** | Alto (OCR) |
| 17 | Kingcomments em português | Ger de Koning; trad. Werner Klaes | comentário | Comentário devocional (linha dos Irmãos, como Darby/Kelly) | **Protegido**; "Free non-commercial distribution"; reprodução além do uso pessoal exige permissão **[V]** | CrossWire `PorKingComments`, 3,2 MB **[V]** | Médio; só uso pessoal |
| 18 | Tradução para Tradutores (NT) e Bíblia Livre Para Todos (NT) | E. Deibler 2018; Free Bible Ministry 2022 | Bíblia (NT) | NT explicativo, deixa o implícito explícito; funciona quase como paráfrase comentada | CC BY-SA 4.0 ambos **[V]** | https://ebible.org/portft/ e https://ebible.org/porblt/ | Baixo |

Não encontrei, apesar de procurar: Strong em português com licença aberta;
dicionário bíblico antigo em português com texto digital (o Dicionário da
Bíblia de John Davis traduzido por Carvalho Braga não apareceu em nenhuma
biblioteca digital e a situação da tradução é desconhecida); comentário
clássico completo em português em domínio público; obras religiosas
aproveitáveis no portal Domínio Público além de Vieira (não consegui consultar
o portal diretamente).

## Em inglês e línguas originais

| # | Obra | Autor e data | Tipo | O que acrescenta | Situação legal | Onde obter e formato | Esforço |
|---|---|---|---|---|---|---|---|
| 1 | Strong hebraico (corrigido) + índice BDB/Strong/TWOT | James Strong 1890; Open Scriptures | léxico | Substitui o Strong criptografado; liga Strong a BDB | Arquivos CC BY 4.0; texto de Strong e BDB em domínio público **[V]** | https://github.com/openscriptures/HebrewLexicon — `HebrewStrong.xml`, `LexicalIndex.xml` **[V]**; poucos MB **[I]** | Baixo (XML com esquema) |
| 2 | Strong grego | James Strong 1890; Ulrik Sandborg-Petersen | léxico | Idem, para o NT | CC0 **[V]** | https://github.com/morphgnt/strongs-dictionary-xml — `strongsgreek.xml` **[V]** | Baixo |
| 3 | Strong (módulos SWORD) | James Strong 1890 | léxico | Alternativa pronta | "Public Domain" **[V]** | CrossWire `StrongsGreek`, `StrongsHebrew` (1,5 MB) **[V]** | Médio (formato SWORD) |
| 4 | Brown-Driver-Briggs | Brown, Driver, Briggs 1906 | léxico hebraico | Léxico hebraico de referência | Arquivo CC BY 4.0, texto em domínio público; marcado como "em andamento" **[V]** | `BrownDriverBriggs.xml` no mesmo repositório **[V]**; glosas por Strong em CrossWire `BDBGlosses_Strongs` **[V]** | Baixo/médio |
| 5 | Abbott-Smith, Manual Greek Lexicon | G. Abbott-Smith 1922 | léxico grego | Léxico do NT mais moderno que Strong e Thayer | "Public Domain" **[V]** | CrossWire `AbbottSmith` e `AbbottSmithStrongs` (TEI na origem) **[V]**; também `Dodson` **[V]** (licença do Dodson não abri) | Médio |
| 6 | Keil & Delitzsch, Commentary on the OT | 1864–, 10 volumes | comentário | Melhor comentário clássico do AT a partir do hebraico | "Public Domain"; derivado de módulo de usuário do BibleWorks (W. Swanepoel) **[V]** | CrossWire `KD`, 11 MB **[V]**; e-Sword oferece pelo menu de download **[S]** | Médio (SWORD) ou baixo (e-Sword) |
| 7 | Calvin's Commentaries | João Calvino; trad. Calvin Translation Society, séc. XIX | comentário | Calvino em quase toda a Bíblia | "Public Domain"; origem CCEL **[V]** | CrossWire `CalvinCommentaries`, 20,6 MB **[V]**; `Institutes` **[V]** | Médio |
| 8 | Adam Clarke's Commentary | Clarke, 1810–26 | comentário | Bíblia inteira, linha wesleyana (contraponto a Gill) | "Public Domain" **[V]** | CrossWire `Clarke`, 8,5 MB **[V]** | Médio |
| 9 | Barnes' Notes (NT) | Albert Barnes, 1832– | comentário | NT versículo a versículo | "Public Domain"; o módulo é só NT **[V]** | CrossWire `Barnes`, 5,8 MB **[V]**; AT completo em módulos e-Sword **[S]** | Médio |
| 10 | Septuaginta de Brenton (inglês e grego) | L. C. L. Brenton 1851 | Bíblia | LXX com apócrifos, em inglês e grego alinháveis | Domínio público **[V]** | eBible `eng-Brenton`, `englxxup` (ortografia atualizada), `grcbrent` — USFM etc. **[V]** | Baixo; exige decisão de versificação |
| 11 | Vulgata Clementina | 1598 | Bíblia | Texto latino; base de Figueiredo e da tradição católica | Domínio público **[V]** | eBible `latVUC` **[V]**; CrossWire `VulgClementine`, `Vulgate`, `VulgGlossa` (Glossa ordinaria) **[V]** | Baixo |
| 12 | Douay-Rheims 1899 | — | Bíblia | Católica clássica em inglês, com deuterocanônicos | Domínio público **[V]** | eBible `engDRA` **[V]** | Baixo |
| 13 | Credos, confissões e catecismos | vários | livro | Westminster, Heidelberg, Dort, Belga, 1689, credos antigos, com referências bíblicas | Unlicense, **exceto oito textos** listados no README (Savoy, Consenso Helvético, Chicago e outros), que são protegidos **[V]** | https://github.com/NonlinearFruit/Creeds.json — JSON **[V]**; CrossWire `Westminster`, `BaptistConfession1689`, `Concord` **[V]** | Baixo |
| 14 | Josefo, obras completas | trad. William Whiston 1737 | livro | Contexto histórico do período do segundo templo | "Public Domain" **[V]** | CrossWire `Josephus` **[V]** | Médio |
| 15 | Pais da Igreja: ANF (10 v.), NPNF I (14 v.), NPNF II (14 v.) | ed. Schaff, Roberts, Donaldson, 1885–1900 | livro | Agostinho, Crisóstomo, Atanásio etc. | Obra em domínio público nos EUA **[I]**; a **edição ThML é do CCEL**, que permite uso pessoal, educacional e sem fins lucrativos e pede permissão para republicar **[V]** | https://www.ccel.org/fathers.html — ThML (XML) **[V]**; centenas de MB **[I]** | Médio/alto; usuário baixa |
| 16 | Sermões de Spurgeon (63 volumes) | C. H. Spurgeon | sermões | Complementa o Treasury of David | Obra em domínio público **[I]**; o site permite usar sem cobrar, sem alterar e com crédito **[V]** | https://www.spurgeongems.org/ — PDF **[V]** | Alto (PDF) |
| 17 | Lightfoot, Commentary from the Talmud and Hebraica | John Lightfoot (1602–75) | comentário | Pano de fundo judaico do NT | "Public Domain" **[V]** | CrossWire `Lightfoot`, 0,7 MB **[V]** | Médio |
| 18 | Outros comentários SWORD que ele não tem | Lutero (seleção), Catena Aurea, notas de Genebra, Burkitt, People's NT, Family Bible Notes, Abbott, Fourfold Gospel | comentário | Variedade de tradições | Não abri a página de cada um; os que abri do mesmo repositório são "Public Domain" **[I]** | CrossWire `Luther`, `Catena`, `Geneva`, `Burkitt`, `PNT`, `Family`, `Abbott`, `TFG` **[V]** (existência) | Médio |
| 19 | Clássicos devocionais e teológicos | Owen, Edwards, Ryle, Tomás de Aquino (Summa), Tomás de Kempis, Chesterton | livro | Leitura teológica | Idem **[I]** | CrossWire `JOMortSin`, `JEAffections`, `JCRHoliness`, `Summa`, `Imitation` e outros **[V]** (existência) | Médio |
| 20 | SBL Greek New Testament | SBL / Logos 2010 | Bíblia (grego) | Texto crítico para comparar com o TR | CC BY 4.0 **[V]** | https://sblgnt.com/ ; CrossWire `SBLGNT`, `MorphGNT`, `SBLGNTApp` **[V]** | Baixo/médio |
| 21 | Outros textos gregos e hebraicos | Bizantino 2013, Nestle 1904, Tischendorf, Tregelles, Códice de Alepo, Pentateuco Samaritano | Bíblia (originais) | Comparação de texto-base (ver item 9 do PESQUISA-FEATURES) | eBible lista Bizantino, Tischendorf, TR e WLC como domínio público **[V]**; demais não conferi | eBible e CrossWire (`Byz`, `Nestle1904`, `Tisch`, `TNT`, `Aleppo`, `SP`) **[V]** (existência) | Baixo/médio |
| 22 | Sefaria (Tanakh, Targum, Mishná, Talmud, Rashi, JPS 1917) | vários | Bíblia, comentário | Comentário judaico e traduções | **Licença varia por texto** (ver `LICENSE.md` e os metadados de cada versão); não conferi quais são livres | https://github.com/Sefaria/Sefaria-Export — JSON e texto em bucket público, ~26 GB no total; índice `books.json` **[V]** | Médio; baixar só categorias escolhidas |
| 23 | Thayer's Greek-English Lexicon | J. H. Thayer 1889 | léxico | Léxico clássico do NT | Domínio público nos EUA **[I]**; **não achei** fonte primária estruturada com licença clara; há módulo e-Sword **[S]** | e-Sword (menu de download) **[S]**; digitalização no Internet Archive **[S]** | Baixo via e-Sword; alto se só digitalização |
| 24 | Pulpit Commentary, Expositor's Bible, Lange, Alford, Cambridge Bible, Wesley Notes | séc. XVIII–XIX | comentário | As lacunas restantes da lista | Obras em domínio público nos EUA **[I]**; só achei módulos de terceiros (BibleSupport e blogs) e digitalizações **[S]**; nenhum no repositório principal do CrossWire **[V]** | Módulos e-Sword de terceiros **[S]**; Internet Archive **[S]** | Baixo se o usuário importar o módulo; procedência do módulo é por conta dele |

## As dez melhores, em detalhe

### 1. Notas de estudo da Tyndale em português (Aquifer Open Study Notes)

É o item de maior valor: notas de estudo modernas, por versículo, em
português, com licença que permite redistribuir. O repositório declara CC
BY-SA 4.0 e tem pasta `por` com subpastas `json`, `md`, `docx` e `pdf` e um
`metadata.json` **[V]**. Entraria como comentário: cada artigo JSON traz a
referência bíblica a que se aplica; o importador precisaria de um leitor novo
("aquifer") que gere linhas na mesma tabela de comentários, com `modules`
registrando repositório, idioma e versão. Riscos: não confirmei quantos livros
estão cobertos em português nem se a tradução é revisada por pessoas ou
automática — abrir o `metadata.json` antes de planejar; CC BY-SA exige crédito
à Tyndale e à Mission Mutual e a mesma licença em derivados.

### 2. Dicionário bíblico da Tyndale em português (Aquifer Open Bible Dictionary)

Mesmo formato, mesma licença **[V]**. Resolve a maior lacuna depois dos
comentários: um dicionário bíblico de verdade em português. Entra como
dicionário (verbete → texto). Ganho indireto: os títulos em português dos
verbetes ajudam a "página de tópico" (item 8 do PESQUISA-FEATURES) a casar
"Arca da Aliança" com "Ark of the Covenant", porque o mesmo artigo existe em
`eng` e `por`. Mesmos riscos do item 1.

### 3. Notas de estudo da Biblica em português

Terceiro recurso do Aquifer com `por` e CC BY-SA 4.0 **[V]**. Custa quase nada
depois do leitor do item 1. Dá um segundo ponto de vista em português para o
painel do versículo.

### 4. translationNotes, translationWords e translationQuestions em pt-br

Publicados no catálogo do Door43, releases de 2022, CC BY-SA 4.0 **[V]**. As
notas explicam figuras de linguagem, ambiguidades e termos difíceis versículo
a versículo; vi pastas dos 27 livros do NT **[V]** (não confirmei AT). As
"palavras" são um dicionário de termos-chave e nomes. Formato: Markdown em
pastas `livro/capítulo/versículo.md`, com `manifest.yaml`. Entrada no
importador: notas como comentário, palavras como dicionário, perguntas como
comentário por capítulo. Riscos: o catálogo marca erro de validação em `tn` e
`tq`; as notas foram escritas para tradutores, não para leitura devocional.

### 5. Bíblias livres em português (Bíblia Livre, Almeida Recebida, Bíblia Portuguesa Mundial, Nova Bíblia Viva Open)

Hoje toda Bíblia em português do usuário é protegida e não pode acompanhar um
aplicativo público. Estas quatro podem: CC BY 4.0, domínio público, domínio
público e CC BY-SA 4.0 **[V]**. O eBible.org entrega cada uma em USFM, USFX e
VPL (uma linha por versículo, com SQL), além de módulo SWORD **[V]**; VPL é o
caminho mais curto para o importador. A Bíblia Portuguesa Mundial traz os
deuterocanônicos, mas é rascunho, sem tradutores nem base declarados **[V]**:
rotular como tal. A Bíblia Livre pede citação como "BLIVRE" e a data da
versão.

### 6. Strong hebraico e grego legíveis

Fecha a lacuna do Strong criptografado sem tocar no módulo protegido. Hebraico:
`HebrewStrong.xml` do Open Scriptures, CC BY 4.0, com correções **[V]**. Grego:
`strongsgreek.xml`, CC0 **[V]**. Ambos são XML com uma entrada por número;
entram como dicionário com chave `H0001`/`G0001`, que é exatamente a chave que
as Bíblias com Strong já usam. Isso também desbloqueia a tarefa T20 (Strong
clicável) e serve de base para o "léxico breve em português" já proposto.
Risco baixo: só atribuição ao Open Scriptures.

### 7. Brown-Driver-Briggs e Abbott-Smith

BDB em XML no mesmo repositório do item 6, ligado ao Strong por
`LexicalIndex.xml` **[V]**; o README avisa que está em andamento. Abbott-Smith
(1922) existe como módulo SWORD em domínio público, com versão indexada por
Strong **[V]**, e a origem é um projeto TEI. Para o grego, isso dá um léxico
melhor que Strong enquanto não há fonte limpa do Thayer.

### 8. Keil & Delitzsch, Calvino, Clarke e Barnes

São as quatro lacunas de comentário mais citadas e as quatro têm módulo SWORD
"Public Domain" no CrossWire **[V]** (Barnes só NT). Dois caminhos: (a) o
usuário baixa pelo próprio e-Sword e o importador atual lê — esforço baixo,
mas não conferi o catálogo interno do e-Sword **[S]**; (b) o projeto ganha um
leitor de módulos SWORD (zCom/zLD/zText), o que abre de uma vez todo o
repositório do CrossWire — esforço médio, só biblioteca padrão (zlib).
Riscos: o módulo KD deriva de um módulo de usuário do BibleWorks; o de Calvino
deriva do CCEL, que reivindica direitos sobre suas edições.

### 9. Septuaginta de Brenton e Vulgata Clementina

Ambas em domínio público no eBible, em USFM **[V]**. A LXX em inglês e grego
permite ver como o NT cita o AT; a Vulgata dá o texto por trás de Figueiredo.
Risco técnico, não legal: versificação e livros fora do cânon de 66 (decisão
D005) — depende do item 10 do PESQUISA-FEATURES (TVTMS).

### 10. Credos e confissões em JSON, Josefo e os Pais

Creeds.json traz 43 documentos estruturados com referências bíblicas, sob
Unlicense, menos oito textos protegidos que o README lista **[V]** e que devem
ser filtrados. Josefo (Whiston) está no CrossWire como domínio público
**[V]**. Os Pais (ANF/NPNF) estão completos em ThML no CCEL **[V]**, mas aí
vale a regra "o usuário baixa": o CCEL só autoriza uso pessoal, educacional e
sem fins lucrativos **[V]**. Em português, a Confissão de Westminster e os
catecismos circulam em traduções de editoras; não achei tradução antiga com
texto digital livre.

## Regras práticas de direito autoral

Não é aconselhamento jurídico; são leituras da lei e das páginas de licença.

- **Brasil (Lei 9.610/98) [V]:** os direitos patrimoniais duram 70 anos
  contados de 1º de janeiro do ano seguinte à morte do autor (art. 41); obra
  anônima, 70 anos da publicação (art. 43). Em 2026 estão em domínio público
  os autores mortos até 1955. Obras que já tinham caído em domínio público
  pela lei anterior não voltam a ser protegidas (art. 112).
- **Tradução é obra protegida** (art. 7º, XI) e quem traduz obra em domínio
  público tem direitos sobre a sua tradução (art. 14) **[V]**. Matthew Henry
  morreu em 1714, mas a tradução brasileira é de editora atual. Verifique
  sempre o **tradutor** e o **revisor**.
- **Obra coletiva antiga:** conta o último coautor a morrer. É o que torna a
  Tradução Brasileira de 1917 incerta **[V]** (discussão no Wikisource);
  lembro, sem ter confirmado, que um dos membros da comissão teria vivido até
  a década de 1970 **[I]**.
- **EUA:** em 2026, o que foi publicado antes de 1931 está em domínio público
  lá (regra citada pelo Wikisource **[V]**). Quase toda a lista em inglês se
  apoia nisso. Isso não decide a situação no Brasil.
- **Atualização ortográfica** de texto antigo provavelmente não cria direito
  novo **[I]**; **revisão de linguagem** cria (ARC, ARA, ACF são revisões
  protegidas de um texto em domínio público).
- **Edição digital:** digitar ou marcar um texto em domínio público não gera,
  em regra, direito de autor sobre o texto **[I]**, mas introduções, notas,
  marcação e bancos de dados podem ter proteção, e os termos de uso do site
  valem como contrato. CCEL: uso pessoal, educacional e sem fins lucrativos;
  republicar exige permissão **[V]**. StudyLight: a página de direitos recusou
  meu acesso; não confirmado.
- **Redistribuir junto com o aplicativo:** só o que for domínio público
  declarado, CC0, CC BY ou CC BY-SA, com tela de créditos. Para CC BY-SA,
  manter cada fonte como pacote separado, com sua licença, em vez de fundir
  numa base única distribuída.
- **Deixar o usuário baixar:** serve para o que tem condição de uso não
  comercial ou termos de site (CCEL, Spurgeon Gems, Kingcomments, módulos de
  terceiros). O aplicativo fornece o importador e o endereço; não hospeda.
- Regra do AGENTS.md continua valendo: conferir a licença na página de origem
  antes de usar e registrar em DECISOES.

## Descartado ou arriscado

- **Bíblias de sociedades bíblicas e editoras** (ARA, ARC, NAA, NTLH da SBB;
  ACF da Trinitariana; NVI da Biblica/Vida; Almeida Revisada de 1967). O
  theWord oferece ACF, AR 1967, RA e RC sem nenhuma nota de licença **[V]**:
  gratuito para baixar não é livre para redistribuir.
- **Tradução Brasileira, edição de 2010 da SBB:** texto com ortografia
  atualizada, vendido **[S]**. Usar no máximo a de 1917 e só como download do
  usuário.
- **Strong em português** (Léxico de Strong da SBB): produto comercial **[S]**.
- **Clássicos em tradução moderna:** Matthew Henry, Calvino (Institutas e
  comentários), Agostinho, Lutero, Bunyan, Spurgeon, Ryle em português são de
  editoras atuais. Os originais em inglês são livres; as traduções não **[I]**.
- **Projeto Spurgeon** (sermões em português): CC BY-NC-ND 3.0 Brasil **[V]**
  — pode ler e copiar sem fins comerciais, não pode adaptar; importar para uso
  pessoal é defensável, redistribuir convertido não.
- **Kingcomments em português:** distribuição não comercial, autor reserva
  direitos **[V]**.
- **Bíblia LTT e Palavra Viva** (no theWord): autores vivos, sem licença
  declarada **[V]**.
- **Versão Fácil de Ler e NTBT** no eBible: marcadas como não redistribuíveis
  **[V]**.
- **NETnotesfree** (CrossWire): subconjunto limitado de notas protegidas **[S]**.
- **Sefaria em bloco:** muitas traduções modernas têm licença não comercial ou
  restrita **[I]**; filtrar por versão.
- **Creeds.json inteiro:** oito textos protegidos **[V]**.
- **LXX de Rahlfs** (módulo `LXX` do CrossWire): condições próprias que não
  conferi; preferir Brenton/eBible **[I]**.
- **Módulos de terceiros para e-Sword/theWord** (BibleSupport, blogs): a obra
  costuma ser livre, mas a procedência do arquivo e eventuais acréscimos não
  são verificáveis **[S]**. O usuário pode importar os seus; o projeto não
  deve hospedar.
- **Módulos criptografados** (Guzik, Utley, Bridgeway, Mickelson): continuam
  fora (D008). Para o Strong há substituto aberto; para os demais não procurei
  cópia aberta, porque são obras de autores recentes.

## Fontes consultadas

Abertas e lidas (base das marcas **[V]**):

- https://github.com/BibleAquifer
- https://github.com/BibleAquifer/AquiferOpenStudyNotes (e `/tree/main/por`)
- https://github.com/BibleAquifer/AquiferOpenBibleDictionary
- https://github.com/BibleAquifer/BiblicaStudyNotes
- https://git.door43.org/api/v1/catalog/search?lang=pt-br&stage=prod
- https://git.door43.org/Door43-Catalog/pt-br_tn
- https://git.door43.org/Door43-Catalog/pt-br_tw (e `LICENSE.md`)
- https://ebible.org/Scriptures/translations.csv
- https://ebible.org/Scriptures/copyright.php
- https://ebible.org/find/details.php?id=porbr2018
- https://ebible.org/porbrbsl/copyright.htm
- https://ebible.org/poronbv/copyright.htm
- https://ebible.org/portft/copyright.htm
- https://ebible.org/porblt/copyright.htm
- https://www.almeidarecebida.org/
- https://biblianva.com.br/
- https://pt.wikisource.org/wiki/Bíblia
- https://pt.wikisource.org/wiki/Tradução_Brasileira_da_Bíblia
- https://pt.wikisource.org/wiki/Discussão:Tradução_Brasileira_da_Bíblia_Sagrada
- https://pt.wikisource.org/wiki/Autor:Antônio_Vieira
- https://www.crosswire.org/sword/modules/ModDisp.jsp?modType=Bibles (e `Commentaries`, `Dictionaries`, `Books`)
- https://www.crosswire.org/sword/modules/ModInfo.jsp?modName=… para
  PorAlmeida1911, PorKingComments, PorNVA, StrongsGreek, StrongsHebrew,
  AbbottSmithStrongs, CalvinCommentaries, Barnes, Clarke, KD, Josephus,
  Lightfoot
- https://github.com/openscriptures/HebrewLexicon
- https://github.com/openscriptures/strongs (sem licença visível)
- https://github.com/morphgnt/strongs-dictionary-xml
- https://github.com/NonlinearFruit/Creeds.json
- https://github.com/Sefaria/Sefaria-Export
- https://sblgnt.com/license/
- https://www.stepbible.org/version.jsp?version=KD
- https://www.ccel.org/about/copyright.html
- https://www.ccel.org/fathers.html
- https://www.spurgeongems.org/about-us/
- https://www.projetospurgeon.com.br/
- https://www.theword.net/index.php?downloads.modules&l=portuguese
- https://www.e-sword.net/downloads.html
- https://www.planalto.gov.br/ccivil_03/leis/l9610.htm

Não abriram ou só vistas em resumo de busca (base das marcas **[S]**):

- https://www.gutenberg.org/ebooks/62383 (Almeida; erro 503 nas duas tentativas)
- https://www.studylight.org/site-resources/copyright-statement.html (erro 403)
- https://www.sefaria.org/licensing (erro 404)
- https://dl.atla.com/concern/works/7h149s652 (NT de Figueiredo, 1803)
- https://media.olivetree.com/store/product/24932 (Tradução Brasileira, SBB)
- https://biblia.com/books/bb-sbb-strongs/ (Léxico de Strong, SBB)
- https://biblehub.com/commentaries/expositors/ e blogs sobre módulos e-Sword
  de terceiros (Pulpit, Lange, Alford, Expositor's)
- https://archive.org/ (digitalizações de Keil & Delitzsch e Thayer)

Não consegui confirmar: cobertura e qualidade do português nos recursos do
Aquifer; se as translationNotes pt-br cobrem o AT; a situação da Tradução
Brasileira no Brasil; fonte estruturada e limpa do Thayer; quais módulos o
e-Sword oferece hoje no menu de download; licença de cada módulo SWORD cuja
página não abri; conteúdo religioso do portal Domínio Público e das
bibliotecas digitais (BN, BNP, Brasiliana), que não consultei diretamente.
