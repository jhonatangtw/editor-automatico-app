# Estilo de edição — Upsell DR (referência: Upsell MarcaG)

Fonte: `original/Upsell_MarcaG_QA.mp4` (ferramenta de revisão, time Offers, 22/10/2026).
1080×1080 (1:1) · 23,976 fps · 6:58 · 75 cortes · 1.172 palavras (169 ppm) · −21,4 LUFS integrado
(baixo: entregar a −14) · trilha de fundo contínua (só 1 silêncio < −45 dB no vídeo todo).
Comentário na ferramenta de revisão: 1:31 "ABSOLUTEEEE" (time Offers), no fim do depoimento do Mark.

Tudo é IA: médico apresentador (avatar), 7 depoentes UGC (avatar selfie), b-roll em vídeo (não é still)
e mecanismo 3D. A edição é **calma e limpa**: nada de lettering gigante, X vermelho ou punch-in a cada
frase. Quem trabalha é a estrutura, a legenda e os cards da oferta.

## 1. Estrutura (o esqueleto que se repete)

| # | tempo | bloco | o que acontece na tela |
|---|---|---|---|
| 1 | 0:00–0:10 | **Interrupção** — "Before we ship your order…" | médico no consultório; 1 packshot do produto em "co-founder of MarcaG" |
| 2 | 0:10–0:46 | **Reafirma a decisão + future pacing** ("when names and faces…") | b-roll emocional a cada 1,2–5 s (família, neto, avó cozinhando), sem voltar pro médico |
| 3 | 0:46–1:15 | **A descoberta** ("some were having much faster restoration") | médico com punch-in alternado + b-roll ilustrando |
| 4 | 1:15–2:21 | **3 depoimentos** (Mark 71, Elaine 68, Robert 72), ~21 s cada | selfie UGC parada, sem b-roll, tarja de nome+idade nos 5–6 s iniciais |
| 5 | 2:21–3:12 | **Mecanismo novo** ("they tripled the dose") | mosaico 3×3 de depoentes → conta-gotas → split em 3 painéis café/almoço/jantar → anatomia 3D → metáfora do eletricista |
| 6 | 3:12–3:33 | **Depoimento-ponte** (Margaret 82) | selfie, tarja |
| 7 | 3:33–4:09 | **O problema** (vai acabar 3× mais rápido, estoque, fornecedor 5 meses, "can't rush plants") | médico + b-roll literal (estoque, armazém, navio, mudas, frasco caído) |
| 8 | 4:09–4:52 | **Solução de emergência + oferta** (pedido já está sendo embalado → frete coberto) | caixa sendo embalada, fábrica, linha de envase, kit → **card de preço** |
| 9 | 4:52–5:13 | **Garantia + CTA** | **card 100% money-back** sobre médico desfocado → **tarjas de contato** (telefone/e-mail) → **botão ADD & CONTINUE** em "click the button below" |
| 10 | 5:13–5:22 | **Como usar** (café, almoço, jantar) | b-roll literal |
| 11 | 5:22–6:53 | **3 depoimentos do protocolo** (Frank 64, Nancy 72, George 74), 21–35 s | selfie, tarja |
| 12 | 6:53–6:58 | **End card** | packshot do kit + "CLICK THE BUTTON BELOW / TO GET YOUR / TRIPLE-DOSE TREATMENT" + seta pra baixo |

Proporção: médico ~35 %, depoimentos ~45 %, b-roll/cards ~20 %. A prova social é o meio e o fim.

## 2. Ritmo
- **Médico:** plano médio fixo com punch-in no corte (alternando ~1,0 ↔ ~1,15, corte seco, sem zoom
  animado). Troca de enquadramento a cada 3–5 s quando não há b-roll.
- **B-roll:** vídeo de IA de 1,2–5 s (mediana ~2,7 s), sempre **literal à palavra falada** ("your keys" =
  chaves, "wallet" = carteira, "we can't rush plants" = mudas). Movimento é do próprio vídeo, sem Ken Burns.
- **Depoimentos:** plano único de 20–35 s, sem corte nem b-roll. Deixa respirar.
- Cortes secos em tudo. Sem transição, flash, whoosh ou glitch.

## 3. Legenda (sempre na tela, inclusive nos depoimentos)
- Montserrat **Bold**, ~48 px, branco, **caixa normal** (não caixa-alta), sem palavra ativa colorida.
- Pílula preta **~50 % de opacidade**, raio ~8 px, padding ~14×18 px, largura acompanha o texto.
- Centro horizontal; base da pílula em y ≈ **972** (margem inferior ~108 px). 1 linha por padrão,
  2 linhas quando a frase pede (entrelinha ~1,2); nunca 3.
- Blocos de 3–7 palavras, quebrando em vírgula/ponto. Troca seca (sem pop nem animação por palavra).
- Sobe pra cima do card quando o card ocupa a base (contato, preço).

## 4. Elementos gráficos (paleta da marca: verde `#17523E`, branco, dourado do selo)
- **Tarja de depoente:** encostada na borda esquerda, y ≈ 800–895. Barra verde `#17523E` com fio
  branco vertical à esquerda + nome em Montserrat SemiBold ~38 px branco; à direita, quadrado branco
  com "AGE" (pequeno, cinza, espaçado) e a idade em verde bold ~44 px. Entra com wipe da esquerda
  (~0,3 s) no 1º segundo do depoimento e sai em ~5–6 s.
- **Card de preço:** retângulo branco ~85 % de opacidade no canto inferior esquerdo, sobre o packshot do
  kit; "$" sobrescrito + número enorme verde black (~150 px) + "/month" verde bold. Entra no número falado.
- **Card de garantia:** médico desfocado e escurecido; "100%" branco ~130 px, "MONEY-BACK" ~70 px,
  "GUARANTEE" ~36 px espaçado (letter-spacing ~.3em). Fica a frase da garantia inteira.
- **Tarjas de contato:** duas, empilhadas à esquerda (y ≈ 655–850). Ícone branco num quadrado oliva/verde +
  telefone em branco bold ~56 px numa barra oliva; e-mail em verde/oliva sobre barra branca. Ficam de
  "call or email us" até "No questions asked".
- **Botão CTA:** pílula laranja em degradê (`#F26A1B`→`#E8531A`), "ADD & CONTINUE ›" branco ExtraBold
  ~34 px, no centro da tela (y ≈ 840) em "click the button below". Pulso leve.
- **Split de 3 painéis:** três verticais lado a lado, fio branco entre eles, ícone + rótulo pequeno
  espaçado (BREAKFAST / LUNCH / DINNER) na base de cada um.
- **Mosaico 3×3** de depoentes (efeito "videochamada") em "after hearing messages like this".
- **End card:** fundo claro desfocado, 3 frascos, título verde-escuro ExtraBold caixa-alta, subtítulo
  espaçado entre fios, pílula verde com o nome do tratamento, círculo com seta pra baixo.

## 5. Áudio
- Voz na frente, **trilha emocional contínua** baixa (piano/cordas) do início ao fim. Sem SFX.
- Referência saiu a −21,4 LUFS; a nossa entrega vai a −14 LUFS, com a trilha ~−18 dB abaixo da voz.

## 6. O que é diferente do ADVALIDADO-WEIGHTLOSS
| | weight loss (AD frio 9:16) | upsell (pós-compra, 1:1) |
|---|---|---|
| objetivo | parar o scroll | não deixar o comprador sair da página |
| energia | dopaminérgica: punch-in por frase, lettering, X, SFX | calma, autoridade e prova social |
| legenda | ≤3 palavras, caixa-alta, palavra ativa amarela | frase inteira, caixa normal, pílula translúcida |
| gráfico | lettering Anton | tarja de depoente, card de preço, garantia, contato, botão |
| apresentador | 1 avatar | médico + 6 a 8 depoentes UGC |
