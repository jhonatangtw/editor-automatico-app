# Referência — Prompt para Google Flow / Veo 3.1

Veo 3.1 é o modelo padrão dentro do Google Flow (2026). Use estas regras ao
escrever o campo `PROMPT FLOW` de cada bloco.

## Índice
1. Estrutura básica de um prompt de vídeo
2. Regras de ouro
3. Áudio nativo
4. Consistência entre blocos (@assets, @me, start/end frame)
5. Tipos de bloco e como prompta cada um
6. Exemplos prontos

---

## 1. Estrutura básica

Veo interpreta a ordem **literalmente** — o que vem primeiro recebe mais peso.
Monte cada prompt nesta sequência:

```
[SUBJECT] → [SETTING] → [LIGHT] → [CAMERA/MOVEMENT] → [STYLE/MOOD]. [AUDIO em frase separada]
```

- **Subject** — quem/o quê está em cena (descreva de forma concreta e específica).
- **Setting** — ambiente, contexto, props relevantes.
- **Light** — qualidade e direção da luz (golden hour, hard light, neon, etc.).
- **Camera/Movement** — tipo de plano + movimento ("slow dolly-in", "handheld
  push", "static medium shot"). Descreva o **resultado visual**, não a técnica de
  software.
- **Style/Mood** — registro estético (cinematic, editorial, UGC, documental, 3D).
- **Audio** — em frase própria (ver seção 3).

Alternativa: framework **SCAM** (Subject, Composition, Action, Mood) — útil quando
o movimento/ação é o ponto central.

## 2. Regras de ouro

- **Comprimento**: 30–80 palavras; alvo ideal **50–60**. Específico o bastante
  para cobrir os 4 elementos, curto o bastante pro modelo parsear tudo.
- **Inglês** rende mais consistência no Veo — escreva os prompts em EN, mesmo que
  o vídeo-fonte seja PT.
- **Duração do clipe**: 8–10s por geração. Como os blocos são ~10s, **um bloco =
  um clipe Veo**.
- **Um conceito por prompt.** Não empilhe 3 cenas num prompt só — vira ruído.
- **Itere mudando 1 elemento por vez.** A primeira geração é ponto de partida.
- Evite jargão de editor ("keyframe scale em After Effects"); descreva o que se vê
  ("the frame scales inward rapidly").

## 3. Áudio nativo

Veo 3.1 gera áudio sincronizado nativo. **Se você não mencionar áudio, pode vir
mudo.** Sempre termine com uma frase de áudio descrevendo ambiente sonoro, foley
ou música — ex.: "Audio: soft ambient room tone with subtle paper rustle." Para
B-roll que vai entrar SOB a narração original do vídeo, peça áreas sonoras
neutras/sem fala: "Audio: ambient texture only, no dialogue."

## 4. Consistência entre blocos

O vídeo inteiro precisa parecer uma peça só. Dentro do Flow:
- `@nome-do-asset` referencia um personagem/elemento já criado no projeto — mantém
  consistência sem reenviar imagem.
- `@me` usa o avatar pessoal.
- **Start/End frame (S/E)** e **Image-to-Video (I2V)**: para encadear blocos com
  continuidade, use o último frame de um bloco como start frame do próximo.
- Defina uma **LINHA VISUAL** no topo (paleta, lente, grade de cor, registro) e
  repita os mesmos descritores de luz/estilo em todos os prompts.

## 5. Tipos de bloco

- **B-roll** — imagem que ilustra literalmente ou metaforicamente a fala. Prompt
  cinematográfico completo (subject→setting→light→camera). Áudio neutro.
- **Motion design** — gráfico/abstrato/tipografia animada (números, setas, fluxo,
  partículas). Descreva movimento e estética do grafismo; fundo limpo se for
  entrar como overlay.
- **Overlay/Lettering** — quando a tradução visual é texto na tela, não vídeo
  gerado. Aqui o "prompt" é a instrução de lettering (palavra-chave, ênfase,
  posição), não um prompt Veo.
- **Stock/Real** — quando faz mais sentido footage real do que geração. Sinalize
  e dê termos de busca em vez de prompt Veo.

## 6. Exemplos prontos

**Fala:** "Seu intestino é o segundo cérebro do corpo."
**Tipo:** B-roll (metáfora)
**Prompt Flow (Veo 3.1):**
> Anatomical 3D render of a human gut gently glowing with soft blue neural light,
> faint synapse-like sparks traveling along the intestinal walls, dark clean
> medical-studio background. Soft volumetric rim light from the left. Slow
> macro dolly-in, shallow depth of field. Cinematic, photoreal, premium DTC ad
> look. Audio: low ambient hum, no dialogue.

**Fala:** "Em 30 dias os resultados aparecem."
**Tipo:** Motion design
**Prompt Flow (Veo 3.1):**
> Minimal animated calendar on a clean off-white background, pages flipping
> quickly from day 1 to day 30, a thin green progress bar filling left to right,
> soft drop shadows, premium fintech-style motion graphics. Static centered
> framing. Crisp, modern, high-contrast. Audio: subtle UI ticks, no dialogue.

**Fala:** "Eu estava cansado o tempo todo." (talking head já na tela)
**Tipo:** B-roll de apoio (não competir com o rosto)
**Prompt Flow (Veo 3.1):**
> A tired woman in her 40s slumped on a sofa in a dim living room at dusk, warm
> low window light, muted desaturated palette, slight haze. Static medium shot,
> shallow focus, subtle handheld drift. Naturalistic, documentary, emotional.
> Audio: quiet room tone, distant city ambience, no dialogue.
