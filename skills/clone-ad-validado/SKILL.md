---
name: clone-ad-validado
description: Clona um AD validado (anúncio que já vende) trocando o personagem e/ou a copy, no automático e com aprovação antes de cada gasto — decupa o original com Whisper (mapa de cenas com tempos, legenda queimada como juiz), cria a personagem nova (retrato-âncora no GPT Image 2.5 com bloco anti-cara-de-IA e o mesmo rosto em cada cenário), escolhe a voz no ElevenLabs medindo o F0 contra a original e encaixa cada frase no mesmo segundo, faz o lip sync no HeyGen Avatar IV a partir de foto + áudio, refaz no Kling só os b-rolls que mostravam a pessoa antiga, monta no HyperFrames com a mesma estrutura e os mesmos tempos, e confere (lip sync por quadro do silêncio × quadro do pico, folha original × clone, nenhuma imagem da pessoa antiga, legenda contra a copy, −14 LUFS). Use SEMPRE que pedirem "clona esse AD", "clone de AD validado", "troca o personagem do anúncio", "troca a apresentadora/o avatar", "mesmo AD com outra pessoa", "o criativo cansou, faz outro rosto", "refaz esse anúncio com outra atriz", "mantém a estrutura e troca a copy/o produto", ou mandarem um AD que performa pedindo uma versão nova. NÃO é para editar um bruto de avatar do zero (use editor-automatico-de-broll), nem para só conferir um AD pronto (use conferir-ads-por-frame), nem para trocar só o hook (use hooks-meat-hook).
---

# Clone de AD validado

Um anúncio que vende um dia cansa: o público já viu aquele rosto e passa reto.
Clonar é **manter o que faz ele vender** (roteiro, cortes, ritmo, legenda,
tempos) e **trocar só o personagem** — ou também a copy, para outro produto.
A estrutura fica, o rosto muda, e o mesmo anúncio volta ao leilão como se
fosse outro.

São 8 passos. **Todo passo que gasta crédito para e pede aprovação** antes de
gerar, com a estimativa de custo na mesma mensagem. "Pode seguir" dado lá
atrás não vale para a etapa seguinte.

`SK` = a pasta desta skill. Scripts: `python3 "$SK/scripts/..."`.

## Regras que não se negociam

1. **O original nunca é alterado.** Copie para `<pasta do job>/original/` e trabalhe na cópia.
2. **Aprovação antes de cada gasto** — retrato, voz, lip sync, cada lote de b-roll, render final. Mostre o que vai gerar, quantas vezes e quanto custa (`higgsfield generate cost ...`, saldo da HeyGen) e espere o "sim".
3. **Nunca sobra imagem da pessoa antiga.** Rosto, corpo, mãos, cabelo, reflexo, foto num porta-retrato, miniatura num celular. Plano que mostra qualquer pedaço dela é REFEITO; plano que não mostra é reaproveitado com a legenda antiga apagada. Isso é conferido por varredura no fim (passo 7).
4. **Mesmos tempos.** Cada frase da voz nova começa no segundo em que começava no original; cada troca de cena cai no mesmo quadro.
5. **Chave nunca no chat.** HeyGen e Higgsfield entram pelo login do CLI (aba Contas do Editor Automático); ElevenLabs pela variável `ELEVENLABS_API_KEY`. Não peça, não imprima, não grave chave em arquivo do job.
6. **Tudo que entra na montagem mora na pasta do job.** Nada de importar de pasta temporária — ela some e a montagem fica com mídia offline.
7. **Voz no idioma e sotaque do público do original.** Anúncio para os EUA = inglês americano. Números por extenso no texto do TTS.

## Passo 0 — Ambiente (uma vez)

Confira e diga o que falta, **sem mostrar chave nenhuma**:

```bash
ffmpeg -version | head -1; whisper --help >/dev/null && echo whisper ok
higgsfield account status          # logado? saldo?
heygen auth status                 # logado? créditos premium (é deste bolso que sai o lip sync)
[ -n "$ELEVENLABS_API_KEY" ] && echo "ElevenLabs: chave no ambiente" || echo "ElevenLabs: falta a chave"
command -v hyperframes || ls ~/.editorblackbelt/bin/hyperframes   # senão: npx --yes hyperframes@0.8.134
```

O que faltar se instala pelo **Editor Automático › Ambiente › Preparar este computador**; login pela aba **Contas**. Se o Higgsfield responder "Not authenticated", pare de tentar variações: o usuário precisa rodar `higgsfield auth login` num terminal dele.

Pastas do job:

```
<pasta do job>/
  original/   decupagem/   img/   voz/   lipsync/   broll/   hf/   qc/   entrega/
```

## Passo 1 — Pegar o AD

```bash
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,r_frame_rate:format=duration -of compact original/AD.mp4
ffmpeg -v error -i original/AD.mp4 -vf "fps=1/2,scale=200:-1,tile=8x4" -frames:v 1 qc/mosaico_original.jpg
```

Responda: duração, resolução, fps, se tem **legenda queimada**, se tem música.
Se o pedido for clonar só um trecho (ex.: os primeiros 30 s), **corte no fim de
uma frase** — nunca no meio de palavra (o tempo exato sai da decupagem).

## Passo 2 — Decupar

```bash
ffmpeg -v error -i original/AD.mp4 -vn -ac 1 -ar 16000 decupagem/orig.wav
whisper decupagem/orig.wav --model medium --word_timestamps True --output_format json --output_dir decupagem/
```

AD de até ~1 min: uma passada `medium` com tempo por palavra resolve. Mais longo: transcreva em janelas de ~20 s (`ffmpeg -ss X -t 20`) — passada longa inventa palavra no silêncio e engole frase.

Monte `decupagem/decupagem.md` (modelo em `references/decupagem-modelo.md`):

- **Roteiro por frase** com início/fim (s).
- **Palavra por palavra** com tempo.
- **Mapa de cenas**: bloco, tempo, tipo (avatar, tela dividida, b-roll, produto, lettering), o que aparece, e a coluna **No clone**: `personagem nova` · `REFEITO (mostra a pessoa antiga)` · `reaproveitado (sem a pessoa)`.
- **Transições** com o quadro exato (flash, desfoque, vazamento de luz) — medidas no original.
- **Estilo da legenda**: caixa, cor, fonte aproximada, por frase ou por palavra, e a **altura** (y da base, em fração da tela) em cada bloco.

⚠️ **A legenda queimada é o juiz do Whisper.** No job real o Whisper ouviu "this food" numa respiração; a legenda dizia "—". Na dúvida, vale o que está escrito na tela (e a copy, se houver). Corte de cena: em vídeo VP9/AV1 baixado da internet o `scene detect` do ffmpeg não acha nada — meça a diferença quadro a quadro (ver `boas-praticas-black-belt`).

**Checkpoint 2 — mostre o mapa de cenas e PERGUNTE** se o mapa está certo e o que é refeito × reaproveitado. É a decisão que define o custo inteiro.

## Passo 3 — Personagem nova (e a copy)

### 3a. A copy

- **Troca só de personagem:** copy igual, palavra por palavra (a da legenda queimada).
- **Troca de copy/produto:** reescreva com a MESMA estrutura (mesmo número de frases por bloco, duração parecida), mostre lado a lado com a original em `copy.md`, e só siga com o "aprovado". Hooks novos: no mesmo formato do original, cada um com um ângulo, ≤ 4 s de fala.

### 3b. Retrato-âncora (GPT Image 2.5 no Higgsfield)

Pergunte idade, etnia, cabelo, estilo (o mesmo do original: selfie UGC, cozinha, carro...). Diferente o bastante da pessoa antiga para não parecer a mesma.

```bash
higgsfield generate cost gpt_image_2_5 --prompt "$(cat img/p_selfie.txt)" --aspect_ratio 9:16 --quality high --resolution 2k
# aprovado:
higgsfield generate create gpt_image_2_5 --prompt "$(cat img/p_selfie.txt)" --aspect_ratio 9:16 --quality high --resolution 2k --json
```

Prompt na ordem que funciona: **cena e pessoa → specs de câmera (celular, se o original é UGC) → bloco anti-cara-de-IA → frase final de pele**. Modelo completo, testado, em `references/prompts-personagem.md`. Pontos que não podem faltar:

- "Not a stock image, not a commercial shoot, not an AI render", luz imperfeita (janela estourada de um lado, duas temperaturas de cor), rosto assimétrico item a item, grão e filme nomeado (Portra 400), "no beauty filter, no HDR glow, no glossy plastic sheen".
- Olhar na lente, boca fechada e relaxada (é o quadro de partida do lip sync).
- "Any packaging, sign or paper in the background is out of focus and unreadable".
- Termina EXATAMENTE com: `Visible pores, micro-texture, natural skin imperfections, subtle peach fuzz, natural skin sheen, no airbrushing, no smoothing filters.`

**O mesmo rosto em cada cenário** onde ela fala (cozinha, carro...): passe o **id do job** do retrato aprovado como `--image-references` e abra o prompt com `IDENTITY: the SAME woman as in the reference image — same face, same skin, same hair, same earrings, same top. Same day, a different room.`

⚠️ A saída do `--json` é um **array de ids**, não objeto. Baixe pelo `result_url` (não `min_result_url`, que é miniatura de ~600 px) e confira o tamanho com `ffprobe` antes de usar. Se o parser falhar, **não reenvie** — o job já foi cobrado: `higgsfield generate list --image --json` e case pelo prompt.

**Checkpoint 3b — mostre os retratos e espere a aprovação.** Tudo depois (voz, lip sync, b-roll) é construído em cima deste rosto.

### 3c. Voz (ElevenLabs), escolhida pelo F0

1. Escolha 2–3 vozes candidatas do idioma/sotaque certo e gere **a copy inteira** com cada uma (aprovação: são 2–3 gerações):
   ```bash
   python3 "$SK/scripts/tts_elevenlabs.py" <VOICE_ID> --arquivo copy.txt voz/cand_a.mp3
   ```
2. Meça contra a voz original:
   ```bash
   python3 "$SK/scripts/f0_voz.py" decupagem/orig.wav voz/cand_a.mp3 voz/cand_b.mp3 voz/cand_c.mp3
   ```
   A tabela ordena pela distância de F0 até a original e mostra palavras/min. Ritmo se corrige no encaixe; altura de voz não.
3. **O ouvido do usuário decide.** Número separa grave × agudo; sotaque, idade e "voz batida" não saem de medida. Mande as amostras e espere a escolha.
4. Gere a versão final e **encaixe nos tempos do original**:
   ```bash
   python3 "$SK/scripts/encaixar_voz.py" --original decupagem/orig.json --nova voz/voz_nova.json \
       --audio voz/voz_nova.mp3 --fim <DURAÇÃO> --saida voz/voz_clone.wav
   ```
   Se as listas de palavras divergirem (Whisper inventou palavra, "going to" × "gonna", número em dígito), o script grava a lista do original para você corrigir e mostra onde. Bloco que "não coube" passa do próximo: encurte a frase ou aceite o deslize se for < 0,2 s.

⚠️ TTS não é idempotente: regerou o áudio, refaça o encaixe e tudo que veio do JSON antigo. Guarde `.mp3` + `.json` juntos em `voz/`.

## Passo 4 — Lip sync (HeyGen Avatar IV, foto + áudio)

**Avatar IV**, não V: o V exige avatar treinado com filmagem real e recusa `expressiveness`/`motion_prompt` em pessoa gerada por IA. O IV aceita a foto solta direto.

Um vídeo **por cenário** (selfie, cozinha...). Para cada um, recorte da `voz_clone.wav` o trecho daquele cenário com ~0,3 s de folga antes, e use o retrato daquele cenário:

```bash
ffmpeg -v error -ss <INI-0.3> -to <FIM+0.3> -i voz/voz_clone.wav lipsync/aud_cenario1.wav
heygen asset create --file lipsync/cenario1.jpg      # imagem: o campo do retorno é "id"
heygen asset create --file lipsync/aud_cenario1.wav  # áudio: o campo é "asset_id" (ler as duas chaves)
heygen auth status                                   # créditos ANTES — mostre a estimativa e peça aprovação
heygen video create -d '{"type":"image","image":{"type":"asset_id","asset_id":"<ID_IMG>"},
  "audio_asset_id":"<ID_AUD>","aspect_ratio":"9:16","resolution":"1080p","fit":"cover",
  "expressiveness":"medium","motion_prompt":"<arco da fala: intenção de cada frase, ênfases, quando muda a expressão>",
  "output_format":"mp4"}'
heygen video get <VIDEO_ID>                          # repita até o status de pronto (começa em "waiting")
heygen video download <VIDEO_ID> --output-path lipsync/lipsync_cenario1.mp4
```

- Estimativa: ~4 créditos premium por segundo de vídeo (um trecho de ~27 s custou ~104). Use o saldo do **CLI** (`heygen auth status`), não o da chave de API — são bolsos diferentes.
- Arquivo até 32 MB: áudio longo vai em mp3.
- `aspect_ratio: "9:16"` é obrigatório para vertical.
- A HeyGen entrega **25 fps**. No HyperFrames não importa (render a 30); no Premiere, case a sequência com a fonte ou ele derruba quadro justo na boca.
- Meça o deslocamento do vídeo devolvido contra o áudio enviado e some à folga no ponto de entrada:
  ```bash
  python3 "$SK/scripts/offset_audio.py" lipsync/lipsync_cenario1.mp4 lipsync/aud_cenario1.wav
  ```
- **Produto na mão?** O lip sync reescreve o texto miúdo do rótulo. Não regere por isso: recole o frasco do still aprovado por cima (ver `boas-praticas-black-belt`). Regerar só por rosto, boca ou pose.

## Passo 5 — B-rolls

Para cada cena de b-roll do mapa:

- **Mostra a pessoa antiga (qualquer pedaço)** → REFEITA com a personagem nova:
  1. Imagem no GPT Image 2.5 com o retrato como `--image-references` + `IDENTITY` no topo, mesmo enquadramento do plano original (descreva o plano original: o que entra, o que fica cortado).
  2. **Folha de contato → aprovação → só então animar.** Animar imagem errada é crédito jogado fora.
  3. Kling 3.0 Turbo, 9:16:
     ```bash
     higgsfield generate create kling3_0_turbo --start-image <id da imagem aprovada> --aspect_ratio 9:16 \
       --resolution 1080p --duration 5 --prompt "<um movimento sutil, câmera quase parada, no scene change, no text on screen>" \
       --json
     ```
     Sai 1076×1928 a 24 fps — o HyperFrames enquadra com `object-fit: cover`.
- **Não mostra a pessoa** → reaproveitado do original: recorte a faixa/trecho com ffmpeg e **apague a legenda queimada** (recorte fora da faixa da legenda, ou desfoque a caixa e cubra com a legenda nova no mesmo lugar).

⚠️ **403 no `generate create` com crédito sobrando = moderação**, não login nem saldo. Tire a descrição de corpo do prompt ("soft belly", "overweight", "abdomen") e descreva roupa, pose e enquadramento; mantenha "non-sexual, everyday, documentary".
⚠️ Lote com vários jobs: submeta sem `--wait` e acompanhe com `higgsfield generate list`/`get`; se usar `--wait`, passe `--wait-timeout 50m --wait-interval 20s`.

## Passo 6 — Montagem (HyperFrames)

Um `index.html` 1080×1920, 30 fps, gerado por um script — modelo real e comentado em `templates/gerar_index_exemplo.py`. Copie para `hf/gerar_index.py`, adapte ao mapa de cenas e rode. O que tem que sair igual ao original:

- mesma estrutura de blocos e **mesmos tempos** (da decupagem);
- mesmas transições no mesmo quadro (flash, desfoque, vazamento de luz);
- legenda **no mesmo estilo e na mesma altura**, gerada dos tempos da `voz_clone.json` (por frase se o original é por frase). Para acertar o corpo da fonte, meça a **largura do texto** num quadro do original e resolva o tamanho por busca — detecção automática da faixa de legenda não funciona;
- SFX discretos só onde o original tinha.

```bash
cd hf && hyperframes check && hyperframes preview      # o usuário confere no Studio antes do render
hyperframes render                                       # 1080x1920, 30 fps
```

Regras de animação (o que quebra no MP4 e não aparece no preview): todo elemento que anima depois começa escondido com `tl.set(..., {opacity:0})` em t=0 e entra com `fromTo(..., {immediateRender:false})`; movimento contínuo com `ease: "none"`; nada de `tl.to` relativo. Depois do render: `ffmpeg -i render.mp4 -vf freezedetect=n=0.0005:d=0.25 -f null -` — trecho parado fora de respiro intencional é "lapso".

## Passo 7 — Conferir

```bash
python3 "$SK/scripts/folha_original_x_clone.py" --original original/AD.mp4 --clone renders/clone.mp4 --saida qc/original_x_clone.jpg --tempos "<um tempo dentro de cada cena e logo depois de cada troca>"
python3 "$SK/scripts/folha_original_x_clone.py" --clone renders/clone.mp4 --varredura 4 --saida qc/clone_varredura_4fps.jpg
python3 "$SK/scripts/qc_lipsync.py" --video renders/clone.mp4 --voz voz/voz_clone.wav --palavras voz/voz_clone.json \
    --saida qc/lipsync_silencio_x_pico.jpg --fase "selfie:<t0>:<t1>:<x_boca>:<y_boca>" --fase "cozinha:..."
ffmpeg -i renders/clone.mp4 -af loudnorm=print_format=summary -f null - 2>&1 | grep -E "Input Integrated|Input True Peak"
```

**ABRA e OLHE cada folha** — retorno sem erro não prova nada. Lista do que precisa passar:

- [ ] **Nenhuma imagem da pessoa antiga** em nenhum quadro da varredura (inclui cabelo e mãos na borda do quadro e a legenda antiga vazando).
- [ ] O rosto da personagem **não muda** entre cenários e b-rolls.
- [ ] Original × clone: mesma estrutura, trocas no mesmo segundo.
- [ ] Lip sync: boca **fechada no silêncio, aberta e variada nos picos**, em cada cenário. Nunca reprove por correlação automática boca × áudio — ela dá falso reprovado em massa.
- [ ] Legenda contra a copy **palavra por palavra** (nome de produto, números, negativas).
- [ ] Loudness ≈ **−14 LUFS**, true peak ≤ −1 dBTP (senão `loudnorm` em dois passos).
- [ ] Sem "lapso" no `freezedetect`, sem quadro preto.

Mostre ao usuário as folhas e a lista do que está fora, antes de entregar.

## Passo 8 — Entregar

MP4 H.264, 9:16, 30 fps, AAC 48 kHz, com o nome no padrão do usuário (pergunte). Com hooks: uma versão por hook (hook + o mesmo corpo). Salve em `entrega/` e liste os arquivos com a duração de cada um.

## Custos de referência (conferir com `generate cost` na hora — tabela muda)

| Etapa | Motor | Ordem de grandeza |
|---|---|---|
| Retrato / cenário / b-roll still | `gpt_image_2_5` high 2k | ~3 créditos Higgsfield cada |
| B-roll animado 5 s | `kling3_0_turbo` 1080p | ~10 créditos Higgsfield |
| Lip sync | HeyGen Avatar IV (foto + áudio) | ~4 créditos premium por segundo |
| Voz | ElevenLabs TTS | caracteres do plano; 1 geração por candidata |

## Onde aprofundar

- `references/decupagem-modelo.md` — o modelo do decupagem.md com um exemplo real preenchido.
- `references/prompts-personagem.md` — prompts testados: retrato selfie, mesmo rosto em outro cenário, plano de "antes".
- `templates/gerar_index_exemplo.py` — a montagem real no HyperFrames.
- Skill `boas-praticas-black-belt` — as armadilhas de Higgsfield, HeyGen, ElevenLabs, HyperFrames e QC que valem aqui.
