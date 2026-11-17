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
