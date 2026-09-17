# Sintaxe por modelo

## Limites de duração (confirmar sempre, mudam com versões)
- **Veo 3.1**: ~8s por geração. Áudio/fala nativa. (Veo 3.1 Lite costuma gerar com áudio também.)
- **Kling V3 (3.0)**: ~10s nativo; 15s pode exigir extend.
- **Seedance 2.0**: até ~15s; ponto ótimo de movimento 5–8s (clipes longos artefatam mais).

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
