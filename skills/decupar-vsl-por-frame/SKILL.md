---
name: decupar-vsl-por-frame
description: Decupa uma VSL (ou qualquer vídeo longo — webinar, orgânico de YouTube, AD de referência) QUADRO A QUADRO, por plano. Detecta cada corte de cena, tira um quadro em alta de cada plano (mais quadros de cobertura nos planos longos), alinha a FALA daquele trecho (legenda .vtt/.srt, transcrição ou Whisper) e lê o TEXTO NA TELA (OCR — lettering, rótulos de capítulo, preços). Entrega folhas de contato numeradas para o Claude ler, uma página HTML interativa (player sincronizado, linha do tempo com os cortes, ampliar com setas, marcar ★ e anotar, exportar os marcados) e a tabela .md/.csv/.json. Aceita arquivo local ou link do YouTube. Use SEMPRE que pedirem "decupa essa VSL", "tira os frames da VSL", "frame por frame", "quadro a quadro", "mapa de cenas", "quais cortes/planos tem", "o que aparece na tela", "decupagem visual", "storyboard reverso", ou antes de dissecar uma VSL em vídeo (dissecador-de-vsl-atlas / bifi-funil-completo) para a dissecação enxergar o que a transcrição não mostra. NÃO é para QA de AD curto pronto para subir (use conferir-ads-por-frame) nem para cortar ou editar o vídeo.
---

# Decupar VSL por frame

A transcrição conta o que foi **dito**. A decupagem conta o que foi **mostrado**: cada
plano, cada lettering, cada rótulo de capítulo, cada preço na tela, cada troca de cenário.
Numa VSL, metade da persuasão está na imagem — e um mosaico de 18 quadros espalhados
(o que o `conferir.py` faz por padrão) perde quase tudo isso.

Esta skill amostra **por plano**, não por relógio: um quadro logo depois de cada corte,
e quadros de cobertura dentro dos planos longos (talking head parado), para nenhum
trecho ficar sem imagem.

## Passo 1 — Rodar a decupagem

```bash
SK=~/.claude/skills/decupar-vsl-por-frame
python3 "$SK/scripts/decupar.py" "<video.mp4 ou URL>" --ocr [--legenda legenda.vtt]
```

No Windows, use `python` no lugar de `python3` e `%USERPROFILE%\.claude\skills\decupar-vsl-por-frame` no lugar de `~/.claude/skills/...`.

- **Link do YouTube:** baixa o vídeo (até 720p) e a legenda sozinho (`yt-dlp`). A fala já
  vem alinhada; não precisa de Whisper.
- **Arquivo local sem legenda:** acrescente `--transcrever --modelo small --idioma eng|por`.
  Se já existir uma transcrição com `[hh:mm:ss]` no começo das linhas, passe em `--legenda`.
- **Momentos exatos que você quer ver:** `--tempos "0:35,1:01,23:54"` (somam aos cortes).
- **Vídeo com pouco corte (avatar, talking head):** `--cobertura 6` aperta a amostragem.
- **Cortes demais ou de menos:** `--sensibilidade 1.5` (pega mais) / `0.7` (pega menos).
- **Só por relógio:** `--modo intervalo --intervalo 5`.

Tempo de referência: VSL de 31 min em 720p → ~1 min (282 cortes, 353 quadros, com OCR).

Saída em `<video>_DECUPAGEM/` (ou `-o pasta`):

| Arquivo | Para quê |
|---|---|
| `folhas/folha_NN.jpg` | **O que o Claude lê.** 20 quadros por folha, com `#n`, timecode e motivo (CORTE amarelo · COBERTURA cinza · TEMPO azul) |
| `decupagem.md` | Tabela `# · timecode · motivo · fala do trecho · texto na tela` — leia junto com as folhas |
| `decupagem.html` | Página interativa para o usuário (ver Passo 4) |
| `decupagem.json` / `.csv` | Dados completos, para outra skill ou planilha |
| `frames/` | Quadros em alta (`0005_00m06s.jpg`) — para ampliar um detalhe |

## Passo 2 — Ler as folhas (a camada de julgamento)

Leia `folhas/folha_01.jpg`, `folha_02.jpg`… **em ordem**, com o `decupagem.md` ao lado.
Para cada trecho, anote o que a fala não conta:

- **Ambientes e formato:** quantos cenários existem (estúdio, campo, escritório, chamada
  de vídeo) e como alternam. Mudança de ambiente costuma marcar mudança de bloco.
- **Lettering e rótulos:** títulos de capítulo, nomes de mecanismo na tela, números
  gigantes, "OBJECTIVE"/HUD, lower thirds. **Compare o nome na tela com o nome falado** —
  quando divergem, o nome chiclete enfraquece.
- **Prova visual:** documentos, gráficos, preços, contadores, depoimentos com rosto
  pixelado, antes/depois, selos.
- **CTA visual:** botão de inscrição, link, seta, card de oferta — mesmo sem fala.
- **Ritmo:** planos por minuto em cada trecho (dá para contar pelos `#n` × timecode).

**Regra de ouro — confira antes de afirmar.** Contador animado, legenda karaokê e
transição pegam o quadro "no meio". Antes de dizer que um número ou texto está errado,
amplie o quadro em `frames/` ou rode de novo com `--tempos` em volta do momento.
(Caso real: um contador parecia mostrar "$21,2 bi" contra "$22,7 bi" falado — o quadro
assentado do plano mostrava "$22,700,000,000".)

O OCR é **pista, não prova**: ele acha rótulos e números rápido (busca na página), mas
erra letra estilizada. O que vale é o que você vê no quadro.

## Passo 3 — Usar na dissecação

Quando a decupagem alimenta o `dissecador-de-vsl-atlas` ou o `bifi-funil-completo`:

- Cite o quadro como evidência visual: "**(quadro #15, 01:01)** lista de missões estilo
  videogame". Fica rastreável na página e na pasta `frames/`.
- Os 3 lugares onde a imagem mais muda a dissecação: **Formato** (ambientes e linguagem
  visual), **Credibilidade/Provas** (o que é mostrado, não só dito) e **Gimmick names**
  (rótulo na tela × fala).
- Marque como **Inferência** qualquer leitura de intenção ("parece o mapa de 1957").

## Passo 4 — Entregar a página

```bash
open "<saida>/decupagem.html"
```

O que o usuário consegue fazer nela:
- **Player sincronizado:** clicar num quadro leva o vídeo àquele ponto; **Seguir** (`F`)
  faz a lista acompanhar o vídeo tocando.
- **Linha do tempo:** cada corte é um traço (amarelo = corte, cinza = cobertura, azul =
  pedido, rosa = marcado). Passar o mouse mostra a miniatura; clicar pula.
- **Navegar:** `←` `→` quadro a quadro · `Enter` amplia · `espaço` play/pause · `/` busca.
- **Filtrar:** só cortes, só pedidos, só quadros com texto na tela, só marcados; busca na
  fala, no texto da tela e nas notas (com destaque).
- **Marcar e anotar:** `S` ou ★ marca; a caixa de nota salva no navegador.
- **Exportar:** copiar os marcados (timecode + fala + tela + nota), `.csv` dos marcados,
  ou `.json` de tudo com as notas — para mandar ao editor ou ao copy.

O vídeo é referenciado pelo caminho relativo. Se mover a pasta da decupagem para longe
do vídeo, os quadros continuam funcionando; só o player deixa de tocar.

## Requisitos

`ffmpeg` (obrigatório) · `pillow` (folhas com rótulo; sem ele saem sem texto) ·
`tesseract` (para `--ocr`) · `yt-dlp` (para link) · `numpy` (deixa a detecção de corte
~10× mais rápida) · `faster-whisper` (só para `--transcrever`). Ver `references/setup.md`.

## Notas técnicas

- A detecção de corte é feita em Python sobre o vídeo decodificado em cinza pequeno
  (4 quadros/s, 96×54), com limiar adaptativo à vizinhança. Não usa o filtro `scene` do
  ffmpeg, que falha em alguns VP9 de redes sociais.
- O quadro de cada plano é tirado 0,4 s depois do corte, para não pegar a fusão da
  transição.
- A legenda automática do YouTube repete linhas "rolando"; o leitor tira as duplicadas e
  cada trecho vai até o começo do próximo, para a fala não aparecer em dois quadros.
