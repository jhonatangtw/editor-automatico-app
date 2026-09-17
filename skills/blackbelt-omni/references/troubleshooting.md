# Bugs conhecidos e correções

Leia isto quando o usuário disser que um clipe saiu errado. Diagnostique pelo sintoma, corrija a causa, e regere **só aquele clipe** — nunca o lote inteiro.

## Legenda queimada que ninguém pediu

**Sintoma:** o clipe volta com a fala escrita na tela, geralmente mal grafada.
**Causa:** existe fala no prompt e a regra de texto não proíbe subtitle explicitamente.
**Correção:** a regra de texto precisa dizer, com essas palavras, que o diálogo é áudio e nunca aparece como legenda. Adicione também `no subtitles, no burned-in captions` no DO NOT. Se persistir, regere — costuma sair limpo na segunda tentativa.

## Metadata renderizada como texto

**Sintoma:** aparecem na tela coisas como `25 fps`, `1080x1920`, `#C9A227` ou `ease-out`.
**Causa:** o Omni interpreta as notas técnicas do prompt como conteúdo visual.
**Correção:** a primeira regra crítica precisa listar explicitamente: pixel sizes, font names, color codes, easing names, durations, frame rates. Se já estiver lá e mesmo assim vazou, reduza o bloco TECHNICAL ao mínimo.

## Grafia errada no texto renderizado

**Sintoma:** `EU QUEIRO`, `COMMENTE`, letra duplicada, L virando i maiúsculo.
**Causa:** limitação do renderizador de texto, não do prompt.
**Correções, em ordem:**
1. Regere o mesmo prompt — a string é curta, costuma sair certa em 2 ou 3 tentativas.
2. Encurte a string. Duas palavras erram menos que quatro.
3. Use caixa alta — texto uppercase sai mais limpo.
4. Repita a string idêntica em todos os pontos do prompt onde ela aparece.
5. Se insistir, mude pro modo A e crave o texto na edição. É mais rápido que brigar com o modelo.

## Fala corrida ou acelerada

**Sintoma:** a pessoa fala rápido demais, come sílabas, atropela o fim.
**Causa:** a fala passa de 24 palavras para 10 segundos.
**Correção:** corte a fala para no máximo 24 palavras. Se o sentido não couber, quebre em dois clipes.

## Fala repetida ou em loop

**Sintoma:** a última frase repete, ou a fala reinicia no fim do clipe.
**Causa:** a fala é curta demais para os 10 segundos e o modelo preenche o resto.
**Correção:** aumente a fala para pelo menos 16 palavras, ou estenda o beat de HERO FRAME e declare explicitamente `Silence` nele. A trava `The line is spoken once, exactly as written, and is not repeated or looped` precisa estar no VOICE & DIALOGUE.

## Voz extra ou narrador

**Sintoma:** aparece uma segunda voz, um narrador, ou eco.
**Causa:** falta a trava de voz única.
**Correção:** `Single voice only — no narrator, no voice-over, no echo, no second speaker` no VOICE & DIALOGUE, e `no second voice` no DO NOT.

## Sotaque errado

**Sintoma:** sai português europeu, espanhol ou inglês com sotaque.
**Correção:** a negação precisa ser explícita — `never European Portuguese, never Spanish, never English` — e o DO NOT precisa repetir. Declarar só "Brazilian Portuguese" não basta.

## Sigla soletrada

**Sintoma:** "IA" vira "i-á" picotado, números saem em algarismo lido errado.
**Correção:** escreva tudo por extenso na fala: "inteligência artificial", "quatro", "dois". Mantenha `Numbers are spoken as full words` no bloco de voz.

## Primeira palavra cortada

**Sintoma:** o clipe começa no meio da primeira palavra.
**Causa:** o Ingredient tem a boca aberta, ou falta a trava de entrada.
**Correção:** `Speaks continuously from the first frame with no silent lead-in` no bloco de voz, e use imagem de referência com a boca fechada. Comece a fala com uma palavra curta.

## Clipe hiperativo, sem respiro

**Sintoma:** algo se move em todos os frames, cansa em 3 segundos.
**Causa:** os beats RESOLVE e HERO FRAME foram preenchidos com movimento.
**Correção:** o HERO FRAME precisa conter a palavra `frozen` ou `held perfectly still` e nenhuma ação. `No motion filling every single second` no DO NOT.

## Paleta ou grain diferente entre clipes do mesmo lote

**Sintoma:** os clipes não emendam, um está mais quente ou mais granulado.
**Causa:** gerados em sessões diferentes, ou com Ingredients diferentes.
**Correção:** mesma sessão, mesmo Ingredient, blocos STYLE e PALETTE idênticos. Se já geraram assim, iguale na correção de cor da edição.

## Gráfico invadindo a faixa central

**Sintoma:** o card sobe demais e a legenda da edição fica em cima dele.
**Correção:** reforce a caption safe zone e ancore os cards explicitamente — `cards and panels live in the lower third; the subject occupies the upper half`.

## Interface reconhecível de app

**Sintoma:** aparece algo parecido com uma rede social ou um app conhecido.
**Correção:** `Any interface shown is an abstract generic panel with blank rows` na regra de obra original, e `no recognisable app interface` no DO NOT. Descreva campos como formas arredondadas abstratas, nunca como UI.
