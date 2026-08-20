# Formato do `edicao.json`

Entrada do `scripts/montar.py`. Este é o exemplo real do AD01 da LeafTide (aprovado).

```json
{
  "body": "VIDEO DO BODY.mp4",
  "duracao": 133.6,
  "largura": 1080,
  "altura": 1920,
  "saida": "AD01_FINAL_9x16.mp4",
  "legenda": "AD01_LEGENDAS.mov",

  "punch": [
    [0,      16.08, 1.00],
    [16.08,  23.0,  1.12],
    [23.0,   45.36, 1.00],
    [45.36,  51.2,  1.16],
    [51.2,   82.16, 1.00],
    [82.16,  88.2,  1.10],
    [88.2,  127.4,  1.00],
    [127.4, 133.6,  1.14]
  ],

  "inserts": [
    {"arquivo": "BROLL/B1_guardaroupa.mp4", "inicio": 8.52,   "fim": 14.16},
    {"arquivo": "BROLL/B2_dosando.mp4",     "inicio": 23.52,  "fim": 28.52},
    {"arquivo": "BROLL/B3_receita.mp4",     "inicio": 64.32,  "fim": 72.32},
    {"arquivo": "BROLL/B4_espelho.mp4",     "inicio": 118.32, "fim": 121.96}
  ],

  "flash": null,
  "sfx": null
}
```

## Campos

| Campo | Regra |
|---|---|
| `punch` | Precisa cobrir `0..duracao` **sem buraco e sem sobreposição**. Escala `1.00` = sem punch. O script valida e aborta se não fechar. |
| `inserts` | `inicio`/`fim` em segundos na timeline. O clipe é escalado para preencher o frame e cortado no centro. |
| `legenda` | `.mov` com alpha gerado pelo `legendas.py`. Sempre composta **por último**, para não estourar junto com o flash. |
| `overlays` | Lista de `.mov` com alpha compostos **depois** da legenda — lettering, marca d'água. Ordem importa. |
| `flash` | `null` por padrão. **Corte seco é o padrão aprovado.** |
| `sfx` | `null` por padrão. |

## Lettering animado

`lettering.json` (entrada do `lettering.py`):

```json
[
  {"texto": "22 POUNDS\nIN 12 DAYS", "inicio": 5.90,  "fim": 8.10},
  {"texto": "100% NATURAL",          "inicio": 70.30, "fim": 72.30},
  {"texto": "NO GYM\nNO STARVING",   "inicio": 73.50, "fim": 76.40}
]
```

E no `edicao.json`: `"overlays": ["AD01_LETTERING.mov"]`.

**Sempre mutar a legenda nas mesmas janelas**, senão o texto aparece duplicado na tela:
```bash
python3 legendas.py --srt X.srt --overlay Y.mov --dur D \
        --mute "5.90-8.10" --mute "70.30-72.30" --mute "73.50-76.40"
```

Escolher 2–3 falas, não mais — lettering demais vira videoclipe e rouba a legenda. Os que se pagam: o número da promessa, o mecanismo, e a remoção de objeção ("sem academia, sem passar fome").

## Escolhendo as escalas de punch

Entre 110% e 116%, **variando** entre as janelas. Todas iguais vira tique visível.

Colocar nos beats de virada emocional onde **não** há B-roll cobrindo — punch atrás de insert é desperdício.

## Se o usuário pedir flash e SFX

```json
"flash": {
  "arquivo": "ASSETS/_Flash Transitions 3.mp4",
  "in": 0.20, "out": 0.62, "lead": 0.12
},
"sfx": {
  "arquivo": "ASSETS/clean-fast-swooshaiff-14784.mp3",
  "lead": 0.30, "volume": 0.60
}
```

- `in`/`out`: a **janela útil** do clipe de flash. Medir antes — as pontas costumam ser preto puro:
  ```bash
  ffmpeg -v error -i flash.mp4 -vf scale=64:36 fr%03d.png
  python3 -c "from PIL import Image,ImageStat;import glob
  [print(i/25, ImageStat.Stat(Image.open(f).convert('L')).mean[0]) for i,f in enumerate(sorted(glob.glob('fr*.png')))]"
  ```
- `lead` do flash: distância do início da janela até o **pico**, para o pico cair no frame do corte.
- `lead` do sfx: onde está o **impacto** do whoosh (medir RMS por janela de 50ms).
- `volume` 0.60 dá ~+3,5 dB no corte — audível sem cobrir a voz. 0.30 é baixo demais.
