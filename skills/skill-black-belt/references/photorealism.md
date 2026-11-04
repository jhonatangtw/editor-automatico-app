# MODO PHOTOREALISM — Prompts de imagem ultrarrealista

Prompts de geração de imagem com aparência de fotografia real (Nano Banana Pro, Seedream, Midjourney, Flux, etc.). Usos principais dentro da Black Belt:
1. **Criar o START FRAME do avatar** quando o usuário ainda não tem a imagem (alimenta o modo AVATAR direto).
2. **Cena de produto/CTA** do modo STORYBOARD (a "quebra do 3D pro real").
3. Imagens realistas avulsas (image creatives, thumbnails, B-roll estático).

## Regras fundamentais

1. **Realismo fotográfico por padrão**, salvo pedido de outro estilo.
2. **Nunca** cartoon/anime/ilustração/stylized sem pedido (pra 3D Pixar, use o modo STORYBOARD).
3. **1 a 3 prompts fortes**, sem explicações longas.
4. Pedido ambíguo → **uma pergunta curta** (assunto, cena ou luz) antes de gerar.
5. Prompt já escrito pelo usuário → melhore preservando a intenção.
6. Linguagem visual concreta — nada de "beautiful", "amazing", "stunning", "perfect skin".

## Estrutura do prompt (incluir quando fizer sentido)

**Técnica fotográfica:** câmera (Sony A7R V, Canon EOS R5, Hasselblad X2D, Leica M11), lente (85mm f/1.4, 35mm f/2, 50mm f/1.2), abertura, ISO, obturador.

**Luz e ambiente:** tipo (natural, estúdio, rembrandt, split, golden hour, overcast), hora do dia, localização/clima.

**Composição e estética:** regra dos terços, close-up, full body, POV; profundidade de campo (shallow DOF, bokeh); color science (Kodak Portra 400, Fuji Superia, cine-grade, teal & orange, desaturated mids).

**Detalhes físicos (pessoas):** assimetria facial natural, textura de pele realista, fios de cabelo individuais, microdetalhes de olhos e lábios, textura de roupas.

## Frase final OBRIGATÓRIA (pessoas/rostos/pele visível)

Todo prompt com pessoa/rosto/pele DEVE terminar EXATAMENTE com:

```
visible pores, micro-texture, natural skin imperfections, subtle peach fuzz, natural skin sheen, no airbushing, no smoothing filters
```

**Nunca modifique essa frase.** Último elemento do prompt, sem adições ou cortes.

## Start frame de avatar (uso mais comum na Black Belt)

Ao criar a imagem-base de um avatar UGC/VSL, além das regras acima:
- Defina **proporção** conforme o destino (9:16 pra UGC vertical — declare no prompt).
- Descreva a **pose pensando no vídeo**: mãos visíveis e em posição estável (colo, volante, mesa), olhar pra câmera, boca fechada e relaxada (o vídeo nasce melhor de boca fechada).
- Formato selfie → enquadramento de câmera frontal de celular, braço do celular fora do quadro.
- Look UGC: luz natural imperfeita, textura de câmera de celular ("shot on iPhone front camera" quando couber), cenário crível (carro estacionado, quarto, cozinha).
- Idosos: descreva sinais de idade honestos (rugas, manchas, cabelo grisalho ralo) — nada de pele lisa.
- Depois de gerada/aprovada, siga pro modo AVATAR do SKILL.md (a análise da imagem extrai identidade/cenário/pose de lá).

## Exemplos

### Retrato (ambiente urbano)
```
Candid portrait of a woman in her early 30s walking through a rain-wet Lisbon street at blue hour, shot on Sony A7R V with 85mm f/1.4 lens, f/1.8, ISO 800, 1/250s. Rembrandt lighting from a shopfront window casting warm amber on her left cheek. Shallow depth of field, cobblestone street blurred into soft bokeh. She wears a slightly damp olive wool coat, individual threads visible. Asymmetric face, sparse eyebrow hairs, slightly chapped lips. Hair strands catching the ambient streetlight. Kodak Portra 800 color science, desaturated shadows, warm mids. visible pores, micro-texture, natural skin imperfections, subtle peach fuzz, natural skin sheen, no airbushing, no smoothing filters
```

### Produto (sem pessoas)
```
Commercial product photography of a matte black espresso cup on a worn concrete counter, shot on Hasselblad X2D with 120mm macro lens, f/8, ISO 100, 1/200s. Soft north-facing window light creating a single directional shadow. Steam rising gently from the cup. Ultra-sharp detail on the ceramic surface — micro-scratches, matte finish variation, condensation ring on the concrete. Teal and orange color grade, slightly lifted blacks. Clean minimal composition, copy space on right.
```

### Paisagem / arquitetura
```
Wide angle shot of an abandoned industrial warehouse interior, Detroit, winter morning. Shot on Canon EOS R5 with 16-35mm f/2.8 at 16mm, f/8, ISO 200, 1/60s. Diffused gray overcast light through broken skylights, dust particles suspended in light beams. Crumbling concrete floor with puddles reflecting the ceiling structure. Rust patterns on steel beams, peeling paint layers, broken glass. Desaturated palette with cold blue-gray tones. Architectural photography, sharp throughout.
```

## Linguagem

**Prefira:** "natural window light from the left", "visible individual hair strands", "worn leather texture with micro-cracks", "slightly asymmetric jawline", "bokeh from 85mm at f/1.4".

**Evite:** "beautiful lighting", "stunning portrait", "amazing details", "perfect skin", "gorgeous".

## Fluxo

1. Identifique assunto, cena, estilo, presença de pessoas.
2. Ambíguo → UMA pergunta curta.
3. Gere 1–3 prompts (variando composição/luz/mood).
4. Pessoas/pele? → frase obrigatória no fim de cada prompt.
5. Entregue direto, sem explicar o que fez.
