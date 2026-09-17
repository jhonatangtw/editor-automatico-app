# Sintaxe por modelo

## Limites de duração (verificado contra `models_explore` em 25/07/2026)

Sempre reconfirmar com `models_explore(action='get', model_id=...)` antes de um lote grande — mudam com versões.

- **Veo 3.1** (`veo3_1`): duração **DISCRETA — só 4, 6 ou 8s**. Não aceita valor intermediário. Áudio/fala nativa. Params: `quality` (basic/high/ultra), `variant` (`veo-3-1-preview` = melhor, `veo-3-1-fast` = rápido). Aspect: só 16:9 e 9:16. Media: só `start_image` (SEM end_image).
- **Veo 3.1 Lite** (`veo3_1_lite`): mesmas durações 4/6/8, mas `generate_audio` é **false por default** e aceita `end_image`. É o modelo de lote barato.
- **Kling V3 (3.0)** (`kling3_0`): **3–15s nativo, contínuo — NÃO precisa extend.** Params: `mode` (std/pro/4k), `sound` (on/off — `off` gasta menos crédito). Media: `start_image` + `end_image`.
- **Seedance 2.0** (`seedance_2_0`): 4–15s contínuo; ponto ótimo de movimento 5–8s (clipes longos artefatam mais). Params: `mode` (std = até 4k / fast = só 480p-720p), `resolution`, `genre`, `generate_audio`. Media: `start_image`, `end_image`, **`image_references`, `video_references`, `audio_references`**.
- **Seedance 2.0 Mini** (`seedance_2_0_mini`): mesma família, 480p/720p só. Variante barata pra teste de prompt antes de queimar crédito no `std`.

### Referências do Seedance 2.0 — o diferencial subusado
`image_references` é o caminho mais confiável pra **consistência de identidade** (personagem/produto igual entre cenas) — melhor que repetir o CHARACTER BIBLE no texto do prompt. `video_references` transfere movimento/ritmo de um clipe existente. Use antes de tentar resolver consistência só na descrição.

### Modelos que a skill não cobria (avaliar caso a caso)
- **`cinematic_studio_3_0`** — 4–15s, até 4K, `genre` (action/horror/comedy/noir/drama/epic). Forte pra B-roll cinematográfico sem fala.
- **`wan2_7`** — 2–15s, áudio sincronizado + consistência de personagem, aceita `audio_references`.
- **`gemini_omni`** — 4–10s, `image_references` + `video_references`. É o motor da skill `gemini-omni`, agora chamável direto por MCP em vez de colar no app.

### Regra de custo pra B-ROLL
B-roll não precisa de áudio nativo (a trilha e a fala vêm da timeline). **Sempre desligar o áudio** — `generate_audio: false` no Veo/Seedance, `sound: 'off'` no Kling. Testar o prompt no Mini/Lite antes de rodar o lote no modelo caro.

Cadência: natural ≈ 2.5 palavras/s; 1.25x ≈ 3.1 palavras/s.
- 8s natural ≈ 20 pal | 8s a 1.25x ≈ 25 pal
- 10s natural ≈ 25 pal | 10s a 1.25x ≈ 31 pal
- 15s natural ≈ 37 pal | 15s a 1.25x ≈ 46 pal

---

## VEO 3.1

Formato de 5 partes, fala dentro do Action, `(no subtitles...)` obrigatório no fim.
Veo NÃO tem campo negativo: descreva ausências de forma positiva dentro do Style.

```
Cinematography: [enquadramento, câmera, 9:16 ou proporção da imagem, micro-shake ou estático]
Subject: [identidade exata da imagem; "keep her exact identity from the source image"]
Action: [expressão + gesto ancorado em palavras + buffer de silêncio + boca + ela fala: "..." (no subtitles, no captions, no on-screen text)]
Context: [cenário, objetos do quadro, tudo estável e sem distorção]
Style & Ambiance: [luz, textura de pele real, ritmo/velocidade, boca contida, anti-texto, anti-voz-extra, anti-hmm, blinks naturais, ambiente]
```

Buffer de silêncio (Veo): "She holds for a brief silent beat of about half a second before speaking... after the line she stays silent for the rest of the clip."

Anti-texto (no Style): "Absolutely no text on screen: no subtitles, no captions, no titles, no overlays, no watermark. A completely clean frame with zero text anywhere."

Anti-voz-extra (no Style): "Only the main avatar's voice. No second voice, no interviewer, no off-screen voice, no 'yeah', no 'mm-hmm', no reactions from anyone else."

Cuidado FAL/422: evitar aspas duplas (usar simples), travessões longos (—) e reticências (…) no payload.

---

## KLING V3 (3.0)

Blocos rotulados. Tem campo `[Negative]` — use-o, é onde o Kling mais obedece.

```
[Subject] [identidade exata da imagem]
[Setting] [cenário, objetos, estável]
[Action timeline]
- Seconds 0-X: [silêncio inicial ~0.5s + expressão]
- ...: [gestos/ênfase ancorados, gesto no fígado/barriga quando citado]
- ...: [fecho + ~0.5s de silêncio final]
[Camera] [estático/locked, sem zoom; proporção da imagem]
[Style] [luz, textura real, boca contida, idoso se aplicável]
[Audio]
[Avatar voice, tom, ritmo]: "fala com pronúncia fonética"
Ambient: [room tone]. Only the avatar's voice — no second voice, no 'yeah', no 'uhum', no host.
[Negative] slow speech, sluggish pacing, long pauses, second voice, interviewer voice, yeah, uhum, mm-hmm, subtitles, captions, on-screen text, smiling perfectly, plastic skin, exaggerated mouth, wide mouth opening, warping hands, extra fingers, moving background, [+ específicos da cena]
```

Lip-sync: se o áudio for anexado à parte (Kling Avatar), o `[Audio]` guia tom/ritmo e o motor sincroniza; a intensidade do gesto segue a energia do áudio.

---

## SEEDANCE 2.0

Estrutura em prosa por blocos: Subject / Action / Camera / Style / Audio + Negative prompt.

```
Subject: [identidade exata da imagem]
Action: [timeline de beats, gestos ancorados, gesto no fígado/barriga quando citado, buffer de silêncio]
Camera: [estático ou handheld micro-shake; proporção da imagem]
Style: [iPhone/UGC ou cinematográfico conforme cena; textura real; boca contida; idoso se aplicável]
Audio: [voz do avatar, tom, ritmo; pronúncia fonética; só a voz do avatar, sem voz extra]
```
Negative prompt (campo separado): plastic skin, exaggerated mouth, second voice, yeah, uhum, subtitles, captions, on-screen text, warping hands, moving background, [+ específicos].

Observações Seedance:
- JSON/FAL: usar aspas simples na fala evita erro 422.
- Clipes de 15s artefatam mais boca/mão; preferir 5–8s quando possível.
