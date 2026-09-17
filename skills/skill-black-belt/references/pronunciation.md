# Pronúncia fonética

Os modelos de fala (Veo/Kling/Seedance) erram termos incomuns, nomes de marca e siglas. Reescreva-os FONETICAMENTE **na própria fala** (dentro das aspas), não só na descrição — é da fala que o áudio é gerado. O vídeo sai com o som correto mesmo com a grafia "errada".

## Lista fixa (aplicar sempre)
| Original | Escrever como |
|---|---|
| silymarin | Silimerin |
| NAC | N-A-C |
| choline | Koh-leen |
| ashwagandha | ash-wa-gan-da |
| milk thistle | Milk Tissel |
| A1C | A-one-C |
| I'll | I will |

## Mantidos na grafia normal (os modelos costumam acertar)
Só foneticize se a geração sair errada; nesse caso use o fallback.
| Termo | Fallback fonético (só se errar) |
|---|---|
| metformin | met-for-min |
| berberine | ber-ber-een |
| Ozempic | (normal) |
| glutathione | gloo-ta-thigh-own |
| Ritual Labs | (normal) |
| cysteine | sis-teen |

## Números → por extenso
| Original | Escrever como |
|---|---|
| 74% | seventy-four percent |
| 80% | eighty percent |
| 60% | sixty percent |
| 500 | five hundred |
| 1960s | nine-teen six-tees |
| 10k | ten thousand |
| 2 to 3 weeks | two to three weeks |
| week 5 | week five |
| the 90s | the nineties |
| high 5s, low 6s | high fives, low sixes |
| around 7 | around seven |
| 3 capsules | three capsules |
| 60 to 90 days | sixty to ninety days |

## Nomes de marca (anti-fusão)
Nomes próprios no início da fala costumam fundir/gaguejar. Para `Happy Liver by Ritual Labs`:
- separar com pausa/respiro antes,
- manter "Happy Liver" claramente separado de "by Ritual Labs",
- nunca deixar a marca como primeira sílaba absoluta do clipe (usar o buffer de silêncio antes).
Se fundir mesmo assim ("Happyriliver"), reordenar para tirar a marca do ataque: "...the one I'd look into is Happy Liver, by Ritual Labs."

## Regra geral
Sempre que aparecer um termo novo de difícil pronúncia (substância, nome científico, sigla, marca), adicione aqui e aplique a versão fonética. Na dúvida, soletre siglas (X-Y-Z) e separe sílabas com hífen.
