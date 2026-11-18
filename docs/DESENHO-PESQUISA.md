# Desenho do painel de busca detalhada (para avaliação)

Especificação para o usuário avaliar **antes** de construir. Complementa a área
**Pesquisar** da `docs/PROPOSTA-DESIGN.md` (seção 4). Nada foi implementado.
Base: o que já existe (busca por palavra, busca por sentido, aba Temas, pontes
bilíngues) e o que os programas mostraram (Super Search, operadores, Strong).

## 1. Objetivo

Permitir uma pergunta de estudo precisa: "onde a graça aparece perto de
verdade", "todas as ocorrências de G5485 nos Evangelhos", "o que os comentários
dizem sobre Romanos 8:1 que cita a palavra justificação". O resultado deve dizer
**por que** cada item apareceu.

## 2. Viabilidade (verificada na base)

- **Strong por ocorrência:** a tabela `tokens` guarda `strong`, `book`,
  `chapter`, `verse`, `pos`, `module_id` e `original`, com 1.421.482 linhas. A
  busca por número Strong não exige reimportação.
- **NEAR:** o FTS5 da tabela `verses_fts` aceita `NEAR(termo termo, n)`
  (verificado: 32 versículos com "graça" e "verdade" a até 5 palavras).
- **Escopo:** versões são `modules`; obras de comentário são `modules` do tipo
  comentário; livros são `book` (faixa da T66 já existe).

## 3. Layout

Tela inteira, na área Pesquisar. Em telas menores que 760 px, os filtros viram
uma folha que se abre por um botão.

```
┌ Pesquisar ─────────────────────────────────────────────────────┐
│ [ graça                          ] [Pesquisar]   Histórico ▾   │
│ Filtros ativos: (ARA ×) (Jo ×) (G5485 ×)     [Salvar busca]    │
├──────────────────────┬─────────────────────────────────────────┤
│ ESCOPO               │ 1.284 resultados · Versículos 412         │
│ MODO                 │ Comentários 691 · Dicionários 181         │
│ STRONG               │ ─────────────────────────────────────── │
│ IDIOMA               │ João 1:14 · ARA                          │
│ LIVROS               │ "...cheio de graça e de verdade..."      │
│ ORDEM                │ por quê: graça ✓ · G5485 ✓ · NEAR 2      │
└──────────────────────┴─────────────────────────────────────────┘
```

## 4. Campos

| Campo | Opções | Observação |
|---|---|---|
| **Escopo** | toda a biblioteca; uma versão; uma obra (comentário ou dicionário); uma faixa de livros | padrão: a versão aberta no Ler |
| **Modo** | todas as palavras; qualquer palavra; frase exata; próximas (NEAR, alcance n) | NEAR usa o alcance da T96 |
| **Strong** | número G ou H, com ou sem a palavra no texto | busca em `tokens`; mostra a tradução usada no versículo |
| **Idioma** | português; inglês; original (hebraico e grego) | reaproveita o filtro de idioma já existente |
| **Livros** | chips por livro (T66), faixa do Antigo ou do Novo Testamento | |
| **Ordem** | relevância; ordem da Bíblia | |

## 5. Resultados

- **Cabeçalho com contagem por tipo** (versículos, comentários, dicionários),
  como a busca atual.
- **"Por quê"** em cada item: os termos encontrados, o Strong encontrado e o
  alcance do NEAR. Sem isso, o estudante não sabe por que a passagem apareceu.
- **Por sentido** continua separado (aba própria), como já está na busca atual.
- **Copiar todos** (T97) e **salvar busca** (com nome) para repetir depois.
- **Histórico** de buscas recentes (local no navegador, sem guardar em `user.db`
  sem pedido).

## 6. API proposta (não implementada)

`/api/search2?q=...&modo=todas|qualquer|frase|near&near=5&strong=G5485&escopo=modulo:3|livros:40-43&idioma=por&ordem=relevancia&offset=0`

- Retorno com a mesma forma de `/api/search` (listas por tipo, totais) e um campo
  `porque` em cada item.
- Limite de página igual ao atual (60 versículos).
- Nada é gravado; a busca é só leitura de `library.db`.

## 7. Fases

1. **Escopo e modo** (sobre o FTS5 que já existe, com NEAR). Baixo risco.
2. **Strong** (consulta em `tokens`). Médio: é a parte mais útil para estudo de
   palavra.
3. **Copiar e salvar busca.** Baixo.
4. **Sugestão de ortografia** (T100). Depende de léxico; por último.

## 8. Decisões para você

1. **Escopo padrão:** a versão aberta no Ler (recomendado) ou toda a biblioteca?
2. **Strong na busca:** mostrar o número junto a cada palavra no resultado?
   (recomendado: sim, é o que permite estudar a palavra.)
3. **Busca salva:** ficar só no navegador ou em `user.db`? (recomendado:
   `user.db`, porque é do usuário e sobrevive a reimportações.)
4. **Ordem da Fase 1 e 2:** começar pelo escopo e modo, ou pelo Strong? (o
   recomendado é escopo e modo, por ser o de menor risco.)

## 9. Fora deste desenho

- Resumo ou resposta gerada por modelo de linguagem: fora, por pedido seu.
- Busca em texto criptografado: fora, pela regra D008.

## 10. Estado da implementação

**Fase 1 (escopo e modo): feita.** Decisões do usuário aplicadas: escopo padrão
é a versão aberta (1); Strong nos resultados fica para a fase 2 (2); a busca salva
será no navegador por enquanto e depois no painel autenticado (3); a ordem é
escopo e modo (4).

- Modo na Bíblia: todas as palavras, qualquer palavra, frase exata e próximas
  (NEAR, alcance de 1 a 50 palavras). Testado: "graça verdade" dá 9 (todas), 516
  (qualquer), 0 (frase exata), 7 (NEAR 5) e 1 (NEAR 1), em ARA.
- Escopo: versão aberta ou todas as versões.
- **Limite:** o modo vale para os versículos. Comentários e dicionários continuam
  em todas as palavras (com a ponte por Strong). Estender o modo a eles é parte
  da fase 2.
- Não implementado ainda: Strong nos resultados (fase 2), copiar e salvar buscas
  (fase 3) e sugestão de ortografia (fase 4).
