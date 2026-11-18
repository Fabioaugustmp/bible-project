# Pesquisa de mercado: o que faz uma plataforma gerar resultado no estudo

Pesquisa feita em 2026-11-17. Complementa a
[PESQUISA-FEATURES.md](PESQUISA-FEATURES.md) (o que os programas oferecem e
que dados abertos existem) e a [PROPOSTA-DESIGN.md](PROPOSTA-DESIGN.md)
(guardar, organizar e sair). Aqui a pergunta é outra: **o que, segundo a
evidência, faz uma pessoa lembrar e entender mais**, e quem já oferece isso.
Não altera nenhuma decisão nem tarefa; as propostas ainda precisam passar
pelo backlog.

**Marcas usadas em cada afirmação:**

- **[V]** verificado por mim na página primária (artigo, página do produto,
  documentação oficial);
- **[S]** visto apenas em resumo de busca ou em fonte secundária (resenha,
  fórum, notícia), conferir antes de depender disso;
- **[I]** inferência ou proposta minha, sem fonte.

Esforços são estimativas **[I]**, nada foi medido. Não instalei nem testei
nenhum produto: o que se diz sobre eles vem das páginas e resenhas citadas.

---

## 1. Resumo

Um leitor bíblico ajuda a **encontrar** e a **ler**; o que a pesquisa sobre
aprendizagem mostra que gera resultado é **recuperar da memória, espaçar no
tempo, explicar com as próprias palavras e receber retorno sobre o que se
lembra** [V: Roediger e Karpicke 2006; Cepeda et al. 2006; Bisra et al. 2018;
Wisniewski et al. 2020]. Reler e destacar, que são o centro da maioria dos
aplicativos bíblicos, aparecem como técnicas de baixa utilidade [V: Dunlosky
et al. 2013, via resumo da APS/ScienceDaily]. No mercado bíblico, a revisão
espaçada existe só para **decorar o texto de versículos** (Remember Me, Bible
Memory App, ferramenta de memorização do Logos) [S]; nenhum produto pesquisado
transforma **as notas, conclusões e sermões do próprio usuário** em perguntas
de revisão, o que Readwise e RemNote já fazem fora do nicho [V]. Esse ciclo
fechado (estudar → escrever → revisar → ver o que ficou), local e com
procedência, é a lacuna mais clara para este projeto [I].

---

## 2. Tabela de elementos

Esforço refere-se a este projeto, considerando que T40 (`user.db` com notas)
e T42 (exportação) ainda estão pendentes [V: BACKLOG.md]. "Baixo" ≈ dias,
"Médio" ≈ uma a duas semanas, "Alto" ≈ mais que isso [I].

| # | Recurso | Por que gera resultado no estudo | Quem já oferece e como | O que falta no mercado | Esforço aqui |
|---|---|---|---|---|---|
| 1 | **Revisão ativa das próprias notas** (cartões de pergunta e resposta criados a partir de uma nota, de um destaque ou de uma conclusão de estudo) | Testar-se retém mais que reestudar após dias; o ganho só aparece com atraso [V: Roediger e Karpicke 2006] | Readwise "Mastery": cartões P/R a partir de destaques, reapresentados por um modelo de meia-vida [V]; RemNote: cartões escritos dentro das notas, editar a nota atualiza o cartão [V]; Logseq: bloco marcado `#card` [S] | Nenhum programa bíblico pesquisado faz isso com notas de estudo; só com o texto do versículo [S] | Médio, depois de T40 [I] |
| 2 | **Agendador de repetição espaçada** | Espaçar supera concentrar; o intervalo ideal cresce com o tempo que se quer lembrar [V: Cepeda et al. 2006] | Anki com FSRS ou SM-2, retenção desejada configurável (padrão 90%) [V]; RemNote com SM-2 e FSRS [V]; Remember Me e Bible Memory App para versículos, algoritmo não documentado [V/S] | Programas bíblicos de estudo profundo não têm agendador para material de estudo; o do Logos sorteia versículos de uma lista e usuários pedem um modo "à la Anki" há anos [S: fórum Logos] | Baixo para SM-2 ou Leitner; Médio para FSRS em Python puro (D003) [I] |
| 3 | **Memorização do texto** (primeiras letras, lacunas, digitação) | Mesma base de 1 e 2; útil para pregar sem ler [I] | Remember Me: cartões, jogos de lacuna e digitação, áudio, gratuito [V]; Bible Memory App: revisão espaçada, versão PRO [S]; Logos: ferramenta "Memorization" sobre listas de passagens, quiz só em ordem aleatória [S] | Pouco: o nicho está atendido; falta só integração com as versões que o usuário já tem offline [I] | Baixo [I] |
| 4 | **Notas ancoradas no versículo, com "tudo o que já escrevi sobre este versículo"** | Pré-condição de 1, 5 e 6; sem lugar para guardar não há o que revisar [I] | Olive Tree: notas pesquisáveis, destaques com etiquetas, offline e sincronizadas [V]; Bíblia Raízes (.com.br): notas por versículo e destaques, sincronizados por conta [V]; Obsidian: kit gratuito com a Bíblia em Markdown e backlinks [V] | No Obsidian, usuários reclamam de ter de garimpar os backlinks de capítulos populares [V: fórum]; nos programas bíblicos, a nota fica presa ao versículo e não aparece em sermões ou estudos que citam o mesmo texto [I] | Médio (é T40) [I] |
| 5 | **Escrita guiada por perguntas** (observação, interpretação, aplicação; "explique com suas palavras por que…") | Autoexplicação induzida por perguntas: g = 0,55 em 69 efeitos [V: Bisra et al. 2018]; escrever para aprender tem efeito pequeno e positivo, maior com perguntas metacognitivas [V: Bangert-Drowns et al. 2004] | Logos Workflows: roteiros em etapas com perguntas para refletir, ex. "Passage Exegesis", só no desktop e na web, conforme o plano [S]; BibleProject: plano com vídeos, passagens e pergunta de reflexão [S] | Roteiros que gravam as respostas como notas consultáveis e depois as **revisam** (ligação com 1) não foram encontrados [I] | Baixo a médio [I] |
| 6 | **Do estudo ao sermão ou à aula, com procedência** | Preparar para ensinar e ensinar de fato melhoram a compreensão posterior [S: Fiorella e Mayer 2013 e 2014, d = 0,56 para ensinar] | Logos Sermon Builder: manuscrito, slides, folhetos e perguntas de discussão juntos; Sermon Manager para planejar o ano; assistente de IA nos planos maiores [S]; Sermonary: construtor em blocos, assistente de IA [S]; Bíblia Raízes: editor em blocos para esboços com passagens e comentários na margem [V] | Ferramentas offline que mantêm a obra e a chave de origem de cada citação no esboço [I]; a maioria dos geradores com IA escreve o sermão pelo pregador [S] | Médio (estende T42) [I] |
| 7 | **Registro do que foi pregado ou ensinado** (data, passagem, local, notas) | Permite revisar o próprio ensino e evita repetir sem querer [I] | Logos Sermon Manager organiza documentos de sermão e permite esboçar o calendário do ano [S] | Ligação do registro com o versículo no leitor ("preguei Rm 8:28 em 2025-03-02") não foi encontrada [I] | Baixo, depois de T40 [I] |
| 8 | **Retorno sobre o que se lembra** (taxa de acerto por livro, tema ou estudo; cartões vencidos; o que caiu) | Retorno com informação sobre a tarefa tem efeito maior (d = 0,99) que só certo/errado (0,46) ou recompensa (0,24) [V: Wisniewski et al. 2020]; quem só relê fica **mais confiante** e lembra **menos** [V: Roediger e Karpicke 2006] | Readwise mostra a probabilidade de lembrança de cada cartão [V]; aplicativos bíblicos mostram progresso de leitura e sequências [S] | Nenhum aplicativo bíblico pesquisado mostra retenção, só quantidade lida [S] | Médio [I] |
| 9 | **Constância** (plano de leitura, "continuar de onde parei") | A pesquisa do Center for Bible Engagement associa ler, refletir e responder **4 ou mais dias por semana** a vários desfechos de vida; é correlacional, autodeclarada e o limiar foi escolhido nos próprios dados [V: página da pesquisa, com essas ressalvas] | YouVersion: milhares de planos, planos com amigos [S]; mais de 3 milhões de inscrições em planos anuais no Ano-Novo de 2025, dado da empresa [S]; Olive Tree, Blue Letter Bible: planos de leitura [V] | Bem atendido; falta só nos programas de estudo profundo [I] | Baixo (já previsto como B06/item 6 da PESQUISA-FEATURES) [I] |
| 10 | **Comparar fontes lado a lado** | Explicar diferenças entre comentaristas é autoexplicação [I] | Bible Hub e Blue Letter Bible por versículo [S]; Olive Tree "Resource Guide" puxa trechos da biblioteca sobre a passagem aberta [V] | Já tratado na PROPOSTA-DESIGN (jornada do pastor, item 3) [V] | Já previsto [V] |
| 11 | **Pergunta com resposta citada (IA)** | Pode acelerar a busca; não há evidência encontrada de ganho de aprendizagem [I] | Logos Study Assistant (Logos 46, nov. 2025): respostas com citações da biblioteca, planos Premium em diante [S]; Bíblia Raízes "Oliver": respostas com referências e aviso de que pode errar [V] | Usuário do Logos relata respostas "superficiais" [S: fórum] | Já previsto como opcional tardio (item 19) [V] |
| 12 | **Cursos estruturados** | Ensino sequenciado com prática [I] | BibleProject: aulas gratuitas, começando por Gênesis, com notas e progresso salvos [V]; Blue Letter Bible Institute: cursos gratuitos [V] | Conteúdo licenciado; fora do escopo de um leitor local [I] | Não recomendado [I] |

---

## 3. Os cinco elementos mais promissores, com evidência

**1. Revisão ativa (recuperar em vez de reler).** No experimento de Roediger
e Karpicke (2006), estudantes que leram um texto e fizeram um teste de
lembrança livre, sem retorno, lembraram 56% das ideias uma semana depois,
contra 42% de quem releu o texto; no segundo experimento, quem fez três
testes lembrou 61% após uma semana, contra 40% de quem leu quatro vezes,
embora este último grupo tenha lido o texto 14,2 vezes e o primeiro 3,4 vezes
[V]. No teste após 5 minutos o padrão se invertia (reler ganhava), e o grupo
que só releu era o **mais confiante** de que lembraria [V]. Uma meta-análise
posterior conclui que testes práticos superam reestudar e as demais condições
comparadas [V: resumo no repositório da WSU]; o tamanho do efeito (g ≈ 0,70)
e a contagem de 118 artigos e 272 efeitos só os vi em fontes secundárias
[S]. Uma revisão de estudos feitos em salas de aula reais relata 57% dos
efeitos médios ou grandes [S: Agarwal, Nunes e Blunt 2021]. Para o projeto,
isso significa que o estudo só "fica" se o aplicativo pedir de volta o que o
usuário concluiu, não só se mostrar de novo [I].
Fontes: Roediger e Karpicke 2006 (PDF), Adesope et al. 2017, Agarwal et al.
2021.

**2. Espaçamento com agendador.** A meta-análise de Cepeda et al. (2006)
reuniu 839 avaliações em 317 experimentos de 184 artigos e concluiu que o
intervalo entre sessões e o tempo de retenção atuam juntos: quanto mais tempo
se quer lembrar, maior deve ser o intervalo que produz a melhor retenção [V].
A revisão de Dunlosky et al. (2013) deu "alta utilidade" só a duas técnicas
entre dez, testes práticos e prática distribuída, e "baixa utilidade" a
reler, destacar e resumir [V: comunicado divulgado no ScienceDaily; a página
da APS recusou o acesso]. No lado das ferramentas, o manual do Anki descreve
o FSRS como alternativa ao SM-2 legado, com "retenção desejada" padrão de 90%
e alerta que a carga sobe muito perto de 100% [V]; o benchmark aberto de
algoritmos usa cerca de 350 milhões de revisões de quase 10 mil coleções
[V], mas não encontrei na página principal uma comparação direta com SM-2, e
os percentuais de "revisões a menos" que circulam (15% a 50%) vêm de blogs e
de páginas de concorrentes [S].
Fontes: Cepeda et al. 2006 (PDF), ScienceDaily 2013, manual do Anki,
srs-benchmark.

**3. Escrever e explicar com as próprias palavras, guiado por perguntas.** A
meta-análise de Bisra et al. (2018) encontrou g = 0,55 para perguntas que
induzem autoexplicação, em 69 efeitos de 64 relatórios, e recomenda pesquisar
perguntas geradas por computador [V]. Segundo o resumo da BPS, autoexplicação
superou explicação dada pelo professor, e formatos de múltipla escolha foram
os menos eficazes [V: BPS Research Digest]. A meta-análise de Bangert-Drowns,
Hurley e Wilkinson (2004) sobre 48 programas de "escrever para aprender"
encontrou efeito pequeno e positivo, maior com perguntas metacognitivas e
tratamentos mais longos [V: resumo no SUNY]; o valor numérico (≈ 0,17 a 0,20)
só aparece em fontes secundárias [S]. O efeito de geração (produzir a
resposta em vez de lê-la) tem média de cerca de 0,40 em 86 estudos [S:
Bertsch et al. 2007]. Para o projeto, roteiros curtos de perguntas ao lado do
texto, cujas respostas viram notas, aproveitam isso sem IA [I].
Fontes: Bisra et al. 2018 (PDF), BPS Research Digest, Bangert-Drowns et al.
2004, Bertsch et al. 2007.

**4. Retorno sobre o que se lembra.** A reanálise de Wisniewski, Zierer e
Hattie (2020), com 435 estudos, 994 efeitos e mais de 61 mil participantes,
estimou efeito médio d = 0,48 para retorno (feedback), com grande
heterogeneidade; retorno rico em informação sobre a tarefa e o processo teve
d = 0,99, retorno corretivo d = 0,46 e recompensa ou punição d = 0,24 [V]. A
meta-análise mais antiga de Kluger e DeNisi (1996) é citada por registrar
cerca de um terço de efeitos negativos [S]. Combinado com o achado de que
quem relê superestima o que lembra [V: Roediger e Karpicke 2006], o retorno
útil num aplicativo de estudo é mostrar **o que foi esquecido e onde está a
fonte para reestudar**, não medalhas ou sequências [I]. Readwise já mostra a
meia-vida e a probabilidade de lembrança de cada cartão [V]; nenhum
aplicativo bíblico pesquisado faz algo parecido [S].
Fontes: Wisniewski et al. 2020, documentação do Readwise.

**5. Do estudo ao ensino (sermão ou aula) com procedência.** Ensinar de fato
(explicar a outros) melhorou a compreensão num teste adiado (d = 0,56), e
preparar-se para ensinar teve efeito principalmente de curto prazo [S:
Fiorella e Mayer 2014, via resumo; o artigo de 2013 não foi lido]. Logos
investe nisso: o Sermon Builder produz manuscrito, slides, folhetos e
perguntas de discussão ao mesmo tempo, e o Sermon Manager organiza os sermões
e o calendário [S: páginas da Logos inacessíveis (403), resumo de busca]. O
Bíblia Raízes (.com.br) tem editor em blocos para esboços de pregação, com
passagens e comentários na margem [V]. O que não encontrei é a ligação de
volta: o esboço pregado virar material de revisão e aparecer no versículo
dentro do leitor [I]. A PESQUISA-FEATURES descartou o montador de sermões
porque "nada no plano indica que o usuário prega" [V]; o pedido desta
pesquisa diz o contrário (uso para pregação), então esse descarte merece ser
revisto em DECISOES [I].
Fontes: Fiorella e Mayer 2013 e 2014, Logos Sermon Builder, Bíblia Raízes.

---

## 4. O que o mercado oferece e que não vale copiar

- **Destaque colorido como centro da experiência.** É o recurso mais visível
  de quase todos (Olive Tree, Bible Gateway, Bíblia Raízes) [V], mas destacar
  e reler estão entre as técnicas de baixa utilidade [V: Dunlosky 2013]. Uma
  meta-análise mais recente relata efeito do destaque feito pelo estudante na
  memória (≈ 0,36) e menor na compreensão (≈ 0,20) [S: Ponce, Mayer e Méndez
  2022, números não conferidos no artigo]. Manter o destaque como marcação
  barata, não como "estudo" [I].
- **Sequências de dias, versículo do dia, metas e medalhas.** São engajamento,
  não aprendizagem; recompensa é a forma de retorno com menor efeito (d =
  0,24) [V: Wisniewski 2020]. Não encontrei estudo confiável sobre o efeito de
  sequências na conclusão de planos [S]. Já descartado em IDEIAS [V:
  PESQUISA-FEATURES].
- **Feed social e planos com amigos** (YouVersion) [S]. Contraria "local e
  offline" e não há evidência encontrada de ganho de compreensão [I].
- **IA que escreve o sermão ou o estudo.** Remove justamente a geração e a
  autoexplicação, que são a parte que gera resultado [I, com base em Bisra
  2018 e Bertsch 2007]. Os produtos de sermão com IA anunciam pesquisa,
  ilustrações e reaproveitamento em clipes [S]. Se houver IA, que faça
  perguntas e aponte fontes, não que escreva a conclusão [I].
- **Chat com respostas genéricas.** Usuário do Logos relata respostas do Study
  Assistant "superficiais" a ponto de recorrer a IA genérica [S]. Já tratado
  na PESQUISA-FEATURES [V].
- **Conteúdo sem fonte declarada.** Uma página que usa o nome "Bíblia Raízes"
  (domínio .life) promete "5 camadas históricas" de cada palavra, PaRDeS e
  gematria, sem mostrar de onde vêm [V: a página não mostra fontes]. Fere o
  princípio de procedência do projeto [V: PROPOSTA-DESIGN, princípio 2].
- **Modelo de loja e assinatura com recursos presos a planos** (Logos
  Workflows e Study Assistant por nível de assinatura [S]; Bible Gateway Plus
  US$ 6,99/mês [V]). Não se aplica a um aplicativo pessoal sobre módulos que o
  usuário já tem [I].
- **Discussão "caneta contra teclado".** A vantagem da escrita à mão de
  Mueller e Oppenheimer (2014) não se replicou bem: no teste adiado o modo de
  anotar não fez diferença [V: resumo dos Learning Scientists sobre Morehead,
  Dunlosky e Rawson 2019]. Não vale construir nada em torno disso [I].

---

## 5. Lacunas que o projeto poderia ocupar

1. **Ciclo fechado com as próprias conclusões.** Nota ou trecho guardado →
   pergunta de revisão escrita pelo usuário (ou sugerida a partir da nota) →
   revisão espaçada → painel do que foi esquecido, com link para a fonte.
   *Justificativa:* é o elemento de maior evidência (seções 3.1 a 3.4) e não
   foi encontrado em nenhum programa bíblico; existe fora do nicho (Readwise,
   RemNote) [V], o que mostra que é viável e usado [I].
2. **Revisão do que foi pregado.** Cada sermão ou aula vira uma pequena série
   de perguntas ("qual o argumento de Rm 3:25?", "o que significa ἱλαστήριον
   segundo o Dodson?") e aparece no versículo quando ele é aberto de novo.
   *Justificativa:* junta o efeito de ensinar (3.5) ao de recuperar (3.1); o
   público inicial é um pregador; nenhum produto pesquisado liga sermão a
   revisão [I].
3. **Roteiros de estudo offline que gravam respostas.** Três ou quatro
   perguntas fixas por passagem (observar, interpretar, aplicar, explicar a
   alguém), respostas guardadas como notas ancoradas.
   *Justificativa:* autoexplicação com perguntas tem g = 0,55 [V]; o Logos
   oferece roteiros parecidos só em planos pagos e não no celular [S]; não
   exige IA, então respeita P4 [I].
4. **Procedência dentro das notas e do esboço.** Toda citação guardada leva
   obra e chave de origem (já é princípio 2 da PROPOSTA-DESIGN [V]), e a
   revisão mostra a fonte ao errar.
   *Justificativa:* o retorno mais eficaz é o que informa sobre a tarefa [V:
   Wisniewski 2020]; "errou, a resposta está em Gill, Rm 3:25" é exatamente
   isso [I].
5. **Tudo local.** Olive Tree funciona offline mas sincroniza pela nuvem [V];
   Bíblia Raízes sincroniza pela conta [V]; Remember Me não informa uso
   offline na página consultada [V]. Um caderno de estudo e revisão que não
   sai da máquina é raro [I].
6. **Português primeiro sobre acervo em inglês, também na revisão.** As
   perguntas e respostas ficam em português mesmo quando a fonte é inglesa,
   reaproveitando a ponte Strong já planejada [I; ver PESQUISA-FEATURES].

**Ordem sugerida [I]:** T40 (notas) → registro de sermões (item 7 da tabela)
→ cartões a partir de notas com agendador SM-2 ou Leitner → painel de
retenção → roteiros de perguntas → FSRS só se o SM-2 se mostrar ruim no uso.
Cada passo precisa entrar no backlog antes; o descarte do "montador de
sermões" na PESQUISA-FEATURES deve ser revisto com o usuário.

---

## 6. O que não pôde ser verificado

- **Bíblia Raízes:** existem dois sites com o nome (bibliaraizes.com.br e
  bibliaraizes.life) com propostas diferentes (o primeiro: leitor com
  traduções, interlinear, IA "Oliver", notas e editor de esboços, planos de
  R$ 97,90 e R$ 147,90 por ano [V]; o segundo: estudo de palavras em 8 abas,
  teste de 3 dias [V]). Não consegui confirmar se são o mesmo produto, nem
  quem os faz. Nenhum dos dois descreve revisão ou memorização [V].
- **Logos:** as páginas oficiais do Sermon Builder e dos Workflows
  redirecionam para o suporte, que recusou acesso (403); tudo sobre eles é
  [S]. A ferramenta de memorização do Logos só foi vista em fórum [S].
- **Accordance 14:** a página oficial recusou acesso (403); recursos citados
  (Dynamic Word Study, Custom Phrasing, Easy Answers) são [S]. Não achei
  recurso de revisão ou memorização.
- **YouVersion:** os números de 2025 vêm de comunicados da própria empresa
  reproduzidos pela imprensa [S]; o dado "40 dias de plano concluídos por
  segundo" não foi confirmado.
- **Faithlife Study Bible:** a página oficial confirma edição digital gratuita
  no Logos, mas não traz a contagem de notas ou infográficos [V]; as
  contagens (100, 120, 400 infográficos) divergem entre fontes [S].
- **Números de meta-análises não conferidos no artigo:** Adesope 2017 (g ≈
  0,70), Bangert-Drowns 2004 (≈ 0,17 a 0,20), Ponce 2022, Bertsch 2007,
  Fiorella e Mayer, Kluger e DeNisi, Agarwal 2021 [S]. Os de Roediger e
  Karpicke 2006, Cepeda 2006, Bisra 2018 e Wisniewski 2020 foram lidos no
  texto ou resumo original [V].
- **Pesquisa "Power of 4":** os números vêm da própria organização, sem
  estatísticas publicadas na página; é estudo observacional [V].
- Não encontrei estudo com usuários de software bíblico que meça
  aprendizagem; toda a evidência de resultado é da psicologia educacional
  geral, transposta por inferência [I].

---

## 7. Fontes

### Pesquisa sobre aprendizagem

- Roediger, H. L.; Karpicke, J. D. (2006). *Test-Enhanced Learning*.
  Psychological Science 17(3). PDF:
  <https://psychology.ecu.edu/wp-content/pv-uploads/sites/216/2019/03/Roediger-Karpicke-2006.pdf> [V]
- Cepeda, N. J. et al. (2006). *Distributed Practice in Verbal Recall Tasks*.
  Psychological Bulletin 132(3). PDF:
  <https://www.evullab.org/pdf/CepedaPashlerVulWixtedRohrer-PB-2006.pdf> [V]
- Dunlosky, J. et al. (2013), comunicado: *Which study strategies make the
  grade?* <https://www.sciencedaily.com/releases/2013/01/130110111734.htm> [V]
- Adesope, O. et al. (2017). *Rethinking the Use of Tests*. Review of
  Educational Research 87(3).
  <https://rex.libraries.wsu.edu/esploro/outputs/journalArticle/Rethinking-the-Use-of-Tests-A/99900601154801842> [V para o resumo; números S]
- Agarwal, P. K.; Nunes, L. D.; Blunt, J. R. (2021). *Retrieval Practice
  Consistently Benefits Student Learning*. <https://retrievalpractice.org/review> [S]
- Karpicke, J. D.; Butler, A. C.; Roediger, H. L. (2009). *Metacognitive
  strategies in student learning*. Memory 17.
  <https://pcllab.github.io/downloads/2009/2009_Karpicke_Butler_Roediger.pdf> [S]
- Bisra, K. et al. (2018). *Inducing Self-Explanation: a Meta-Analysis*.
  Educational Psychology Review 30.
  <https://www.Gwern.net/doc/psychology/spaced-repetition/2018-bisra.pdf> [V]
- BPS Research Digest sobre Bisra et al.:
  <https://www.bps.org.uk/research-digest/self-explanation-powerful-learning-technique-according-meta-analysis-64-studies> [V]
- Bangert-Drowns, R. L.; Hurley, M. M.; Wilkinson, B. (2004). *The effects of
  school-based writing-to-learn interventions*.
  <https://researchconnect.suny.edu/en/publications/the-effects-of-school-based-writing-to-learn-interventions-on-aca/> [V]
- Bertsch, S. et al. (2007). *The generation effect: a meta-analytic review*.
  <https://pubmed.ncbi.nlm.nih.gov/17645161/> [S]
- Wisniewski, B.; Zierer, K.; Hattie, J. (2020). *The Power of Feedback
  Revisited*. Frontiers in Psychology.
  <https://www.frontiersin.org/articles/10.3389/fpsyg.2019.03087/full> [V]
- Hattie, J.; Timperley, H. (2007). *The Power of Feedback*.
  <https://www.uky.edu/~gmswan3/575/Hattie_Timperly_2007.pdf> [S]
- Fiorella, L.; Mayer, R. E. (2013). *The relative benefits of learning by
  teaching and teaching expectancy*.
  <https://alexandria.ucsb.edu/lib/ark:/48907/f3ms3qvb> [S]
- Ponce, H. R.; Mayer, R. E.; Méndez, E. E. (2022). *Effects of
  learner-generated highlighting…* DOI 10.1007/s10648-021-09654-1.
  <https://www.epistemonikos.org/en/documents/1a0f73b2b5503dae7a1af529c5734a6fe7600dd6> [S]
- Morehead, K.; Dunlosky, J.; Rawson, K. (2019), resumo:
  <https://www.learningscientists.org/blog/2019/2/21-1> [V para o resumo]
- Bjork, E. L.; Bjork, R. A. (2011). *Making things hard on yourself, but in
  a good way*.
  <https://bjorklab.psych.ucla.edu/wp-content/uploads/sites/13/2016/04/EBjork_RBjork_2011.pdf> [S]
- Center for Bible Engagement, *The Evolution of Bible Engagement*:
  <https://www.backtothebible.org/post/the-evolution-of-bible-engagement-a-research-journey-2004-2023> [V]

### Ferramentas de repetição espaçada e notas

- Manual do Anki, opções do baralho (FSRS):
  <https://docs.ankiweb.net/deck-options.html> [V]
- srs-benchmark: <https://github.com/open-spaced-repetition/srs-benchmark> [V]
- Readwise, revisão de destaques e Mastery:
  <https://docs.readwise.io/readwise/docs/faqs/reviewing-highlights> [V]
- RemNote, repetição espaçada:
  <https://www.remnote.com/feature/spaced-repetition> [V]
- Kit de estudo bíblico no Obsidian:
  <https://forum.obsidian.md/t/bible-study-in-obsidian-kit-including-the-bible-in-markdown/12503> [V]
- Remember Me, guia:
  <https://doc.remem.me/docs/guides/read-the-bible-and-remember/> [V]

### Produtos bíblicos

- Bíblia Raízes: <https://bibliaraizes.com.br/> [V] e
  <https://bibliaraizes.life/> [V]
- Olive Tree: <https://www.olivetree.com/> [V]
- Blue Letter Bible: <https://www.blueletterbible.org/> [V]
- Bible Gateway Plus: <https://www.biblegateway.com/plus/> [V]
- Faithlife Study Bible:
  <https://www.logos.com/product/36338/faithlife-study-bible> [V]
- BibleProject (App Store):
  <https://apps.apple.com/us/app/bibleproject/id1523687027> [V]
- Logos Sermon Builder (suporte, acesso recusado):
  <https://support.logos.com/hc/en-us/articles/360016747391-Sermon-Builder> [S]
- Logos Workflows (suporte, acesso recusado):
  <https://support.logos.com/hc/en-us/articles/360018035692> [S]
- Logos, novidades de novembro de 2025 (Study Assistant):
  <https://www.logos.com/grow/release-november-2025/> [S]
- Fórum Logos sobre memorização:
  <https://community.logos.com/discussion/244677/memorization-tool-improvement-ideas> [S]
- Accordance 14: <https://www.accordancebible.com/accordance-14/> [S]
- YouVersion, versículo do ano de 2025 (ChurchLeaders):
  <https://churchleaders.com/news/2209898-youversion-2025-verse-of-the-year-bobby-gruenewald.html> [V para o que o artigo diz]
- YouVersion, planos anuais em 2025 (Crosswalk):
  <https://www.crosswalk.com/11923935> [S]
- Bible Hub, ferramentas: <https://biblehub.com/tools.htm> [S]
- Sermonary: <https://sermonary.com/home/pro/> [S]
