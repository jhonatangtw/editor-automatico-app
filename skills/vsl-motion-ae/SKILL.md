---
name: vsl-motion-ae
description: Coloca motion graphics em liquid glass, zoom in/out e B-roll gerado por IA num video de talking head (VSL, upsell, aula gravada, VTurb) usando o plugin Higgsfield no After Effects, e renderiza o MP4 final via aerender. Ancora cada elemento na fala transcrita, nao em palpite de timecode. Use quando pedirem "coloca motion nesse video", "deixa o video mais dinamico", "poe zoom in zoom out", "adiciona b-roll", "anima essa parte da fala", "liquid glass", "gel" ou apontarem uma VSL/video pronto pedindo motion. NAO e pra cortar silencio (use cortar-aula) nem pra conferir criativos (use conferir-ads-por-frame).
---

# Motion em VSL (liquid glass + zoom + B-roll) no After Effects

Pipeline que constroi motion nativo dentro do AE do usuario via MCP `ae_*`, e renderiza por fora.

## Ordem obrigatoria

1. **Transcrever o video FINAL** (o que vai receber motion, nao um corte anterior — os timecodes mudam).
2. **Conectar o AE** — `get_host_status` ate `aeft:true`. Sem isso nao ha o que fazer.
3. **Montar** comp + importar video + paineis + zoom.
4. **`ae_finalize_build`** no fim de cada rodada.
5. **Pedir Cmd+S ao usuario** — o `aerender` le o arquivo em disco, nao a sessao aberta.
6. **Renderizar** e fazer QC do MP4.

## 1. Transcricao ancorada na fala

```bash
ffmpeg -y -v error -vn -i "VIDEO.mp4" -ac 1 -ar 16000 -c:a pcm_s16le audio.wav
whisper audio.wav --model small --language pt --output_format json --output_dir .   # localizar
whisper trecho.wav --model medium --language pt --word_timestamps True ...          # confirmar
```

`small` numa passada longa **inventa e duplica segmentos** — usar so pra achar a regiao, e confirmar cada deixa com `medium` + `--word_timestamps` numa janela de ~20s. Ver [[whisper-passada-longa-inventa]]. O CLI nao aceita `--output_name`; para saidas distintas, copiar o wav com outro nome.

## 2. Comp e video

```
ae_create_composition({name, width:1920, height:1080, frameRate:23.976, duration:<seg>})
ae_import_image({compositionName, name:"VSL-video", path:"/abs/video.mp4", scaleToFit:true})
```

`ae_import_image` aceita **video** por `path`. Master 4K entra a 50% = 1080p pixel a pixel, e ai **punch-in ate 2x nao custa um pixel**.

## 3. Painel de liquid glass

Uma chamada monta o rig inteiro. **Precisa do video como camada de fundo** — por isso tudo vive na comp principal (nao ha ferramenta pra aninhar comp).

```
ae_build_liquid_glass({
  compositionName, backgroundLayerName:"VSL-video", name:"<PREFIXO>",
  width, height, centerX, centerY, roundness:30..40,
  frost:72, magnify:103, refraction:-85, saturation:100,
  tintColor:{r:0.03,g:0.03,b:0.04}, tintOpacity:58
})
```

Esses valores sao os **calibrados para texto legivel em cima**. O default (`frost:40, magnify:110, tint branco`) deixa o interior nitido demais e o texto some. `saturation:130` puxa rosa na pele/camiseta ampliada.

Depois: adicionar os textos, **parentear todos ao `<PREFIXO> CTRL`**, animar so a Position do CTRL (entrada/saida) e a Opacity de cada texto na sua deixa.

**Sempre aparar o rig** (`ae_trim_layer`) a janela de uso — 8 camadas: `Effects, Tint, RefractionMap, RefractionMap H, Edge Shine, Edge Darkness, Main, Shadow`. `CC Glass` + duplo displacement + blur rodando o video inteiro multiplica o render.

## 4. Zoom in/out

Keyframar `Scale` + `Position` do `VSL-video`. Base 50 (4K→1080p), punch entre **55 e 59**, com compensacao vertical de **+3,2 px por ponto de escala** pra cabeca nao subir.

Padrao por punch: `(t, 50)`, `(t+0.8, S, influence 75)`, `(hold, S)`, `(+0.9, 50, influence 45)`.

Cadencia: **um a cada 25-30s**, sempre no fim de uma frase. Menos que isso o video fica estatico; um talking head de 7 min pede ~25 punches.

## 5. "Ele ao lado do grafico"

Quando o painel dividir espaco com o apresentador, deslocar o video em vez de sobrepor:

```
Position 960,540 → 660,600   |   Scale 50 → 67
```

**A escala TEM que subir junto.** So deslocar expoe comp vazia e o vidro passa a refratar preto. Conferir cobertura: `pos_x + 19.2*escala >= 1920` e `pos_x - 19.2*escala <= 0`.

## 6. B-roll via Higgsfield

`kling3_0_turbo`, 16:9, 1080p, 5-6s = **10 creditos por clipe**. Sai a 24 fps com faixa de audio — conformar e mutar.

Regras de prompt que funcionaram:
- **Nunca rosto nitido** — IA denuncia e barateia oferta cara. Usar over-the-shoulder, maos, silhuetas, foco raso, ambientes.
- **Casar o grade** do talking head (quente, luz suave) — clipe frio briga com a imagem.
- Terminar com `no text, no logos`.
- Se o servidor sugerir preset, geralmente **recusar** (`declined_preset_id`) — preset traz grade proprio.
- Conferir cada clipe com tiras de frame antes de usar: gerado escuro demais ou estatico demais e comum.

## 7. Render

```bash
"/Applications/Adobe After Effects 2026/aerender" \
  -project "/abs/PROJETO.aep" -comp "NOME DA COMP" -output "/abs/SAIDA.mp4"
```

- **Nao usar `-reuse`** — falha com `AESend error -1712`.
- **Nao passar `-OMtemplate`** — os nomes padrao da Adobe nao existem; o modulo default ja entrega **H.264 1080p + AAC**.
- Referencia: 7 min de 4K→1080p com 3 paineis de vidro = **~10 min**. Nao estimar pelo teste de poucos frames (pega cache e engana).

QC: `format.duration`, `stream(v).duration` e `stream(a).duration` tem que ser **os tres iguais**, e `ffmpeg -v error -i X -f null -` sem saida.

## Armadilhas do plugin (todas falham em SILENCIO)

Ver [[ae-mcp-armadilhas]]. As que mais custam tempo:

- `ae_add_text_layer` **retorna sucesso sem criar a camada** quando o texto tem `+` ou `=`. Verificar com `ae_get_layer_info`. Acentos funcionam.
- `justification:"left"` **nao funciona** — cai em centralizado. Projetar em right/center.
- `ae_batch` **nao roda** — usar chamadas individuais.
- `ae_set_shape_fill` **nao pinta** camadas criadas por ExtendScript (o `Tint` do vidro). Passar `tintColor` no build.
- AE em portugues → efeitos com nome PT ("Desfoque gaussiano", "Transformar").
- **Nao existe apagar keyframe** — sobrescrever com valor neutro.
- **Nao existe camera** — push-in e null + parent.
- **Nao existe save nem render** — pedir Cmd+S e usar `aerender`.
- Rodar `ae_finalize_build` no fim: `influence` sozinho deixa **Position (espacial) LINEAR**.

## Verificar sempre com os olhos

`ae_export_frame` e a unica forma de saber o que foi construido. Exportar apos cada elemento e **tambem fora da janela** do painel, pra confirmar que ele some. Frames baixados com `curl` e lidos com Read.
