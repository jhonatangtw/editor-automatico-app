---
name: boas-praticas-black-belt
description: As armadilhas e receitas que já custaram horas e crédito em jobs reais de edição com IA — organizadas por ferramenta (Higgsfield, HeyGen, ElevenLabs, HyperFrames, Premiere/Tools PRO, ffmpeg/Whisper e QC), cada uma com sintoma, causa e o que fazer. Serve de consulta antes de gerar, montar ou entregar, e de AUDITORIA de um job (confere a pasta e os entregáveis contra a lista e devolve o que está fora, sem mexer em nada). Use quando pedirem "confere meu job contra as boas práticas", "o que pode dar errado nisso", "por que o Higgsfield/HeyGen/Kling deu erro", "deu 401/403", "o vídeo da HeyGen ficou travando no Premiere", "a cor do iPhone ficou lavada", "o Whisper inventou palavra", "a legenda saiu errada", "o lettering fica pulando", "o Premiere travou no import", "o script não aplicou o efeito", "baixei a imagem pequena", "o rótulo do produto saiu errado no lip sync", ou antes de qualquer etapa cara. NÃO executa a edição: aponta e explica. Para fazer o trabalho, use a skill do formato (editor-automatico-de-broll, clone-ad-validado, hooks-meat-hook...).
---

# Boas práticas Black Belt

O que já quebrou em job real e como não quebrar de novo. Cada item:
**Sintoma** (o que você vê) · **Causa** (o que está acontecendo de verdade) ·
**Faça** (o conserto ou a prevenção).

Dois jeitos de usar:

1. **Consulta** — antes de uma etapa cara, leia a seção da ferramenta. Quando algo der errado, procure pelo sintoma.
2. **Auditoria de um job** — siga "Conferir um job" no fim. Você só LÊ e aponta; não conserta, não regera, não reexporta sem o usuário pedir.

Três regras que atravessam tudo:

- **Retorno de sucesso não prova resultado.** Ferramenta que diz "ok" pode ter feito nada (efeito não aplicado, clipe no lugar errado, miniatura no lugar da imagem). Prove lendo de volta, medindo com `ffprobe`, ou OLHANDO um quadro.
- **Timeout não quer dizer que nada aconteceu.** Leia o estado antes de repetir — repetir geração é pagar duas vezes; repetir escrita no Premiere duplica.
- **Aprovação antes de gastar crédito**, com a estimativa na mesma mensagem.

---

## Higgsfield

**MCP para de responder (401)**
- Sintoma: toda chamada do MCP volta `401 Unauthorized` / `AUTH_HEADER_REJECTED`.
- Causa: a sessão do MCP expira sozinha.
- Faça: use o CLI `higgsfield`, que tem login próprio. Se o CLI responder `Not authenticated` (falta o arquivo de credencial do CLI), **pare de tentar variações**: o usuário precisa rodar `higgsfield auth login` num terminal dele (é login por navegador). Enquanto isso, adiante o que não gera (análise, copy, prompts, estrutura).

**"Falhou" mas cobrou — saída JSON em array**
- Sintoma: o script diz que o envio falhou; o saldo caiu.
- Causa: `generate create ... --json` imprime um **array de ids** (`["5cea..."]`), não `{"id": ...}`. Parser de objeto devolve erro com o job já criado. O `generate get --json` às vezes traz linha extra depois do objeto ("Extra data").
- Faça: leia o array direto; para o `get`, `json.JSONDecoder().raw_decode(texto[texto.find('{'):])`. **Se o parser falhar, não reenvie** — rode `higgsfield generate list --image --json` (ou `--video`) e case job ↔ prompt pelo texto.

**Imagem baixada pequena (~600 px)**
- Sintoma: a imagem "2k" tem 600×745; às vezes o `.jpg` é webp.
- Causa: o JSON traz `result_url` (cheia), `min_result_url` (miniatura) e a URL da mídia de entrada. "Primeira URL do JSON" pega a errada.
- Faça: sempre `result_url`; confira com `ffprobe -show_entries stream=width,height` antes de copiar para o job.

**`--wait` volta sem resultado com vários jobs ao mesmo tempo**
- Sintoma: com 10+ jobs simultâneos, `--wait` devolve sem `result_url`; sozinho funciona.
- Causa: estoura o tempo interno de espera; o job continua na fila e termina normal.
- Faça: `--wait --wait-timeout 50m --wait-interval 20s`, ou submeta sem `--wait` e acompanhe com `generate list`/`get`. (Num caso real: de 23 vídeos em 90 min com falhas para 41 em 10 min sem nenhuma.)

**Lote de planos diferentes saiu tudo igual (nano_banana com referência)**
- Sintoma: 20 planos "diferentes" com o mesmo enquadramento da imagem de referência.
- Causa: o `nano_banana_pro` usa a referência como **composição**, não só como estilo.
- Faça: para b-roll abstrato/3D, **sem referência** — um bloco de estilo e material idêntico em todos os prompts + uma linha `CAMERA:` diferente por plano (macro, corte, rasante, de cima). Referência só quando o que precisa repetir é identidade (personagem, frasco).

**Plano 3D virou foto (ou foto antiga)**
- Sintoma: nos planos em que o ambiente domina, o estilo 3D some; sai foto real, às vezes preto e branco, carro antigo, letreiro legível.
- Causa: descrição de cenário puxa o modelo para o fotográfico; a trava de estilo no fim do prompt não segura.
- Faça: personagem 3D como referência em **toda** cena (crie âncora até para figurante); abra o prompt com "A FRAME FROM A PIXAR 3D ANIMATED MOVIE. EVERYTHING in the frame is rendered in the SAME stylized 3D style. THIS IS NOT A PHOTOGRAPH."; feche com "Present day, not vintage, not black and white, NO signs, NO lettering". Espelho: exija "the mirror's frame must be visible" ou saem duas pessoas.

**Persona com produto na mão (GPT Image 2.5)**
- Sintoma: rosto e rótulo ótimos, mas o frasco do tamanho da mão inteira; punho fechado cobrindo a marca; calendário/lista ao fundo legível.
- Causa: o GPT Image 2.5 acerta grafia e mãos de primeira, mas ignora escala escrita no meio do prompt.
- Faça: `gpt_image_2_5 --quality high --resolution 2k` com foto do frasco + close do rótulo como referências. Bloco de produto por ÚLTIMO, aberto pela escala: "SCALE IS CRITICAL: TINY bottle, its full height is only the length of the index finger… held delicately by the base with the fingertips — like holding an egg — so the whole front label stays exposed; the hand is clearly BIGGER than the bottle", e "THIS OVERRIDES EVERYTHING ABOVE". Fundo: "Any calendar, list, book, sign or packaging in the background is out of focus and unreadable". Mesma pessoa em outra imagem: passe o **id do job** da primeira como `--image-references` + "IDENTITY: the SAME person as in the reference image".

**GPT Image copiou o objeto da referência**
- Sintoma: pediu "modelo de coração", saiu o mesmo tubo da imagem de referência; número errado num visor.
- Causa: com referência, o GPT Image copia o PROP; e é mais sensível ao filtro de conteúdo.
- Faça: para objeto/prop e número exato, `nano_banana_pro` (escreva "EXACTLY 172 on the top line"). Barrado por conteúdo: reescreva a cena (roupa abotoada, objeto de sala de aula) ou troque de motor.

**"Cara de IA" mesmo com specs de câmera**
- Sintoma: pele lisa, dente branco, luz perfeita, cenário arrumado — parece banco de imagem.
- Causa: specs de câmera dizem "é foto", mas não impedem a estética de stock.
- Faça: ordem **cena → specs de câmera → bloco anti-stock → trava de produto → frase final de pele**. Bloco anti-stock: "not a stock image, not a commercial shoot, not an AI render"; cômodo vivido com bagunça pequena; uma janela realmente estourada e duas temperaturas de cor no rosto; rosto assimétrico item a item (olho menor, sobrancelha desigual, manchas, dente marfim, lábio seco); mãos com veia e tendão; grão 35 mm e filme nomeado (Portra 400); "no beauty filter, no HDR glow, no digital sharpening halo, no glossy plastic sheen, no teal-and-orange grade". Efeitos colaterais: "film grain" às vezes desenha moldura preta (recorte); expressão espontânea faz olhar para fora — exija "looking straight into the lens".

**Kling: 403 com crédito sobrando**
- Sintoma: `403 Forbidden` no `generate create`; `higgsfield account status` mostra saldo.
- Causa: **moderação** — descrição de corpo ("soft belly", "overweight", "abdomen") no prompt.
- Faça: tire a descrição de corpo; descreva roupa, pose e enquadramento; "non-sexual, everyday, documentary". Em outros motores o mesmo bloqueio volta como status `nsfw`, não `failed`.

**Kling com fala (lip sync nativo)**
- Sintoma: procurou parâmetro de áudio no Kling e não existe.
- Causa: nenhum Kling do Higgsfield recebe áudio.
- Faça: `kling3_0 --mode pro --sound on --start-image <âncora>` com a fala entre aspas no prompt (+ sotaque, ex. "American English accent"): voz e boca saem juntas. A voz muda entre clipes e às vezes inventa palavra — confira cada clipe com Whisper e unifique a voz com ElevenLabs speech-to-speech. Voz exata (sua locução): use `wan3_0` com `--image` (não `--start-image`) + `--audio`, `--generate-audio false`, duração inteira de 2 a 30 s.

**Formato e duração de cada motor**
- Sintoma: geração recusada depois de aprovada; ou 4:5 que não existe.
- Causa: cada motor tem regra própria: Seedance mínimo 4 s; `kling2_6` só 5 ou 10; `kling3_0_turbo` mínimo 3 e sem 4:5 (sai 1076×1928, 24 fps).
- Faça: `higgsfield model get <motor>` antes; cena curta gera no mínimo e apara na timeline; 4:5 = gere 9:16 e recorte o centro.

**Outras do CLI**
- O CLI não apaga geração (só cria/lista/consulta) — apagar é pela web.
- Caminho de pasta com colchetes (`[010125][XX] Job`) quebra `glob.glob` em Python sem erro (colchete vira classe de caracteres): use `os.listdir` + filtro.

---

## HeyGen

**Avatar IV × Avatar V em pessoa gerada por IA**
- Sintoma: Avatar V recusa a foto ("No cross-reference candidate…") ou recusa `expressiveness` / `motion_prompt`.
- Causa: o V exige avatar **treinado** e só aceita direção de movimento com filmagem real da pessoa.
- Faça: persona de IA → **Avatar IV** com foto + áudio (`"type":"image"`, `audio_asset_id`, `expressiveness`, `motion_prompt`). O V fica para avatar treinado com filmagem.

**Vídeo da HeyGen engasgando no Premiere (25 × 23,976)**
- Sintoma: a boca "pula" quadro; parece lip sync ruim.
- Causa: a HeyGen entrega **25 fps**; a sequência em 23,976 derruba quadro na conversão.
- Faça: case a sequência com a fonte (25 fps). Por script: `var t=new Time(); t.ticks="10160640000"; st.videoFrameRate=t;` — passe o número **já calculado como texto**; `String(254016000000/25)` com a divisão dentro quebra a base de tempo. Ou `t.seconds = 1/25`.

**"Sem crédito" na HeyGen, mas tem**
- Sintoma: a consulta de cota pela chave de API mostra quase zero.
- Causa: são **dois bolsos**: a carteira da API (chave) e os créditos da assinatura (login do CLI por OAuth).
- Faça: `heygen auth status` mostra o saldo do bolso certo para quem gera pelo CLI. Referência: ~4 créditos premium por segundo de vídeo de foto.

**Upload "falhou" (id × asset_id)**
- Sintoma: o upload parece não devolver nada.
- Causa: `heygen asset create` devolve `id` para imagem e `asset_id` para áudio.
- Faça: leia as duas chaves. Limite de 32 MB por arquivo — áudio longo vai em mp3.

**Vídeo saiu deitado / payload recusado**
- Sintoma: 1920×1080 quando queria vertical; erro de "discriminator".
- Causa: só `resolution` não define orientação; e o formato do corpo da API muda com o tempo.
- Faça: `"aspect_ratio":"9:16"` sempre. Payload recusado: mande `{"type":"<tag>"}` sozinho e leia o erro — a API diz qual campo falta, um por vez.

**Mesma expressão do começo ao fim**
- Sintoma: avatar com a mesma cara em 2 minutos de fala.
- Causa: uma geração = um `motion_prompt`; prompt de uma emoção só dá uma expressão.
- Faça: gere a copy inteira numa geração (até ~5 min; sem emenda) com um `motion_prompt` que descreve o **arco**: a ordem das intenções, as ênfases, quando muda a expressão, e o pedido de variar o gesto. Segmente só para refazer um trecho ou passar do teto.

**Rótulo do produto reescrito no lip sync**
- Sintoma: no vídeo falante, a marca do frasco vira letras embaralhadas.
- Causa: o lip sync regenera os pixels e corrompe texto miúdo (HeyGen IV/V e outros motores; pedir no prompt não adianta).
- Faça: **não regere por causa de rótulo**. Recole o frasco do still aprovado por cima: recorte frasco + mão do still (no tamanho do vídeo), ache a posição em cada quadro com `cv2.matchTemplate(TM_CCOEFF_NORMED)` numa janela ao redor (a FORMA sobrevive mesmo com o texto corrompido), cole com borda suavizada e reencode em H.264 CRF 16. Confira à mão os quadros de casamento baixo (< 0,7). Regere só por rosto, boca ou pose.

---

## ElevenLabs

**TTS não é idempotente**
- Sintoma: regerou a mesma fala, a legenda dessincronizou.
- Causa: mesmo texto, mesma voz, mesmos ajustes → durações diferentes (±0,4 s por frase).
- Faça: regerou o áudio, regere o JSON de tempos **junto** e recalcule legenda e encaixes a partir dele. Guarde áudio + JSON lado a lado na pasta do job.

**Legenda que bate de verdade**
- Faça: `POST /v1/text-to-speech/{voz}/with-timestamps` devolve o áudio e o tempo de cada caractere; agrupe em palavras e corte a legenda em cima disso. Estimar por palavras/segundo sempre deriva.

**"A chave morreu" (401 em /v1/user)**
- Sintoma: `/v1/user` devolve `missing_permissions`.
- Causa: chave de escopo restrito — TTS, vozes e clone funcionam.
- Faça: não diagnostique a chave por `/v1/user`; teste com o que você vai usar.

**Cofre de vozes cheio**
- Sintoma: clonar devolve `voice_limit_reached`.
- Causa: teto de vozes customizadas do plano.
- Faça: **pergunte antes de apagar** qualquer voz (é irreversível); clone temporário com nome marcado e apague só ele no fim.

**Speech-to-speech (trocar a voz mantendo o tempo)**
- Faça: `POST /v1/speech-to-speech/{voz}` com `eleven_multilingual_sts_v2` preserva o tempo das palavras (desvio ~15 ms) — serve para unificar a voz de um personagem entre clipes gerados. Saída PCM pode ser recusada fora do plano Pro: peça `mp3_44100_128` e converta.

**Escolher a voz**
- Sintoma: a voz "não combina", soa infantil, ou "batida".
- Causa: F0 e ritmo se medem; idade percebida, sotaque e timbre não.
- Faça: gere a mesma fala com 2–3 candidatas, meça **F0 mediano** (mulher ~165–255 Hz, homem ~85–155 Hz) e palavras/min contra a voz de referência, e **leve as amostras ao ouvido do usuário na primeira rodada** — de preferência na timeline, com a imagem de cada personagem. Ritmo se corrige depois (`atempo` até ~1,15x passa despercebido).
- Anúncio para os EUA: **inglês americano**, sempre. Números por extenso no texto.

**Voz do personagem mudou entre clipes**
- Causa: cada geração de vídeo com som nativo inventa uma voz.
- Faça: guarde a voz do **1º clipe** como referência, clone-a (temporário) e passe todos os clipes desse personagem por speech-to-speech; troque só o áudio no MP4 (`-c:v copy`).

---

## HyperFrames

**Lettering "pulando" (tranco)**
- Sintoma: o texto aparece pronto, some e entra animado.
- Causa: `fromTo(..., {immediateRender:false})` num elemento que já estava visível.
- Faça: todo elemento que anima depois começa escondido: `tl.set(el, {opacity:0}, 0)` (ou dentro de um pai escondido até o tween dele).

**"Lapso" antes do corte**
- Sintoma: sensação de imagem travada no fim de cada cena.
- Causa: câmera com `sine.inOut` por cena zera a velocidade no fim.
- Faça: deriva contínua com `ease: "none"` e troca cruzada (a nova entra por cima, a velha sai depois). Cena só de texto precisa de um pouco de deriva (~1,10 de escala) para não parecer congelada.

**Palavras saltam de lugar**
- Causa: empurrar elementos em Z (perspectiva) a cada batida desloca na tela.
- Faça: para empilhar palavras, só escureça as anteriores.

**Certo no preview, errado no MP4**
- Causa: o render busca quadros fora de ordem; `tl.to` relativo depende do estado anterior.
- Faça: `fromTo` explícito em tudo. Depois do render: `ffmpeg -i render.mp4 -vf freezedetect=n=0.0005:d=0.25 -f null -` e uma sequência de 6 quadros (0,1–0,2 s) na entrada de um lettering.

**Outras**
- Vídeo inserido com poucos keyframes faz o render pegar quadro errado: reencode com GOP curto (ex.: 30 fps, `-g 30`).
- Fonte sem `@font-face` local: o lint reclama e o render usa fonte do sistema.
- Composição gerada por script: edite o **gerador** e rode de novo; edição à mão no HTML some na próxima geração.

---

## Premiere / Tools PRO

**Efeito "aplicado" que não aplicou (Premiere em português)**
- Sintoma: a ferramenta diz ok (`updated: false`, ou sem erro) e nada mudou.
- Causa: o efeito foi procurado pelo nome em inglês. A tradução é **mista**: `Movimento`, `Escala`, `Posição`, `Opacidade`, `Transformar` em português; `Track Matte Key` em inglês.
- Faça: procure por uma **lista de candidatos** (PT e EN), informe qual nome funcionou, e confira o valor lido de volta. O efeito Recortar pela QE "entra" sem erro e não aplica: use as propriedades escondidas de corte do próprio `Movimento` (`Corte à esquerda/superior/à direita/inferior`).

**Clipe no lugar errado / sequência 1 quadro fora**
- Sintoma: todos os clipes empilhados no 0; ou tudo "1 quadro curto".
- Causa: `overwriteClip(item, "36.56")` com texto é aceito e posiciona no zero; a base de tempo real (`sequence.timebase`) pode não ser 254016000000/fps exato.
- Faça: sempre `var t=new Time(); t.seconds=36.56; track.overwriteClip(item, t)`; leia `sequence.timebase` em vez de calcular; **nunca `insertClip`** (empurra o resto). Leia `start`/`end` de volta.

**Tudo dá timeout depois de criar sequência (modal)**
- Sintoma: até leitura simples estoura o tempo; o servidor do Tools PRO responde na hora.
- Causa: `createNewSequence` abriu o diálogo "Nova sequência", que prende o Premiere e a ponte.
- Faça: peça ao usuário para olhar o Premiere e clicar **Cancelar** (Esc pelo script não funciona — a thread está presa). Prevenção: crie sequência por `createNewSequenceFromClips` ou clonando uma que já tenha o formato (`seq.clone()`, renomear, esvaziar).

**Premiere congelado no import em lote**
- Sintoma: depois de importar vários arquivos de uma vez, toda chamada dá timeout; CPU do Premiere em 0 % com memória alta.
- Causa: deadlock do motor de script no `importFiles` em lote.
- Faça: não adianta esperar — só fechar à força. Antes, copie o `.prproj`; ao reabrir, confira a pasta **Auto-Save** (ela costuma ter o import que o save não pegou). Prevenção: um arquivo por `importFiles`, poucos por execução. `.wav`: `setInPoint(t, 2)` (mediaType 2) — com 1 não recorta e entra o arquivo inteiro.

**Centenas de clipes**
- Sintoma: colocar 100+ clipes de uma vez estoura o tempo e pendura o painel.
- Causa: resolver cada nome varrendo o projeto vira quadrático.
- Faça: monte o mapa nome→item uma vez no script, coloque em lotes de ~50 com pausa, e leia de volta em páginas (o retorno grande vem truncado). Confira contagem, sobreposição e buracos.

**Mídia "atualizada" que não atualiza / some**
- Sintoma: regravou o MP4 no mesmo caminho e o Premiere mostra a duração antiga, ou o item fica offline.
- Causa: cache do Premiere.
- Faça: importe com **nome novo** (`_v2`), ou `item.changeMediaPath(caminho, true)`. AV1 importa **só com áudio**, sem erro: converta para H.264 com nome novo.

**Mídia offline no dia seguinte**
- Causa: foi importada de pasta **temporária** (do sistema ou da sessão da IA), que é limpa sem aviso.
- Faça: tudo que entra num projeto (TTS, imagem gerada, render intermediário) é gravado **na pasta do job antes de importar**. Temporário só para o descartável (quadros de conferência, logs).

**Export pelo script derrubou o Premiere**
- Causa: export direto lê a fonte; arquivo em nuvem não materializado trava tudo.
- Faça: antes de exportar, teste a leitura da fonte (ler os primeiros MB com timeout); se travar, peça cópia local ("Disponível offline").

**Apagou trilha de áudio sem querer**
- Causa: em `qe.removeTracks(...)`, o 3º argumento é a **quantidade de trilhas de áudio** a remover, não uma opção.
- Faça: teste em cópia; confira contagem de clipes de áudio e o fim de cada trilha antes e depois.

**Valores que não são o que parecem**
- Modo de mesclagem (componente Opacidade): Normal = 18, **Tela (Screen) = 22**, **Add = 14**, Multiplicar = 17. Overlay de luz com fundo preto precisa de Tela.
- Volume (componente Volume, "Nível"): `v = 10^((dB − 15)/20)`; 0 dB = 0,1778; teto 1,0 = +15 dB (acima é cortado em silêncio).
- Keyframe de clipe é no **tempo da fonte**: `inPoint + (t_sequência − start)`.

**Regras por nome pegando item errado**
- Causa: fragmento curto casa em tudo (`vo` em "no**vo**_beat", `h1` em "arc**h1**").
- Faça: palavra longa por "contém"; fragmento curto só por "começa com"; sempre com condição de tipo junto.

---

## ffmpeg / Whisper

**Whisper inventa ou engole fala**
- Sintoma: falso começo, take repetido ou frase faltando que não existem; palavra com 1,4 s de duração; loop repetindo a mesma frase.
- Causa: passada longa (sobretudo em cima de silêncio) alucina; o `medium` também colapsa frase inteira numa palavra.
- Faça: passada longa só para **localizar**; confirme cada achado recortando a janela (`ffmpeg -ss X -t 20`) e transcrevendo com `medium`/`large-v3` e `--word_timestamps True`. Palavra dentro de um corte: meça o nível — pico abaixo de ~−26 dBFS é alucinação. Palavra com duração absurda (> 1,5 s em fala corrida) = trecho engolido; repasse com `large-v3` antes de afirmar que a fala não foi gravada.
- Minuto formatado com `f"{t/60:.0f}"` arredonda (7:34 vira 8:34): use `int(t // 60)`.

**Vídeo HDR do iPhone ficou lavado**
- Sintoma: cor cinza-esverdeada, parede estourada depois do corte.
- Causa: bruto HEVC 10 bits HLG (bt2020); `libx264 yuv420p` descarta o HDR e as tags.
- Faça: `-c:v hevc_videotoolbox -pix_fmt p010le -tag:v hvc1 -color_primaries bt2020 -color_trc arib-std-b67 -colorspace bt2020nc -color_range tv` (no Mac), ou converta para Rec.709 no Premiere com tone map. A rotação −90 já é aplicada — confira com `ffprobe`. Acelerar 1,1x a 60 fps mostra `drop` de ~10 % no log: é o esperado.

**`scene detect` não acha corte nenhum**
- Sintoma: `select='gt(scene,0.1)'` devolve lista vazia num vídeo com cortes.
- Causa: falha em VP9/AV1 (vídeo baixado de rede social).
- Faça: diferença média de luminância entre quadros em miniatura (`fps=30,scale=96:-1`, `np.abs(q - anterior).mean()`), corte onde passa de média + 5 desvios; confira o quadro antes e depois de cada candidato.

**Texto no quadro de conferência**
- O ffmpeg de muitas instalações não tem `drawtext`: desenhe timecode com PIL.

**GIF pesado**
- Causa: o que pesa é quantos pixels mudam por quadro; push-in faz todos mudarem.
- Faça: no prompt do vídeo, "THE CAMERA NEVER MOVES: no push-in, no zoom, no dolly, no drift" e anime só o conteúdo; `hqdn3d` antes do `palettegen`; cascata 800/12/192 → 720/12/160 → 640/12/128 → 640/10/128 → 600/10/96 até caber.

**Corte de master de câmera ALL-I**
- Faça: cópia pura (`-c copy`), sem reencode. Áudio por filtro (`atrim`+`concat`), vídeo por `-frames:v n` com `n = round((fim−início)*fps)`; o concat com `inpoint/outpoint` perde áudio a cada emenda. QC: duração do formato, do vídeo e do áudio iguais.

**Legenda deriva depois de muitos cortes**
- Causa: cada pedaço sai alguns ms mais longo (encaixe no quadro); 45 emendas = 1,3 s de atraso.
- Faça: meça a duração REAL de cada pedaço com `ffprobe` e remapeie os tempos com ela.

**`silencedetect` não pegou tempo morto**
- Causa: respiração/ruído acima do limiar. Corte de silêncio não substitui ler a transcrição.

**Transparência sumiu no MP4**
- Causa: `yuv420p` descarta alfa; máscara feita no canal alfa sai inteira visível.
- Faça: componha sobre fundo dentro do mesmo filtro (`overlay`), ou exporte com alfa (ProRes 4444) quando for camada.

**Arquivo na nuvem (Drive) travando o ffmpeg**
- Causa: arquivo não materializado; o ffmpeg fica preso em I/O.
- Faça: `du -h` (tamanho muito menor que o real = não baixado); copie para disco local antes (cópias em paralelo são muito mais rápidas que em fila) e compare o tamanho local × remoto — um `cp` pode morrer calado e deixar arquivo truncado.

---

## QC (conferência)

**Legenda queimada errada que ninguém viu**
- Sintoma: palavra errada na tela, no ar, em todas as versões de hook.
- Causa: a legenda é gerada de um `.srt` **cru de transcrição automática**; o editor corrige alguns erros e deixa outros (nomes de produto e de medicamento, números, negativas: "isn't" → "is").
- Faça: compare a legenda (o `.srt` e o que está na tela) com a **copy, palavra por palavra** — não por amostragem. Regra: **tempo do áudio, texto da copy**. E o inverso: transcreva o áudio final — locução e legenda podem divergir.

**Lip sync "reprovado" em massa**
- Causa: correlação automática "abertura da boca × volume" é dominada por sombra, barba e movimento de cabeça (num lote real, 42 de 68 falsos reprovados).
- Faça: por cenário, um quadro na pausa mais longa (boca fechada) e 3–4 quadros nos picos de volume (boca aberta, vogais diferentes), recortados na boca, numa folha só. Correlação serve no máximo para ordenar suspeitos; pico de correlação na borda da janela de busca = descarte a medida.

**Copiar a legenda de uma referência**
- Causa: detectar a faixa de legenda automaticamente trava na linha dos olhos/boca e lê camisa clara como texto.
- Faça: cadência pelos cortes (`scene` + agrupar a < 0,22 s), posição a olho com grade, e o **corpo da fonte pela largura** do texto medido na referência (busca binária do tamanho que reproduz a largura). Sobreponha o seu render no quadro da referência: a legenda dela tem que sumir sob a sua.

**Detector de colagem/letterbox acusando demais**
- Faça: use para ordenar; decida na folha de contato (num caso, 4 de 36 "suspeitos" eram reais).

**Áudio que acaba antes do vídeo**
- Causa: preset de export; não vira silêncio detectável.
- Faça: compare a duração do vídeo e do áudio no `ffprobe` de todo entregável.

**Loudness**
- Alvo para redes: **−14 LUFS integrado, true peak ≤ −1 dBTP**. Meça com `loudnorm=print_format=summary`; corrija em dois passos. Hook e body com loudness diferentes: normalize o hook antes de juntar.

---

## Conferir um job (modo auditoria)

Peça a pasta do job (e a copy, se houver). Então, **só lendo**:

1. **Inventário**: liste entregáveis e mídia; ache arquivo que mora em pasta temporária ou em nuvem não materializada.
2. **Cada entregável** (`ffprobe`): resolução e proporção pedidas, fps (25 × 23,976 misturados?), codec, tags de cor (HDR que devia ser SDR?), duração do vídeo = do áudio, nome no padrão.
3. **Imagem**: mosaico de quadros (`fps=1/2,scale=200:-1,tile=8x4`) — preto, congelado, letterbox, colagem, texto queimado de IA, deriva de rosto/estilo, rótulo do produto corrompido. `freezedetect` e `blackdetect`.
4. **Fala e legenda**: transcreva o áudio final (por janelas) e compare com a copy palavra a palavra; compare a legenda na tela com a copy.
5. **Lip sync** (se houver avatar gerado): folha silêncio × pico por cenário.
6. **Som**: loudness e true peak de cada entregável.
7. **Premiere** (se o projeto estiver aberto e o usuário quiser): mídia offline, fps da sequência × fonte, clipes sobrepostos ou buracos — por leitura.

Entregue uma lista curta: **✓ o que passou · ✗ o que está fora (com o tempo, o arquivo e a evidência) · o conserto sugerido** (citando a seção desta skill). Não conserte sem o usuário pedir.
