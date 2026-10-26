# Padrões de edição e de produção com IA — 4 ADs finalizados

Escopo: só estilo e modelo de edição (ritmo, estrutura, legenda, lettering, B-roll, motion, áudio, personagem e visual gerado, specs). Não há análise de compliance aqui, por pedido do usuário.
Não há dado de desempenho: nada nos arquivos diz se esses ADs venderam. Isto descreve **como foram feitos**, não **o que funciona**.

Método: cópia local (tamanho conferido com `stat`), ffprobe, ebur128 (loudness e true peak), corte de cena por `select=gt(scene,X)` em 0.3 e 0.12 (corte duplicado em menos de 0,25 s conta uma vez), faster-whisper medium com timestamp por palavra, quadros a 1 fps em folha de contato e mosaicos lidos um a um. Nível de áudio nas pausas da fala medido com volumedetect, para inferir trilha.
Legenda: **FATO** = medido ou visto no quadro. **HIPÓTESE** = inferência visual ou de áudio.

Raiz: `<pasta do Drive da equipe>` (com espaço no fim)

---

## V1 — MarcaA (Weight Loss), AD01 H1
Origem: `{raiz}/02. Weight Loss/MarcaA/OT/[100926][OT] NNN_XX [MarcaA] [Squad B]/EXPORT/AD01/[100926][OT] NNN_XX [MarcaA] AD01 H1 [Squad B].mp4`

- **Specs (FATO):** 73,7 s · 1080x1920 · 23,976 fps · H.264 9,7 Mb/s · AAC 48 kHz estéreo · **−31,3 LUFS** · true peak −13,6 dBFS · LRA 2,3.
- **Estrutura (FATO):**
  - 0–4,7 s: **hook em split.** Moldura amarela com manchete fixa no topo ("THIS MATCHA RITUAL HELPS YOU LOSE UP TO 70 POUNDS IN 3 WEEKS", com o branco, o amarelo e o verde-limão em destaque). A avatar aparece ao fundo e um inset com borda branca mostra a dor, trocando 3 vezes ("this… this too… and this too").
  - 4,7–14,5 s: agitação em B-roll orgânico de tela cheia (chocolate, geladeira, mulher sem energia no carro).
  - 14,7 s: a avatar volta com a promessa.
  - 21,9–24 s: **pack-shot em motion** do pote, com tipografia cinética "MarcaA" em fundo verde, entrada por flash verde e saída por light leak quente.
  - 26–38 s: mecanismo (ingredientes) e demonstração com mãos misturando o pó.
  - 50–54 s: B-roll de reforço da dor (sofá).
  - 58–67 s: prova social em números.
  - 67,6 s: CTA falado ("If the link is showing up for you…"). O **botão "LEARN MORE"** em pílula aparece por volta de 66–67 s e pisca entre amarelo, branco e cinza até o fim.
- **Ritmo (FATO):** 12 cortes (limiar 0.3), ou 9,8/min com plano médio de 5,7 s; 33 cortes (limiar 0.12), ou 27/min com plano médio de 2,2 s. A avatar alterna escala entre planos (punch-in visível nos quadros). Fala a 185 palavras/min, com só 3 pausas acima de 0,4 s.
- **Legenda (FATO):** 2 a 3 palavras por vez, em caixa normal, sans bold branca (tipo Montserrat) sobre caixa escura semitransparente, **no centro da tela (~50% da altura)**. Não há palavra ativa colorida.
- **Visual:** apresentadora fixa numa cozinha de estúdio, com o pote, um copo d'água, gengibre e canela numa tábua, idênticos em todos os planos (FATO). HIPÓTESE: avatar gerada (HeyGen ou parecido) a partir de um start frame com o produto já composto. O plano das mãos usa a mesma camisa (consistência mantida). O B-roll de dor tem cara de footage orgânico de TikTok ou UGC; o sofá parece IA fotorreal (HIPÓTESE). B-roll em tela cheia ocupa ~23% do tempo, mais ~7% no inset do hook.
- **Áudio:** pausas da fala entre −32 e −38 dB, ou seja, há algo sob a voz (HIPÓTESE: trilha baixa). Voz americana feminina; TTS ou clonada é HIPÓTESE.
- **Defeitos (FATO):** loudness muito baixo (−31 LUFS, a 17 LU do alvo de −14). Fora isso, nenhum quadro preto (blackdetect zerado).

## V2 — MarcaD (Heart), AD01 H1
Origem: `{raiz}/23. Heart/MarcaD/OT/[050826][OT] 23_JV [MarcaD] [Squad A]/04. Render/AD01/23_JV [MarcaD] AD01 H1.mp4`

- **Specs (FATO):** 230,8 s · 1080x1920 · 30 fps · H.264 6,2 Mb/s · AAC **44,1 kHz** · **−28,4 LUFS** · true peak −9,1 · LRA 4,5.
- **Estrutura (FATO):**
  - 0–9 s: **hook em split horizontal.** No terço de cima, B-roll de frascos de remédio com manchete em caixa vermelha e letra branca ("THE BIG PHARMA CHARADE HAS BEEN EXPOSED"); embaixo, o convidado de podcast.
  - Body em **formato de entrevista de podcast** (estúdio com cortina vermelha, microfone e fone). O entrevistador entra em contraplano com falas curtas de reação ("Hold on…", "That's insane", "Your dad is over 90 now, right?").
  - História do pai, depois mecanismo, depois resultado, depois CTA.
  - CTA **só falado**: em 198 s ("put the link… in the button right below") e em 225 s ("Tap the button now and watch"). **Não há botão gráfico.**
- **Ritmo (FATO):** 19 cortes (0.3), ou 4,9/min com plano médio de 11,5 s; 43 cortes (0.12), ou 11/min com plano médio de 5,3 s. O ritmo vem de **punch-in e alternância de enquadramento no mesmo take** (aberto e fechado), visíveis na folha de contato, e não de B-roll. Fala a 199 palavras/min, a mais rápida das quatro.
- **Legenda (FATO):** 2 a 3 palavras, caixa normal, branca bold com caixa escura, a ~59% da altura. Sem destaque de palavra.
- **Visual:** o convidado ocupa ~76% do tempo. Inserts:
  - B-roll fotorreal (braço com medidor de pressão, frascos sobre a mesa com abajur, coração 3D brilhante);
  - split de duas webcams com tarja amarela de nome;
  - split com filtro laranja de uma cena de pai e filho diante de um laptop.
  HIPÓTESE: o diálogo inteiro (convidado e entrevistador) foi gerado com lip sync sobre um set de podcast, e o B-roll é imagem de IA animada (Kling ou parecido). B-roll e inserts somam ~24%.
- **Áudio:** pausas entre −27 e −50 dB; pode haver trilha muito baixa ou só ambiente (HIPÓTESE). Duas vozes masculinas americanas.
- **Defeitos (FATO):** loudness baixo (−28,4 LUFS); 44,1 kHz destoa dos outros (48 kHz). Arquivo sem o padrão de nome de entregável (`23_JV [MarcaD] AD01 H1.mp4`).

## V3 — MarcaB (Memory), AD01 H1 (AD para advertorial)
Origem: `{raiz}/08. Memory/MarcaB/OT/[300826][OT] NNN_XX [MarcaB] - AD's para Advertorial [Squad]/EXPORT/AD01/[300826][OT] NNN_XX [MarcaB] - AD's para Advertorial AD01 H1 [Squad B].mp4`

- **Specs (FATO):** 98,0 s · 1080x1920 · 30 fps · H.264 **2,3 Mb/s** (o mais leve) · AAC 48 kHz · −23,2 LUFS · true peak −5,9 · **LRA 8,8** (o mais irregular).
- **Estrutura (FATO):**
  - 0–14,7 s: **hook com faixa vermelha fixa no topo** ("IGNORING THIS COULD COST YOU / YOUR MEMORY AND YOUR INDEPENDENCE", em branco e amarelo). Tem um B-roll P&B de asilo (4–6 s). Entre 11 e 15 s aparecem **botões de vidro** com o contraste "GETTING YOUR INDEPENDENCE BACK" (verde) e "OR LOSING YOUR MEMORY FOREVER" (vermelho).
  - 14,9 s: começa o body, um depoimento em primeira pessoa (veterano de 80 anos), seguido de virada ("met a 95-year-old man"), mecanismo, truque do mel, resultado e CTA.
  - CTA: falado a partir de 83,7 s ("leaving a link below to the article"), com **"CLICK BELOW" em caixa de contorno amarelo e seta** entre ~84 e 87 s, e fecho de urgência em 94,4 s.
- **Ritmo (FATO):** 13 cortes (0.3), ou 8/min com plano médio de 7 s; 33 (0.12), ou 20/min com plano médio de 2,9 s. Fala a 186 palavras/min.
- **Legenda (FATO):** 1 a 3 palavras, caixa normal, branca bold **pequena** com caixa escura, a ~66% da altura.
- **Lettering (FATO):** frase forte em tela cheia sobre fundo preto com glow neon vermelho ("I WAS A BURDEN / TO MY FAMILY", 28,7 s) e em amarelo neon sobre o B-roll ("WITH NO ONE WATCHING / OVER ME", ~72 s).
- **Visual:** idoso sentado em poltrona, plano tipo selfie. O hook tem grão e enquadramento diferentes dos do body (FATO visual), o que sugere fontes ou gerações distintas para hook e body (HIPÓTESE). O B-roll é fotorreal: esposa na janela, cortador de grama, laboratório, colher de mel, caminhonete. HIPÓTESE: IA (start frame mais Kling ou Veo). B-roll ~27%.
- **Defeitos (FATO visual):** o personagem do B-roll não bate entre planos. O homem do cortador aparece de camiseta verde num plano e de macacão jeans noutro, e o idoso da poltrona no ângulo alternativo tem outra camisa e outro rosto. A legenda pequena (~1/3 da largura) é a menos legível das quatro.

## V4 — ProdutoJ (Biz Opp / prosperidade), AD01 HK1
Origem: `{raiz}/26. Biz Opp/ProdutoJ/OT/[021026][OT] NNN_XX [ProdutoJ] - Ads [Squad]/EXPORT/AD01/[021026][OT] NNN_XX AD01 HK1 [ProdutoJ] [Squad].mp4`

- **Specs (FATO):** 112,9 s · 1080x1920 · **25 fps** · H.264 13,6 Mb/s · AAC 48 kHz · **−16,0 LUFS** · true peak **−1,2 dBFS** · LRA 3,6. É o único perto do padrão de entrega.
- **Estrutura (FATO):**
  - 0–7,2 s: **hook** com outro personagem, num set de entrevista, falando de um "método de manifestação".
  - 7,2 s: body com avatar feminina em selfie no quarto. Pergunta de abertura ("Why is nobody talking…"), inimigo (afirmações, vision boards), novo mecanismo (identidade), nome do produto em 48,8 s ("That's where the ProdutoJ comes in"), 4 fases, facilidade ("15 minutes a day") e CTA.
  - ~89,5 s: **transição por flash branco** que abre o bloco de CTA.
  - 97,8 s: link falado. A **pílula "LEARN MORE ↓" branca com texto vermelho** fica fixa a partir daí até o fim (~15 s, 13% do vídeo).
- **Ritmo (FATO):** 31 cortes (0.3), ou 16,5/min com plano médio de 3,5 s, o mais rápido. Os dois limiares quase coincidem (31 contra 34 cortes), sinal de corte seco entre planos bem diferentes. Fala a 168 palavras/min.
- **Legenda (FATO):** **CAIXA ALTA, karaokê**, 2 a 4 palavras em 1 ou 2 linhas, branca com **caixa roxa e glow na palavra ativa**, a ~73% da altura. O hook usa outra fonte (condensada) com a mesma lógica de palavra ativa roxa.
- **Lettering (FATO):** palavra-chave em amarelo e laranja com glow forte, sobre o rosto ou o B-roll ("THE ProdutoJ", "4 PHASES", "RESET", "SYNTAX", "MIRROR", "15 MIN / DAY").
- **Visual:** avatar fixa (mesmo quarto, mesmo moletom, mesmo coque) em ~60% do tempo. B-roll ~33%, cinematográfico, escuro e quente: espelho com post-its, mulher diante do espelho, cérebro dourado com sinapses, cabeça em raio-X com cérebro brilhante, caixa de cadernos manuscritos, celular tocando vídeo. Há também footage de arquivo de um performer. HIPÓTESE: avatar no HeyGen (Avatar IV) e B-roll em GPT Image ou nano_banana animado no Kling, coerente com a skill `edicao-prosperidade-adhw`.
- **Áudio:** pausas entre −17 e −36 dB, a trilha mais alta das quatro (HIPÓTESE: trilha presente com SFX nas transições, como o whoosh do flash). Voz feminina americana.
- **Defeitos:** nenhum quadro preto. True peak de −1,2 está no limite.

---

## Tabela comparativa (FATO)

| | MarcaA | MarcaD | MarcaB | ProdutoJ |
|---|---|---|---|---|
| Duração | 73,7 s | 230,8 s | 98,0 s | 112,9 s |
| fps | 23,976 | 30 | 30 | 25 |
| LUFS / TP | −31,3 / −13,6 | −28,4 / −9,1 | −23,2 / −5,9 | −16,0 / −1,2 |
| Fim do hook | ~4,7 s (split) | ~9 s (split) | ~14,7 s (faixa) | ~7,2 s (troca de personagem) |
| Cortes/min (0.3 / 0.12) | 9,8 / 27 | 4,9 / 11 | 8 / 20 | 16,5 / 18 |
| Palavras/min | 185 | 199 | 186 | 168 |
| B-roll (aprox.) | ~30% | ~24% | ~27% | ~33% |
| Legenda | 2–3 palavras, centro | 2–3 palavras, 59% | 1–3 palavras, 66% | 2–4 em CAIXA ALTA, karaokê roxo, 73% |
| Lettering de frase | não (só manchete do hook) | não | sim (neon vermelho e amarelo) | sim (amarelo com glow) |
| CTA visual | pílula LEARN MORE piscando | nenhum | CLICK BELOW e seta | pílula LEARN MORE ↓ |

---

## Padrões recorrentes

### Para o EDITOR DE VÍDEO
1. **Manchete de hook fixa no topo nos primeiros 5–15 s e removida no body (FATO, 3 de 4):** moldura amarela no MarcaA, caixa vermelha no MarcaD, faixa vermelha no MarcaB. Duas cores de destaque na mesma manchete (branco mais amarelo ou verde).
2. **Hook em layout diferente do body (FATO, 4 de 4):** split com inset no MarcaA, split horizontal no MarcaD, faixa com botões no MarcaB, outro personagem e outro set no ProdutoJ. A virada para o body é marcada por mudança de layout ou de personagem, o que facilita trocar o hook (HK1…HK10) sobre o mesmo body.
3. **Legenda sempre em pedaços de 1 a 4 palavras, sobre caixa ou glow, entre 50% e 73% da altura (FATO, 4 de 4).** Dois estilos convivem: o simples (caixa normal, caixa escura) e o premium (CAIXA ALTA, palavra ativa roxa, só no ProdutoJ).
4. **O ritmo vem de punch-in no talking head mais B-roll literal (FATO).** A cabeça falante ocupa 60–77% do tempo, e o B-roll ilustra a palavra dita ("crave sweets" vira chocolate, "mow the lawn" vira cortador, "brain" vira cérebro). No formato podcast, longo, quase todo o ritmo vem do punch-in.
5. **Fala sem respiro (FATO):** entre 168 e 199 palavras/min, com 3 ou menos pausas acima de 0,4 s nos ADs curtos. O corte de silêncio é agressivo.
6. **CTA visual nos últimos 10–15% (FATO, 3 de 4)**, entrando junto com a frase do link: pílula LEARN MORE fixa ou piscando, ou CLICK BELOW com seta. O MarcaD é o único sem CTA gráfico.
7. **Transição de bloco por flash ou light leak (FATO, 2 de 4):** o pack-shot do MarcaA e a entrada do CTA no ProdutoJ.
8. **Lettering de frase-chave em neon ou glow (FATO, 2 de 4)**, em amarelo e laranja ou vermelho, tela cheia sobre preto ou sobre o B-roll.
9. **Specs inconsistentes (FATO):** fps de 23,976, 25 e 30, sample rate de 44,1 e 48 kHz, loudness de −31 a −16 LUFS (15 LU de diferença). Não há padrão de master; três dos quatro estão bem abaixo de −14.

### Para o IA CREATOR
1. **Um personagem âncora fixo por body (FATO, 4 de 4):** mesmo cenário, roupa e enquadramento do começo ao fim. No MarcaA o produto já está composto na cena, na mesma posição em todos os planos. HIPÓTESE: start frame fixo mais lip sync (HeyGen ou similar).
2. **Arquétipo de personagem casado ao nicho (FATO visual):** mulher comum de 30–40 anos em cozinha (weight loss), idoso veterano em casa (memory), convidado de podcast (heart), mulher em selfie no quarto (prosperidade).
3. **O B-roll mistura duas famílias (FATO visual, origem HIPÓTESE):** footage orgânico de UGC para a dor cotidiana (MarcaA) e IA fotorreal cinematográfica para mecanismo e conceito (cérebro dourado, raio-X, medidor de pressão, mel). Paleta escura e quente no Biz Opp; luz natural no Memory.
4. **Consistência do personagem secundário é o ponto fraco (FATO, MarcaB):** o mesmo "eu" do depoimento aparece com outra roupa e outro rosto no B-roll. É preciso gerar o B-roll do protagonista a partir do mesmo retrato-âncora.
5. **Hook gerado à parte do body (FATO visual em MarcaB e ProdutoJ):** grão, enquadramento ou personagem diferentes. É um módulo trocável.
6. **Pack-shot do produto em motion** (MarcaA: pote sobre tipografia cinética) quando o produto é nomeado. No Biz Opp, o produto é o nome em lettering ("THE ProdutoJ").
7. **Voz americana (FATO);** TTS, clonada ou humana é HIPÓTESE. As duas vozes do formato podcast (convidado e entrevistador) indicam uma geração por personagem.
