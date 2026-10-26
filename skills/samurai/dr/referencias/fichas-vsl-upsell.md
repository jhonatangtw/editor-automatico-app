# Padrões de edição e produção com IA — VSLs e upsells finalizados

Levantamento de 22/10/2026. Só leitura no Drive: os arquivos foram copiados para esta pasta antes de qualquer medição.
Escopo (ajustado a pedido do usuário): **estilo e modelo de edição** — specs, blocos, ritmo, legenda, lettering, B-roll, motion, áudio e o que parece gerado por IA. Compliance ficou fora.

Legenda: **FATO** = medido (ffprobe, ebur128, detecção de cena, transcrição, quadro visto). **HIPÓTESE** = leitura visual que não dá para provar pelo arquivo.

## Método

- Specs: `ffprobe`. Loudness: `ebur128` (integrado, LRA, true peak).
- Cortes: `select='gt(scene,0.25)'` em proxy de 180–320 px, com cortes a menos de 0,3 s de distância juntados.
  **Limitação:** a detecção conta menos do que existe quando há fusão (dissolve) ou desfoque de transição. Por isso o número de cortes do UP3 é um piso.
- Tempo de apresentador: comparação das faixas laterais de cada quadro (2 fps) com um quadro de referência do apresentador. É aproximado, porque punch-in e fundo desfocado contam como "não apresentador".
- Trilha: nível RMS por janela de 100 ms, olhando o percentil baixo (piso entre as frases) e as pausas abaixo de −40 dB.
- Estrutura: faster-whisper small no arquivo inteiro, usada **só para os blocos e os tempos aproximados**. Nenhuma frase foi dada como ausente com base nela.
- Frames vistos: UP1 44 · UP2 30 · UP3 36 · MarcaB 48 · MarcaF 38.

---

## Ficha 1 — Família de upsells ProdutoI (St. Anthony), 3 vídeos

Origem: `Arquivo de Edição /26. Biz Opp/ProdutoI/Offer/[051026][OF] Funil Upsell Prosperidade [ProdutoI] - Info [Squad Offer]/5. Render/`
(Upsell 1 e Upsell 2 são masters copiados do Drive. O Upsell 3 é o proxy da ferramenta de revisão que já estava em `<arquivo local da referência>`, com a mesma duração do master.)

| | UP1 "Turbo Prayer" | UP2 "Divine Shield" | UP3 "Divine Compass" |
|---|---|---|---|
| Duração | 5:51,9 | 3:58,5 | 5:34,8 |
| Resolução / proporção / fps | 1280×720 · 16:9 · 29,97 | idem | idem |
| Loudness integrado | **−24,3 LUFS** | **−24,5 LUFS** | **−24,9 LUFS** |
| LRA / true peak | 2,9 LU / −2,3 dBTP | 3,2 / −1,5 | 3,2 / −2,0 |
| Cortes/min (geral) | 14,7 | 16,6 | 5,4 (piso, há fusões) |
| Plano mediano | 3,2 s | 2,9 s | 7,3 s |
| Tela do apresentador (aprox.) | ~30% | ~18% | ~44% |
| Preço / posição do pitch | $67 em 4:20 (74%) | $47 em 3:06 (78%) | $47 em 4:28 (80%) |
| Garantia | 180 dias, 4:34 | 180 dias, 3:13 | 180 dias, 4:33 |

### Mapa de blocos (tempos aproximados, pela transcrição)

UP1: 0–48 parabéns e "não feche a página" · 48–153 problema (os 10 erros) · 153–216 produto e mecanismo (ciclo manhã/noite) · 216–238 entrega e bônus · 238–274 âncora ($297) e preço $67 · 274–305 garantia · 305–352 escassez ("só nesta página") e CTA "click the button below" repetido 2×.
UP2: 0–18 abertura · 18–40 inimigo/problema · 40–102 produto e benefícios · 102–151 agitação · 151–170 entrega · 170–193 preço ($197 → $97 → $47) · 193–207 garantia · 207–239 escassez e CTA.
UP3: 0–32 agradecimento · 32–93 história ("dois tipos de fiel") · 93–157 revelação · 157–230 produto e entrega · 230–252 future pacing ("imagine…") · 252–273 preço · 273–298 garantia · 298–335 escassez e CTA.

**Esqueleto comum (FATO):** abertura de continuidade de compra → problema → produto com nome próprio → entregáveis → âncora de preço → preço → garantia de 180 dias → "oferta só nesta página" → CTA → bênção de saída. O preço sempre cai entre 74% e 80% da duração.

### Ritmo por bloco (cortes/min)
- UP1: 13,8 na abertura · 16,6–17,1 no problema e no produto · 16,7 no preço · **9,7 na garantia e 8,9 no CTA**.
- UP2: 16,4–18,4 no corpo · pico de **25,3 na lista de entregáveis** · **8,6 na garantia** · 15,0 no CTA.
- UP3: 5,6–6,6 em quase tudo · 0 no future pacing (plano de 22 s) · 1,6 no CTA (plano de 18 s).
→ **FATO:** nos três, o ritmo cai na garantia. Ela fica no apresentador ou num selo, com menos cortes.

### Visual (FATO, pelos quadros)
- Apresentador: religioso em plano médio fixo, de frente, olhando para a câmera. Cenário diferente em cada upsell: UP1 interno com estátua dourada, UP2 externo com jardim e tijolo, UP3 parede de tijolo.
- B-roll cobre a maior parte da tela (56–82% nos três). Há dois tipos de B-roll:
  - **UP1 e UP2:** banco de imagem clássico (mão no mouse, aperto de mãos, homem na cama, cinto de segurança, relógio, calendário), mais elementos de motion (partículas, fogo, ondas sonoras, raio de luz).
  - **UP3:** imagens estilizadas de cena única (peões de xadrez luminosos, mãos de vidro, manuscrito com anjos, Jesus em contraluz, cruz com selo).
- **Mesmos clipes de B-roll entre UP1 e UP2:** calendário 3D, homem sorrindo na cama, cinto de segurança, fogo, homem com a mão na cabeça, selo de 180 dias.
- Legenda: pílula branca com texto escuro, **palavra ativa preta e o resto cinza (karaokê)**, uma linha, no rodapé.
  - UP1 e UP2: Montserrat Bold em minúsculas.
  - UP3: CAIXA ALTA, exceto **uma legenda em minúsculas aos 4:30** ("your one time contribution will be only $47") — quebra do padrão (defeito).
- Lettering grande, poucas vezes:
  - UP1: "ONLY $67" em verde-limão com contorno, 2× (4:25 e 5:35).
  - UP3: nome do produto em serifa dourada/branca ("DIVINE COMPASS OF SAINT ANTHONY", "COMPLETE MANUSCRIPT").
  - Selo dourado "180 DAYS 100% MONEY BACK" sobre o apresentador ou o B-roll (UP1, UP2, UP3).
- Transições: fade a preto com partículas (UP1 4:49,6, 0,7 s de preto **intencional**, áudio corre por cima), desfoque do apresentador (UP3 1:43), cortes secos.
- Sem mockup de produto: é infoproduto. O "produto" vira lettering com o nome e B-roll simbólico.

### Áudio (FATO)
- Voz em inglês americano, compressão leve (LRA 2,9–3,2 LU).
- UP1 e UP2: **nenhuma pausa abaixo de −40 dB** (piso de −50 a −48 dB). Há uma cama contínua, compatível com trilha baixa.
- UP3: 74 pausas abaixo de −40 dB. Piso de −55 dB, tonal (planura espectral 0,13) e com 68% da energia abaixo de 300 Hz. É compatível com pad grave quase inaudível (**HIPÓTESE**).
- **Os três estão em −24 a −25 LUFS, 10 dB abaixo de MarcaB e MarcaF (−16/−17).**

### IA (HIPÓTESE)
- O apresentador de UP1 e UP2 é o mesmo rosto de bispo, mas **o solidéu roxo aparece e some entre planos do mesmo vídeo** (UP2: tem aos 0:01 e 3:07, não tem aos 0:50 e 2:30). Isso indica clipes gerados separadamente, avatar ou lip sync, e não gravação contínua.
- O UP3 usa outro rosto (padre de clergyman), embora a narrativa do funil seja do mesmo "Father Michael Ashford" do UP1. A troca de apresentador dentro do mesmo funil é **FATO**. Que seja avatar é **HIPÓTESE**.
- O B-roll do UP3 tem cara de geração por imagem (luz volumétrica, objetos de vidro, composição central limpa). O de UP1 e UP2 parece banco de imagem.

### Defeitos técnicos
- Loudness de −24 a −25 LUFS nos três: fica baixo para web e para a página de vendas.
- UP3: uma legenda em minúsculas no meio de um padrão em caixa alta (4:30).
- UP1/UP2: continuidade de figurino do apresentador (o solidéu).

---

## Ficha 2 — VSL MarcaB, Lead 1 (DR, 9:16)

Origem: `Arquivo de Edição /08. Memory/MarcaB/Offer/[250826][OF] 83_PG [MarcaB] - Otimização Urgente [Time de Criação]/Render MarcaB/[250826][OF] 83_PG [MarcaB - Lead 1].mp4` (1,96 GB, cópia de 7 min).

- **Specs (FATO):** 28:33 · 1080×1920 · **9:16** · 30 fps · −16,4 LUFS · LRA 6,1 LU · **true peak +0,4 dBTP (clipa)**.
- **Ritmo geral:** 11,6 cortes/min, plano mediano 3,6 s (p10 1,1 s · p90 10,7 s · máximo 55,6 s).
- **Apresentador na tela (aprox.):** 23% no 1º terço, 50% no 2º, 42% no 3º. Entra só por volta de 9:20, depois da abertura de notícia.

### Mapa de blocos (aprox.) e ritmo

| Bloco | Tempo | Cortes/min | Plano |
|---|---|---|---|
| Lead em formato de telejornal (âncora + tarja de manchete fixa, "executive order") | 0:00–1:25 | 13,4 | 4,2 s |
| História e prova inicial (família, entrevista em biblioteca, depoimento) | 1:25–5:00 | **5,6** | 10,2 s |
| MUP — o problema ("silent attack", microplástico no cérebro) | 5:00–8:40 | 13,9 | 4,2 s |
| Origem secreta + MUS + ingredientes | 8:40–12:10 | 12,6 | 4,7 s |
| Benefícios / future pacing | 12:10–14:10 | 12,5 | 4,6 s |
| História / depoimento longo | 14:10–16:40 | **5,2** | 10,7 s |
| Agitação (consequências) | 16:40–18:04 | 12,1 | 4,7 s |
| Oferta: programa, como funciona (chat no celular), "included free" | 18:04–20:50 | 12,3 | 4,7 s |
| Bundle e preço ("só paga os 3 últimos frascos"), escassez "100 por dia" | 20:50–23:20 | 11,2 | 5,2 s |
| Depoimento de cliente | 23:20–24:14 | 10,0 | 5,4 s |
| Fechamento (duas escolhas, recapitulação, CTA "take the evaluation") | 24:14–28:33 | **16,2** | 3,6 s |

O pitch começa em ~18:04 (63%) e o bundle aparece por volta de 20:50 (73%).
**FATO:** nos blocos de história e depoimento, o ritmo cai para ~5 cortes/min; nos de argumento, volta para 12–14; o fechamento é o trecho mais rápido.

### Visual (FATO)
- **Abertura de telejornal:** apresentador de estúdio, tarja vermelha "MEMORY LOSS" + manchete em serifa condensada + logo de canal, mantida por ~3–4 min sobre todo o B-roll. Também há rótulos de local no canto ("WHITE HOUSE", "HARVARD") e tela de site governamental em perspectiva.
- **Apresentador principal:** homem de terno em mesa, de frente, mãos cruzadas, fundo escuro com quadro. Alterna plano médio e **punch-in fechado no rosto** (por exemplo, 20:50 fechado e 28:20 aberto).
- **Legenda:** Montserrat SemiBold branca, sentence case, em **caixa escura translúcida**, 1–2 linhas, centralizada na faixa de 55–70% da altura. Frase curta, sem karaokê de cor.
- **Lettering:** Montserrat ExtraBold em **amarelo neon com glow**, empilhado, por cima do apresentador **desfocado e escurecido** ("THIRD / YOUR MarcaB, DELIVERED DIRECTLY TO…"). Também há pílula de contorno luminoso ("NO / COFFEE") e texto branco 3D com glow e linha-guia ("WHILE, DEEP INSIDE,"). Bate com a spec de `padrao-visual-MarcaB`.
- **Motion/explicativo:** cérebro vermelho com estilhaços, neurônios azuis luminosos, ressonância e angiografia, conta-gotas de laboratório, chat de celular simulado ("Hey, I have a question" + digitando).
- **Produto:** frasco conta-gotas azul-cobalto "MarcaB" na mão de cliente sorrindo (selfie em casa, 22:35).
- **B-roll de pessoas:** idosos em casa, família, casal no sofá, jantar. É fotorreal, com luz quente e cara de cinema; em 14:10 há preto e branco para o passado.

### Áudio (FATO)
- Nenhuma pausa abaixo de −40 dB em 28 min. O piso fica em −39 dB (p2), o que indica **cama de trilha contínua e alta** sob a voz.
- LRA de 6,1 LU, o dobro dos upsells: a trilha sobe nos respiros e nas viradas.

### IA (HIPÓTESE)
- O B-roll de pessoas (idosos, família, depoimentos em poltrona com bandeira) tem a assinatura de GPT Image/Kling: pele limpa, luz de janela perfeita, composição central.
- Os depoimentos de cliente falando para a câmera ("I'll be honest with you, I cried") são compatíveis com avatar com lip sync (HeyGen/Kling).
- O apresentador principal em plano fixo com variações de escala é compatível com avatar ou lip sync sobre um plano-âncora.
- O cliente segurando o frasco pede o rótulo exato, coerente com a regra de usar referência do produto no GPT Image (ver memória `MarcaB-produto-mockups`).

### Defeitos técnicos
- **True peak de +0,4 dBTP:** clipa.
- A tarja de telejornal fica ~3–4 min fixa por cima de B-roll que não é estúdio (laboratório, site, entrevista).

---

## Ficha 3 — VSL MarcaF (DR, 9:16)

Origem: `<arquivo local da referência>` (export local de 12/10, 5,18 GB; não foi preciso copiar do Drive).
Escolhida no lugar da MarcaD V10 (2,58 GB no Drive) por já estar local.

- **Specs (FATO):** 1:04:28 · 1080×1920 · **9:16** · 30 fps · −17,2 LUFS · LRA 3,9 LU · true peak −2,9 dBTP.
- **Ritmo geral:** **17,3 cortes/min**, plano mediano 2,4 s (p10 0,6 s · p90 7,1 s · máximo 47 s). É o mais rápido dos analisados.

### Mapa de blocos (aprox.) e ritmo

| Bloco | Tempo | Cortes/min | Plano |
|---|---|---|---|
| Hook (receita caseira + promessa) | 0:00–1:00 | **28,0** | 2,1 s |
| Resto do lead (inimigo, credenciais do narrador) | 1:00–6:10 | 19,2 | 3,1 s |
| História (LA, cliente famoso, relato da esposa) | 6:10–16:30 | 17,8 | 3,4 s |
| MUP — a causa (veneno na comida) | 16:30–21:40 | 19,9 | 3,0 s |
| MUP — o mecanismo ("cimento" na esponja) + por que remédio e cirurgia falham | 21:40–31:10 | 18,2 | 3,3 s |
| MUS: cavalos, veterinário, 4 passos, ingredientes, estudos | 31:10–41:40 | **20,9** | 2,9 s |
| Prova: teste com Kevin, 37 homens, desenvolvimento | 41:40–51:00 | 14,0 | 4,2 s |
| Depoimentos | 51:00–54:20 | **8,1** | 7,1 s |
| Oferta: estoque, âncora, **preço em 56:29 (87,6%)**, kits 1/2/3, bônus, garantia | 54:20–1:00:00 | 13,9 | 4,2 s |
| Fechamento (duas escolhas, recapitulação) | 1:00:00–1:04:28 | 15,7 | 3,8 s |

**FATO:** de novo o ritmo cai nos depoimentos (8/min) e sobe no mecanismo. O hook tem o dobro da média do resto.

### Visual (FATO)
- **Hook em tela dividida:** metade de cima com B-roll e lettering, metade de baixo com o apresentador. Depois vira tela cheia.
- **Apresentador:** homem careca de camisa escura, sentado em poltrona num escritório com estante, de frente, em plano americano. Ao longo da VSL entram planos mais fechados (55:00+).
- **Legenda:** branca, sans bold, sentence case, **caixa escura translúcida arredondada**, 1 linha, frase de 2–5 palavras, a ~60% da altura. Depoimento usa **amarelo itálico**.
- **Lettering:** três famílias convivem:
  1. condensada tipo Impact, branca + vermelha ("THE DAMAGE IS ALREADY DONE", "BLUE PILL");
  2. Montserrat ExtraBold amarela com contorno/glow ("A SPOONFUL OF BAKING SODA", "LOGIC / MECHANICS / IDENTITY");
  3. **preço em verde neon gigante com glow** sobre fundo desfocado ("$79", "$33 per bottle").
- **Motion/explicativo:** tecido 3D (vasos vermelhos com placas), estômago verde translúcido, tela "ACCESS BLOCKED" com ícone 3D.
- **Produto:** mockups do frasco MarcaF em cenários variados (mesa de madeira com 3 frascos, tronco com musgo na floresta, bancada de mármore), mais presente com laço para os bônus.
- **B-roll:** mistura de banco de imagem, recorte de TV/entrevista, UGC de celular e material adulto explícito. O mix de fontes é intenso.

### Áudio (FATO)
- Só 2 pausas abaixo de −40 dB em 64 min. O piso fica em −39 dB (p2): **cama de trilha contínua**, como na MarcaB.
- −17,2 LUFS e LRA de 3,9 LU: voz bem comprimida.

### IA (HIPÓTESE)
- O apresentador principal tem pele e luz uniformes e o mesmo enquadramento em 64 min. É compatível com avatar (HeyGen) a partir de foto gerada.
- A mulher de robe no quarto de hotel (4:00) e a "esposa" na cozinha (45:00) têm cara de personagem gerado com lip sync.
- **Mockups do frasco em cenários diferentes** (floresta, mármore, madeira) são compatíveis com GPT Image/Nano Banana com referência do rótulo.
- O tecido 3D, o estômago verde e o ícone 3D parecem gerados (imagem estática animada, sem paralaxe de câmera real).

### Defeitos técnicos
- Não houve defeito mensurável de áudio (true peak −2,9).
- Três famílias tipográficas de lettering ao mesmo tempo: a hierarquia muda de um bloco para outro.

---

## Padrões recorrentes

### Para o EDITOR DE VÍDEO

1. **Formato por função (FATO).** As VSLs longas de DR (MarcaB e MarcaF) saem em **9:16, 1080×1920, 30 fps**. Os upsells (ProdutoI) saem em **16:9, 1280×720, 29,97**.
2. **Ritmo-base (FATO).** Upsell 15–17 cortes/min (plano mediano ~3 s); VSL longa 12–17 cortes/min (plano mediano 2,4–3,6 s). O UP3, com fusões e planos de 8 s, é o ponto fora da curva.
3. **Curva de ritmo por bloco (FATO, nos 5 vídeos).**
   - Hook acima da média (MarcaF 28/min no 1º minuto).
   - Mecanismo e argumento na média ou acima (12–21/min).
   - **História e depoimento caem para 5–8/min**, com planos de 7–11 s.
   - **Garantia cai** (8,6–9,7/min nos upsells).
   - Fechamento volta a acelerar (MarcaB 16,2/min, o bloco mais rápido do vídeo).
4. **Pitch e preço.** Upsell: preço em 74–80% da duração, garantia de 180 dias logo depois, "só nesta página" + CTA no fim. VSL longa: oferta em 63% (MarcaB) a 84% (MarcaF), preço em 73–88%.
5. **Legenda (FATO).** Sempre presente, uma frase curta por vez, em caixa (pílula ou caixa translúcida) na faixa de 55–70% da altura no 9:16 e no rodapé no 16:9. Upsell: pílula branca com karaokê preto/cinza. VSL: caixa escura translúcida com texto branco.
   Erro a evitar: misturar caixa alta e minúsculas dentro do mesmo vídeo (UP3 4:30).
6. **Lettering só nos momentos-chave (FATO).** Preço, nome do produto, a palavra que vira o argumento. Receita que se repete:
   - **fundo = apresentador ou produto desfocado e escurecido + palavra em neon** (amarelo MarcaB, verde MarcaF);
   - preço em **verde neon gigante** nas duas peças que mostram valor (UP1 "ONLY $67", MarcaF "$79/$33");
   - selo dourado de 180 dias na garantia.
7. **Cobertura (FATO).** O apresentador fica na tela só 18–50% do tempo. O resto é B-roll, motion ou lettering. O apresentador "volta" para os pontos de confiança: preço, garantia, CTA final.
8. **Áudio.**
   - FATO: as VSLs longas (−16/−17 LUFS) têm cama de trilha contínua; os upsells estão em −24/−25 LUFS.
   - Recomendação: **padronizar em −16 LUFS / −1 dBTP**. A MarcaB clipou (+0,4 dBTP) e os upsells ficaram 8–9 dB abaixo.
9. **Continuidade.** Conferir figurino e rosto do apresentador entre planos e entre vídeos do mesmo funil: o solidéu entra e sai no UP1/UP2, e o UP3 troca o rosto.
   Reuso de B-roll entre upsells do mesmo funil aconteceu (6 clipes iguais entre UP1 e UP2). Se for evitar repetição, a regra precisa valer no funil todo, não só por vídeo.

### Para o IA CREATOR (o que a casa já produz por IA — HIPÓTESE visual, sem metadado)

1. **Apresentador fixo de frente, plano médio, cenário de autoridade** (escritório com estante, mesa de terno, igreja ou jardim) em todos os 5. É compatível com avatar e lip sync a partir de um retrato-âncora.
   Para a edição, entregar **2 escalas** (médio e fechado), porque a montagem alterna punch-in (MarcaB).
2. **Âncora de identidade travada.** Gerar todos os planos do apresentador do mesmo retrato e com o mesmo figurino. Nos upsells, gerações separadas mudaram o figurino (solidéu).
3. **Personagens de depoimento** (idosa na poltrona com bandeira, cliente com frasco, esposa na cozinha): retrato fotorreal + lip sync. O cliente aparece **segurando o frasco com o rótulo legível**, o que pede referência do produto na geração.
4. **Mockups de produto em 3–4 cenários** (mesa de madeira, mármore, natureza) para a sequência de preço e bundle (MarcaF). Para os bônus, objeto simbólico (presente com laço).
5. **Explicativo 3D do mecanismo:** órgão ou tecido estilizado (cérebro com estilhaços, neurônios luminosos, vasos com placa, estômago translúcido). Esse é o B-roll do bloco de MUP/MUS, que é o bloco mais rápido. Pedir **várias variações por conceito**: com 18–21 cortes/min, um clipe único se repete.
6. **B-roll emocional fotorreal com luz quente** (família, casal, idosos) para história e benefícios. Para o "antes/passado", a montagem usou preto e branco.
7. **Formato de "notícia/UI" como B-roll:** tarja de telejornal, tela de site, chat de celular, "ACCESS BLOCKED". É produzido como gráfico ou mockup de tela, não como foto.
8. **No upsell espiritual (UP3), o estilo é ilustração fotorreal simbólica** (luz volumétrica, vidro, manuscrito, contraluz) e precisa sair na proporção do vídeo (16:9).
