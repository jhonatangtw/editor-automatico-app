# Padrão de tamanho do produto (usuário, 31/10/2026)

**A régua é "parecer como a cabeceira aprovada".** Referência de ouro: `nr_cabeceira_r3` (NNN_XX, 7:40). usuário: "esse tamanho tá ok". Prancha visual: `regua_tamanho_produto.png`.

## 1. Referência de ouro (medida no quadro 1080×1920)
| Medida | Valor | Faixa (±10 %) |
|---|---|---|
| altura do pote ÷ altura do quadro | 28,5 % | 26–31 % |
| largura do pote ÷ largura do quadro | 24 % | 22–26 % |
| pote ÷ copo d'água ao lado | 1,29 | 1,16–1,42 |
| altura ÷ largura do pote | 2,1 | ≥ 1,8 (o real é 1,9; o GPT sai 2,1–2,6) |
| plano | aberto: criado-mudo, copo, óculos, abajur, cama ao fundo | o ambiente em volta é obrigatório |

Atenção: o build aplica push 1→1,08, então na tela o pote chega a ~31 %.

## 2. Medidas reais
- Pote de 300 ml (MarcaM): **13 × 6,9 cm**, razão 1,9.
- Conta-gotas 1 fl oz (MarcaG): 0,9× o pote = 11,7 cm com a tampa, ~3,5 cm de largura.
- Caixa de envio de 6 potes: ~30 × 20 × 15 cm.

## 3. Âncoras humanas (o gerador não consegue escalar)
- Rosto, do queixo ao topo da cabeça, 23 cm → pote ≈ **0,55** do rosto (0,50–0,61).
- Palma sem o polegar 8,5 cm → o pote é **mais estreito** que a palma.
- Indicador 7 cm → o pote tem **~2 indicadores** de altura.
- Mão inteira 18–19 cm → o pote tem **~0,7** da mão.

## 4. % da altura do quadro 9:16 por tipo de plano
| Plano | Pote (cada) | Base da faixa |
|---|---|---|
| Packshot sem pessoa (lua, fundo neutro) | livre | — |
| Mesa ou bancada aberta, 1–2 produtos | **26–31 %** | ouro (cabeceira 28,5 %; duo 28,5 %; caixa fecha 26 %) |
| Kit de 6 na bancada (padrão MarcaK) | 17–22 %, kit no terço do meio | kits 180 e CTA (20 e 18 %) |
| Pessoa da cintura para cima segurando | 12–15 % | rosto ~25 % do quadro × 0,55 |
| Mão com produto | a mão inteira e o pulso no quadro; pote ≤ 0,7 da mão e mais estreito que a palma | close de mão reprovado 2× (mão v1–v6, tg/tf) |
| Estoque e prateleira | 7–14 % | estoque sd 13 % |

## 5. Proporções dentro da cena (só valem com o objeto em escala humana)
- Pote ÷ copo ou caneca: 1,16–1,42 (ouro 1,29). Não vale se a IA aumentou a caneca: conferir pelo % do quadro.
- Pote ÷ caixa de depósito: 0,30–0,35.
- Pote ÷ caixa de envio: ≈ 0,85 da altura; os potes ocupam no máximo 60 % da área interna, com kraft visível.
- Entre potes da mesma cena: ±3 %.

## 6. Bloco de prompt padrão (colar e ajustar o ambiente)
```
Real-world scale, person and environment first, the product SMALL in the frame. Open medium-wide shot of <environment> with the surroundings visible around the product. The product is a small 300 ml supplement bottle, 13 cm tall and 6.9 cm wide (height about 1.9 times its width) — narrower than an adult palm, about the length of two fingers, about half the height of an adult face. In the 9:16 frame the bottle takes up only about <N>% of the image height. Use the attached photos ONLY to copy the label design, NOT the size of the bottle in the pictures. <LABEL LOCK>
```
`<N>` vem da tabela da seção 4 (ex.: 28 para mesa aberta, 13 para pessoa da cintura para cima).

## 7. QC
1. Medir em px no quadro do meio (grade `grade.py`): altura do pote ÷ altura do quadro, comparada com a faixa do plano.
2. Com pessoa: pote ÷ rosto 0,50–0,61 e pote mais estreito que a palma.
3. Altura ÷ largura do pote ≥ 1,8.
4. **Nunca** aprovar só pela razão contra uma caneca ou caixa geradas pela IA (o caso da caneca gigante de 31/10).
5. Antes de animar, montar a folha lado a lado com o quadro de ouro em primeiro lugar.

## 8. Plano de fuga (o GPT insiste em ampliar)
Gerar a cena **sem** o produto (mão em posição de segurar, ou bancada com espaço livre) e colar o PNG oficial em escala:
`altura_px = (13 / tamanho_real_da_âncora_cm) × altura_da_âncora_em_px`
(ex.: rosto de 400 px → 13/23 × 400 = 226 px). Casar sombra de contato, direção da luz, temperatura e oclusão dos dedos (máscara da mão por cima do PNG). Sem colagem solta: a mão tem que envolver o pote.

## 9. Forma aprovada pelo usuário (31/10) e ajuste "diminui um pouco"
- **Forma = frasco da cabeceira:** H/L 2,0–2,1 (medido 2,07), tampa com anel 12–14 % da altura (medido 13 %), ombro largo e arredondado, rótulo do ombro até ~3 % antes da base. Rejeitar frasco alto e fino (H/L > 2,15) ou tampa flip alta.
- Asset pronto: `ia/mockups/nr_forma_ouro.png` (PNG oficial com a tampa comprimida a 72 %: H/L 2,02, tampa 12,8 %).
- **Tamanho −15 % (usuário 31/10):** mesa/bancada alvo **24 %** da altura (22–26 %); kit de 6 15–19 % por pote; estoque 6–12 %; meio-corpo 10–13 %; pote ÷ caneca 1,1–1,2.
- Receita que funcionou: placa limpa pelo GPT ("remove all bottles, keep everything else") + frasco colado por código (`scratchpad/scr/troca.py` copiado em templates se reaproveitar). A passada de "realismo" do GPT sobre a colagem REESCREVE o texto do rótulo: não usar. O Kling também corrompe o rótulo pequeno: produto pequeno em plano aberto = still + push no HyperFrames.
- Vídeo de ouro grande demais: reduzir 0,84 sobre fundo estendido por outpaint, com máscara só no miolo (borda reta mostra emenda).

## 10. Régua MarcaE para frasco de cápsula (usuário 31/10) + régua de conta-gotas
Pedido do usuário (31/10, V4 MarcaD NNN_XX): **frasco de CÁPSULAS mede como o frasco do MarcaE; frasco de GOTAS segue o conta-gotas já validado (MarcaG NNN_XX).** Folha: `<pasta de trabalho>/_SAMURAI/MarcaD-up2-NNNxx/v4/prancha/folha_tamanho_MarcaE_x_MarcaM.png`.

**Medidas do MarcaE** (Upsell #1 Preço A, 1440×1080; altura e largura do frasco em % do quadro):
| plano | tempo | altura | largura | H/L |
|---|---|---|---|---|
| close de mesa (mão + caneca + suco) | 3:02 | 52 % | 20 % | 1,92 |
| 3 frascos na bancada | 4:22 | 57 % | 24 % | 1,80 |
| meio plano com pessoa (café da manhã) | 6:09 | 33 % | 14 % | 1,81 |
| packshot em 1º plano (casal ao fundo) | 6:13 | 62 % | 25,5 % | 1,83 |
Tampa 18–20 % da altura e ~80 % da largura do corpo. Frasco ≈ 1,4 × caneca na mesma profundidade.

**Como transpor para 9:16 (1080×1920): pela LARGURA do frasco** (o MarcaE é 4:3; a altura em % não se transfere):
- close de mesa / produto sozinho: largura 20–24 % → MarcaM ≈ 380–440 px de altura (20–23 %);
- bancada com 2–3 frascos: 18–22 % → 340–400 px;
- par MarcaD + MarcaM, 3 pares lado a lado: NR ≈ 300 px;
- kit de 6 em dois trios lado a lado: ≤ 15 % → NR ≈ 290 px;
- estoque / prateleira: NR ≈ 250 px; meio plano com pessoa: 13–14 % → ≈ 270 px; packshot 1º plano: ≈ 500 px.
Escala SEMPRE checada contra a âncora da cena (mão, caneca ≈ 1,1–1,4×, caixa ≈ 0,85 da altura) — a régua dá a faixa, a cena dá o número.

**Forma do MarcaM:** a forma ouro aprovada (`nr_forma_ouro.png` do NNN_XX, H/L 2,02, tampa ≈ 13 %; real 13 × 6,9 cm). Reprovar b-roll de IA com frasco fino/alto (H/L > 2,15). Na V4 o PNG colado por código é `assets/img/nr_ouro.png` (cópia da forma ouro); kits `nr_kit3_ab.png` e `nr_kit6.png` refeitos a partir dele (mesma altura por frasco).
**Frasco de gotas (MarcaD, MarcaG):** régua de conta-gotas 1 fl oz = **0,9 × a altura do MarcaM na mesma cena** (11,7 cm com tampa, ~3,5 cm de largura, H/L ≈ 3,2–3,3).
**Componente que aplica isso:** `MarcaD-up2-NNNxx/.../edicao/v4_produto.py` (cena real vazia vz_* do NNN_XX + frasco oficial colado: `frasco("nr"|"cf", x, base, alt, t=…)`, alturas NR_MESA 380 · NR_PAR 300 · NR_KIT 290 · NR_ESTOQUE 250; CF = 0,9 × NR).

## Vídeo 4:3 (1440×1080): a régua é o MarcaE NNN_XX (usuário, 03/11)
As % acima são de quadro 9:16 e NÃO valem em 4:3. Medido a olho nos quadros do "V2 Preço A" (`MarcaD-up2-NNNxx/referencias_padrao/MarcaE_4x3_frascos_e_legenda.jpg`):
- Mesa aberta, 1 frasco com prato e copo (188 s): frasco ~25% da altura do quadro, cerca de 1,2× o copo ao lado. Assim que o frasco aparece na maior parte do tempo.
- Close com a mão aberta e a cápsula (182 s): frasco ~50% da altura, com a mão, a caneca e o copo no quadro. É plano pontual.
Sempre um frasco só, em pé, rótulo de frente, numa mesa real.
