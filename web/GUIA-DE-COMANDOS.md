# Guia de comandos — Editor Automático

Comandos prontos para colar na Conversa do app (ou no Claude Code). Troque o que está entre colchetes pelo seu caso. A IA sempre mostra o plano antes de mexer no projeto — e o que gasta crédito pede sua aprovação.

**Quem roda:** **Claude** — Usa as ferramentas do plugin Tools PRO — precisa do Claude conectado. · **Claude e ChatGPT** — Funciona com qualquer uma das duas IAs do app.


## Começar e conferir

Antes de editar: a IA olha o que está aberto e confirma que está no projeto certo.

### Ver o que está aberto

```text
O que está aberto no Premiere agora? Me diga o projeto, a sequência ativa e o que tem na timeline.
```

- **O que faz:** Lê o projeto e a sequência ativa e resume clipes, trilhas e marcadores.
- **Quando usar:** Sempre no começo — confirma que a IA vai mexer no projeto certo.
- **Precisa:** Premiere aberto; Painel Tools PRO aberto (Janela › Extensões)
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `adobe_estado`, `timeline_ler`

### Trocar de sequência

```text
Liste as sequências deste projeto e ative a [nome da sequência].
```

- **O que faz:** Mostra as sequências e torna outra a ativa, conferindo que a troca aconteceu.
- **Quando usar:** Quando o comando seguinte precisa agir em outra sequência.
- **Precisa:** Premiere aberto com o projeto
- **Funciona com:** Claude
- **Por baixo:** `pr_sequencias_listar`, `pr_sequencia_ativar`

### Retrato da timeline

```text
Me mostre o que tem em cada trilha de vídeo e de áudio da sequência ativa, com início e fim de cada clipe.
```

- **O que faz:** Lista trilha por trilha, com tempos e quais trilhas estão mudas.
- **Quando usar:** Para conferir o resultado depois de qualquer mudança.
- **Precisa:** Sequência ativa no Premiere
- **Funciona com:** Claude
- **Por baixo:** `pr_timeline_listar`


## Organizar projeto

Bins e pastas arrumados sem mexer em nenhum arquivo do disco.

### Organizar o projeto do Premiere

```text
Organize o projeto do Premiere em bins (vídeos, áudios, imagens, sequências, legendas). Primeiro me mostre o plano; só aplique depois que eu aprovar.
```

- **O que faz:** Lê todos os itens, monta um plano de bins e, com seu ok, move os itens. Não toca em nada no disco.
- **Quando usar:** Projeto bagunçado, antes de entregar ou passar para outro editor.
- **Precisa:** Premiere aberto com o projeto; Só um projeto aberto (com dois, o Premiere pode escrever no errado)
- **Funciona com:** Claude
- **Por baixo:** `pr_organizar_analisar`, `pr_organizar_aplicar`

### Desfazer a organização

```text
Desfaça a última organização que você fez no projeto.
```

- **O que faz:** Devolve cada item ao bin e ao nome de antes e apaga os bins vazios que ela criou.
- **Quando usar:** Se o resultado não ficou como você queria.
- **Precisa:** Na mesma conversa em que a organização foi feita
- **Funciona com:** Claude
- **Por baixo:** `pr_organizar_desfazer`

### Organizar o projeto do After

```text
Organize o projeto do After Effects em pastas (comps principais, precomps, vídeos, imagens, áudios, sólidos). Me mostre o plano antes de aplicar.
```

- **O que faz:** Classifica cada item (inclusive o que é comp principal ou precomp) e move para pastas. Um Cmd/Ctrl+Z no After desfaz tudo.
- **Quando usar:** Projeto de motion com muitos itens soltos.
- **Precisa:** After Effects aberto com o projeto; Painel Tools PRO aberto no After
- **Funciona com:** Claude
- **Por baixo:** `ae_organizar_analisar`, `ae_organizar_aplicar`

### Salvar o projeto

```text
Salve o projeto do Premiere.
```

- **O que faz:** Salva o projeto aberto.
- **Quando usar:** No fim de um lote de mudanças.
- **Precisa:** Projeto que já foi salvo uma vez (com nome e pasta)
- **Funciona com:** Claude
- **Por baixo:** `pr_projeto_salvar`


## Cortar silêncio e transcrever

Feito no seu computador com FFmpeg e Whisper — o Tools PRO não corta áudio, então o corte sai num arquivo novo.

### Cortar os silêncios de um vídeo

```text
Corte os silêncios deste vídeo com FFmpeg: [caminho do vídeo]. Use silencedetect a -32 dB com 0,6 s, deixe 0,34 s depois e 0,42 s antes de cada fala, e salve uma cópia ao lado com "(corte suave)" no nome. Não sobrescreva o original.
```

- **O que faz:** Detecta as pausas, corta só o miolo delas (margem generosa para não comer palavra) e gera um vídeo novo.
- **Quando usar:** Aula, talking head ou locução com muitas pausas.
- **Precisa:** FFmpeg instalado (aba Ambiente); O caminho do vídeo
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `FFmpeg`

### Transcrever palavra por palavra

```text
Transcreva este vídeo com o Whisper, com tempo de cada palavra, e salve o .srt ao lado: [caminho do vídeo].
```

- **O que faz:** Gera a legenda/transcrição no seu computador, sem subir o vídeo para lugar nenhum.
- **Quando usar:** Para legenda, para conferir a fala contra a copy ou para marcar pontos de b-roll.
- **Precisa:** Whisper instalado (aba Ambiente)
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `Whisper`


## Marcadores e cortes

Convenção da casa: vermelho = b-roll, azul = lettering, roxo = decisão humana.

### Marcar os pontos de b-roll pela fala

```text
Marque esta timeline para b-roll seguindo a fala: vermelho onde entra b-roll, azul onde entra lettering e roxo onde eu preciso decidir. Me mostre a lista antes de criar os marcadores.
```

- **O que faz:** Transcreve, escolhe os pontos ancorados na fala e cria todos os marcadores de uma vez, com nome e comentário.
- **Quando usar:** Antes de gerar ou colocar b-roll.
- **Precisa:** Sequência ativa com o body; Whisper instalado
- **Funciona com:** Claude
- **Por baixo:** `editor-automatico-de-broll`, `pr_marcadores_criar`

### Cortar nos marcadores

```text
Corte a timeline nos marcadores verdes. Simule antes e me diga quantos cortes sairiam — não corte nos vermelhos, azuis e roxos.
```

- **O que faz:** Divide os clipes nos marcadores da cor escolhida. Simula primeiro, porque cortar não tem desfazer pela IA.
- **Quando usar:** Quando você já marcou à mão onde quer os cortes.
- **Precisa:** Sequência ativa com marcadores
- **Funciona com:** Claude
- **Por baixo:** `pr_autoclip_info`, `pr_autoclip`

### Apagar marcadores

```text
Apague os marcadores cujo nome começa com [prefixo] — me diga quantos são antes de apagar.
```

- **O que faz:** Apaga só os marcadores que batem com o critério (prefixo, intervalo de tempo ou todos).
- **Quando usar:** Para limpar uma marcação que não vale mais.
- **Precisa:** Sequência ativa
- **Funciona com:** Claude
- **Por baixo:** `pr_marcadores_listar`, `pr_marcadores_apagar`


## B-roll

Do bruto do avatar ao criativo montado — o que gasta crédito sempre pede aprovação.

### Editar um criativo inteiro com b-roll

```text
Edite este criativo: [pasta com o body, a copy e a foto do avatar]. Coloque b-roll da mesma pessoa, punch-ins e legenda, e monte no Premiere. Vá etapa por etapa e me peça aprovação antes de gerar.
```

- **O que faz:** Roda as 12 etapas do app: análise, confere a copy, marca, planeja, gera imagens e vídeos (com sua aprovação), acabamento, montagem e controle de qualidade.
- **Quando usar:** UGC/VSL 9:16 de avatar falante em plano fixo.
- **Precisa:** Higgsfield conectado (créditos); ElevenLabs para voz; Premiere aberto com o projeto
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `editor-automatico-de-broll`, `etapas do app`

### Colocar os vídeos de uma pasta na timeline

```text
Importe os vídeos da pasta [caminho] para o bin B-ROLL e coloque cada um na V2, no marcador vermelho correspondente. Simule antes e me mostre onde cada um entra.
```

- **O que faz:** Importa em lote e coloca tudo de uma vez — se algum nome ou trilha estiver errado, nada é colocado.
- **Quando usar:** Quando os b-rolls já existem (gerados ou de banco).
- **Precisa:** Sequência ativa marcada; Os arquivos na pasta do projeto
- **Funciona com:** Claude
- **Por baixo:** `pr_midia_importar`, `pr_timeline_colocar`

### Calar o som dos b-rolls

```text
Silencie a trilha de áudio dos b-rolls ([A2]).
```

- **O que faz:** Deixa a trilha inteira muda, sem apagar nada. Volta com "devolva o som da A2".
- **Quando usar:** B-roll gerado com áudio que atrapalha a fala.
- **Precisa:** Sequência ativa
- **Funciona com:** Claude
- **Por baixo:** `pr_timeline_mudo`

### Refazer um b-roll específico

```text
Regere o b-roll do insert [número] com outra roupa e outro enquadramento, mantendo a mesma pessoa.
```

- **O que faz:** Gera de novo só aquele insert e troca na timeline.
- **Quando usar:** Um insert saiu com defeito ou repetido.
- **Precisa:** Projeto do app em andamento; Higgsfield conectado
- **Funciona com:** Claude
- **Por baixo:** `editor-automatico-de-broll`


## Zoom, suavização e atributos

Movimento no plano parado. Transições ainda não têm ferramenta própria no plugin.

### Punch-in nos clipes do avatar

```text
Selecione os clipes da V1 e aplique punch-in variando entre 12% e 16% de clipe para clipe, curva suave, foco no rosto (Y 35%).
```

- **O que faz:** Anima o zoom num efeito próprio, por cima do Movimento — o seu enquadramento não é tocado.
- **Quando usar:** Para quebrar o plano parado de talking head/UGC.
- **Precisa:** Sequência ativa
- **Funciona com:** Claude
- **Por baixo:** `pr_timeline_selecionar`, `pr_zoom_aplicar`

### Tirar o zoom

```text
Tire o zoom que você aplicou nos clipes selecionados.
```

- **O que faz:** Remove só o efeito de zoom do plugin; o Movimento e os keyframes feitos à mão ficam.
- **Quando usar:** Para refazer o punch-in de outro jeito.
- **Precisa:** Clipes selecionados
- **Funciona com:** Claude
- **Por baixo:** `pr_zoom_limpar`

### Suavizar keyframes no Premiere

```text
Deixe suaves (ease in/out) os keyframes dos clipes selecionados.
```

- **O que faz:** Muda a curva dos keyframes que já existem, sem criar novos.
- **Quando usar:** Animação mecânica, com cara de linear.
- **Precisa:** Clipes com keyframes selecionados
- **Funciona com:** Claude
- **Por baixo:** `pr_smoothify`

### Copiar escala e posição

```text
Copie escala e posição do primeiro clipe selecionado para os outros selecionados.
```

- **O que faz:** Cola só os atributos que você pediu; o resto fica como estava.
- **Quando usar:** Padronizar o enquadramento de vários clipes.
- **Precisa:** Pelo menos 2 clipes selecionados (o primeiro é a fonte)
- **Funciona com:** Claude
- **Por baixo:** `pr_copiar_atributos`

### Suavizar keyframes no After

```text
No After, dê ease suave nos keyframes das camadas selecionadas.
```

- **O que faz:** Ajusta a curva de tempo dos keyframes. Um Cmd/Ctrl+Z no After volta.
- **Quando usar:** Motion com movimento duro.
- **Precisa:** After Effects aberto; Camadas selecionadas na composição ativa
- **Funciona com:** Claude
- **Por baixo:** `ae_smoothify`


## Legendas e títulos (After Effects)

A legenda nasce do Whisper e entra no After como camadas de texto.

### Legendar uma composição

```text
Transcreva [caminho do vídeo] com o Whisper e importe a legenda na composição ativa do After: texto branco, contorno preto, na parte de baixo.
```

- **O que faz:** Gera o .srt e cria uma camada de texto por bloco, já posicionada e estilizada.
- **Quando usar:** Legenda queimada em criativo ou corte vertical.
- **Precisa:** After Effects aberto com a composição ativa; Whisper instalado
- **Funciona com:** Claude
- **Por baixo:** `Whisper`, `ae_legendas_importar`

### Tirar a legenda gerada

```text
Remova as legendas que você criou nesta composição.
```

- **O que faz:** Apaga só as camadas criadas pela ferramenta — texto feito à mão fica.
- **Quando usar:** Para refazer a legenda com outro estilo.
- **Precisa:** Composição ativa no After
- **Funciona com:** Claude
- **Por baixo:** `ae_legendas_limpar`

### Inserir um título animado

```text
Insira o título animado [caminho do .mogrt] na composição ativa com o texto "[seu texto]".
```

- **O que faz:** Importa o template de título e troca o texto.
- **Quando usar:** Abertura, lettering ou chamada com template pronto.
- **Precisa:** After Effects aberto; O arquivo .mogrt
- **Funciona com:** Claude
- **Por baixo:** `ae_titulos_inserir`


## Motion e overlays

Motion graphics gerado por IA (Higgsfield/Google Flow) e prompts prontos para colar.

### Motions de oferta para uma VSL

```text
Gere os motions das marcações de oferta desta VSL no estilo escuro (preço, garantia, bônus, CTA), aplique na timeline e confira a grafia de cada um.
```

- **O que faz:** Produz o lote de overlays no mesmo sistema visual, coloca por cima do body e confere o texto quadro a quadro.
- **Quando usar:** VSL ou criativo de resposta direta com a timeline já marcada.
- **Precisa:** Timeline marcada; Higgsfield conectado (créditos); Premiere aberto
- **Funciona com:** Claude
- **Por baixo:** `motion-omni-vsl`

### Clipe de motion puro (Vibe Motion)

```text
Crie um prompt para o Higgsfield Vibe Motion: reveal de preço de [preço antigo] para [preço novo], 6 s, vertical 9:16, sem locução.
```

- **O que faz:** Escreve o prompt com medidas, cores e tempos exatos para gerar o motion como código — o texto não quebra.
- **Quando usar:** Hook animado, número, logo ou CTA sem pessoa falando.
- **Precisa:** Nada aberto — é só o prompt
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `vibe-motion`

### Escolher um estilo de motion

```text
Me mostre a galeria de motion design e recomende 3 estilos para [produto/campanha].
```

- **O que faz:** Abre a galeria de estilos e sugere os que combinam com a sua campanha.
- **Quando usar:** Quando você não sabe por onde começar o motion.
- **Precisa:** Nada aberto
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `motion-design`

### Recriar um motion de referência

```text
Recrie este vídeo de referência para o meu produto, mantendo o ritmo e os enquadramentos: [arquivo]. Só me mostre o prompt — não gere ainda.
```

- **O que faz:** Usa o vídeo como molde e troca assunto e texto. Mostra o prompt completo antes de gastar crédito.
- **Quando usar:** Você achou um motion que quer adaptar.
- **Precisa:** O vídeo de referência
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `motion-design`, `omni-flash-reverse`

### Copy em clipes estilo Black Belt

```text
Transforme esta copy em clipes de 10 s no estilo Black Belt (estúdio escuro, cards de vidro dourados, legenda karaokê): [copy].
```

- **O que faz:** Fatia a copy e entrega um prompt por clipe, pronto para o Google Flow / Omni Flash.
- **Quando usar:** Talking head com motion embutido.
- **Precisa:** A copy
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `blackbelt-omni`


## Hooks

Hooks novos no formato Meat Hook para ADs já validados.

### Gerar hooks novos

```text
Gere hooks Meat Hook para estes ADs validados a partir da copy [doc ou arquivo]. Comece pela tabela de hooks e espere minha aprovação antes de gerar qualquer imagem.
```

- **O que faz:** Mapeia os hooks, gera os frames de início, coloca no Premiere para aprovação, anima, unifica a voz e monta hook + body.
- **Quando usar:** Trocar ou empilhar hooks em criativos que já performam.
- **Precisa:** Copy com os comentários do copywriter; Higgsfield e ElevenLabs conectados; Premiere aberto
- **Funciona com:** Claude
- **Por baixo:** `hooks-meat-hook`

### Empilhar um hook no AD

```text
Empilhe o hook [H03] no início do [AD02] e me mostre o quadro da emenda.
```

- **O que faz:** Monta o hook antes do body inteiro e confere o ponto de corte.
- **Quando usar:** Depois que os hooks foram aprovados.
- **Precisa:** Hooks aprovados; Premiere aberto
- **Funciona com:** Claude
- **Por baixo:** `hooks-meat-hook`


## Prompts de imagem e vídeo

Para quem gera no Higgsfield, Flow, Kling, Veo ou Seedance. Nada abre no Premiere.

### Do zero ao criativo (skill mestra)

```text
Use a skill Black Belt: aqui está a copy e a foto do avatar. Separe em blocos de vídeo prontos para o Higgsfield, com as travas anti-bug. [copy + imagem]
```

- **O que faz:** Divide a copy em blocos autocontidos e escreve o prompt de cada um para avatar falante.
- **Quando usar:** Criativo de resposta direta com avatar falando.
- **Precisa:** Copy; Imagem do avatar
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `skill-black-belt`, `avatar-vsl-video-prompts`

### Imagem fotorrealista

```text
Crie um prompt de imagem fotorrealista de [cena], com câmera, lente, luz e pele realistas, sem cara de IA.
```

- **O que faz:** Escreve o prompt com especificação fotográfica completa.
- **Quando usar:** Start frame, foto de produto ou cena de b-roll.
- **Precisa:** Nada aberto
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `photorealism-prompts`

### Vídeo shot por shot (Seedance)

```text
Monte um prompt de vídeo shot por shot para o Seedance a partir deste brief: [brief], [duração] s.
```

- **O que faz:** Transforma a ideia em planos com câmera, ação e tempo de cada um.
- **Quando usar:** Brand film, b-roll de produto ou cena de anúncio.
- **Precisa:** O brief
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `video-prompt-builder`

### Storyboard com personagem 3D

```text
Crie um storyboard cena por cena no estilo personagem 3D (Pixar) para [produto], com prompt de imagem, locução e legenda de cada cena.
```

- **O que faz:** Entrega o roteiro visual completo, cena a cena, pronto para gerar.
- **Quando usar:** Criativo viral de TikTok Shop com personagem animado.
- **Precisa:** Produto ou copy
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `storyboard-viral-3d`, `pixar3d`

### B-roll a partir de um vídeo pronto

```text
Divida este vídeo em blocos de 10 s alinhados à fala e gere, para cada bloco, um prompt de b-roll para o Google Flow: [caminho do vídeo].
```

- **O que faz:** Transcreve, divide e escreve a tradução visual de cada trecho.
- **Quando usar:** Ilustrar um vídeo já gravado.
- **Precisa:** O vídeo; Whisper instalado
- **Funciona com:** Claude e ChatGPT
- **Por baixo:** `video-to-flow`


## Avançado

Para o que nenhuma ferramenta pronta cobre. Use com cuidado.

### Script sob medida no Premiere ou no After

```text
Não existe ferramenta pronta para isto: [o que você quer]. Escreva um ExtendScript, me mostre antes e rode no [Premiere/After] só depois do meu ok.
```

- **O que faz:** Roda um script feito na hora dentro do programa, pelo painel do plugin.
- **Quando usar:** Tarefa repetitiva que as ferramentas acima não fazem.
- **Precisa:** Modo avançado ligado no painel Tools PRO (rodapé › Conectar IA); Premiere ou After aberto
- **Funciona com:** Claude
- **Por baixo:** `pr_extendscript`, `ae_extendscript`
