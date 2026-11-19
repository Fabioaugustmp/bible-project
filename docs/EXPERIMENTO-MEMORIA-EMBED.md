# Experimento: memória e qualidade da busca por sentido (BGE-M3)

Data: 2026-11-19. Script: `bench/experimento_memoria.py`. Ambiente: `.venv-bench` (torch 2.11, sentence-transformers 6.3), CPU com 4 threads (o servidor tem 4 vCPUs). Limite de trabalho: 3 GB de RAM para o serviço `embed`.

O índice carregado é o mesmo do serviço: 31.102 versículos e 199.150 comentários, em float16 no arquivo. Os versículos são convertidos para float32 e os comentários ficam em float16, com o produto escalar feito em blocos. Por isso o número inclui o índice inteiro, não só o modelo.

## Resultados

| Modo | Pico de memória | Memória estável | Consulta mediana | Consulta p90 | Situação |
|---|---|---|---|---|---|
| fp32 (atual) | 2,46 GB | 1,72 GB | 106 ms | 244 ms | **adotado** |
| bf16 | 4,27 GB | 2,12 GB | 289 ms | 443 ms | descartado: mais memória e mais lento |
| int8 (quantização dinâmica) | 5,21 GB | 4,78 GB | 79 ms | 92 ms | descartado: mais memória e qualidade menor |

Qualidade das consultas em relação ao fp32, sobre 31 consultas em português (top-10 de versículos):

| Modo | Cosseno médio | Cosseno mínimo | Top-10 em comum (média) | Top-10 em comum (mínimo) |
|---|---|---|---|---|
| bf16 | 0,9999 | 0,9999 | 99% | 90% |
| int8 | 0,9536 | 0,9243 | 81% | 40% |

## Conclusão

- Com fp32, o serviço fica abaixo de 3 GB de pico e tem a melhor qualidade. Por isso a quantização não é necessária agora, e a configuração atual foi mantida.
- O teto de 3 GB foi colocado como `mem_limit` no serviço `embed` do compose.
- A diferença entre os dois ambientes (Windows com CPU mais rápida e servidor com 4 vCPUs) não foi medida no servidor. Medir lá com `docker stats` durante algumas buscas é o próximo passo.

## Limites do experimento

- Mediu-se só a busca nos versículos para a qualidade. A busca nos comentários usa o mesmo modelo, mas não foi comparada.
- O conjunto de 31 consultas é pequeno. Serve para detectar perda grande de qualidade, não para afirmar uma diferença pequena.
- No Windows o `torch` estava com CUDA disponível, mas o experimento forçou a CPU, para se aproximar do servidor.
