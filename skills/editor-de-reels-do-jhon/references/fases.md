# Fases em detalhe — os números e o porquê

Valores tirados de um Reels de lançamento real (bruto iPhone 4K60 HDR HLG de
10 min → corte de 65 s → premium 1,15x).

## 1. Decupagem

| Item | Valor | Por quê |
|---|---|---|
| Modelo | Whisper `medium`, pt, `word_timestamps` | `small` inventa take repetido; `large-v3` só para reconferir trecho engolido |
| Trechos | voz por energia (RMS 10 ms), blocos de até ~25 s | passada longa alucina no silêncio e omite frase |
| Limiar da voz | nível forte da voz (p90) − 24 dB, entre −52 e −34 dBFS | celular tem noise gate (silêncio digital de −180 dB): "piso de ruído" não serve |
| Borda do corte | energia da voz, não o tempo do Whisper | palavra do Whisper desloca até 0,5 s |
| Margem | 0,40 s antes / 0,30 s depois ("corte suave") | nunca come sílaba; respiração na margem é aceitável |
| Fala vizinha | margem para no meio do silêncio entre duas falas | não puxar palavra de outro take |
| Reconferência | cada take transcrito de novo só na sua janela | a passada longa às vezes erra o LUGAR do take |
| Palavra > 1,5 s | alerta "trecho engolido" | o Whisper colapsa frase inteira numa palavra |

Nota do take (0–100) = 60 × parecido com o roteiro + 20 × completo + 10 × sem
pausa > 0,8 s + 10 × voz mais firme entre os takes da frase. Empate (≤ 5 pontos)
vira aviso "ouça os dois". **Entonação de pergunta, final enrolado e falso
começo o script não percebe** — no job real, o take escolhido pelo ouvido foi o
2º colocado na nota.

Gente improvisa: a maioria das frases do roteiro saiu diferente e houve 2 min de
improviso que não estavam no texto. Por isso o mapa lista "falas fora do roteiro".

## 2. Premiere pelo Tools PRO

- Ponte: painel Tools PRO › Conectar IA (gera o token local) › Modo avançado
  (libera ExtendScript). Servidor local em 127.0.0.1; o token fica no arquivo de
  conexão do painel na pasta do usuário e é lido na hora.
- Motor do Premiere 26: tem `const`, `JSON`, `Array.forEach`; **não tem** `let`,
  arrow function, `String.trim`. Os scripts gerados usam só `var`.
- Sequência: `app.project.createNewSequenceFromClips(nome, [item], bin)` — herda
  2160×3840 / 59,94 fps / espaço de cor do clipe, sem diálogo.
  `createNewSequence` abre a janela "Nova sequência" e **trava a ponte** até
  alguém clicar Cancelar.
- Posição: `Time` com `ticks` (254016000000 por segundo). String de segundos em
  `overwriteClip` é aceita sem erro e joga tudo no 0.
- `item.setInPoint(seg, 4)` / `setOutPoint(seg, 4)` (4 = vídeo+áudio) antes de
  cada `overwriteClip`; limpar in/out no fim.
- Timeout de ~2 min por script: lotes de 10 itens.
- Renomear trilha não existe na API pública (só pela QE). Não precisa aqui.

## 3. Cor

- Diagnóstico real: mídia Rec.2100 HLG → a sequência herdou Rec.2100 HLG → no
  Reels (SDR) tudo claro e lavado.
- Correção: `st = seq.getSettings(); st.workingColorSpace = <item "Rec. 709" de
  st.workingColorSpaceList>; st.autoToneMapEnabled = true; seq.setSettings(st)`.
- Lumetri: `qe.project.getVideoEffectByName("Cor de Lumetri")` (PT) ou
  `"Lumetri Color"` (EN) + `addVideoEffect` pela QE; os controles da Correção
  básica são achados pelo nome (Saturação/Saturation…) com índice de reserva.
- Look aprovado: Saturação 110, Contraste +10, Realces −20, Sombras −10, Brancos −10.
- Prévia pelo ffmpeg: este ffmpeg não tem `zscale`/`libplacebo`; a aproximação
  `eq=gamma=0.80:saturation=1.55:contrast=1.12` serve só para ouvir/ver o corte.

## 4. Exportar o corte (o aluno)

H.264, vertical no tamanho da sequência, Rec.709, AAC 48 kHz. O premium lê esse
arquivo e nunca o altera.

## 5. Premium (HyperFrames)

| Item | Valor |
|---|---|
| Canvas | 1080×1920, 30 fps |
| Proxy de composição | 1440×2560 30 fps CRF 12, keyframe a cada 1 s (cobre punch-in de 116 % sem ampliar) |
| Lettering | topo y 196–620, 1–4 palavras/linha, aparece na palavra (pop 0,34 s) |
| Gancho | 1ª linha já visível no quadro 1 |
| Punch-in | ~1 a cada 1,5–3 s, 102–116 %, "snap" 0,15 s na batida forte + deriva linear |
| Legenda | 1–3 palavras, máx. ~19 caracteres, palavra ativa em destaque, faixa y 1432–1528 |
| Zona segura Reels | nada importante em y < 192, y > 1536, nem x > 960 na metade de baixo |
| Telas | placas 3D 570×350 com aro dourado, carrossel nas palavras |
| Layout | cheio / dividido (rosto sobe 120 px, painel de vidro a partir de y 1010) / pip (cartão 460×620 no alto) |

## 6. Mix e QC

- Voz original intocada; música −16 dB com sidechain (threshold 0.03, ratio 5,
  attack 25 ms, release 400 ms); SFX com volume da lista × 0,8.
- Normalização para −14 LUFS + limitador; true peak final ≤ −1 dBTP (real: −14,1 / −1,9).
- `freezedetect=n=0.0005:d=0.25`: zero trechos parados é a meta.

## 7. Velocidade

`setpts=PTS/1.15,fps=30` + `atempo=1.15` no mesmo comando, depois do vídeo
pronto. 65,6 s → 57,0 s. Loudness re-normalizado (−14 LUFS, TP −1,5).
