# Armadilhas — o que já quebrou em job real

## Whisper
- **Passada longa inventa e omite.** Inventa "E", "aí", "Obrigado" com duração
  fixa dentro do silêncio; colapsa frase inteira numa palavra de 2–3 s. Sempre por
  trecho (transcrever.py) e reconferindo janela curta antes de afirmar "esse take
  não existe" ou "aqui tem falso começo".
- **Nome próprio sai trocado**: "editar"→"estar", "IA"→"EA", "GPT"→"ABT",
  "bio"→"Bill", "Tá no ar"→"Itanor". Passe `--termos` e revise com
  `revisar_transcricao.py`: é a transcrição revisada que vira legenda.
- Formatar minuto com `f"{t/60:.0f}"` arredonda (7:34 vira "8:34"). Use `int(t//60)`.

## Premiere / Tools PRO
- `createNewSequence` abre o diálogo "Nova sequência" e trava a ponte (timeout em
  tudo, até leitura). Diagnóstico: o servidor responde `tools/list` na hora mas
  scripts não. Peça ao aluno para olhar o Premiere e clicar **Cancelar**.
  Prevenção: `createNewSequenceFromClips` (o script já usa).
- Timeout não quer dizer que nada aconteceu: **leia de volta antes de repetir**.
- `overwriteClip` com string de segundos joga o clipe no 0 sem erro. Sempre `Time`
  em ticks; nunca `insertClip` (empurra o resto).
- `sequence.timebase` real pode não ser 254016000000/fps exato: confira encaixe
  lendo `start/end.ticks` do Premiere, não recalculando.
- O efeito Recortar pela QE "entra" sem erro e não aplica. Para corte de borda use
  as propriedades escondidas do Movimento. Aqui não é necessário.
- Camada de ajuste não é criável pela API: o Lumetri vai clipe a clipe.
- Modo avançado desligado = o Premiere recusa ExtendScript com a mensagem por
  extenso. Só o aluno liga (de propósito, não há rota para a IA se autorizar).

## Cor
- HDR do iPhone (HLG, bt2020) com `libx264 yuv420p` sem tone map = cor lavada.
  A conversão certa é no Premiere (Rec.709 + tone map automático).
- Rotação −90 do iPhone: Premiere e ffmpeg já desviram; confira com ffprobe,
  não presuma.

## HyperFrames
- **Tranco no lettering**: elemento animado depois com `immediateRender:false`
  aparece pronto, some e entra. Cada elemento tem UM primeiro tween que o esconde
  desde o carregamento (o construir já faz assim).
- **Lapso**: câmera com `sine.inOut` por cena para no fim de cada cena. Deriva
  sempre `ease: none`; o QC acusa com `freezedetect`.
- Empurrar palavras em Z (perspectiva) a cada batida faz o texto pular de lugar.
- Vídeo inserido precisa de keyframe denso (novo_projeto.py reencoda telas em
  30 fps, GOP 30) senão o render pega quadro errado.
- Ids únicos no projeto montado: o construir prefixa tudo com o id da cena.
- Fonte sem `@font-face` local = lint falha e o render usa fonte do sistema.
- Ícones ✓ ● não existem nas fontes da marca: use SVG/CSS (o cartão já usa).

## Áudio
- Mixar SEM ducking: a música briga com a voz. Sidechain sempre.
- Normalizar só pelo pico estoura loudness do Reels; o alvo é −14 LUFS integrado
  com true peak ≤ −1 dBTP (o Instagram reduz o que passar).
- Acelerar a imagem e o som em comandos separados = dessincroniza. Sempre juntos,
  depois do vídeo pronto.

## Arquivos
- Drive/nuvem: ler vídeo direto de pasta sincronizada pode travar o ffmpeg ou o
  Premiere. Copie para o disco local primeiro.
- Nunca importe mídia de pasta temporária: tudo que entra no projeto vive na
  pasta do projeto.

## Acrescentadas depois (valem também para o Reels)
- **Whisper: palavra com duração absurda** (> 1,5 s em fala corrida) é trecho ENGOLIDO,
  não pausa. Repasse a janela com `large-v3` antes de dizer que a frase não foi gravada.
  Palavra "dentro" de um corte: meça o nível; pico abaixo de ~−26 dBFS é alucinação.
- **Referência baixada do Instagram (VP9/AV1)**: o `scene detect` do ffmpeg devolve zero
  cortes sem erro. Para medir o ritmo de cortes de uma referência, use a diferença de
  luminância entre quadros em miniatura e confira cada candidato no quadro.
- **Copiar a legenda de uma referência**: detectar a faixa automaticamente não funciona
  (pega olhos/boca e camisa clara). Posição a olho com grade; corpo da fonte pela
  **largura** do texto medido na referência.
- **Premiere travado depois de importar vários arquivos** (CPU 0 %, toda chamada em
  timeout): é deadlock, não processamento. Importe um arquivo por vez; ao reabrir,
  confira a pasta Auto-Save antes de achar que perdeu o import.
- **Efeito pelo nome**: no Premiere em português a tradução é mista (`Movimento`,
  `Escala` em PT; `Track Matte Key` em EN). Procure por lista de candidatos e confira o
  valor lido de volta — "ok" sem erro não prova que aplicou.
- **Cópia da nuvem truncada**: um `cp` pode morrer calado. Compare o tamanho local ×
  remoto antes de analisar ou importar.
- Mais, por ferramenta: skill `boas-praticas-black-belt`.
