# Formato podcast + split + legenda em caixa (medido no AD04, 10/09/2026)

Segunda gramática da skill, para ad de resposta direta com avatar em podcast. Medida numa
referência pronta de 111 s (720x1280, 30 fps) — os números são o contrato.

## Hook em tela dividida
| | |
| --- | --- |
| costura | **y = 0,49 H** (942 px em 1920), faixa branca 6 px a 55 % |
| topo | take do entrevistador a **1:1 cortado no topo** (720→1080 = 150 %, posição (540, 960) num precomp de 1080x942) |
| base | B-roll "antes" → corte seco para "depois" **na palavra do produto** ("simple matcha"), push 100→104 % no hold |
| troca de falante | o "Yes, it's true" entra no topo com corte seco + pop; a base continua |
| duração | o hook inteiro (pergunta + resposta) antes do body em tela cheia |

## Legenda em caixa
| | |
| --- | --- |
| caixa | verde `#23500D` (0.137, 0.314, 0.051), altura **103 px**, raio 36, padding lateral 44 |
| fonte | **Nunito ExtraBold 60 px** branco — 'a' de dois andares e terminais macios; Poppins foi descartada por medição |
| blocos | 1–2 palavras, ≤ 13 caracteres, ≤ 0,6 s; **1,7–2,3 blocos/s**; nunca atravessa corte de segmento |
| posição | hook: centro em **0,459 H** (logo acima da costura) · body: **0,638 H** |
| entrada | pop 88 → 106 → 100 % em 4 quadros (do Pinterest: a palavra chega no beat) |
| acento | ≤ 8 blocos com número/promessa em amarelo `#F4D35E` a 112 %; 3 blocos-chave **invertidos** (caixa amarela, texto verde) |
| centro pela tinta | `sourceRectAtTime` e não a métrica da fonte — senão o texto escorrega na caixa |

## Body
- **Cartão**: 680x880 no centro-alto (540, 700), raio 40, borda branca 8 px, sombra 20/50/45 %;
  entra com **blur 40→0 + escala 94→100 + opacidade em 6 quadros**, Ken Burns 100→105 no hold,
  sai em 5 quadros. Cartões vizinhos cortam seco entre si (sem re-blur).
- **Prova grande** ("3,000 patients"): cutaway tela cheia, zoom-in 108→100 em 5 quadros.
- **Split no body** (comentário "tela dividida acima a Dra abaixo…"): precomp com o take
  deslocado (`startTime = BODY_START − t0`), matte sólido 1080x942 no topo e 1080x978 na base.
- **Antes/depois**: dois cartões 470x740 em x = 290 e 790, o "depois" entra 0,9 s depois.
- **Punch-in** 100→107 % em 3 quadros + **2 quadros de tremor** (±7 px) nas palavras de impacto.
- **Objeto na palavra** (Pinterest): cutout pop 0→118→100 % com rotação −14→−4°, ao lado do rosto,
  sai antes da próxima cena.
- **CTA sem texto novo**: chevron branco pulsando no rodapé (y 1560) em cada "tap the button".
- **SFX**: swish −14 dB só onde entra elemento; pop −10 dB na troca de falante e no reveal. ~12 no vídeo.

## Decupagem
- Takes em pasta `lip/` são **segmentos** (hook do entrevistador, hooks do avatar, body) — não alternativas.
- B-roll com **número no quadro** tem que bater com a copy: "3,000" aceito; "1.308/3.500/200" reprovados.
- O arquivo com prefixo **"usar esse -"** é instrução do editor — obedecer.

## Camada dopaminérgica (Pinterest 15551561209923797) — medida e aplicada no AD04 v3

Entra **por cima** de qualquer gramática, numa comp separada (`*_DOPA`, duplicata da MAIN) para a
versão limpa sobreviver.

| Elemento | Como | Números |
| --- | --- | --- |
| **Cena de lettering** | fundo 2D creme `#F3EFE6` ou preto `#0A0A0B` alternados, texto **3D** (`threeDLayer`) em profundidades diferentes, vinheta 18 (creme) / 40 (preto), linha-caminho cinza `#CCC7BA` 22 px desenhando por trim path só no creme | 1,0–3,4 s por cena, 6–8 por vídeo, só em número/promessa/CTA |
| **Palavra** | Montserrat ExtraBold; corpo 90–110 (apoio, tinta `#121214` ou branco) / 150–260 (chave, vermelho `#E0212A`); pop 0→112→100 % em 5 f com rotação 2×→1×; no preto, o vermelho leva `ADBE Glo2` (60 / 40 / 0,35) | um pop por palavra falada, **no tempo da palavra** |
| **Câmera 3D** | `addCamera` de um nó (`NO_AUTO_ORIENT`); por cena, 2 chaves de posição (dolly −140 a −260 em Z + deriva de 40–80 px) cercadas por **hold** no valor padrão — fora da cena a câmera fica parada | texto chave em z = −140…−200, apoio em z = +20…+80 → parallax |
| **Objeto na palavra** | render 3D limpo (Nano Banana Pro, fundo `#8A8A8A`, "no digits/numerals"), recorte por `recortar_gradiente.py`, camada 3D pop 0→115→100 % em 7 f com rotação −18→0 | balança em "pounds", relógio em "days"/"seconds", copo em "Matcha." |
| **Zoom por frase** | escala do talking head em **hold** alternando 100/106 a cada início de frase (palavra depois de `. ? !`) — jump cut sem cortar o take | 22–25 trocas num body de 2 min |
| **Som** | `CARTOON_POP` −13 dB em cada palavra de lettering; `Fast_Swish` −12 dB na entrada de cada cena | ~35 SFX |
| **Legenda** | **cala** sob toda cena de lettering (opacidade em hold na camada `PC_LEGENDAS`) — inclusive no hook | armadilha 37 da motion-vox |

**Só palavras da copy.** "3 days" seria mais forte que "three days", mas não está escrito assim — fica "three days".

**Emoji não entra pelo AE.** `AppleColorEmoji` é aceito como fonte, mas renderiza **contorno preto
monocromático** (sbix não suportado); "Apple Color Emoji" com espaço é recusado (caractere 32). Se
precisar de emoji, é PNG — e neste formato de podcast ele quebra o realismo, então objeto 3D no lugar.

## Gramática EDITORIAL (Pinterest 1142999580450072622 — "motivation / discipline") — DOPA-2 do AD04

| Elemento | Como | Números |
| --- | --- | --- |
| **Papel + luz de janela** | sólido creme `#EDE9E1`; shape com 5 retângulos 2600x230 espaçados 560, preto 14 %, rotação 35°, blur 70, derivando ~90 px na cena; vinheta 16; ruído 3 | cena preta `#0B0B0D` para contraste, vinheta 38 |
| **Palavra-fantasma** | a chave da cena em **Anton** caixa alta 560 px, 6–7 %, camada 3D em z = +420 (fica atrás no parallax), escala 92→100 % na cena | "POUNDS", "DAYS", "SECONDS", "PAID", "FREE" |
| **Tipografia** | lead-in **Fraunces Regular** 62–74 px (fade 6 f); chave **Montserrat Bold** 124–210 px, tracking −10, **reveal letra a letra com blur** | animador de texto: Opacity 0 + Blur 34, seletor por caracteres (`Range Type2 = 1`), Start 0→100 em 0,42 s |
| **Ornamentos** | ✦✦✦ (estrela de 4 pontas por path, 3 grupos), linha vertical 300 px + estrela (**duas camadas**, ver abaixo), círculo de contorno 2 px desenhando por trim | tudo carvão `#2A2A2E` no creme, branco no preto |
| **Objeto** | render limpo (balança, relógio, copo) **cortado no canto**, camada 3D em z = −60, entra deslizando 140 px em 10 f | sombra 26/60/45 % a 120° |
| **Transições** | corte seco; **flash branco** (sólido 0→100→0 em 7 f) na saída de uma cena; **anel desfocado** (elipse stroke 90, blur 45, escala 20→620 % em 12 f) na entrada de outra — um de cada por vídeo | |
| **Câmera 3D** | dolly −120 a −220 em Z com deriva de 30–60 px, hold fora da cena | ghost atrás, texto no meio, objeto na frente |

**Legenda premium** (`PC_LEGENDAS_PREMIUM`, duplicata restilizada da caixa verde): pílula preta 42 % (52 % no acento) 96 px de altura, **Montserrat Bold 58** branco tracking −8 com sombra 4/12/70 %; acento em **Playfair Display Bold Italic 70 dourado `#E7C36A`** com Glo2 (55/36/0,5). A versão limpa (`AD04_MAIN`) continua com a caixa verde.

**Armadilha nova (ExtendScript):** numa shape layer, **adicionar um segundo grupo depois de já ter
adicionado stroke ao primeiro invalida a referência** — o `fill()` no grupo novo dá "O objeto é
inválido". `estrelas()` (3 grupos só com fill) passa; `pino()` (grupo com stroke + grupo com fill)
quebra. Saída: um grupo por camada e parentear.

## Fundo sob cartão — blur + escurecimento animados (pedido do Jhon, 10/09/2026)

Sempre que imagem/B-roll entra **sobre** a locutora (cartão, antes/depois, objeto solto), o talking head
atrás recebe desfoque e escurecimento; o cartão fica nítido e iluminado.

| | |
| --- | --- |
| como | **um par de camadas por comp**, logo acima do `PC_00_TALKING_HEAD` e abaixo de todo cartão: `TH_blur` (adjustment com `ADBE Gaussian Blur 2`, repeat edge) + `TH_escurece` (sólido preto, opacidade) |
| valores | blur **22 px**, preto **40 %**, rampa **8 quadros** com ease nas duas pontas |
| janelas | calculadas dos in/out **reais** das camadas `CARD_*`/`OBJ_*` do comp; intervalos com gap < 0,3 s viram **uma janela só** (três cartões seguidos = uma subida e uma descida, nada empilha) |
| fora da janela | as duas propriedades voltam a 0 — nenhum efeito sobra sem imagem na tela |
| não se aplica | cutaway tela cheia, split e cena de lettering (cobrem a locutora inteira) |

Armadilha: cartão cujo precomp tem folga (0,5 s a mais que a janela) fica com `outPoint` além do
momento em que ele já sumiu por opacidade — a janela do fundo seguiria o `outPoint` e o desfoque
sobreviveria à imagem. Aparar o `outPoint` do cartão no fim visual antes de calcular as janelas.
Prova: frame 3 f depois do início (rampa subindo), meio da janela (blur pleno), 4 f depois do fim
(nítido, sem véu).

## Reenquadrar o locutor no quadro superior do split (pedido do Jhon, 10/09/2026)

Meta: rosto no centro horizontal, olhos perto do terço superior da metade (942 px), sem cortar
cabeça, fones, queixo ou ombros; quadro inferior intacto.

1. **Medir, não estimar**: YuNet (`corte-viral/models/face_detection_yunet_2023mar.onnx`) em 3–5
   quadros do take dá centro do rosto, linha dos olhos e altura; uma **régua** desenhada por PIL
   dá o topo dos fones/cabelo (Rogan y≈200, Rhonda y≈95 no 720×1280).
2. **Escala ≥ 150 %** sempre (720→1080 sem barra). Só sobe de 150 quando precisa de folga
   horizontal para centrar: Rogan a 156 % ganha ±22 px.
3. **Vertical**: `Py = margem_topo − (y_topo − 640)·s`, com margem de 100 px (UI do Reels). O
   terço exato (0,33) **não é alcançável** sem cortar os fones — com a margem, os olhos ficam em
   0,41–0,48 da metade. Dizer isso no relatório em vez de cortar.
4. **Chaves**: se a camada tem punch-ins (escala com keyframes), `setValue` recusa — apagar as
   chaves e recriar os punches sobre a base nova.
5. **Legenda do hook**: fica entre o queixo e a costura — aqui 858 px (box 806–910): ~130 px abaixo
   do queixo, 32 px acima da linha. Mover as duas versões (`PC_LEGENDAS` e `_PREMIUM`).
6. **Provar no quadro final**: rodar o YuNet de novo nos PNG de 1080×1920 e reportar x/540, olhos
   como fração da metade, topo e queixo.
