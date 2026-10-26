---
name: upsell-agente
description: Upsell-Agente — produz um vídeo de UPSELL DR pós-compra (nutra/saúde EUA) de ponta a ponta no padrão validado da casa (Upsell #1 MarcaB / MarcaG / MarcaE): apresentador(a) fotorrealista falando no Avatar IV com voz ElevenLabs ultrarrealista, 6–10 depoimentos UGC selfie no Avatar IV com controle de movimento, b-roll cena por cena da referência (orgânico do TikTok primeiro, IA onde faltar), frasco do produto em escala real (Nano Banana Pro + mockup), gráficos de oferta (card de preço, selo de garantia, tarjas de contato, botões ADD & CONTINUE / GET TRIPLE-DOSE, split café/almoço/jantar, mosaico de depoentes, CTA fixa, card final), legenda por frase em pílula, trilha + SFX discretos, montado no HyperFrames e renderizado em N versões de preço (A/B/C). Use SEMPRE que pedirem "faz o upsell", "Upsell-Agente", "novo upsell do [produto]", "upsell no padrão do MarcaB/MarcaG/MarcaE", "espelha esse upsell cena por cena", "troca de preço do upsell em 3 versões", ou mandarem copy de upsell (Doc com apresentador + depoimentos + preço A/B/C) com vídeo de referência. NÃO é para AD frio 9:16 (advalidado-weightloss / clone-ad-validado), nem VSL longa, nem só trocar o preço de um upsell já editado no Premiere (aí é edição pontual).
---

# Upsell-Agente

Receita validada no **Upsell #1 MarcaE** (job `25. Joint Pain/MarcaE/OT/[221026][OT] NNN_XX [MarcaE] [Squad Offer]`,
22–23/10/2026): 9:45, 4:3 1440×1080, 25 fps, 3 preços, 10 depoentes, ~US$ 64 no HWStudio. Área de trabalho de referência
(tudo que funcionou, para copiar): `<pasta de trabalho>/_SAMURAI/MarcaE-up1-335da/`.

Leia junto: `references/ESTILO_UPSELL.md` (estrutura e medidas da referência), `references/LICOES.md` (o que o usuário
reprovou e por quê — **ler antes de gerar qualquer coisa**), skill `padrao-visual-MarcaB` (a referência original em AE).
Roda dentro da Agência Samurai (`/samurai`): Revisor (pré) → G1 → IA Creator + Editor em paralelo → G3. Sem Samurai, siga os mesmos gates.

## Estrutura do job (local; mídia pesada fora do Drive)

```
<pasta de trabalho>/_SAMURAI/<produto>-up<n>-<job>/
  ref/        vídeo de referência (baixar da ferramenta de revisão, ver memória frameio-comentar-via-chrome) + mosaicos + cortes
  copy/copy.md  copy marcada (formato abaixo) + pedidos do copywriter (comentários do Doc!)
  ia/         susan|apresentador/, depoentes/ (start, video), voz/ (blocos, depoentes_tts), mockups/
  broll/      tiktok/ (candidatos, final), ia/ (img, vid, final), acervo/ (cópia local do acervo reutilizado)
  edicao/     build.py · prep.py · master.py · render_3.sh (copiar de templates/ e adaptar) + folhas de QA
  hyperframes/<projeto>/  index.html gerado + assets/
  entrega/    finais (+ _versoes_anteriores/)
```
Job no Drive: `_SAMURAI/` (briefing, ledger, revisões, planos) e os finais em `5 Render/`.

### copy.md
Depois de uma linha `---`, cada fala começa com um marcador: `[APRESENTADOR]` (qualquer nome sem número),
`[NOME SOBRENOME, IDADE]` para depoente, `[PREÇO A]` / `[PREÇO B]` / `[PREÇO C]` na frase de preço (uma linha).
`scripts/blocos_apresentador.py copy.md blocos.json` divide em S01..Snn (~85 palavras, fecha em frase),
PRECO_x e D01..Dnn.

## Passo a passo (aprovação antes de cada gasto)

1. **Ler tudo.** Copy COM comentários (Drive `read_file_content includeComments`; cópia de Doc perde comentário),
   briefing do copy, vídeo de referência (qual é: confirme — no MarcaE o usuário trocou da MarcaG para a MarcaB
   no meio), mockups oficiais (PNG alfa, 1/3/6/9/12 frascos), contato de suporte, preços.
2. **Dissecar a referência**: `scripts/transcrever.py`, `ffmpeg select='gt(scene,0.25)'` para cortes, mosaico a cada 3 s.
   Mapa cena por cena (`05_plano_edicao.md`): tempo, tipo (apresentador / b-roll / depoimento / gráfico), frase nova
   que cai ali, decisão (reuso do acervo · TikTok · IA · gráfico). Reuso só se não mostra produto/nicho errado e o
   usuário não vetou a fonte (ele vetou o upsell CoreStrength no MarcaE).
3. **Revisor (pré)** sobre a copy (claims, depoimento de IA × FTC). Vermelho = decisão do usuário; registrar no ledger.
4. **G1** numa mensagem: formato (4:3? 1:1?), nº de versões de preço, Studio (local ou empresa — o local exige chave
   OpenRouter; empresa só com autorização explícita do usuário por demanda), teto de gasto, piloto.
   Custos de referência (OpenRouter via Studio): GPT Image 2.5 Flare ~US$ 0,04–0,06 · Nano Banana Pro ~0,14 ·
   Avatar IV US$ 0,05/s · Kling v3.0 Pro 5 s US$ 0,56 · Seedance 2.5 480p ~0,10/s (720p ~0,23/s).
5. **Apresentador(a)**: foto do usuário → `photorealism-prompts` + GPT Image 2.5 Flare com a foto como 1ª referência
   (IDENTITY LOCK, rosto não descrito, anti-cara-de-IA só em pele/luz/tecido/cenário), **16:9** centralizado para
   recorte 4:3 sem ampliar. Voz: 3–4 candidatas da Voice Library (preview grátis, F0), o usuário escolhe de ouvido.
   MarcaE = Michelle `xg7RXypgOlRSIidsSV4l`, `eleven_v4`.
6. **Piloto** (~US$ 3): 1 still do apresentador + 15 s no Avatar IV; 1 depoente completo. Mostrar, esperar ok.
7. **Vozes e TTS**: vozes dos depoentes (idade certa, conversacional, gravação crua; nunca as do MarcaB nem a do
   apresentador; o usuário delegou a escolha no MarcaE). `scripts/tts_lote.py` → `scripts/qc_tts.py`; refaça só o
   que errar (seed novo). O `_alin.json` da ElevenLabs é a fonte de tempo e legenda.
8. **Avatar IV** (`or:heygen/avatar-iv`, 1080p 16:9, `image_urls` + `audio_urls`; o Studio não tem campo de
   expressiveness/motion — escreva "Expressiveness: medium." + arco emocional no `prompt`). Um clipe por bloco/depoente.
   Start frames dos depoentes: selfie de celular 16:9, cenários diferentes, sem produto na mão (ver LICOES).
9. **B-roll**: orgânico do TikTok por trecho+palavra-chave (Chrome; capas com yt-dlp; recorte 4:3 sem texto queimado,
   fonte ≥ 1080 de largura). Onde não achar → IA (GPT Image/Nano Banana → Kling v3.0 Pro câmera travada). Planos COM
   PRODUTO: Nano Banana Pro + mockup como referência, escala real, medir proporção (`scripts/proporcao_mockup.py`)
   antes de animar; nunca colar o PNG por cima. Folha de contato + `qc-visual` antes de montar.
10. **Montagem** (`templates/` → `edicao/`): `prep.py` (SFX do Baú, trilha, recortes 4:3, grão), `build.py <A|B|C>`
    (gera o index.html; edite aqui, nunca o HTML), `npx hyperframes check`, snapshots nos pontos-chave
    (`npx hyperframes snapshot . --at t1,t2`), **preview para o usuário ANTES de qualquer render**
    (`npx hyperframes preview --background`, node 24). O que trocar no build: ver `references/TROCAR_NO_BUILD.md`.
11. **Render** `render_3.sh` (1 worker, ~15 min/versão, apaga temporários; disco!) → `master.py` (−16 LUFS, TP ≤ −1,5).
    Conferir em cada versão, por quadro: frase+card de preço, CTA fixa, selo, botões, abertura, e que nenhum gráfico
    fica atrás de legenda de 2 linhas. Uma versão pode sair com imagem quebrada sozinha (botão esticado na A) —
    conferir as três, não só uma. Copiar para `5 Render/` (antigas em `_versoes_anteriores/`), fechar ledger.

## Padrão de edição (o que o usuário aprovou)
- Estrutura da referência cena por cena (abertura "Before we ship your order" → future pacing → descoberta →
  3 depoimentos → mecanismo (mosaico, split café/almoço/jantar, 3D) → depoimento-ponte → problema (estoque, navio,
  "can't rush plants") → solução de emergência → preço → garantia → contato → botão → como usar → 3 depoimentos → CTA final).
- Abre direto no "Hello" (o Avatar IV ignora gesto; aceno feito no Kling deformou a mão e saiu).
- Apresentador: punch-in sutil 1,0↔1,08 nos cortes; b-roll com push lento e corte seco; light leak (Baú, screen 60 %)
  só nas emendas que pulam e em poucas viradas de bloco.
- Legenda: Montserrat Bold 48, pílula preta 50 %, **por frase** (corta só em pontuação; oração longa em 2 linhas,
  divide antes de conectivo, `text-wrap:balance`), sem legenda sob card de garantia e sob a CTA fixa.
- Gráficos na cor do rótulo: tarja nome+idade (nome completo nos primeiros, só o primeiro nome depois), card de preço
  sobre o kit, selo de garantia (arte do usuário), tarjas de contato, ADD & CONTINUE (laranja) e GET TRIPLE-DOSE
  (arte do usuário) acima da legenda, CTA fixa (arte do usuário) sobre os 3 últimos depoimentos.
- Áudio: trilha contínua ~20 dB abaixo da voz (o bed é −34,6 LUFS → volume 0,39), sobe no card final; SFX discretos
  (whoosh .05–.14, pop/click nos gráficos, ding no preço, riser antes da garantia). Master −16 LUFS.
