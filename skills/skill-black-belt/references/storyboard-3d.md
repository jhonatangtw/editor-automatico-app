# MODO STORYBOARD 3D — Character VSL para TikTok Shop

Transforma uma **copy** (ou apenas um **produto/nicho**) num **storyboard completo cena a cena**, no formato viral do TikTok Shop: personagem 3D antropomórfico (estilo Pixar/Disney) que conduz uma VSL comprimida, com troca constante de cenário, legenda karaokê palavra-por-palavra, fake UI nativa e disclaimer de compliance fixo.

O entregável central de cada cena é um **prompt de imagem pronto pra gerar** (Nano Banana Pro / Seedance / Higgsfield). Cada cena também traz locução, legenda na tela e nota de animação (que pode ser expandida com o MODO EFFECTS ou gerada via Higgsfield MCP — ver `higgsfield-execution.md`).

## A pegada do formato (o que torna isso viral)

1. **Hook de roubo de atenção, não de beleza.** Os primeiros 1–2s são um pattern interrupt: close extremo, distorção, movimento exagerado, personagem grotesco-fofo. Não é "bonito", é *scroll-stopping*.
2. **Personagem-mascote como fio condutor.** O MESMO personagem em todas as cenas, costurando cenários diferentes. É o que dá coesão e torna o formato escalável (troca produto/nicho, mantém personagem).
3. **Churn de cenário.** Cada 3–8s o ambiente muda (academia → quarto → dentro do corpo → praia → produto). Novidade constante = Hold Rate alto mesmo em 30–60s.
4. **Native disguise.** Fake UI do TikTok (logo + @handle) queimada no vídeo. Parece repost orgânico e serve de marca d'água.
5. **Legenda karaokê palavra-por-palavra.** Centralizada, com @handle embaixo. Prende o olho no centro.
6. **Arco de VSL comprimido.** Hook → identificação → problema → mecanismo → prova → produto + CTA. Uma carta de 30min em 30–60s.
7. **Compliance à vista.** Disclaimer ("Resultados podem variar. Consulte um médico.") fixo no rodapé.

## Os dois modos de entrada

### Modo A — Só o produto / nicho
1. Primeiro **escreva a copy/roteiro** seguindo o arco de VSL comprimido (30–60s de locução).
2. **Confirme o ângulo com o usuário** em 1–2 linhas antes de gerar tudo ("Vou pela dor de cansaço/baixa energia, mecanismo de óxido nítrico — fecha?"). Proponha e siga, não interrogue.
3. Depois rode o storyboard.

### Modo B — Copy pronta
1. **Não reescreva a copy** (a menos que peçam).
2. **Segmente a copy em beats** (`beat-framework.md`) e mapeie cada segmento numa cena.
3. Rode o storyboard.

## Passo a passo

### 1. Trave o CHARACTER BIBLE (passo mais importante)
A consistência do personagem entre cenas faz ou quebra o criativo. Defina um **bloco fixo** descrevendo o mascote e **embuta esse bloco literalmente no início de TODO prompt de imagem**.

- Imagem de referência enviada → descreva-a fielmente e instrua o uso como referência na geração.
- Sem personagem → proponha um que case com o nicho (esqueleto fitness pra energia; órgão antropomórfico pra saúde intestinal). Trave faixa/acessório/cor como assinatura.

Exemplo:
> **CHARACTER BIBLE (copiar em todo prompt):** An anthropomorphic 3D cartoon skeleton, Pixar Disney style, bones inside a glossy translucent rubbery transparent skin, big expressive googly cartoon eyes with bright blue irises, wearing a signature green athletic sweatband headband, photorealistic 3D render with subsurface scattering on the translucent skin.

### 2. Defina o SISTEMA VISUAL PERSISTENTE
Elementos que se repetem na peça inteira (camada de edição — não vão no prompt de imagem, mas o editor precisa saber):
- **Formato:** vertical 9:16.
- **Render look:** Pixar/Disney 3D fotorrealista, subsurface scattering, global illumination, soft shadows, 4K.
- **Legenda karaokê:** palavra por palavra, centralizada, branca com contorno, @handle embaixo.
- **Fake UI nativa:** logo TikTok + @handle no canto.
- **Disclaimer fixo:** rodapé, fonte pequena, o tempo todo.

### 3. Mapeie a copy nos beats
Quebre a locução nos beats (`beat-framework.md`). Cada beat vira uma ou mais cenas. **A copy manda no ritmo** — não force 7 cenas se a copy tem 4 beats. Para cada trecho, escolha a **tradução visual** mais forte usando `biblioteca-visual.md`.

### 4. Gere o storyboard — FORMATO DE SAÍDA OBRIGATÓRIO

Comece com CHARACTER BIBLE + SISTEMA VISUAL PERSISTENTE. Depois, cada cena:

```
CENA [N] — [função do beat] (≈[timestamp])
• LOCUÇÃO: "[trecho da copy]"
• LEGENDA (karaokê): [palavra(s)-chave na tela]
• TRADUÇÃO VISUAL: [cenário, ação do personagem, enquadramento]
• PROMPT DE IMAGEM:
[prompt completo em inglês, começando com o CHARACTER BIBLE, pronto pra colar]
• ANIMAÇÃO: [movimento + câmera; se houver fala, marcar lip-sync em português]
```

Feche com **CTA / próximo passo** (ex.: "Cena final emenda com close do produto real + seta vermelha + 'compra no link'").

## Framework de beats (resumo — detalhe em `beat-framework.md`)

1. **HOOK / Pattern Interrupt** — para o scroll. Close extremo + distorção + movimento.
2. **CALLOUT / Identificação** — quem é o público / estado atual.
3. **PROBLEMA / Agitação da dor** — o sofrimento visual (personagem exausto, fumaça na cabeça).
4. **MECANISMO / "Aqui está o porquê"** — a ciência. Visual interno (microbioma, células) — credibility shot.
5. **VILÃO / Choque visceral** — o que tá errado dentro (bola de toxina, placa). Grotesco e memorável.
6. **SOLUÇÃO / Prova / Aspiração** — o "depois". Transformação.
7. **PRODUTO + CTA** — quebra do 3D pro real (mão humana com o frasco), seta vermelha, "no TikTok Shop".

## Regras do prompt de imagem (cada cena)

- **Sempre começar pelo CHARACTER BIBLE** literal, depois a cena.
- **Inglês**, mesmo com copy em português (locução fica em PT no campo LOCUÇÃO).
- **Um beat = uma imagem clara.** Não empilhe duas ideias num frame.
- **Estilo técnico fixo no fim de todo prompt:** `cinematic composition, shallow depth of field, soft lighting with rim light, subsurface scattering, soft shadows, global illumination, highly detailed PBR materials, 50mm lens, f/1.8, Octane render style, ultra detailed, photorealistic lighting, 4K, vertical 9:16 format`.
- Beats de **mecanismo** e **vilão**: o personagem pode sair de cena (CGI interno do corpo) — CHARACTER BIBLE não entra, mas mantenha o look 3D fotorrealista.
- Cena de **produto/CTA**: mão humana real segurando o frasco (quebra proposital) — sem personagem. Para realismo do produto, use as técnicas de `photorealism.md`.

## Animação → vídeo

Cada cena traz nota de animação curta. Se o usuário quiser os prompts de vídeo completos, expanda cada cena com o **MODO EFFECTS** (`effects-seedance.md`) usando a imagem gerada como start frame. Cenas com fala = marcar **lip-sync em português** e sugerir voz ElevenLabs PT-BR se o timbre nativo não convencer. Para executar direto (imagem + vídeo), ver `higgsfield-execution.md`.

## Compliance (saúde / suplemento)

- Disclaimer fixo sempre.
- Prefira linguagem de **benefício e sensação** ("mais energia", "leveza") a claims médicos absolutos ("cura", "trata"). Se a copy do usuário tiver claim duro, sinalize o risco de reprovação/ban, mas respeite a decisão dele.
- Não invente ingredientes ou estudos. Produto não especificado = genérico.
