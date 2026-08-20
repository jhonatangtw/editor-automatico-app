---
name: editor-automatico-de-broll
description: >-
  Edita um criativo UGC 9:16 a partir do BRUTO de um avatar falante (VSL/UGC/depoimento) em plano
  fixo — gera B-ROLL da MESMA pessoa em roupas diferentes no Higgsfield, encaixa os inserts nos
  pontos exatos da fala, aplica punch-ins pra quebrar o plano parado, e entrega legenda sincronizada
  + MP4 final + timeline no Premiere. Use SEMPRE que o usuário mandar um vídeo de avatar/talking head
  pronto e pedir "edita esse criativo", "coloca b-roll", "deixa dinâmico", "monta o AD", "edita o
  body", "faz a edição do criativo", "insere os inserts", "pega os brutos e deixa pronto", ou apontar
  uma pasta de demanda com body + avatar + copy. Aciona também para regerar um B-roll específico,
  mudar ponto de insert, corrigir legenda contra a copy, ou refazer o corte com mais/menos inserts.
  NÃO é para conferir criativos prontos (use conferir-ads-por-frame), nem para cortar silêncio de
  aula (use cortar-aula), nem para gerar prompts sem editar (use skill-black-belt).
---

# Editor Automático de B-roll

Recebe o **bruto** de um criativo (body de avatar falante em plano único) e devolve o criativo **editado**: B-roll gerado, inserts encaixados na fala, punch-ins, legenda e MP4 final.

**Princípio que rege tudo:** a alavanca é o **B-ROLL**, não o efeito. Um body de avatar é um plano travado de 2 minutos — o que segura retenção é ver a pessoa em outro lugar, com outra roupa, fazendo o que ela está narrando. Transição e efeito são enfeite e costumam denunciar a produção. **Corte seco é o padrão.**


---

## Dois formatos, dois caminhos

| | O que é | Onde está |
|---|---|---|
| **1. UGC 9:16** | body de avatar em plano fixo + inserts de B-roll | este documento |
| **3. VSL 3D Pixar** | 8–12 min narrados, **tudo gerado**, 40–50 cenas | `references/historia-3d-pixar.md` |

Se o material for **locução longa sem avatar filmado**, ou uma timeline já parcialmente editada com vãos a preencher, é o formato 2 — **ler `historia-3d-pixar.md` antes de qualquer coisa.** O que muda não é o acabamento: é o risco central. No formato 1 o risco é o insert não casar com a fala; no formato 2 é **o personagem mudar de rosto entre as cenas**, e a resposta para isso é a imagem-âncora, não o texto do prompt.

---

## Entradas esperadas

| Item | Onde costuma estar | Obrigatório |
|---|---|---|
| Body (avatar falando) | `VIDEO DO BODY.mp4` na pasta da demanda | sim |
| Imagem do avatar | `ARQUIVOS BRUTO/*AVATAR*.jpeg` | sim (identidade do B-roll) |
| Vídeo de referência | `EXEMPLO*.mp4` | recomendado (define o estilo) |
| Copy | Google Docs / .docx | recomendado (corrige a legenda) |

Se faltar a referência, seguir o padrão UGC descrito em `references/estilo-ugc.md`.

---

## Fluxo

### 0. Abertura — o que descobrir e o que perguntar

Duas listas, e a ordem importa. **Descobrir primeiro, perguntar depois** — perguntar o que dá para ler no sistema atrasa o trabalho e faz o usuário repetir o que já está na tela.

#### 0a. Descobrir sozinho (uma rodada, tudo junto)

```
pr_midia_info          →  Tools PRO vivo? qual projeto e sequência ativa?
get_host_status        →  Higgsfield MCP vivo, com ppro: true?
higgsfield account status  →  o CLI está autenticado? qual saldo?
pr_sequencias_listar   →  quantas sequências? alguma duplicada?
pr_timeline_listar     →  já existe edição? onde estão os vãos?
pr_marcadores_info     →  já tem marcador? quantos?
```

E na pasta da demanda, olhar antes de perguntar:

```
folhas de personagem  →  IMAGENS/, PERSONAGENS/, *padrao*.png
b-roll já gerado      →  VIDEOS/, CENAS*/, *.mp4 soltos
```

Se existirem folhas de personagem, são as âncoras — usar, não criar do zero. Se existir B-roll pronto, conferir também se está **importado no projeto**: arquivo na pasta não é arquivo no bin, e foi por isso que 9 clipes prontos ficaram sem uso em três ADs.

Isso responde sozinho: se o Premiere está aberto, qual projeto, se já há edição, qual caminho de geração está disponível, e o que de material já existe.

**Dois sinais de alarme para ler com atenção:**

- **Sequência ativa aparecendo duplicada** em `pr_sequencias_listar` costuma ser mais de um projeto aberto. Ver `armadilhas.md`.
- **Nome de projeto que não bate com a demanda.** Aconteceu de `AD08.prproj` aberto ser outro job com o mesmo nome. Conferir o conteúdo da timeline, não só o nome.

#### 0b. Perguntar — só o que o sistema não conta

Fazer as perguntas **em bloco, de uma vez**, já com o que foi descoberto como contexto.

**1. Onde está o material?**
> Caminho da pasta da demanda. Costuma ser um Drive compartilhado — o caminho tem acento, espaço e colchete, então copiar inteiro.

**2. Tem a copy do criativo?** — *opcional, deixar em branco se não houver*
> Link do Google Docs ou caminho do arquivo. Costuma existir e vale muito:
>
> - **É a copy que corrige a transcrição.** O Whisper acerta o timing e erra nome próprio — saíram "Stalinger" por Stillingia, "Monjaro" por Mounjaro, "Brickly ash" por Prickly Ash. Regra: **timing do áudio, texto da copy.**
> - Traz o **brief de edição** ("a edição deve imitar este anúncio aqui"), os **hooks** H1/H2/H3 e o nome dos personagens.
> - Sem ela dá para trabalhar — a marcação sai da transcrição — mas a legenda não tem contra o que ser conferida, e o nome do produto pode ir errado para a tela.

**3. Qual formato?** — *resposta livre, não oferecer lista fechada*
> A operação trabalha com cinco formatos (Criativos, VSL, Microleads, Lead, Troca de potes), e dentro de cada um há variações. Perguntar aberto: **"que formato é esse job?"**
>
> Dois caminhos já documentados aqui:
> - **UGC 9:16** — body de avatar em plano fixo + inserts → este documento
> - **VSL 3D narrada** — 8–12 min, tudo gerado, 40–50 cenas → `historia-3d-pixar.md`
>
> **Se a resposta não for nenhum dos dois, não forçar no molde de UGC.** Pedir um job **já feito** desse formato — material de entrada, saída final e o `.prproj` se existir — e deduzir o processo olhando o resultado. Foi assim que o padrão de legenda, ritmo de insert e estilo de corte entraram nesta skill: olhando o `EXEMPLO DE AVATAR.mp4`, não pedindo explicação.
>
> Formato novo que se repetir vira **referência própria** em `references/`, como o `historia-3d-pixar.md` — não um `if` a mais no meio do fluxo de UGC.

**4. Até onde vai a entrega?**
> - só **marcações** na timeline
> - marcações **+ geração** de B-roll
> - até o **MP4 final** montado
>
> Muda o custo em ordem de grandeza. Marcar é local e de graça; gerar 45 cenas custa ~2.000 créditos.

**5. Gerar pelo MCP do Higgsfield ou pelo CLI?**
> - **CLI** (`higgsfield`) — independente do conector, não expira, aceita lote e `--json`. **Padrão recomendado.**
> - **MCP** — mais integrado, mas a sessão expira sem avisar e só volta removendo e readicionando o conector.
>
> Se `higgsfield account status` respondeu com saldo, o CLI está pronto — dizer isso na pergunta.


> **Gerar sem texto nenhum na tela.** A legenda é feita à mão pelo editor, então nada de letra, subtítulo ou UI legível nos prompts — entra como negativo explícito. Texto gerado por IA sai embolado de qualquer jeito; ver `armadilhas.md`.

> **Padrão de geração: Seedance `fast`, 720p, máximo 15 s por cena.** O `fast` custa 3,5 créditos/s contra 4,5 do `std`, sem perda no QA frame a frame. Mínimo do Seedance é 4 s — cena mais curta gera em 4 s e apara-se no corte.

> **Quem opera a timeline é o Tools PRO.** Não é pergunta, é o padrão: local, ~3 ms, sem login, marcador e clipe em lote. O Higgsfield é quem **gera** imagem e vídeo — as duas coisas somam, não competem. Só cair para as `pr_*` do Higgsfield se o Tools PRO não responder.

> **A conta do Higgsfield é da equipe.** Não é pergunta, é o estado: o teto de **8 jobs Seedance simultâneos** é dividido com os outros — usar fila de 4 e deixar folga. E **nunca medir custo por diferença de saldo**, porque o delta inclui o gasto de quem mais estiver gerando; medir por `higgsfield account transactions`. Detalhe em `armadilhas.md`.

Se nenhum dos dois MCP responder, **avisar e parar.** Nunca editar o `.prproj` direto — ver `armadilhas.md`.

Detalhes, ferramentas e travas em `references/mcp-premiere.md`. **Ler antes de escrever no Premiere.**

### 1. Ler o material antes de decidir qualquer coisa
```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate \
  -show_entries format=duration -of default=noprint_wrappers=1 "<arquivo>"
# mosaico de frames do vídeo de REFERÊNCIA — é dele que sai a receita de estilo
ffmpeg -v error -i "<ref>.mp4" -vf "fps=1/5,scale=270:-1,tile=6x6" -frames:v 1 mosaico.jpg
```
Olhar o mosaico **de verdade**. Extrair: quanto tempo fica no talking head, quantos inserts, estilo/posição da legenda, se usa split screen, o que acontece no CTA.

Olhar também a imagem do avatar — ela define cenário, guarda-roupa e props que o B-roll precisa repetir.

### 2. Transcrever — **sem forçar idioma**
```bash
ffmpeg -v error -i body.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le body.wav
whisper body.wav --model large-v3 --word_timestamps True --output_format json --output_dir ./
```
O body pode estar **em inglês mesmo com copy PT-BR no doc**. Forçar `--language pt` num áudio inglês produz lixo. A legenda segue o **ÁUDIO**, nunca a coluna do documento.

### 3. Mapear os inserts pela fala
Ler a transcrição e escolher **poucos** pontos (4–5 em ~2min). Critério único que importa: **casamento verbal-visual** — o insert entra no segundo em que a fala o descreve.

> "tive que trocar o guarda-roupa" → ela aparece **de outra roupa**
> "três colheres misturadas com..." → a receita sendo feita

Body de TTS não tem silêncio pra cortar (gaps de ~0,3s). **Não existe corte de tempo morto aqui** — não perder tempo procurando.

O mapeamento vira um **`plano.json`** — beats com a fala que justifica cada insert, a intenção do plano e o estilo escolhido. Formato em `references/plano-e-estilo.md`.

```bash
python3 scripts/revisar.py --plano plano.json
```

**Este é o portão.** Mostra a régua da timeline, a cobertura medida contra o alvo do estilo, o maior vão sem troca de imagem, e sai com código 1 se faltar mídia. Passar por aqui **antes de gerar b-roll** — errar o ponto de insert depois de gastar crédito é o retrabalho mais caro da skill.

### 4. Gerar o B-roll (Higgsfield)
Detalhes e templates de prompt em `references/prompts-broll.md`.

```
media_upload → media_confirm  (imagem do avatar)
generate_image  model=nano_banana_pro, medias=[{role:image, value:<media_id>}], aspect_ratio=9:16
generate_video  model=kling3_0_turbo, medias=[{role:start_image, value:<job_id>}], 1080p
```
Custo: ~2 créditos/imagem, ~10/clipe de 5s. Preflight com `get_cost:true`.

**Roupas diferentes em cada B-roll** — lê como dias diferentes, que é o cheiro de UGC real. Manter cenário/props da imagem original em pelo menos um insert, pra ancorar a continuidade.

**Baixar e conferir frame a frame antes de montar.** Clipe de IA quebra no meio:
```bash
ffmpeg -v error -i clip.mp4 -vf "fps=1,scale=200:-1,tile=8x1" -frames:v 1 qa.jpg
```

### 5. Legenda
```bash
python3 scripts/legendas.py --json body.json --out AD01_legendas.srt \
        --overlay AD01_LEGENDAS.mov --dur <duracao>
```
Gera SRT em frases de 3–4 palavras + overlay ProRes 4444 com alpha (pílula branca, texto preto).

**Obrigatório antes de renderizar:** diffar o texto contra a copy do doc e corrigir nome de marca/produto. O Whisper acerta timing e erra nome próprio.
```bash
python3 scripts/conferir_legenda.py --srt AD01_legendas.srt --copy copy.txt
```

### 5b. Lettering animado (só quando pedido)
```bash
python3 scripts/lettering.py --config lettering.json --out LETTERING.mov --dur <duracao>
```
Tipografia grande com glow, pop-in com overshoot, em 2–3 falas de maior peso. Posição padrão `y=0.55` — acima da legenda (0.73) e abaixo do rosto, que num selfie 9:16 ocupa o terço superior.

**Regra que não pode ser esquecida:** suprimir a legenda nas janelas de lettering, senão o **mesmo texto aparece duas vezes na tela** (o lettering em cima e a legenda logo abaixo). Naquele beat o lettering *é* a legenda.
```bash
python3 scripts/legendas.py --srt legendas.srt --overlay LEGENDAS.mov --dur <dur> \
        --mute "5.90-8.10" --mute "70.30-72.30"
```

### 6. Montar e exportar
```bash
python3 scripts/compilar.py --plano plano.json --out .
python3 scripts/montar.py  --config edicao.json > build.sh && bash build.sh
```
O `compilar.py` deriva do plano + estilo os dois artefatos de execução: `edicao.json` (com o punch já calculado e contíguo) e `marcadores.json` (já com cor e cobertura). O `montar.py` gera o ffmpeg com punch-ins, inserts e legenda. Formatos em `references/plano-e-estilo.md` e `references/config.md`.

Trocar o ritmo do criativo é trocar um argumento — `--estilo talking-head-puro` — não reescrever o `edicao.json`.

Punch-ins com escalas **variadas** (110/112/114/116%) — escala igual em todas vira tique visível.

### 7. Conferir o resultado — sempre
```bash
for t in 3 11 26 47 68 84 120 130; do
  ffmpeg -v error -ss $t -i final.mp4 -frames:v 1 -vf scale=230:-1 f_$t.png -y; done
ffmpeg -v error -i f_3.png -i f_11.png ... -filter_complex hstack=8 -frames:v 1 qa.jpg
```
**Olhar a imagem.** Não reportar como pronto sem ter visto. Nesta skill já apareceram: vídeo inteiro magenta, efeito vazando pra todos os frames, legenda duplicada — todos invisíveis nos retornos de sucesso das ferramentas.

### 8. Montar no Premiere

Com o Tools PRO ligado, isto deixou de ser opcional: dá para entregar o projeto **editável**, que é melhor que um MP4 fechado — o editor troca um insert, testa outro hook.

**Sempre ler o estado imediatamente antes de escrever.** A sequência ativa muda quando o usuário clica noutra aba, e o estado de minutos atrás não vale.

```
pr_midia_info        →  confere projeto e sequência ativa
pr_midia_importar    →  {"arquivos":[...], "bin":"BROLL"}
pr_midia_listar      →  pega o nome EXATO de cada item
pr_timeline_colocar  →  {"sequencia":"<nome>", "clipes":[...]}   ← em lote
```

`pr_timeline_colocar` resolve **todos** os clipes antes de colocar qualquer um: se um nome estiver errado, nada entra. Timeline pela metade é pior que nada feito.

**Marcações** — `pr_marcadores_criar` aceita a lista inteira numa chamada. Vermelho = B-roll, azul = lettering, roxo = decisão humana. Marcador de **trecho** (com `duracao`), cobrindo a janela da fala.

**Punch-in** — `pr_zoom_aplicar` age sobre a **seleção**, então peça ao usuário para selecionar os clipes. Escalas variadas (110–116%).

**Tire o áudio do B-roll.** `pr_timeline_colocar` traz o áudio nativo junto, e ele briga com a voz do avatar:
```
pr_timeline_remover  →  {"sequencia":"<nome>", "tipo":"audio", "trilha":<n>}
```

**Confira lendo de volta — sempre.** `pr_timeline_listar` mostra o que existe em cada trilha. Não reportar como pronto sem ter lido: retorno de sucesso diz que a chamada não deu erro, não que o resultado está certo. Foi exatamente assim que o áudio de b-roll passou despercebido.

**Antes de qualquer coisa destrutiva**, rode com `simular: true` e mostre o número ao usuário. Não há desfazer pelo MCP.

> **Não rode `pr_autoclip` numa sequência anotada** — ele corta em todos os marcadores, inclusive nos de sugestão. Use `ignorarCores: [1,2,6]`.

---

## Decisões que já estão tomadas (não perguntar de novo)

- **Corte seco por padrão.** Não propor transição/flash/glitch. Se o usuário pedir, ver `references/armadilhas.md`.
- **Poucos inserts**, em ponto estratégico, não espalhados.
- Punch-in é de graça e resolve plano parado — usar em vez de gerar mais B-roll.
- O usuário finaliza transição e música de fundo no Premiere. Não fazer isso por ele.

---

## Se o bruto ainda não existe

A skill começa no body pronto. Para gerar o bruto a partir da copy (copy → áudio → lipsync), ver `references/heygen-lipsync.md`: HeyGen v3 com Avatar V, clone de voz no ElevenLabs, e o caminho alternativo pelo Higgsfield quando o HeyGen recusa a persona.

## Referências
- `references/como-pedir-marcacoes.md` — **para o usuário**: o prompt, o que muda o resultado e o que precisa estar instalado
- `references/mcp-premiere.md` — conectar e operar Premiere/AE, as travas e a convenção de cor. **Ler antes de escrever no Premiere.**
- `references/historia-3d-pixar.md` — **formato 2**: VSL narrada em 3D, âncora de personagem, marcação sobre timeline já editada
- `references/armadilhas.md` — falhas silenciosas do Premiere/ffmpeg/Whisper. **Ler antes de montar.**
- `references/heygen-lipsync.md` — gerar o bruto: TTS, clone de voz, lipsync e motores
- `references/prompts-broll.md` — templates de prompt de B-roll e modelos do Higgsfield
- `references/estilo-ugc.md` — o padrão visual UGC extraído da referência aprovada
- `references/config.md` — formato do `edicao.json`

- `references/marcacao.md` — formato dos marcadores de trecho, cores e a regra de cobertura
- `scripts/qc_colagem.py` — detector de colagem, letterbox e rotação nas imagens geradas
- `scripts/cep.py` — ExtendScript no Premiere pela porta de debug CEP (o que o Tools PRO não faz)
