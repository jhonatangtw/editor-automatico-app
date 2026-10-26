# Matriz de decisão

A decisão de edição combina quatro coisas: **tipo de peça** (o que a peça precisa conseguir), **estilo de vídeo** (como o material foi ou será capturado), **nicho/público** (o que gera confiança para essa pessoa) e **registro** (a "linguagem de acabamento", que define os tokens de transição, legenda, loudness e SFX).

## 1. Registros de acabamento

As skills existentes da operação usam regras que parecem contraditórias (corte seco × flash; −14 × −16 LUFS; legenda em pílula × palavra ativa). Elas não são contraditórias: cada uma pertence a um registro. Escolha **um registro por peça** e use os tokens dele.

| Registro | Quando | Transição | Legenda | Lettering | SFX | Zoom | Loudness final |
|---|---|---|---|---|---|---|---|
| **UGC cru** | Criativo de "pessoa comum"; credibilidade de celular | Corte seco (ESCOLHA, MarcaA) | Pílula branca, texto preto, 3–4 palavras, centro-baixo (OBSERVADO 5/5) | Raro | Nenhum ou quase nenhum | Punch-in seco de 110–116%, variando a escala; sem zoom animado | −14 LUFS, TP ≤ −1 |
| **UGC alta densidade / dinâmico** | Story-ad, clone de winner "dopaminérgico", emagrecimento 30–45 | Corte seco + rajadas | ≤3 palavras, palavra ativa amarela | Só palavras faladas, poucas | Discretos (whoosh, pop, boom, ding) | Snap rápido por frase (1,0↔1,1–1,28) | −14 LUFS |
| **Premium DR** | Biz Opp, manifestação, avatar + B-roll literal | Flash branco curto nas viradas (ESCOLHA, ProdutoJ) | 2–4 palavras CAIXA ALTA, palavra ativa em caixa colorida | Palavra-chave amarela com deep glow, altura do peito | Whoosh por B-roll, pop/boom no lettering, riser antes do CTA | Punch seco de 112% + zoom 100↔107 em janelas ≥2 s | ≈ −16 LUFS (voz −16, trilha bem abaixo) |
| **Solene / sagrado** | Religioso, oração, público mais velho espiritualizado | Fade, luz, fade pelo preto | Serifada, frase inteira, palavras-chave em itálico dourado; **karaokê reprovado** (ESCOLHA, ProdutoI) | Serifada, pouco | Quase nenhum; trilha coral/orquestral | Push-in lento | −14 a −16 |
| **Editorial / clínico** | Especialista, saúde 50+, upsell, VSL de saúde | Corte seco, fade em capítulo | Sóbria, pílula ou contorno simples, grande | Uma expressão destacada (ex.: azul com glow, MarcaB) | Mínimos | Punch sóbrio de 105–115% | −15 a −16 |
| **STUDIO / premium de marca** (Reels do usuário, motion AE) | Conteúdo próprio, orgânico premium | Slide/wipe/push/sweep; **sem** flash, whip pan e glitch | Por projeto | Tipografia mista, câmera 3D, profundidade | Som desenhado | Câmera com profundidade | −14 LUFS |

Se o projeto já tem padrão próprio (skill dedicada, referência do copywriter, peça anterior aprovada), **ele vence** esta tabela.

## 2. Tipo de peça × estilo: o que funciona

| | UGC | Talking head / avatar | Especialista | Podcast/entrevista | Depoimento | Demonstração | Tutorial/tela | Documentário/story | Animação | Montagem B-roll |
|---|---|---|---|---|---|---|---|---|---|---|
| **Criativo** | ●●● base do feed | ●●● | ●● (objeção "funciona?") | ●● parece conteúdo | ●● | ●●● hook de ação | ●● infoproduto | ● curto demais | ●● mecanismo | ●●● faceless |
| **Microlead** | ●● | ●●● | ●●● | ●● | ●● | ●● | ●● | ●●● | ●●● mecanismo | ●●● |
| **Upsell** | ● | ●●● conselho | ●●● | ● | ●●● prova social | ●● | ●● | ● | ●● | ● |
| **VSL** | ● (só blocos) | ●●● | ●●● | ●● | ●●● | ●● | ●● | ●●● | ●●● | ●●● |

●●● escolha natural · ●● bom em contextos específicos · ● raro ou só como bloco

## 3. Como decidir (sequência)

1. **Qual é o próximo passo que a peça precisa conseguir?** Clique (criativo), seguir assistindo até a emenda (microlead), "sim" imediato (upsell), compra (VSL). Isso define a estrutura (`pecas/`).
2. **Qual é a maior objeção do público neste momento?** "É anúncio" → UGC/podcast. "Funciona?" → demonstração/especialista. "É para mim?" → depoimento parecido com o público. "Por que agora?" → oportunidade/notícia. Isso define o ângulo de comunicação e reforça o estilo.
3. **Que material existe?** Não escolha um estilo que exige material que não há. Avatar fixo sem B-roll → talking head com punch-in + inserts gerados; só locução → montagem; tela gravada → tutorial.
4. **Qual registro?** Pelo nicho e pela referência do cliente (tabela 1).
5. **Que intensidade?** Pelo público: mais velho e mais desconfiado = mais calma e mais legível; mais jovem e mais exposto a feed = mais densidade. Ver `nichos/`.
6. **Declare a escolha em 2–3 linhas** e siga.

## 4. Combinações típicas (atalhos)

| Situação | Combinação |
|---|---|
| Emagrecimento, público feminino 35–55, Meta, frio | Criativo · UGC alta densidade · história pessoal · ângulo dor ou desejo · demonstração de ritual no hook |
| Pressão/glicose, público 55+, EUA | Criativo/Microlead · Meat Hook ou talking head · ângulo mecanismo/demonstração · registro editorial · legenda grande · SFX mínimos |
| Biz Opp / manifestação, público 25–45 | Criativo · avatar + B-roll literal · registro premium DR · ângulo curiosidade/oportunidade · rajada na revelação |
| Religioso, público 50+ | Criativo · avatar solene · registro solene · ângulo desejo/esperança · serifada, frase inteira |
| Suplemento, pós-compra | Upsell · talking head + depoimentos + especialista · editorial · oferta muito legível |
| Mecanismo invisível, VSL longa | VSL · animação 3D + narração · cenas de até ~15 s · legenda conforme o cliente |
| Infoproduto / SaaS | Criativo ou VSL · tutorial/tela + rosto em PiP · STUDIO ou editorial · prova = método funcionando |
| Beleza | Criativo · UGC de espelho + demonstração · close de textura · sem retoque |
