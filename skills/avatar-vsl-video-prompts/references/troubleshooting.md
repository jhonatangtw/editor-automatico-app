# Troubleshooting — bugs comuns e correções

Catálogo de problemas reais de geração de avatar e como corrigir. A maioria é resolvida na DIREÇÃO do prompt, sem mudar a copy.

## Fala / áudio

**Fala corrida (acelerada).**
- Causa: muitas palavras para o tempo do clipe.
- Correção: dividir o bloco em dois (cada um mais folgado) OU, se couber, reforçar "calm, even, unrushed pace, not rushed". Preferir dividir.

**Cortou no meio da fala.**
- Causa: bloco maior que o teto do modelo.
- Correção: resegmentar respeitando o teto (8/10/15s) e fim de frase.

**Começa já falando / gagueja / funde sílaba (ex.: "Happyriliver").**
- Causa: áudio nasce no ataque da primeira sílaba.
- Correção: buffer de silêncio (~0,5s) antes da fala; separar palavras do nome; pronúncia fonética. Para marca no início, reordenar a frase tirando a marca do ataque.

**"Hmm" / "uh" / humming no meio.**
- Causa: vírgulas/pausas lidas como hesitação, ou instrução de "beat/breath".
- Correção: "no filler sounds, no hmm, no uh, no humming"; em blocos terminados em vírgula, "after the last word she simply stops, mouth settling closed, no filler".

**Entonação não fecha (soa aberta) no fim do vídeo.**
- Causa: fala termina exatamente no fim do clipe, sem espaço para a curva descer.
- Correção: "lands the final words on a clear downward, conclusive falling intonation, not rising, not trailing" + silêncio final de ~0,5s. No Veo, garantir que ela termine antes do fim do clipe.

**Voz extra ("yeah", "uhum", host).**
- Causa: cenário de podcast/entrevista induz segunda voz.
- Correção (sempre): "Only the main avatar's voice. No second voice, no interviewer, no off-screen voice, no 'yeah', no 'mm-hmm'." No Kling, jogar também no [Negative].

## Boca / expressão

**Boca muito expressiva / mandíbula exagerada / rosto teatral.**
- Correção: "subtle, controlled mouth movement, minimal jaw, calm restrained delivery, NOT exaggerated, no wide mouth opening, no theatrical mouth movement." Reforçar no Base e no fim de cada Action.
- Idosos: aplicar boca mínima sempre.

**Piscar robótico.**
- Correção: "eyes blink naturally and irregularly, never on a fixed rhythm; blinks land on pauses and gaze shifts."

**Olhos arregalados.**
- Correção: remover qualquer "eyes widening"; usar "eyes natural, not widened"; ênfase via sobrancelha/nod/voz.

## Movimento / corpo

**Avatar se aproxima/afasta da câmera (lean/push-in indesejado).**
- Correção: "distance between subject and lens stays fixed, no lean forward/back, no push-in, no zoom, no dolly."

**Carro parece em movimento (devia estar estacionado).**
- Correção: "parked, stationary car, completely still, fixed static background, no rolling scenery, no sliding light, no engine noise."

**Mão fantasma / aparece a mão que segura o celular (UGC selfie).**
- Correção: "the phone-holding hand/arm stays completely out of frame; only the free hand ever appears." Confirmar o lado pela imagem.

**Mãos deformam ao gesticular (saindo do colo e voltando).**
- Correção: oferecer versão de gesto mínimo (mãos quase não saem do colo, só palmas abrindo). Comum no Veo/Kling em clipe curto.

**Selfie parece câmera em tripé (estável demais / sem vida).**
- Causa: faltou o micro-shake de mão.
- Correção: "constant subtle natural handheld micro-shake from the hand holding the phone, slight organic drift in framing, never tripod-stable, never perfectly still — the small involuntary motion of a real hand holding a phone." Sem exagerar (não é shaky-cam). Se a cena é num carro parado, o veículo/fundo fica imóvel; só a câmera (mão) treme.

**Anatomia cresce/deforma (ex.: órgão "crescendo" em B-roll).**
- Correção: câmera locked, "shape and size stay identical, only [a propriedade que muda] changes"; reforçar nos timestamps. Se persistir, gerar 2 imagens fixas e crossfade na edição.

## Legenda / texto na tela

**Aparece legenda/caption/texto.**
- Correção: proibir em múltiplos termos (no subtitles, no captions, no closed captions, no on-screen words, no titles, no overlays, no lower thirds, no watermark, no kinetic text) + "completely clean frame with zero text". No Veo, fechar a fala com `(no subtitles, no captions, no on-screen text)`. Se persistir, é seed — regerar 1–2 vezes.

## Erros de plataforma (FAL)

**Erro 422 "Error validating the input".**
- NÃO é recusa de conteúdo — é payload fora do schema.
- Correções: trocar aspas duplas por simples na fala; remover travessões longos (—) e reticências (…); no image-to-video, garantir `image_url` carregado; `duration` no formato aceito (ex.: "8s"); `aspect_ratio` válido (auto/9:16/16:9/1:1); `generate_audio` ligado se precisar de fala.
- Diagnóstico: testar 1 bloco curto e limpo; se passar, era formatação.

**Recusa por conteúdo (raro).**
- Imagem de profissional de saúde (jaleco/estetoscópio) ou claims médicos fortes podem disparar filtro em alguns modelos. Se acontecer, suavizar enquadramento clínico ou ajustar a imagem; mas confirmar antes que não é 422/payload.
