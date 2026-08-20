# Armadilhas — todas descobertas na prática, custaram tempo real

## Whisper

**Não forçar `--language`.** O body pode estar em inglês mesmo com copy PT-BR no documento. Forçar `pt` num áudio inglês faz o modelo "ouvir" português onde não há: `matchá`→"mancha", `Mounjaro`→"manjarra", `burning fat`→"fatia". O timing continua certo, o texto vira lixo.

**Sempre diffar contra a copy.** O `large-v3` acerta o timing mas erra nome próprio e às vezes picota frase. Num vídeo de 414 palavras escaparam 4 erros: `MOUNJARO`→"MANJARO" (2×), `following this`→"follow-up", `100%`→"100 %". Corrigir o **texto** pela copy e manter o **timing** do Whisper.

```python
import difflib
sm = difflib.SequenceMatcher(None, palavras_doc, palavras_srt)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag != 'equal': print(tag, doc[i1:i2], '->', srt[j1:j2])
```

**Sobreposição de blocos.** Se você aplicar duração mínima por bloco, clampar depois: `fim = min(fim, inicio_do_proximo)`. Sem isso dois blocos aparecem juntos e a legenda pisca.

---

## ffmpeg

**SAR não-quadrado quebra o `concat`.** Body de avatar costuma vir com SAR tipo `1935:1936`. Segmentos escalados saem `1:1` e o concat falha com *"parameters do not match"*. Pôr `setsar=1` em **todo** segmento.

**`blend=all_mode=screen` em YUV tinge o vídeo INTEIRO.** Preto em YUV limitado é `Y=16, U=V=128`, não zero — screen levanta a luma e desloca a croma nos dois planos, e o resultado é uma dominante magenta em tudo. Converter os dois lados antes e voltar depois:
```
[main]format=gbrp[a];[fx]format=gbrp[b];[a][b]blend=all_mode=screen,format=yuv420p[out]
```

**Não montar camada de efeito com `overlay` sobre base preta + `enable`.** O `overlay` segura o último frame fora da janela e o efeito vaza pro vídeo todo. Usar `tpad` pra criar um stream do tamanho completo, preto fora da janela, e blendar em screen (neutro com preto em RGB):
```
[fx]trim=A:B,setpts=PTS-STARTPTS,tpad=start_duration=<pre>:stop_duration=<post>:color=black[layer]
```

**`-vsync vfr` conflita com `-r`.** Para CFR a partir de um concat de durações variáveis, usar `-vf fps=25` e não `-vsync`.

**Este ffmpeg não tem `libass`, `drawtext` nem `subtitles`.** Legenda se desenha com PIL e vira PNG → concat → ProRes 4444 (`yuva444p10le`). Tem `overlay`, `blend`, `tpad`, `prores_ks`, `qtrle`.

**`volumedetect` não imprime neste build.** Medir nível decodificando para `s16le` e calculando RMS em Python.

**Glob vazio no zsh aborta o comando.** `rm -f *.png` com zero matches mata o resto da linha.

---

## Antes de qualquer coisa: quem está do outro lado?

**Chamar `pr_midia_info` (Tools PRO) no começo.** Se responder, ele está ligado e é quem deve operar a timeline — local, ~3 ms, sem login.

Se não responder, tentar `get_host_status` (Higgsfield). Se vier `ppro: true`, usar as `pr_*` dele.

Como ligar o Tools PRO: painel → **Conectar IA** → **Ligar** → colar o comando no terminal, uma vez só. Detalhes em `mcp-premiere.md`.

**Se não estiver conectado, NÃO improvisar.** Especificamente:

- **Nunca editar o `.prproj` diretamente com o projeto aberto** — o Premiere sobrescreve ao salvar e o trabalho é perdido. É a única saída *destrutiva* disponível, e por isso a mais tentadora.
- Não descompactar o XML do projeto para "injetar" marcador.

O certo é **avisar que falta a conexão e parar**. Se o usuário não puder conectar agora, a saída não-destrutiva é entregar a lista de timecodes em texto — ele mesmo marca — ou um CSV de marcadores para importar em Marker Panel → Import Markers. Nunca escrever no arquivo do projeto.

## Premiere — as que mais custam tempo

**A SEQUÊNCIA ATIVA MUDA QUANDO O USUÁRIO CLICA NOUTRA ABA.** Toda ferramenta age na ativa. Ler o estado, o usuário clicar noutra aba, e escrever depois = escrever na sequência errada. Aconteceu: **17 marcadores de um job real apagados** no lugar dos de um teste.
→ Declarar o nome no campo `sequencia` (obrigatório em `pr_marcadores_apagar`). Se não bater com a ativa, a operação morre sem tocar em nada. E reler `pr_marcadores_info` **imediatamente antes** de escrever — não confiar em leitura de minutos atrás.

**`pr_autoclip` corta em TODOS os marcadores, inclusive nos de anotação.** Isso bastava quando marcador só queria dizer "corte aqui". Agora a automação usa marcador como sugestão de B-roll e lettering — rodar o AutoClip numa sequência anotada pica o body em vinte pedaços.
→ `pr_autoclip_info` devolve a contagem por cor. Filtrar com `ignorarCores: [1,2,6]` e simular antes.

**Simular antes de destruir.** `simular: true` em `pr_autoclip`, `pr_marcadores_apagar`, `pr_timeline_colocar` e `pr_midia_importar` devolve o que *seria* feito. Não há desfazer pelo MCP — a diferença entre "3 cortes" e "20 cortes" é a diferença entre uma edição e um estrago.


**DOIS PROJETOS ABERTOS = ESCRITA NO PROJETO ERRADO.** A pior de todas. Com mais de um projeto aberto, `pr_get_project_info` e `pr_get_active_sequence` passam a **discordar sobre qual sequência está ativa**, bins criados vão parar no projeto em foco, e um `pr_overwrite_to_timeline` coloca o clipe de um job dentro da timeline de outro. Aconteceu de verdade: um `HK2.mp4` entrou no lugar de um insert, e três imports sumiram num projeto de outro cliente.
→ **Checar `pr_get_project_info` no começo de cada lote.** Se o nome não for o do job, parar e pedir para fechar os outros. Se as duas leituras discordarem, o estado do plugin está corrompido — fechar e reabrir o Premiere resolve.

**NodeIds são RECICLADOS depois de salvar/reabrir.** O id que um `pr_import_media` devolveu pode, minutos depois, apontar para outro item. Nunca guardar id entre etapas: reler com `pr_list_project_items` imediatamente antes de usar.

**`ReferenceError: undoStackIndex is not a function`** — erro interno do plugin numa chamada de escrita. **A operação pode ter aplicado PELA METADE**: já aconteceu de o clipe entrar na timeline e o `drop_audio` falhar, deixando o áudio do B-roll no A2. Reler `pr_get_active_sequence` e corrigir só o que faltou; não repetir a chamada inteira.

**A conexão do plugin cai sozinha.** Duas vezes numa sessão. `get_host_status` antes de cada lote de escrita.

**Sobrescrever mídia no mesmo caminho fica em cache.** Ao corrigir um clipe já importado, salvar com **nome novo** (`_v2`) e reimportar — senão o Premiere continua exibindo a versão antiga.

**Arquivo que existe na pasta não está no projeto.** Nove b-rolls prontos estavam parados nos três ADs simplesmente porque ninguém os importou — `pr_timeline_colocar` responde *"não achei no projeto"*. Conferir com `pr_midia_listar` antes de concluir que o material não existe.

## Premiere (plugin Higgsfield)

**Interface em PT-BR quebra `pr_set_clip_transform`.** A tool procura o efeito `Motion`, não acha `Movimento`, e retorna `{"updated": false, "changes": {}}` **sem erro**. Usar:
```
pr_set_effect_property(effect_name="Movimento", property_name="Escala", value=112)
```
e conferir o `actual` no retorno. Descobrir nomes com `pr_get_effect_properties`. Propriedades: `Posição`, `Escala`, `Rotação`, `Ponto de ancoragem`.

**`pr_create_caption_track` mente nos dois sentidos.** Já retornou `verified:false, captionTracks:0` tendo **criado** a track (que queimou no export), e já retornou o mesmo tendo **não criado** nada. `pr_list_sequence_tracks` não enxerga caption track. Não existe tool pra deletar. **Recomendação: não usar.** Entregar o `.srt` no bin e deixar o usuário arrastar pra timeline.

**`pr_export_sequence_frame` falha com `upload failed (400)`.** Não é transitório. Sem QC visual pelo Premiere — conferir exportando e abrindo o MP4 com ffmpeg.

**Export exige `.epr`.** Nem `pr_export_sequence` nem `pr_add_to_render_queue` acham preset sozinhos. Para 9:16 usar Match Source, que herda a resolução da sequência:
```
/Applications/Adobe Media Encoder 2026/Adobe Media Encoder 2026.app/Contents/MediaIO/systempresets/4E49434B_48323634/00 - Match Source - High bitrate.epr
```
Os demais presets são 16:9 e geram barras.

**Não existe tool para criar projeto.** Se houver outro projeto aberto, criar um **bin + sequência dedicados** e avisar o usuário para "Salvar como". **Nunca salvar por conta própria** num projeto que não é do job.

**Sobrescrever mídia no mesmo caminho pode ficar em cache.** Ao corrigir um asset já importado, salvar com **nome novo** e reimportar.

---

## Higgsfield

**`nano_banana_pro` roteia para `nano_banana_2`.** Normal. Se a fidelidade de rosto escapar, trocar para `soul_2`.

**Recomendação de preset intercepta a geração.** O servidor pode devolver `preset_recommendation` em vez de gerar (já sugeriu "IN THE DARK" para uma cozinha ensolarada). Recusar com `declined_preset_id` e regerar literal.

**`kling3_0_turbo` ignora "no scene change".** Ele às vezes corta sozinho para um macro no meio do clipe. Isso costuma ser **melhor** que o pedido — conferir antes de descartar.

**Saída não é exatamente 1080x1920.** Vem `1076x1924`. Normalizar com `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920`.

**B-roll não precisa de áudio nativo.** `generate_audio:false` (Veo/Seedance) ou `sound:'off'` (Kling) economiza crédito. O `kling3_0_turbo` nem tem o parâmetro.

---

---

## Higgsfield — geração em escala (formato VSL 3D)

**O conector MCP expira e não avisa.** `balance` e `show_generations` passam a devolver *session expired*. O caminho que funciona é o **CLI**: `npm i -g @higgsfield/cli` e `higgsfield auth login`. Reautorizar o conector exige remover e readicionar — o CLI é independente disso.

**Teto de 8 jobs Seedance simultâneos, compartilhado com a equipe.** Submeter 39 de uma vez faz 15 falharem com `rate_limit_reached` — e o erro só aparece se você imprimir o retorno do submit. Usar **fila com 4 workers** (submete, espera, pega a próxima) e backoff de 45 s. Deixa metade do teto livre para os outros.

**Duração do Seedance: mínimo 4 s, máximo 15 s.** Marcador de 2,9 s gera em 4 s e apara-se no corte — sobra handle, o que é bom.

**`fast` custa 3,5 créditos/s contra 4,5 do `std`**, em 720p, sem perda visível no QA frame a frame. `mode: fast` só aceita 480p e 720p.

**Corpo humano translúcido é barrado como `nsfw`** no modelo de vídeo — mesmo sendo ilustração médica, e mesmo depois de virar silhueta chapada cinza. O job termina com `status: nsfw` e não gasta. Resolver indo para o abstrato: rede de vasos em macro, sem corpo.

**O frame de estilo com rosto contamina cena sem personagem.** Usar um close do protagonista como referência de render faz ele aparecer como pessoa real em shots de produto e ilustração — aconteceu em 7 cenas de um mesmo AD. Para essas cenas, usar um frame de estilo **sem rosto** (um close de objeto ou de cintura serve) e negativo explícito de pessoas.

**O rótulo do produto some se não for exigido.** O frasco sai como vidro liso. Passar a foto do produto como **primeira** referência e escrever que o rótulo tem de estar de frente, nítido e legível, *"nunca um frasco liso sem rótulo"*. E conferir rótulo no QA — não só rosto.

**Com duas âncoras de personagem no prompt, o modelo pega a errada.** Numa cena de "mulher desconhecida chorando" com a protagonista também referenciada, saiu a protagonista chorando. Quando a cena é de um personagem só, passar **só a âncora dele**.

**Guarda-roupa vaza da âncora.** Se a âncora do "depois" usa o vestido da festa, ele aparece nas semanas anteriores e rouba o impacto da cena da festa. Gerar uma variante casual da mesma âncora.

---

## Conta compartilhada e processos paralelos

**Não medir custo por diferença de saldo.** Numa conta de equipe o delta inclui o gasto dos outros — deu 445 lidos contra 207,5 reais, mais que o dobro. Medir por `higgsfield account transactions`, casando modelo e horário. O extrato vem em UTC.

**Dois processos gravando o mesmo índice JSON se sobrescrevem.** Um script auxiliar leu o arquivo com 33 entradas e gravou de volta com 36, apagando 7 URLs que o lote tinha escrito no meio. Reler o arquivo imediatamente antes de gravar, dentro de um lock. As URLs perdidas dá para recuperar em `higgsfield generate list --json`, casando pelo texto do prompt.


## Se o usuário pedir transição e SFX

Assets do Premiere Composer ficam na biblioteca configurada em
`~/Library/Application Support/MisterHorse/PremiereComposer/preferences` → `BrowserApp.userFolders`.
No Mac o path tem Unicode decomposto (NFD) — buscar com `find -iname`, nunca com string literal.

- **Flash** é a única transição que não denuncia produção em UGC. Glitch / Burning Light / Film Strip Burns quebram a ilusão.
- Usar só a janela útil do clipe de flash (medir luminância frame a frame; costuma ser preto nas pontas).
- Alinhar o **pico** do flash e o **impacto** do whoosh no frame do corte, não o início do arquivo.
- Whoosh a `volume=0.60` dá ~+3,5 dB no corte — audível sem cobrir a voz. `0.30` é baixo demais.

## Geração de imagem — o que o modelo faz por conta própria (AD04 Crowned)

**Prompt de montagem vira colagem.** `"montage of"`, `"three short inserts"`, `"intercut framing"`,
`"then cut to"` produzem **painéis empilhados** dentro do quadro vertical — cada painel é uma tira
horizontal. Foi exatamente isso que o cliente leu como *"tem muito footage em 16x9"*, embora todos
os arquivos fossem 720×1280.
→ **Um prompt = um plano.** Beat que pede várias imagens vira **takes separados**.

**Composição girada 90°.** O modelo compõe em paisagem e encaixa no quadro vertical: a personagem
deitada de lado. É literalmente conteúdo 16:9 espremido no 9:16.
→ Trava explícita: *"the camera is in PORTRAIT orientation, subject UPRIGHT and VERTICAL, head
toward the top edge, do NOT rotate the composition."*

**O gerador embeleza o defeito que a copy narra.** Pedido "cabelo ralo, risca larga, couro à mostra"
devolveu um chanel cheio — num anúncio cujo nicho é queda de cabelo, a abertura não mostrava o
problema.
→ **Regra do ângulo:** o que precisa ser *provado* no corpo exige **ângulo alto sobre a região**.
Retrato frontal na altura dos olhos não carrega essa informação.
→ E **adjetivo agressivo não resolve**: `severe`, `unflattering`, `bare scalp` devolveram outra
pessoa, mais velha e com calvície de padrão masculino. Quebra a identidade.

**Nano Banana recusa desenhar falha/calvície**, inclusive em desenho infantil — devolvia todas as
figuras com cabelo, duas tentativas seguidas.
→ **`gpt_image_2`** obedece "deixe a cabeça em branco". **Desenho e gráfico vão nele.**

**Cor de cabelo escapa** no meio de uma sequência.
→ Travar na âncora com negativa: `ASH-WHITE SILVER-GREY hair (never brown, never auburn)`.

**Texto queimado.** Vieram legendas inventadas ("Are you sure, dear?") e tarjas com nome de
personagem, mesmo com `no text` no prompt. Confira — não confie na trava.

**Conferir imagem antes de animar.** Vídeo custa **11×** uma imagem (22,5 contra 2 créditos).
No AD04 o QC pegou 7 reprovados em 41 na primeira rodada e 8 em 151 na segunda.

## Seedance — entrada de imagem

**Job id de imagem não serve como entrada.** O erro fala de papéis de mídia e lista job types de
vídeo. `--image-references` também erra nesse caso.
→ **`--start-image` com caminho de arquivo local.** A CLI faz o upload.

Falha de validação **não cobra** — as 41 primeiras tentativas custaram 0.

## Premiere — as duas que mais custaram

**Timeout de 120s do Tools PRO NÃO é falha.** É o Premiere ainda executando. Retentativa empilha
trabalho: travou o app por ~25 min a 100% de CPU e **desfez a escala de 60 clipes** já ajustados.
→ **Espere. Leia o estado. Só repita o que a leitura provar que faltou.**

**`setScaleToFrameSize()` mente.** Retorna OK e **não altera clipe que já está na timeline** — só o
padrão de futuras inserções.
→ Aplique em `Movimento › Escala` (PT-BR) por clipe e **leia de volta**.
Vídeo 720×1280 em sequência 1080×1920 → `150`. Imagem 1536×2752 → `70.31`.

**Limite de 100 clipes** por `pr_timeline_colocar`. **Importar 151 arquivos de uma vez** trava o
Premiere ~15 min conformando — importe em lotes de 50.
