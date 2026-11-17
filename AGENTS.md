# Guia para quem continua este projeto

Vale para pessoas e para modelos. Responda e documente em português.

## Por onde começar

1. [docs/BACKLOG.md](docs/BACKLOG.md): objetivo, estado atual, decisões
   pendentes do usuário e as tarefas, na ordem. **É a fonte única do que fazer.**
2. [docs/EXECUCOES-CRITICAS.md](docs/EXECUCOES-CRITICAS.md): ordem em ondas e
   desenho das tarefas mais difíceis. Leia a seção da tarefa antes de codificar.
3. [docs/PLANO.md](docs/PLANO.md): princípios e marcos.
4. [docs/DECISOES.md](docs/DECISOES.md): o que já foi decidido e por quê. Não
   contrarie uma decisão sem registrar uma nova que a revê.
5. [docs/FORMATOS.md](docs/FORMATOS.md): o que se sabe sobre os arquivos do
   e-Sword e do theWord. Tudo ali foi verificado nos arquivos reais.

Siga a seção "Roteiro por modelo" do backlog: ela diz a próxima tarefa, qual
modelo deve executá-la e quando um modelo menor deve parar e devolver a
tarefa. Fora do roteiro, pegue a primeira tarefa não concluída cujas
dependências estejam prontas. Se ela depender de uma pergunta da tabela
"Decisões pendentes do usuário", pergunte antes; não decida pelo usuário.

## Comandos

Importação completa (cerca de 8 minutos; gravar em arquivo separado, D009):

```bash
python -u importer/build.py --out data/library-full.db "C:\Program Files (x86)\e-Sword" "C:\ProgramData\The Word" "%APPDATA%\The Word"
```

Importação rápida só das amostras, para testar mudanças no importador:

```bash
python importer/build.py --out data/test.db modules-sample
```

```bash
python importer/verify.py data/library.db
```

```bash
python app/server.py
```

O servidor abre em http://localhost:8377 e lê `data/library.db`. A
configuração para a pré-visualização fica em `.claude/launch.json`.

## Regras

- **Planeje antes de executar.** Mudança que não está no backlog entra
  primeiro no backlog (ou em [docs/IDEIAS.md](docs/IDEIAS.md)).
- **Uma tarefa por commit.** A mensagem diz o que foi feito e o que foi
  verificado, com números.
- **Concluída significa:** critérios de aceite conferidos, `verify.py`
  passando, interface testada no navegador quando a tarefa a afeta, e
  documentos atualizados no mesmo commit (estado da tarefa no backlog;
  FORMATOS se algo do formato foi descoberto; DECISOES se houve escolha).
- **Relate o que não funcionou.** Falha, módulo ignorado ou verificação não
  feita aparecem no relatório e no commit, não são omitidos.
- **Procedência sempre.** Todo dado importado guarda o módulo e a chave de
  origem; não crie tabela derivada sem dizer de onde veio.
- **Nunca escreva nos módulos de origem** nem nas pastas dos programas.
- **Nunca tente abrir módulos criptografados** (D008).
- **Módulos e bases não entram no git** (D007): vários são protegidos por
  direito autoral.
- **Só biblioteca padrão do Python** enquanto a D003 valer.
- **Dados externos:** conferir a licença na página de origem antes de usar e
  registrar em DECISOES. As licenças citadas em
  [docs/PESQUISA-FEATURES.md](docs/PESQUISA-FEATURES.md) não foram conferidas.

## Armadilhas já encontradas

- Texto com barras invertidas (RTF, expressões regulares) passado por heredoc
  de shell é corrompido (`\r` vira quebra de linha, `\x` some). Escreva um
  arquivo `.py` e execute-o.
- Colunas de texto dos módulos podem conter bytes que não são UTF-8. Leia com
  `cast(coluna as blob)` e decodifique no Python.
- `length()` do SQLite para em um byte nulo; para tamanho real use
  `length(cast(coluna as blob))`.
- Campos de `config` dos `.twm` não são confiáveis (há `encrypted = 1` com
  texto aberto). Decida pelo conteúdo.
- A importação completa leva cerca de 10 minutos e a base passa de 1 GB. Rode
  em segundo plano, grave em `data/library-full.db` e só substitua
  `data/library.db` depois de verificar (D009). Pare o servidor antes de
  substituir.
- A saída do importador só aparece em tempo real com `python -u`.
- Versões como NVI, NTLH e a católica não têm exatamente 31.102 versículos.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `importer/build.py` | ponto de entrada; grava módulos, procedência e relatório |
| `importer/esword.py`, `importer/theword.py` | leitores de cada programa |
| `importer/rtf.py`, `importer/rvf.py` | conversão de RTF e RVF para texto |
| `importer/db.py` | esquema da base e utilitários (Strong, idioma) |
| `importer/canon.py`, `canon.json` | 66 livros e versículos por capítulo (KJV) |
| `importer/verify.py` | critérios de aceite da base |
| `app/server.py` | API local somente leitura |
| `app/static/` | interface (HTML, CSS e JavaScript puros) |
| `docs/` | plano, backlog, decisões, formatos, ideias, pesquisa |
| `data/`, `modules-sample/` | base gerada e módulos de amostra (fora do git) |
