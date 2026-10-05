# roteiro.json — o formato

Um arquivo na pasta do projeto premium. `construir.py` lê e gera tudo; **nunca
edite os .html gerados**. Modelo completo: `templates/roteiro-exemplo.json`.

## Tempo: número ou âncora na fala

- `5.6` → 5,6 s no vídeo.
- `"zero@1.6"` → início da palavra "zero" mais perto de 1,6 s (sem acento/pontuação na comparação).
- `"zero@1.6>"` → o FIM dessa palavra.

Âncora é melhor que número: se a transcrição for corrigida, o lettering continua
na palavra. Âncora que não existe = erro (o construir para e diz qual).

## Topo do arquivo

```json
{
 "duracao": null,                       // null = duração do vídeo
 "layout": [[0, "cheio"], ["editor@6.2", "dividido"], ["link@57.6", "pip"]],
 "punch_ins": "auto",                   // ou [[t, escala_ao_chegar, escala_no_proximo, snap_s], ...]
 "musica": {"arquivo": "assets/musica/x.mp3", "volume_db": -16},   // ou null
 "legenda": {"ligada": true, "ocultar": [[30.4, 31.1]]},
 "cenas": [ ... ]
}
```

Layouts: `cheio` (rosto em tela cheia), `dividido` (rosto sobe, painel de vidro
embaixo para telas/cartões), `pip` (o rosto vira um cartão no alto — fim/CTA).

## Cena

```json
{"id": "gancho", "ini": 0, "fim": 6.4, "beats": [ ... ], "visual": { ... }}
```

`fim` é opcional (padrão: início da próxima + 0,3 s de cruzamento). No máximo 2
cenas ao mesmo tempo.

### beats (lettering)

```json
{"kicker": "E o melhor",
 "linhas": [{"texto": "Você pede em", "em": "pede@19.6"},
            {"texto": "português", "em": "português@20.2", "destaque": true}],
 "ate": "português@20.2>"}
```

- 1–2 linhas por batida, **1–4 palavras por linha** (o construir avisa se passar).
- `destaque: true` = linha na cor de destaque (e punch-in forte + impacto).
- `"texto": "de *vocês.*"` = só a palavra entre * em destaque.
- `"partes": [{"texto": "E agora", "em": ...}, {"texto": "você", "em": ...}]` =
  pedaços da mesma linha entrando em tempos diferentes.
- `"em": 0` na primeira linha do vídeo = texto já no 1º quadro (gancho).
- `ate` opcional (padrão: logo antes da próxima batida).

### visual (um por cena, opcional)

| tipo | campos | uso |
|---|---|---|
| `hit` | `linhas` [2], `em`, `em2?` | frase-chave gigante em destaque, flash + brilho, riser + impacto |
| `telas` | `itens` [{`arquivo`, `rotulo` [app, nome]}], `passos` "auto" ou [tempos] | carrossel 3D das telas reais (layout dividido) |
| `tela_unica` | `arquivo`, `rotulo`, `ini?`, `fim?` | uma gravação/print numa placa inclinada (layout dividido) |
| `aprovacao` | `titulo` [2], `status` [antes, depois], `carimbo` | cartão com anel que enche e check na palavra |
| `cta` | `kicker`, `linhas` [2], `url`, `pilula`, `comentario`, `comentario_em` | cartão final com PiP (layout pip) |

`arquivo` é relativo à pasta do projeto (`assets/telas/...`), sempre material do
próprio aluno (print/gravação da janela do app dele). Vídeo vira `<video>` mudo
sincronizado com a cena.

## SFX

`construir.py --sfx-auto` gera `sfx-cues.json` a partir das batidas
(`[tempo, nome, volume, corte_s]`): whoosh na troca de batida, impacto na linha
em destaque, riser+impacto+brilho no hit, tick nos passos das telas, chime no
carimbo e no CTA, swell no fim. Depois dá para editar à mão (sem `--sfx-auto` o
construir respeita o arquivo). Nome = arquivo `assets/sfx/<nome>.mp3`.

## marca.json

Cores (`fundo`, `fundo2`, `texto`, `destaque`, `destaque_claro`,
`tinta_sobre_destaque`), fontes (`titulo`, `legenda`, `mono` com `familia`,
`arquivo`, `peso`), `lettering.maiusculas`, `legenda` (tamanho, máx. caracteres,
expressões que não quebram: "passo a passo"), `punch_in` (forte, leve, máximo).
