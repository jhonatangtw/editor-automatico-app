# MODO EFFECTS — Shot-by-shot para Seedance 2.0 (sem avatar falante)

Constrói prompts de vídeo cinematográficos, shot a shot, a partir de um brief criativo. Usar para: brand films, B-roll, product videos, sequências de efeitos, e para **animar cenas do MODO STORYBOARD** (imagem gerada = start frame). NÃO usar para avatar falante — isso é o modo principal do SKILL.md.

Antes de gerar, leia `effects-breakdown-reference.txt` para calibrar o nível de detalhe.

## Input

O brief pode ser simples ("um corredor num estádio, estilo Nike") ou detalhado (storyboard completo). Pode incluir: sujeito, cenário, mood, marca/produto, efeitos desejados, duração, referências visuais, paleta. Se for vago demais, faça UMA pergunta focada — não interrogue; decida criativamente onde o usuário não especificou.

## Output — SEMPRE as 4 seções, nesta ordem

### Seção 1: SHOT-BY-SHOT EFFECTS TIMELINE (o núcleo)

```
SHOT [N] ([timestamp]) — [Nome / Descrição do shot]
• EFFECT: [efeito primário] + [efeitos empilhados]
• [O que acontece visualmente]
• [Câmera — ângulo, movimento, lente]
• [Velocidade/timing]
• [Como conecta com o próximo shot — tipo de transição]
```

Regras:
- Cada shot 1–4s, salvo holds intencionais.
- Nomeie efeitos com precisão: "speed ramp (deceleration)", não "speed ramp"; "digital zoom (scale-in)", não "zoom".
- Efeitos empilhados: liste todos explicitamente.
- Transições têm lógica de saída/entrada entre shots.
- Descreva o resultado visual, não a técnica de software ("the frame scales inward rapidly", não "keyframed scale no After Effects").
- Marque o shot mais impactante: "This is the SIGNATURE VISUAL EFFECT".
- Slow motion com percentual ("approximately 20-25% speed").
- Motion blur, comportamento de luz e atmosfera quando relevante.

### Seção 2: MASTER EFFECTS INVENTORY
Lista numerada de cada efeito distinto: nome, quantas vezes usado, em quais shots, papel no edit. Agrupe por categoria (speed manipulation, camera movement, digital effects, transitions, compositing, optical effects).

### Seção 3: EFFECTS DENSITY MAP
Segmentos de ~3–6s classificados:
- **HIGH DENSITY** — 4+ efeitos empilhados ou rapid-fire
- **MEDIUM DENSITY** — 2–3 efeitos
- **LOW DENSITY** — 1 efeito ou footage limpa

```
[range] = [DENSIDADE] ([efeitos] — [count] effects in [duração])
```

### Seção 4: ENERGY ARC
Arco de energia em atos (2–4 conforme a duração): abertura (como agarra atenção), desenvolvimento (momentos assinatura), resolução (como fecha). A energia PRECISA resolver — o final tem que parecer intencional.

## Princípios criativos

1. **Contraste gera impacto.** Alterne alta e baixa densidade. Slow-motion depois de speed ramp bate mais forte que dois ramps seguidos.
2. **Momentos assinatura.** Todo vídeo tem ao menos um "hero effect" — chame explicitamente.
3. **Transições são shots.** Whip pan, bloom flash, motion blur smear — momentos criativos, não conectores descartáveis.
4. **Especificidade.** "The frame rotates clockwise by approximately 15-20°" > "the camera tilts".
5. **Energia resolve.** O fim não pode parecer que o orçamento de efeitos acabou.

## Tom

Direto, técnico — notas de diretor, não brief de marketing. Bullets dentro de cada shot. Sem hype ("stunning", "breathtaking").

## Calibração de duração

- **5–10s**: 4–7 shots, 1 signature effect
- **10–20s**: 8–14 shots, 1–2 signatures
- **20–30s**: 12–20 shots, arco de 3 atos, 2–3 signatures
- **30+s**: escale mantendo o contraste de densidade
- Sem duração especificada → 15–20s.

Nota Seedance: clipes de 15s artefatam mais; ponto ótimo de movimento 5–8s. Para execução via Higgsfield MCP, ver `higgsfield-execution.md`.
