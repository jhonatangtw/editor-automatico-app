---
name: conferir-ads-por-frame
description: >-
  QA (conferência) de criativos de vídeo / ADs já prontos, no terminal — visual, legenda na tela,
  qualidade de imagem, consistência de avatar/criador, b-roll, compliance/IP, coerência com a copy
  E fala (transcrição). Roda uma CLI (scripts/conferir.py) que extrai FRAMES + MOSAICO de cada
  vídeo via ffmpeg, roda checks automáticos e gera um relatório HTML. Use SEMPRE que o usuário
  tiver vídeos/ADs prontos numa pasta e pedir para "conferir os ADs", "checar meus criativos",
  "revisar os vídeos", "confere esse anúncio", "QA dos criativos", "verificar visual e legenda",
  "conferir antes de subir pro Meta/TikTok", "revisar os hooks", ou apontar uma pasta/arquivo de
  vídeo pedindo revisão. Serve para 1 vídeo ou pastas com dezenas (AD01, AD02..., hooks H1/H2/H3).
  NÃO é para GERAR criativos/prompts (isso é a skill-black-belt / avatar-vsl) — esta CONFERE
  material já exportado. Roda 100% local (terminal do VSCode): a transcrição da fala funciona aqui.
allowed-tools: Bash, Read, Glob, Grep, Write
---

# Conferir ADs por frame (terminal / local)

Fluxo de QA para revisar criativos de vídeo já exportados **sem assistir cada um**, rodando local
no terminal (ex.: terminal integrado do VSCode). A ideia central: **um vídeo de anúncio é uma
sequência de decisões visuais + legenda + fala.** Dá pra auditar a maior parte disso olhando um
**mosaico de frames bem amostrados** + os **checks automáticos** + a **transcrição**, o que é
ordens de magnitude mais rápido do que assistir.

> Este é o ambiente **local** (Claude Code no terminal). Diferente do Cowork na nuvem: os arquivos
> estão direto no disco (bash normal, sem device bridge), e a **transcrição da fala FUNCIONA**
> aqui porque há rede pra baixar o modelo Whisper. Não há `SendUserFile` — os relatórios são
> arquivos em disco que o usuário abre.

## Quando esta skill se aplica
O usuário tem **material pronto** (mp4/mov exportado) numa pasta e quer saber se está **ok pra
subir**: erro de imagem, legenda errada/typo, arquivo corrompido, avatar inconsistente, b-roll
problemático, risco de compliance no Meta/TikTok, coerência com a copy, bug de fala. Se o pedido
for **criar/gerar** vídeo ou prompts, esta NÃO é a skill certa.

---

## Passo 1 — Rodar a CLI (faz o pesado sozinha)
O motor é `scripts/conferir.py` (fica ao lado deste arquivo, em
`~/.claude/skills/conferir-ads-por-frame/scripts/conferir.py`). Rode apontando pra pasta dos
vídeos:

```bash
python3 ~/.claude/skills/conferir-ads-por-frame/scripts/conferir.py "<PASTA_DOS_VIDEOS>" \
  --formato 9:16 --min-largura 1080 --ocr --idioma por
```

A CLI: lê metadados (duração, resolução, formato, fps, áudio), roda os **checks automáticos**
(🔴 QUEBRADO, RESOLUCAO, FORMATO, SEM_AUDIO/SILENCIO; 🟠 FRAME_PRETO, CONGELADO, DURACAO), gera o
**mosaico com timecode** de cada vídeo, faz **OCR da legenda** (`--ocr`) e escreve em `<PASTA>/_QA/`:
`relatorio.html` (dashboard auto-contido), `relatorio.md` (resumo acionável), `montage/*.jpg`,
`audio/*.mp3`, `dados.json`.

Flags úteis: `--formato 9:16,1:1` ou `qualquer`; `--min-largura`, `--min-dur`, `--max-dur`;
`--frames N`; `--jobs 4` (paralelo, mais rápido); `-o <saida>`; `--copy copy.txt`.

**Requisitos** (uma vez): `ffmpeg` obrigatório; `tesseract` + idioma pra `--ocr`; `pillow`.
Se faltar algo, ver `references/setup.md` e instalar antes.

## Passo 2 — Transcrever a fala (opcional, FUNCIONA no local)
Diferente da nuvem, aqui a transcrição roda. Adicione `--transcrever`:

```bash
pip install faster-whisper --break-system-packages   # 1ª vez
python3 ~/.claude/skills/conferir-ads-por-frame/scripts/conferir.py "<PASTA>" \
  --ocr --transcrever --modelo small --idioma por
```

Gera `_QA/transcripts/<AD>.txt` (com timestamps) e embute a transcrição no `relatorio.html`. Use
pra: comparar **fala × copy**, achar **bugs de fala** (repetição/loop já é sinalizado; fala
corrida, corte da 1ª palavra e voz dupla saem dos gaps/repetições nos segmentos). Modelos:
`tiny.en`/`base.en`/`small.en` (inglês limpo), `small`/`medium` (multilíngue, PT). **Sincronia
labial fina** ainda precisa assistir — seja honesto sobre isso no relatório.

## Passo 3 — Olhar os mosaicos (camada subjetiva)
A CLI resolve o **objetivo**; a parte **subjetiva** é você/Claude olhando. Leia cada mosaico com o
**Read (visão)** a partir de `<PASTA>/_QA/montage/*.jpg` e anote por AD:
- qualidade de imagem e artefatos; consistência do avatar entre os frames;
- **texto da legenda** e estilo; se o avatar/criador do HOOK é o mesmo do corpo;
- b-roll: pessoas de "antes/depois" que não são quem fala; marcas, celebridades, personagens,
  telas de app/idioma; claims na tela.

**Regra de ouro — verifique antes de acusar typo.** Legenda karaokê anima letra por letra; um
frame pode pegar o texto no meio da animação e parecer erro (ex.: "GLICK" que é "CLICK" entrando).
Antes de reportar erro de texto, extraia 2–3 frames em alta ao redor daquele momento (crop na
faixa da legenda) e confirme:
```bash
ffmpeg -ss <t> -i "<video>" -frames:v 1 -vf "crop=in_w:in_h/4:0:in_h*0.6,scale=640:-1" -q:v 2 out.jpg
```

## Passo 4 — Copy × vídeo
Se o usuário tiver a **copy oficial**, leia-a (arquivo local, Google Doc, etc.) e compare com a
legenda (OCR) e a fala (transcrição). Separe claramente:
- **Erro de execução** (typo, corte, pessoa errada, flip/espelhamento, resolução, arquivo quebrado)
  → responsabilidade da edição, **corrigir**.
- **Decisão de copy** (menções a Ozempic/Mounjaro/GLP-1, claims fortes) que **já estão na copy** →
  não é "erro", mas continua sendo **risco de compliance** no Meta/TikTok — sinalize como risco.

## Passo 5 — Relatório final
A CLI já entrega `relatorio.html` e `relatorio.md`. Some a isso o que você viu nos mosaicos e na
copy, e diga ao usuário para abrir o HTML:
```bash
open "<PASTA>/_QA/relatorio.html"      # macOS
```
Estrutura do resumo (ordene por urgência, seja específico: qual AD, qual hook, qual segundo):
```
# Conferência de ADs — <projeto> (<data>)
Escopo: <n vídeos, n ADs, hooks>. Método: CLI (checks + mosaico + OCR [+ transcrição]) + revisão visual.
> Ressalva: o que NÃO deu pra checar 100% (ex.: lip-sync fino).

## 🔴 Crítico — reexportar/corrigir   (arquivo quebrado, flip, resolução baixa, typo confirmado)
## 🟠 Compliance / IP                  (celebridade, marca, personagem, remédio, claim agressivo)
## 🟡 Consistência de criador / b-roll (hook ≠ corpo, antes/depois de outra pessoa, idioma vazando)
## ✅ Legenda / o que passou OK
## Resumo por AD  (tabela: AD | Visual | Legenda | Fala | Atenção)
```

---

## Convenção de nomes
O rótulo de cada card sai do **nome do arquivo/pasta**, não da ordem: `AD01`, `AD 02`,
`.../AD03/video.mp4`, e o hook de `HOOK1` / `H1` / `..._H2.mp4`. Nomeie assim que os cards saem
certinhos (`AD01_H1`, `AD02_H3`...).

## Notas de execução
- Se `python3` reclamar de módulo faltando (`PIL`, `faster_whisper`), instale com
  `pip install ... --break-system-packages` (ver `references/setup.md`).
- `--jobs` acima de 1 acelera pastas grandes, mas usa mais CPU; comece com `--jobs 4`.
- A pasta `_QA/` pode ser apagada depois; recriar é barato.
