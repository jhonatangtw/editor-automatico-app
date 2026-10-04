---
name: hooks-meat-hook
description: Pipeline completo de HOOKS novos no formato Meat Hook para ADs de DR em saúde — lê a copy com os comentários do copywriter, mapeia os hooks, gera start frames (GPT Image 2.5 / Nano Banana Pro) com sequência A/B/C de demonstração, coloca na timeline do Premiere para aprovação, anima no MiniMax H3 Max, unifica a voz por personagem (ElevenLabs STS), decupa silêncio + normaliza loudness, monta hook + body dos ADs validados (empilhamento ou troca do hook original), replica o pacote de SFX/transição que o editor montou na primeira sequência e renderiza no Media Encoder em EXPORT/ADxx. Use quando pedirem "trocar os hooks dos ADs validados", "gerar hooks meat hook", "colocar os hooks nos criativos", "fazer os 10 hooks da copy", "empilhar hook no AD", ou mandarem um doc de copy de hooks com referências. NÃO é para criar copy (copywriting), nem conferir AD pronto (conferir-ads-por-frame), nem hook sem geração de imagem/vídeo (hook-dr-saude só escreve).
---

# Hooks Meat Hook — do doc de copy aos 30 entregáveis

Conversa em português. Todo prompt de IA em inglês. Voz sempre **inglês americano**, números **por extenso**.

Os scripts em `scripts/` são do job NNN_XX e funcionam como MOLDE: edite as constantes do topo (PROJ, avatares,
dicionário de cenas `S`, clipes `C`, `ADS` com ponto de corte) antes de rodar. Rode tudo no scratchpad; mídia final
vai para a pasta do job, nunca importar do scratchpad.

## Portões (não pular)
1. **Tabela de hooks aprovada** antes de qualquer imagem.
2. **Start frames aprovados na timeline** antes de animar.
3. **Clipes conferidos** (fala × copy, movimento, voz) antes de montar.

## Etapas

### 1. Ler a copy
- `read_file_content` com `includeComments:true`. Comentários = direção de cena por hook.
- **Mapear comentário → hook pelo texto ancorado, nunca pelo horário** (erro que já custou H06/H07).
- As imagens de referência do doc NÃO saem pelo Drive (export "File too large"). **Peça print da referência de cada hook** — é ela que define o avatar (médico, padre, mulher japonesa…).
- Corpos: links no doc; baixar com `curl "https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t"` e conferir tamanho com o metadado.

### 2. Mapear
Tabela: Hook · fala EN · estrutura (6 da skill hook-dr-saude) · avatar/cenário · prop · planos. Avatar **por hook**
conforme a referência; mesmo personagem repetido = mesma âncora.

### 3. Abrir o job
Pastas `EXPORT FOOTAGE PROJECT MEDIA/{AUDIO,IMG,SRT,LEGENDA,AEF,BANCO,IA LIPSYNC}` + cópia do `Projeto Padrão.prproj`
(ver memória abrir-job-premiere). Raiz local: `…/Arquivo de Edição ` (espaço no fim).

### 4. Start frames — `scripts/frames.py`
- Padrão Meat Hook: celular 9:16 (iPhone 13 Pro 26mm f/1.5 ISO 500), prop "plastic medical teaching model" na lente,
  bandeira dos EUA grande atrás, terço de baixo livre, bloco anti-IA, frase final de pele obrigatória.
- **Demonstração = 3 frames**: A prop com gordura · B ritual derramando · C resultado (gordura caída na perna/no cepo).
- Antes × depois do mesmo personagem = **roupa diferente**.
- Âncora de avatar: `gpt_image_2_5` (9:16, 2k, quality high). Derivados, props anatômicos, pernas/pés: `nano_banana_pro`
  — o GPT copia o prop da referência (coração virou tubo, tornozelo virou braço).
- Identidade: passar frame anterior + âncora (`EXTRA_REFS`) e "IDENTITY IS CRITICAL: the SAME … as in BOTH reference images".
- Monitor: "reads EXACTLY 172 on the top line and 98 on the bottom line".
- Barrado (nsfw): trocar registro ("classroom model", "waxy pale-yellow", camisa abotoada, meia) e ir de Nano Banana Pro ou Grok Image.
- Conferir por mosaico (ffmpeg hstack) antes de mostrar. Reprovado → `START FRAMES/_REPROVADOS/`.

### 5. Aprovação — `scripts/premiere/place2.js`
Sequência `HOOKS - APROVACAO FRAMES` clonada da 9x16, 3 s por frame, 1 s entre hooks, marcador por frame, escala = 1080/largura.

### 6. Animar — `scripts/anim.py` (MiniMax H3 Max)
- `minimax_h3_max`, 768p, 9:16, `--start-image` (+ `--end-image` na transformação), 5–15 s. 2,5 créditos/s. Gera a fala junto.
- Prompt: trava de identidade · ação · "inhales … then says, exactly once: \"…\"" · voz · janela de fala em segundos · restrições.
- Movimento: "facing the direction he moves, never backwards". Escada olhando pra câmera = câmera no ALTO.
- Ação com beats ("para 3×"): beats em segundos + gerar 2 versões; escolher pela medição de movimento (diff quadro a quadro).
- Falhas conhecidas: derramar no próprio corpo falando → dividir em 2 clipes sem end image; fala só depois de 3 s mudos → começar em ~1 s; 1ª frase some com end image → "starts speaking right away with the words '…'".
- QC: `scripts/qc.py` (Whisper small, match × copy, 1ª palavra, tira de quadros). Número em dígito no Whisper não é erro.

### 7. Voz única — `scripts/voz.py`
Sempre que o hook tiver 2+ clipes: clonar (ElevenLabs IVC) a voz do 1º clipe do personagem, STS nos demais, trocar só o
áudio. O cofre de vozes da ElevenLabs tem poucas vagas: **um clone por vez, apagar só o `TMP_*`**. Original em `_REPROVADOS/*_voz_original.mp4`.

### 8. Decupar + loudness — `scripts/decupa.py`
silencedetect -40 dB / 0,3 s, margem 0,1 s, cauda 0,3 s após a última palavra (Whisper); `KEEP_TAIL` para cena que fecha
a demonstração depois da fala; `NO_DROP` se o Whisper marcar palavra curta fora do lugar. loudnorm 2 passos para o LUFS
dos corpos (~-14,3). **Transcrever o decupado e comparar com o copy.**

### 9. Montar — `scripts/premiere/mkads.tpl.js` + `rep.tpl.js` + `fadefix.tpl.js`
- Corpo AV1 → converter H.264 e **renomear** (`_h264`), senão o Premiere lê só áudio (cache).
- Ponto de corte: palavra (Whisper) + quadro (diff); o in-point arredonda para a grade 23,976 — **exportar o quadro da emenda**.
- Empilhamento = corpo inteiro; troca = corpo a partir do 1º quadro limpo depois do hook original.
- Editor monta o pacote de SFX/transição na 1ª sequência → `readhk1.js` lê; `rep.tpl.js` clona a sequência-modelo,
  troca V1/A1 e desloca V2/A3/A4 pela diferença; `fadefix.tpl.js` recria o fade-out da música (a transição não acompanha `clip.end`).
- Arquivo substituído no Drive com Premiere aberto → offline: `relink2.js` (`changeMediaPath`).

### 10. Render — `scripts/premiere/ame3.js`
Media Encoder, preset `…/systempresets/4E49434B_48323634/01 - Match Source - High bitrate.epr`, saída **local ASCII**
(`~/Movies/<job>_EXPORT/ADxx/`) — o Drive compartilhado chega deformado e falha tudo. Depois mover para
`EXPORT/ADxx/`, conferir 10 por AD, decodificar o fim de cada um, apagar `_1` e a pasta local. Nome:
`[DDMMAA][OT] NNN_XX ADxx HKn [Produto] [Squad].mp4`.

## Premiere por script
`scripts/pr.sh arquivo.js` roda ExtendScript pela porta 7842 (Tools PRO). Use `return` no fim. Clone de sequência:
achar a cópia pelo `sequenceID` novo, nunca por índice. Import: 1 arquivo por `importFiles`, até 6 por chamada.
