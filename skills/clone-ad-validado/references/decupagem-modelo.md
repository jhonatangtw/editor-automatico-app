# Modelo do decupagem.md

Copie, preencha e mostre ao usuário no checkpoint do passo 2. O exemplo
preenchido no fim é de um clone real (anúncio de emagrecimento em inglês,
UGC selfie, primeiros 29 s).

```markdown
# Decupagem — [NOME DO AD] (trecho [0,00 → FIM s])

Fonte: original/[ARQUIVO] — [LARGURA]×[ALTURA], [FPS] fps. Transcrição: Whisper medium,
tempo por palavra, conferida contra a legenda queimada.

**Corte:** 0,00 → [FIM] s — fim da frase "[ÚLTIMAS PALAVRAS]" (a próxima começa em [T] s).

> Correções do Whisper: [o que ele ouviu] → [o que a legenda queimada diz]. Vale a legenda.

## Roteiro
| # | Início | Fim | Fala |
|---|---|---|---|

## Palavra por palavra
palavra[início] palavra[início] ...

## Mapa de cenas
| Bloco | Tempo | Tipo | O que tem na tela | No clone |
|---|---|---|---|---|
| A | | avatar / tela dividida / b-roll / produto | | personagem nova · REFEITO (mostra a pessoa antiga) · reaproveitado (sem a pessoa) |
| — | | Transição | flash / desfoque / vazamento de luz (quadro exato) | igual |

## Legenda (estilo)
Caixa [cor, cantos], texto [cor, peso, fonte aproximada], [por frase | por palavra],
altura da base: [y em fração da tela por bloco]. Grupos: "..." · "..." · "..."
```

## Exemplo preenchido (resumido)

**Corte:** 0,00 → 29,04 s — fim de frase (a seguinte começa em 29,04 s).

> Correção do Whisper: ele ouviu "responding **this food**, it's not your fault". A legenda
> queimada diz "responding — it's not your fault" (era respiração). Ficou valendo a legenda.

| Bloco | Tempo | Tipo | O que tem na tela | No clone |
|---|---|---|---|---|
| A | 0,00 – 12,60 | Tela dividida | Clipe de uma mulher num avião em cima; a apresentadora em selfie UGC embaixo. Legenda a ~49 % da altura. | Avião **reaproveitado** (só a faixa de cima, sem a legenda nem a apresentadora); **personagem nova em selfie** (lip sync) embaixo. |
| — | 12,60 – 12,64 | Transição | Flash branco (1 quadro). | Flash branco. |
| B | 12,64 – 17,38 | Tela dividida | Cima: apresentadora na cozinha falando. Baixo: b-roll da receita (só mãos e utensílios). Legenda a ~71 %. | Cima: **personagem nova na cozinha**. Baixo: receita **reaproveitada**, legenda antiga borrada e coberta pela nova. |
| — | 17,38 – 17,46 | Transição | Chicote com desfoque. | Desfoque de movimento. |
| C | 17,46 – 24,48 | Avatar | Cozinha em tela cheia, selfie. | Personagem nova na cozinha, tela cheia. |
| — | 24,48 – 24,69 | Transição | Vazamento de luz quente + branco. | Igual. |
| D | 24,69 – 28,83 | B-roll "antes" | Dois planos lado a lado do corpo da apresentadora, rosto cortado, **cabelo aparecendo**. | **REFEITO**: 2 imagens GPT Image 2.5 da personagem nova + Kling 3.0 Turbo. |
| — | 28,83 – 29,04 | Transição | Vazamento de luz → branco. | Igual; o clone termina no branco. |

Repare no bloco D: o rosto estava fora do quadro, mas o **cabelo** da apresentadora
aparecia — por isso foi refeito. "Mostra a pessoa antiga" é qualquer pedaço dela.

Legenda: caixa branca de cantos arredondados, texto preto em sans bold (tipo Poppins Bold),
1–2 linhas, **por frase**; base da caixa a 0,55 da altura no bloco A e a 0,75 nos blocos B/C/D.
