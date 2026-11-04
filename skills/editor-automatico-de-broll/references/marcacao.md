# Marcação

## Formato

- Marcador de **TRECHO** (`duracao > 0`) cobrindo a janela real da fala.
- Nome `NN - TIPO - descrição`, numerado em ordem de timeline.
- Comentário com a **fala citada** e a direção do plano.

## Cores (convenção da casa)

| Cor | Índice | Tipo |
|---|---|---|
| vermelho | 1 | `B-ROLL` |
| azul | 6 | `LETTERING` |
| roxo | 2 | `COPY` |

## Cobertura

O **vermelho é a cama de imagem**: estique cada B-ROLL até o início do próximo, e o primeiro começa
em `0` mesmo antes da primeira palavra — o b-roll de abertura tem que estar no ar antes da primeira
sílaba.

Azul e roxo ficam colados na fala. Esticar cartela destrói a informação de quando o texto entra.

## O que vira roxo

- Conflito entre hook e corpo da copy (no AD04: o H1 dizia banheiro, o corpo dizia cozinha).
- Nome real de pessoa citado — risco de uso de imagem.
- Claim sensível (GLP1, promessa de resultado).
- Vão sem transcrição onde a copy tem texto.
- Erro provável de ASR — cite o que veio e o que a copy diz.

## Aplicar

`pr_marcadores_criar` aceita até 200 por chamada e respeita `duracao`. Se precisar **editar**
marcador existente, não há tool — use ExtendScript (`mk.name`, `mk.comments`, `mk.end = <segundos>`).

Confira sempre com `pr_marcadores_listar` e `pr_autoclip_info` (que devolve contagem por cor).
