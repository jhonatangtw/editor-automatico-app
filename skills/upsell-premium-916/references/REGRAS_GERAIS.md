---
name: regras-gerais-upsell
description: "Regras do usuário para todo upsell (frasco, b-roll, cards, legenda, preço, gifts, fluxo de aprovação) consolidadas das revisões do Upsell #1 MarcaK em 30/10/2026"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1d3630f8-da34-4dbd-ba25-a12d6f7c1db9
  modified: 2026-11-01T19:55:47.848Z
---

Regras que o usuário consolidou em 30/10/2026 depois das revisões do Upsell #1 MarcaK. Valem para TODO upsell.

**Fluxo:** formato 9:16 1080×1920, salvo pedido diferente (o MarcaK foi 4:3 porque o briefing do copy pediu). A aprovação é pela prévia aberta no HyperFrames, nunca pelo ferramenta de revisão, e o render só vem depois. Antes de gerar, reaproveitar b-roll de jobs anteriores do produto. O IA Creator (Agência Samurai) audita cada lote e a prévia.

**Frasco:**
- Rótulo oficial dos mockups. Frasco branco, genérico ou de outra marca reprova, inclusive em fábrica.
- Sempre em pé, com o rótulo de frente. Deitado reprova.
- ~10 cm, cabe na palma. Tamanho único em todas as telas.
- Rótulo fosco que pega a luz do ambiente, com sombra dos dedos. Conferir letra por letra, incluindo o número de cápsulas.
- **Cena da entrega = caminhão UPS** (usuário, 01/11, vale para TODO upsell): no trecho que mostra o pedido saindo/chegando, o caminhão é o da UPS — carroceria marrom-escura com o escudo dourado "ups" na lateral, entregador de uniforme marrom; as caixas de envio continuam com a logo do produto — EXCETO no nicho de ED, onde são LISAS, sem nome/logo (regra de 02/11). Referência: `~/.claude/skills/upsell-premium-916/(exemplo visual que não acompanha o app) (antes, sem logo: `MarcaL_entrega_sem_logo_antes.png`). Gerar a imagem já com o escudo (GPT Image/Nano Banana com a ref) e conferir a grafia "ups"; não colar logo por cima. Obs.: é marca registrada de terceiro — decisão do usuário ciente do risco; se a copy/compliance de algum produto pedir sem logo, perguntar.
- Não inventar embalagem fora dos mockups. Caixa de envio com a logo do produto; só no nicho de ED ela é LISA, sem nome (discrição; usuário 02/11). A caixa premium do kit no preço sempre mantém a marca.
- A quantidade falada aparece na tela, sincronizada com a palavra.

**B-roll:**
- **Nada de b-roll estilo Pixar 3D/cartoon** (usuário, 31/10). Só real ou IA fotorrealista; 3D anatômico médico realista ok.
- **Orgânico primeiro, IA por último** (usuário, 31/10; stock BANIDO em 03/11): para cada plano, buscar antes footage real de gente comum (acervo do produto/DTC, jobs anteriores, TikTok/IG/YouTube de vlog), nunca banco de vídeo/stock, e só gerar por IA o que não existir — IA erra rótulo e tem cara de IA.
- O insert demonstra a fala. Dor concreta, do dia a dia.
- 3D explica (progressão, antes e depois, mês 1→2→3). Para ereção, 3D anatômico translúcido e médico.
- Mesmo rosto em todos os planos. Figurino muda a cada momento/dia da história e só se repete dentro do mesmo momento contínuo (regra nova do usuário, 01/11; planejar roupa por cena no storyboard e no prompt; ver `upsell-premium-916/references/REGRAS_JHON_3010.md`).
- Bloco ANTI-STOCK nos prompts.

**Cards e legenda:**
- Proibido texto solto sobre avatar borrado. Todo destaque precisa de imagem ou 3D que diga a mesma coisa.
- Interface de pedido é mão real segurando celular, nunca celular desenhado.
- Legenda nunca para (pula só as palavras da headline). Headline em cima, legenda embaixo, nenhuma cobre rosto.
- **Número na legenda sempre em algarismo** (usuário, 01/11): a locução pode falar por extenso ("nineteen a bottle… one twenty-nine total"), mas a legenda mostra "$19 a bottle… $129 total". Vale para preço, total, quantidade de frascos, dias, porcentagem e idade. O TTS recebe o texto falado; o `_alin.json` e a legenda usam o texto com algarismos (alinhar pelo tempo das palavras).
- Lettering atrás do avatar opaco e nunca cortado pela cabeça.
- Transições de luz e light leak. Ritmo bbkatana.

**Preço (padrão MarcaE NNN_XX):** bancada real com luz natural, frascos em pé e mão pegando um. Card branco ou translúcido arredondado, com "$X/bottle" grande e o total embaixo. Legenda em faixa escura translúcida. Cor do card na identidade do produto. Não copiar caixa de kit que o produto não tem.

**Kit premium (aprovado 30/10, MarcaK):** caixa de kit aberta com frascos em nichos mais frascos soltos em pé na frente, bancada de mármore, sol lateral e cozinha clara desfocada. Referência em `<pasta de trabalho>/_SAMURAI/MarcaK-up1/referencias/kit_padrao_premium_jhon.png`. O total visível bate com a versão, e o "N BOTTLES" na caixa só aparece se bater.

**Gifts:** cada um ganha imagem ou vídeo próprio. Video lesson é personagem assistindo no tablet ou celular. E-book é mockup com o nome na capa. Texto de capa ou tela entra em HTML, nunca gerado pela IA. "GIFT #N" e o valor riscado virando FREE são lettering integrado. Tom sugestivo, nada explícito.

**CTA:** botão no padrão do upsell validado.

**Oferta:** conferir cápsulas × dose × dias contra o rótulo. Se não fechar, a fala segue a copy, a conta fica fora da tela e o copywriter é avisado.

**Why:** reprovações reais do usuário no MarcaK (frasco deitado, rótulo CGI, logo em caixa de envio, frasco gigante, kit fake).
**How to apply:** checklist obrigatório antes de mostrar qualquer prévia de upsell. Complementa [[upsell-cor-psicologia-vence-referencia]] e [[anti-cara-de-ia-em-imagem]].

**Frascos lado a lado (31/10, NNN_XX):** no trecho "how many bottles / mês 1-2-3", o usuário pede os frascos lado a lado na ideia do MarcaE: split de 3 painéis verticais com fio branco e rótulo pequeno (cena 33 de `MarcaE-up1-NNNxx/edicao/build_antes_DEF.py`, CSS `.split`). Conferir na prévia antes do render.
**Referências visuais (31/10, NNN_XX):** o split chapado foi reprovado ("estilo de edição muito fraco"). Cena de produto/frascos/kit segue MarcaE + MarcaG NNN_XX + MarcaL Up1 (`<pasta de trabalho>/_SAMURAI/`); lettering segue o MarcaG NNN_XX; frasco de cápsula tem o TAMANHO do frasco do MarcaE (padrão da casa).
**Tamanho por tipo de frasco (31/10):** frasco de GOTAS (conta-gotas, ex. MarcaD, MarcaG) segue o padrão de tamanho de gotas já validado; frasco de CÁPSULA (ex. MarcaM) segue o padrão de cápsula validado do MarcaE NNN_XX.
**Reprovado 2× em 31/10 (NNN_XX):** frascos PNG em painéis/fundo azul chapado e card "100" sobre expert desfocado = "zero padrão visual". O lado a lado do MarcaE são 3 FOTOS REAIS (café/almoço/jantar); lettering MarcaG = título condensado branco + linha colorida sobre imagem full-bleed. Pranchas em `<pasta de trabalho>/_SAMURAI/MarcaD-up2-NNNxx/referencias_padrao/`; mandar a prancha pro agente em vez de descrever.
**Frasco direto na imagem (usuário 31/10):** cena de produto = UMA imagem gerada já com os frascos + rótulo/logo dentro (GPT Image/Nano Banana com o rótulo oficial de referência), animada no Kling se for b-roll. Não colar PNG de frasco por cima de cena vazia; se a grafia sair errada, regerar ou corrigir só a palavra.

**Personagem da história ≠ expert (01/11/2026):** quando o expert não é quem vive a história, o b-roll da história usa um personagem próprio. O rosto é diferente do expert e fica o mesmo em todas as cenas, e o figurino muda a cada momento. O foco é b-roll orgânico com pessoa coerente com esse personagem; IA só no que faltar. O rosto do expert nunca aparece na história de outra pessoa. Gravado também em REGRAS_JHON_3010.md.
**Why:** o usuário pediu no Upsell 2 MarcaO (NNN_XX) e mandou deixar como regra.
**How to apply:** no plano de todo upsell, VSL ou AD com história, marcar em cada b-roll quem aparece e se a cena é orgânica ou gerada.
**Tela de celular/tablet (01/11, NNN_XX):** tela desenhada em HTML colada sobre mão/tablet foi reprovada como "bugado". Gerar a cena já com o conteúdo na tela (oferta, capa do guia) e animar; lettering por fora da tela.
**Cena de frasco = padrão MarcaE (01/11):** momento real de uso à mesa (1 frasco, mão com cápsula, prato de café/almoço/jantar, mesma mesa mudando a luz, rótulo pequeno com ícone, legenda em faixa), não fileira de catálogo com título grande. Ficha: `MarcaD-up2-NNNxx/referencias_padrao/ficha_frascos_MarcaE_x_nosso.jpg`; ref MarcaE V2 Preço A 182/188/434 s.
**Tela de preço validada (01/11) — padrão copy, SEMPRE assim:** kit premium aberto + frascos soltos na frente (mármore, cozinha com sol de manhã), banner inclinado "Triple-Dose Kit" no topo, card "$X /bottle" em paralelogramo com cheio riscado em vermelho + tarja "$Y TOTAL", sem legenda na cena; mesmo cenário de fundo para o selo de garantia. **Molduras (banner, card, tarja) sempre na cor da marca do produto** (o azul-escuro do exemplo é do MarcaK; MarcaL = canela/dourado). Substitui o card branco do padrão MarcaE acima. Claims de tratamento na caixa ("Restores Insulin Sensitivity") trocar por claim de rótulo seguro e avisar o usuário. Exemplo: `MarcaD-up2-NNNxx/referencias_padrao/padrao_price_validado_MarcaK.png` (o "R$33" do exemplo é erro; usar $).

- **Timeline antes do render (01/11/2026, usuário):** antes de QUALQUER render, abrir APENAS a timeline (prévia do HyperFrames no navegador) para o usuário aprovar o visual. Sem o OK dele na prévia, não pedir a vez nem renderizar. Motivo: evitar retrabalho de render.

- **Supervisor-Upsell obrigatório (01/11/2026, usuário):** todo upsell passa pelo agente `supervisor-upsell` (~/.claude/agents/supervisor-upsell.md) antes da prévia, antes do render e nos mp4. Ele lê todas as regras na versão mais nova, corrige no build o que não custa dinheiro e devolve só geração paga e decisões do usuário. Regra nova de upsell → gravar no REGRAS_JHON_3010.md, que é de onde ele lê.


**Economia de tokens (usuário, 02/11):** supervisor e caça-erro em Sonnet; caça-erro só uma vez, no mp4 final (repassada só nos trechos corrigidos); supervisor leve antes do render + no mp4; no máximo 2 upsells trabalhando ao mesmo tempo; mensagens ao Controle curtas e só para vez/fim/entrega.

**Regras de 03/11 (rodada NNN_XX MarcaD), 21 itens** — consolidadas em `upsell-premium-916/references/REGRAS_JHON_3010.md`, seção "03/11/2026". Resumo: gotas direto na boca; frasco junto ao expert ~25–30%; expert num ambiente só, com câmera parada e corte A/B; card do gift junto do expert desde t=0; edição humana (corte seco + L/J-cut + light leak suave, sem zoom/whip/órbita); IA ≤3 s com grão; pessoas = orgânico primeiro com rosto liberado (meta 70%), 3D pode ser IA; YouTube/TikTok/casos clínicos e cenas fortes liberados, com blur em logo e paciente; nunca cortar com zoom na troca de proporção (outpaint/gerar nativo); vertical em pillarbox com blur; nada de texto sobre rosto; headline ≤60%; lettering sóbrio; citações uma por vez; legenda sem palavra solta; SFX real antes do render; verificador visual na prévia antes de mostrar.
