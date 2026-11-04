# Storyboard (feito antes de montar)

Arquivo do job: `_SAMURAI/storyboard.md` (Drive) + cópia em `1 Projeto/<slug>/storyboard.md`.

Cabeçalho: produto, oferta (preço, frascos, garantia, texto do botão), expert, voz, duração estimada, paleta.

Uma linha por momento, na ordem da fala:

| # | tempo (após TTS) | frase de entrada → frase de saída | tipo | visual | asset | movimento | transição | texto na tela | SFX |
|---|---|---|---|---|---|---|---|---|---|

- `tipo`: D, F, M, T, B, R (ver PADRAO.md).
- `asset`: nome do arquivo existente ou `NOVO:<id>`; todo NOVO aparece na lista de geração com prompt de imagem e de movimento.
- Antes de gerar: conferir proporção D ≈ 30–40 %, nenhum trecho D > 8 s fora de respiro, nenhum asset usado duas vezes.
- Depois do TTS, preencher a coluna de tempo com os `_alin.json` e reconferir os trechos longos.
