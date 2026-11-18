# Desenho de Estudos (D5) para avaliação

Documento para o usuário avaliar **antes** de qualquer código. Parte da seção 5
e da seção 4 de `docs/PROPOSTA-DESIGN.md` e das observações de
`docs/ESTUDO-PROGRAMAS.md`. Nada aqui foi implementado.

## 1. O que é um estudo

Um estudo é um texto que o usuário monta a partir do que leu: um esboço com
passagens, citações de comentários, palavras originais e notas próprias. Ele
**não copia** a Bíblia nem o comentário: guarda a referência e, para citações,
um trecho curto com a procedência (obra e chave de origem).

O nome da área é **Meus estudos**. A palavra "sermão" não aparece na
interface, e o estudo não tem formato de pregação: é um caderno de estudo
organizado por blocos.

## 2. Como se entra num estudo

Três caminhos, do mais leve ao mais formal:

1. **Adicionar ao estudo** a partir de qualquer passagem, comentário ou palavra
   (um botão no painel). Se não há estudo ativo, cria um rascunho com o título
   da passagem.
2. **Nota solta**: escrever sem estudo. Pode ser promovida a estudo depois.
3. **Novo estudo** em Meus estudos, com título e passagem principal.

## 3. Telas (esboço em texto)

```
┌ Meus estudos ───────────────────────────────────────────────┐
│ Estudos   Notas   Marcações   Importadas (e-Sword)          │
├─────────────────────────────────────────────────────────────┤
│ Romanos 8 — a vida no Espírito         rascunho   atualizado│
│ Ansiedade e confiança                  pronto     ontem     │
│ Perdão no Salmo 130                    rascunho   há 3 dias │
└─────────────────────────────────────────────────────────────┘

┌ Estudo: Romanos 8 — a vida no Espírito ─────── [Exportar ▾] ┐
│ Passagem principal: Rm 8:1–4                                │
│ ── Bloco 1  título  "Não há condenação"                      │
│ ── Bloco 2  passagem  Rm 8:1  (abre no leitor)               │
│ ── Bloco 3  citação  Gill sobre Rm 8:1  [procedência]        │
│ ── Bloco 4  palavra  G2917 krino (abre o Strong)             │
│ ── Bloco 5  nota  "pergunta: o que é 'condenação' aqui?"     │
│ [+ bloco: passagem · citação · palavra · nota · título]      │
└─────────────────────────────────────────────────────────────┘
```

A coluna do estudo ativo aparece **ao lado do Ler**, como uma coluna fixada
(já existe o mecanismo de colunas, T61). Assim, a leitura e o estudo ficam na
mesma tela, e "Adicionar ao estudo" não tira o usuário do texto.

## 4. Blocos

| Bloco | O que guarda | Vem de |
|---|---|---|
| Título | texto curto de seção | digitado |
| Passagem | referência (livro, capítulo, versículo) | painel do versículo |
| Citação | trecho curto, obra, chave de origem, procedência | comentário |
| Palavra | número Strong e termo original | painel Strong |
| Nota | texto próprio, em Markdown simples | digitado |

## 5. Pontos de cuidado

- **Não vira texto gerado.** O estudo é montado pelo usuário; o app não escreve
  parágrafos, não resume e não completa frases.
- **Citação sempre com procedência.** Se a obra mudar na reimportação, o bloco
  mostra "o texto na origem mudou desde que você citou" (proposta, seção 5).
- **Exportar:** Markdown e Word já existem para as notas (T42); estudos entram
  no mesmo formato, um bloco por parágrafo, com as referências visíveis.
- **Nada apagado sem pedido:** estudos vão para a lixeira, como as notas.

## 6. Decisões que dependem de você

1. **Nome da área:** "Meus estudos" ou outro? (Evite "Sermões" e "Pregações",
   como você pediu.)
2. **Caminho de entrada:** começar pelo botão "Adicionar ao estudo" no painel
   (leve) ou pela área Meus estudos (formal)? Recomendação: o botão, com a área
   para ver e organizar.
3. **Coluna ao lado do Ler:** sempre que houver estudo ativo, ou só quando o
   usuário abrir? Recomendação: só quando abrir.
4. **Tamanho do bloco de citação:** limitar a 1.000 caracteres (proposta) ou
   deixar o usuário escolher o trecho? Recomendação: o trecho escolhido, até
   1.000 caracteres.
5. **Ordem de construção:** primeiro as notas (T40, já feito), depois os
   estudos com blocos de passagem e nota; citação e palavra depois. Você
   concorda com essa ordem?

## 7. Fora deste desenho

- Google Docs e PDF: ficam para depois, com a decisão sobre bibliotecas (D003)
  e a conta do usuário.
- Compartilhar estudos: não previsto; o app é local.
- Estudos com IA: fora, por pedido do usuário.
