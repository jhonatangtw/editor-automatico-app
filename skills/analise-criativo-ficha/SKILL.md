---
name: analise-criativo-ficha
description: >-
  Analisa criativos de vídeo (ADs/UGC/orgânicos) prontos e entrega UM relatório HTML por
  criativo no padrão "Detalhamento AD por AD": QA técnico automático (resolução, formato,
  frame preto/congelado, silêncio, duração), mosaico de frames com timestamp, resumo da
  edição, transcrição palavra-por-palavra, pontos de atenção por severidade, FICHA TÉCNICA
  DO ANÚNCIO (tipo, plataforma, nicho, formato, tom, nível de consciência, sofisticação,
  ângulo, framework, MUP, MUS, público, Deeper Core) e MAPA DE FLUXO PERSUASIVO
  (hook · corpo · close). SEM notas PONTE — é a versão de dissecação/ficha, não a de
  scorecard. Use quando o usuário pedir "analisa esse criativo", "disseca esse AD",
  "monta a ficha técnica do anúncio", "quero o relatório do criativo", "mapeia o fluxo
  persuasivo", "analisa esse orgânico validado" ou apontar um vídeo/pasta de vídeos.
  Serve para 1 criativo ou dezenas. Roda 100% local (ffmpeg + Whisper). NÃO gera criativos
  nem prompts; NÃO dá nota PONTE (para isso use analise-criativos-ponte).
---

# Análise de criativo — QA + Detalhamento + Ficha Técnica + Mapa de Fluxo

Entrega **um HTML auto-contido, tema escuro, um card por criativo**, com esta ordem fixa
dentro do card:

```
[badge]  [descrição em 1 linha + produto]
┌─ mosaico de frames ─┬─ Duração · Resolução · FPS · Áudio
│                     │  QA técnico (chips automáticos)
│                     │  Resumo da edição
│                     │  Transcrição de áudio (palavra por palavra)
│                     │  Pontos de atenção (severidade)
│                     │  Ficha Técnica do Anúncio  (13 campos)
│                     │  Mapa de Fluxo Persuasivo  (Hook · Corpo · Close)
└─────────────────────┴─
```

> **Sem seção PONTE.** Esta skill é a de **dissecação/ficha**. Se o pedido for nota 1–5
> por letra + matriz de experimentação, é a `analise-criativos-ponte`.

Ambiente **local** (Claude Code no terminal) — a transcrição funciona porque há rede pra
baixar o modelo Whisper. O relatório é um arquivo em disco que o usuário abre no navegador.

---

## Fluxo (siga em ordem)

### Passo 1 — QA técnico + frames + transcrição (a máquina faz o pesado)

```bash
python3 <skill>/scripts/conferir.py "<PASTA_DOS_VIDEOS>" \
  --formato 9:16 --min-largura 1080 --ocr --transcrever --modelo small --idioma <por|eng> --jobs 4
```

Gera `<PASTA>/_QA/` com `dados.json` (metadados + flags), `montage/*.jpg` (mosaico com
timecode), `transcripts/*.txt` (fala) e `relatorio.html` (QA cru).

Flags de check: 🔴 QUEBRADO/RESOLUCAO/FORMATO/SEM_AUDIO · 🟠 FRAME_PRETO/CONGELADO/DURACAO.

**Idioma:** detecte antes numa amostra e transcreva no idioma certo. Forçar inglês como
português (ou o contrário) embananha a fala e contamina toda a análise.

**No Claude Cowork, rode SEM `--transcrever`.** A VM do Cowork já traz o `ffmpeg` (então
QA, frames e mosaico funcionam), mas a rede é allowlist — só `pypi.org`, `registry.npmjs.org`
e `api.anthropic.com`. O `faster-whisper` instala, porém o **modelo de fala vem do Hugging
Face e o download é bloqueado**. Nesse caso peça a **copy/roteiro em texto** ao usuário
(quase sempre ele tem — é o anúncio dele) e escreva direto no campo `transcricao` do
`analise.json`. O relatório sai idêntico: a transcrição renderizada vem do JSON, não da
pasta `_QA/transcripts/`. O mesmo vale para `--ocr` (tesseract pode não existir na VM) —
não é obrigatório, e a leitura da legenda no mosaico é mais confiável que o OCR de qualquer
forma.

**Orgânico de outra marca:** se o criativo for um winner que já escalou (referência de
decupagem), rode igual — mas registre isso em `atencao` como `plain`, e diga no `produto`
que é referência, não um AD do produto do cliente.

### Passo 2 — Ler o mosaico (a camada de julgamento)

Leia cada `<PASTA>/_QA/montage/*.jpg` com o **Read (visão)** e a transcrição correspondente.
Escreva, por criativo:

- **`one_line`** — 1 frase: quem aparece, onde foi filmado, b-roll principal, textos on-screen.
- **`resumo_edicao`** — o ângulo entre aspas, como alterna talking-head × inserts × b-roll,
  e como fecha. Use `**negrito**` nos beats (funciona: o gerador converte).
- **`atencao[]`** — `{"sev": "orange|yellow|plain", "texto": "..."}`. Compliance e claim =
  laranja; execução, typo, bug de transcrição = amarelo; observação/contexto = plain.

**Regra de ouro do QA:** legenda karaokê anima letra a letra — **não** acuse typo sem
extrair 2–3 frames em alta ao redor do momento e confirmar no olho. O OCR erra aqui.

### Passo 3 — Preencher a Ficha Técnica (o que diferencia esta skill)

São 13 campos + o fluxo. **Não deixe campo vazio e não invente**: o que não estiver no
criativo, marque como inferência. O detalhe de cada campo está em
`references/ficha-campos.md` — leia antes de preencher pela primeira vez.

Resumo dos campos: `tipo`, `plataforma`, `nicho`, `formato`, `tom`, `consciencia`,
`sofisticacao`, `angulo`, `framework`, `mup` (vilão), `mus` (solução), `publico`, `deeper`
(Deeper Core), e `flow{hook, corpo, close}`.

Para a metodologia completa de dissecação, carregue a skill-irmã `dissecador-de-ads-atlas`
via `Skill` — esta aqui é a versão condensada que alimenta a ficha.

### Passo 4 — Escrever o `analise.json`

Lista, 1 objeto por criativo. O campo `name` **casa exatamente** com o nome no `_QA`
(ex.: `AD01_H1`). Schema completo no topo de `scripts/montar_relatorio.py`; exemplo real
preenchido em `references/exemplo-analise.json`.

```json
[{
  "name": "Goli_Organico",
  "badge": "Goli · Orgânico VALIDADO",
  "produto": "— Goli 3-in-1 — winner orgânico (outra marca) · molde de decupagem",
  "one_line": "...", "resumo_edicao": "...", "transcricao": "...",
  "atencao": [{"sev": "orange", "texto": "..."}],
  "ficha": { "tipo": "...", "...": "...", "flow": {"hook": "...", "corpo": "...", "close": "..."} }
}]
```

### Passo 5 — Gerar o relatório (sempre com `--sem-ponte`)

```bash
python3 <skill>/scripts/montar_relatorio.py \
  --qa "<PASTA>/_QA" --analise analise.json -o "<PASTA>" \
  --projeto "<Produto> (criativo)" --sem-ponte
```

Sai `Analise Criativos - <projeto>.html` — auto-contido, mosaico embutido em base64
(abre em qualquer máquina, sem pasta de imagens ao lado).

**`--sem-ponte` é obrigatório nesta skill.** Sem a flag, o gerador renderiza a seção PONTE
e o entregável sai fora do padrão.

### Passo 6 — Entregar

```bash
open "<PASTA>/Analise Criativos - <projeto>.html"        # macOS
start "" "<PASTA>\Analise Criativos - <projeto>.html"   # Windows
```

No chat, resuma: o ângulo de cada criativo, os achados 🔴/🟠, e — se rodou vários — qual
hook tende a ganhar e por quê.

---

## Convenção de nomes

O rótulo do card sai do **nome do arquivo/pasta**: `AD01`, `AD 02`, `.../AD03/video.mp4`;
o hook de `HOOK1` / `H1` / `..._H2.mp4`. Nomeie `AD01_H1.mp4` que os cards saem certos.
O `badge` do JSON sobrescreve, quando você quiser um rótulo falado
(ex.: `"Goli · Orgânico VALIDADO"`).

## Requisitos (o instalador resolve)

`ffmpeg` (obrigatório) · `tesseract` + idioma (para `--ocr`) · Python `pillow` e
`faster-whisper` (transcrição). Ver `references/setup.md`.

## Escopo

- **É para:** dissecar criativo pronto (mp4/mov) — o que é, como está montado, o que fala,
  onde arrisca, e qual a arquitetura persuasiva (ficha + fluxo).
- **NÃO é para:** gerar criativo/prompt; dar nota PONTE (`analise-criativos-ponte`);
  rodar o funil inteiro com VSL e copies (`bifi-funil-completo`).
