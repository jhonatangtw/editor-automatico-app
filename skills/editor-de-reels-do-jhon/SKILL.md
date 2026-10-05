---
name: editor-de-reels-do-jhon
description: Editor de Reels do Jhon. Edita Reels de talking head (gravado no celular) do bruto ao vídeo premium pronto para postar — decupa os takes com Whisper, monta o corte no Premiere pelo Tools PRO (sequência de corte + sequência com todos os takes por frase), corrige a cor HDR do iPhone para Rec.709, e depois faz a edição premium em HyperFrames (lettering no 1º quadro, "hit" dourado, telas reais em placas 3D, cartão de aprovação, legenda palavra a palavra na zona segura, ~25 punch-ins, SFX, mixagem -14 LUFS, QC e aceleração final). Use SEMPRE que o aluno disser "edita meu reels", "edição de reels", "talking head premium", "decupa meus takes", "escolhe o melhor take", "monta o corte no Premiere", "corrige a cor do iPhone", "meu vídeo ficou lavado/claro", "reels de lançamento", "deixa meu reels premium", "coloca lettering e legenda no meu reels", "acelera meu reels" ou mandar um vídeo vertical gravado no celular pedindo edição. NÃO é para cortar silêncio de aula longa (use cortar-aula), nem para criativo de anúncio com B-roll de IA (use editor-automatico-de-broll), nem para conferir vídeo já pronto (use conferir-ads-por-frame).
---

# Editor de Reels do Jhon — talking head premium

O fluxo que editou um Reels de lançamento real, do bruto do iPhone ao vídeo
premium de 65 s, transformado em receita. São 7 fases com um **ponto de
conferência** no fim de cada uma. Quem decide take, música, velocidade, marca
e CTA é **o aluno** — você pergunta, mostra e executa.

`SK` abaixo = a pasta desta skill. Os scripts rodam com `python3 "$SK/scripts/..."`.

## Antes de tudo

1. `bash "$SK/scripts/requisitos.sh"` — Node 22+, HyperFrames, ffmpeg, Whisper e
   numpy. O HyperFrames usado é o atalho do Editor Automático
   (`~/.editorblackbelt/bin/hyperframes`, versão fixa e testada); sem ele, cai no
   `npx hyperframes@0.8.134`. Se faltar algo, mande o aluno ao **Editor Automático ›
   Ambiente › Preparar este computador** (é ele que instala). Não instale nada por
   conta própria.
2. Pergunte (uma mensagem só, curta):
   - onde está o **bruto** e em que pasta trabalhar;
   - se tem **roteiro** (texto do que ele ia falar) — melhora muito a decupagem;
   - se o Premiere está aberto com o **Tools PRO** e o **Conectar IA** ligado
     (fases 2–3). Sem Premiere, dá para pular direto da fase 1 para a 5 com um
     corte feito pelo ffmpeg (ver `references/sem-premiere.md`).
3. `python3 "$SK/scripts/sondar.py" BRUTO` e conte ao aluno o que é: vertical?
   HDR (HLG do iPhone)? 60 fps? duração? Isso decide a fase 3.

## Regras de segurança (não negociáveis)

- **Nunca altere o original.** O bruto e o corte exportado são só lidos: nada de
  sobrescrever, mover, renomear ou "converter no lugar". Toda saída vai para
  pastas novas (`decupagem/`, `Edicao premium/`).
- **Nunca escreva por cima do trabalho do aluno no Premiere**: sequência nova
  sempre com nome novo; o script recusa nome repetido. Leia de volta antes de
  repetir qualquer passo que deu timeout (a escrita pode ter acontecido).
- **Captura de tela só da JANELA** do app combinado (nunca a tela inteira — o
  aluno usa o computador junto). Prefira provar por leitura (ExtendScript, ffprobe,
  quadro exportado) a capturar a tela.
- **Sem dados pessoais** em nada que você gravar (legenda, nome de arquivo, log):
  e-mail, telefone, token, chave de API. O token do Tools PRO é lido na hora do
  arquivo do próprio painel do aluno e nunca copiado.
- Telas, gravações, música e fontes vêm **da pasta do aluno**. Música e SFX só
  com licença de uso; na dúvida, use `gerar_kit_sfx.py` (sintetizado, livre).

## Fase 1 — Decupar os takes

```
python3 "$SK/scripts/transcrever.py" BRUTO --saida decupagem/transcricao.json --termos "Marca, Produto, Premiere, ChatGPT"
python3 "$SK/scripts/decupar.py" --video BRUTO --transcricao decupagem/transcricao.json --roteiro roteiro.txt --saida decupagem/
python3 "$SK/scripts/previa_corte.py" --video BRUTO --plano decupagem/plano-corte.json --saida decupagem/previa-corte.mp4
```

- `transcrever.py` corta o áudio onde há voz (energia RMS a cada 10 ms) e passa o
  Whisper **medium** em cada trecho, com tempo por palavra. Nunca uma passada longa
  só: ela inventa palavra no silêncio e engole frase.
- `decupar.py` acha **todos os takes de cada frase** do roteiro, ajusta as bordas
  pela **energia da voz** (o tempo de palavra do Whisper desloca até 0,5 s),
  aplica o **corte suave** (0,40 s antes / 0,30 s depois, sem invadir a fala
  vizinha), **reconfere cada take transcrevendo só a janela dele** e grava
  `mapa-takes.md`, `takes.json` e `plano-corte.json`.
- O mapa marca o RECOMENDADO (fala completa, parecida com o roteiro, sem pausa
  longa, voz mais firme), os alertas (pausa no meio, incompleto, improviso,
  provável falso começo) e as **falas fora do roteiro** (improviso que pode valer).

**Checkpoint 1 — PERGUNTE:** mostre o mapa em poucas linhas (frase › takes ›
recomendado › alertas) e a prévia. Pergunte **qual take** em cada frase com
"empate técnico" e se as peças **opcionais** e os **improvisos** entram. O script
não ouve entonação nem final enrolado: o ouvido do aluno decide. Refaça com
`--escolha "2:3,5:6"` / `--sem "4"`. Se o aluno citar um falso começo, reconfira
a janela com `transcrever.py --ini X --fim Y` antes de afirmar.

## Fase 2 — Montar no Premiere pelo Tools PRO

Pré-requisito: painel Tools PRO aberto › **Conectar IA** › **Modo avançado
(ExtendScript)** ligado (sem isso o Premiere recusa scripts).

```
python3 "$SK/scripts/premiere/montar.py" diagnostico
python3 "$SK/scripts/premiere/montar.py" importar  --video BRUTO
python3 "$SK/scripts/premiere/montar.py" corte     --plano decupagem/plano-corte.json --nome "Meu Reels — corte v1"
python3 "$SK/scripts/premiere/montar.py" takes     --takes decupagem/takes.json --nome "Meu Reels — takes por frase"
python3 "$SK/scripts/premiere/montar.py" subclipes --takes decupagem/takes.json
python3 "$SK/scripts/premiere/montar.py" salvar
```

- Se você já tem a ferramenta `pr_extendscript` do Tools PRO carregada, use
  `--so-gerar` e passe o código a ela (argumento `codigo`); senão o script fala
  direto com o servidor local do painel.
- **corte v1**: as peças encostadas na V1/A1, cada clipe com o nome da fala e um
  marcador com o texto. **takes por frase**: todos os takes (0,25 s entre takes,
  1 s entre frases), marcador "Frase N · take X (RECOMENDADO) — texto" e os
  alertas no comentário. **subclipes**: um bin por frase em "TAKES POR FRASE".
- Por que assim: `createNewSequenceFromClips` herda vertical/fps/HDR e **não abre
  o diálogo "Nova sequência"** (que trava a ponte); posição sempre em ticks;
  `overwriteClip` (nunca insert); lotes de 10; tudo termina lendo de volta.

**Checkpoint 2:** a leitura de volta tem que bater: nº de clipes = nº de peças,
0 buracos, 0 sobreposições, duração ≈ a do plano (±1 quadro por emenda),
sequência vertical. Diga ao aluno onde está cada coisa no projeto.

## Fase 3 — Cor: HDR do iPhone → Rec.709

Só se `sondar.py` disse HDR (HLG/PQ). Sintoma que o aluno descreve: "ficou claro,
lavado, parede estourada".

```
python3 "$SK/scripts/premiere/montar.py" cor --sequencias "Meu Reels — corte v1,Meu Reels — takes por frase"
```

- Espaço de trabalho da sequência **Rec. 709** + **tone map automático** das
  mídias HDR (é isso que conserta o "lavado"; o Reels é SDR).
- Look por clipe (Lumetri, Correção básica): **Saturação 110, Contraste +10,
  Realces −20, Sombras −10, Brancos −10** (`--look padrao`). `--look nenhum` só
  converte; `--look "sat=105,contraste=5"` personaliza. A API não cria camada de
  ajuste: o efeito vai clipe a clipe e o valor gravado é conferido.
- Não mexa nas **Preferências** do Premiere (gerenciamento de cor da tela é do aluno).

**Checkpoint 3 — PERGUNTE:** peça ao aluno para olhar o Monitor de Programa
(pele, parede, preto) e dizer se aprova o look ou quer mais/menos.

## Fase 4 — O aluno ajusta e exporta o corte

O aluno revisa o corte (trocar take, apertar emenda) e **exporta ele mesmo**:
H.264, mesmo tamanho da sequência (vertical), Rec.709, áudio AAC 48 kHz, em uma
pasta `Render/`. Você não exporta por ele (é a aprovação dele do corte).
Confirme com `sondar.py` que o arquivo exportado está **SDR**, vertical, com áudio.

## Fase 5 — Edição premium no HyperFrames

```
python3 "$SK/scripts/premium/novo_projeto.py" --corte "Render/corte.mp4" --pasta "Edicao premium" --telas "minhas-telas/" [--musica trilha.mp3] [--marca marca.json]
python3 "$SK/scripts/transcrever.py" "Edicao premium/assets/audio/voz.wav" --saida "Edicao premium/transcricao.json" --termos "..."
python3 "$SK/scripts/revisar_transcricao.py" "Edicao premium/transcricao.json" --troca "errado=certo" ...
python3 "$SK/scripts/premium/rascunho_roteiro.py" "Edicao premium" [--cta "Link|na bio"]
python3 "$SK/scripts/premium/gerar_kit_sfx.py" "Edicao premium/assets/sfx"
python3 "$SK/scripts/premium/construir.py" "Edicao premium" --sfx-auto
```

1. **Transcrição revisada palavra a palavra** — é ela que vira legenda e âncora
   de tudo. Corrija marca, produto, nomes e gírias com `revisar_transcricao.py`
   (mantém os tempos). Interjeição ininteligível: `--inaudivel` (fica sem legenda).
2. **roteiro.json** (formato em `references/roteiro.md`; modelo em
   `templates/roteiro-exemplo.json`): o rascunho automático já renderiza; depois
   você e o aluno trocam o que importa:
   - **gancho**: a 1ª linha já na tela no **quadro 1** (`"em": 0`) + punch-in;
   - **hit** dourado na frase-chave (ex.: "ESTÁ NO AR.") com flash e brilho;
   - **telas**: carrossel de placas 3D com as telas/gravações REAIS do aluno,
     layout **dividido** (rosto sobe, painel de vidro embaixo);
   - **tela_unica**: uma gravação de tela numa placa inclinada com selo;
   - **aprovacao**: cartão com anel que enche e check que carimba na palavra;
   - **cta**: o rosto vira cartão no alto (**pip**), "Link na bio", site e
     palavra para comentar.
   Lettering: **1–4 palavras por linha**, aparece NA palavra falada.
3. **marca.json**: padrão = Editor Black Belt (escuro #08090b + dourado #f2b33d,
   Instrument Sans / Manrope / IBM Plex Mono). Para a marca do aluno, copie
   `templates/marca.json` para a pasta do projeto e troque cores e fontes.
4. `construir.py` gera tudo (cenas, câmera com ~1 punch-in a cada 1,5–3 s de
   102–116 % no envoltório do vídeo, painel, legendas com a palavra ativa em
   destaque na faixa y 1432–1528, SFX) e **para com erro** se uma âncora não
   existir, se 3 cenas se sobrepõem ou se algo sai da zona segura.

**Checkpoint 5 — PERGUNTE** antes do render final: **música ou não** (e qual —
com licença), **cores/fontes** da marca, **texto do CTA** (site, palavra para
comentar), e mostre um rascunho: `renderizar.sh ... --rascunho` + folha de quadros.

## Fase 6 — Mixagem, render e QC

```
bash "$SK/scripts/premium/renderizar.sh" "Edicao premium" --nome "Meu Reels" [--sem-musica]
```

- Mix: voz original intocada + SFX + música com **ducking** (sidechain) →
  **−14 LUFS, true peak ≤ −1 dBTP**. `mixar.py --sem-musica` faz a versão sem trilha.
- Render 1080×1920, 30 fps, ~22 Mbps; junta com a mixagem.
- `qc.py` roda sozinho: formato, loudness, **freezedetect** (trecho parado ≥ 0,25 s
  = "lapso"), preto, e a **folha com a zona segura** desenhada em vermelho.
  **Olhe a folha** e mais uma sequência de quadros na entrada de um lettering
  antes de mostrar: texto não pode "pular" nem cair no vermelho.

## Fase 7 — Velocidade e entrega

**PERGUNTE** se acelera (o real ficou 1,15x) e se quer as duas versões (com/sem música).

```
python3 "$SK/scripts/premium/acelerar.py" "Edicao premium/renders/Meu Reels - premium.mp4" --fator 1.15 --audio "Edicao premium/renders/mix.wav"
python3 "$SK/scripts/premium/qc.py" "Edicao premium/renders/Meu Reels - premium 1.15x.mp4"
```

A aceleração vem **depois** da composição (setpts + atempo juntos): legenda,
lettering e SFX continuam no tempo e a voz mantém o tom. Entregue: caminho dos
MP4, duração, LUFS/TP, e uma capa (quadro do hit) se o aluno pedir.

## Onde aprofundar

- `references/fases.md` — detalhes e números de cada fase (o porquê de cada valor).
- `references/roteiro.md` — formato completo do roteiro.json e dos visuais.
- `references/armadilhas.md` — o que já quebrou em job real e como evitar.
- `references/prompts-do-aluno.md` — o que o aluno pode pedir em cada fase.
- `references/sem-premiere.md` — caminho só com ffmpeg (sem Premiere/Tools PRO).
