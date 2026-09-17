---
name: video-to-flow
description: Transforma um vídeo existente em um workflow de edição visual bloco a bloco para o Google Flow (Veo 3.1). Divide o vídeo em blocos de ~10s alinhados à fala, transcreve o áudio, e para cada bloco gera uma tradução visual (B-roll, motion design, overlay) com prompt pronto pro Flow. Use SEMPRE que o usuário enviar um vídeo (ou seus blocos/transcrição) e pedir para "dividir o vídeo", "criar edição visual", "gerar B-roll", "transformar a fala em imagem", "workflow visual", "roteiro de B-roll", "prompts pro Flow/Veo a partir do vídeo", ou descrever que quer ilustrar visualmente o que é falado num vídeo. Diferente do video-prompt-builder (que parte de um brief e gera prompt Seedance) — este parte de um VÍDEO REAL já gravado e mapeia a edição visual em cima da fala existente.
---

# Video to Flow

Pega um vídeo já gravado (geralmente narração/VSL/UGC com talking head) e produz
um **plano de edição visual bloco a bloco** pronto para executar no Google Flow:
para cada trecho de ~10s, o que é dito vira uma imagem/animação, com prompt Veo 3.1
pronto pra colar.

## Como esta skill funciona

O fluxo tem duas metades: **preparação mecânica** (script) e **direção criativa**
(você, lendo o resultado).

1. **Prepara o vídeo** rodando `scripts/process_video.py`. Ele corta o vídeo em
   blocos semânticos de ~10s, transcreve a fala com Whisper, extrai um frame por
   bloco, e escreve `blocos.json` + `blocos.md`.
2. **Lê `blocos.json`** e, para CADA bloco, **olha o frame** correspondente (use a
   ferramenta de visualização de imagem) e lê a fala transcrita.
3. **Gera o workflow visual** — uma entrada por bloco, no template fixo abaixo,
   com prompt pronto pro Flow.

Antes de escrever qualquer prompt Flow, leia `references/flow-veo-reference.md`
para calibrar a estrutura (Subject→Setting→Light→Camera + áudio, ~50-60 palavras,
em inglês).

## Onde isto roda

Idealmente no terminal do usuário (Claude Code na máquina dele), onde `ffmpeg` e
`whisper` estão instalados — assim a transcrição roda local sem restrição de rede.
Se rodar num sandbox sem Whisper, peça a transcrição/copy e use `--transcript`.

## Passo 1 — Preparar o vídeo

Rode (ajuste o caminho do vídeo e o idioma):

```bash
python scripts/process_video.py "CAMINHO/DO/video.mp4" -o ./saida --lang pt
```

Opções úteis:
- `--transcript copy.srt` — pula o Whisper e usa uma transcrição pronta (`.srt`,
  `.json` no formato Whisper, ou `.txt` sem timestamps).
- `--target 10 --min 6 --max 14` — alvo/limites de duração dos blocos.
- `--whisper-model medium` — mais preciso (mais lento); `small` é o padrão.
- `--no-clips` — só frames + json, sem cortar os arquivos de vídeo.

Se o script reclamar que não há backend de transcrição, oriente o usuário:
`pip install -U openai-whisper` (ou `faster-whisper`), ou fornecer `--transcript`.

Saída em `./saida/`: `blocos.json`, `blocos.md`, `blocos/bloco_NN.mp4`,
`frames/bloco_NN.jpg`.

## Passo 2 — Analisar cada bloco

Para cada bloco em `blocos.json`:
1. **Veja o frame** (`frame`) — é o que JÁ está na tela. B-roll bom complementa
   ou contrasta com isso; nunca repita o óbvio. Se já tem talking head, o B-roll é
   apoio (não pode competir com o rosto). Se já tem gráfico, reforce ou simplifique.
2. **Leia a fala** (`text`) — qual é a ideia central? Há algo concreto pra mostrar
   (objeto, número, lugar) ou é abstrato (sentimento, conceito)?
3. **Decida o tipo**: B-roll, Motion design, Overlay/Lettering, ou Stock/Real.

## Passo 3 — Gerar o workflow

ALWAYS comece com o cabeçalho de direção, depois um bloco por trecho, na ordem.

### Cabeçalho (uma vez, no topo)

```
TEMA: [do que o vídeo trata, 1 linha]
TOM: [registro emocional/comercial — ex.: DR agressivo, educativo, intimista]
PALETA: [3-4 cores/grade de cor que amarram tudo]
LINHA VISUAL: [a regra de consistência — lente, luz, estética repetida em todos os
blocos; ex.: "macro photoreal, golden rim light, fundo escuro limpo"]
DICA FLOW: [se houver personagem/produto recorrente, sugerir criar @asset no Flow
para manter consistência entre blocos]
```

### Por bloco (template fixo)

```
BLOCO NN · [mm:ss-mm:ss] ([dur]s) · bloco_NN.mp4
FALA: "[trecho transcrito]"
NA TELA: [o que o frame já mostra]
IDEIA VISUAL: [como traduzir a fala em imagem — 1-2 frases]
TIPO: B-roll | Motion design | Overlay/Lettering | Stock/Real
PROMPT FLOW (Veo 3.1): [prompt em inglês, ~50-60 palavras, Subject→Setting→Light→
Camera + frase de áudio. Para Overlay/Stock, dar instrução de lettering ou termos
de busca em vez de prompt Veo.]
CORTE: [como entra/sai pro próximo bloco — match cut, hard cut, whip, dissolve]
```

## Princípios criativos

Guie cada decisão por estes pontos:

1. **Não duplique a tela.** Se a fala diz "café" e a tela já mostra café, o B-roll
   deve ADICIONAR (origem do grão, vapor em macro, ritual), não repetir.
2. **Concreto vira literal, abstrato vira metáfora.** "30 dias" → calendário
   animado. "Sua mente fica nublada" → névoa dissipando, não um cérebro genérico.
3. **Coerência acima de variedade.** Melhor 8 blocos na mesma linguagem visual do
   que 8 estéticas diferentes. Repita luz, lente e paleta.
4. **B-roll sob narração é mudo.** Quando o áudio original (a fala) continua por
   cima, o prompt deve pedir áudio neutro/sem diálogo.
5. **Ritmo por contraste.** Alterne blocos "calmos" (talking head limpo, overlay
   simples) com blocos "cheios" (B-roll cinematográfico, motion). Não encha tudo.
6. **Hook nos primeiros 10s.** O bloco 01 é o mais importante — proponha o visual
   mais forte ali.

## Tom e estilo da saída

- Direto, técnico, como notas de direção — não copy de marketing.
- Prompts Flow sempre em inglês; o resto (fala, ideia, notas) em PT.
- Conciso e completo: cada linha do template ganha seu lugar.
- Não invente fala que não está na transcrição. Se um bloco veio sem fala
  (música/silêncio), diga "(sem fala)" e proponha o visual a partir do frame.

## Fallbacks

- **Sem áudio / só música:** os blocos vêm por tempo fixo e sem fala. Trabalhe a
  partir dos frames; sugira ritmo visual e motion alinhados à trilha.
- **Transcrição já existe (copy/VSL):** use `--transcript`. Comum no fluxo do
  usuário (HW Publishing já tem o doc de copy).
- **Rodando em sandbox sem Whisper:** peça a copy e rode com `--transcript`, ou,
  se nem isso, trabalhe só pelos frames e sinalize que faltou a fala.
- **Vídeo muito longo:** ok — o script gera quantos blocos forem necessários.
  Para entregas grandes, processe e entregue o workflow em lotes de ~10 blocos.

## Exemplo de fluxo

**Usuário diz:** "Toma esse vídeo de VSL de 2 min do JellyLean e monta a edição
visual em cima, divide em blocos de 10s."

**Você faz:**
1. Roda `process_video.py video.mp4 -o ./saida --lang pt` (ou `--transcript` se ele
   já anexou a copy).
2. Lê `references/flow-veo-reference.md`.
3. Lê `blocos.json`, vê cada `frame`, lê cada `text`.
4. Escreve o cabeçalho de direção + um bloco por trecho no template fixo, com
   prompt Veo 3.1 pronto pra colar no Flow.
5. Entrega em texto no chat (ou salva em `.md` se ele pedir arquivo).
