# Avaliação da busca bilíngue (T23)

Feita em 2026-11-17 sobre a base completa (`data/library.db`), com as regras
de `app/bridge.py` descritas na D013. Comentários e dicionários são buscados
com e sem a ponte; a Bíblia é sempre buscada só na versão aberta.

## Expansões e quantidade de resultados

As 15 primeiras consultas são as do roteiro de validação (EC2); as quatro
últimas testam acentos ("graca"), uma palavra muito frequente ("senhor") e
duas palavras de apoio que não podem ser expandidas ("ser", "dizer").

| Consulta | Termos incluídos | Comentários sem ponte | com ponte | Verbetes sem | com |
|---|---|---|---|---|---|
| graça | grace (G5485) | 565 | 18245 | 86 | 1625 |
| fé | faith (G4102) | 1086 | 17545 | 260 | 2106 |
| arrependimento | repentance (G3341) | 260 | 5228 | 30 | 439 |
| aliança | covenant (H1285) | 160 | 7349 | 77 | 1357 |
| justificação | justification (G1347) | 63 | 2513 | 13 | 275 |
| expiação | atonement (H3725) | 74 | 2636 | 22 | 434 |
| ressurreição | resurrection (G386) | 295 | 4938 | 56 | 693 |
| batismo | baptism (G908) | 110 | 2073 | 35 | 341 |
| oração | prayer (H8605), prayers (G4335) | 475 | 11320 | 72 | 1449 |
| santificação | holiness (G38), sanctification (G38) | 38 | 6876 | 4 | 537 |
| reino | kingdom (G932), kingdoms (H4467) | 759 | 12855 | 106 | 1934 |
| misericórdia | loving devotion (H2617), mercy (H2617) | 411 | 10422 | 30 | 785 |
| redenção | redemption (G629) | 92 | 4409 | 12 | 453 |
| esperança | hope (G1680) | 465 | 9977 | 31 | 1011 |
| pecado | sin (G266), sins (G266) | 1110 | 25074 | 81 | 2718 |
| graca | grace (G5485) | 565 | 18245 | 86 | 1625 |
| senhor | lord (H3068) | 1502 | 41088 | 359 | 5342 |
| ser | — | 2255 | 2255 | 1090 | 1090 |
| dizer | — | 1191 | 1191 | 240 | 240 |

Consultas com mais de uma palavra:

| Consulta | Consulta montada | Comentários sem ponte | com ponte |
|---|---|---|---|
| justificação pela fé | `("justificação" OR "justification") AND ("fé" OR "faith")` | 27 | 1.717 |
| reino de deus | `("reino" OR "kingdom" OR "kingdoms") AND ("deus" OR "god")` | 659 | 10.062 |
| "vida eterna" graça | frase exata não é expandida; só "graça" | 64 | 64 |

Tempo de cada consulta: de 0,00 a 0,02 s.

## Pertinência dos primeiros resultados em inglês (conferida à mão)

Li os 10 primeiros comentários em inglês de quatro consultas.

| Consulta | Pertinentes | Observação |
|---|---|---|
| graça | 10 de 10 | Gill, Poole, JFB, Henry e Vincent sobre Jo 1:16 e Ef 2:8; um é a lista de referências do TSKe, pertinente mas pouco útil para ler |
| expiação | 10 de 10 | Gill, TSKe, Biblical Illustrator, Darby e Scofield sobre a expiação em Levítico e Números |
| misericórdia | 9 de 10 | um falso positivo: "loving devotion to rectitude" (Sl 119), porque "loving devotion" é como a BSB traduz H2617 |
| pecado | 10 de 10 | todos sobre pecado; antes de excluir "sin offering" a lista pendia para a oferta pelo pecado em Levítico |

## O que fica de fora (limites conhecidos)

- **Palavras que a ARA quase não usa como tradução de um Strong** não são
  expandidas: "santificação" só aparece 10 vezes e já é coberta; termos
  teológicos posteriores à Bíblia ("pré-milenismo", "Trindade") não têm
  Strong e ficam para a busca semântica (M3).
- **Verbos** não são expandidos na prática: a ARA espalha cada verbo por
  várias formas ("ama", "amou", "amam"), e nenhuma passa do limite.
- **Frases entre aspas** não são expandidas.
- **Ordem dos resultados:** comentários em português vêm primeiro; os em
  inglês vêm depois, ordenados por relevância do FTS. Com a ponte há muito
  mais resultados em inglês (por exemplo 18.245 para "graça"), e só a
  primeira página é lida; a qualidade da ordem não foi medida além dos
  10 primeiros de cada consulta acima.
