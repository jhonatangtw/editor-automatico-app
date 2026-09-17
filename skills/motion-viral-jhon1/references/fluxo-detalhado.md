# Fluxo detalhado — do briefing ao relatório

Cada etapa tem uma **trava**: o que precisa existir antes de seguir. A ordem existe porque cada
passo alimenta o seguinte (a transcrição dá os timecodes; os timecodes dão o mapa; o mapa dá as cenas).

## 1. Validar a demanda
- `ls -la` da pasta e subpastas; `ffprobe` (codec, resolução, fps, duração) em todo vídeo; PIL nas imagens.
- Identificar: takes (`lip/`, `takes/`, arquivos com "take"/"hook"/"body"), B-rolls, referência local, `.aep`.
- **Nunca** apagar, mover ou sobrescrever original. Materiais novos vão para `05_Assets_IA/`, `07_SFX/`.
- Trava: lista de arquivos com veredito (usa / não usa / por quê).

## 2. Ler a copy e os comentários
- `get_file_metadata` primeiro: título começando com "Cópia de" = os comentários não vieram junto.
- `read_file_content` com `includeComments: true`. O retorno traz `commentThreads` (com `status`
  OPEN/RESOLVED e replies) e o texto com âncoras `<comment_start id=kix.…>` — **a API não liga o
  thread à âncora**: relacionar pelo conteúdo do comentário com o trecho da copy e com os nomes dos
  arquivos de B-roll (o editor costuma nomear pelo pedido).
- Documento com vários ADs: recortar só a seção da demanda.
- Conflito entre comentários: vale o mais recente; sinalizar antes de executar.
- Trava: `00_brief/COMENTARIOS_APLICADOS.md` + mapa de inserts iniciado (`references/mapa-de-inserts.md`).

## 3. Analisar as referências
- Link (Pinterest/Reels/TikTok): `yt-dlp` baixa; folha de contato a 2 fps + abertura a 8–10 fps; transcrição
  se houver fala; medir tipografia/paleta/posições por pixel (`PIL`/`numpy`), não de olho.
- Vídeo local: mesma folha; medir costura de split, caixa de legenda (cor moda, altura, centro), blocos/s.
- Registrar em `00_brief/ANALISE_REFERENCIAS.md`: ritmo, densidade, tipografia, paleta, composição,
  hierarquia, entradas/saídas, transições, zooms/câmera, tratamento de B-roll, legendas, SFX, elementos
  recorrentes, momentos de impacto — e **o que se leva vs. o que fica**.
- Trava: análise escrita; gramática escolhida (`formato-podcast-split.md` ou `IDENTIDADE.md`).

## 4. Analisar os takes
- Whisper `large-v3-turbo` com `word_timestamps=True` em todos; comparar com a copy palavra a palavra.
- Vários arquivos costumam ser **segmentos** (hook / resposta / body), não alternativas.
- Áudio (`volumedetect`), enquadramento (YuNet: centro do rosto, olhos), iluminação, performance.
- Cortes só em silêncio medido (`silencedetect`); repetição no fim do take → cortar antes; palavra
  estrangeira transcrita errado → a legenda vem da copy, alinhada pelos tempos.
- Trava: `00_brief/transcripts/*.json` + `ancoras.json` com o tempo de cada palavra-âncora.

## 5. Preparar os materiais
- Prioridade: o que está na pasta. B-roll com número/texto no quadro tem que bater com a copy.
- Higgsfield só com autorização e só para objeto que falta (`references/prompts-asset.md`); recortar
  com `lib/recortar_gradiente.py`; conferir cada PNG antes de importar (texto de IA = reprovado).
- Trava: todo asset conferido visualmente e gravado **na pasta da demanda** (nunca no scratchpad).

## 6. Organizar
- Pastas `01_Footage · 02_Audio · 03_Broll · 04_Imagens · 05_Assets_IA · 06_Precomps · 07_SFX · 08_Exports`
  na demanda e no projeto. Camadas/precomps nomeados pelo trecho da copy (`CARD_harvard_lab`,
  `SPLIT_ritual_receita`, `LET_13lb`). Não mover mídia vinculada.

## 7. Executar no After Effects
- Conexão: `lib/toolspro.sh tools/list` (porta 7843). Se falhar, dizer **o quê** falhou e seguir com
  tudo que não depende do AE (análise, transcrição, mapa, assets). A construção é por ExtendScript
  (`lib/rodar.sh`); o Tools PRO entra para legendas e leitura de volta.
- Estado: script de uma linha lê `app.project.file` e a comp ativa antes de escrever qualquer coisa.
- Construir cena a cena (`ae_lib.jsx` + `ae_podcast.jsx`), `report()` + `frame()` em cada uma.
- Regras: safe margins (100 px topo, 260 px rodapé), legenda longe de olhos/boca/costura, entrada +
  permanência + saída para tudo, `fundoSobCartao()` sob imagem em destaque, `reenquadrar()` no split.
- Trava: frames exportados de cada cena revisados **antes** de avançar.

## 8. Finalização e QA
1. `ae_titulos_info`/`ae_organizar_info` (Tools PRO) lêem o projeto de volta; `ae_smoothify` se disponível.
2. `lib/conferir_render.py frames` nos principais momentos; folhas de contato do vídeo inteiro.
3. Conferir textos (grafia = copy), enquadramentos, recortes, mãos, rostos, sobreposições.
4. Nenhuma camada com `outPoint` além da comp; nenhum efeito vivo sem o elemento na tela.
5. `lib/conferir_render.py sync` 4 f antes / 6 f depois de cada palavra-âncora.
6. `app.project.save()` por script (o `aerender` lê o disco).
7. `lib/render.sh` (recusa render duplo, valida com ffprobe).
8. Resolução, fps, duração, áudio (`volumedetect`), último quadro não preto.

## 9. Relatório
Demanda · take · referências · comentários aplicados · inserts · B-rolls/imagens · gerados · animações
por trecho · caminho do projeto · caminho do render · pendências/limitações · tempo.
