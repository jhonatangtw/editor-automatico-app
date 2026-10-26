# Padrões de MICROLEAD — (5 vídeos medidos, 22/10/2026)

Legenda de evidência: **FATO** = medido (ffprobe, ebur128, scene-detect 0,28, Whisper large-v3-turbo, frames lidos). **HIPÓTESE** = leitura visual/inferência. Nenhum dado de venda por vídeo: nada aqui fala de desempenho.

Método: specs via ffprobe; loudness via ebur128 só na janela do ML; cortes via `select=gt(scene,0.28)` (subestima punch-in e troca entre planos parecidos); palavras/min e piso de pausa via timestamps por palavra do Whisper; 16 frames por vídeo + amostragem densa em 2 deles. Whisper usado só para estrutura (errou "Vicks and Honey" → "Vixen Honey").

---

## Fichas

### 1. MarcaB NNN_XX — ML1 [Squad Offer]
- Origem: `Drives compartilhados/ - Edição de Vídeo -Q3/Arquivo de Edição /08. Memory/MarcaB/OT/[051026][OT] NNN_XX [MarcaB] - ML [Squad]/5 Render/[051026][OT] NNN_XX [MarcaB] - ML1 [Squad Offer].mp4` (cópia: `MN_ML1.mp4`)
- Specs: 115,3 s · 720×1280 (9:16) · 30 fps · 9,1 Mb/s · **−28,5 LUFS** (TP −11,2) · LRA 3,8
- Formato: telejornal falso. 0–1 s vinheta "Anderson Cooper 360" → âncora (plano fixo) → "Dr. Oz" em escritório → âncora fecha.
- Hook 0–3 s: "Breaking news! The White House has called an emergency press conference." Promessa aos 9–13 s (reverter Alzheimer). Mecanismo aos 41 s (microplástico em volta dos neurônios). Prova: "matéria" com manchete "98%" (60 s), estudo de 2.000 voluntários, 99%. Vilão: Big Pharma (90 s). Ponte: "Up next, Elon Musk reveals… The full video starts now. Three, two, one." (108–115 s).
- Ritmo: 12 cortes = 6,2/min; plano mediano 4,8 s; plano mais longo 28,9 s (Dr. Oz falando).
- Legenda: sans pequena, branca, em caixa escura translúcida, centro-baixo, frase inteira (estilo closed caption de TV), sem palavra ativa.
- Visual: 2 "apresentadores"; inserts poucos (UGC de idosa mexendo Vicks no prato, 7 s; matéria fake com cérebro 3D, 60 s).
- Áudio: 176 palavras/min; piso das pausas −46,8 dBFS (quase seco, pouca ou nenhuma trilha).
- IA (HIPÓTESE): lip sync/deepfake sobre filmagem real de Anderson Cooper e Dr. Oz, com voz clonada; a matéria é um mockup de site com imagem gerada (cérebro com partículas).
- Defeitos: **loudness 8 LU abaixo dos outros** (−28,5); resolução 720p.

### 2. MarcaB NNN_XX — ML02 [Squad]
- Origem: `.../[051026][OT] NNN_XX [MarcaB] - ML [Squad]/5 Render/[051026][OT] NNN_XX [MarcaB] - ML02 [Squad].mp4` (`MN_ML02.mp4`)
- Specs: 141,2 s · **1920×1080 (16:9)** · 23,976 fps · −21,4 LUFS (TP −3,6) · LRA 6,6
- Formato: "60 Minutes" falso + morte de celebridade (Dolly Parton "R.I.P").
- Hook 0–3 s: **tela preta (~0–2,5 s)** → abertura com o cronômetro do 60 Minutes. A primeira fala é aos 8,8 s ("Dolly Parton risked everything… may have cost her life"). A apresentadora se apresenta como "Leslie Stahl" aos 20 s. Conspiração e Big Pharma de 22 a 45 s. O "vídeo deixado por ela" vai de 52 a 70 s. Prova: ressonância "antes/depois" (78–91 s) e depoimento de "paciente" (96–121 s). Ponte: "the censored presentation where Elon Musk reveals… The uncensored broadcast begins in 3, 2, 1." (130–141 s).
- Ritmo: 15 cortes = 6,4/min; plano mediano 5,0 s; maior 39,7 s (split celebridade + apresentadora com o título "ROSEMARY CONSPIRACY R.I.P").
- Legenda: igual à do ML1 (sans pequena em caixa escura, frase). Lettering em serifa clara no canto superior direito. Bug do logo "60 MINUTES" no canto superior esquerdo o tempo todo.
- Visual: velório com retrato P&B, táxi de NY, dinheiro caindo, cozinha, "paciente" em cozinha com potes de Vicks + mel. Proporção (HIPÓTESE por frame): ~70% imagem gerada.
- Áudio: 163 palavras/min; piso das pausas −23,4 dBFS → **trilha dramática alta** sob a voz (FATO: o piso está perto do RMS geral, −24).
- IA (HIPÓTESE): as cenas fotorreais têm cara de GPT Image/nano banana animadas em Kling (velas, cozinha, paciente); a apresentadora e a Dolly são deepfake/lip sync.
- Defeitos: 2,5 s de preto + 8,8 s sem fala na abertura (serve para emenda 16:9 na VSL, não para feed).

### 3. MarcaB NNN_XX — ML03 [Squad]
- Origem: `.../5 Render/[051026][OT] NNN_XX [MarcaB] - ML03 [Squad].mp4` (`MN_ML03.mp4`)
- Specs: 115,0 s · 1080×1920 (9:16) · 30 fps · 19,3 Mb/s · −19,9 LUFS (TP −5,5) · LRA 2,7
- Formato: celebridade falando em 1ª pessoa (Samuel L. Jackson com moletom #ENDALZ, jardim) segurando um cérebro e um pote de Vicks.
- Hook 0–3 s: "I bet you a million dollars that if you do this Vicks and Honey recipe…" com os 2 objetos-prova na mão desde o 1º quadro; aos 4 s ele empurra o Vicks para a câmera. Promessa: memória "mais afiada que há 20 anos" em 3 semanas. Garantia pessoal aos 23–33 s ("I'll never make another movie again"). "Give me 60 seconds" (39 s). Prova social de celebridade: Eastwood e Helen Mirren com o Vicks (35, 60, 70 s). Mecanismo: "microplastic parasite" (68–74 s). Ponte: "Team roll the video. 3, 2, 1." (108–115 s).
- Ritmo: 26 cortes = 13,6/min; plano mediano 4,0 s; maior 8,9 s. Punch-in alternado no apresentador (FATO visual: plano aberto aos 40 s e 50 s, fechado aos 45 s).
- Legenda: **nenhuma legenda queimada nos 32 frames amostrados** (dado amostral; não afirmo ausência total).
- Visual: inserts de 3–5 s: idosa no caderno de palavras cruzadas, cérebro 3D azul brilhante com partículas, frascos de remédio em luz dourada, idoso fazendo a mistura, idosos UGC.
- Áudio: 172 palavras/min; piso das pausas −33,5 dBFS (trilha baixa).
- IA (HIPÓTESE): o apresentador é avatar gerado (fundo de jardim sintético, objetos colados nas mãos), provável imagem→vídeo com lip sync (HeyGen/Kling); idosos e remédios em fotorreal no estilo GPT Image/nano banana; cérebro 3D gerado. O idoso de regata (20 s) parece orgânico.
- Defeitos: Whisper mostra frase repetida (39–54 s), possível take duplicado na VO (confirmar no áudio).

### 4. MarcaH (QA NNN_XX) — ML01
- Origem: `<arquivo local da referência>` (cópia da conferência de 06/10; encoder Lavf, cortada em 420,0 s; não achei o export original: `02. Weight Loss/MarcaH/{OT,DTC,Offer}` aparecem vazias no Drive local)
- Specs: 1080×1350 (**4:5**) · 30 fps · janela do ML 0–98 s: −20,6 LUFS (TP −2,9); a VSL depois dela fica em −20,8 LUFS
- **Estrutura medida: ML de 98 s emendado na VSL.** Em 98,0 s começa o corpo ("Why don't take Ozempic?"). Esse corpo é o mesmo nos 6 MLs da pasta (emendas em 98,0 · 98,1 · 97,9 · 132,8 · 116,9 · 76,0 s).
- Hook 0–3 s: "If you have matcha and ice at home and you're not melting at least four inches of belly fat, you're wasting your time" + corte aos 2,2 s para barriga real (UGC). Escassez aos 6–12 s ("last time… for free"). Receita em plano zenital das mãos (15–26 s). Objeções de idade, filhos e menopausa (29–40 s). Mecanismo e nome: "bariatric matcha" (50 s). Diferencial: sem efeito sanfona (54–64 s). Vilão: indústria farmacêutica (67 s). Autoridade: "Dr. Rhonda Patrick" (71 s). Ponte: "watch the next five minutes… Are you ready for this?" (88–98 s).
- Ritmo: 34 cortes = **20,8/min**; plano mediano **1,6 s**; maior 14,9 s. Punch-in no rosto (FATO: 10,5 s aberto, 12 s fechado).
- Legenda: **serifa branca com sombra**, 2–4 palavras, 1–2 linhas, ~70–80% da altura, sem palavra ativa colorida.
- Visual: apresentadora UGC na cozinha com copo verde e ingredientes no balcão; B-roll orgânico de corpos (barrigas, espelho), receita em top-down, antes/depois. Na VSL: entrevista com a "doutora", recorte do Harvard Gazette, esteira de GLP-1.
- Áudio: 166 palavras/min; piso das pausas −40 dBFS (trilha leve); só 1 pausa > 0,35 s em 98 s (fala colada).
- IA (HIPÓTESE): a apresentadora parece avatar/lip sync sobre influencer real; os B-rolls de corpo parecem orgânicos de TikTok; a "Dr. Rhonda Patrick" da VSL é pessoa real.

### 5. MarcaH (QA NNN_XX) — ML06
- Origem: `<arquivo local da referência>` (Lavf, 720×900, cortada em 300 s; é proxy da conferência, não o master)
- Specs: 4:5 · 30 fps · ML 0–76 s: −22,1 LUFS (TP −6,7)
- Hook 0–3 s: "Fuck it ladies, today I'm going to show you the real matcha recipe that works" (palavrão + mãe com bebê no colo, de frente para a câmera). Desafio aos 6 s ("Sue me if you want"). Lettering "THE REAL MATCHA RECIPE" sobre fundo desfocado aos 4 s. Resultado: −94 lb (16 s). Fonte: "Mel Robbins' podcast with Dr Rhonda Patrick that wasn't supposed to air" (26–36 s). Objeções (42–60 s). Ponte: "stay here with me because next I'm going to show you the special episode…" (64–76 s).
- Ritmo: 21 cortes = 16,6/min; plano mediano 3,2 s.
- Legenda: a mesma serifa branca do ML01 (é a identidade da VSL de destino). Corpo da VSL: lettering vermelho/branco grande ("THEY'RE NOT JUST temporary").
- Visual: mãe UGC, B-roll orgânico (moça com shaker, balança com chips), celebridade (Rebel Wilson) em foto (20 s), Mel Robbins (30 s).
- Áudio: 174 palavras/min; piso das pausas −36 dBFS.
- IA (HIPÓTESE): mãe com bebê = avatar gerado/lip sync (bebê imóvel, luz de estúdio).

---

## Padrões recorrentes

### Números (FATO, 5 MLs)
| | Duração do ML | Proporção | LUFS | Cortes/min | Plano mediano | Palavras/min |
|---|---|---|---|---|---|---|
| MN ML1 | 115 s | 9:16 | −28,5 | 6,2 | 4,8 s | 176 |
| MN ML02 | 141 s | 16:9 | −21,4 | 6,4 | 5,0 s | 163 |
| MN ML03 | 115 s | 9:16 | −19,9 | 13,6 | 4,0 s | 172 |
| BM ML01 | 98 s | 4:5 | −20,6 | 20,8 | 1,6 s | 166 |
| BM ML06 | 76 s | 4:5 | −22,1 | 16,6 | 3,2 s | 174 |
Duração dos 6 MLs MarcaH (pela emenda): 76–133 s, mediana ~98 s.

### EDITOR
1. **O ML é uma abertura emendada (modo A) em todos os 9 MLs com estrutura conferida.** Os 6 BM caem no mesmo corpo de VSL, e os 3 MN terminam em contagem que entrega o vídeo seguinte. Não há CTA de clique em nenhum deles: o CTA é "continue assistindo".
2. **Fecho padrão: ponte nomeando quem fala a seguir + promessa do que vai ser mostrado + "3, 2, 1".** A contagem aparece nos 3 MN e no BM ML04; nos outros BM, a ponte é verbal ("watch the next five minutes", "stay here with me").
3. **O formato, a legenda e a loudness seguem a VSL de destino, não o feed:** BM em 4:5 com legenda serifada igual à do corpo (ML −20,6 e corpo −20,8 LUFS); MN ML02 em 16:9 a 23,976 fps.
4. **O ritmo depende do registro:** UGC/receita = 17–21 cortes/min com plano de 1,6–3 s; telejornal/celebridade = 6–14/min com plano âncora de até 40 s. O corpo da VSL BM roda 18–22/min, então o ML mantém o ritmo do corpo.
5. **Arco medido:** hook com número ou aposta (0–5 s) → escassez ou confissão → mecanismo nomeado antes dos 75 s (bariatric matcha a 50 s; microplástico a 41, 68 e 70 s) → vilão Big Pharma → autoridade nomeada → ponte. Todos os 5 nomeiam o mecanismo antes da ponte.
6. Fala densa: 163–176 palavras/min, poucas pausas (1–15 > 0,35 s). A trilha fica sob a voz em 4 de 5 (piso das pausas de −23 a −40 dBFS); a exceção é o telejornal (−47).
7. Defeitos encontrados: 1 render a −28,5 LUFS; 2,5 s de preto + 8,8 s sem fala na abertura do ML02; possível frase duplicada no ML03.

### IA CREATOR
1. **O "apresentador" é o ativo central e quase sempre é (HIPÓTESE) avatar ou lip sync:** celebridade, médico ou âncora em 3 de 3 MN; influencer ou mãe UGC em 2 de 2 BM.
2. **Objetos-prova nas mãos do avatar desde o 1º quadro** (cérebro + Vicks; copo verde + matcha + vinagre no balcão; bebê no colo). A âncora do produto/mecanismo está na imagem antes de ser dita.
3. B-roll de memória (MN): idosos em fotorreal (palavras cruzadas, remédios, mistura na cozinha), cérebro 3D brilhante, "notícia" em mockup de site. B-roll de emagrecimento (BM): **orgânico de corpo real** (barriga, espelho) e mãos em top-down. Na leitura dos frames, o IA aparece mais no MN e o orgânico domina no BM (HIPÓTESE).
4. Mockups de "prova": manchete de site (MN ML1), recorte do Harvard Gazette (BM), ressonância antes/depois (MN ML02).

### O que diferencia o ML (nestes arquivos)
- **Contra o AD:** dura 76–141 s, o que é mais longo que um AD; termina em ponte/contagem para a VSL, não em "clique"; nomeia o mecanismo e a autoridade dentro da peça; herda o formato e a legenda da VSL.
- **Contra a VSL:** é só a abertura (o corpo é compartilhado: 6 aberturas BM → 1 corpo) e troca o ângulo/apresentador por variação (receita × mãe × celebridade × telejornal) com o mesmo mecanismo.
