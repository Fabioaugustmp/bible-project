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
