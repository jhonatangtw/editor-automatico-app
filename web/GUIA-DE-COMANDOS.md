# Guia de comandos — Editor Automático

Receitas tiradas de edições reais feitas com o app — webinário, upsell, VSL, criativos, aulas e Reels. Cada comando já traz a ordem que funcionou, as regras que foram aprovadas e as armadilhas que custaram tempo. Copie, troque o que está entre colchetes e cole na Conversa (ou no Claude Code). A IA mostra o plano antes de mexer no projeto, e o que gasta crédito pede sua aprovação.

**Quem roda:** **Claude** — Usa as ferramentas do plugin Tools PRO dentro do Premiere/After — precisa do Claude conectado. · **Claude e ChatGPT** — Roda no seu computador (FFmpeg, Whisper, scripts) ou só escreve prompts — funciona com as duas IAs do app.

**Nível:** **rápido** — Uma tarefa só, poucos minutos. · **completo** — O job inteiro, etapa por etapa, com aprovações no meio.


## Organização de job

Antes e depois de editar: a pasta certa, o projeto certo e o entregável com o nome certo.

### Conferir que estou no projeto certo

*Nível: rápido*

```text
Antes de mexer em qualquer coisa, me diga o nome e o caminho do projeto aberto no Premiere, a sequência ativa e o tamanho dela (largura × altura e fps).
Compare com a pasta do job: [PASTA DO JOB].
Se o projeto aberto NÃO for deste job, pare e me avise — não salve nada.
Atenção: com dois projetos abertos o Premiere pode escrever no errado. O tamanho da sequência não é o tamanho do bruto — leia da sequência.
```

- **O que faz:** Prova qual projeto e qual sequência estão ativos antes de qualquer escrita.
- **Quando usar:** No começo de todo job, sempre.
- **Precisa:** Premiere aberto com o projeto do job; Painel Tools PRO aberto (Janela › Extensões)
- **Funciona com:** Claude
- **Por baixo:** `pr_organizar_info`, `pr_sequencias_listar`, `pr_midia_info`

### Montar a estrutura de pastas do job

*Nível: rápido*

```text
Crie a estrutura de pastas do job dentro de [PASTA DO JOB], sem apagar nada que já exista:
EXPORT/, FOOTAGE/, PROJECT/ e MEDIA/ com AUDIO, IMG, SRT, LEGENDA, AEF, BANCO e IA LIPSYNC.
Se o job tiver vários ADs, crie FOOTAGE/AD01… e EXPORT/AD01… para [QUANTOS ADs].
Depois me diga onde copiar o projeto-modelo do Premiere (eu abro o projeto; você executa dentro dele).
Atenção: tudo o que for gerado para o job (imagens, vídeos, áudios de voz) é salvo dentro desta pasta ANTES de importar. Mídia importada de pasta temporária fica offline amanhã.
```

- **O que faz:** Cria as pastas padrão da demanda para que mídia, projeto e entrega fiquem no mesmo lugar.
- **Quando usar:** Job novo, antes de gerar ou importar qualquer coisa.
- **Precisa:** A pasta do job (local ou no Drive)
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `pastas do computador`

### Organizar bins e salvar

*Nível: rápido*

```text
Organize o projeto do Premiere em bins: 01 Sequências, 02 Brutos, 03 Mídias (áudio, imagem, legenda) e 04 IA.
Primeiro me mostre o plano (qual item vai para qual bin). Só aplique depois do meu ok, e guarde o "antes" para eu poder desfazer.
No fim, salve o projeto e me mostre quantos itens foram movidos e se ficou alguma mídia offline.
Atenção: nada no disco é movido — só os bins dentro do projeto. Se o projeto nunca foi salvo, salve você uma vez antes (o salvar por script recusa projeto sem nome).
```

- **O que faz:** Arruma os bins pelo plano aprovado, salva e avisa mídia offline.
- **Quando usar:** Projeto bagunçado ou antes de passar para outro editor.
- **Precisa:** Premiere aberto com o projeto do job
- **Funciona com:** Claude
- **Por baixo:** `pr_organizar_analisar`, `pr_organizar_aplicar`, `pr_organizar_desfazer`, `pr_projeto_salvar`

### Montar e nomear os entregáveis (hook + body)

*Nível: completo*

```text
Monte os entregáveis finais deste job. Cada arquivo é UM hook + o body já emendados — não as peças soltas.
Pasta das peças: [PASTA DAS PEÇAS]. Saída: [PASTA DO JOB]/EXPORT/ADxx/.
Nome de cada arquivo: [DDMMAA][OT] [NN]_[SIGLA] ADxx HKn [PRODUTO] [SQUAD].mp4 (os campos vêm do nome da pasta do job).
Faça nesta ordem:
1. Confira com o ffprobe que todas as peças têm o mesmo codec, tamanho, fps e áudio. Se baterem, emende sem reencodar (concat com cópia); se não, reencode só o que diverge.
2. Gere um arquivo por AD × hook.
3. No fim, me mostre a lista com nome, duração e se cada um abre do começo ao fim (decodifique o último segundo de cada).
Atenção: hook e body com loudness diferente denunciam a emenda — iguale o hook ao body (loudnorm em duas passadas) antes de emendar.
```

- **O que faz:** Emenda hook + body, aplica o padrão de nome e confere cada arquivo até o fim.
- **Quando usar:** Fechamento de pacote de ADs com várias variações de hook.
- **Precisa:** FFmpeg instalado; As peças (hooks e bodies) numa pasta
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `FFmpeg`

### Renderizar pelo Media Encoder

*Nível: rápido*

```text
Envie para o Media Encoder as sequências cujo nome começa com [PREFIXO], uma por arquivo, com o preset H.264 "Match Source - High bitrate".
Renderize numa pasta LOCAL com nome sem acento (ex.: ~/Movies/[JOB]_EXPORT/) e só depois copie para [PASTA DO JOB]/EXPORT/.
No fim confira: quantos arquivos saíram, se cada um tem a duração da sequência e se não sobrou arquivo duplicado com "_1" no nome.
Atenção: render direto numa pasta do Drive com acento ou "&" no caminho falha com "destino não encontrado".
```

- **O que faz:** Fila as sequências no Media Encoder por script e confere a saída.
- **Quando usar:** Muitas sequências para exportar de uma vez.
- **Precisa:** Modo avançado ligado no painel Tools PRO (rodapé › Conectar IA); Adobe Media Encoder instalado
- **Funciona com:** Claude
- **Por baixo:** `pr_sequencias_listar`, `pr_extendscript`

### Conferir o job contra as boas práticas

*Nível: rápido*

```text
Use a skill boas-praticas-black-belt no modo auditoria: confira meu job em [PASTA DO JOB] (copy em [ARQUIVO DA COPY], se houver).
Só leia e meça — não conserte, não regere e não reexporte nada.
Confira em cada entregável: resolução, proporção e fps (25 × 23,976 misturados?), cor (HDR que devia ser SDR?), duração do vídeo igual à do áudio, quadro preto ou congelado, texto queimado de IA, rosto ou rótulo do produto mudando, legenda contra a copy palavra por palavra, lip sync pelo quadro do silêncio × pico, e −14 LUFS.
Veja também se tem mídia em pasta temporária ou na nuvem sem baixar.
Me devolva ✓ o que passou e ✗ o que está fora, com o arquivo, o tempo e o conserto sugerido.
```

- **O que faz:** Uma auditoria do job contra as armadilhas que já custaram retrabalho em jobs reais.
- **Quando usar:** Antes de entregar ou de avisar que o job acabou.
- **Precisa:** A pasta do job com os entregáveis
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `boas-praticas-black-belt`, `FFmpeg`, `Whisper`


## Webinário

Slides que acompanham a fala de um apresentador — centenas de slides, no segundo certo.

### Slides de webinário pela fala

*Nível: completo*

```text
Crie os slides do webinário que acompanham a fala do apresentador.
Vou te passar: o áudio da apresentação [ARQUIVO DE ÁUDIO], o roteiro [ROTEIRO] e uma referência visual [IMAGENS DE REFERÊNCIA].
Faça nesta ordem:
1. Transcreva com tempo de cada palavra (fatiando em pedaços de 5 minutos — veja a armadilha abaixo).
2. Divida em slides pela fala: um slide a cada ideia nova, não a cada X segundos.
3. Me mostre 10 slides de teste antes de gerar o resto.
4. Depois do meu ok, gere em lote e salve DIRETO em [PASTA DO JOB]/Slides Webinar/.
Regras aprovadas:
- Na tela, só a palavra-chave: 1 a 4 palavras por slide (pergunta pode chegar a ~8). A fala carrega a frase.
- Formatos fixos: revelação = fundo chapado + UMA palavra gigante ("FALSE."); pergunta = fundo claro com a palavra-chave colorida; foto = foto dominante + rótulo curto em caixa alta; dado de mídia = papel rasgado sobre foto; número = número sozinho gigante.
- Tipografia pesada e condensada; deixe livre a área do apresentador ([CANTO E TAMANHO]) e confira que o texto não invade.
Atenção:
- Um único processo escreve o arquivo de controle dos jobs. Dois processos gravando o mesmo arquivo já apagaram centenas de jobs pagos.
- Whisper em passada longa (40 min) entra em laço e repete palavras; fatie em 5 min sem condicionar no texto anterior.
- Leitura automática do texto (OCR) erra cor sobre cor; use só como alerta, a conferência final é visual.
No fim confira: quantos slides, se a grafia de cada um está certa e se nenhum cobre o apresentador.
```

- **O que faz:** Transcreve, quebra a fala em slides, gera em lote com as regras da referência e salva na pasta do job.
- **Quando usar:** Webinário longo com apresentador (real ou IA) e muitos slides.
- **Precisa:** Whisper instalado; Higgsfield conectado (créditos); Áudio e roteiro do webinário
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `Whisper`, `Higgsfield`, `skill-black-belt`

### Colocar centenas de slides na timeline

*Nível: rápido* · *Tempo: menos de 1 minuto para ~800 slides*

```text
Coloque os slides de [PASTA DOS SLIDES] na V[NÚMERO] da sequência [NOME], cada um no tempo indicado em [ARQUIVO DE TEMPOS], sem buraco entre eles.
Faça em lotes de 50 com pausa de 3 segundos entre lotes, montando o mapa nome → item do projeto UMA vez só.
Feche lacunas menores que 0,2 s esticando o slide anterior até o próximo.
No fim, leia a timeline de volta em páginas de 200 e me diga: quantos slides entraram, se há sobreposição, se há lacuna e o maior desvio de tempo.
Atenção: com projeto grande (centenas de itens), a ferramenta de colocar clipe um a um pendura o Premiere. Salve (Cmd+S) antes de começar.
```

- **O que faz:** Coloca centenas de stills em lote por script e confere contagem, lacunas e desvio.
- **Quando usar:** Mais de ~100 slides ou imagens para posicionar.
- **Precisa:** Modo avançado ligado no painel Tools PRO (rodapé › Conectar IA); Slides já importados no projeto
- **Funciona com:** Claude
- **Por baixo:** `pr_extendscript`, `pr_timeline_listar`

### Religar slides que estão fora da pasta do job

*Nível: rápido*

```text
Alguns slides/imagens deste projeto foram importados de uma pasta fora do job. Copie todos para [PASTA DO JOB]/Slides Webinar/ e religue cada item ao arquivo novo.
No fim, me diga quantos foram religados e confirme que ficou 0 mídia offline.
Atenção: o projeto é aberto por outros editores — mídia fora da pasta do job some para eles.
```

- **O que faz:** Copia a mídia para a pasta do job e troca o caminho dentro do projeto.
- **Quando usar:** Antes de entregar ou compartilhar o projeto.
- **Precisa:** Modo avançado ligado no painel Tools PRO (rodapé › Conectar IA)
- **Funciona com:** Claude
- **Por baixo:** `pr_midia_listar`, `pr_extendscript`

### Transcrever um webinário longo sem inventar fala

*Nível: rápido*

```text
Transcreva [ARQUIVO] com tempo de cada palavra, em pedaços de 5 minutos, e junte tudo num .srt e num .json.
Depois procure palavras com duração absurda (mais de 1,5 s no meio da fala) e repetições em laço, e repasse só essas janelas com o modelo maior.
Atenção: em passada longa o Whisper inventa palavras dentro do silêncio e às vezes engole uma frase inteira numa palavra só. Não afirme que um trecho da copy não foi gravado sem repassar a janela.
```

- **O que faz:** Transcrição em pedaços, com a conferência dos pontos onde o Whisper costuma errar.
- **Quando usar:** Base de tempo para slides, legenda ou corte.
- **Precisa:** Whisper instalado
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `Whisper`


## Upsell e VSL

Trocar oferta, encurtar, versionar e colocar motion numa VSL já gravada.

### Trocar o preço numa VSL de upsell

*Nível: completo*

```text
Troque a oferta desta VSL de upsell: [PREÇO ANTIGO] passa a ser [PREÇO NOVO] (e [OUTROS VALORES QUE MUDAM]).
Vou te passar: o render de referência [ARQUIVO], o projeto aberto e a voz do apresentador ([VOZ NA ELEVENLABS]).
Faça nesta ordem:
1. Marque os timecodes de cada fala de preço em cima do MESMO arquivo que bate com a comp/sequência (confira a duração antes — versões cortadas depois do render erram segundos).
2. Me mostre a tabela "onde / era / vira" antes de gerar qualquer áudio.
3. Gere a locução nova (inglês americano se o produto for para os EUA; números por extenso no texto) e encaixe nas janelas de silêncio.
4. Corrija também o texto do card de preço na tela: ele costuma ficar visível vários segundos DEPOIS da fala.
Regras: a emenda de áudio é feita por amostra, e a duração total tem que ficar IDÊNTICA à original.
Atenção:
- Emendar pedaços de áudio por concatenação simples acumula deriva (quase meio segundo) e dessincroniza o resto.
- O card de preço pode morar em camadas soltas da comp principal, presas a um nulo — não numa comp de apoio. Edite onde o render lê.
No fim confira: transcreva o trecho novo, compare com o texto aprovado e exporte um quadro do card com o preço novo.
```

- **O que faz:** Mapeia as falas de preço, gera a locução nova, emenda sem deriva e corrige o card na tela.
- **Quando usar:** Mudança de ticket ou de oferta numa VSL que já existe.
- **Precisa:** ElevenLabs conectado (voz do apresentador); Projeto aberto (Premiere ou After); FFmpeg e Whisper instalados; Modo avançado ligado no painel Tools PRO (rodapé › Conectar IA)
- **Funciona com:** Claude
- **Por baixo:** `ElevenLabs`, `Whisper`, `FFmpeg`, `pr_marcadores_criar`, `ae_extendscript`

### Encurtar uma VSL sem quebrar a oferta

*Nível: completo*

```text
Preciso encurtar esta VSL em cerca de [MINUTOS]. Vou te passar a lista de cortes sugerida: [LISTA DE CORTES].
Faça nesta ordem:
1. Transcreva a VSL inteira com tempo de cada palavra.
2. Confira cada borda da lista: ela cai dentro de uma palavra? Quebra uma frase? Deixa uma resposta sem a pergunta?
3. Verifique se algum corte apaga um ELO da oferta: âncora de preço, promessa de bônus e a volta dela, lógica de "por que levar mais unidades", garantia.
4. Marque na sequência ORIGINAL marcadores de TRECHO em vermelho "NN - CORTE - motivo" e, onde a sua proposta for melhor, em roxo "PNN - CORTAR - motivo" com a emenda sugerida no comentário.
5. Só depois do meu ok monte a sequência cortada, com marcador nas emendas.
Atenção:
- Cortar silêncio quase não encurta VSL (dezenas de segundos em mais de uma hora); encurtar sai de tirar bloco de conteúdo.
- Trecho que foi REGRAVADO (preço novo, palavra trocada) não sai cortando o original — exige locução nova. Marque à parte.
No fim confira: duração final, nenhuma emenda no meio de palavra e a oferta completa ouvida do começo ao fim.
```

- **O que faz:** Transforma a lista de cortes em mapa de edição, protege a oferta e monta a versão curta.
- **Quando usar:** Versão curta de VSL para afiliado ou teste.
- **Precisa:** Whisper instalado; Premiere aberto com a VSL
- **Funciona com:** Claude
- **Por baixo:** `Whisper`, `pr_marcadores_criar`, `pr_marcadores_listar`, `pr_timeline_listar`

### Achar o deslocamento entre duas versões da VSL

*Nível: rápido*

```text
Estas duas sequências são a mesma VSL com aberturas diferentes: [SEQUÊNCIA A] e [SEQUÊNCIA B].
Descubra a partir de onde elas são iguais e qual é o deslocamento fixo de tempo entre elas.
Meça por correlação do envelope de áudio (wav 16 kHz mono, envelope a 100 Hz) em pelo menos 5 pontos e confirme com a transcrição em 4 frases.
Depois copie os marcadores de [SEQUÊNCIA A] para [SEQUÊNCIA B] aplicando o deslocamento.
Atenção: nunca copie timecode de uma versão para a outra sem o deslocamento. Se a correlação cair em algum ponto, as versões divergem dali em diante — reencontre por conteúdo.
```

- **O que faz:** Mede o offset entre duas versões e replica os marcadores com o tempo certo.
- **Quando usar:** Lead 1 × Lead 2, versão DTC × versão afiliado, ou qualquer par de versões do mesmo corpo.
- **Precisa:** FFmpeg instalado; As duas sequências no projeto
- **Funciona com:** Claude
- **Por baixo:** `FFmpeg`, `Whisper`, `pr_marcadores_listar`, `pr_marcadores_criar`

### Motions de oferta nos marcadores da VSL

*Nível: completo*

```text
Gere os motions de overlay desta VSL nos marcadores de [COR DO MARCADOR DE MOTION] (só neles; os outros marcadores são de outra etapa).
Sistema visual: [ESCURO ou CLARO] — um só no criativo inteiro.
Faça nesta ordem:
1. Leia o tamanho e o fps da SEQUÊNCIA antes de gerar (não do bruto).
2. Me mostre a lista de motions com o texto exato de cada um.
3. Gere em lote; formato fora de 16:9/9:16 → gere em 9:16 e recorte.
4. Coloque na trilha acima do body, cada um no seu marcador, e confira a grafia quadro a quadro.
Regras: sem o apresentador dentro dos motions (o único humano é o body); número por extenso no prompt; contagem de unidades travada ("exactly three bottles").
Atenção: gerar no formato errado já custou centenas de créditos — confira o tamanho da sequência primeiro.
No fim confira: cada motion no marcador certo, grafia certa, e fora dos marcadores a imagem idêntica ao original.
```

- **O que faz:** Produz o lote de overlays no mesmo sistema visual, aplica nos marcadores e confere o texto.
- **Quando usar:** VSL ou criativo de resposta direta com a timeline já marcada.
- **Precisa:** Higgsfield conectado (créditos); Premiere aberto com a timeline marcada
- **Funciona com:** Claude
- **Por baixo:** `motion-omni-vsl`, `pr_midia_importar`, `pr_timeline_colocar`

### VSL narrada inteira em 3D (estilo Pixar)

*Nível: completo*

```text
Monte uma VSL narrada em 3D estilo Pixar a partir da locução [ARQUIVOS DE LOCUÇÃO] e de uma referência aprovada [VÍDEO DE REFERÊNCIA].
Faça nesta ordem:
1. Transcreva e marque as cenas na sequência: marcador de TRECHO "NN - TIPO - descrição" (cena, mecanismo, produto, CTA, hook), nenhuma cena acima de 15 s.
2. Folha de personagens: uma imagem-âncora por personagem (frente + expressões).
3. Storyboard: um prompt de imagem por cena.
4. Imagens → vídeos (Seedance 720p, mínimo 4 s por clipe), sempre com a âncora do personagem como referência.
5. Coloque cada clipe NO marcador da cena dele.
Regras: a âncora de imagem é o que trava o rosto, não o texto. Para o estilo, use um quadro da própria referência (sem rosto quando a cena não tiver personagem). Frasco com rótulo de frente e legível em toda cena de produto.
Atenção:
- Hooks podem vir embutidos no começo do áudio do body — confira antes de procurar arquivo separado.
- Locução que já vem com música: pausa não é silêncio, não corte por volume.
- Corpo humano translúcido é barrado pela moderação; vá para o abstrato.
- Encaixar clipes em cascata quebra a sincronia; buraco se fecha esticando o clipe que sai.
No fim confira: rosto igual entre cenas, rótulo legível, e cada cena casando com a fala.
```

- **O que faz:** Da locução à VSL animada: cenas marcadas, personagens, storyboard, geração e montagem no marcador.
- **Quando usar:** VSL ou AD longo sem avatar filmado, todo em personagem 3D.
- **Precisa:** Higgsfield conectado (créditos); Whisper instalado; Premiere aberto
- **Funciona com:** Claude
- **Por baixo:** `storyboard-viral-3d`, `pixar3d`, `Higgsfield`, `pr_marcadores_criar`, `pr_timeline_colocar`


## Criativos e ADs

UGC 9:16, hooks no formato Meat Hook e troca de produto em criativos que já performam.

### Criativo UGC 9:16 completo (b-roll + punch-in + legenda)

*Nível: completo*

```text
Edite este criativo UGC 9:16 a partir do bruto do avatar: [PASTA COM BODY, COPY E FOTO DO AVATAR].
Faça nesta ordem, me pedindo aprovação antes de cada etapa que gasta crédito:
1. Confira a fala contra a copy (palavra por palavra).
2. Marque os pontos de b-roll ancorados na fala: vermelho = b-roll, azul = lettering, roxo = decisão minha.
3. Gere o b-roll da MESMA pessoa em roupas e cenários diferentes, casando com o que ela diz (ex.: aparece de roupa nova no segundo em que diz "troquei o guarda-roupa").
4. Anime os b-rolls no Kling 3.0 Turbo, 9:16.
5. Punch-in variando entre 110% e 116% de clipe para clipe, foco no rosto.
6. Legenda sincronizada e revisada contra a copy, entrando no Premiere como faixa de legenda criada direto do .srt (nada de arrastar à mão).
7. Monte no Premiere e salve.
Regras aprovadas: corte seco, sem transição nem efeito (em UGC transição denuncia produção). A alavanca é o b-roll, não o corte. Eu coloco música e transição depois, se quiser.
No fim confira: legenda contra a copy palavra a palavra, nenhum b-roll repetido e áudio só do body.
```

- **O que faz:** As 12 etapas do app num pedido só, com as regras validadas em criativo que foi ao ar.
- **Quando usar:** Body de avatar falante em plano fixo, 9:16.
- **Precisa:** Higgsfield conectado (créditos); ElevenLabs para voz; Premiere aberto com o projeto do job
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `editor-automatico-de-broll`, `etapas do app`

### Animar os b-rolls no Kling

*Nível: rápido*

```text
Anime as imagens de b-roll de [PASTA DAS IMAGENS] no Kling 3.0 Turbo: 9:16, 720p, 5 segundos cada, usando cada imagem como quadro inicial.
Salve os vídeos em [PASTA DO JOB]/MEDIA/ com o mesmo nome da imagem.
No fim, monte uma folha de contato com 3 quadros de cada vídeo e me mostre os que mudaram de rosto ou de roupa no meio.
Atenção: formato 4:5 não existe no Kling — gere em 9:16 e recorte o centro.
```

- **O que faz:** Anima o lote de stills no Kling e aponta os clipes com deriva.
- **Quando usar:** Depois que as imagens de b-roll foram aprovadas.
- **Precisa:** Higgsfield conectado (créditos)
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `Higgsfield`, `editor-automatico-de-broll`

### Hooks novos no formato Meat Hook

*Nível: completo*

```text
Gere hooks novos no formato Meat Hook para os ADs validados [ADs], a partir da copy de hooks [DOC DA COPY] (com os comentários do copywriter).
Faça nesta ordem, com aprovação minha entre as etapas:
1. Tabela de hooks: fala em inglês, estrutura, avatar/cenário, objeto de demonstração e planos. Mapeie cada comentário ao hook pelo TEXTO ancorado, não pela ordem.
2. Start frames (vertical de celular, terço de baixo livre para legenda). Demonstração = 3 quadros: A objeto com o problema · B o ritual acontecendo · C o resultado.
3. Coloque os frames numa sequência de aprovação no Premiere (3 s por frame, 1 s entre hooks, marcador por frame).
4. Anime (A→B e B→C), com a fala começando em ~1 s e a ação correndo junto.
5. Unifique a voz de cada personagem (mesma voz em todos os clipes dele).
6. Decupe o silêncio, iguale o volume ao body e monte hook + body.
Atenção:
- Peça print da imagem de referência de cada hook: ela define o avatar.
- Para objeto anatômico e números exatos na tela, Nano Banana Pro acerta melhor; quem copia a referência é o GPT Image.
- Cada geração inventa uma voz nova — sempre unifique a voz quando um hook tiver 2+ clipes.
No fim confira: transcreva cada hook decupado contra a copy e exporte o quadro da emenda hook→body.
```

- **O que faz:** Pipeline inteiro de hooks: tabela, frames de demonstração, aprovação, animação, voz única e montagem.
- **Quando usar:** Trocar ou empilhar hooks em ADs que já performam.
- **Precisa:** Higgsfield conectado (créditos); ElevenLabs conectado; Premiere aberto com os ADs
- **Funciona com:** Claude
- **Por baixo:** `hooks-meat-hook`, `photorealism-prompts`, `Higgsfield`, `ElevenLabs`, `pr_marcadores_criar`

### Frames de demonstração A/B/C

*Nível: rápido*

```text
Crie os 3 start frames de demonstração do hook [NÚMERO]: A = [OBJETO] com o problema na lente · B = o ritual sendo feito · C = o resultado.
Vertical 9:16, foto de celular realista, personagem [DESCRIÇÃO], terço de baixo livre para legenda.
Para B e C passe como referência o frame anterior E a âncora do personagem, com "IDENTITY IS CRITICAL: the SAME person as in BOTH reference images".
Número na tela? Escreva exatamente: "reads EXACTLY [NÚMERO] on the top line".
Me mostre os três lado a lado antes de animar.
Atenção: barrado pela moderação → troque o registro ("classroom model", roupa fechada) e use Nano Banana Pro.
```

- **O que faz:** Os três quadros da demonstração com identidade travada entre eles.
- **Quando usar:** Hook de demonstração antes de animar.
- **Precisa:** Higgsfield conectado (créditos)
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `hooks-meat-hook`, `photorealism-prompts`, `Higgsfield`

### Troca de produto (frasco) em criativos prontos

*Nível: completo*

```text
Troque o produto [PRODUTO ANTIGO] pelo [PRODUTO NOVO] nestes criativos: [PASTA DOS CRIATIVOS].
Vou te passar o produto novo: [IMAGENS DO PRODUTO NOVO] (ideal: frasco isolado com fundo transparente em 3 ângulos + close do rótulo).
Faça nesta ordem:
1. Mapeie cada aparição: folha de contato a cada 2 s + leitura do texto na tela (OCR) + transcrição. Cruze as três.
2. Separe o que é marca FALADA do que é dose, quantidade, preço ou garantia — só muda se o produto novo tiver spec diferente. Me pergunte.
3. Crie uma sequência por criativo com marcador em cada aparição.
4. Antes de produzir o final, me diga o que bloqueia (vídeo em baixa resolução, falta de imagem do produto, locução nova).
Atenção: OCR é o que dá o timecode confiável de marca na tela. Locução nova sempre em inglês americano.
```

- **O que faz:** Mapeia todas as aparições do produto (imagem, texto e fala) e prepara a troca por criativo.
- **Quando usar:** Reaproveitar criativos validados para vender outro produto.
- **Precisa:** Premiere aberto; FFmpeg e Whisper instalados; Imagens do produto novo
- **Funciona com:** Claude
- **Por baixo:** `Whisper`, `FFmpeg`, `pr_midia_importar`, `pr_marcadores_criar`

### Avatar falando com o produto na mão (rótulo intacto)

*Nível: completo*

```text
Gere as falas do avatar segurando o produto: still aprovado [IMAGEM] + áudio de cada fala [PASTA DOS ÁUDIOS].
Use lip sync a partir do áudio (wan 3.0, a imagem como referência, sem gerar áudio), duração inteira acima da fala.
Depois RECOLE o frasco do still aprovado por cima de cada vídeo: recorte frasco + mão, ache a posição em cada quadro por correlação e cole com borda suavizada.
Atenção: o lip sync reescreve o texto miúdo do rótulo em quase todos os clipes, e pedir no prompt não resolve. Não gaste crédito regerando por causa de rótulo — só por rosto, boca ou pose.
No fim confira: grade com o quadro do silêncio (boca fechada) e 3 quadros de pico de voz (boca aberta) de cada clipe, e o rótulo legível.
```

- **O que faz:** Lip sync com a voz certa e o rótulo do produto preservado de graça pela recolagem.
- **Quando usar:** Depoimento ou talking head com frasco na mão.
- **Precisa:** Higgsfield conectado (créditos); Áudios de voz prontos (ElevenLabs); Python com OpenCV para a recolagem (pip install opencv-python)
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `Higgsfield`, `ElevenLabs`, `FFmpeg`

### Legenda no Premiere a partir de um .srt

*Nível: rápido*

```text
Coloque a legenda [ARQUIVO .srt] na sequência [NOME DA SEQUÊNCIA] do Premiere.
Nativa (editável no painel Texto): crie a faixa de legenda direto do .srt — nada de arrastar à mão.
Animada: me mostre os estilos das Legendas MOGRT e use [ESTILO] numa trilha nova, simulando antes. Se faltar o After Effects, me avise antes de aplicar.
No fim, me diga quantos blocos entraram e em qual trilha.
```

- **O que faz:** Legenda do .srt na timeline sem arrastar nada: faixa de legenda nativa ou um clipe animado por bloco.
- **Quando usar:** Depois de revisar o .srt contra a copy.
- **Precisa:** Premiere aberto com o projeto salvo; Tools PRO 1.8.1 ou mais novo; After Effects 2026 só para a legenda animada
- **Funciona com:** Claude
- **Por baixo:** `pr_legenda_nativa_criar`, `pr_legendas_mogrt_info`, `pr_legendas_mogrt_aplicar`

### Conferir a legenda queimada contra a copy

*Nível: rápido*

```text
Confira a legenda deste criativo: [VÍDEO] e a copy [COPY].
1. Transcreva o áudio do vídeo.
2. Compare a legenda (.srt da pasta de legendas, ou o texto na tela) com a copy linha a linha.
3. Liste cada divergência com timecode: nomes próprios, números e negativas primeiro.
4. Diga também onde o ÁUDIO diverge da legenda.
Atenção: o .srt é saída crua de transcrição automática — erra exatamente onde o erro mais custa. Não confie em amostragem.
```

- **O que faz:** Pega erro de legenda que passou para o ar: nome, número, negativa, e áudio diferente do texto.
- **Quando usar:** Antes de entregar qualquer criativo com legenda.
- **Precisa:** Whisper instalado; A copy aprovada
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `Whisper`, `FFmpeg`


## Clone de AD validado

Mesmo anúncio que já vende, com outro rosto (e, se quiser, outra copy): mesma estrutura, mesmos tempos, aprovação antes de cada gasto.

### Clonar um AD validado trocando a personagem (pedido único)

*Nível: completo* · *Tempo: cerca de 1 h com as aprovações, para um trecho de 30 s*

```text
Use a skill clone-ad-validado: clone este AD validado trocando a personagem: [ARQUIVO DO AD]. Pasta do job: [PASTA DO JOB].
Personagem nova: [IDADE, ETNIA, CABELO], no mesmo estilo do original (ex.: selfie UGC). Copy: [IGUAL PALAVRA POR PALAVRA / NOVA PARA O PRODUTO X].
Faça nesta ordem e PARE para eu aprovar antes de cada etapa que gasta crédito, já com a estimativa:
1. Decupagem com Whisper (roteiro por frase, mapa de cenas com tempos, o que é refeito e o que é reaproveitado).
2. Retrato-âncora no GPT Image 2.5 sem cara de IA e o mesmo rosto em cada cenário onde ela fala.
3. 2 ou 3 vozes candidatas no ElevenLabs, medidas pelo F0 contra a original — eu escolho de ouvido; depois encaixe cada frase no mesmo segundo do original.
4. Lip sync no HeyGen Avatar IV (foto + áudio), 9:16, um vídeo por cenário.
5. Refaça no Kling 3.0 Turbo só os b-rolls que mostravam a pessoa antiga; reaproveite o resto sem a legenda antiga.
6. Monte no HyperFrames com a mesma estrutura, as mesmas transições e a legenda na mesma altura.
7. Confira: lip sync pelo quadro do silêncio × quadro do pico, folha original × clone, nenhuma imagem da pessoa antiga, legenda contra a copy e −14 LUFS.
```

- **O que faz:** O clone inteiro, do AD original ao MP4 novo, com as regras que funcionaram num clone real.
- **Quando usar:** O AD ainda vende, mas o público já cansou do rosto.
- **Precisa:** O AD validado (arquivo); Higgsfield e HeyGen conectados (créditos); Chave do ElevenLabs configurada; HyperFrames instalado (aba Ambiente)
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `clone-ad-validado`, `Whisper`, `Higgsfield`, `ElevenLabs`, `HeyGen`, `HyperFrames`

### Decupar o AD e decidir o que refazer

*Nível: rápido*

```text
Use a skill clone-ad-validado só no passo de decupagem: [ARQUIVO DO AD], pasta [PASTA DO JOB].
Transcreva palavra por palavra com o Whisper e corrija pelo que está na legenda queimada (na dúvida, vale a tela).
Monte o decupagem.md: roteiro por frase com tempos, mapa de cenas (o que aparece em cada trecho, transições no quadro exato, estilo e altura da legenda) e a coluna "no clone": personagem nova, REFEITO (mostra qualquer pedaço da pessoa antiga) ou reaproveitado.
Não gere nada — só me mostre o mapa para eu aprovar.
```

- **O que faz:** O mapa que define o custo do clone, sem gastar crédito.
- **Quando usar:** Antes de orçar ou aprovar um clone.
- **Precisa:** O AD validado (arquivo)
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `clone-ad-validado`, `Whisper`, `FFmpeg`

### Personagem nova: retrato, voz e lip sync

*Nível: completo*

```text
Use a skill clone-ad-validado, passos 3 e 4, em cima do decupagem.md de [PASTA DO JOB].
Retrato-âncora: [IDADE, ETNIA, CABELO, ROUPA], GPT Image 2.5 em 9:16, specs de câmera de celular, bloco anti-cara-de-IA, boca fechada e olhar na lente. Depois o mesmo rosto em [CENÁRIOS], com o retrato como referência.
Voz: 2 ou 3 candidatas no ElevenLabs em [IDIOMA E SOTAQUE DO PÚBLICO], tabela de F0 e palavras por minuto contra a voz original; eu escolho de ouvido. Encaixe a escolhida nos tempos do original.
Lip sync: HeyGen Avatar IV com foto + áudio, 9:16, um vídeo por cenário; meça o deslocamento do vídeo contra o áudio.
Me mostre a estimativa e espere meu ok antes de cada geração.
```

- **O que faz:** Rosto, voz e avatar falando, cada um aprovado antes de virar a base do seguinte.
- **Quando usar:** Depois do mapa aprovado.
- **Precisa:** decupagem.md aprovado; Higgsfield e HeyGen conectados; Chave do ElevenLabs configurada
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `clone-ad-validado`, `Higgsfield`, `ElevenLabs`, `HeyGen`

### Conferir o clone antes de entregar

*Nível: rápido*

```text
Use a skill clone-ad-validado, passo 7: confira [ARQUIVO DO CLONE] contra [ARQUIVO DO ORIGINAL].
Monte e me mostre: folha original × clone no mesmo segundo, varredura do clone a 4 quadros por segundo e a folha de lip sync (quadro do silêncio × quadros de pico, recortados na boca, por cenário). Não use correlação automática para reprovar sincronia.
Confira também: nenhuma imagem da pessoa antiga (rosto, cabelo, mãos, legenda antiga), o rosto novo igual em todas as cenas, legenda contra a copy palavra por palavra e −14 LUFS.
Me dê a lista do que está fora com o tempo de cada item. Não conserte nada sem eu pedir.
```

- **O que faz:** As provas de que o clone está pronto, em três imagens e uma lista.
- **Quando usar:** Antes de subir o clone no gerenciador de anúncios.
- **Precisa:** O clone renderizado e o AD original
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `clone-ad-validado`, `FFmpeg`, `Whisper`


## Conferir vídeo contra a copy

Antes de entregar ou subir: o vídeo pronto conferido por quadro, pela fala e pela legenda contra a copy e contra cada comentário do copywriter. Aponta o que está fora — não conserta.

### Conferir a demanda inteira contra a copy e os comentários

*Nível: completo* · *Tempo: cerca de 10–20 min para 20 vídeos curtos*

```text
Use a skill conferir-ads-por-frame: confira os vídeos da pasta [PASTA DOS VÍDEOS] contra a copy [ARQUIVO OU LINK DA COPY].
Leia a copy JUNTO com os comentários do copywriter e liste cada pedido de edição (insert, b-roll, lettering, troca de palavra).
Rode a conferência com transcrição (modelo medium, idioma [INGLÊS / PORTUGUÊS]) e leitura da legenda na tela.
Para cada AD e cada hook: fala × copy palavra por palavra, legenda × copy, e se cada comentário foi atendido (com o segundo onde aparece ou não).
Separe ERRO DE EDIÇÃO (corrigir) de DECISÃO DA COPY (só risco de Meta/TikTok). Antes de acusar erro de legenda, confira 2–3 quadros em volta do momento.
No fim, me entregue a lista por urgência e abra o relatorio.html.
```

- **O que faz:** A conferência completa da demanda: técnica (resolução, formato, quadro preto/congelado, silêncio), fala e legenda contra a copy, e o checklist dos comentários do copywriter atendidos ou não.
- **Quando usar:** Demanda pronta, antes de entregar para o cliente ou subir no Frame.io.
- **Precisa:** Os vídeos exportados numa pasta (sem "_QA" no caminho); A copy com os comentários (.docx, Google Doc ou texto); FFmpeg e Whisper (aba Ambiente)
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `conferir-ads-por-frame`, `FFmpeg`, `Whisper`

### QA técnico rápido antes de subir

*Nível: rápido* · *Tempo: poucos minutos*

```text
Use a skill conferir-ads-por-frame: faça o QA técnico da pasta [PASTA DOS VÍDEOS], formato [9:16 / 1:1 / 4:5], largura mínima 1080.
Sem copy: só arquivo quebrado, resolução, formato, sem áudio/silêncio, quadro preto, quadro congelado e duração. Olhe os mosaicos e me diga só o que está fora, com o AD e o segundo.
```

- **O que faz:** Pega o erro de exportação antes do cliente: resolução errada, formato errado, quadro preto no fim, trecho congelado, áudio sumido.
- **Quando usar:** Logo depois de renderizar, em qualquer lote de vídeos.
- **Precisa:** Os vídeos exportados numa pasta; FFmpeg (aba Ambiente)
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `conferir-ads-por-frame`, `FFmpeg`

### Conferir a fala de um AD palavra por palavra

*Nível: rápido*

```text
Use a skill conferir-ads-por-frame: transcreva [ARQUIVO DO VÍDEO] com o Whisper medium (idioma [INGLÊS / PORTUGUÊS]) e compare palavra por palavra com este trecho da copy: [COLE O TRECHO].
Aponte palavra trocada, frase que falta, frase que sobra, repetição e corte da primeira palavra, com o segundo de cada uma. Nome de remédio ou marca que o Whisper errou: confira ouvindo o trecho antes de acusar.
```

- **O que faz:** Prova que a locução (ou o avatar) disse exatamente a copy, e mostra onde não disse.
- **Quando usar:** Body de avatar ou locução nova chegou e você precisa saber se pode montar.
- **Precisa:** O vídeo ou áudio; O trecho da copy; Whisper (aba Ambiente)
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `conferir-ads-por-frame`, `Whisper`


## Aulas e cortes

Tirar tempo morto sem comer palavra, e remontar gravação de OBS para 16:9.

### Cortar o silêncio de uma aula (corte suave)

*Nível: rápido* · *Tempo: um módulo de ~68 min virou ~50 min*

```text
Corte os silêncios desta aula: [ARQUIVO DA AULA].
Receita aprovada:
1. Detecte pausas com silencedetect a -32 dB e 0,6 s.
2. Corte só o MIOLO de cada pausa: deixe 0,34 s depois da fala e 0,42 s antes da próxima palavra; só corte se sobrar pelo menos 0,20 s. Apare também o tempo morto do começo e do fim.
3. Render H.264 CRF 19 + AAC 192k, salvo ao lado com "(corte suave)" no nome. Não sobrescreva o original.
Atenção: margem igual de 0,35 s dos dois lados comeu palavras. A margem ANTES da próxima palavra é a que protege.
No fim confira: duração antes e depois, e ouça 3 emendas aleatórias.
```

- **O que faz:** A receita de corte que foi aprovada em módulo inteiro de aulas, sem motion.
- **Quando usar:** Aula gravada, tela + voz, sem edição.
- **Precisa:** FFmpeg instalado
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `FFmpeg`

### Cortar uma pasta inteira de aulas

*Nível: rápido*

```text
Aplique o corte suave (silencedetect -32 dB / 0,6 s, margem 0,34 s depois e 0,42 s antes) em todas as aulas de [PASTA DE ENTRADA] e salve em [PASTA DE SAÍDA] com "(corte suave)" no nome.
Uma aula de cada vez; se uma falhar, siga para a próxima e me diga qual falhou.
No fim, me dê a tabela: aula · duração antes · depois · quanto saiu.
```

- **O que faz:** O mesmo corte, em lote, com relatório por aula.
- **Quando usar:** Módulo inteiro gravado.
- **Precisa:** FFmpeg instalado
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `FFmpeg`

### Cortar master de câmera 4K sem perder qualidade

*Nível: rápido* · *Tempo: cerca de 1 minuto (contra ~18 min reencodando)*

```text
Corte o tempo morto de [ARQUIVO] SEM reencodar.
1. Confira se é ALL-I (todo quadro é keyframe) com o ffprobe. Se for, corte o vídeo por cópia pura.
2. Corte cada pedaço por número de quadros (n = arredondado(duração × fps)), não por segundos, e derive o fim do áudio desse número.
3. Corte o áudio por filtro (atrim + concat) e junte com o vídeo no fim.
Atenção: concat com inpoint/outpoint perde amostras de áudio em cada emenda (dessincronia progressiva), e cortar por segundos inclui quadro extra.
No fim confira: as três durações (arquivo, vídeo e áudio) têm que ser IGUAIS, e o número de quadros o esperado.
```

- **O que faz:** Corte frame-exato e sem perda para material que ainda vai para o After.
- **Quando usar:** Master de câmera 4K ALL-I.
- **Precisa:** FFmpeg instalado
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `FFmpeg`

### Gravação do OBS empilhada → aula 16:9 com câmera no canto

*Nível: rápido*

```text
Esta aula saiu do OBS num quadro vertical com DUAS metades empilhadas: em cima a tela, embaixo a câmera (16:9 com tarja preta). Arquivo: [ARQUIVO].
1. Meça as linhas de cada metade em 5 pontos da aula (a tarja da câmera precisa ser constante).
2. Monte numa sequência 1920×1080: V1 = tela sangrando o quadro (só Movimento, cortando barra de menu e dock); V2 = câmera em PiP no canto inferior direito com 40 px de margem (corte superior/inferior para tirar a tarja).
3. Use UMA trilha de áudio só — se o arquivo trouxer várias trilhas iguais, somadas estouram o volume.
Atenção: amostre quadros ao longo da aula antes de aceitar o corte da tela — o professor troca de app e o conteúdo pode chegar perto da borda.
No fim confira: exporte 3 quadros (começo, meio e fim) e me mostre.
```

- **O que faz:** Remonta a gravação empilhada em 16:9 com a câmera em PiP.
- **Quando usar:** Aula gravada no OBS com tela e câmera no mesmo quadro vertical.
- **Precisa:** Premiere aberto com a aula importada; Modo avançado ligado no painel Tools PRO (rodapé › Conectar IA)
- **Funciona com:** Claude
- **Por baixo:** `FFmpeg`, `pr_timeline_colocar`, `pr_extendscript`

### Achar take repetido e falso começo

*Nível: rápido*

```text
Procure takes repetidos e falsos começos em [ARQUIVO].
1. Passada rápida no arquivo inteiro só para LOCALIZAR suspeitos.
2. Para cada suspeito, recorte ~20 s e transcreva de novo com o modelo maior e tempo por palavra.
3. Me mostre só os confirmados, com o ponto de corte: fim da última palavra boa e começo do take escolhido (fique com a segunda vez).
Atenção: a passada longa inventa repetições que não existem e arredonda o tempo para o segundo — nunca corte em cima dela. Buraco na fala com áudio ALTO é conteúdo tocando na tela, não pausa.
```

- **O que faz:** Encontra e confirma takes ruins antes de cortar, sem falso positivo.
- **Quando usar:** Locução ou aula com recomeços de frase.
- **Precisa:** Whisper instalado; FFmpeg instalado
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `Whisper`, `FFmpeg`


## Reels e motion

Motion premium no After e movimento na timeline do Premiere, sem estragar o que já está animado.

### Reels com motion no After a partir dos takes

*Nível: completo* · *Tempo: cerca de 45 min do pedido à prévia*

```text
Monte um Reels 9:16 no After Effects a partir dos takes [PASTA DOS TAKES] e da copy [COPY].
Faça nesta ordem:
1. Os takes são os parágrafos da copy EM SEQUÊNCIA (não alternativas): corte o começo e o fim de cada um pelo silêncio medido e tire repetição no fim de take.
2. Divida em cenas por tempo (cartão, lista, tipografia, legenda, CTA) e me mostre o plano antes de construir.
3. Construa na comp principal que eu abri; use a referência [REFERÊNCIA] para o estilo.
4. Legenda a partir do Whisper, revisada contra a copy.
5. Suavize os keyframes e renderize uma prévia.
Atenção: o Whisper troca palavras parecidas (ex.: "hook" virou "Hulk") — revise a legenda. Não rode a organização automática de pastas se eu já tiver a minha estrutura.
No fim confira: prévia renderizada inteira, legenda contra a copy e nenhum texto fora da área segura.
```

- **O que faz:** Do take bruto à prévia do Reels com cenas de motion, legenda e suavização.
- **Quando usar:** Reels/talking head com motion tipográfico.
- **Precisa:** After Effects aberto com a comp principal; Modo avançado ligado no painel Tools PRO (rodapé › Conectar IA); Whisper instalado
- **Funciona com:** Claude
- **Por baixo:** `Whisper`, `ae_extendscript`, `ae_legendas_importar`, `ae_smoothify`

### Lettering premium no After (padrão aprovado)

*Nível: rápido*

```text
Crie os letterings das frases [FRASES COM TEMPO] na comp ativa do After, no padrão aprovado:
- Fonte geométrica extra-negrito em caixa alta; UMA expressão por frase em cor de destaque [COR].
- Brilho suave branco + brilho na cor de destaque; sombra leve.
- Fundo: o apresentador desfocado e escurecido por trás do texto.
- Palavras entrando uma a uma com blur, presas a um nulo de controle.
Sincronia: cada lettering começa na primeira palavra da frase (pelo tempo do Whisper).
Atenção: a primeira palavra da transcrição costuma vir grudada no zero — corrija só ela pelo volume do áudio; esticar a frase inteira atrasa tudo. Entrelinha calculada pelo maior corpo da frase, senão a segunda linha sobe por cima.
No fim confira: transcreva o render e confira que cada lettering entra na palavra certa.
```

- **O que faz:** Letterings no padrão visual aprovado, ancorados na fala.
- **Quando usar:** Frases de impacto em VSL, upsell ou Reels.
- **Precisa:** After Effects aberto com a comp; Whisper instalado; Modo avançado ligado no painel Tools PRO (rodapé › Conectar IA)
- **Funciona com:** Claude
- **Por baixo:** `ae_extendscript`, `Whisper`

### Legenda no After a partir da fala

*Nível: rápido*

```text
Transcreva [VÍDEO] com o Whisper, revise o texto contra a copy [COPY] e só então importe a legenda na comp ativa do After: [ESTILO: cor do texto, caixa, posição].
Blocos curtos (até ~5 palavras), nada de legenda passando de uma linha para dentro do rosto.
No fim, me mostre a lista das palavras que eu corrigi em relação à transcrição crua.
```

- **O que faz:** Legenda revisada entrando como camadas de texto na comp.
- **Quando usar:** Corte vertical, Reels ou criativo no After.
- **Precisa:** After Effects aberto com a comp ativa; Whisper instalado
- **Funciona com:** Claude
- **Por baixo:** `Whisper`, `ae_legendas_importar`, `ae_legendas_limpar`

### Punch-in sem destruir a animação que já existe

*Nível: rápido*

```text
Aplique punch-in nos clipes da V[NÚMERO] entre [INÍCIO] e [FIM]: intensidade variando entre 12% e 16% de clipe para clipe, curva suave, foco no rosto (Y 35%).
O zoom entra num efeito próprio por cima do Movimento — não mexa no meu enquadramento nem nos keyframes que eu fiz.
No fim, exporte um quadro de 2 clipes e me mostre o antes/depois.
Atenção: escala igual em todos os clipes vira tique visível. Para tirar depois, remova só o zoom aplicado (o resto fica).
```

- **O que faz:** Punch-in variado que preserva o enquadramento e as animações do editor.
- **Quando usar:** Quebrar o plano parado de talking head.
- **Precisa:** Premiere aberto com a sequência ativa
- **Funciona com:** Claude
- **Por baixo:** `pr_timeline_selecionar`, `pr_zoom_aplicar`, `pr_zoom_limpar`

### Mesmo enquadramento em vários clipes

*Nível: rápido*

```text
Selecione os clipes [TRILHA E TRECHO], com o clipe-modelo [NOME] primeiro, e copie dele só escala e posição para os outros.
Depois suavize os keyframes que já existem nesses clipes.
Atenção: na propriedade copiada, os keyframes do destino são zerados (o valor cola estático) — me avise antes se algum destino tiver animação.
```

- **O que faz:** Padroniza o enquadramento e suaviza as curvas de uma vez.
- **Quando usar:** Vários takes que precisam do mesmo corte de quadro.
- **Precisa:** Premiere aberto com a sequência ativa
- **Funciona com:** Claude
- **Por baixo:** `pr_timeline_selecionar`, `pr_copiar_atributos`, `pr_smoothify`


## Reels premium (talking head)

Talking head gravado no celular, do bruto ao Reels premium: decupagem dos takes, corte no Premiere, cor do iPhone e a edição premium (lettering, legenda palavra a palavra, telas em placas 3D, SFX) feita em código pelo HyperFrames.

### Reels premium do bruto ao vídeo pronto

*Nível: completo*

```text
Use a skill editor-de-reels-do-jhon para editar o meu Reels.
Bruto: [VÍDEO BRUTO]. Pasta de trabalho: [PASTA DO JOB]. Roteiro (o que eu ia falar): [ROTEIRO].
Siga as fases da skill e PARE em cada checkpoint para eu decidir:
1. Rode os requisitos e me diga o que é o bruto (vertical? HDR do iPhone? fps?).
2. Decupe os takes e me mostre o mapa (frase › takes › recomendado › alertas) com a prévia do corte.
3. Monte o corte e os takes por frase no Premiere pelo Tools PRO; se o bruto for HDR, corrija a cor para Rec.709.
4. Eu ajusto e exporto o corte; depois faça a edição premium no HyperFrames e me mostre um rascunho.
Atenção: nunca altere o bruto nem escreva por cima de sequência minha — tudo em pasta e sequência novas. Música só com licença.
No fim confira: o QC da skill (formato, −14 LUFS, trecho parado, zona segura) e me diga o caminho do MP4.
```

- **O que faz:** Do bruto do celular ao Reels premium, com você decidindo take, cor, música e CTA.
- **Quando usar:** Reels de talking head que vai ser postado com cara de produção.
- **Precisa:** HyperFrames com ✓ na aba Ambiente (o teste de render passou); Skill editor-de-reels-do-jhon instalada (Ambiente › Skills da IA); Whisper instalado; Premiere aberto com o painel Tools PRO e o Modo avançado ligado (rodapé › Conectar IA) — sem Premiere a skill corta pelo FFmpeg
- **Funciona com:** Claude
- **Por baixo:** `editor-de-reels-do-jhon`, `HyperFrames`, `Whisper`, `FFmpeg`

### Edição premium a partir do corte já exportado

*Nível: completo*

```text
Use a skill editor-de-reels-do-jhon, direto na fase da edição premium.
Corte já aprovado e exportado: [CORTE .mp4]. Telas e gravações reais para mostrar: [PASTA DAS TELAS]. Pasta do projeto: [PASTA DO JOB]/Edicao premium.
1. Transcreva a voz do corte e revise palavra a palavra (marca, produto, nomes) — é ela que vira legenda.
2. Monte o rascunho do roteiro: gancho na tela no 1º quadro, um hit na frase-chave, telas nas placas 3D e o CTA [TEXTO DO CTA].
3. Construa e me mostre um rascunho (--rascunho) com a folha de quadros.
Atenção: lettering de 1 a 4 palavras por linha, entrando na palavra falada; nada fora da zona segura. Marca padrão é o dourado do Editor Black Belt — para a minha, use [MARCA: cores e fontes].
No fim confira: a folha de quadros com a zona segura e a legenda contra a fala.
```

- **O que faz:** Lettering, legenda palavra a palavra, telas 3D e SFX sobre um corte pronto.
- **Quando usar:** Quando o corte já está aprovado (feito no Premiere ou em outro lugar).
- **Precisa:** HyperFrames com ✓ na aba Ambiente (o teste de render passou); Skill editor-de-reels-do-jhon instalada (Ambiente › Skills da IA); Whisper instalado; O corte exportado em H.264 vertical, SDR
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `editor-de-reels-do-jhon`, `HyperFrames`, `Whisper`, `FFmpeg`

### Render final, QC e versão acelerada do Reels

*Nível: rápido*

```text
O rascunho do Reels em [PASTA DO JOB]/Edicao premium está aprovado. Pela skill editor-de-reels-do-jhon:
1. Renderize a versão final com o nome [NOME DO REELS] — [COM ou SEM] música.
2. Rode o QC da skill e olhe a folha da zona segura antes de me mostrar.
3. Faça também a versão acelerada em [FATOR, ex.: 1.15]x e rode o QC nela.
Não mude nada na composição nesta etapa.
No fim me diga: caminho dos MP4, duração, LUFS e true peak de cada um.
```

- **O que faz:** Mixagem a −14 LUFS, render 1080×1920, QC e a versão acelerada.
- **Quando usar:** Depois que o rascunho foi aprovado.
- **Precisa:** HyperFrames com ✓ na aba Ambiente (o teste de render passou); Skill editor-de-reels-do-jhon instalada (Ambiente › Skills da IA)
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `editor-de-reels-do-jhon`, `HyperFrames`, `FFmpeg`


## Prompts de imagem e vídeo

Quando a tarefa é só o prompt — para colar no Higgsfield, Flow, Kling ou Seedance.

### Foto realista sem cara de IA (com produto)

*Nível: rápido*

```text
Escreva um prompt de imagem fotorrealista de [CENA] com [PERSONA] segurando [PRODUTO].
Ordem do prompt (a que funcionou): cena → specs de câmera (câmera, lente, ISO, luz) → bloco anti-stock → trava de produto → frase de pele.
Bloco anti-stock: "not a stock image, not a commercial shoot", cômodo vivido com bagunça pequena, luz imperfeita (janela estourada), rosto assimétrico, pele com marcas reais, mãos com veias, grão de filme nomeado, sem filtro de beleza.
Trava de produto por ÚLTIMO, com "THIS OVERRIDES EVERYTHING ABOVE", começando pela ESCALA ("the hand is clearly BIGGER than the bottle", segurado "like holding an egg" para o rótulo ficar à mostra) e o rótulo de frente.
Fundo: "any text in the background is out of focus and unreadable"; olhar para a lente.
```

- **O que faz:** O prompt na ordem que acertou rótulo, escala e realismo de primeira.
- **Quando usar:** Personas de depoimento, start frame com produto.
- **Precisa:** Imagens do produto para referência
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `photorealism-prompts`

### Avatar falante: copy em blocos para o vídeo

*Nível: rápido*

```text
Use a skill Black Belt: separe esta copy em blocos de vídeo para avatar falante, prontos para o Higgsfield, com as travas anti-bug.
Copy: [COPY]. Imagem do avatar: [IMAGEM]. Modelo: [VEO / KLING / SEEDANCE].
Blocos autocontidos (até 2.500 caracteres), falas curtas juntas em ~8–9 s, duração casando com a fala, sem legenda e sem voz extra.
Voz em inglês americano se o anúncio for para os EUA; números por extenso.
```

- **O que faz:** Divide a copy em blocos com prompt de vídeo por bloco.
- **Quando usar:** Criativo de resposta direta com avatar.
- **Precisa:** Copy e imagem do avatar
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `skill-black-belt`, `avatar-vsl-video-prompts`

### Plano 3D sem virar foto

*Nível: rápido*

```text
Escreva os prompts das cenas 3D estilo Pixar de [HISTÓRIA], uma por cena.
Toda cena abre com a trava: "A FRAME FROM A PIXAR 3D ANIMATED MOVIE. EVERYTHING in the frame is rendered in the SAME stylized 3D style. THIS IS NOT A PHOTOGRAPH." e fecha com "Present day, not vintage, no signs, no lettering".
Toda cena leva um personagem 3D como referência (crie âncora até para figurante).
Para planos abstratos (órgão, artéria), NÃO use referência de imagem: repita o mesmo bloco de estilo em todos e mude só a linha CAMERA (macro, corte, rasante, de cima).
```

- **O que faz:** Prompts que seguram o 3D nos planos de ambiente e variam a composição nos abstratos.
- **Quando usar:** Storyboard 3D, b-roll de mecanismo.
- **Precisa:** A história ou a copy
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `pixar3d`, `storyboard-viral-3d`

### Vídeo shot por shot (Seedance)

*Nível: rápido*

```text
Monte um prompt de vídeo shot por shot para o Seedance a partir deste brief: [BRIEF], [DURAÇÃO] s, [FORMATO].
Câmera, ação e tempo de cada plano; produto com rótulo de frente quando aparecer.
Atenção: duração mínima do Seedance é 4 s — cena menor gera em 4 e apara na timeline.
```

- **O que faz:** Transforma a ideia em planos prontos para gerar.
- **Quando usar:** Brand film, b-roll de produto, cena de anúncio.
- **Precisa:** O brief
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `video-prompt-builder`

### Clipe de motion puro (Vibe Motion)

*Nível: rápido*

```text
Crie um prompt para o Higgsfield Vibe Motion: [O QUE ANIMAR — ex.: reveal de preço de [PREÇO ANTIGO] para [PREÇO NOVO]], [DURAÇÃO] s, [FORMATO], sem locução.
Medidas, cores (hex), tempos (ms) e curvas exatas no prompt.
```

- **O que faz:** Motion gerado como código, com texto que não quebra.
- **Quando usar:** Hook animado, número, logo ou CTA.
- **Precisa:** Nada aberto — é só o prompt
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `vibe-motion`

### Recriar um motion de referência

*Nível: rápido*

```text
Recrie este vídeo de referência para [PRODUTO/MENSAGEM], mantendo ritmo, enquadramentos e tempos: [ARQUIVO].
Só me mostre o prompt completo e os ajustes — não gere ainda.
```

- **O que faz:** Usa o vídeo como molde e troca o assunto, sem gastar crédito antes da sua aprovação.
- **Quando usar:** Você achou um motion que quer adaptar.
- **Precisa:** O vídeo de referência
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `motion-design`, `omni-flash-reverse`


## Plataforma de IA própria

Sua plataforma de gerar imagem e vídeo com a sua marca, na API do Higgsfield — sem assinatura e sem expor a chave.

### Montar o prompt de design da sua plataforma

*Nível: rápido*

```text
Use a skill plataforma-ia-higgsfield: preencha o prompt de design da minha plataforma de IA.
Nome: [NOME DA MARCA]. Cor de destaque: [COR EM HEX]. Tom: [PREMIUM / MINIMALISTA / CRIATIVO]. Modelos no seletor: [IMAGEM E VÍDEO QUE EU QUERO].
Me entregue o texto pronto para colar no ChatGPT ou no Claude logo depois do setup prompt do Higgsfield, com SUA_CHAVE_AQUI no lugar de qualquer chave.
Não me peça a chave em momento nenhum.
```

- **O que faz:** O prompt completo (visual estilo Apple, modo claro e escuro, seletor de modelos, histórico e a regra de segurança da chave), preenchido com a sua marca.
- **Quando usar:** Você vai montar a plataforma num chat.
- **Precisa:** Conta no Higgsfield com chave de API criada (a chave fica com você)
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `plataforma-ia-higgsfield`

### Criar a plataforma na sua pasta (sem expor a chave)

*Nível: completo*

```text
Use a skill plataforma-ia-higgsfield, caminho B: crie a minha plataforma de IA em [PASTA].
Vou colar abaixo o setup prompt do Higgsfield — sem a chave. Marca: [NOME], cor [HEX], tom [TOM].
Regras: a chave nunca no código nem no chat; a plataforma pede a chave numa tela de configuração e guarda só no navegador, mostrando só os 4 últimos caracteres. Se a API recusar chamada pelo navegador (CORS), crie o servidor intermediário que lê a chave de variável de ambiente.
Me mostre a estrutura antes de escrever e, no fim, confira que nenhuma chave ficou escrita nos arquivos. Não gere nada na minha conta para testar sem me perguntar.
[SETUP PROMPT DO HIGGSFIELD]
```

- **O que faz:** Os arquivos da plataforma prontos para abrir no navegador, com a chave fora do código.
- **Quando usar:** Você quer a plataforma montada direto no seu computador.
- **Precisa:** Setup prompt do Higgsfield (a janela "Save your API key"); Uma pasta para os arquivos
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `plataforma-ia-higgsfield`, `Higgsfield`, `pastas do computador`
