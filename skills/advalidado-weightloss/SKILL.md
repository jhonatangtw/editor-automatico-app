---
name: advalidado-weightloss
description: Clona um AD validado de emagrecimento (story-ad de mãe/mulher, GLP-1, "receita de gelatina", resposta direta em saúde para os EUA) de ponta a ponta — ficha técnica do original, hooks novos, start frames da personagem nova (GPT Image 2.5 no Higgsfield), avatar falante na HeyGen (Avatar IV, voz desenhada), b-roll palavra por palavra (50% IA com a mesma personagem + 50% orgânico do TikTok recortado sem texto) e a edição dinâmica/dopaminérgica montada no HyperFrames (punch-in, legenda palavra por palavra na área segura do Reels, lettering nas frases fortes, X vermelho, seta de CTA, SFX discretos). Use SEMPRE que pedirem "clona esse AD de emagrecimento", "faz o ADVALIDADO-WEIGHTLOSS", "mesmo AD com outra personagem", "AD validado weight loss", ou mandarem um AD validado de perda de peso / GLP-1 / gelatina pedindo uma versão nova. NÃO é para conferir AD pronto (conferir-ads-por-frame), nem para clone fora de emagrecimento (clone-ad-validado), nem para só escrever hooks (hooks-meat-hook).
---

# ADVALIDADO-WEIGHTLOSS

Pega um AD de emagrecimento que já vende e entrega outro, com **a mesma estrutura e a mesma copy
no corpo**, personagem nova, hooks novos e edição premium. Feito e validado num AD real de 3:27
(mãe pós-parto → foto do aniversário da filha → GLP-1/GIP pararam → receita de gelatina → CTA).

**Regra de ouro: mostre o custo e espere o "pode" antes de cada gasto** (imagem, avatar, voz).

## O que precisa estar instalado
ffmpeg · Whisper · Node 24 (HyperFrames) · `higgsfield` CLI logado · `heygen` CLI logado ·
`yt-dlp` (para os orgânicos). O app Editor Automático instala quase tudo em "Preparar esta máquina".
HyperFrames pede Node 22+: `export PATH=/opt/homebrew/opt/node@24/bin:$PATH` antes dos comandos
(no Mac). Se o node 24 parar de abrir com erro de `libsimdjson`, `brew reinstall node@24`.

## Pastas do job
```
<JOB>/
  original/   o AD validado (só leitura — nunca altere)
  analise/    ficha técnica
  copy.md     hooks novos + regra do corpo + avatar/voz escolhidos
  avatar/     H1_start.png… prompts/ heygen/
  broll/      plano.py → plano.json, imagens/, tiktok/, folha_de_contato.jpg
  edicao/     palavras_h1.json, palavras_corpo.json, build.py
  hyperframes/<projeto>/
  entrega/
```

## Passo 1 — Ficha do original
Use a skill `analise-criativo-ficha` com a saída fora de `original/`. Transcreva com Whisper
**medium** (o small pula palavra) e `initial_prompt` com os nomes difíceis (Mounjaro, Ozempic,
GLP-1, GIP, gelatin). **A legenda queimada do original é o juiz** da copy: confira os trechos
duvidosos recortando a área da legenda com ffmpeg.
- Trecho **borrado** no original quase sempre esconde celebridade ou especialista real usado
  como endosso. **Nunca** reproduza nome nem rosto: troque por pronome ("She's suing those people").

## Passo 2 — Copy e briefing do copywriter (`copy.md`)
Normalmente a copy **vem pronta**: um documento com hooks, corpo, briefing e comentários do copywriter.
- Leia a copy **junto com os comentários** (Google Doc: exporte com os comentários; uma cópia do Doc
  perde todos) e siga à risca: hooks e corpo como estão escritos, sem reescrever.
- Cada pedido do copywriter (insert, b-roll, lettering, troca de palavra) vira um item do plano.
- Personagem, voz, tom e estilo saem do briefing.
- Registre em `copy.md` a copy recebida e a lista de pedidos do copywriter.
- Só se a copy **não** trouxer hooks: escreva no mesmo formato do original, um ângulo cada, ≤ 5 s de
  fala (~14 palavras). Sem copy de corpo: corpo = copy do original **palavra por palavra** (só sai
  nome de pessoa real).
- Copy e briefing dizendo coisas diferentes: pergunte ao editor, não decida.

## Passo 3 — Personagem nova (start frames)
GPT Image 2.5 no Higgsfield, 9:16, 2k. Personagem **diferente** da do original (idade, cabelo,
roupa) no mesmo tipo de cena. Ordem do prompt: **cena e pessoa → câmera de celular → bloco
anti-cara-de-IA → frase final de pele**. Boca fechada e olhar na lente (é o quadro do lip sync).
O H1 vira a âncora; H2/H3 levam o H1 como `--image-references` e abrem com
`IDENTITY: the SAME woman as in the reference image…`. Os blocos prontos estão em
`scripts/plano_broll.py` (CAM, ANTI, PELE, ID).
```bash
higgsfield generate cost gpt_image_2_5 --prompt "$(cat avatar/prompts/h1.txt)" --aspect_ratio 9:16 --quality high --resolution 2k
```

## Passo 4 — Avatar falante (HeyGen, Avatar IV)
1. Voz: `heygen voice create --prompt "warm friendly female voice, American, 30s, casual" --gender female`
   (sem `--locale` — com ele a busca volta vazia). Baixe as prévias e meça a altura contra a
   original: `python3 scripts/f0_voz.py orig.wav cand*.mp3`. O ouvido decide.
2. `heygen asset create --file avatar/H1_start.png` → `heygen video create -d pedido.json` com
   `"type":"image"`, `"aspect_ratio":"9:16"`, `"resolution":"1080p"`, `"expressiveness":"medium"`,
   `script`, `voice_id` e um `motion_prompt` com o arco emocional. Use os créditos do **plano**
   pelo CLI logado (a chave de API costuma ter bem menos).
3. **Confira a fala do avatar contra a copy** (Whisper + difflib) antes de editar. Palavra que
   "sumiu" pode ser o Whisper juntando: retranscreva só aquele trecho antes de regerar.

## Passo 5 — Plano de b-roll palavra por palavra
Copie `scripts/plano_broll.py` para `broll/plano.py` e preencha:
- **posição** = onde o original tinha b-roll; **conteúdo** = o que é falado naquela palavra.
- Toda pessoa em cena = a personagem do H1 (`pessoa(...)`, vai com referência).
- Mecanismo em 3D (`mecanismo(...)`) com bloco de estilo fixo e **sem** referência.
- Texto que tem de sair certo vai entre aspas no prompt ("TOTAL $2,000.00", "TOO BIG").
- Pós-parto: escreva "she is NOT pregnant", senão sai grávida.

Gerar: `python3 scripts/gerar_broll.py --custo` (só orça) → `python3 scripts/gerar_broll.py`.
O script envia sem esperar, acompanha a fila e baixa pelo `result_url`; se algo ficar na fila,
rode de novo — ele **só baixa**, não cobra outra vez.

## Passo 6 — 50% orgânico do TikTok
- Busca por palavra só pelo navegador (`tiktok.com/search/video?q=…`); `yt-dlp` não busca.
  Pegue 6 links por cena, baixe só as capas (`yt-dlp --skip-download --write-thumbnail`) e
  escolha no olho: **plano de ação** ganha de gente falando para a câmera.
- Baixe os escolhidos (`yt-dlp -f "bv*+ba/b" --merge-output-format mp4`) e **recorte um trecho
  sem texto queimado**: `crop` mantendo 9:16 + `scale=1080:1920`, sem áudio. Confira 3 quadros.
  Se não der para limpar sem borrar (vídeo de 576p), use a versão de IA daquela cena.
- Orgânico nunca mostra a personagem; IA fica com pessoa, 3D e texto exato.
- Vídeo de terceiros em anúncio pago tem risco de direito autoral — avise o dono do job.

## Passo 7 — Folha de contato → aprovação
`python3 scripts/folha_de_contato.py` (selo IA/TIKTOK, tempo e fala em cada cena). Só depois
da aprovação anima ou monta.

## Passo 8 — Montagem no HyperFrames
1. Transcreva os vídeos do avatar palavra por palavra (`edicao/palavras_h1.json`,
   `palavras_corpo.json`) e **reposicione cada cena na voz nova** — o ritmo muda.
2. Copie `scripts/build_hyperframes.py` para `edicao/build.py`, troque as listas
   (BROLL, PUNCH, LETTER, FLASH, SETA, SFX, CORRIGE) pelos tempos do seu AD e rode.
3. `npx hyperframes check` → `npx hyperframes snapshot --at <tempos>` → olhe os quadros →
   `npx hyperframes preview --background`. Render só depois do "aprovado".

### Padrão de edição (dinâmica / dopaminérgica)
- **Avatar**: punch-in em snap de 0,16 s a cada frase (1,0 ↔ 1,1–1,28); crash-zoom (1,4) em
  "zoomed in"; empurrão lento nos momentos emocionais.
- **B-roll**: push lento ou punch; nas listas ("low carb, fasting, walking…") **um corte por
  palavra**; a "foto" entra como polaroid e depois dá zoom em cada parte que ela cita.
  **Nunca repita footage** na mesma timeline — volta emocional pede imagem nova.
- **Legenda**: grupos de até 3 palavras, Montserrat ExtraBold ~76 px, contorno preto, palavra
  ativa amarela 1,12×, `top:1250px` (área segura do Reels). Some enquanto há lettering.
  Dê `margin:0 .16em` em cada palavra, senão a ativa come o espaço.
- **Lettering**: Anton ~132 px, só com palavras FALADAS, nas frases-soco (vermelho/amarelo/caixa);
  X vermelho em "No injection / no diet / no gym"; seta branca pulsando no CTA; flash branco
  nas viradas; escurecer na frase de arrependimento.
- **SFX discretos** (da sua biblioteca, copiados para `assets/sfx/`): whoosh 0,12–0,2 nos
  b-rolls, pop 0,18–0,45 no lettering e nos cortes rápidos, impacto 0,2–0,28 nas frases-soco,
  riser 0,18 antes da virada, clique de câmera na "foto", caixa registradora no preço, ding no CTA.

## Armadilhas do HyperFrames
- Cópia de `.html` com `data-composition-id` dentro do projeto vira 2ª composição (áudio em dobro).
  Guarde backups fora.
- Três `<img>` com o mesmo arquivo → aviso de mídia duplicada: use cópias.
- Avisos `nested_structure_needs_subcomposition` e `container_overflow` do punch-in são esperados.

## Compliance (avise, não decida pelo dono do job)
Promessa de GLP-1, marca de remédio na tela, antes/depois de corpo e vídeo de terceiros entram
nas regras do Meta e de direito autoral.
