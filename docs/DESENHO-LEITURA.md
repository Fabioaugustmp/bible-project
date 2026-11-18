# Desenho: leitura diária (T82)

Base: "Leitura diária" do theWord e os planos por capítulo do e-Sword; a
ESTUDO-PROGRAMAS pede marcar intervalos de versículos como lidos. Esta primeira
versão marca **capítulos**; intervalos ficam para a próxima etapa.

## Modelo (data/user.db)

- `reading_plans(id, title, created_at, deleted_at)`: um plano.
- `reading_days(id, plan_id, pos, book, chapter, done_on)`: um capítulo por dia do
  plano, na ordem da Bíblia. `done_on` é a data em que foi marcado como lido.

Sem data fixa: "hoje" é o próximo capítulo ainda não lido. Não há calendário nem
lembrete nesta etapa.

## Regras

- Criar: capítulo inicial até o final, até 400 capítulos por plano.
- Marcar como lido grava a data de hoje (`done_on`); desmarcar limpa a data.
- Apagar o plano é lixeira (`deleted_at`), como as notas e os estudos.
- "Notas de hoje": notas criadas na data de hoje (`created_at`).

## Interface

- Botão **Leitura** na barra: abre "Leitura de hoje" no painel.
- Por plano: progresso, próximo capítulo (clicar abre a leitura), "Marcar como
  lido" e "Apagar plano".
- Formulário para criar: livro e capítulo inicial, livro e capítulo final.

## Fora desta etapa

- Intervalos de versículos e leitura por versículo.
- Planos com datas, calendário e lembrete.
- Devocionais e planos prontos (a Bíblia em um ano).
